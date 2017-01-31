# from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
import datetime


# class Jvmain(models.Model):
#     id = models.BigIntegerField(primary_key=True)
#     jv_num = models.CharField(unique=True, max_length=10)
#     jv_date = models.DateTimeField()
#     jvtype_id = models.ForeignKey('jvtype.Jvtype', related_name='jvtype_jvmain_id', null=True, blank=True)
#     refnum = models.CharField(max_length=150, blank=True, null=True)
#     department = models.ForeignKey('department.Department', related_name='department_jvmain_id', null=True, blank=True)
#     branch = models.ForeignKey('branch.Branch', related_name='branch_main_id', null=True, blank=True)
#     particular = models.TextField(blank=True, null=True)
#     STATUS_CHOICES = (
#         ('A', 'Active'),
#         ('I', 'Inactive'),
#         ('C', 'Cancelled'),
#         ('O', 'Posted'),
#         ('P', 'Printed'),
#     )
#     status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
#     enterby = models.ForeignKey(User, default=1, related_name='jvmain_enter')
#     enterdate = models.DateTimeField(auto_now_add=True)
#     modifyby = models.ForeignKey(User, default=1, related_name='jvmain_modify')
#     modifydate = models.DateTimeField(default=datetime.datetime.now())
#     postby = models.ForeignKey(User, default=1, related_name='jvmain_modify')
#     postdate = models.DateTimeField(default=datetime.datetime.now())
#     isdeleted = models.IntegerField(default=0)
#
#     class Meta:
#         db_table = 'jvmain'
#         ordering = ['-pk']
#         permissions = (("view_jvmain", "Can view jvmain"),)
#
#     def get_absolute_url(self):
#         return reverse('jvtype:detail', kwargs={'pk': self.pk})
#
#     def __str__(self):
#         return self.code
#
#     def __unicode__(self):
#         return self.code
#
#     def status_verbose(self):
#         return dict(Jvmain.STATUS_CHOICES)[self.status]

