# -*- coding: utf-8 -*-
import warnings
import django
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.fields.related import ManyRelatedObjectsDescriptor, ReverseManyRelatedObjectsDescriptor, \
    cached_property, create_many_related_manager, router, signals
from django.utils import timezone

from .models import ManyToManyHistoryVersion
from .signals import m2m_history_changed

# compatibility with Django 1.9
if django.VERSION[:2] >= (1, 9):
    raise NotImplementedError("Unfortunately django-m2m-history application still is not compatible with Django 1.9")


def create_many_related_history_manager(superclass, rel):
    baseManagerClass = create_many_related_manager(superclass, rel)

    class ManyToManyHistoryThroughManager(baseManagerClass):

        # time of altering transaction
        time = None

        @property
        def db(self):
            return router.db_for_write(self.through, instance=self.instance)

        @property
        def versions(self):
            return ManyToManyHistoryVersion.objects.filter(
                content_type=ContentType.objects.get_for_model(self.instance),
                object_id=self.instance.pk, field_name=self.prefetch_cache_name)

        def get_time(self):
            if not self.time:
                self.time = timezone.now()
            return self.time

        def last_update_time(self):
            # TODO: refactor and optimize this method to one query
            qs = self.get_queryset_through()
            try:
                time_to = qs.exclude(time_to=None).order_by('-time_to')[0].time_to
                time_from = qs.exclude(time_from=None).order_by('-time_from')[0].time_from
                return time_to if time_to > time_from else time_from
            except IndexError:
                return qs.exclude(time_from=None).order_by('-time_from')[0].time_from

        def _prepare_queryset(self, qs, only_pk=False, unique=True):
            qs = qs.values_list(self.target_field_name, flat=True)
            if not only_pk:
                if unique is False:
                    raise ValueError("Argument `unique` should be True if argument only_pk is False")
                method_name = 'get_queryset' if django.VERSION[:2] >= (1, 7) else 'get_query_set'
                qs = getattr(super(ManyToManyHistoryThroughManager, self), method_name)().using(
                    self.db).filter(pk__in=qs)

            if unique:
                qs = qs.distinct()
            return qs

        def get_query_set(self, **kwargs):
            warnings.warn("Backward compatibility. Use get_queryset() instead", DeprecationWarning)
            return self.get_queryset(**kwargs)

        def get_query_set_through(self):
            warnings.warn("Backward compatibility. Use get_queryset_through() instead", DeprecationWarning)
            return self.get_queryset_through()

        @property
        def queryset_through(self):
            return self.get_queryset_through()

        def get_queryset_through(self):
            qs = self.through._default_manager.using(self.db).filter(**{
                self.source_field_name: self._fk_val,
            })
            return qs

        def get_queryset(self, **kwargs):
            qs = self.get_queryset_through().filter(time_to=None)
            return self._prepare_queryset(qs, **kwargs)

        def were_between(self, time_from, time_to, **kwargs):
            if time_to <= time_from:
                raise ValueError('Argument time_to should be later, than time_from')
            qs = self.get_queryset_through().filter(
                Q(time_from=None, time_to=None) |
                Q(time_from=None, time_to__gte=time_to) |
                Q(time_from__lte=time_from, time_to=None) |
                Q(time_from__gte=time_from, time_to__lte=time_to) |
                Q(time_from__lte=time_from, time_to__gte=time_to) |
                Q(time_from__lt=time_to, time_to__gt=time_from))
            return self._prepare_queryset(qs, **kwargs)

        def added_between(self, time_from, time_to, **kwargs):
            if time_to <= time_from:
                raise ValueError('Argument time_to should be later, than time_from')
            qs = self.get_queryset_through().filter(time_from__gte=time_from, time_from__lte=time_to)
            return self._prepare_queryset(qs, **kwargs)

        def removed_between(self, time_from, time_to, **kwargs):
            if time_to <= time_from:
                raise ValueError('Argument time_to should be later, than time_from')
            qs = self.get_queryset_through().filter(time_to__gte=time_from, time_to__lte=time_to)
            return self._prepare_queryset(qs, **kwargs)

        def were_at(self, time, **kwargs):
            qs = self.get_queryset_through().filter(
                Q(time_from=None, time_to=None) |
                Q(time_from=None, time_to__gt=time) |
                Q(time_from__lte=time, time_to=None) |
                Q(time_from__lte=time, time_to__gt=time))
            return self._prepare_queryset(qs, **kwargs)

        def added_at(self, time, **kwargs):
            qs = self.get_queryset_through().filter(time_from=time)
            return self._prepare_queryset(qs, **kwargs)

        def removed_at(self, time, **kwargs):
            qs = self.get_queryset_through().filter(time_to=time)
            return self._prepare_queryset(qs, **kwargs)

        def clear(self, *objs):
            self._clear_items(self.source_field_name, self.target_field_name, *objs)

            # If this is a symmetrical m2m relation to self, clear the mirror entry in the m2m table
            if self.symmetrical:
                self._clear_items(self.target_field_name, self.source_field_name, *objs)

        clear.alters_data = True

        def send_signal(self, source_field_name, action, ids):
            if self.reverse or source_field_name == self.source_field_name:
                # Don't send the signal when we are inserting the
                # duplicate data row for symmetrical reverse entries.
                signals.m2m_changed.send(sender=self.through, action=action,
                                         instance=self.instance, reverse=self.reverse,
                                         model=self.model, pk_set=ids, using=self.db)

                m2m_history_changed.send(sender=self.through, action=action,
                                         instance=self.instance, reverse=self.reverse,
                                         model=self.model, pk_set=ids, using=self.db,
                                         field_name=self.prefetch_cache_name, time=self.get_time())

        def get_set_of_values(self, objs, target_field_name, check_values=False):
            values = set()
            # Check that all the objects are of the right type
            for obj in objs:
                if isinstance(obj, self.model):
                    if check_values and not router.allow_relation(obj, self.instance):
                        raise ValueError('Cannot add "%r": instance is on database "%s", value is on database "%s"' %
                                         (obj, self.instance._state.db, obj._state.db))
                    fk_val = self._get_fk_val(obj, target_field_name)
                    if check_values and fk_val is None:
                        raise ValueError('Cannot add "%r": the value for field "%s" is None' %
                                         (obj, target_field_name))
                    values.add(fk_val)
                elif isinstance(obj, models.Model):
                    raise TypeError("'%s' instance expected, got %r" % (self.model._meta.object_name, obj))
                else:
                    values.add(obj)
            return values

        def _add_items(self, source_field_name, target_field_name, *objs):
            # source_field_name: the PK fieldname in join table for the source object
            # target_field_name: the PK fieldname in join table for the target object
            # *objs - objects to add. Either object instances, or primary keys of object instances.

            # If there aren't any objects, there is nothing to do.
            if objs:
                new_ids = self.get_set_of_values(objs, target_field_name, check_values=True)
                current_ids = self.through._default_manager.using(self.db) \
                    .values_list(target_field_name, flat=True) \
                    .filter(**{
                        source_field_name: self._fk_val,
                        '%s__in' % target_field_name: new_ids,
                        'time_to': None,
                    })
                # remove current from new, otherwise integrity error while bulk_create
                new_ids = new_ids.difference(set(current_ids))

                self.send_signal(source_field_name, 'pre_add', new_ids)

                # Add the ones that aren't there already
                self.through._default_manager.using(self.db).bulk_create([
                    self.through(**{
                        '%s_id' % source_field_name: self._fk_val,
                        '%s_id' % target_field_name: obj_id,
                        'time_from': self.get_time(),
                    }) for obj_id in new_ids
                ])

                self.send_signal(source_field_name, 'post_add', new_ids)

        def _remove_items(self, source_field_name, target_field_name, *objs):
            # source_field_name: the PK colname in join table for the source object
            # target_field_name: the PK colname in join table for the target object
            # *objs - objects to remove

            # If there aren't any objects, there is nothing to do.
            if objs:
                old_ids = self.get_set_of_values(objs, target_field_name)
                self.send_signal(source_field_name, 'pre_remove', old_ids)

                # Remove the specified objects from the join table
                qs = self.through._default_manager.using(self.db).filter(**{
                    source_field_name: self._fk_val,
                    'time_to': None,
                    '%s__in' % target_field_name: old_ids,
                })
                qs.update(time_to=self.get_time())

                self.send_signal(source_field_name, 'post_remove', old_ids)

        def _clear_items(self, source_field_name, target_field_name, *objs):
            # source_field_name: the PK colname in join table for the source object
            # target_field_name: the PK colname in join table for the target object
            # *objs - objects to clear

            new_ids = self.get_set_of_values(objs, target_field_name, check_values=True)
            current_ids = self.through._default_manager.using(self.db) \
                .values_list(target_field_name, flat=True) \
                .filter(**{
                    source_field_name: self._fk_val,
                    'time_to': None,
                })
            old_ids = set(current_ids).difference(new_ids)
            self.send_signal(source_field_name, 'pre_clear', old_ids)

            qs = self.through._default_manager.using(self.db).filter(**{
                source_field_name: self._fk_val,
                'time_to': None,
                '%s__in' % target_field_name: old_ids,
            })
            qs.update(time_to=self.get_time())

            self.send_signal(source_field_name, 'post_clear', set(self.removed_at(self.get_time(), only_pk=True)))

        # compatibility with Django 1.7
        if django.VERSION[:2] >= (1, 7):

            @property
            def _fk_val(self):
                return self.related_val[0]

            def _get_fk_val(self, obj, target_field_name):
                return self.through._meta.get_field(target_field_name).get_foreign_related_value(obj)[0]

    return ManyToManyHistoryThroughManager


