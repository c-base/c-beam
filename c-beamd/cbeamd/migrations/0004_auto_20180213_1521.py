# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-13 14:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cbeamd', '0003_auto_20160116_0247'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='rfid',
            field=models.CharField(default='', max_length=200),
        ),
    ]