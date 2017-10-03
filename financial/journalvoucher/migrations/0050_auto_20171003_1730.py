# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-10-03 09:30
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journalvoucher', '0049_auto_20171002_1751'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='jvmain',
            options={'ordering': ['-pk'], 'permissions': (('view_journalvoucher', 'Can view journalvoucher'), ('approve_assignedjv', 'Can approve assigned jv'), ('approve_alljv', 'Can approve all jv'))},
        ),
        migrations.AlterField(
            model_name='jvdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 3, 17, 30, 8, 844000)),
        ),
        migrations.AlterField(
            model_name='jvdetail',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 3, 17, 30, 8, 844000)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdown',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 3, 17, 30, 8, 849000)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdown',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 3, 17, 30, 8, 849000)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdowntemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 3, 17, 30, 8, 854000)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdowntemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 3, 17, 30, 8, 854000)),
        ),
        migrations.AlterField(
            model_name='jvdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 3, 17, 30, 8, 852000)),
        ),
        migrations.AlterField(
            model_name='jvdetailtemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 3, 17, 30, 8, 852000)),
        ),
        migrations.AlterField(
            model_name='jvmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 3, 17, 30, 8, 840000)),
        ),
        migrations.AlterField(
            model_name='jvmain',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 3, 17, 30, 8, 840000)),
        ),
    ]
