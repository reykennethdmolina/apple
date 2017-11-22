from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import datetime


class Dcmain(models.Model):
    dcnum = models.CharField(max_length=10, unique=True)
    dcdate = models.DateField()
    DC_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    dcstatus = models.CharField(max_length=1, choices=DC_STATUS_CHOICES, default='F')
    DC_TYPE_CHOICES = (
        ('D', 'Debit Memo'),
        ('C', 'Credit Memo'),
    )
    dctype = models.CharField(max_length=1, choices=DC_TYPE_CHOICES)
    dcartype = models.ForeignKey('dcartype.Dcartype', related_name='dcmain_dcartype_id', null=True, blank=True)
    dcsubtype = models.ForeignKey('debitcreditmemosubtype.Debitcreditmemosubtype', related_name='dcmain_subtype_id')
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    branch = models.ForeignKey('branch.Branch', related_name='dcmain_branch_id', default=5)
    customer = models.ForeignKey('customer.Customer', related_name='dcmain_customer_id', null=True, blank=True)
    customer_code = models.CharField(max_length=10, null=True, blank=True)
    customer_name = models.CharField(max_length=250, null=True, blank=True)
    outputvattype = models.ForeignKey('outputvattype.Outputvattype', related_name='dcmain_outvattype_id', null=True,
                                      blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='dcmain_vat_id', validators=[MinValueValidator(1)])
    vatrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)])
    particulars = models.TextField()
    designatedapprover = models.ForeignKey(User, related_name='dcmain_designated_approver', null=True, blank=True)
    actualapprover = models.ForeignKey(User, related_name='dcmain_actual_approver', null=True, blank=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='dcmain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='dcmain_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='dcmain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'dcmain'
        ordering = ['-pk']
        permissions = (("view_debitcreditmemo", "Can view debit credit memo"),
                       ("approve_assigneddc", "Can approve assigned dc"),
                       ("approve_alldc", "Can approve all dc"),)

    def get_absolute_url(self):
        return reverse('debitcreditmemo:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.dcnum

    def __unicode__(self):
        return self.dcnum


class Dcdetail(models.Model):
    item_counter = models.IntegerField()
    dcmain = models.ForeignKey('debitcreditmemo.Dcmain', related_name='dcmain_dcdetail_id', null=True, blank=True)
    dc_num = models.CharField(max_length=10)
    dc_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='chartofaccount_dcdetail_id')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_dcdetail_id', null=True,
                                    blank=True)
    department = models.ForeignKey('department.Department', related_name='department_dcdetail_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_dcdetail_id', null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_dcdetail_id', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_dcdetail_id', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_dcdetail_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_dcdetail_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_dcdetail_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_dcdetail_id', null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_dcdetail_id', null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_dcdetail_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_dcdetail_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_dcdetail_id', null=True, blank=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='dcdetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='dcdetail_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='dcdetail_post', null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'dcdetail'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('dcdetail:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Dcdetail.STATUS_CHOICES)[self.status]


class Dcdetailbreakdown(models.Model):
    item_counter = models.IntegerField()
    dcmain = models.ForeignKey('debitcreditmemo.Dcmain', related_name='dcmain_dcdetailbreakdown_id', null=True,
                               blank=True)
    dcdetail = models.ForeignKey('debitcreditmemo.Dcdetail', related_name='dcdetail_dcdetailbreakdown_id', null=True,
                                 blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    dc_num = models.CharField(max_length=10)
    dc_date = models.DateTimeField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount',
                                       related_name='chartofaccount_dcdetailbreakdown_id')
    particular = models.TextField(null=True, blank=True)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_dcdetailbreakdown_id',
                                    null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='department_dcdetailbreakdown_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_dcdetailbreakdown_id', null=True,
                                 blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_dcdetailbreakdown_id', null=True,
                                 blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_dcdetailbreakdown_id', null=True,
                                 blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_dcdetailbreakdown_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_dcdetailbreakdown_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_dcdetailbreakdown_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_dcdetailbreakdown_id', null=True,
                                 blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_dcdetailbreakdown_id', null=True,
                                  blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_dcdetailbreakdown_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_dcdetailbreakdown_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_dcdetailbreakdown_id', null=True,
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
    enterby = models.ForeignKey(User, default=1, related_name='dcdetailbreakdown_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='dcdetailbreakdown_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='dcdetailbreakdown_post', null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'dcdetailbreakdown'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('dcdetailbreakdown:dcdetailbreakdown', kwargs={'pk': self.pk})

    def __str__(self):
        return self.dcdetail

    def __unicode__(self):
        return unicode(self.dcdetail)

    def status_verbose(self):
        return dict(Dcdetailbreakdown.STATUS_CHOICES)[self.status]


class Dcdetailtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    dcmain = models.CharField(max_length=10, null=True, blank=True)
    dcdetail = models.CharField(max_length=10, null=True, blank=True)
    dc_num = models.CharField(max_length=10)
    dc_date = models.DateTimeField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='dcdetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='dcdetailtemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='dcdetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'dcdetailtemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('dcdetailtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Dcdetailtemp.STATUS_CHOICES)[self.status]


class Dcdetailbreakdowntemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    dcdetailtemp = models.CharField(max_length=10, null=True, blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    dcmain = models.CharField(max_length=10, null=True, blank=True)
    dcdetail = models.CharField(max_length=10, null=True, blank=True)
    dcdetailbreakdown = models.CharField(max_length=10, null=True, blank=True)
    dc_num = models.CharField(max_length=10)
    dc_date = models.DateTimeField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='dcdetailbreakdowntemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='dcdetailbreakdowntemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='dcdetailbreakdowntemp_post', null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'dcdetailbreakdowntemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('dcdetailbreakdowntemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk)

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Dcdetailbreakdowntemp.STATUS_CHOICES)[self.status]
