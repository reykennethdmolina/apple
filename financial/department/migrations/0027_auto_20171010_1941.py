# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-10-10 11:41
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('department', '0026_auto_20170807_1731'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 10, 19, 41, 37, 653000)),
        ),
    ]