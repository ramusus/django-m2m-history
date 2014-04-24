from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from signals import m2m_history_changed


class ManyToManyHistoryCache(models.Model):
    class Meta:
        unique_together = ('content_type', 'field_name', 'time')

    content_type = models.ForeignKey(ContentType, db_index=True)
    field_name = models.CharField(max_length=50, db_index=True)
    time = models.DateTimeField(db_index=True)

    added_count = models.PositiveIntegerField(default=0)
    removed_count = models.PositiveIntegerField(default=0)


@receiver(m2m_history_changed)
def save_m2m_history_cache(sender, action, instance, reverse, pk_set, field_name, time, **kwargs):
    need_to_cache = not reverse and instance._meta.get_field(field_name).cache
    if need_to_cache and action in ['post_add', 'post_remove', 'post_clear'] and len(pk_set):
        cache = ManyToManyHistoryCache.objects.get_or_create(content_type=ContentType.objects.get_for_model(instance), field_name=field_name, time=time)[0]
        if action in ['post_add']:
            cache.added_count = len(pk_set)
        elif action in ['post_remove', 'post_clear']:
            cache.removed_count = len(pk_set)
        cache.save()