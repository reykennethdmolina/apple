# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-06-20 03:07
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0016_auto_20170524_1107'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplier',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 6, 20, 11, 7, 20, 747000)),
        ),
    ]
