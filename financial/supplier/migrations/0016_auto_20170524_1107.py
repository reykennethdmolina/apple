# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-05-24 03:07
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0015_auto_20170511_1725'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplier',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 24, 11, 7, 21, 561000)),
        ),
    ]