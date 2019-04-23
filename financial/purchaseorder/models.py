from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import datetime


class Pomain(models.Model):
    ponum = models.CharField(max_length=10, unique=True)
    podate = models.DateField()
    refnum = models.CharField(max_length=150, null=True, blank=True)
    RF_TYPE_CHOICES = (
        ('REG', 'Regular'),
        ('EXD', 'Exdeal'),
    )
    potype = models.CharField(max_length=10, choices=RF_TYPE_CHOICES, default='REG')
    URGENCY_CHOICES = (
        ('N', 'Normal'),
        ('R', 'Rush'),
    )
    urgencytype = models.CharField(max_length=1, choices=URGENCY_CHOICES, default='N')
    dateneeded = models.DateField(null=True, blank=True)
    particulars = models.TextField()
    PO_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    postatus = models.CharField(max_length=1, choices=PO_STATUS_CHOICES, default='F')
    remarks = models.CharField(max_length=250, null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='pomain_supplier_id')
    supplier_code = models.CharField(max_length=25)
    supplier_name = models.CharField(max_length=250)
    apnum = models.CharField(max_length=150, null=True, blank=True)
    apdate = models.DateField(null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='pomain_inputvat_id', null=True, blank=True)
    creditterm = models.ForeignKey('creditterm.Creditterm', related_name='pomain_creditterm_id', null=True, blank=True)
    atc = models.ForeignKey('ataxcode.Ataxcode', related_name='pomain_atc_id', validators=[MinValueValidator(1)])
    atcrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)])
    atcamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vat = models.ForeignKey('vat.Vat', related_name='pomain_vat_id', validators=[MinValueValidator(1)])
    vatrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)])
    inputvattype = models.ForeignKey('inputvattype.Inputvattype', related_name='pomain_inputvattype_id')
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    deferredvat = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    currency = models.ForeignKey('currency.Currency', related_name='pomain_currency_id', default=1)
    fxrate = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=5, max_digits=18)
    wtax = models.ForeignKey('wtax.Wtax', related_name='pomain_wtax_id', validators=[MinValueValidator(1)], null=True,
                             blank=True)
    wtaxrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)])
    wtaxamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    totalquantity = models.IntegerField(default=0)
    totalamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    print_ctr = models.IntegerField(default=0)
    vatable = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatexempt = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatzerorated = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    grossamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    discountamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    netamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    designatedapprover = models.ForeignKey(User, default=2, related_name='pomain_designated_approver')
    actualapprover = models.ForeignKey(User, related_name='pomain_actual_approver', null=True, blank=True)
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    approverremarks = models.CharField(max_length=250, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    deliverydate = models.DateTimeField(null=True, blank=True)
    DELIVERY_STATUS_CHOICES = (
        ('O', 'Ordered'),
        ('P', 'Partial Delivery'),
        ('C', 'Complete'),
        ('S', 'Stop'),
    )
    deliverystatus = models.CharField(max_length=1, choices=DELIVERY_STATUS_CHOICES, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='pomain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='pomain_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='pomain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='pomain_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    # for APV
    apvamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    isfullyapv = models.IntegerField(default=0)
    totalremainingamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)  # upon creation, this is equal to totalamount
    # for APV

    class Meta:
        db_table = 'pomain'
        ordering = ['-pk']
        permissions = (("view_purchaseorder", "Can view purchaseorder"),
                       ("approve_assignedpo", "Can approve assigned po"),
                       ("approve_allpo", "Can approve all po"),)

    def get_absolute_url(self):
        return reverse('purchaseorder:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.ponum

    def __unicode__(self):
        return self.ponum


class Prfpotransaction(models.Model):
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    prfmain = models.ForeignKey('purchaserequisitionform.Prfmain', related_name='prfmain_prfpotransaction')
    prfdetail = models.ForeignKey('purchaserequisitionform.Prfdetail', related_name='prfdetail_prfpotransaction')
    pomain = models.ForeignKey('purchaseorder.Pomain', related_name='pomain_prfpotransaction')
    podetail = models.ForeignKey('purchaseorder.Podetail', related_name='podetail_prfpotransaction')
    poquantity = models.IntegerField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')

    class Meta:
        db_table = 'prfpotransaction'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('purchaseorder:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pomainz

    def __unicode__(self):
        return self.pomain.ponum


class Podetail(models.Model):
    pomain = models.ForeignKey('purchaseorder.Pomain', related_name='podetail_pomain_id', null=True, blank=True)
    item_counter = models.IntegerField()
    invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='podetail_invitem_id')
    invitem_code = models.CharField(max_length=25)
    invitem_name = models.CharField(max_length=250)
    invitem_unitofmeasure = models.CharField(max_length=50)
    unitofmeasure = models.ForeignKey('unitofmeasure.Unitofmeasure', related_name='podetail_unitofmeasure')
    quantity = models.IntegerField(default=0)
    unitcost = models.FloatField(default=0.00)
    currency = models.ForeignKey('currency.Currency', related_name='podetail_currency')
    branch = models.ForeignKey('branch.Branch', related_name='podetail_branch_id', null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='podetail_department_id', blank=True,
                                   null=True)
    department_code = models.CharField(max_length=10)
    department_name = models.CharField(max_length=250)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='podetail_vat_id')
    vatrate = models.IntegerField(default=0)
    vatable = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatexempt = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatzerorated = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    grossamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    discountrate = models.IntegerField(default=0, null=True, blank=True)
    discountamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    netamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    employee = models.ForeignKey('employee.Employee', related_name='podetail_employee_id', null=True, blank=True)
    employee_code = models.CharField(max_length=10, null=True, blank=True)
    employee_name = models.CharField(max_length=250, blank=True, null=True)
    assetnum = models.CharField(max_length=250, blank=True, null=True)
    serialnum = models.CharField(max_length=250, blank=True, null=True)
    expirationdate = models.DateTimeField(null=True, blank=True)
    atc = models.ForeignKey('ataxcode.Ataxcode', related_name='podetail_atc_id', validators=[MinValueValidator(1)],
                            null=True, blank=True)
    atcrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)])
    atcamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='podetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='podetail_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='podetail_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='podetail_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    prfmain = models.ForeignKey('purchaserequisitionform.Prfmain', related_name='prfmain_podetail', null=True,
                                blank=True)
    prfdetail = models.ForeignKey('purchaserequisitionform.Prfdetail', related_name='prfdetail_podetail', null=True,
                                  blank=True)

    # additional columns for PO-APV transactions
    isfullyapv = models.IntegerField(default=0)
    apvtotalamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    apvremainingamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)  # upon creation, this is equal to netamount
    inputvattype = models.ForeignKey('inputvattype.Inputvattype', related_name='podetail_inputvattype', null=True,
                                     blank=True)

    class Meta:
        db_table = 'podetail'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('purchaseorder:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name

    def __unicode__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name


class Podetailtemp(models.Model):
    pomain = models.ForeignKey('purchaseorder.Pomain', related_name='podetailtemp_pomain_id', null=True, blank=True)
    podetail = models.ForeignKey('purchaseorder.Podetail', related_name='podetailtemp_podetail_id', null=True,
                                 blank=True)
    item_counter = models.IntegerField()
    invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='podetailtemp_invitem_id')
    invitem_code = models.CharField(max_length=25)
    invitem_name = models.CharField(max_length=250)
    invitem_unitofmeasure = models.CharField(max_length=50)
    unitofmeasure = models.ForeignKey('unitofmeasure.Unitofmeasure', related_name='podetailtemp_unitofmeasure')
    quantity = models.IntegerField(default=0)
    unitcost = models.FloatField(default=0.00)
    currency = models.ForeignKey('currency.Currency', related_name='podetailtemp_currency')
    branch = models.ForeignKey('branch.Branch', related_name='podetailtemp_branch_id', null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='podetailtemp_department_id', blank=True,
                                   null=True)
    department_code = models.CharField(max_length=10)
    department_name = models.CharField(max_length=250)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='podetailtemp_vat_id')
    vatrate = models.IntegerField(default=0)
    vatable = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatexempt = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatzerorated = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    grossamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    discountrate = models.IntegerField(default=0, null=True, blank=True)
    discountamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    netamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    employee = models.ForeignKey('employee.Employee', related_name='podetailtemp_employee_id', null=True, blank=True)
    employee_code = models.CharField(max_length=10, null=True, blank=True)
    employee_name = models.CharField(max_length=250, blank=True, null=True)
    assetnum = models.CharField(max_length=250, blank=True, null=True)
    serialnum = models.CharField(max_length=250, blank=True, null=True)
    expirationdate = models.DateTimeField(null=True, blank=True)
    atc = models.ForeignKey('ataxcode.Ataxcode', related_name='podetailtemp_atc_id', validators=[MinValueValidator(1)],
                            null=True, blank=True)
    atcrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)])
    atcamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='podetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='podetailtemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='podetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='podetailtemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    secretkey = models.CharField(max_length=255)
    prfmain = models.ForeignKey('purchaserequisitionform.Prfmain', related_name='prfmain_podetailtemp', null=True,
                                blank=True)
    prfdetail = models.ForeignKey('purchaserequisitionform.Prfdetail', related_name='prfdetail_podetailtemp', null=True,
                              blank=True)

    # additional columns for PO-APV transactions
    isfullyapv = models.IntegerField(default=0)
    apvtotalamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    apvremainingamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2,
                                             max_digits=18)  # upon creation, this is equal to netamount
    inputvattype = models.ForeignKey('inputvattype.Inputvattype', related_name='podetailtemp_inputvattype', null=True,
                                     blank=True)

    class Meta:
        db_table = 'podetailtemp'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('purchaseorder:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name + ' temp'

    def __unicode__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name + ' temp'


class Podata(models.Model):
    pomain = models.ForeignKey('purchaseorder.Pomain', related_name='podata_pomain_id', null=True, blank=True)
    prfmain = models.ForeignKey('purchaserequisitionform.Prfmain', related_name='podata_prfmain_id')
    secretkey = models.CharField(max_length=255)
    isdeleted = models.IntegerField(default=0)
    enterdate = models.DateTimeField(auto_now_add=True)
    modifydate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'podata'
        ordering = ['-pk']
        # permissions = (("view_podata", "Can view podata"),)

    def get_absolute_url(self):
        return reverse('purchaseorder:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.id

    def __unicode__(self):
        return self.id
