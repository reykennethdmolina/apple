# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-01-10 07:33
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('productgroupcategory', '0004_auto_20180110_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productgroupcategory',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productgroupcategory_category', to='locationcategory.Locationcategory'),
        ),
        migrations.AlterField(
            model_name='productgroupcategory',
            name='chartofaccount',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productgroupcategory_chartofaccount', to='chartofaccount.Chartofaccount'),
        ),
        migrations.AlterField(
            model_name='productgroupcategory',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 1, 10, 15, 33, 50, 796000)),
        ),
        migrations.AlterField(
            model_name='productgroupcategory',
            name='productgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productgroupcategory_product', to='productgroup.Productgroup'),
        ),
    ]
