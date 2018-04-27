# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-04-19 09:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('purchaseorder', '0032_auto_20180419_1652'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pomain',
            name='creditterm',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pomain_creditterm_id', to='creditterm.Creditterm'),
        ),
    ]