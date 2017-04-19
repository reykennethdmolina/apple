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
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postdate = models.DateTimeField(null=True, blank=True)
    enterby = models.ForeignKey(User, default=1, related_name='csmain_enter')
    modifyby = models.ForeignKey(User, default=1, related_name='csmain_modify')
    postby = models.ForeignKey(User, related_name='csmain_post', null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    designatedapprover = models.ForeignKey(User, default=2, related_name='csdesignated_approver')
    actualapprover = models.ForeignKey(User, related_name='csactual_approver', null=True, blank=True)


    class Meta:
        db_table = 'csmain'
        ordering = ['-pk']
        # permissions = (("view_canvasssheet", "Can view canvasssheet"),)

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


class Csdetail(models.Model):
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='csdetail_invitem_id')
    invitem_code = models.CharField(max_length=25) # get data from prf imported
    invitem_name = models.CharField(max_length=250)
    currency = models.ForeignKey('currency.Currency', related_name='csdetail_currency')
    item_counter = models.IntegerField()
    supplier = models.ForeignKey('supplier.Supplier', related_name='csdetail_supplier_id')
    suppliercode = models.CharField(max_length=10, null=True, blank=True,)
    suppliername = models.CharField(max_length=250, null=True, blank=True,)
    vat = models.ForeignKey('vat.Vat', related_name='csdetail_vat_id')
    vatrate = models.IntegerField(default=0)
    unitcost = models.DecimalField(default=0.00, decimal_places=2, max_digits=18)
    negocost = models.DecimalField(default=0.00, decimal_places=2, max_digits=18)
    csmain = models.ForeignKey('canvasssheet.Csmain', related_name='csdetail_csmain_id')
    csstatus = models.IntegerField(default=0)

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='csdetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='csdetail_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, default=1, related_name='csdetail_post', null=True, blank=True)
    postdate = models.DateTimeField(default=datetime.datetime.now(), null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    # remarks = models.CharField(max_length=250, null=True, blank=True)

    # vat
    vatable = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatexempt = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatzerorated = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    grossamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    vatamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    netamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)

    class Meta:
        db_table = 'csdetail'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('canvasssheet:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name

    def __unicode__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name
#
#
# class Prfdetailtemp(models.Model):
#     STATUS_CHOICES = (
#         ('A', 'Active'),
#         ('I', 'Inactive'),
#         ('C', 'Cancelled'),
#         ('O', 'Posted'),
#         ('P', 'Printed'),
#     )
#
#     prfmain = models.ForeignKey('purchaserequisitionform.Prfmain', related_name='temp_prfmain_id', null=True, blank=True)
#     rfdetail = models.ForeignKey('requisitionform.Rfdetail', related_name='temp_rfdetail_id', null=True, blank=True)
#     prfdetail = models.ForeignKey('purchaserequisitionform.Prfdetail', related_name='temp_prfdetail_id', null=True, blank=True)
#     invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='temp_prfdetail_invitem_id')
#     invitem_code = models.CharField(max_length=25)
#     invitem_name = models.CharField(max_length=250)
#     item_counter = models.IntegerField()
#     quantity = models.IntegerField()
#     # remarks = models.CharField(max_length=250, null=True, blank=True)
#     status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
#     enterby = models.ForeignKey(User, default=1, related_name='prfdetailtemp_enter')
#     enterdate = models.DateTimeField(auto_now_add=True)
#     modifyby = models.ForeignKey(User, default=1, related_name='prfdetailtemp_modify')
#     modifydate = models.DateTimeField(default=datetime.datetime.now())
#     postby = models.ForeignKey(User, related_name='prfdetailtemp_post', null=True, blank=True)
#     postdate = models.DateTimeField(null=True, blank=True)
#     isdeleted = models.IntegerField(default=0)
#     secretkey = models.CharField(max_length=255)
#
#     class Meta:
#         db_table = 'prfdetailtemp'
#         ordering = ['-pk']
#
#     def get_absolute_url(self):
#         return reverse('purchaserequisitionform:detail', kwargs={'pk': self.pk})
#
#     def __str__(self):
#         return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name
#
#     def __unicode__(self):
#         return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name
