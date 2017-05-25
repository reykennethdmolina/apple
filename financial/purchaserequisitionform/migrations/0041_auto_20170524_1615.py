# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-05-24 08:15
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchaserequisitionform', '0040_auto_20170524_1444'),
    ]

    operations = [
        migrations.AddField(
            model_name='prfdetail',
            name='negocost',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='prfdetail',
            name='uc_cost',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='prfdetailtemp',
            name='negocost',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='prfdetailtemp',
            name='uc_cost',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True),
        ),
        migrations.AlterField(
            model_name='prfdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 24, 16, 15, 44, 43000)),
        ),
        migrations.AlterField(
            model_name='prfdetail',
            name='postdate',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2017, 5, 24, 16, 15, 44, 43000), null=True),
        ),
        migrations.AlterField(
            model_name='prfdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 24, 16, 15, 44, 49000)),
        ),
        migrations.AlterField(
            model_name='prfmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 24, 16, 15, 44, 35000)),
        ),
    ]
