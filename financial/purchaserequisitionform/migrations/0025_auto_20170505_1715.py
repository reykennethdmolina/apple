# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-05-05 17:15
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchaserequisitionform', '0024_auto_20170504_1635'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rfprftransaction',
            old_name='status',
            new_name='status',
        ),
        migrations.AddField(
            model_name='prfdetail',
            name='fxrate',
            field=models.DecimalField(blank=True, decimal_places=5, default=0.0, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='prfdetailtemp',
            name='fxrate',
            field=models.DecimalField(blank=True, decimal_places=5, default=0.0, max_digits=18, null=True),
        ),
        migrations.AlterField(
            model_name='prfdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 5, 17, 14, 46, 643000)),
        ),
        migrations.AlterField(
            model_name='prfdetail',
            name='postdate',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2017, 5, 5, 17, 14, 46, 643000), null=True),
        ),
        migrations.AlterField(
            model_name='prfdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 5, 17, 14, 46, 645000)),
        ),
        migrations.AlterField(
            model_name='prfmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 5, 17, 14, 46, 631000)),
        ),
    ]