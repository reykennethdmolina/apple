# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-20 10:38
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryitem', '0009_auto_20170419_1525'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryitem',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 10, 38, 16, 315000)),
        ),
    ]
