# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-07-18 10:19
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # ('oftype', '0002_auto_20170718_1019'),
        ('operationalfund', '0009_auto_20170718_1018'),
    ]

    operations = [
        # migrations.AddField(
        #     model_name='ofmain',
        #     name='oftype',
        #     field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ofmain_oftype_id', to='oftype.Oftype'),
        # ),
        migrations.AlterField(
            model_name='ofmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 7, 18, 10, 19, 21, 757000)),
        ),
    ]
