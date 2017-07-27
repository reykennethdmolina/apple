from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Apmain(models.Model):
    AP_TYPE_CHOICES = (
        ('PO', 'PO'),
    )

    AP_STATUS_CHOICES = (
        ('V', 'Verified'),
    )

    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    apnum = models.CharField(max_length=10, unique=True)
    apprefix = models.CharField(default='AP', max_length=5)
    apdate = models.DateField()
    aptype = models.ForeignKey('aptype.Aptype', related_name='aptype_apmain_id')
    apstatus = models.CharField(max_length=1, choices=AP_STATUS_CHOICES, default='V')

    payee = models.ForeignKey('supplier.Supplier', related_name='ap_supplier_id')
    payeecode = models.CharField(max_length=10)

    branch = models.ForeignKey('branch.Branch', related_name='ap_branch_id')

    vat = models.ForeignKey('vat.Vat', related_name='ap_vat_id', null=True, blank=True)
    vatcode = models.CharField(max_length=10, null=True, blank=True)
    vatrate = models.IntegerField(default=0, null=True, blank=True)

    atax = models.ForeignKey('ataxcode.Ataxcode', related_name='ap_ataxcode_id', null=True, blank=True)
    ataxcode = models.CharField(max_length=10, null=True, blank=True)
    ataxrate = models.IntegerField(default=0, null=True, blank=True)

    bankbranchdisburse = models.ForeignKey('bankbranchdisburse.Bankbranchdisburse', related_name='ap_bankbranchdisburse_id')
    bankbranchdisbursebranch = models.CharField(max_length=10)

    inputvattype = models.ForeignKey('inputvattype.Inputvattype', related_name='ap_inputvattype_id')
    creditterm = models.ForeignKey('creditterm.Creditterm', related_name='ap_creditterm_id')
    duedate = models.DateField()
    refno = models.CharField(max_length=250)
    particulars = models.CharField(max_length=250)
    deferred = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    currency = models.ForeignKey('currency.Currency', related_name='ap_currency_id')
    fxrate = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=5, max_digits=18)

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='ap_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ap_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'apmain'
        ordering = ['-pk']
        permissions = (("view_accountspayable", "Can view accountspayable"),)

    def get_absolute_url(self):
        return reverse('accountspayable:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.apnum

    def __unicode__(self):
        return self.apnum

    def status_verbose(self):
        return dict(Apmain.STATUS_CHOICES)[self.status]

class Apdetail(models.Model):
    item_counter = models.IntegerField()
    apmain = models.ForeignKey('accountspayable.Apmain', related_name='apmain_apdetail_id', \
        null=True, blank=True)
    ap_num = models.CharField(max_length=10)
    ap_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', \
        related_name='chartofaccount_apdetail_id')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', \
        related_name='bankaccount_apdetail_id', null=True, blank=True)
    department = models.ForeignKey('department.Department', \
        related_name='department_apdetail_id', null=True, blank=True)
    employee = models.ForeignKey('employee.Employee', \
        related_name='employee_apdetail_id', null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', \
        related_name='supplier_apdetail_id', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', \
        related_name='customer_apdetail_id', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_apdetail_id', \
        null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_apdetail_id', \
        null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_apdetail_id', \
        null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_apdetail_id', \
        null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', \
        related_name='outputvat_apdetail_id', null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_apdetail_id', \
        null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_apdetail_id', \
        null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_apdetail_id', \
        null=True, blank=True)
    debitamount = models.DecimalField(max_digits=18, decimal_places=2, \
        blank=True, null=True, default=0.00)
    creditamount = models.DecimalField(max_digits=18, decimal_places=2, \
        blank=True, null=True, default=0.00)
    balancecode = models.CharField(max_length=1, blank=True, null=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, \
        null=True, default=0.00)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='apdetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='apdetail_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='apdetail_post', \
        null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'apdetail'
        ordering = ['-pk']
        #permissions = (("view_apmain", "Can view apmain"),)

    def get_absolute_url(self):
        return reverse('apdetail:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Apdetail.STATUS_CHOICES)[self.status]

class Apdetailbreakdown(models.Model):
    item_counter = models.IntegerField()
    apmain = models.ForeignKey('accountspayable.Apmain', \
        related_name='apmain_apdetailbreakdown_id', null=True, blank=True)
    apdetail = models.ForeignKey('accountspayable.Apdetail', \
        related_name='apdetail_apdetailbreakdown_id', null=True, blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    ap_num = models.CharField(max_length=10)
    ap_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', \
        related_name='chartofaccount_apdetailbreakdown_id')
    particular = models.TextField(null=True, blank=True)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', \
        related_name='bankaccount_apdetailbreakdown_id', null=True,
                                    blank=True)
    department = models.ForeignKey('department.Department', \
        related_name='department_apdetailbreakdown_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', \
        related_name='employee_apdetailbreakdown_id', null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', \
        related_name='supplier_apdetailbreakdown_id', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', \
        related_name='customer_apdetailbreakdown_id', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_apdetailbreakdown_id', \
        null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', \
        related_name='branch_apdetailbreakdown_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', \
        related_name='product_apdetailbreakdown_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', \
        related_name='inputvat_apdetailbreakdown_id', null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', \
        related_name='outputvat_apdetailbreakdown_id', null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_apdetailbreakdown_id', \
        null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_apdetailbreakdown_id', \
        null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', \
        related_name='ataxcode_apdetailbreakdown_id', null=True, blank=True)
    debitamount = models.DecimalField(max_digits=18, decimal_places=2, \
        blank=True, null=True, default=0.00)
    creditamount = models.DecimalField(max_digits=18, decimal_places=2, \
        blank=True, null=True, default=0.00)
    balancecode = models.CharField(max_length=1, blank=True, null=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2, \
        blank=True, null=True, default=0.00)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='apdetailbreakdown_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='apdetailbreakdown_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='apdetailbreakdown_post', \
        null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'apdetailbreakdown'
        ordering = ['-pk']
        # permissions = (("view_apmain", "Can view apmain"),)

    def get_absolute_url(self):
        return reverse('apdetailbreakdown:apdetailbreakdown', kwargs={'pk': self.pk})

    def __str__(self):
        return self.apdetail

    def __unicode__(self):
        return unicode(self.apdetail)

    def status_verbose(self):
        return dict(Apdetailbreakdown.STATUS_CHOICES)[self.status]
