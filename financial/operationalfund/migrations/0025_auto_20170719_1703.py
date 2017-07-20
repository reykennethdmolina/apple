# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-07-19 17:03
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operationalfund', '0024_auto_20170719_1702'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ofmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 7, 19, 17, 3, 13, 180000)),
        ),
        migrations.AlterField(
            model_name='ofmain',
            name='ofstatus',
            field=models.CharField(choices=[('F', 'For Approval'), ('A', 'Approved'), ('D', 'Disapproved'), ('I', 'In Process'), ('R', 'Released')], default='F', max_length=1),
        ),
    ]