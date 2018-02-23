# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-02-23 01:32
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('debitcreditmemo', '0012_auto_20180123_1405'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dcdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 23, 9, 32, 48, 694000)),
        ),
        migrations.AlterField(
            model_name='dcdetail',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 23, 9, 32, 48, 694000)),
        ),
        migrations.AlterField(
            model_name='dcdetailbreakdown',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 23, 9, 32, 48, 697000)),
        ),
        migrations.AlterField(
            model_name='dcdetailbreakdown',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 23, 9, 32, 48, 697000)),
        ),
        migrations.AlterField(
            model_name='dcdetailbreakdowntemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 23, 9, 32, 48, 701000)),
        ),
        migrations.AlterField(
            model_name='dcdetailbreakdowntemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 23, 9, 32, 48, 701000)),
        ),
        migrations.AlterField(
            model_name='dcdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 23, 9, 32, 48, 699000)),
        ),
        migrations.AlterField(
            model_name='dcdetailtemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 23, 9, 32, 48, 699000)),
        ),
        migrations.AlterField(
            model_name='dcmain',
            name='dcsubtype',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dcmain_subtype_id', to='debitcreditmemosubtype.Debitcreditmemosubtype'),
        ),
        migrations.AlterField(
            model_name='dcmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 23, 9, 32, 48, 691000)),
        ),
    ]
