# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-11-06 11:15
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chartofaccount', '0021_auto_20171106_1436'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chartofaccount',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 6, 19, 14, 57, 421000)),
        ),
    ]
