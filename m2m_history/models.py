# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Q
from django.db.models.fields.related import ReverseManyRelatedObjectsDescriptor, cached_property, create_many_related_manager, router, signals
from datetime import datetime
from IPython.core.debugger import Pdb

__all__ = ['ManyToManyHistoryField']


def create_many_related_history_manager(superclass, rel):
    baseManagerClass = create_many_related_manager(superclass, rel)

    class ManyToManyHistoryThroughManager(baseManagerClass):

        time = None

        def get_time(self):
            return self.time or datetime.now()

        def last_update_time(self):
            # TODO: optimize this method to one query
            db = router.db_for_write(self.through, instance=self.instance)
            qs = self.through._default_manager.using(db).filter(**{
                self.source_field_name: self._fk_val,
            })
            try:
                time_to = qs.exclude(time_to=None).order_by('-time_to')[0].time_to
                time_from = qs.exclude(time_from=None).order_by('-time_from')[0].time_from
                return time_to if time_to > time_from else time_from
            except IndexError:
                return qs.exclude(time_from=None).order_by('-time_from')[0].time_from

        def get_user_ids_of_period(self, group, date_from, date_to, field=None, unique=True):

            if field is None:
                # TODO: made normal filtering
                kwargs = {'time_entered': None, 'time_left': None} \
                    | {'time_entered__lte': date_from, 'time_left': None} \
                    | {'time_entered': None, 'time_left__gte': date_to}
            elif field in ['left','entered']:
                kwargs = {'time_%s__gt' % field: date_from, 'time_%s__lte' % field: date_to}
            else:
                raise ValueError("Attribute `field` should be equal to 'left' of 'entered'")

            qs = self.filter(group=group, **kwargs)
            return self._prepare_qs(qs, unique)

        def _get_qs_through(self):
            db = router.db_for_write(self.through, instance=self.instance)
            qs = self.through._default_manager.using(db).filter(**{self.source_field_name: self._fk_val,}).values_list(self.target_field_name, flat=True)
            return qs

        def added(self, time):
            qs_through = self._get_qs_through().filter(time_from=time)
            qs = super(ManyToManyHistoryThroughManager, self).all()
            return qs.filter(pk__in=qs_through).distinct()

        def removed(self, time):
            qs_through = self._get_qs_through().filter(time_to=time)
            qs = super(ManyToManyHistoryThroughManager, self).all()
            return qs.filter(pk__in=qs_through).distinct()

        def all(self, time=None, *args, **kwargs):
            qs_through = self._get_qs_through()

            if time is None:
                qs_through = qs_through.filter(time_to=None)
            else:
                qs_through = qs_through.filter(
                    Q(time_from=None,        time_to=None) | \
                    Q(time_from=None,        time_to__gt=time) | \
                    Q(time_from__lte=time,   time_to=None) | \
                    Q(time_from__lte=time,   time_to__gt=time))

            qs = super(ManyToManyHistoryThroughManager, self).all(*args, **kwargs)
            return qs.filter(pk__in=qs_through).distinct()

        def clear(self, *objs):
            self._clear_items(self.source_field_name, self.target_field_name, *objs)

            # If this is a symmetrical m2m relation to self, clear the mirror entry in the m2m table
            if self.symmetrical:
                self._clear_items(self.target_field_name, self.source_field_name, *objs)
        clear.alters_data = True

        def _add_items(self, source_field_name, target_field_name, *objs):
            # source_field_name: the PK fieldname in join table for the source object
            # target_field_name: the PK fieldname in join table for the target object
            # *objs - objects to add. Either object instances, or primary keys of object instances.

            # If there aren't any objects, there is nothing to do.
            from django.db.models import Model
            if objs:
                new_ids = set()
                for obj in objs:
                    if isinstance(obj, self.model):
                        if not router.allow_relation(obj, self.instance):
                            raise ValueError('Cannot add "%r": instance is on database "%s", value is on database "%s"' %
                                               (obj, self.instance._state.db, obj._state.db))
                        fk_val = self._get_fk_val(obj, target_field_name)
                        if fk_val is None:
                            raise ValueError('Cannot add "%r": the value for field "%s" is None' %
                                             (obj, target_field_name))
                        new_ids.add(self._get_fk_val(obj, target_field_name))
                    elif isinstance(obj, Model):
                        raise TypeError("'%s' instance expected, got %r" % (self.model._meta.object_name, obj))
                    else:
                        new_ids.add(obj)
                db = router.db_for_write(self.through, instance=self.instance)
                vals = self.through._default_manager.using(db).values_list(target_field_name, flat=True)
                vals = vals.filter(**{
                    source_field_name: self._fk_val,
                    '%s__in' % target_field_name: new_ids,
                    'time_to': None,
                })
                new_ids = new_ids - set(vals)

                if self.reverse or source_field_name == self.source_field_name:
                    # Don't send the signal when we are inserting the
                    # duplicate data row for symmetrical reverse entries.
                    signals.m2m_changed.send(sender=self.through, action='pre_add',
                        instance=self.instance, reverse=self.reverse,
                        model=self.model, pk_set=new_ids, using=db)
                # Add the ones that aren't there already
                self.through._default_manager.using(db).bulk_create([
                    self.through(**{
                        '%s_id' % source_field_name: self._fk_val,
                        '%s_id' % target_field_name: obj_id,
                        'time_from': self.get_time(),
                    })
                    for obj_id in new_ids
                ])

                if self.reverse or source_field_name == self.source_field_name:
                    # Don't send the signal when we are inserting the
                    # duplicate data row for symmetrical reverse entries.
                    signals.m2m_changed.send(sender=self.through, action='post_add',
                        instance=self.instance, reverse=self.reverse,
                        model=self.model, pk_set=new_ids, using=db)

