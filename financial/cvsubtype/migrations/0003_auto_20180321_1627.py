# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-03-21 08:27
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cvsubtype', '0002_auto_20170913_1729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cvsubtype',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 3, 21, 16, 27, 41, 17000)),
        ),
    ]
