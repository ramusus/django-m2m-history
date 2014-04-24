# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ManyToManyHistoryVersion'
        db.create_table(u'm2m_history_manytomanyhistoryversion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='m2m_history_versions', to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.BigIntegerField')(db_index=True)),
            ('field_name', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('added_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('removed_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'm2m_history', ['ManyToManyHistoryVersion'])

        # Adding unique constraint on 'ManyToManyHistoryVersion', fields ['content_type', 'object_id', 'field_name', 'time']
        db.create_unique(u'm2m_history_manytomanyhistoryversion', ['content_type_id', 'object_id', 'field_name', 'time'])


    def backwards(self, orm):
        # Removing unique constraint on 'ManyToManyHistoryVersion', fields ['content_type', 'object_id', 'field_name', 'time']
        db.delete_unique(u'm2m_history_manytomanyhistoryversion', ['content_type_id', 'object_id', 'field_name', 'time'])

        # Deleting model 'ManyToManyHistoryVersion'
        db.delete_table(u'm2m_history_manytomanyhistoryversion')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'm2m_history.manytomanyhistoryversion': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'field_name', 'time'),)", 'object_name': 'ManyToManyHistoryVersion'},
            'added_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'m2m_history_versions'", 'to': u"orm['contenttypes.ContentType']"}),
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'removed_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        }
    }

    complete_apps = ['m2m_history']