# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-01-11 06:32
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locationcategory', '0002_auto_20180110_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='locationcategory',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 1, 11, 14, 32, 24, 404000)),
        ),
    ]