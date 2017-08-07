# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-07-27 02:37
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accountspayable', '0002_auto_20170704_1154'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='apmain',
            name='aptype',
        ),
        migrations.AddField(
            model_name='apmain',
            name='apprefix',
            field=models.CharField(default='AP', max_length=5),
        ),
        migrations.AlterField(
            model_name='apmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 7, 27, 10, 37, 8, 112000)),
        ),
    ]