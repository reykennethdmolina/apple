# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-08-18 02:57
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oftype', '0004_auto_20170718_1032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oftype',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 18, 10, 56, 55, 363000)),
        ),
    ]
