# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-10-19 03:34
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0017_auto_20171019_1056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 19, 11, 33, 46, 8000)),
        ),
    ]