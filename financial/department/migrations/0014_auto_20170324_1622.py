# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-03-24 16:22
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('department', '0013_auto_20170324_1620'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 3, 24, 16, 22, 44, 107352)),
        ),
    ]