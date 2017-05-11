# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-20 14:11
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journalvoucher', '0039_auto_20170420_1104'),
    ]

    operations = [
        migrations.AddField(
            model_name='jvdetailtemp',
            name='particular',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='jvdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 14, 11, 8, 368787)),
        ),
        migrations.AlterField(
            model_name='jvdetail',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 14, 11, 8, 368891)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdown',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 14, 11, 8, 373525)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdown',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 14, 11, 8, 373635)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdowntemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 14, 11, 8, 380239)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdowntemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 14, 11, 8, 380334)),
        ),
        migrations.AlterField(
            model_name='jvdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 14, 11, 8, 377524)),
        ),
        migrations.AlterField(
            model_name='jvdetailtemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 14, 11, 8, 377621)),
        ),
        migrations.AlterField(
            model_name='jvmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 14, 11, 8, 364915)),
        ),
        migrations.AlterField(
            model_name='jvmain',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 14, 11, 8, 365046)),
        ),
    ]