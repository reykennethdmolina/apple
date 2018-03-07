from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import datetime


class Cvmain(models.Model):
    cvnum = models.CharField(max_length=10, unique=True)
    cvdate = models.DateField()
    cvtype = models.ForeignKey('cvtype.Cvtype', related_name='cvmain_cvtype_id', null=True, blank=True)
    cvsubtype = models.ForeignKey('cvsubtype.Cvsubtype', related_name='cvmain_cvsubtype_id', null=True, blank=True)
    CV_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
        ('I', 'In Process'),
        ('FR', 'For Release'),
        ('R', 'Released'),
    )
    cvstatus = models.CharField(max_length=2, choices=CV_STATUS_CHOICES, default='F')
    payee = models.ForeignKey('supplier.Supplier', related_name='cvmain_payee_id', null=True, blank=True)
    payee_code = models.CharField(max_length=25, null=True, blank=True)
    payee_name = models.CharField(max_length=150)
    checknum = models.CharField(max_length=150)
    checkdate = models.DateTimeField()
    vat = models.ForeignKey('vat.Vat', related_name='cvmain_vat_id', validators=[MinValueValidator(1)])
    vatrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)], null=True,
                                  blank=True)
    atc = models.ForeignKey('ataxcode.Ataxcode', related_name='cvmain_atc_id', validators=[MinValueValidator(1)])
    atcrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)], null=True,
                                  blank=True)
    currency = models.ForeignKey('currency.Currency', related_name='cvmain_currency_id', default=1)
    fxrate = models.DecimalField(default=0.00, decimal_places=5, max_digits=18)
    inputvattype = models.ForeignKey('inputvattype.Inputvattype', related_name='cvmain_inputvattype_id')
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    deferredvat = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    branch = models.ForeignKey('branch.Branch', related_name='cvmain_branch_id', default='5')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='cvmain_bankaccount_id', null=True, blank=True)
    disbursingbranch = models.ForeignKey('bankbranchdisburse.Bankbranchdisburse',
                                         related_name='cvmain_bankbranchdisburse_id', null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=18, validators=[MinValueValidator(1)], default=0.00)
    amountinwords = models.CharField(max_length=500, null=True, blank=True)
    particulars = models.TextField()
    refnum = models.CharField(max_length=150, null=True, blank=True)
    designatedapprover = models.ForeignKey(User, related_name='cvmain_designated_approver', null=True, blank=True)
    actualapprover = models.ForeignKey(User, related_name='cvmain_actual_approver', null=True, blank=True)
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    approverremarks = models.CharField(max_length=250, null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='cvmain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='cvmain_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='cvmain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    releaseby = models.ForeignKey(User, related_name='cvmain_release', null=True, blank=True)
    releasedate = models.DateTimeField(null=True, blank=True)
    releaseto = models.CharField(max_length=250, null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'cvmain'
        ordering = ['-pk']
        permissions = (("view_checkvoucher", "Can view check voucher"),
                       ("approve_assignedcv", "Can approve assigned cv"),
                       ("approve_allcv", "Can approve all cv"),)

    def get_absolute_url(self):
        return reverse('checkvoucher:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.cvnum

    def __unicode__(self):
        return self.cvnum


class Cvdetail(models.Model):
    item_counter = models.IntegerField()
    cvmain = models.ForeignKey('checkvoucher.Cvmain', related_name='cvmain_cvdetail_id', null=True, blank=True)
    cv_num = models.CharField(max_length=10)
    cv_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='chartofaccount_cvdetail_id')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_cvdetail_id', null=True,
                                    blank=True)
    department = models.ForeignKey('department.Department', related_name='department_cvdetail_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_cvdetail_id', null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_cvdetail_id', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_cvdetail_id', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_cvdetail_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_cvdetail_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_cvdetail_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_cvdetail_id', null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_cvdetail_id', null=True,
                                  blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_cvdetail_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_cvdetail_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_cvdetail_id', null=True, blank=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='cvdetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='cvdetail_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='cvdetail_post', null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'cvdetail'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('cvdetail:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Cvdetail.STATUS_CHOICES)[self.status]


class Cvdetailbreakdown(models.Model):
    item_counter = models.IntegerField()
    cvmain = models.ForeignKey('checkvoucher.Cvmain', related_name='cvmain_cvdetailbreakdown_id', null=True,
                               blank=True)
    cvdetail = models.ForeignKey('checkvoucher.Cvdetail', related_name='cvdetail_cvdetailbreakdown_id',
                                 null=True, blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    cv_num = models.CharField(max_length=10)
    cv_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount',
                                       related_name='chartofaccount_cvdetailbreakdown_id')
    particular = models.TextField(null=True, blank=True)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_cvdetailbreakdown_id',
                                    null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='department_cvdetailbreakdown_id',
                                   null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_cvdetailbreakdown_id', null=True,
                                 blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_cvdetailbreakdown_id', null=True,
                                 blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_cvdetailbreakdown_id', null=True,
                                 blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_cvdetailbreakdown_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_cvdetailbreakdown_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_cvdetailbreakdown_id', null=True,
                                blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_cvdetailbreakdown_id', null=True,
                                 blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_cvdetailbreakdown_id', null=True,
                                  blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_cvdetailbreakdown_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_cvdetailbreakdown_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_cvdetailbreakdown_id', null=True,
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
    enterby = models.ForeignKey(User, default=1, related_name='cvdetailbreakdown_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='cvdetailbreakdown_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='cvdetailbreakdown_post', null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'cvdetailbreakdown'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('cvdetailbreakdown:cvdetailbreakdown', kwargs={'pk': self.pk})

    def __str__(self):
        return self.cvdetail

    def __unicode__(self):
        return unicode(self.cvdetail)

    def status_verbose(self):
        return dict(Cvdetailbreakdown.STATUS_CHOICES)[self.status]


class Cvdetailtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    cvmain = models.CharField(max_length=10, null=True, blank=True)
    cvdetail = models.CharField(max_length=10, null=True, blank=True)
    cv_num = models.CharField(max_length=10)
    cv_date = models.DateTimeField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='cvdetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='cvdetailtemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='cvdetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'cvdetailtemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('cvdetailtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Cvdetailtemp.STATUS_CHOICES)[self.status]


class Cvdetailbreakdowntemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    cvdetailtemp = models.CharField(max_length=10, null=True, blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    cvmain = models.CharField(max_length=10, null=True, blank=True)
    cvdetail = models.CharField(max_length=10, null=True, blank=True)
    cvdetailbreakdown = models.CharField(max_length=10, null=True, blank=True)
    cv_num = models.CharField(max_length=10)
    cv_date = models.DateTimeField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='cvdetailbreakdowntemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='cvdetailbreakdowntemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='cvdetailbreakdowntemp_post', null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'cvdetailbreakdowntemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('cvdetailbreakdowntemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk)

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Cvdetailbreakdowntemp.STATUS_CHOICES)[self.status]
