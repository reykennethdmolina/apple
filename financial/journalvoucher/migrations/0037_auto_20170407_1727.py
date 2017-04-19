# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-07 17:27
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journalvoucher', '0036_auto_20170406_1115'),
    ]

    operations = [
        migrations.AddField(
            model_name='jvdetail',
            name='customerbreakstatus',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jvdetail',
            name='employeebreakstatus',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jvdetail',
            name='supplierbreakstatus',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdowntemp',
            name='customerbreakstatus',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdowntemp',
            name='employeebreakstatus',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdowntemp',
            name='supplierbreakstatus',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='jvdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 27, 11, 743141)),
        ),
        migrations.AlterField(
            model_name='jvdetail',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 27, 11, 743228)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdowntemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 27, 11, 748893)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdowntemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 27, 11, 748984)),
        ),
        migrations.AlterField(
            model_name='jvdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 27, 11, 746305)),
        ),
        migrations.AlterField(
            model_name='jvdetailtemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 27, 11, 746391)),
        ),
        migrations.AlterField(
            model_name='jvmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 27, 11, 740279)),
        ),
        migrations.AlterField(
            model_name='jvmain',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 27, 11, 740364)),
        ),
    ]