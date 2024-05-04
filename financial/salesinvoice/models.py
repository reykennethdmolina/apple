    
from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Simain(models.Model):
    sinum= models.CharField(max_length=10, unique=True)               
    sidate = models.DateField()                     
    sitype = models.ForeignKey('sitype.Sitype', related_name='simain_sitype_id')
    sisubtype = models.ForeignKey('sisubtype.Sisubtype', related_name='simain_sisubtype_id')
    branch = models.ForeignKey('branch.Branch', related_name='simain_branch_id')
    customer = models.ForeignKey('customer.Customer', related_name='simain_customer_id') 
    creditterm = models.ForeignKey('creditterm.Creditterm', related_name='simain_creditterm_id')
    duedate = models.DateField()                    
    accountexecutive = models.ForeignKey('employee.Employee', related_name='simain_employee_id', null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    amountinwords = models.CharField(max_length=500, null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='simain_vat_id', validators=[MinValueValidator(1)], null=True,
                            blank=True)
    vatrate = models.IntegerField(default=0, null=True, blank=True)  
    vatamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    outputvattype = models.ForeignKey('outputvattype.Outputvattype', related_name='simain_outputvattype_id')
    wtax = models.ForeignKey('wtax.Wtax', related_name='simain_wtax_id', validators=[MinValueValidator(1)], null=True, blank=True) 
    wtaxrate = models.IntegerField(default=0, null=True, blank=True) 
    wtaxamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    discountpercent = models.IntegerField(default=0, null=True, blank=True)
    discountamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    refno = models.CharField(max_length=250, null=True, blank=True)
    actualapprover = models.ForeignKey(User, related_name='simain_actual_approver', null=True, blank=True)
    designatedapprover = models.ForeignKey(User, related_name='simain_designated_approver', null=True, blank=True)
    SI_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
        ('R', 'Ready for Posting')
    )
    sistatus = models.CharField(max_length=1, choices=SI_STATUS_CHOICES, default='F')
    particulars = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    vatablesale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    vatexemptsale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    vatzeroratedsale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    totalsale = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved')
    )
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    approverremarks = models.CharField(max_length=255, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed')
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    acctentry_incomplete = models.IntegerField(default=0)
    enterdate = models.DateTimeField(auto_now_add=True)
    modifydate = models.DateTimeField(auto_now_add=True)
    enterby = models.ForeignKey(User, default=1, related_name='simain_enter')
    modifyby = models.ForeignKey(User, default=1, related_name='simain_modify')
    postby = models.ForeignKey(User, related_name='simain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'simain'
        ordering = ['-pk']
        permissions = (("view_salesinvoice", "Can view sales invoice"),
                       ("approve_assignedsi", "Can approve assigned si"),
                       ("approve_allsi", "Can approve all si"))

    def get_absolute_url(self):
        return reverse('salesinvoice:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.sinum

    def __unicode__(self):
        return self.sinum
    
    
class Sidetail(models.Model):
    item_counter = models.IntegerField()
    simain = models.ForeignKey('salesinvoice.Simain', related_name='simain_sidetail_id', null=True, blank=True)
    si_num = models.CharField(max_length=10)
    si_date = models.DateField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='chartofaccount_sidetail_id')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_sidetail_id', null=True,
                                    blank=True)
    department = models.ForeignKey('department.Department', related_name='department_sidetail_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_sidetail_id', null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_sidetail_id', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_sidetail_id', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_sidetail_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_sidetail_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_sidetail_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_sidetail_id', null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_sidetail_id', null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_sidetail_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_sidetail_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_sidetail_id', null=True, blank=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='sidetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='sidetail_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='sidetail_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='sidetail_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'sidetail'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('sidetail:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Sidetail.STATUS_CHOICES)[self.status]


class Sidetailbreakdown(models.Model):
    item_counter = models.IntegerField()
    simain = models.ForeignKey('salesinvoice.Simain', related_name='simain_sidetailbreakdown_id', null=True,
                                blank=True)
    sidetail = models.ForeignKey('salesinvoice.Sidetail', related_name='sidetail_sidetailbreakdown_id', null=True,
                                    blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    si_num = models.CharField(max_length=10)
    si_date = models.DateField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount',
                                        related_name='chartofaccount_sidetailbreakdown_id')
    particular = models.TextField(null=True, blank=True)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_sidetailbreakdown_id',
                                    null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='department_sidetailbreakdown_id', null=True,
                                    blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_sidetailbreakdown_id', null=True,
                                    blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_sidetailbreakdown_id', null=True,
                                    blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_sidetailbreakdown_id', null=True,
                                    blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_sidetailbreakdown_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_sidetailbreakdown_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_sidetailbreakdown_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_sidetailbreakdown_id', null=True,
                                    blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_sidetailbreakdown_id', null=True,
                                    blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_sidetailbreakdown_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_sidetailbreakdown_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_sidetailbreakdown_id', null=True,
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
    enterby = models.ForeignKey(User, default=1, related_name='sidetailbreakdown_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='sidetailbreakdown_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='sidetailbreakdown_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='sidetailbreakdown_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'sidetailbreakdown'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('sidetailbreakdown:sidetailbreakdown', kwargs={'pk': self.pk})

    def __str__(self):
        return self.sidetail

    def __unicode__(self):
        return unicode(self.sidetail)

    def status_verbose(self):
        return dict(Sidetailbreakdown.STATUS_CHOICES)[self.status]


class Sidetailtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    simain = models.CharField(max_length=10, null=True, blank=True)
    sidetail = models.CharField(max_length=10, null=True, blank=True)
    si_num = models.CharField(max_length=10)
    si_date = models.DateField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='sidetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='sidetailtemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='sidetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='sidetailtemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'sidetailtemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('sidetailtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Sidetailtemp.STATUS_CHOICES)[self.status]


class Sidetailbreakdowntemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    sidetailtemp = models.CharField(max_length=10, null=True, blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    simain = models.CharField(max_length=10, null=True, blank=True)
    sidetail = models.CharField(max_length=10, null=True, blank=True)
    sidetailbreakdown = models.CharField(max_length=10, null=True, blank=True)
    si_num = models.CharField(max_length=10)
    si_date = models.DateField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='sidetailbreakdowntemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='sidetailbreakdowntemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='sidetailbreakdowntemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='sidetailbreakdowntemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'sidetailbreakdowntemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('sidetailbreakdowntemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk)

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Sidetailbreakdowntemp.STATUS_CHOICES)[self.status]


class Siupload(models.Model):
    simain = models.ForeignKey('salesinvoice.Simain', related_name='simain_siupload_id', null=True, blank=True)
    filename = models.CharField(max_length=250, null=True, blank=True)
    filetype = models.CharField(max_length=250, null=True, blank=True)
    enterby = models.ForeignKey(User, default=1, related_name='siupload_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='siupload_modify')
    modifydate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'siupload'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('siupload:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.filename

    def __unicode__(self):
        return self.filename
