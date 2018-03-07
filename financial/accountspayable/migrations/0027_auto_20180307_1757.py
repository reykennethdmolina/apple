# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-03-07 09:57
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accountspayable', '0026_auto_20180110_1745'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 3, 7, 17, 57, 12, 917000)),
        ),
        migrations.AlterField(
            model_name='apdetail',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2018, 3, 7, 17, 57, 12, 918000)),
        ),
        migrations.AlterField(
            model_name='apdetailbreakdown',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 3, 7, 17, 57, 12, 920000)),
        ),
        migrations.AlterField(
            model_name='apdetailbreakdown',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2018, 3, 7, 17, 57, 12, 920000)),
        ),
        migrations.AlterField(
            model_name='apdetailbreakdowntemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 3, 7, 17, 57, 12, 924000)),
        ),
        migrations.AlterField(
            model_name='apdetailbreakdowntemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2018, 3, 7, 17, 57, 12, 924000)),
        ),
        migrations.AlterField(
            model_name='apdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 3, 7, 17, 57, 12, 922000)),
        ),
        migrations.AlterField(
            model_name='apdetailtemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2018, 3, 7, 17, 57, 12, 922000)),
        ),
        migrations.AlterField(
            model_name='apmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 3, 7, 17, 57, 12, 914000)),
        ),
    ]
