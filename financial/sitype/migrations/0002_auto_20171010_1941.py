# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-10-10 11:41
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ortype', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ortype',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 10, 19, 41, 37, 585000)),
        ),
    ]