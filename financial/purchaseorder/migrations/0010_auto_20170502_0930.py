# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-05-02 09:30
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('purchaserequisitionform', '0018_auto_20170502_0930'),
        ('purchaseorder', '0009_auto_20170421_1351'),
    ]

    operations = [
        migrations.CreateModel(
            name='Podata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('secretkey', models.CharField(max_length=255)),
                ('isdeleted', models.IntegerField(default=0)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 5, 2, 9, 30, 13, 657000))),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'podata',
            },
        ),
        migrations.AlterField(
            model_name='podetail',
            name='enterdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 2, 9, 30, 13, 652000)),
        ),
        migrations.AlterField(
            model_name='podetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 2, 9, 30, 13, 652000)),
        ),
        migrations.AlterField(
            model_name='podetailtemp',
            name='enterdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 2, 9, 30, 13, 655000)),
        ),
        migrations.AlterField(
            model_name='podetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 2, 9, 30, 13, 655000)),
        ),
        migrations.AlterField(
            model_name='pomain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 2, 9, 30, 13, 649000)),
        ),
        migrations.AddField(
            model_name='podata',
            name='pomain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='podata_pomain_id', to='purchaseorder.Pomain'),
        ),
        migrations.AddField(
            model_name='podata',
            name='prfmain',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='podata_prfmain_id', to='purchaserequisitionform.Prfmain'),
        ),
    ]