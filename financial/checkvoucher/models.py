from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import datetime


class Cvmain(models.Model):
    cvnum = models.CharField(max_length=10, unique=True)
    cvdate = models.DateField()
    cvtype = models.ForeignKey('cvtype.Cvtype', related_name='cvmain_cvtype_id', null=True, blank=True)
    CV_STATUS_CHOICES = (
        ('I', 'In Process'),
        ('R', 'RELEASED'),
    )
    cvstatus = models.CharField(max_length=1, choices=CV_STATUS_CHOICES, default='I')
    payee = models.ForeignKey('supplier.Supplier', related_name='cvmain_payee_id', null=True, blank=True)
    payee_code = models.CharField(max_length=25, null=True, blank=True)
    payee_name = models.CharField(max_length=150)
    checknum = models.CharField(max_length=150)
    checkdate = models.DateTimeField()
    vat = models.ForeignKey('vat.Vat', related_name='cvmain_vat_id', validators=[MinValueValidator(1)])
    vatrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)])
    atc = models.ForeignKey('ataxcode.Ataxcode', related_name='cvmain_atc_id', validators=[MinValueValidator(1)])
    atcrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)])
    currency = models.ForeignKey('currency.Currency', related_name='cvmain_currency_id', default=1)
    fxrate = models.DecimalField(default=0.00, decimal_places=5, max_digits=18)
    inputvattype = models.ForeignKey('inputvattype.Inputvattype', related_name='cvmain_inputvattype_id')
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    deferredvat = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    branch = models.ForeignKey('branch.Branch', related_name='cvmain_branch_id', default='5')
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='cvmain_bankaccount_id')
    disbursingbranch = models.ForeignKey('bankbranchdisburse.Bankbranchdisburse',
                                         related_name='cvmain_bankbranchdisburse_id')
    amount = models.DecimalField(decimal_places=2, max_digits=18, validators=[MaxValueValidator(1000),
                                                                              MinValueValidator(1)], default=0.00)
    particulars = models.TextField()
    refnum = models.CharField(max_length=150, null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='cvmain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='cvmain_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='cvmain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    releaseby = models.ForeignKey(User, related_name='cvmain_release', null=True, blank=True)
    releasedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'cvmain'
        ordering = ['-pk']
        permissions = (("view_checkvoucher", "Can view check voucher"),)

    def get_absolute_url(self):
        return reverse('checkvoucher:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.cvnum

    def __unicode__(self):
        return self.cvnum
