# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-11-07 14:51
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wtax', '0013_auto_20171107_2251'),
        ('customer', '0015_auto_20171107_2251'),
        ('collector', '0004_auto_20171107_2251'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('supplier', '0032_auto_20171107_2251'),
        ('bankaccount', '0016_auto_20171107_2251'),
        ('bank', '0005_auto_20171107_2251'),
        ('product', '0013_auto_20171107_2251'),
        ('outputvat', '0011_auto_20171107_2251'),
        ('chartofaccount', '0025_auto_20171107_2251'),
        ('arsubtype', '0002_auto_20171107_2251'),
        ('unit', '0017_auto_20171107_2251'),
        ('vat', '0022_auto_20171107_2251'),
        ('bankbranch', '0006_auto_20171107_2251'),
        ('inputvat', '0012_auto_20171107_2251'),
        ('department', '0031_auto_20171107_2251'),
        ('ataxcode', '0019_auto_20171107_2251'),
        ('paytype', '0005_auto_20171107_2251'),
        ('branch', '0025_auto_20171107_2251'),
        ('artype', '0005_auto_20171107_2251'),
        ('employee', '0021_auto_20171107_2251'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ardetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_counter', models.IntegerField()),
                ('ar_num', models.CharField(max_length=10)),
                ('ar_date', models.DateTimeField()),
                ('debitamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('creditamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('balancecode', models.CharField(blank=True, max_length=1, null=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 11, 7, 22, 50, 59, 597000))),
                ('postdate', models.DateTimeField(blank=True, null=True)),
                ('isdeleted', models.IntegerField(default=0)),
                ('customerbreakstatus', models.IntegerField(blank=True, null=True)),
                ('supplierbreakstatus', models.IntegerField(blank=True, null=True)),
                ('employeebreakstatus', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'ardetail',
            },
        ),
        migrations.CreateModel(
            name='Ardetailbreakdown',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_counter', models.IntegerField()),
                ('datatype', models.CharField(blank=True, max_length=1, null=True)),
                ('ar_num', models.CharField(max_length=10)),
                ('ar_date', models.DateTimeField()),
                ('particular', models.TextField(blank=True, null=True)),
                ('debitamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('creditamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('balancecode', models.CharField(blank=True, max_length=1, null=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 11, 7, 22, 50, 59, 602000))),
                ('postdate', models.DateTimeField(blank=True, null=True)),
                ('isdeleted', models.IntegerField(default=0)),
                ('customerbreakstatus', models.IntegerField(blank=True, null=True)),
                ('supplierbreakstatus', models.IntegerField(blank=True, null=True)),
                ('employeebreakstatus', models.IntegerField(blank=True, null=True)),
                ('ardetail', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ardetail_ardetailbreakdown_id', to='acknowledgementreceipt.Ardetail')),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'ardetailbreakdown',
            },
        ),
        migrations.CreateModel(
            name='Ardetailbreakdowntemp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_counter', models.IntegerField()),
                ('secretkey', models.CharField(blank=True, max_length=255, null=True)),
                ('ardetailtemp', models.CharField(blank=True, max_length=10, null=True)),
                ('datatype', models.CharField(blank=True, max_length=1, null=True)),
                ('armain', models.CharField(blank=True, max_length=10, null=True)),
                ('ardetail', models.CharField(blank=True, max_length=10, null=True)),
                ('ardetailbreakdown', models.CharField(blank=True, max_length=10, null=True)),
                ('ar_num', models.CharField(max_length=10)),
                ('ar_date', models.DateTimeField(blank=True, null=True)),
                ('chartofaccount', models.IntegerField(blank=True, null=True)),
                ('particular', models.TextField(blank=True, null=True)),
                ('bankaccount', models.IntegerField(blank=True, null=True)),
                ('department', models.IntegerField(blank=True, null=True)),
                ('employee', models.IntegerField(blank=True, null=True)),
                ('supplier', models.IntegerField(blank=True, null=True)),
                ('customer', models.IntegerField(blank=True, null=True)),
                ('unit', models.IntegerField(blank=True, null=True)),
                ('branch', models.IntegerField(blank=True, null=True)),
                ('product', models.IntegerField(blank=True, null=True)),
                ('inputvat', models.IntegerField(blank=True, null=True)),
                ('outputvat', models.IntegerField(blank=True, null=True)),
                ('vat', models.IntegerField(blank=True, null=True)),
                ('wtax', models.IntegerField(blank=True, null=True)),
                ('ataxcode', models.IntegerField(blank=True, null=True)),
                ('debitamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('creditamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('balancecode', models.CharField(blank=True, max_length=1, null=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('customerbreakstatus', models.IntegerField(blank=True, null=True)),
                ('supplierbreakstatus', models.IntegerField(blank=True, null=True)),
                ('employeebreakstatus', models.IntegerField(blank=True, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 11, 7, 22, 50, 59, 607000))),
                ('postdate', models.DateTimeField(blank=True, null=True)),
                ('isdeleted', models.IntegerField(default=0)),
                ('enterby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ardetailbreakdowntemp_enter', to=settings.AUTH_USER_MODEL)),
                ('modifyby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ardetailbreakdowntemp_modify', to=settings.AUTH_USER_MODEL)),
                ('postby', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ardetailbreakdowntemp_post', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'ardetailbreakdowntemp',
            },
        ),
        migrations.CreateModel(
            name='Ardetailtemp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_counter', models.IntegerField()),
                ('secretkey', models.CharField(blank=True, max_length=255, null=True)),
                ('armain', models.CharField(blank=True, max_length=10, null=True)),
                ('ardetail', models.CharField(blank=True, max_length=10, null=True)),
                ('ar_num', models.CharField(max_length=10)),
                ('ar_date', models.DateTimeField(blank=True, null=True)),
                ('chartofaccount', models.IntegerField(blank=True, null=True)),
                ('bankaccount', models.IntegerField(blank=True, null=True)),
                ('department', models.IntegerField(blank=True, null=True)),
                ('employee', models.IntegerField(blank=True, null=True)),
                ('supplier', models.IntegerField(blank=True, null=True)),
                ('customer', models.IntegerField(blank=True, null=True)),
                ('unit', models.IntegerField(blank=True, null=True)),
                ('branch', models.IntegerField(blank=True, null=True)),
                ('product', models.IntegerField(blank=True, null=True)),
                ('inputvat', models.IntegerField(blank=True, null=True)),
                ('outputvat', models.IntegerField(blank=True, null=True)),
                ('vat', models.IntegerField(blank=True, null=True)),
                ('wtax', models.IntegerField(blank=True, null=True)),
                ('ataxcode', models.IntegerField(blank=True, null=True)),
                ('debitamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('creditamount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('balancecode', models.CharField(blank=True, max_length=1, null=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=18, null=True)),
                ('customerbreakstatus', models.IntegerField(blank=True, null=True)),
                ('supplierbreakstatus', models.IntegerField(blank=True, null=True)),
                ('employeebreakstatus', models.IntegerField(blank=True, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 11, 7, 22, 50, 59, 605000))),
                ('postdate', models.DateTimeField(blank=True, null=True)),
                ('isdeleted', models.IntegerField(default=0)),
                ('enterby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ardetailtemp_enter', to=settings.AUTH_USER_MODEL)),
                ('modifyby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ardetailtemp_modify', to=settings.AUTH_USER_MODEL)),
                ('postby', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ardetailtemp_post', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'ardetailtemp',
            },
        ),
        migrations.CreateModel(
            name='Aritem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_counter', models.IntegerField()),
                ('arnum', models.CharField(max_length=10)),
                ('ardate', models.DateTimeField()),
                ('num', models.CharField(blank=True, max_length=200, null=True)),
                ('authnum', models.CharField(blank=True, max_length=200, null=True)),
                ('date', models.DateTimeField(blank=True, null=True)),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=18)),
                ('remarks', models.CharField(blank=True, max_length=500, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 11, 7, 22, 50, 59, 593000))),
                ('postdate', models.DateTimeField(blank=True, null=True)),
                ('isdeleted', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'aritem',
            },
        ),
        migrations.CreateModel(
            name='Aritemtemp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_counter', models.IntegerField()),
                ('secretkey', models.CharField(blank=True, max_length=255, null=True)),
                ('armain', models.CharField(blank=True, max_length=10, null=True)),
                ('aritem', models.CharField(blank=True, max_length=10, null=True)),
                ('arnum', models.CharField(max_length=10)),
                ('ardate', models.DateTimeField(blank=True, null=True)),
                ('paytype', models.CharField(blank=True, max_length=10, null=True)),
                ('bank', models.CharField(blank=True, max_length=10, null=True)),
                ('bankbranch', models.CharField(blank=True, max_length=10, null=True)),
                ('num', models.CharField(blank=True, max_length=200, null=True)),
                ('authnum', models.CharField(blank=True, max_length=200, null=True)),
                ('date', models.DateTimeField(blank=True, null=True)),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=18)),
                ('remarks', models.CharField(blank=True, max_length=500, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 11, 7, 22, 50, 59, 595000))),
                ('postdate', models.DateTimeField(blank=True, null=True)),
                ('isdeleted', models.IntegerField(default=0)),
                ('enterby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='aritemtemp_enter', to=settings.AUTH_USER_MODEL)),
                ('modifyby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='aritemtemp_modify', to=settings.AUTH_USER_MODEL)),
                ('postby', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aritemtemp_post', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'aritemtemp',
            },
        ),
        migrations.CreateModel(
            name='Armain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arnum', models.CharField(max_length=10, unique=True)),
                ('ardate', models.DateField()),
                ('payor_code', models.CharField(max_length=25)),
                ('payor_name', models.CharField(max_length=250)),
                ('collector_code', models.CharField(max_length=25)),
                ('collector_name', models.CharField(max_length=250)),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=18)),
                ('amountinwords', models.CharField(blank=True, max_length=500, null=True)),
                ('particulars', models.TextField(blank=True, null=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('arstatus', models.CharField(choices=[('F', 'For Approval'), ('A', 'Approved'), ('D', 'Disapproved'), ('R', 'Released')], default='F', max_length=1)),
                ('approverresponse', models.CharField(blank=True, choices=[('A', 'Approved'), ('D', 'Disapproved')], max_length=1, null=True)),
                ('responsedate', models.DateTimeField(blank=True, null=True)),
                ('approverremarks', models.CharField(blank=True, max_length=250, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 11, 7, 22, 50, 59, 590000))),
                ('postdate', models.DateTimeField(blank=True, null=True)),
                ('releasedate', models.DateTimeField(blank=True, null=True)),
                ('isdeleted', models.IntegerField(default=0)),
                ('print_ctr', models.IntegerField(default=0)),
                ('actualapprover', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='armain_actual_approver', to=settings.AUTH_USER_MODEL)),
                ('arsubtype', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='armain_arsubtype_id', to='arsubtype.Arsubtype')),
                ('artype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='armain_artype_id', to='artype.Artype')),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='armain_branch_id', to='branch.Branch')),
                ('collector', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='armain_collector_id', to='collector.Collector')),
                ('designatedapprover', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='armain_designated_approver', to=settings.AUTH_USER_MODEL)),
                ('enterby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='armain_enter', to=settings.AUTH_USER_MODEL)),
                ('modifyby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='armain_modify', to=settings.AUTH_USER_MODEL)),
                ('payor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='armain_payor_id', to='employee.Employee')),
                ('postby', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='armain_post', to=settings.AUTH_USER_MODEL)),
                ('releaseby', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='armain_release', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'armain',
                'permissions': (('view_acknowledgementreceipt', 'Can view acknowledgement receipt'),),
            },
        ),
        migrations.AddField(
            model_name='aritem',
            name='armain',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aritem_armain_id', to='acknowledgementreceipt.Armain'),
        ),
        migrations.AddField(
            model_name='aritem',
            name='bank',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aritem_bank_id', to='bank.Bank'),
        ),
        migrations.AddField(
            model_name='aritem',
            name='bankbranch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aritem_bankbranch_id', to='bankbranch.Bankbranch'),
        ),
        migrations.AddField(
            model_name='aritem',
            name='enterby',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='aritem_enter', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='aritem',
            name='modifyby',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='aritem_modify', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='aritem',
            name='paytype',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aritem_paytype_id', to='paytype.Paytype'),
        ),
        migrations.AddField(
            model_name='aritem',
            name='postby',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aritem_post', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='armain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='armain_ardetailbreakdown_id', to='acknowledgementreceipt.Armain'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='ataxcode',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ataxcode_ardetailbreakdown_id', to='ataxcode.Ataxcode'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='bankaccount',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bankaccount_ardetailbreakdown_id', to='bankaccount.Bankaccount'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='branch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branch_ardetailbreakdown_id', to='branch.Branch'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='chartofaccount',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chartofaccount_ardetailbreakdown_id', to='chartofaccount.Chartofaccount'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='customer_ardetailbreakdown_id', to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='department_ardetailbreakdown_id', to='department.Department'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='employee_ardetailbreakdown_id', to='employee.Employee'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='enterby',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ardetailbreakdown_enter', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='inputvat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inputvat_ardetailbreakdown_id', to='inputvat.Inputvat'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='modifyby',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ardetailbreakdown_modify', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='outputvat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outputvat_ardetailbreakdown_id', to='outputvat.Outputvat'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='postby',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ardetailbreakdown_post', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_ardetailbreakdown_id', to='product.Product'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supplier_ardetailbreakdown_id', to='supplier.Supplier'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='unit_ardetailbreakdown_id', to='unit.Unit'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='vat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vat_ardetailbreakdown_id', to='vat.Vat'),
        ),
        migrations.AddField(
            model_name='ardetailbreakdown',
            name='wtax',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wtax_ardetailbreakdown_id', to='wtax.Wtax'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='armain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='armain_ardetail_id', to='acknowledgementreceipt.Armain'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='ataxcode',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ataxcode_ardetail_id', to='ataxcode.Ataxcode'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='bankaccount',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bankaccount_ardetail_id', to='bankaccount.Bankaccount'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='branch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branch_ardetail_id', to='branch.Branch'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='chartofaccount',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chartofaccount_ardetail_id', to='chartofaccount.Chartofaccount'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='customer_ardetail_id', to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='department_ardetail_id', to='department.Department'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='employee_ardetail_id', to='employee.Employee'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='enterby',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ardetail_enter', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='inputvat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inputvat_ardetail_id', to='inputvat.Inputvat'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='modifyby',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ardetail_modify', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='outputvat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outputvat_ardetail_id', to='outputvat.Outputvat'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='postby',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ardetail_post', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_ardetail_id', to='product.Product'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supplier_ardetail_id', to='supplier.Supplier'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='unit_ardetail_id', to='unit.Unit'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='vat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vat_ardetail_id', to='vat.Vat'),
        ),
        migrations.AddField(
            model_name='ardetail',
            name='wtax',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wtax_ardetail_id', to='wtax.Wtax'),
        ),
    ]