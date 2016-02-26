# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManyToManyHistoryVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.BigIntegerField(db_index=True)),
                ('field_name', models.CharField(max_length=50, db_index=True)),
                ('time', models.DateTimeField(db_index=True)),
                ('count', models.PositiveIntegerField(default=0)),
                ('added_count', models.PositiveIntegerField(default=0)),
                ('removed_count', models.PositiveIntegerField(default=0)),
                ('content_type', models.ForeignKey(related_name='m2m_history_versions', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='manytomanyhistoryversion',
            unique_together=set([('content_type', 'object_id', 'field_name', 'time')]),
        ),
    ]
