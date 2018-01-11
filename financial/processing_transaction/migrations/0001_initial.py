# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-12-20 05:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('purchaseorder', '0023_auto_20171220_1316'),
        ('accountspayable', '0022_auto_20171220_1316'),
        ('checkvoucher', '0017_auto_20171220_1316'),
    ]

    operations = [
        migrations.CreateModel(
            name='Apvcvtransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cvamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('apmain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='apmain_apvcvtransaction', to='accountspayable.Apmain')),
                ('cvmain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cvmain_apvcvtransaction', to='checkvoucher.Cvmain')),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'apvcvtransaction',
            },
        ),
        migrations.CreateModel(
            name='Poapvtransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('apamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('apmain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='apmain_poapvtransaction', to='accountspayable.Apmain')),
                ('pomain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pomain_poapvtransaction', to='purchaseorder.Pomain')),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'poapvtransaction',
            },
        ),
    ]