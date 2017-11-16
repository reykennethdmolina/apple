# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-11-16 07:53
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0015_auto_20171107_2251'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='contactperson',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='contactposition',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 16, 15, 52, 47, 763000)),
        ),
    ]
