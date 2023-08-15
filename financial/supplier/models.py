from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class Supplier(models.Model):
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=250)
    address1 = models.CharField(max_length=250)
    address2 = models.CharField(max_length=250, blank=True, null=True)
    address3 = models.CharField(max_length=250, blank=True, null=True)
    tin = models.CharField(max_length=20)
    telno = models.CharField(max_length=20, blank=True, null=True)
    faxno = models.CharField(max_length=20, blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)

    multiplestatus = models.CharField(max_length=1, choices=YESNO_CHOICES,
                                      default='Y', null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='supplier_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='supplier_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    triplec = models.IntegerField(default=0)
    ccc = models.CharField(max_length=10) # COL, COR, CON

    # added/modified fields
    contactperson = models.CharField(max_length=250)
    creditterm = models.ForeignKey('creditterm.Creditterm',
                                   related_name='supplier_creditterm_id')
    inputvattype = models.ForeignKey('inputvattype.Inputvattype',
                                     related_name='supplier_inputvattype_id', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat',
                                     related_name='supplier_inputvat_id', null=True, blank=True)
    deferredvat = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    vat = models.ForeignKey('vat.Vat', related_name='supplier_vat_id',
                            validators=[MinValueValidator(1)])
    vatrate = models.IntegerField(default=0, validators=[MinValueValidator(1),
                                                         MaxValueValidator(100)])
    atc = models.ForeignKey('ataxcode.Ataxcode', related_name='supplier_atc_id',
                            validators=[MinValueValidator(1)])
    atcrate = models.IntegerField(default=0, validators=[MinValueValidator(1),
                                                         MaxValueValidator(100)])
    currency = models.ForeignKey('currency.Currency', related_name='supplier_currency_id',
                                 default=1)
    fxrate = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=5,
                                 max_digits=18)

    industry = models.ForeignKey('industry.Industry', related_name='supplier_industry_id',
                                 validators=[MinValueValidator(1)])
    suppliertype = models.ForeignKey('suppliertype.Suppliertype',
                                     related_name='supplier_suppliertype_id',
                                     validators=[MinValueValidator(1)])
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='supplier_bankaccount_id', null=True,
                                    blank=True)
    bankbranchdisburse = models.ForeignKey('bankbranchdisburse.Bankbranchdisburse',
                                           related_name='supplier_bankbranchdisburse_id', null=True, blank=True)
    paytype = models.ForeignKey('paytype.Paytype', related_name='supplier_paytype_id', null=True, blank=True)
    ccc_code = models.CharField(max_length=10, null=True, blank=True)
    ccc_code2 = models.CharField(max_length=10, null=True, blank=True)
    ccc_code3 = models.CharField(max_length=10, null=True, blank=True)
    serv_code = models.CharField(max_length=10, null=True, blank=True)
    remarks = models.CharField(max_length=250, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'supplier'
        ordering = ['-pk']
        permissions = (("view_supplier", "Can view supplier"),)

    def get_absolute_url(self):
        return reverse('supplier:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Supplier.STATUS_CHOICES)[self.status]

    def serialize(self):
        return {
            'code': self.code,
            'name': self.name,
            'address1': self.address1,
            'address2': self.address2,
            'address3': self.address3,
            'tin': self.tin,
            'telno': self.telno,
            'faxno': self.faxno,
            'zipcode': self.zipcode,
            #'inputvatrate': self.inputvatrate,
            'multiplestatus': dict(Supplier.YESNO_CHOICES)[self.multiplestatus],
            'status': dict(Supplier.STATUS_CHOICES)[self.status],
            'enterdate': self.enterdate,
            'modifydate': self.modifydate,
            'enterby': self.enterby.username,
            'modifyby': self.modifyby.username,
            #'ataxcode': self.atc,
            'inputvat': self.inputvat,
            'vat': self.vat,
        }
