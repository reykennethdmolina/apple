# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-03 20:49
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('department', '0016_auto_20170327_1338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 3, 20, 49, 3, 714000)),
        ),
    ]