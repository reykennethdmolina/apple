# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-01-23 06:05
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryitem', '0011_auto_20170420_1110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryitem',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 1, 23, 14, 5, 9, 283000)),
        ),
    ]