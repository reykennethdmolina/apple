# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-05-04 14:46
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0007_auto_20170420_1342'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='fxrate',
            field=models.DecimalField(blank=True, decimal_places=5, default=0.0, max_digits=18, null=True),
        ),
        migrations.AlterField(
            model_name='currency',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 4, 14, 46, 9, 788000)),
        ),
    ]