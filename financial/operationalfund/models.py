from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import datetime


class Ofmain(models.Model):
    ofnum = models.CharField(max_length=10, unique=True)
    ofdate = models.DateField()
    oftype = models.ForeignKey('oftype.Oftype', related_name='ofmain_oftype_id', null=True, blank=True)
    requestor = models.ForeignKey('employee.Employee', related_name='ofmain_requestor_id')
    requestor_code = models.CharField(max_length=10)
    requestor_name = models.CharField(max_length=250)
    designatedapprover = models.ForeignKey('employee.Employee', related_name='ofmain_designated_approver')
    actualapprover = models.ForeignKey('employee.Employee', related_name='ofmain_actual_approver', null=True,
                                       blank=True)
    department = models.ForeignKey('department.Department', related_name='ofmain_department_id')
    department_code = models.CharField(max_length=10)
    department_name = models.CharField(max_length=150)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    approvedamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    particulars = models.TextField(null=True, blank=True)
    refnum = models.CharField(max_length=150, null=True, blank=True)
    cashadv_amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    creditterm = models.ForeignKey('creditterm.Creditterm', related_name='ofmain_creditterm_id', null=True, blank=True)
    OF_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
        ('C', 'Cancelled'),
        ('I', 'In Process'),
        ('H', 'OIC-Approved'),
        ('O', 'For JV'),
        ('P', 'JV in Process'),
        ('R', 'Released'),
    )
    ofstatus = models.CharField(max_length=1, choices=OF_STATUS_CHOICES, default='F')
    hrstatus = models.CharField(max_length=1, choices=OF_STATUS_CHOICES, default='F')
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
        ('F', 'For Approval'),
    )
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)

    hr_approved_lvl1 = models.CharField(max_length=1, choices=RESPONSE_CHOICES, default='F')
    hr_approved_lvl1_by = models.IntegerField(null=True, blank=True)
    hr_approved_lvl1_date = models.DateTimeField(null=True, blank=True)

    hr_approved_lvl2 = models.CharField(max_length=1, choices=RESPONSE_CHOICES, default='F')
    hr_approved_lvl2_by = models.IntegerField(null=True, blank=True)
    hr_approved_lvl2_date = models.DateTimeField(null=True, blank=True)

    nurse_approved = models.CharField(max_length=1, choices=RESPONSE_CHOICES, default='F')
    nurse_approved_date = models.DateTimeField(null=True, blank=True)

    remarks = models.CharField(max_length=250, null=True, blank=True)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='ofmain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ofmain_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ofmain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ofmain_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    # triggers In Process status START
    receiveby = models.ForeignKey(User, related_name='ofmain_receive', null=True, blank=True)
    receivedate = models.DateTimeField(null=True, blank=True)
    # triggers In Process status END
    releaseby = models.ForeignKey(User, related_name='ofmain_release', null=True, blank=True)
    releasedate = models.DateTimeField(null=True, blank=True)
    paymentreceivedby = models.ForeignKey('employee.Employee', related_name='ofmain_paymentreceived', null=True,
                                          blank=True)
    paymentreceiveddate = models.DateTimeField(null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='ofmain_branch_id', default=5)
    isdeleted = models.IntegerField(default=0)
    print_ctr1 = models.IntegerField(default=0)   # user
    print_ctr2 = models.IntegerField(default=0)   # cashier

    # pcv replenishment fields
    reppcvmain = models.ForeignKey('replenish_pcv.Reppcvmain', related_name='ofmain_reppcvmain_id', null=True,
                                   blank=True)
    reppcvdetail = models.ForeignKey('replenish_pcv.Reppcvdetail', related_name='ofmain_reppcvdetail_id', null=True,
                                     blank=True)
    cvmain = models.ForeignKey('checkvoucher.Cvmain', related_name='ofmain_cvmain_id', null=True, blank=True)
    # pcv replenishment fields

    # rfv replenishment fields
    reprfvmain = models.ForeignKey('replenish_rfv.Reprfvmain', related_name='ofmain_reprfvmain_id', null=True,
                                   blank=True)
    reprfvdetail = models.ForeignKey('replenish_rfv.Reprfvdetail', related_name='ofmain_reprfvdetail_id', null=True,
                                     blank=True)
    apmain = models.ForeignKey('accountspayable.Apmain', related_name='ofmain_apmain_id', null=True, blank=True)
    # rfv replenishment fields

    # cellphone subsidy vouchers
    jvmain = models.ForeignKey('journalvoucher.Jvmain', related_name='ofmain_jvmain_id', null=True, blank=True)

    class Meta:
        db_table = 'ofmain'
        ordering = ['-pk']
        permissions = (("view_operationalfund", "Can view operational fund"),
                       ("approve_assignedof", "Can approve assigned of"),
                       ("approve_allof", "Can approve all of"),
                       ("is_cashier", "Is from cashier's office"),
                       ("assign_requestor", "Can assign requestor"),)

    def get_absolute_url(self):
        return reverse('operationalfund:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.ofnum

    def __unicode__(self):
        return self.ofnum


class Ofitem(models.Model):
    item_counter = models.IntegerField()
    ofmain = models.ForeignKey('operationalfund.Ofmain', related_name='ofitem_ofmain_id', null=True, blank=True)
    ofnum = models.CharField(max_length=10)
    ofdate = models.DateField()
    oftype = models.ForeignKey('oftype.Oftype', related_name='ofitem_oftype_id', null=True, blank=True)
    ofsubtype = models.ForeignKey('ofsubtype.Ofsubtype', related_name='ofitem_ofsubtype_id', null=True, blank=True)
    payee = models.ForeignKey('supplier.Supplier', related_name='ofitem_payee_id', null=True, blank=True)
    payee_code = models.CharField(max_length=25, null=True, blank=True)
    payee_name = models.CharField(max_length=150)
    supplier = models.ForeignKey('supplier.Supplier', related_name='ofitem_supplier_id', null=True, blank=True)
    supplier_code = models.CharField(max_length=25, null=True, blank=True)
    supplier_name = models.CharField(max_length=150, null=True, blank=True)
    tin = models.CharField(max_length=150, null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=18)
    particulars = models.TextField()
    refnum = models.CharField(max_length=150, null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='ofitem_vat_id', validators=[MinValueValidator(1)], null=True,
                            blank=True)
    vatrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)], null=True,
                                  blank=True)
    atc = models.ForeignKey('ataxcode.Ataxcode', related_name='ofitem_atc_id', validators=[MinValueValidator(1)],
                            null=True, blank=True)
    atcrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)], null=True,
                                  blank=True)
    inputvattype = models.ForeignKey('inputvattype.Inputvattype', related_name='ofitem_inputvattype_id', null=True,
                                     blank=True)
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    deferredvat = models.CharField(max_length=1, choices=YESNO_CHOICES, null=True, blank=True, default='N')
    currency = models.ForeignKey('currency.Currency', related_name='ofitem_currency_id', default=1)
    fxrate = models.DecimalField(default=1.00, null=True, blank=True, decimal_places=5, max_digits=18)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    periodfrom = models.DateField(null=True, blank=True)
    periodto = models.DateField(null=True, blank=True)
    noofpax = models.IntegerField(null=True, blank=True)
    OF_ITEM_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    ofitemstatus = models.CharField(max_length=1, choices=OF_ITEM_STATUS_CHOICES, default='F')
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='ofitem_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ofitem_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ofitem_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ofitem_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    logs = models.TextField(null=True, blank=True)
    class Meta:
        db_table = 'ofitem'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ofitem:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ofitem.STATUS_CHOICES)[self.status]


