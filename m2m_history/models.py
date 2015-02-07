from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver

from .signals import m2m_history_changed


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
    def items(self):
        return getattr(self.object, self.field_name).were_at(self.time)

    @property
    def added(self):
        return getattr(self.object, self.field_name).added_at(self.time)

    @property
    def removed(self):
        return getattr(self.object, self.field_name).removed_at(self.time)


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
