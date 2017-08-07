# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-07-27 10:32
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bankaccounttype', '0002_auto_20170727_1032'),
        ('supplier', '0020_auto_20170726_1240'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='bankaccountname',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='supplier',
            name='bankaccountnumber',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='supplier',
            name='bankaccounttype',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supplier_bankaccounttype_id', to='bankaccounttype.Bankaccounttype'),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 7, 27, 10, 32, 51, 880000)),
        ),
    ]