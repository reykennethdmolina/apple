# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-19 15:25
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vat', '0005_auto_20170417_1005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vat',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 19, 15, 25, 13, 232000)),
        ),
    ]
