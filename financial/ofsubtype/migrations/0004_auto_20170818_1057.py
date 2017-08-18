# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-08-18 02:57
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('oftype', '0005_auto_20170818_1057'),
        ('ofsubtype', '0003_auto_20170818_1035'),
    ]

    operations = [
        migrations.AddField(
            model_name='ofsubtype',
            name='oftype',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ofsubtype_oftype', to='oftype.Oftype'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='ofsubtype',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 18, 10, 56, 55, 361000)),
        ),
    ]