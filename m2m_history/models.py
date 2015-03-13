from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver

from .signals import m2m_history_changed


class HistoryVersionNotLast(Exception):
    pass


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

    def items(self, **kwargs):
        return getattr(self.object, self.field_name).were_at(self.time, **kwargs)

    def added(self, **kwargs):
        return getattr(self.object, self.field_name).added_at(self.time, **kwargs)

    def removed(self, **kwargs):
        return getattr(self.object, self.field_name).removed_at(self.time, **kwargs)

    def delete(self, *args, **kwargs):
        if getattr(self.object, self.field_name).versions.order_by('-time')[0].pk == self.pk:
            self.delete_version_items()
            super(ManyToManyHistoryVersion, self).delete(*args, **kwargs)
        else:
            raise HistoryVersionNotLast("It isn't supported to delete not last version of history m2m relation")

    def delete_version_items(self):
        # get previous version
        try:
            prev_time = getattr(self.object, self.field_name).versions.exclude(pk=self.pk).order_by('-time')[0].time
        except IndexError:
            prev_time = None

        m2m_field = getattr(self.object, self.field_name)
        qs = m2m_field.through.objects.filter(**{m2m_field.source_field_name: self.object})

        if prev_time:
            # delete all joined and left after time of the version
            qs.filter(time_to__gt=prev_time, time_from__gt=prev_time).delete()
            # delete all joined and not left after time of the version
            qs.filter(time_from__gt=prev_time, time_to=None).delete()
            # set time the version to all left afterc
            qs.filter(time_to__gt=prev_time).update(time_to=None)
        else:
            # delete all if no previous version
            qs.all().delete()

@receiver(m2m_history_changed)
def save_m2m_history_version(sender, action, instance, reverse, pk_set, field_name, time, **kwargs):
    keep_version = not reverse and instance._meta.get_field(field_name).versions
    if keep_version and action in ['post_add', 'post_remove', 'post_clear'] and len(pk_set):
        version = ManyToManyHistoryVersion.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(instance), object_id=instance.pk, field_name=field_name, time=time)[0]
        version.count = getattr(instance, field_name).get_query_set(only_pk=True).count()
        if action in ['post_add']:
            version.added_count = len(pk_set)
        elif action in ['post_remove', 'post_clear']:
            version.removed_count = len(pk_set)
        version.save()
