# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ManyToManyHistoryCountsCache'
        db.create_table(u'm2m_history_manytomanyhistorycountscache', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('field_name', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('added_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('removed_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'm2m_history', ['ManyToManyHistoryCountsCache'])

        # Adding unique constraint on 'ManyToManyHistoryCountsCache', fields ['content_type', 'field_name', 'time']
        db.create_unique(u'm2m_history_manytomanyhistorycountscache', ['content_type_id', 'field_name', 'time'])


    def backwards(self, orm):
        # Removing unique constraint on 'ManyToManyHistoryCountsCache', fields ['content_type', 'field_name', 'time']
        db.delete_unique(u'm2m_history_manytomanyhistorycountscache', ['content_type_id', 'field_name', 'time'])

        # Deleting model 'ManyToManyHistoryCountsCache'
        db.delete_table(u'm2m_history_manytomanyhistorycountscache')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'm2m_history.manytomanyhistorycountscache': {
            'Meta': {'unique_together': "(('content_type', 'field_name', 'time'),)", 'object_name': 'ManyToManyHistoryCountsCache'},
            'added_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'removed_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        }
    }

    complete_apps = ['m2m_history']