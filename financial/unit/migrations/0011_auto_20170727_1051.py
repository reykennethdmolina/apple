# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-07-27 02:51
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unit', '0010_auto_20170727_1046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 7, 27, 10, 51, 26, 930000)),
        ),
    ]