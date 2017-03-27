# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-03-27 13:46
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryitem', '0006_auto_20170327_1346'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('requisitionform', '0008_auto_20170327_1346'),
        ('purchaserequisitionform', '0003_auto_20170327_1341'),
    ]

    operations = [
        migrations.CreateModel(
            name='Prfdetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invitem_code', models.CharField(max_length=25)),
                ('invitem_name', models.CharField(max_length=250)),
                ('item_counter', models.IntegerField()),
                ('quantity', models.IntegerField()),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 3, 27, 13, 46, 35, 426000))),
                ('postdate', models.DateTimeField(default=datetime.datetime(2017, 3, 27, 13, 46, 35, 426000))),
                ('isdeleted', models.IntegerField(default=0)),
                ('enterby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='prfdetail_enter', to=settings.AUTH_USER_MODEL)),
                ('invitem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prfdetail_invitem_id', to='inventoryitem.Inventoryitem')),
                ('modifyby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='prfdetail_modify', to=settings.AUTH_USER_MODEL)),
                ('postby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='prfdetail_post', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'prfdetail',
            },
        ),
        migrations.CreateModel(
            name='Prfdetailtemp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invitem_code', models.CharField(max_length=25)),
                ('invitem_name', models.CharField(max_length=250)),
                ('item_counter', models.IntegerField()),
                ('quantity', models.IntegerField()),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 3, 27, 13, 46, 35, 428000))),
                ('postdate', models.DateTimeField(blank=True, null=True)),
                ('isdeleted', models.IntegerField(default=0)),
                ('secretkey', models.CharField(max_length=255)),
                ('enterby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='prfdetailtemp_enter', to=settings.AUTH_USER_MODEL)),
                ('invitem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='temp_prfdetail_invitem_id', to='inventoryitem.Inventoryitem')),
                ('modifyby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='prfdetailtemp_modify', to=settings.AUTH_USER_MODEL)),
                ('postby', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prfdetailtemp_post', to=settings.AUTH_USER_MODEL)),
                ('prfdetail', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='temp_prfdetail_id', to='purchaserequisitionform.Prfdetail')),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'prfdetailtemp',
            },
        ),
        migrations.AlterField(
            model_name='prfmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 3, 27, 13, 46, 35, 423000)),
        ),
        migrations.AddField(
            model_name='prfdetailtemp',
            name='prfmain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='temp_prfmain_id', to='purchaserequisitionform.Prfmain'),
        ),
        migrations.AddField(
            model_name='prfdetailtemp',
            name='rfdetail',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='temp_rfdetail_id', to='requisitionform.Rfdetail'),
        ),
        migrations.AddField(
            model_name='prfdetail',
            name='prfmain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prfmain_id', to='purchaserequisitionform.Prfmain'),
        ),
        migrations.AddField(
            model_name='prfdetail',
            name='rfdetail',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rfdetail_prfdetail', to='requisitionform.Rfdetail'),
        ),
    ]
