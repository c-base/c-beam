# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Subscription'
        db.create_table('cbeamd_subscription', (
            ('regid', self.gf('django.db.models.fields.CharField')(max_length='2000')),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cbeamd.User'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cbeamd', ['Subscription'])


    def backwards(self, orm):
        # Deleting model 'Subscription'
        db.delete_table('cbeamd_subscription')


    models = {
        'cbeamd.lte': {
            'Meta': {'object_name': 'LTE'},
            'day': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'eta': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'cbeamd.mission': {
            'Meta': {'object_name': 'Mission'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'due_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '3', 'blank': 'True'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'cbeamd.subscription': {
            'Meta': {'object_name': 'Subscription'},
            'regid': ('django.db.models.fields.CharField', [], {'max_length': "'2000'"}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cbeamd.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cbeamd.user': {
            'Meta': {'object_name': 'User'},
            'arrivesub': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'username': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['cbeamd']