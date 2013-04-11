# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Mission.assigned_to'
        db.delete_column('cbeamd_mission', 'assigned_to_id')

        # Adding M2M table for field assigned_to on 'Mission'
        db.create_table('cbeamd_mission_assigned_to', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mission', models.ForeignKey(orm['cbeamd.mission'], null=False)),
            ('user', models.ForeignKey(orm['cbeamd.user'], null=False))
        ))
        db.create_unique('cbeamd_mission_assigned_to', ['mission_id', 'user_id'])


    def backwards(self, orm):
        # Adding field 'Mission.assigned_to'
        db.add_column('cbeamd_mission', 'assigned_to',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cbeamd.User'], unique=True, null=True),
                      keep_default=False)

        # Removing M2M table for field assigned_to on 'Mission'
        db.delete_table('cbeamd_mission_assigned_to')


    models = {
        'cbeamd.event': {
            'Meta': {'object_name': 'Event'},
            'end': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'uid': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'cbeamd.lte': {
            'Meta': {'object_name': 'LTE'},
            'day': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'eta': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'cbeamd.mission': {
            'Meta': {'object_name': 'Mission'},
            'ap': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'assigned_to': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['cbeamd.User']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'due_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '3', 'blank': 'True'}),
            'repeat_after_days': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'cbeamd.missionlog': {
            'Meta': {'object_name': 'MissionLog'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mission': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cbeamd.Mission']", 'unique': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cbeamd.User']", 'unique': 'True'})
        },
        'cbeamd.subscription': {
            'Meta': {'object_name': 'Subscription'},
            'regid': ('django.db.models.fields.CharField', [], {'max_length': "'2000'"}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cbeamd.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cbeamd.user': {
            'Meta': {'object_name': 'User'},
            'ap': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'arrivesub': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'autologout': ('django.db.models.fields.IntegerField', [], {'default': '600'}),
            'eta': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'etasub': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'etatimestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'etd': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'etdtimestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastlocation': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'logintime': ('django.db.models.fields.DateTimeField', [], {}),
            'logouttime': ('django.db.models.fields.DateTimeField', [], {}),
            'nickspell': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'reminder': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'remindertimestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'wlanlogin': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'cbeamd.userstatsentry': {
            'Meta': {'object_name': 'UserStatsEntry'},
            'etacount': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'usercount': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['cbeamd']