# # Create your models here.
#
# class Jvdetailbreakdown(models.Model):
#     item_counter = models.IntegerField(unique=True)
#     main_id = models.IntegerField(blank=True, null=True)
#     detail_id = models.IntegerField()
#     jv_num = models.CharField(max_length=10)
#     jv_date = models.DateTimeField()
#     chartofaccount_id = models.IntegerField()
#     particular = models.CharField(max_length=255, blank=True, null=True)
#     bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_id', blank=True, null=True)
#     department = models.ForeignKey('department.Department', related_name='department_id', blank=True, null=True)
#     employee_id = models.ForeignKey('employee.Employee', related_name='employee_id', blank=True, null=True)
#     supplier_id = models.IntegerField(blank=True, null=True)
#     customer_id = models.IntegerField(blank=True, null=True)
#     unit_id = models.IntegerField(blank=True, null=True)
#     branch_id = models.IntegerField(blank=True, null=True)
#     product_id = models.IntegerField(blank=True, null=True)
#     inputvat_id = models.IntegerField(blank=True, null=True)
#     outputvat_id = models.IntegerField(blank=True, null=True)
#     vat_id = models.IntegerField(blank=True, null=True)
#     wtax_id = models.IntegerField(blank=True, null=True)
#     ataxcode_id = models.IntegerField(blank=True, null=True)
#     debitamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     creditamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     balancecode = models.CharField(max_length=1, blank=True, null=True)
#     amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     STATUS_CHOICES = (
#         ('A', 'Active'),
#         ('I', 'Inactive'),
#         ('C', 'Cancelled'),
#         ('O', 'Posted'),
#         ('P', 'Printed'),
#     )
#     status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
#     enterby = models.ForeignKey(User, default=1, related_name='jvdetailbreakdown_enter')
#     enterdate = models.DateTimeField(auto_now_add=True)
#     modifyby = models.ForeignKey(User, default=1, related_name='jvdetailbreakdown_modify')
#     modifydate = models.DateTimeField(default=datetime.datetime.now())
#     isdeleted = models.IntegerField(default=0)
#     postby = models.ForeignKey(User, default=0, related_name='jvdetailbreakdown_post', blank=True, null=True)
#     postdate = models.DateTimeField(default=datetime.datetime.now())
#
#     class Meta:
#         db_table = 'jvdetailbreakdown'
#         unique_together = (('id', 'item_counter'),)
#
#     def get_absolute_url(self):
#         return reverse('jvdetailbreakdown:detail', kwargs={'pk': self.pk})
#
#     def __str__(self):
#         return self.id
#
#     def __unicode__(self):
#         return self.id
#
#     def status_verbose(self):
#         return dict(Inputvat.STATUS_CHOICES)[self.status]
#
#
# class Jvdetailbreakdowntemp(models.Model):
#     id = models.BigIntegerField(primary_key=True)
#     detailtemp_id = models.BigIntegerField(blank=True, null=True)
#     detail_id = models.BigIntegerField(blank=True, null=True)
#     item_counter = models.IntegerField(blank=True, null=True)
#     chartofaccount_id = models.IntegerField()
#     particular = models.CharField(max_length=255, blank=True, null=True)
#     bankaccount_id = models.IntegerField(blank=True, null=True)
#     department_id = models.IntegerField(blank=True, null=True)
#     employee_id = models.IntegerField(blank=True, null=True)
#     supplier_id = models.IntegerField(blank=True, null=True)
#     customer_id = models.IntegerField(blank=True, null=True)
#     unit_id = models.IntegerField(blank=True, null=True)
#     branch_id = models.IntegerField(blank=True, null=True)
#     product_id = models.IntegerField(blank=True, null=True)
#     inputvat_id = models.IntegerField(blank=True, null=True)
#     outputvat_id = models.IntegerField(blank=True, null=True)
#     vat_id = models.IntegerField(blank=True, null=True)
#     wtax_id = models.IntegerField(blank=True, null=True)
#     ataxcode_id = models.IntegerField(blank=True, null=True)
#     debitamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     creditamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     ischange = models.IntegerField(blank=True, null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'jvdetailbreakdowntemp'
#
#
# class Jvdetails(models.Model):
#     id = models.BigIntegerField(primary_key=True)
#     item_counter = models.IntegerField()
#     jvmain_id = models.BigIntegerField()
#     jv_num = models.CharField(max_length=10)
#     jv_date = models.DateTimeField()
#     chartofaccount_id = models.IntegerField()
#     bankaccount_id = models.IntegerField(blank=True, null=True)
#     department_id = models.IntegerField(blank=True, null=True)
#     employee_id = models.IntegerField(blank=True, null=True)
#     supplier_id = models.IntegerField(blank=True, null=True)
#     customer_id = models.IntegerField(blank=True, null=True)
#     unit_id = models.IntegerField(blank=True, null=True)
#     branch_id = models.IntegerField(blank=True, null=True)
#     product_id = models.IntegerField(blank=True, null=True)
#     inputvat_id = models.IntegerField(blank=True, null=True)
#     outputvat_id = models.IntegerField(blank=True, null=True)
#     vat_id = models.IntegerField(blank=True, null=True)
#     wtax_id = models.IntegerField(blank=True, null=True)
#     ataxcode_id = models.IntegerField(blank=True, null=True)
#     debitamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     creditamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     balancecode = models.CharField(max_length=1, blank=True, null=True)
#     amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     status = models.CharField(max_length=1)
#     enterby = models.IntegerField()
#     enterdate = models.DateTimeField()
#     modifyby = models.IntegerField()
#     modifydate = models.DateTimeField()
#     postby = models.IntegerField(blank=True, null=True)
#     postdate = models.DateTimeField(blank=True, null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'jvdetails'
#         unique_together = (('id', 'item_counter'),)
#
#
# class Jvdetailstemp(models.Model):
#     id = models.BigIntegerField(primary_key=True)
#     token = models.CharField(max_length=255, blank=True, null=True)
#     item_counter = models.IntegerField(blank=True, null=True)
#     main_id = models.BigIntegerField(blank=True, null=True)
#     detail_id = models.BigIntegerField(blank=True, null=True)
#     chartofaccount_id = models.IntegerField()
#     bankaccount_id = models.IntegerField(blank=True, null=True)
#     department_id = models.IntegerField(blank=True, null=True)
#     employee_id = models.IntegerField(blank=True, null=True)
#     supplier_id = models.IntegerField(blank=True, null=True)
#     customer_id = models.IntegerField(blank=True, null=True)
#     unit_id = models.IntegerField(blank=True, null=True)
#     branch_id = models.IntegerField(blank=True, null=True)
#     product_id = models.IntegerField(blank=True, null=True)
#     inputvat_id = models.IntegerField(blank=True, null=True)
#     outputvat_id = models.IntegerField(blank=True, null=True)
#     vat_id = models.IntegerField(blank=True, null=True)
#     wtax_id = models.IntegerField(blank=True, null=True)
#     ataxcode_id = models.IntegerField(blank=True, null=True)
#     debitamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     creditamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     ischange = models.IntegerField(blank=True, null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'jvdetailstemp'
#
#
# class Jvmain(models.Model):
#     id = models.BigIntegerField(primary_key=True)
#     jv_num = models.CharField(unique=True, max_length=10)
#     jv_date = models.DateTimeField()
#     jvtype_id = models.IntegerField()
#     refnum = models.CharField(max_length=150, blank=True, null=True)
#     department_id = models.IntegerField(blank=True, null=True)
#     branch_id = models.IntegerField(blank=True, null=True)
#     particular = models.TextField(blank=True, null=True)
#     status = models.CharField(max_length=1)
#     enterby = models.IntegerField()
#     enterdate = models.DateTimeField()
#     modifyby = models.IntegerField()
#     modifydate = models.DateTimeField()
#     postby = models.IntegerField(blank=True, null=True)
#     postdate = models.DateTimeField(blank=True, null=True)
#     isdeleted = models.IntegerField(blank=True, null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'jvmain'
