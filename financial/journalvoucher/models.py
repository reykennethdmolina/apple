from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


class Jvmain(models.Model):
    jvnum = models.CharField(unique=True, max_length=10)
    jvprefix = models.CharField(default='JV', max_length=5)
    jvdate = models.DateField()
    jvtype = models.ForeignKey('jvtype.Jvtype', related_name='jvtype_jvmain_id')
    jvsubtype = models.ForeignKey('jvsubtype.Jvsubtype', related_name='jvsubtype_jvmain_id')
    refnum = models.CharField(max_length=150, blank=True, null=True)
    currency = models.ForeignKey('currency.Currency', related_name='currency_jvmain_id')
    fxrate = models.DecimalField(default=1.00, null=True, blank=True, decimal_places=5, max_digits=18)
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
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='jvmain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='jvmain_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    JV_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
        ('I', 'In Process'),
        ('R', 'Ready for Posting'),
    )

    jvstatus = models.CharField(max_length=1, choices=JV_STATUS_CHOICES, default='F')
    designatedapprover = models.ForeignKey(User, related_name='jvmain_designated_approver', null=True, blank=True)
    actualapprover = models.ForeignKey(User, related_name='jvmain_actual_approver', null=True, blank=True)
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    approverremarks = models.CharField(max_length=250, null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    releaseby = models.ForeignKey(User, related_name='jvmain_release', null=True, blank=True)
    releasedate = models.DateTimeField(null=True, blank=True)
    print_ctr = models.IntegerField(default=0)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    importedjvnum = models.CharField(null=True, blank=True, max_length=500)
    confi = models.IntegerField(default=0)

    class Meta:
        db_table = 'jvmain'
        ordering = ['-pk']
        permissions = (("view_journalvoucher", "Can view journalvoucher"),
                       ("approve_assignedjv", "Can approve assigned jv"),
                       ("approve_alljv", "Can approve all jv"),)

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
    jv_date = models.DateField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='chartofaccount_jvdetail_id')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_jvdetail_id', null=True,
                                    blank=True)
    department = models.ForeignKey('department.Department', related_name='department_jvdetail_id', null=True,
                                   blank=True)
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
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='jvdetail_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='jvdetail_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'jvdetail'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('jvdetail:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Jvdetail.STATUS_CHOICES)[self.status]


class Jvdetailbreakdown(models.Model):
    item_counter = models.IntegerField()
    jvmain = models.ForeignKey('journalvoucher.Jvmain', related_name='jvmain_jvdetailbreakdown_id', null=True,
                               blank=True)
    jvdetail = models.ForeignKey('journalvoucher.Jvdetail', related_name='jvdetail_jvdetailbreakdown_id', null=True,
                                 blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    jv_num = models.CharField(max_length=10)
    jv_date = models.DateField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount',
                                       related_name='chartofaccount_jvdetailbreakdown_id')
    particular = models.TextField(null=True, blank=True)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_jvdetailbreakdown_id',
                                    null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='department_jvdetailbreakdown_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_jvdetailbreakdown_id', null=True,
                                 blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_jvdetailbreakdown_id', null=True,
                                 blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_jvdetailbreakdown_id', null=True,
                                 blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_jvdetailbreakdown_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_jvdetailbreakdown_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_jvdetailbreakdown_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_jvdetailbreakdown_id', null=True,
                                 blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_jvdetailbreakdown_id', null=True,
                                  blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_jvdetailbreakdown_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_jvdetailbreakdown_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_jvdetailbreakdown_id', null=True,
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
    enterby = models.ForeignKey(User, default=1, related_name='jvdetailbreakdown_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='jvdetailbreakdown_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='jvdetailbreakdown_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='jvdetailbreakdown_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'jvdetailbreakdown'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('jvdetailbreakdown:jvdetailbreakdown', kwargs={'pk': self.pk})

    def __str__(self):
        return self.jvdetail

    def __unicode__(self):
        return unicode(self.jvdetail)

    def status_verbose(self):
        return dict(Jvdetailbreakdown.STATUS_CHOICES)[self.status]


class Jvdetailtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    jvmain = models.CharField(max_length=10, null=True, blank=True)
    jvdetail = models.CharField(max_length=10, null=True, blank=True)
    jv_num = models.CharField(max_length=10)
    jv_date = models.DateField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='jvdetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='jvdetailtemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='jvdetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='jvdetailtemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
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
    jvdetail = models.CharField(max_length=10, null=True, blank=True)
    jvdetailbreakdown = models.CharField(max_length=10, null=True, blank=True)
    jv_num = models.CharField(max_length=10)
    jv_date = models.DateField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='jvdetailbreakdowntemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='jvdetailbreakdowntemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='jvdetailbreakdowntemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='jvdetailbreakdowntemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'jvdetailbreakdowntemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('jvdetailbreakdowntemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk)

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Jvdetailbreakdowntemp.STATUS_CHOICES)[self.status]


class Jvupload(models.Model):
    jvmain = models.ForeignKey('journalvoucher.Jvmain', related_name='jvmain_jvupload_id', null=True, blank=True)
    filename = models.CharField(max_length=250, null=True, blank=True)
    filetype = models.CharField(max_length=250, null=True, blank=True)
    enterby = models.ForeignKey(User, default=1, related_name='jvupload_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='jvupload_modify')
    modifydate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'jvupload'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('jvupload:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.filename

    def __unicode__(self):
        return self.filename

