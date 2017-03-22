# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-03-22 11:46
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('unitofmeasure', '0002_auto_20170322_1146'),
        ('inventoryitemclass', '0003_auto_20170322_1146'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Inventoryitem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True)),
                ('description', models.CharField(max_length=250)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 3, 22, 11, 46, 23, 877989))),
                ('isdeleted', models.IntegerField(default=0)),
                ('enterby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='inventoryitem_enter', to=settings.AUTH_USER_MODEL)),
                ('inventoryitemclass', models.ForeignKey(default='1', on_delete=django.db.models.deletion.CASCADE, related_name='invitem_inventoryitemclass_id', to='inventoryitemclass.Inventoryitemclass')),
                ('modifyby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='inventoryitem_modify', to=settings.AUTH_USER_MODEL)),
                ('unitofmeasure', models.ForeignKey(default='1', on_delete=django.db.models.deletion.CASCADE, related_name='invitem_unitofmeasure_id', to='unitofmeasure.Unitofmeasure')),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'inventoryitem',
                'permissions': (('view_inventoryitem', 'Can view inventoryitem'),),
            },
        ),
    ]