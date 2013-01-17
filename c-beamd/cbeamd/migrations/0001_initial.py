# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'User'
        db.create_table('cbeamd_user', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('logintime', self.gf('django.db.models.fields.DateTimeField')()),
            ('logouttime', self.gf('django.db.models.fields.DateTimeField')()),
            ('eta', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('etatimestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('etd', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('etdtimestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('nickspell', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('reminder', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('remindertimestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('lastlocation', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('etasub', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('arrivesub', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('cbeamd', ['User'])

        # Adding model 'LTE'
        db.create_table('cbeamd_lte', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('day', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('eta', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('cbeamd', ['LTE'])

        # Adding model 'Mission'
        db.create_table('cbeamd_mission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('short_description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('due_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=3)),
        ))
        db.send_create_signal('cbeamd', ['Mission'])


    def backwards(self, orm):
        # Deleting model 'User'
        db.delete_table('cbeamd_user')

        # Deleting model 'LTE'
        db.delete_table('cbeamd_lte')

        # Deleting model 'Mission'
        db.delete_table('cbeamd_mission')


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
            'due_date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '200'})
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