# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-11-26 11:03
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reportdashboard', '0004_auto_20181126_1039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportmaintenance',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 11, 26, 11, 3, 27, 246000)),
        ),
        migrations.AlterField(
            model_name='reportmaintenancemodule',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 11, 26, 11, 3, 27, 246000)),
        ),
    ]