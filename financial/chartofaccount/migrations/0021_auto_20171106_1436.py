# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-11-06 06:36
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chartofaccount', '0020_auto_20171010_1941'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chartofaccount',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 6, 14, 35, 52, 10000)),
        ),
    ]