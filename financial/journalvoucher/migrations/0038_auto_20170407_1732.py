# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-07 17:32
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wtax', '0003_auto_20170407_1732'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bankaccount', '0003_auto_20170407_1732'),
        ('product', '0003_auto_20170407_1732'),
        ('employee', '0004_auto_20170407_1732'),
        ('outputvat', '0003_auto_20170407_1732'),
        ('chartofaccount', '0009_auto_20170407_1732'),
        ('ataxcode', '0004_auto_20170407_1732'),
        ('vat', '0004_auto_20170407_1732'),
        ('department', '0018_auto_20170407_1732'),
        ('customer', '0006_auto_20170407_1732'),
        ('inputvat', '0004_auto_20170407_1732'),
        ('unit', '0009_auto_20170407_1732'),
        ('branch', '0011_auto_20170407_1732'),
        ('supplier', '0006_auto_20170407_1732'),
        ('journalvoucher', '0037_auto_20170407_1727'),
    ]

    operations = [
        migrations.CreateModel(
            name='Jvdetailbreakdown',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_counter', models.IntegerField()),
                ('datatype', models.CharField(blank=True, max_length=1, null=True)),
                ('jv_num', models.CharField(max_length=10)),
                ('jv_date', models.DateTimeField()),
                ('debitamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('creditamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('balancecode', models.CharField(blank=True, max_length=1, null=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('status', models.CharField(choices=[(b'A', b'Active'), (b'I', b'Inactive'), (b'C', b'Cancelled'), (b'O', b'Posted'), (b'P', b'Printed')], default=b'A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 32, 40, 529572))),
                ('postdate', models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 32, 40, 529774))),
                ('isdeleted', models.IntegerField(default=0)),
                ('customerbreakstatus', models.IntegerField(blank=True, null=True)),
                ('supplierbreakstatus', models.IntegerField(blank=True, null=True)),
                ('employeebreakstatus', models.IntegerField(blank=True, null=True)),
                ('ataxcode', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ataxcode_jvdetailbreakdown_id', to='ataxcode.Ataxcode')),
                ('bankaccount', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bankaccount_jvdetailbreakdown_id', to='bankaccount.Bankaccount')),
                ('branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branch_jvdetailbreakdown_id', to='branch.Branch')),
                ('chartofaccount', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chartofaccount_jvdetailbreakdown_id', to='chartofaccount.Chartofaccount')),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='customer_jvdetailbreakdown_id', to='customer.Customer')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='department_jvdetailbreakdown_id', to='department.Department')),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='employee_jvdetailbreakdown_id', to='employee.Employee')),
                ('enterby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='jvdetailbreakdown_enter', to=settings.AUTH_USER_MODEL)),
                ('inputvat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inputvat_jvdetailbreakdown_id', to='inputvat.Inputvat')),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'jvdetailbreakdown',
            },
        ),
        migrations.AlterField(
            model_name='jvdetail',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 32, 40, 525101)),
        ),
        migrations.AlterField(
            model_name='jvdetail',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 32, 40, 525318)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdowntemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 32, 40, 536200)),
        ),
        migrations.AlterField(
            model_name='jvdetailbreakdowntemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 32, 40, 536379)),
        ),
        migrations.AlterField(
            model_name='jvdetailtemp',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 32, 40, 533487)),
        ),
        migrations.AlterField(
            model_name='jvdetailtemp',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 32, 40, 533577)),
        ),
        migrations.AlterField(
            model_name='jvmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 32, 40, 520154)),
        ),
        migrations.AlterField(
            model_name='jvmain',
            name='postdate',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 7, 17, 32, 40, 520250)),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdown',
            name='jvdetail',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jvdetail_jvdetailbreakdown_id', to='journalvoucher.Jvdetail'),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdown',
            name='jvmain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jvmain_jvdetailbreakdown_id', to='journalvoucher.Jvmain'),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdown',
            name='modifyby',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='jvdetailbreakdown_modify', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdown',
            name='outputvat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outputvat_jvdetailbreakdown_id', to='outputvat.Outputvat'),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdown',
            name='postby',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='jvdetailbreakdown_post', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdown',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_jvdetailbreakdown_id', to='product.Product'),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdown',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supplier_jvdetailbreakdown_id', to='supplier.Supplier'),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdown',
            name='unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='unit_jvdetailbreakdown_id', to='unit.Unit'),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdown',
            name='vat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vat_jvdetailbreakdown_id', to='vat.Vat'),
        ),
        migrations.AddField(
            model_name='jvdetailbreakdown',
            name='wtax',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wtax_jvdetailbreakdown_id', to='wtax.Wtax'),
        ),
    ]