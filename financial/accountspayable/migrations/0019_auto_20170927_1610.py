# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-09-27 08:10
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apsubtype', '0002_auto_20170927_1610'),
        ('accountspayable', '0018_auto_20170926_1120'),
    ]

    operations = [
        migrations.AddField(
            model_name='apmain',
            name='apsubtype',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='apsubtype_apmain_id', to='apsubtype.Apsubtype'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='apdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 9, 27, 16, 10, 39, 403000)),
        ),
        migrations.AlterField(
            model_name='apdetail',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 9, 27, 16, 10, 39, 403000)),
        ),
        migrations.AlterField(
            model_name='apdetailbreakdown',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 9, 27, 16, 10, 39, 407000)),
        ),
        migrations.AlterField(
            model_name='apdetailbreakdown',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 9, 27, 16, 10, 39, 407000)),
        ),
        migrations.AlterField(
            model_name='apdetailbreakdowntemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 9, 27, 16, 10, 39, 413000)),
        ),
        migrations.AlterField(
            model_name='apdetailbreakdowntemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 9, 27, 16, 10, 39, 413000)),
        ),
        migrations.AlterField(
            model_name='apdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 9, 27, 16, 10, 39, 410000)),
        ),
        migrations.AlterField(
            model_name='apdetailtemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 9, 27, 16, 10, 39, 410000)),
        ),
        migrations.AlterField(
            model_name='apmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 9, 27, 16, 10, 39, 398000)),
        ),
    ]