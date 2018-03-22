from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
import datetime


class Armain(models.Model):
    arnum = models.CharField(max_length=10, unique=True)
    ardate = models.DateField()
    artype = models.ForeignKey('artype.Artype', related_name='armain_artype_id')
    arsubtype = models.ForeignKey('arsubtype.Arsubtype', related_name='armain_arsubtype_id', null=True, blank=True)
    payor = models.ForeignKey('employee.Employee', related_name='armain_payor_id', null=True, blank=True)
    payor_code = models.CharField(max_length=25)  # code is NONTRADE if payor is not an employee
    payor_name = models.CharField(max_length=250)
    collector = models.ForeignKey('collector.Collector', related_name='armain_collector_id')
    collector_code = models.CharField(max_length=25)
    collector_name = models.CharField(max_length=250)
    branch = models.ForeignKey('branch.Branch', related_name='armain_branch_id')
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    amountinwords = models.CharField(max_length=500, null=True, blank=True)
    depositorybank = models.ForeignKey('bankaccount.Bankaccount', related_name='armain_bankaccount_id', null=True,
                                       blank=True)
    particulars = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    AR_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
        ('R', 'Released'),
    )
    arstatus = models.CharField(max_length=1, choices=AR_STATUS_CHOICES, default='F')
    designatedapprover = models.ForeignKey(User, related_name='armain_designated_approver', null=True, blank=True)
    actualapprover = models.ForeignKey(User, related_name='armain_actual_approver', null=True, blank=True)
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    approverremarks = models.CharField(max_length=250, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='armain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='armain_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='armain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='armain_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    releaseby = models.ForeignKey(User, related_name='armain_release', null=True, blank=True)
    releasedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'armain'
        ordering = ['-pk']
        permissions = (("view_acknowledgementreceipt", "Can view acknowledgement receipt"),)

    def get_absolute_url(self):
        return reverse('acknowledgementreceipt:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.arnum

    def __unicode__(self):
        return self.arnum


class Aritem(models.Model):
    item_counter = models.IntegerField()
    armain = models.ForeignKey('acknowledgementreceipt.Armain', related_name='aritem_armain_id')
    arnum = models.CharField(max_length=10)
    ardate = models.DateTimeField()
    paytype = models.ForeignKey('paytype.Paytype', related_name='aritem_paytype_id')
    bank = models.ForeignKey('bank.Bank', related_name='aritem_bank_id', null=True, blank=True)
    bankbranch = models.ForeignKey('bankbranch.Bankbranch', related_name='aritem_bankbranch_id', null=True, blank=True)
    num = models.CharField(max_length=200, null=True, blank=True)
    authnum = models.CharField(max_length=200, null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    remarks = models.CharField(max_length=500, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='aritem_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='aritem_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='aritem_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='aritem_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'aritem'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('aritem:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Aritem.STATUS_CHOICES)[self.status]


class Aritemtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    armain = models.CharField(max_length=10, null=True, blank=True)
    aritem = models.CharField(max_length=10, null=True, blank=True)
    arnum = models.CharField(max_length=10, null=True, blank=True)
    ardate = models.DateTimeField(blank=True, null=True)
    paytype = models.ForeignKey('paytype.Paytype', related_name='aritemtemp_paytype_id')
    bank = models.ForeignKey('bank.Bank', related_name='aritemtemp_bank_id', null=True, blank=True)
    bankbranch = models.ForeignKey('bankbranch.Bankbranch', related_name='aritemtemp_bankbranch_id', null=True,
                                   blank=True)
    num = models.CharField(max_length=200, null=True, blank=True)
    authnum = models.CharField(max_length=200, null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    remarks = models.CharField(max_length=500, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='aritemtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='aritemtemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='aritemtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='aritemtemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'aritemtemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('aritemtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Aritemtemp.STATUS_CHOICES)[self.status]


class Ardetail(models.Model):
    item_counter = models.IntegerField()
    armain = models.ForeignKey('acknowledgementreceipt.Armain', related_name='armain_ardetail_id', null=True, blank=True)
    ar_num = models.CharField(max_length=10)
    ar_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='chartofaccount_ardetail_id')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_ardetail_id', null=True,
                                    blank=True)
    department = models.ForeignKey('department.Department', related_name='department_ardetail_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_ardetail_id', null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_ardetail_id', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_ardetail_id', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_ardetail_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_ardetail_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_ardetail_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_ardetail_id', null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_ardetail_id', null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_ardetail_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_ardetail_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_ardetail_id', null=True, blank=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='ardetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ardetail_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ardetail_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ardetail_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'ardetail'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ardetail:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ardetail.STATUS_CHOICES)[self.status]


class Ardetailbreakdown(models.Model):
    item_counter = models.IntegerField()
    armain = models.ForeignKey('acknowledgementreceipt.Armain', related_name='armain_ardetailbreakdown_id', null=True,
                               blank=True)
    ardetail = models.ForeignKey('acknowledgementreceipt.Ardetail', related_name='ardetail_ardetailbreakdown_id', null=True,
                                 blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    ar_num = models.CharField(max_length=10)
    ar_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount',
                                       related_name='chartofaccount_ardetailbreakdown_id')
    particular = models.TextField(null=True, blank=True)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_ardetailbreakdown_id',
                                    null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='department_ardetailbreakdown_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_ardetailbreakdown_id', null=True,
                                 blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_ardetailbreakdown_id', null=True,
                                 blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_ardetailbreakdown_id', null=True,
                                 blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_ardetailbreakdown_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_ardetailbreakdown_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_ardetailbreakdown_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_ardetailbreakdown_id', null=True,
                                 blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_ardetailbreakdown_id', null=True,
                                  blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_ardetailbreakdown_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_ardetailbreakdown_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_ardetailbreakdown_id', null=True,
                                 blank=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='ardetailbreakdown_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ardetailbreakdown_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ardetailbreakdown_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ardetailbreakdown_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'ardetailbreakdown'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ardetailbreakdown:ardetailbreakdown', kwargs={'pk': self.pk})

    def __str__(self):
        return self.ardetail

    def __unicode__(self):
        return unicode(self.ardetail)

    def status_verbose(self):
        return dict(Ardetailbreakdown.STATUS_CHOICES)[self.status]


class Ardetailtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    armain = models.CharField(max_length=10, null=True, blank=True)
    ardetail = models.CharField(max_length=10, null=True, blank=True)
    ar_num = models.CharField(max_length=10)
    ar_date = models.DateTimeField(blank=True, null=True)
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
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='ardetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ardetailtemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ardetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ardetailtemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'ardetailtemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ardetailtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ardetailtemp.STATUS_CHOICES)[self.status]


class Ardetailbreakdowntemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    ardetailtemp = models.CharField(max_length=10, null=True, blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    armain = models.CharField(max_length=10, null=True, blank=True)
    ardetail = models.CharField(max_length=10, null=True, blank=True)
    ardetailbreakdown = models.CharField(max_length=10, null=True, blank=True)
    ar_num = models.CharField(max_length=10)
    ar_date = models.DateTimeField(blank=True, null=True)
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
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='ardetailbreakdowntemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ardetailbreakdowntemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ardetailbreakdowntemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ardetailbreakdowntemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'ardetailbreakdowntemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ardetailbreakdowntemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk)

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ardetailbreakdowntemp.STATUS_CHOICES)[self.status]
