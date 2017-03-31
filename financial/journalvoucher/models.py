# from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
import datetime


class Jvmain(models.Model):
    jvnum = models.CharField(unique=True, max_length=10)
    jvprefix = models.CharField(default='JV', max_length=5)
    jvdate = models.DateTimeField()
    jvtype = models.ForeignKey('jvtype.Jvtype', related_name='jvtype_jvmain_id')
    refnum = models.CharField(max_length=150, blank=True, null=True)
    currency = models.ForeignKey('currency.Currency', related_name='currency_jvmain_id')
    branch = models.ForeignKey('branch.Branch', related_name='branch_jvmain_id')
    department = models.ForeignKey('department.Department', related_name='department_jvmain_id', null=True, blank=True)
    particular = models.TextField()
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='jvmain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='jvmain_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, default=1, related_name='jvmain_post')
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'jvmain'
        ordering = ['-pk']
        permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('jvmain:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.jvnum

    def __unicode__(self):
        return self.jvnum

    def status_verbose(self):
        return dict(Jvmain.STATUS_CHOICES)[self.status]

class Jvdetail(models.Model):
    item_counter = models.IntegerField()
    jvmain = models.ForeignKey('journalvoucher.Jvmain', related_name='jvmain_jvdetail_id', null=True, blank=True)
    jv_num = models.CharField(max_length=10)
    jv_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='chartofaccount_jvdetail_id')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_jvdetail_id', null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='department_jvdetail_id', null=True, blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_jvdetail_id', null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_jvdetail_id', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_jvdetail_id', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_jvdetail_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_jvdetail_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_jvdetail_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_jvdetail_id', null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_jvdetail_id', null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_jvdetail_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_jvdetail_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_jvdetail_id', null=True, blank=True)
    debitamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    creditamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    balancecode = models.CharField(max_length=1, blank=True, null=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='jvdetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='jvdetail_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, default=1, related_name='jvdetail_post')
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'jvdetail'
        ordering = ['-pk']
        #permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('jvdetail:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.jvmain

    def __unicode__(self):
        return unicode(self.jvmain)

    def status_verbose(self):
        return dict(Jvdetail.STATUS_CHOICES)[self.status]


class Jvdetailtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    jvmain = models.CharField(max_length=10, null=True, blank=True)
    jv_num = models.CharField(max_length=10)
    jv_date = models.DateTimeField(blank=True, null=True)
    chartofaccount = models.IntegerField(blank=True, null=True)
    bankaccount = models.IntegerField(blank=True, null=True)
    department = models.IntegerField(blank=True, null=True)
    employee = models.IntegerField(blank=True, null=True)
    supplier = models.IntegerField(blank=True, null=True)
    customer = models.IntegerField(blank=True, null=True)
    unit = models.IntegerField(blank=True, null=True)
    branch = models.IntegerField(blank=True, null=True)
    product = models.IntegerField(blank=True, null=True)
    inputvat = models.IntegerField(blank=True, null=True)
    outputvat = models.IntegerField(blank=True, null=True)
    vat = models.IntegerField(blank=True, null=True)
    wtax = models.IntegerField(blank=True, null=True)
    ataxcode = models.IntegerField(blank=True, null=True)
    debitamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    creditamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    balancecode = models.CharField(max_length=1, blank=True, null=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='jvdetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='jvdetailtemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, default=1, related_name='jvdetailtemp_post')
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'jvdetailtemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('jvdetailtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Jvdetailtemp.STATUS_CHOICES)[self.status]

class Jvdetailbreakdowntemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    jvdetailtemp = models.CharField(max_length=10, null=True, blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    jvmain = models.CharField(max_length=10, null=True, blank=True)
    jv_num = models.CharField(max_length=10)
    jv_date = models.DateTimeField(blank=True, null=True)
    chartofaccount = models.IntegerField(blank=True, null=True)
    particular = models.TextField(null=True, blank=True)
    bankaccount = models.IntegerField(blank=True, null=True)
    department = models.IntegerField(blank=True, null=True)
    employee = models.IntegerField(blank=True, null=True)
    supplier = models.IntegerField(blank=True, null=True)
    customer = models.IntegerField(blank=True, null=True)
    unit = models.IntegerField(blank=True, null=True)
    branch = models.IntegerField(blank=True, null=True)
    product = models.IntegerField(blank=True, null=True)
    inputvat = models.IntegerField(blank=True, null=True)
    outputvat = models.IntegerField(blank=True, null=True)
    vat = models.IntegerField(blank=True, null=True)
    wtax = models.IntegerField(blank=True, null=True)
    ataxcode = models.IntegerField(blank=True, null=True)
    debitamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    creditamount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    balancecode = models.CharField(max_length=1, blank=True, null=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='jvdetailbreakdowntemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='jvdetailbreakdowntemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, default=1, related_name='jvdetailbreakdowntemp_post')
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'jvdetailbreakdowntemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('jvdetailbreakdowntemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Jvdetailbreakdowntemp.STATUS_CHOICES)[self.status]




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
