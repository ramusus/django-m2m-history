from django.db import models

from .descriptors import (ManyRelatedObjectsHistoryDescriptor,
                          ReverseManyRelatedObjectsHistoryDescriptor)

__all__ = ['ManyToManyHistoryField']


class ManyToManyHistoryField(models.ManyToManyField):

    def __init__(self, *args, **kwargs):
        self.versions = kwargs.pop('versions', False)
        super(ManyToManyHistoryField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        '''
        Call super method and remove unique_together, add time fields and change descriptor class
        '''
        super(ManyToManyHistoryField, self).contribute_to_class(cls, name)

        try:
            self.rel.through._meta.unique_together = ()
            self.rel.through.add_to_class(
                'time_from', models.DateTimeField(u'Datetime from', null=True, db_index=True))
            self.rel.through.add_to_class('time_to',  models.DateTimeField(u'Datetime to', null=True, db_index=True))
        except AttributeError:
            pass
        # wrong behaviour of south
#        self.rel.through._meta.auto_created = False

        setattr(cls, self.name, ReverseManyRelatedObjectsHistoryDescriptor(self))

    def contribute_to_related_class(self, cls, related):
        '''
        Change descriptor class
        '''
        super(ManyToManyHistoryField, self).contribute_to_related_class(cls, related)

        # `swapped` attribute is not present before Django 1.5
        if not self.rel.is_hidden() and not getattr(related.model._meta, 'swapped', None):
            setattr(cls, related.get_accessor_name(), ManyRelatedObjectsHistoryDescriptor(related))

#     def _get_m2m_db_table(self, opts):
#         db_table = super(ManyToManyHistoryField, self)._get_m2m_db_table(opts)
#         return db_table + '_history'

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^m2m_history\.fields\.ManyToManyHistoryField"])
except ImportError:
    pass
