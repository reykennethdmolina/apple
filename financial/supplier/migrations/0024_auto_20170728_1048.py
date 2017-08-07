# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-07-28 10:48
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bankbranchdisburse', '0007_auto_20170728_1048'),
        ('paytype', '0002_auto_20170728_1048'),
        ('bankaccount', '0007_auto_20170728_1048'),
        ('supplier', '0023_auto_20170728_1046'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='bankaccount',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supplier_bankaccount_id', to='bankaccount.Bankaccount'),
        ),
        migrations.AddField(
            model_name='supplier',
            name='bankbranchdisburse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supplier_bankbranchdisburse_id', to='bankbranchdisburse.Bankbranchdisburse'),
        ),
        migrations.AddField(
            model_name='supplier',
            name='paytype',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supplier_paytype_id', to='paytype.Paytype'),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 7, 28, 10, 48, 48, 444000)),
        ),
    ]