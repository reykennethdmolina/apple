# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-08-23 08:52
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operationalfund', '0042_auto_20170823_1636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ofdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 714000)),
        ),
        migrations.AlterField(
            model_name='ofdetail',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 714000)),
        ),
        migrations.AlterField(
            model_name='ofdetailbreakdown',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 721000)),
        ),
        migrations.AlterField(
            model_name='ofdetailbreakdown',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 721000)),
        ),
        migrations.AlterField(
            model_name='ofdetailbreakdowntemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 734000)),
        ),
        migrations.AlterField(
            model_name='ofdetailbreakdowntemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 734000)),
        ),
        migrations.AlterField(
            model_name='ofdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 730000)),
        ),
        migrations.AlterField(
            model_name='ofdetailtemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 730000)),
        ),
        migrations.AlterField(
            model_name='ofitem',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 708000)),
        ),
        migrations.AlterField(
            model_name='ofitem',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 708000)),
        ),
        migrations.AlterField(
            model_name='ofitemtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 726000)),
        ),
        migrations.AlterField(
            model_name='ofitemtemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 726000)),
        ),
        migrations.AlterField(
            model_name='ofmain',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True),
        ),
        migrations.AlterField(
            model_name='ofmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 23, 16, 52, 36, 702000)),
        ),
    ]