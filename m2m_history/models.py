# -*- coding: utf-8 -*-
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models, connection
from django.dispatch import receiver

from .signals import m2m_history_changed

try:
    from django.db.transaction import atomic
except ImportError:
    from django.db.transaction import commit_on_success as atomic


class ManyToManyHistoryVersion(models.Model):
    class Meta:
        unique_together = ('content_type', 'object_id', 'field_name', 'time')

    content_type = models.ForeignKey(ContentType, related_name='m2m_history_versions', db_index=True)
    object_id = models.BigIntegerField(db_index=True)
    object = generic.GenericForeignKey('content_type', 'object_id')

    field_name = models.CharField(max_length=50, db_index=True)
    time = models.DateTimeField(db_index=True)

    count = models.PositiveIntegerField(default=0)
    added_count = models.PositiveIntegerField(default=0)
    removed_count = models.PositiveIntegerField(default=0)

    @property
    def m2m(self):
        return getattr(self.object, self.field_name)

    @property
    def prev(self):
        try:
            return self.m2m.versions.filter(time__lt=self.time).order_by('-time')[0]
        except IndexError:
            return None

    @property
    def next(self):
        try:
            return self.m2m.versions.filter(time__gt=self.time).order_by('time')[0]
        except IndexError:
            return None

    def items(self, **kwargs):
        return self.m2m.were_at(self.time, **kwargs)

    def added(self, **kwargs):
        return self.m2m.added_at(self.time, **kwargs)

    def removed(self, **kwargs):
        return self.m2m.removed_at(self.time, **kwargs)

    @atomic
    def delete(self, *args, **kwargs):
        self.delete_version_items()
        super(ManyToManyHistoryVersion, self).delete(*args, **kwargs)

    def delete_version_items(self):
        qs = self.m2m.queryset_through

        next = self.next
        prev = self.prev

        if next is None and prev is None:
            # it's only version -> delete all
            qs.all().delete()
        elif next is None and prev:
            # it's last version
            # delete all current entered items
            qs.filter(time_from=self.time).delete()
            # all left items are not left
            qs.filter(time_to=self.time).update(time_to=None)
        elif next and prev:
            # it's version in the middle
            cursor = connection.cursor()

            # all, who left now and exist in next version -> set right time_to value, which get from last part:
            # 1. make temporary table, because of partial indexes cannot let do all operations in current table
            # 2. remove second part of members, who left in first part
            # 3. update time_to of first part of members using temp table
            # 4. drop temp table
            sql = '''
                CREATE TEMP TABLE m2m_history_items_temp AS
                    SELECT second.%(m2m_object_name)s, second.%(m2m_item_name)s, second.time_from, second.time_to
                    FROM %(m2m_table_name)s AS second
                    WHERE (second.time_from = %(next_time_from)s
                        AND second.%(m2m_object_name)s = %(object_id)s
                        AND second.%(m2m_item_name)s IN (
                            SELECT first.%(m2m_item_name)s FROM %(m2m_table_name)s AS first
                                WHERE (first.%(m2m_object_name)s = second.%(m2m_object_name)s
                                    AND first.time_to = %(time_to)s
                                    AND first.%(m2m_item_name)s IN %(items)s)));

                DELETE FROM %(m2m_table_name)s AS second
                    WHERE (second.time_from = %(next_time_from)s
                        AND second.%(m2m_object_name)s = %(object_id)s
                        AND second.%(m2m_item_name)s IN (
                            SELECT first.%(m2m_item_name)s FROM %(m2m_table_name)s AS first
                                WHERE (first.%(m2m_object_name)s = second.%(m2m_object_name)s
                                    AND first.time_to = %(time_to)s
                                    AND first.%(m2m_item_name)s IN %(items)s)));

                UPDATE %(m2m_table_name)s AS first
                    SET time_to = second.time_to
                    FROM "m2m_history_items_temp" AS second
                    WHERE first.%(m2m_object_name)s = %(object_id)s
                      AND first.time_to = %(time_to)s
                      AND first.%(m2m_item_name)s IN %(items)s
                      AND first.%(m2m_item_name)s = second.%(m2m_item_name)s
                      AND second.%(m2m_object_name)s = first.%(m2m_object_name)s
                      AND second.time_from = %(next_time_from)s;

                DROP TABLE m2m_history_items_temp;
                '''.replace('%(m2m_table_name)s', self.m2m.through._meta.db_table) \
                .replace('%(m2m_object_name)s', self.m2m.source_field_name + '_id') \
                .replace('%(m2m_item_name)s', self.m2m.target_field_name + '_id')

            params = {
                'object_id': self.object.pk,
                'time_to': self.time,
                'items': tuple(next.items(only_pk=True)),
                'next_time_from': next.time
            }
            cursor.execute(sql, params)

            users_next = {'%s_id__in' % self.m2m.target_field_name: next.items(only_pk=True)}

            # all, who left here and not exist in the next -> left in the next
            qs.filter(time_to=self.time).exclude(**users_next).update(time_to=next.time)
            # all, who entered here and not exist in the next -> delete
            qs.filter(time_from=self.time).exclude(**users_next).delete()
            # all, who entered here and exist in the next -> entered in the next
            qs.filter(time_from=self.time).filter(**users_next).update(time_from=next.time)

            # update counts of the next version
            next.added_count = next.added(only_pk=True).count()
            next.removed_count = next.removed(only_pk=True).count()
            next.save()


@receiver(m2m_history_changed)
def save_m2m_history_version(sender, action, instance, reverse, pk_set, field_name, time, **kwargs):
    keep_version = not reverse and instance._meta.get_field(field_name).versions
    if keep_version and action in ['post_add', 'post_remove', 'post_clear'] and len(pk_set):
        defaults = {
            'count': getattr(instance, field_name).get_queryset(only_pk=True).count(),
        }
        if action in ['post_add']:
            defaults['added_count'] = len(pk_set)
        elif action in ['post_remove', 'post_clear']:
            defaults['removed_count'] = len(pk_set)
        version, created = ManyToManyHistoryVersion.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(instance), object_id=instance.pk, field_name=field_name,
            time=time, defaults=defaults)
        if not created:
            version.__dict__.update(defaults)
            version.save()
