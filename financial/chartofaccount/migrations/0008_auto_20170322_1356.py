# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-03-22 13:56
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chartofaccount', '0007_auto_20170321_1255'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chartofaccount',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 3, 22, 13, 56, 46, 623939)),
        ),
    ]