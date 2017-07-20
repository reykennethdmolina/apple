# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-06-19 05:05
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bank', '0002_auto_20170619_1305'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bankbranchdisburse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('branch', models.CharField(max_length=10, unique=True)),
                ('address', models.CharField(blank=True, max_length=250, null=True)),
                ('telephone1', models.CharField(blank=True, max_length=75, null=True)),
                ('telephone2', models.CharField(blank=True, max_length=75, null=True)),
                ('contact_person', models.CharField(blank=True, max_length=250, null=True)),
                ('contact_position', models.CharField(blank=True, max_length=250, null=True)),
                ('remarks', models.CharField(blank=True, max_length=250, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 6, 19, 13, 5, 49, 499000))),
                ('isdeleted', models.IntegerField(default=0)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_bankbranchdisburse_id', to='bank.Bank')),
                ('enterby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='bankbranchdisburse_enter', to=settings.AUTH_USER_MODEL)),
                ('modifyby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='bankbranchdisburse_modify', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'bankbranchdisburse',
                'permissions': (('view_bankbranchdisburse', 'Can view bankbranchdisburse'),),
            },
        ),
    ]