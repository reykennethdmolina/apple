# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-05-04 14:41
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('purchaserequisitionform', '0024_auto_20170504_1441'),
        ('requisitionform', '0030_auto_20170504_1358'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rfdetail',
            name='enterdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 4, 14, 13, 18, 867000)),
        ),
        migrations.AlterField(
            model_name='rfdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 4, 14, 13, 18, 868000)),
        ),
        migrations.AlterField(
            model_name='rfdetailtemp',
            name='enterdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 4, 14, 13, 18, 873000)),
        ),
        migrations.AlterField(
            model_name='rfdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 4, 14, 13, 18, 873000)),
        ),
        migrations.AlterField(
            model_name='rfmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 4, 14, 13, 18, 865000)),
        ),
    ]