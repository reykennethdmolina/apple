# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-05-15 11:52
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subledger', '0014_auto_20180515_1333'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='logs_subledger',
            name='particulars',
        ),
        migrations.RemoveField(
            model_name='subledger',
            name='particulars',
        ),
    ]