# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-02-09 02:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inputvattype', '0011_auto_20180209_1053'),
        ('inventoryitemtype', '0008_auto_20170327_1338'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryitemtype',
            name='inputvattype',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inventoryitemtype_inputvattype', to='inputvattype.Inputvattype'),
        ),
        migrations.AlterField(
            model_name='inventoryitemtype',
            name='modifydate',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]