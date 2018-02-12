# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-02-05 08:06
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budgetapproverlevels', '0008_auto_20180205_1543'),
    ]

    operations = [
        migrations.AlterField(
            model_name='budgetapproverlevels',
            name='level',
            field=models.IntegerField(choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')], unique=True),
        ),
        migrations.AlterField(
            model_name='budgetapproverlevels',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 5, 16, 5, 13, 968000)),
        ),
    ]