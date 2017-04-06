# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-04 20:11
from __future__ import unicode_literals

import datetime
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryitem', '0007_auto_20170404_2011'),
        ('supplier', '0004_auto_20170404_2011'),
        ('canvasssheet', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cshistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetransaction', models.DateTimeField(blank=True, null=True)),
                ('price', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('processingdate', models.IntegerField(validators=[django.core.validators.MaxValueValidator(9), django.core.validators.MinValueValidator(0)])),
                ('invitem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cshistory_invitem_id', to='inventoryitem.Inventoryitem')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cshistory_supplier_id', to='supplier.Supplier')),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'cshistory',
            },
        ),
        migrations.AlterField(
            model_name='csmain',
            name='cstype',
            field=models.CharField(choices=[('REGULAR', 'REGULAR')], default='REGULAR', max_length=10),
        ),
        migrations.AlterField(
            model_name='csmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 4, 20, 11, 10, 799000)),
        ),
    ]