#         def _remove_items(self, source_field_name, target_field_name, *objs):
#             # source_field_name: the PK colname in join table for the source object
#             # target_field_name: the PK colname in join table for the target object
#             # *objs - objects to remove
#
#             # If there aren't any objects, there is nothing to do.
#             if objs:
#                 # Check that all the objects are of the right type
#                 old_ids = set()
#                 for obj in objs:
#                     if isinstance(obj, self.model):
#                         old_ids.add(self._get_fk_val(obj, target_field_name))
#                     else:
#                         old_ids.add(obj)
#                 # Work out what DB we're operating on
#                 db = router.db_for_write(self.through, instance=self.instance)
#                 # Send a signal to the other end if need be.
#                 if self.reverse or source_field_name == self.source_field_name:
#                     # Don't send the signal when we are deleting the
#                     # duplicate data row for symmetrical reverse entries.
#                     signals.m2m_changed.send(sender=self.through, action="pre_remove",
#                         instance=self.instance, reverse=self.reverse,
#                         model=self.model, pk_set=old_ids, using=db)
#                 # Remove the specified objects from the join table
#                 self.through._default_manager.using(db).filter(**{
#                     source_field_name: self._fk_val,
#                     '%s__in' % target_field_name: old_ids
#                 }).delete()
#                 if self.reverse or source_field_name == self.source_field_name:
#                     # Don't send the signal when we are deleting the
#                     # duplicate data row for symmetrical reverse entries.
#                     signals.m2m_changed.send(sender=self.through, action="post_remove",
#                         instance=self.instance, reverse=self.reverse,
#                         model=self.model, pk_set=old_ids, using=db)

        def _clear_items(self, source_field_name, target_field_name, *objs):
            db = router.db_for_write(self.through, instance=self.instance)
            # source_field_name: the PK colname in join table for the source object
            if self.reverse or source_field_name == self.source_field_name:
                # Don't send the signal when we are clearing the
                # duplicate data rows for symmetrical reverse entries.
                signals.m2m_changed.send(sender=self.through, action="pre_clear",
                    instance=self.instance, reverse=self.reverse,
                    model=self.model, pk_set=None, using=db)
            qs = self.through._default_manager.using(db).filter(**{
                source_field_name: self._fk_val,
                'time_to': None,
            }).exclude(**{
                '%s__in' % target_field_name: [obj.pk for obj in objs]
            })
            qs.update(time_to=self.get_time())
            if self.reverse or source_field_name == self.source_field_name:
                # Don't send the signal when we are clearing the
                # duplicate data rows for symmetrical reverse entries.
                signals.m2m_changed.send(sender=self.through, action="post_clear",
                    instance=self.instance, reverse=self.reverse,
                    model=self.model, pk_set=None, using=db)

    return ManyToManyHistoryThroughManager


class ReverseManyRelatedObjectsHistoryDescriptor(ReverseManyRelatedObjectsDescriptor):
    @cached_property
    def related_manager_cls(self):
        # Return our own manager inherited from the build-in
        return create_many_related_history_manager(
            self.field.rel.to._default_manager.__class__,
            self.field.rel
        )

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("Manager must be accessed via instance")

        if not self.field.rel.through._meta.auto_created:
            opts = self.field.rel.through._meta
            raise AttributeError("Cannot set values on a ManyToManyField which specifies an intermediary model.  Use %s.%s's Manager instead." % (opts.app_label, opts.object_name))

        manager = self.__get__(instance)
        manager.time = datetime.now()
        manager.clear(*value)
        manager.add(*value)


class ManyToManyHistoryField(models.ManyToManyField):

    def contribute_to_class(self, cls, name):
        super(ManyToManyHistoryField, self).contribute_to_class(cls, name)

        # remove unique_together add time fields
        self.rel.through._meta.unique_together = ()
        self.rel.through.add_to_class('time_from', models.DateTimeField(u'Datetime from', null=True, db_index=True))
        self.rel.through.add_to_class('time_to',  models.DateTimeField(u'Datetime to', null=True, db_index=True))

        setattr(cls, self.name, ReverseManyRelatedObjectsHistoryDescriptor(self))
