# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-03 20:49
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('branch', '0009_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='branch',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 3, 20, 49, 3, 634000)),
        ),
    ]