# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-01-31 09:41
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vat', '0022_auto_20171107_2251'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vat',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 1, 31, 17, 40, 41, 751000)),
        ),
    ]
