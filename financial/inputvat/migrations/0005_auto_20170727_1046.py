# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-07-27 02:46
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inputvat', '0004_auto_20170407_1732'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inputvat',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 7, 27, 10, 46, 19, 195000)),
        ),
    ]