# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-03-24 16:16
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('department', '0011_auto_20170323_1109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 3, 24, 16, 16, 46, 991027)),
        ),
    ]