# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-03-22 03:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0005_auto_20180321_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agent',
            name='modifydate',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
