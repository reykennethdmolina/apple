# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-20 10:57
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canvasssheet', '0005_auto_20170420_1047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='csdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 10, 57, 20, 867000)),
        ),
        migrations.AlterField(
            model_name='csdetail',
            name='postdate',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2017, 4, 20, 10, 57, 20, 868000), null=True),
        ),
        migrations.AlterField(
            model_name='csdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 10, 57, 20, 870000)),
        ),
        migrations.AlterField(
            model_name='csdetailtemp',
            name='postdate',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2017, 4, 20, 10, 57, 20, 870000), null=True),
        ),
        migrations.AlterField(
            model_name='csmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 20, 10, 57, 20, 861000)),
        ),
    ]
