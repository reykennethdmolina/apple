from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
import datetime


class Ormain(models.Model):
    ornum = models.CharField(max_length=10, unique=True)
    ordate = models.DateField()
    ortype = models.ForeignKey('ortype.Ortype', related_name='ormain_ortype_id')
    OR_SOURCE_CHOICES = (
        ('A', 'Advertising'),
        ('C', 'Circulation'),
    )
    orsource = models.CharField(max_length=1, choices=OR_SOURCE_CHOICES)
    prnum = models.CharField(max_length=10, null=True, blank=True)
    prdate = models.DateField(null=True, blank=True)
    collector = models.ForeignKey('collector.Collector', related_name='ormain_collector_id')
    collector_code = models.CharField(max_length=25)
    collector_name = models.CharField(max_length=250)
    branch = models.ForeignKey('branch.Branch', related_name='ormain_branch_id')
    PAYEE_TYPE_CHOICES = (
        ('Y', 'Agency'),
        ('C', 'Client'),
        ('A', 'Agent'),
    )
    payee_type = models.CharField(max_length=2, choices=PAYEE_TYPE_CHOICES)
    agency = models.ForeignKey('customer.Customer', related_name='ormain_agency_id', null=True, blank=True)
    client = models.ForeignKey('customer.Customer', related_name='ormain_client_id', null=True, blank=True)
    agent = models.ForeignKey('agent.Agent', related_name='ormain_agent_id', null=True, blank=True)
    payee_code = models.CharField(max_length=25)
    payee_name = models.CharField(max_length=250)
    outputvattype = models.ForeignKey('outputvattype.Outputvattype', related_name='ormain_outvattype_id', null=True,
                                      blank=True)
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    deferredvat = models.CharField(max_length=1, choices=YESNO_CHOICES, null=True, blank=True, default='N')
    currency = models.ForeignKey('currency.Currency', related_name='ormain_currency_id', default=1)
    fxrate = models.DecimalField(default=1.00, decimal_places=5, max_digits=18)
    vat = models.ForeignKey('vat.Vat', related_name='ormain_vat_id', validators=[MinValueValidator(1)], null=True,
                            blank=True)
    vatrate = models.IntegerField(default=0, null=True, blank=True)
    vatamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    wtax = models.ForeignKey('wtax.Wtax', related_name='ormain_wtax_id', validators=[MinValueValidator(1)], null=True,
                             blank=True)
    wtaxrate = models.IntegerField(default=0, null=True, blank=True)
    wtaxamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    amountinwords = models.CharField(max_length=500, null=True, blank=True)
    particulars = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    OR_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
        ('R', 'Ready for Posting'),
    )
    orstatus = models.CharField(max_length=1, choices=OR_STATUS_CHOICES, default='F')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='ormain_bankaccount_id', null=True,
                                    blank=True)
    product = models.ForeignKey('product.Product', related_name='ormain_product_id', null=True, blank=True)
    product_code = models.CharField(max_length=25, null=True, blank=True)
    product_name = models.CharField(max_length=250, null=True, blank=True)
    vatablesale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    vatexemptsale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    vatzeroratedsale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    totalsale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    GOVT_CHOICES = (
        ('G', 'Government'),
        ('NG', 'Non-Government'),
        ('M', 'Mixed'),
    )
    government = models.CharField(max_length=2, choices=GOVT_CHOICES, null=True, blank=True, default='NG')
    designatedapprover = models.ForeignKey(User, related_name='ormain_designated_approver', null=True, blank=True)
    actualapprover = models.ForeignKey(User, related_name='ormain_actual_approver', null=True, blank=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='ormain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ormain_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ormain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    releaseby = models.ForeignKey(User, related_name='ormain_release', null=True, blank=True)
    releasedate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ormain_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    # processing_or fields
    initmark = models.CharField(null=True, blank=True, max_length=500)
    glsmark = models.CharField(null=True, blank=True, max_length=500)
    glsdate = models.DateTimeField(null=True, blank=True)
    importornum = models.CharField(null=True, blank=True, max_length=500)
    importordate = models.DateField(null=True, blank=True)
    importdate = models.DateTimeField(null=True, blank=True)
    importby = models.ForeignKey(User, default=1, related_name='ormain_import')
    productgroup = models.ForeignKey('productgroup.Productgroup', related_name='ormain_productgroup_id', null=True,
                                     blank=True)
    circulationproduct = models.ForeignKey('circulationproduct.Circulationproduct',
                                           related_name='ormain_circulationproduct_id', null=True, blank=True)
    circulationproduct_code = models.CharField(max_length=25, null=True, blank=True)
    circulationproduct_name = models.CharField(max_length=250, null=True, blank=True)
    adtype = models.ForeignKey('adtype.Adtype', related_name='ormain_adtype_id', null=True, blank=True)
    transaction_type = models.CharField(default='M', max_length=1)
    acctentry_incomplete = models.IntegerField(default=0)
    logs = models.CharField(null=True, blank=True, max_length=500)
    add1 = models.CharField(null=True, blank=True, max_length=500)
    add2 = models.CharField(null=True, blank=True, max_length=500)
    add3 = models.CharField(null=True, blank=True, max_length=500)
    tin = models.CharField(null=True, blank=True, max_length=500)

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


class Ordetail(models.Model):
    item_counter = models.IntegerField()
    ormain = models.ForeignKey('officialreceipt.Ormain', related_name='ormain_ordetail_id', null=True, blank=True)
    or_num = models.CharField(max_length=10)
    or_date = models.DateField()
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
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ordetail_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ordetail_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
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
    or_num = models.CharField(max_length=10)
    or_date = models.DateField()
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
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ordetailbreakdown_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ordetailbreakdown_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
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


class Ordetailtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    ormain = models.CharField(max_length=10, null=True, blank=True)
    ordetail = models.CharField(max_length=10, null=True, blank=True)
    or_num = models.CharField(max_length=10)
    or_date = models.DateField(blank=True, null=True)
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
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ordetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ordetailtemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
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
    or_date = models.DateField(blank=True, null=True)
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
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ordetailbreakdowntemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ordetailbreakdowntemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
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


class Orupload(models.Model):
    ormain = models.ForeignKey('officialreceipt.Ormain', related_name='ormain_orupload_id', null=True, blank=True)
    filename = models.CharField(max_length=250, null=True, blank=True)
    filetype = models.CharField(max_length=250, null=True, blank=True)
    enterby = models.ForeignKey(User, default=1, related_name='orupload_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='orupload_modify')
    modifydate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orupload'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('orupload:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.filename

    def __unicode__(self):
        return self.filename
