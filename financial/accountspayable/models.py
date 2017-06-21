from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Apmain(models.Model):
    AP_TYPE_CHOICES = (
        ('PO', 'PO'),
    )

    AP_STATUS_CHOICES = (
        ('V', 'Verified'),
    )

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

    apnum = models.CharField(max_length=10, unique=True)
    apdate = models.DateField()
    aptype = models.CharField(max_length=10, choices=AP_TYPE_CHOICES, default='PO')
    apstatus = models.CharField(max_length=1, choices=AP_STATUS_CHOICES, default='V')

    payee = models.ForeignKey('supplier.Supplier', related_name='ap_supplier_id')
    payeecode = models.CharField(max_length=10)

    branch = models.ForeignKey('branch.Branch', related_name='ap_branch_id')

    vat = models.ForeignKey('vat.Vat', related_name='ap_vat_id', null=True, blank=True)
    vatcode = models.CharField(max_length=10, null=True, blank=True)
    vatrate = models.IntegerField(default=0, null=True, blank=True)

    atax = models.ForeignKey('ataxcode.Ataxcode', related_name='ap_ataxcode_id', null=True, blank=True)
    ataxcode = models.CharField(max_length=10, null=True, blank=True)
    ataxrate = models.IntegerField(default=0, null=True, blank=True)

    bankbranchdisburse = models.ForeignKey('bankbranchdisburse.Bankbranchdisburse', related_name='ap_bankbranchdisburse_id')
    bankbranchdisbursebranch = models.CharField(max_length=10)

    inputvattype = models.ForeignKey('inputvattype.Inputvattype', related_name='ap_inputvattype_id')
    creditterm = models.ForeignKey('creditterm.Creditterm', related_name='ap_creditterm_id')
    duedate = models.DateField()
    refno = models.CharField(max_length=250)
    particulars = models.CharField(max_length=250)
    deferred = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    currency = models.ForeignKey('currency.Currency', related_name='ap_currency_id')
    fxrate = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=5, max_digits=18)

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='ap_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ap_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'accountspayable'
        ordering = ['-pk']
        permissions = (("view_accountspayable", "Can view accountspayable"),)

    def get_absolute_url(self):
        return reverse('accountspayable:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.apnum

    def __unicode__(self):
        return self.apnum

    def status_verbose(self):
        return dict(Apmain.STATUS_CHOICES)[self.status]