class ReverseManyRelatedObjectsHistoryDescriptor(ReverseManyRelatedObjectsDescriptor):
    @cached_property
    def related_manager_cls(self):
        """
        Difference from super method is return our own manager inherited from the build-in
        """
        return create_many_related_history_manager(
            self.field.rel.to._default_manager.__class__,
            self.field.rel
        )

    def __set__(self, instance, value):
        """
        Difference from super method is send value to `clear` method as well as to `add` method
        """
        if instance is None:
            raise AttributeError("Manager must be accessed via instance")

        if not self.field.rel.through._meta.auto_created:
            opts = self.field.rel.through._meta
            raise AttributeError("Cannot set values on a ManyToManyField which specifies an intermediary model. "
                                 "Use %s.%s's Manager instead." % (opts.app_label, opts.object_name))

        manager = self.__get__(instance)
        manager.clear(*value)
        manager.add(*value)


class ManyRelatedObjectsHistoryDescriptor(ManyRelatedObjectsDescriptor):
    @cached_property
    def related_manager_cls(self):
        """
        Difference from super method is return our own manager inherited from the build-in
        """
        return create_many_related_history_manager(
            self.related.model._default_manager.__class__,
            self.related.field.rel
        )

    def __set__(self, instance, value):
        """
        Difference from super method is send value to `clear` method as well as to `add` method
        """
        if instance is None:
            raise AttributeError("Manager must be accessed via instance")

        if not self.related.field.rel.through._meta.auto_created:
            opts = self.related.field.rel.through._meta
            raise AttributeError("Cannot set values on a ManyToManyField which specifies an intermediary model. "
                                 "Use %s.%s's Manager instead." % (opts.app_label, opts.object_name))

        manager = self.__get__(instance)
        manager.clear(*value)
        manager.add(*value)
