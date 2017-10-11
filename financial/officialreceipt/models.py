from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import datetime


class Ormain(models.Model):
    ornum = models.CharField(max_length=10, unique=True)
    ordate = models.DateField()
    ortype = models.ForeignKey('ortype.Ortype', related_name='ormain_ortype_id')
    orsubtype = models.ForeignKey('orsubtype.Orsubtype', related_name='ormain_orsubtype_id')
    prnum = models.CharField(max_length=10, null=True, blank=True)
    prdate = models.DateField(null=True, blank=True)
    OR_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
        ('R', 'Released'),
    )
    orstatus = models.CharField(max_length=1, choices=OR_STATUS_CHOICES, default='F')
    adtype = models.ForeignKey('adtype.Adtype', related_name='ormain_adtype_id', null=True, blank=True)
    collector = models.ForeignKey('collector.Collector', related_name='ormain_collector_id')
    branch = models.ForeignKey('branch.Branch', related_name='ormain_branch_id')
    customer = models.ForeignKey('customer.Customer', related_name='ormain_customer_id')
    customer_code = models.CharField(max_length=25)
    customer_name = models.CharField(max_length=250)
    customer_address1 = models.CharField(max_length=250)
    customer_address2 = models.CharField(max_length=250, blank=True, null=True)
    customer_address3 = models.CharField(max_length=250, blank=True, null=True)
    customer_telno1 = models.CharField(max_length=20)
    customer_telno2 = models.CharField(max_length=20, blank=True, null=True)
    customer_celno = models.CharField(max_length=20, blank=True, null=True)
    customer_faxno = models.CharField(max_length=20, blank=True, null=True)
    customer_tin = models.CharField(max_length=20, blank=True, null=True)
    customer_zipcode = models.CharField(max_length=20, blank=True, null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    amountinwords = models.CharField(max_length=500, null=True, blank=True)
    outputvattype = models.ForeignKey('outputvattype.Outputvattype', related_name='ormain_outvattype_id', null=True,
                                      blank=True)
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    deferredvat = models.CharField(max_length=1, choices=YESNO_CHOICES, null=True, blank=True, default='N')
    vat = models.ForeignKey('vat.Vat', related_name='ormain_vat_id', validators=[MinValueValidator(1)], null=True,
                            blank=True)
    vatrate = models.IntegerField(default=0, null=True, blank=True)
    vatamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    wtax = models.ForeignKey('wtax.Wtax', related_name='ormain_wtax_id', validators=[MinValueValidator(1)], null=True,
                             blank=True)
    wtaxrate = models.IntegerField(default=0, null=True, blank=True)
    wtaxamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    currency = models.ForeignKey('currency.Currency', related_name='ormain_currency_id', default=1)
    fxrate = models.DecimalField(default=1.00, decimal_places=5, max_digits=18)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='ormain_bankaccount_id', null=True,
                                    blank=True)
    particulars = models.TextField(null=True, blank=True)
    vatablesale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    vatexemptsale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    vatzeroratedsale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    totalsale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    comments = models.CharField(max_length=250, null=True, blank=True)
    GOVT_CHOICES = (
        ('G', 'Government'),
        ('NG', 'Non-Government'),
        ('M', 'Mixed'),
    )
    government = models.CharField(max_length=2, choices=GOVT_CHOICES, null=True, blank=True, default='NG')
    designatedapprover = models.ForeignKey(User, default=2, related_name='ormain_designated_approver')
    actualapprover = models.ForeignKey(User, related_name='ormain_actual_approver', null=True, blank=True)
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='ormain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ormain_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='ormain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    releaseby = models.ForeignKey(User, related_name='ormain_release', null=True, blank=True)
    releasedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'ormain'
        ordering = ['-pk']
        permissions = (("view_officialreceipt", "Can view official receipt"),
                       ("approve_assignedor", "Can approve assigned or"),
                       ("approve_allor", "Can approve all or"),)

    def get_absolute_url(self):
        return reverse('officialreceipt:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.ornum

    def __unicode__(self):
        return self.ornum


class Oritem(models.Model):
    item_counter = models.IntegerField()
    ormain = models.ForeignKey('officialreceipt.Ormain', related_name='oritem_ormain_id', null=True, blank=True)
    ornum = models.CharField(max_length=10)
    ordate = models.DateTimeField()
    paytype = models.ForeignKey('paytype.Paytype', related_name='oritem_paytype_id')
    bank = models.ForeignKey('bank.Bank', related_name='oritem_bank_id', null=True, blank=True)
    bankbranch = models.ForeignKey('bankbranch.Bankbranch', related_name='oritem_bankbranch_id', null=True, blank=True)
    checknum = models.CharField(max_length=150, null=True, blank=True)
    checkdate = models.DateTimeField(null=True, blank=True)
    creditcard = models.ForeignKey('creditcard.Creditcard', related_name='oritem_creditcard_id', null=True, blank=True)
    creditcardnum = models.CharField(max_length=150, null=True, blank=True)
    authnum = models.CharField(max_length=150, null=True, blank=True)
    expirydate = models.DateTimeField(null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='oritem_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='oritem_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='oritem_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'oritem'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('oritem:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Oritem.STATUS_CHOICES)[self.status]


class Ordetail(models.Model):
    item_counter = models.IntegerField()
    ormain = models.ForeignKey('officialreceipt.Ormain', related_name='ormain_ordetail_id', null=True, blank=True)
    or_num = models.CharField(max_length=10)
    or_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='chartofaccount_ordetail_id')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_ordetail_id', null=True,
                                    blank=True)
    department = models.ForeignKey('department.Department', related_name='department_ordetail_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_ordetail_id', null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_ordetail_id', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_ordetail_id', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_ordetail_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_ordetail_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_ordetail_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_ordetail_id', null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_ordetail_id', null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_ordetail_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_ordetail_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_ordetail_id', null=True, blank=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='ordetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ordetail_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='ordetail_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'ordetail'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ordetail:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ordetail.STATUS_CHOICES)[self.status]


class Ordetailbreakdown(models.Model):
    item_counter = models.IntegerField()
    ormain = models.ForeignKey('officialreceipt.Ormain', related_name='ormain_ordetailbreakdown_id', null=True,
                               blank=True)
    ordetail = models.ForeignKey('officialreceipt.Ordetail', related_name='ordetail_ordetailbreakdown_id', null=True,
                                 blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    of_num = models.CharField(max_length=10)
    of_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount',
                                       related_name='chartofaccount_ordetailbreakdown_id')
    particular = models.TextField(null=True, blank=True)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_ordetailbreakdown_id',
                                    null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='department_ordetailbreakdown_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_ordetailbreakdown_id', null=True,
                                 blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_ordetailbreakdown_id', null=True,
                                 blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_ordetailbreakdown_id', null=True,
                                 blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_ordetailbreakdown_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_ordetailbreakdown_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_ordetailbreakdown_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_ordetailbreakdown_id', null=True,
                                 blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_ordetailbreakdown_id', null=True,
                                  blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_ordetailbreakdown_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_ordetailbreakdown_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_ordetailbreakdown_id', null=True,
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
    enterby = models.ForeignKey(User, default=1, related_name='ordetailbreakdown_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ordetailbreakdown_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='ordetailbreakdown_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'ordetailbreakdown'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ordetailbreakdown:ordetailbreakdown', kwargs={'pk': self.pk})

    def __str__(self):
        return self.ordetail

    def __unicode__(self):
        return unicode(self.ordetail)

    def status_verbose(self):
        return dict(Ordetailbreakdown.STATUS_CHOICES)[self.status]


class Oritemtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    ormain = models.CharField(max_length=10, null=True, blank=True)
    oritem = models.CharField(max_length=10, null=True, blank=True)
    ornum = models.CharField(max_length=10, null=True, blank=True)
    ordate = models.DateTimeField(blank=True, null=True)
    paytype = models.IntegerField(blank=True, null=True)
    bank = models.IntegerField(blank=True, null=True)
    bankbranch = models.IntegerField(blank=True, null=True)
    checknum = models.CharField(max_length=150, null=True, blank=True)
    checkdate = models.DateTimeField(null=True, blank=True)
    creditcard = models.IntegerField(blank=True, null=True)
    creditcardnum = models.CharField(max_length=150, null=True, blank=True)
    authnum = models.CharField(max_length=150, null=True, blank=True)
    expirydate = models.DateTimeField(null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='oritemtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='oritemtemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='oritemtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'oritemtemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('oritemtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Oritemtemp.STATUS_CHOICES)[self.status]


class Ordetailtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    ormain = models.CharField(max_length=10, null=True, blank=True)
    ordetail = models.CharField(max_length=10, null=True, blank=True)
    or_num = models.CharField(max_length=10)
    or_date = models.DateTimeField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='ordetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ordetailtemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='ordetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'ordetailtemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ordetailtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ordetailtemp.STATUS_CHOICES)[self.status]


class Ordetailbreakdowntemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    ordetailtemp = models.CharField(max_length=10, null=True, blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    ormain = models.CharField(max_length=10, null=True, blank=True)
    ordetail = models.CharField(max_length=10, null=True, blank=True)
    ordetailbreakdown = models.CharField(max_length=10, null=True, blank=True)
    or_num = models.CharField(max_length=10)
    or_date = models.DateTimeField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='ordetailbreakdowntemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ordetailbreakdowntemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='ordetailbreakdowntemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'ordetailbreakdowntemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ordetailbreakdowntemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk)

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ordetailbreakdowntemp.STATUS_CHOICES)[self.status]
