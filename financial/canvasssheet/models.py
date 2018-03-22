from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
import datetime


class Csmain(models.Model):
    CS_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )

    CS_TYPE_CHOICES = (
        ('REGULAR', 'REGULAR'),
    )

    csnum = models.CharField(max_length=10, unique=True)
    csdate = models.DateField()
    cstype = models.CharField(max_length=10, choices=CS_TYPE_CHOICES, default='REGULAR')
    csstatus = models.CharField(max_length=1, choices=CS_STATUS_CHOICES, default='F')
    particulars = models.TextField()
    remarks = models.CharField(max_length=250, null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifydate = models.DateTimeField(auto_now_add=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    enterby = models.ForeignKey(User, default=1, related_name='csmain_enter')
    modifyby = models.ForeignKey(User, default=1, related_name='csmain_modify')
    postby = models.ForeignKey(User, related_name='csmain_post', null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='csmain_close', null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    designatedapprover = models.ForeignKey(User, default=2, related_name='csdesignated_approver')
    actualapprover = models.ForeignKey(User, related_name='csactual_approver', null=True, blank=True)
    quantity = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    # nego vat
    vatable = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatexempt = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatzerorated = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    grosscost = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    grossamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    netamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)

    # uc vat
    uc_vatable = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_vatexempt = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_vatzerorated = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_grosscost = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_grossamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_vatamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_netamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)

    class Meta:
        db_table = 'csmain'
        ordering = ['-pk']
        permissions = (("view_canvasssheet", "Can view canvasssheet"),)

    def get_absolute_url(self):
        return reverse('canvasssheet:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.csnum

    def __unicode__(self):
        return self.csnum


class Cshistory(models.Model):
    invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='cshistory_invitem_id')
    supplier = models.ForeignKey('supplier.Supplier', related_name='cshistory_supplier_id')
    datetransaction = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    processingdate = models.IntegerField(validators=[MaxValueValidator(9), MinValueValidator(0)])


    class Meta:
        db_table = 'cshistory'
        ordering = ['-pk']
        # permissions = (("view_cshistory", "Can view cshistory"),)

    def get_absolute_url(self):
        return reverse('canvasssheet:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.id

    def __unicode__(self):
        return self.id


class Csdata(models.Model):
    csmain = models.ForeignKey('canvasssheet.Csmain', related_name='csdata_csmain_id', null=True, blank=True)
    prfmain = models.ForeignKey('purchaserequisitionform.Prfmain', related_name='csdata_prfmain_id')
    secretkey = models.CharField(max_length=255)
    isdeleted = models.IntegerField(default=0)
    enterdate = models.DateTimeField(auto_now_add=True)
    modifydate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'csdata'
        ordering = ['-pk']
        # permissions = (("view_csdata", "Can view csdata"),)

    def get_absolute_url(self):
        return reverse('canvasssheet:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.id

    def __unicode__(self):
        return self.id


class Csdetail(models.Model):
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    prfmain = models.ForeignKey('purchaserequisitionform.Prfmain', related_name='prfmain_csdetail', null=True, blank=True)
    prfdetail = models.ForeignKey('purchaserequisitionform.Prfdetail', related_name='prfdetail_csdetail', null=True, blank=True)
    invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='csdetail_invitem_id')
    invitem_code = models.CharField(max_length=25) # get data from prf imported
    invitem_name = models.CharField(max_length=250)
    quantity = models.IntegerField()
    currency = models.ForeignKey('currency.Currency', related_name='csdetail_currency')
    item_counter = models.IntegerField()
    supplier = models.ForeignKey('supplier.Supplier', related_name='csdetail_supplier_id')
    suppliercode = models.CharField(max_length=10, null=True, blank=True,)
    suppliername = models.CharField(max_length=250, null=True, blank=True,)
    vat = models.ForeignKey('vat.Vat', related_name='csdetail_vat_id')
    vatrate = models.IntegerField(default=0)
    unitcost = models.DecimalField(default=0.00, decimal_places=2, max_digits=18)
    negocost = models.DecimalField(default=0.00, decimal_places=2, max_digits=18)
    csmain = models.ForeignKey('canvasssheet.Csmain', related_name='csdetail_csmain_id', null=True, blank=True)
    csstatus = models.IntegerField(default=0)

    department_code = models.CharField(max_length=25, null=True, blank=True,)
    department_name = models.CharField(max_length=250, null=True, blank=True,)
    department = models.ForeignKey('department.Department', related_name='csdetail_department_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='csdetail_branch_id', null=True, blank=True)
    invitem_unitofmeasure = models.ForeignKey('unitofmeasure.Unitofmeasure', related_name='csdetail_unitofmeasure_id', null=True, blank=True)
    invitem_unitofmeasure_code = models.CharField(max_length=50, null=True, blank=True)
    estimateddateofdelivery = models.DateTimeField(null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    itemdetailkey = models.CharField(max_length=255)
    enterby = models.ForeignKey(User, default=1, related_name='csdetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='csdetail_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='csdetail_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='csdetail_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    # nego vat
    vatable = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatexempt = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatzerorated = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    grosscost = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    grossamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    netamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)

    # uc vat
    uc_vatable = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_vatexempt = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_vatzerorated = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_grosscost = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_grossamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_vatamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_netamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)

    class Meta:
        db_table = 'csdetail'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('canvasssheet:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name

    def __unicode__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name


class Csdetailtemp(models.Model):
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    prfmain = models.ForeignKey('purchaserequisitionform.Prfmain', related_name='prfmain_csdetailtemp', null=True, blank=True)
    prfdetail = models.ForeignKey('purchaserequisitionform.Prfdetail', related_name='prfdetail_csdetailtemp', null=True, blank=True)
    invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='csdetailtemp_invitem_id')
    invitem_code = models.CharField(max_length=25) # get data from prf imported
    invitem_name = models.CharField(max_length=250)
    quantity = models.IntegerField()
    currency = models.ForeignKey('currency.Currency', related_name='csdetailtemp_currency')
    item_counter = models.IntegerField()
    supplier = models.ForeignKey('supplier.Supplier', related_name='csdetailtemp_supplier_id')
    suppliercode = models.CharField(max_length=10, null=True, blank=True,)
    suppliername = models.CharField(max_length=250, null=True, blank=True,)
    vat = models.ForeignKey('vat.Vat', related_name='csdetailtemp_vat_id')
    vatrate = models.IntegerField(default=0)
    unitcost = models.DecimalField(default=0.00, decimal_places=2, max_digits=18)
    negocost = models.DecimalField(default=0.00, decimal_places=2, max_digits=18)
    secretkey = models.CharField(max_length=255)
    itemdetailkey = models.CharField(max_length=255)
    csmain = models.ForeignKey('canvasssheet.Csmain', related_name='csdetailtemp_csmain_id', null=True, blank=True)
    csdetail = models.ForeignKey('canvasssheet.Csdetail', related_name='csdetailtemp_csdetail_id', null=True, blank=True)
    csstatus = models.IntegerField(default=0)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='csdetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='csdetailtemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='csdetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='csdetailtemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    department_code = models.CharField(max_length=25, null=True, blank=True)
    department_name = models.CharField(max_length=250, null=True, blank=True)
    department = models.ForeignKey('department.Department', related_name='csdetailtemp_department_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='csdetailtemp_branch_id', null=True, blank=True)
    invitem_unitofmeasure = models.ForeignKey('unitofmeasure.Unitofmeasure', related_name='csdetailtemp_unitofmeasure_id', null=True, blank=True)
    invitem_unitofmeasure_code = models.CharField(max_length=50, null=True, blank=True)
    estimateddateofdelivery = models.DateTimeField(null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)

    # nego vat
    vatable = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatexempt = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatzerorated = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    grosscost = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    grossamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    netamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)

    # uc vat
    uc_vatable = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_vatexempt = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_vatzerorated = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_grosscost = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_grossamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_vatamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    uc_netamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)

    class Meta:
        db_table = 'csdetailtemp'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('canvasssheet:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name

    def __unicode__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name
