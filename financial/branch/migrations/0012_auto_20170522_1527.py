# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-05-22 07:27
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('branch', '0011_auto_20170407_1732'),
    ]

    operations = [
        migrations.AlterField(
            model_name='branch',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 22, 15, 26, 56, 205000)),
        ),
    ]