class Ofdetail(models.Model):
    item_counter = models.IntegerField()
    ofmain = models.ForeignKey('operationalfund.Ofmain', related_name='ofmain_ofdetail_id', null=True, blank=True)
    of_num = models.CharField(max_length=10)
    of_date = models.DateField()
    ofitem = models.ForeignKey('operationalfund.Ofitem', related_name='ofitem_ofdetail_id', null=True, blank=True)
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='chartofaccount_ofdetail_id')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_ofdetail_id', null=True,
                                    blank=True)
    department = models.ForeignKey('department.Department', related_name='department_ofdetail_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_ofdetail_id', null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_ofdetail_id', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_ofdetail_id', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_ofdetail_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_ofdetail_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_ofdetail_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_ofdetail_id', null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_ofdetail_id', null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_ofdetail_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_ofdetail_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_ofdetail_id', null=True, blank=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='ofdetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ofdetail_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ofdetail_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ofdetail_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'ofdetail'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ofdetail:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ofdetail.STATUS_CHOICES)[self.status]


class Ofdetailbreakdown(models.Model):
    item_counter = models.IntegerField()
    ofmain = models.ForeignKey('operationalfund.Ofmain', related_name='ofmain_ofdetailbreakdown_id', null=True,
                               blank=True)
    ofdetail = models.ForeignKey('operationalfund.Ofdetail', related_name='ofdetail_ofdetailbreakdown_id', null=True,
                                 blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    of_num = models.CharField(max_length=10)
    of_date = models.DateField()
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount',
                                       related_name='chartofaccount_ofdetailbreakdown_id')
    particular = models.TextField(null=True, blank=True)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_ofdetailbreakdown_id',
                                    null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='department_ofdetailbreakdown_id', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='employee_ofdetailbreakdown_id', null=True,
                                 blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_ofdetailbreakdown_id', null=True,
                                 blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='customer_ofdetailbreakdown_id', null=True,
                                 blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='unit_ofdetailbreakdown_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_ofdetailbreakdown_id', null=True, blank=True)
    product = models.ForeignKey('product.Product', related_name='product_ofdetailbreakdown_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_ofdetailbreakdown_id', null=True,
                                 blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='outputvat_ofdetailbreakdown_id', null=True,
                                  blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='vat_ofdetailbreakdown_id', null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='wtax_ofdetailbreakdown_id', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_ofdetailbreakdown_id', null=True,
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
    enterby = models.ForeignKey(User, default=1, related_name='ofdetailbreakdown_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ofdetailbreakdown_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ofdetailbreakdown_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ofdetailbreakdown_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    customerbreakstatus = models.IntegerField(blank=True, null=True)
    supplierbreakstatus = models.IntegerField(blank=True, null=True)
    employeebreakstatus = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'ofdetailbreakdown'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ofdetailbreakdown:ofdetailbreakdown', kwargs={'pk': self.pk})

    def __str__(self):
        return self.ofdetail

    def __unicode__(self):
        return unicode(self.ofdetail)

    def status_verbose(self):
        return dict(Ofdetailbreakdown.STATUS_CHOICES)[self.status]


class Ofitemtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    ofmain = models.CharField(max_length=10, null=True, blank=True)
    ofitem = models.CharField(max_length=10, null=True, blank=True)
    ofnum = models.CharField(max_length=10)
    ofdate = models.DateField(blank=True, null=True)
    oftype = models.IntegerField(blank=True, null=True)
    ofsubtype = models.ForeignKey('ofsubtype.Ofsubtype', related_name='ofitemtemp_ofsubtype_id', null=True, blank=True)
    payee = models.IntegerField(blank=True, null=True)
    payee_code = models.CharField(max_length=25, null=True, blank=True)
    payee_name = models.CharField(max_length=150)
    supplier = models.IntegerField(blank=True, null=True)
    supplier_code = models.CharField(max_length=25, null=True, blank=True)
    supplier_name = models.CharField(max_length=150, null=True, blank=True)
    tin = models.CharField(max_length=150, null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=18)
    particulars = models.TextField(null=True, blank=True)
    refnum = models.CharField(max_length=150, null=True, blank=True)
    vat = models.IntegerField(blank=True, null=True)
    vatrate = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], null=True, blank=True)
    atc = models.IntegerField(blank=True, null=True)
    atcrate = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], null=True, blank=True)
    inputvattype = models.IntegerField(blank=True, null=True)
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    deferredvat = models.CharField(max_length=1, choices=YESNO_CHOICES, null=True, blank=True, default='N')
    currency = models.IntegerField(blank=True, null=True)
    fxrate = models.DecimalField(null=True, blank=True, decimal_places=5, max_digits=18)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    periodfrom = models.DateField(null=True, blank=True)
    periodto = models.DateField(null=True, blank=True)
    noofpax = models.IntegerField(null=True, blank=True)
    OF_ITEM_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    ofitemstatus = models.CharField(max_length=1, choices=OF_ITEM_STATUS_CHOICES, default='F')
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='ofitemtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ofitemtemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ofitemtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ofitemtemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'ofitemtemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ofitemtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ofitemtemp.STATUS_CHOICES)[self.status]


class Ofdetailtemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    ofmain = models.CharField(max_length=10, null=True, blank=True)
    ofdetail = models.CharField(max_length=10, null=True, blank=True)
    of_num = models.CharField(max_length=10)
    of_date = models.DateField(blank=True, null=True)
    ofitem = models.CharField(max_length=10, null=True, blank=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='ofdetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ofdetailtemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ofdetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ofdetailtemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'ofdetailtemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ofdetailtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ofdetailtemp.STATUS_CHOICES)[self.status]


class Ofdetailbreakdowntemp(models.Model):
    item_counter = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    ofdetailtemp = models.CharField(max_length=10, null=True, blank=True)
    datatype = models.CharField(max_length=1, null=True, blank=True)
    ofmain = models.CharField(max_length=10, null=True, blank=True)
    ofdetail = models.CharField(max_length=10, null=True, blank=True)
    ofdetailbreakdown = models.CharField(max_length=10, null=True, blank=True)
    of_num = models.CharField(max_length=10)
    of_date = models.DateField(blank=True, null=True)
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
    enterby = models.ForeignKey(User, default=1, related_name='ofdetailbreakdowntemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ofdetailbreakdowntemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='ofdetailbreakdowntemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='ofdetailbreakdowntemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'ofdetailbreakdowntemp'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('ofdetailbreakdowntemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk)

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Ofdetailbreakdowntemp.STATUS_CHOICES)[self.status]

class Ofupload(models.Model):
    ofmain = models.ForeignKey('operationalfund.Ofmain', related_name='ofmain_ofupload_id', null=True, blank=True)
    filename = models.CharField(max_length=250, null=True, blank=True)
    filetype = models.CharField(max_length=250, null=True, blank=True)
    enterby = models.ForeignKey(User, default=1, related_name='ofupload_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ofupload_modify')
    modifydate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ofupload'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('ofupload:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.filename

    def __unicode__(self):
        return self.filename
