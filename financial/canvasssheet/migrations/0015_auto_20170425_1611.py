# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-25 16:11
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('canvasssheet', '0014_auto_20170425_1509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='csdata',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 25, 16, 11, 32, 981000)),
        ),
        migrations.AlterField(
            model_name='csdetail',
            name='csmain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='csdetail_csmain_id', to='canvasssheet.Csmain'),
        ),
        migrations.AlterField(
            model_name='csdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 25, 16, 11, 32, 982000)),
        ),
        migrations.AlterField(
            model_name='csdetail',
            name='postdate',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2017, 4, 25, 16, 11, 32, 982000), null=True),
        ),
        migrations.AlterField(
            model_name='csdetailtemp',
            name='csmain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='csdetailtemp_csmain_id', to='canvasssheet.Csmain'),
        ),
        migrations.AlterField(
            model_name='csdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 25, 16, 11, 32, 986000)),
        ),
        migrations.AlterField(
            model_name='csdetailtemp',
            name='postdate',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2017, 4, 25, 16, 11, 32, 986000), null=True),
        ),
        migrations.AlterField(
            model_name='csmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 25, 16, 11, 32, 975000)),
        ),
    ]