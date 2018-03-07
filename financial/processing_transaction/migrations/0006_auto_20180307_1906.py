# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-03-07 11:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accountspayable', '0028_auto_20180307_1906'),
        ('processing_transaction', '0005_auto_20180307_1757'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='apvcvtransaction',
            name='old_apmain',
        ),
        migrations.AddField(
            model_name='apvcvtransaction',
            name='new_apmain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='new_apmain_apvcvtransaction', to='accountspayable.Apmain'),
        ),
    ]