from django.db import models

__all__ = ['ManyToManyHistoryField']

class ManyToManyHistoryField(models.ManyToManyField):
    pass


# class GroupMembership(models.Model):
#     class Meta:
#         verbose_name = u'Членство пользователя группы Вконтакте'
#         verbose_name_plural = u'Членства пользователей групп Вконтакте'
#
#     group = models.ForeignKey(Group, verbose_name=u'Группа', related_name='memberships')
#     user_id = models.PositiveIntegerField(u'ID пользователя', db_index=True)
#
#     time_entered = models.DateTimeField(u'Дата и время вступления', null=True, db_index=True)
#     time_left = models.DateTimeField(u'Дата и время выхода', null=True, db_index=True)
#
#     objects = GroupMembershipManager()
#
#     def save(self, *args, **kwargs):
#         # TODO: perhaps useless checkings, since all GroupMemberships are created by bulk_create..
#
#         if self.time_entered and self.time_left and self.time_entered > self.time_left:
#             raise IntegrityError("GroupMembership couldn't have time_entered (%s) > time_left (%s), group %s, user remote ID %s" % (self.time_entered, self.time_left, self.group, self.user_id))
#
#         # check additionally null values of time_entered and time_left,
#         # because for postgres null values are acceptable in unique constraint
#         qs = self.__class__.objects.filter(group=self.group, user_id=self.user_id)
#         if not self.time_entered and qs.filter(time_entered=None).count() != 0:
#             raise IntegrityError("columns group_id=%s, user_id=%s, time_entered=None are not unique" % (self.group_id, self.user_id))
#         if not self.time_left and qs.filter(time_left=None).count() != 0:
#             raise IntegrityError("columns group_id=%s, user_id=%s, time_left=None are not unique" % (self.group_id, self.user_id))
#
#         return super(GroupMembership, self).save(*args, **kwargs)
