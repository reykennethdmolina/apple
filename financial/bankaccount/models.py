from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import datetime


class Bankaccount(models.Model):
    code = models.CharField(max_length=10, unique=True)
    bank = models.ForeignKey('bank.Bank', default=0, related_name='bank_id', validators=[MinValueValidator(1)])
    bankbranch = models.ForeignKey('bankbranch.Bankbranch', default=0, related_name='bankbranch_id',
                                   validators=[MinValueValidator(1)])
    bankaccounttype = models.ForeignKey('bankaccounttype.Bankaccounttype', default=0, related_name='bankaccounttype_id',
                                        validators=[MinValueValidator(1)])
    currency = models.ForeignKey('currency.Currency', default=0, related_name='currency_id', validators=[MinValueValidator(1)])
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', default=0, related_name='chartofaccount_id',
                                       validators=[MinValueValidator(1)], null=True, blank=True)
    accountnumber = models.CharField(max_length=30)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    DEBITCREDIT_CHOICES = (
        ('D', 'Debit'),
        ('C', 'Credit'),
    )
    beg_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    beg_code = models.CharField(max_length=1, null=True, blank=True, choices=DEBITCREDIT_CHOICES)
    beg_date = models.DateField(null=True, blank=True)
    run_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    run_code = models.CharField(max_length=1, null=True, blank=True, choices=DEBITCREDIT_CHOICES)
    run_date = models.DateField(null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='bankaccount_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='bankaccount_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'bankaccount'
        ordering = ['-pk']
        permissions = (("view_bankaccount", "Can view bankaccount"),)

    def get_absolute_url(self):
        return reverse('bankaccount:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Bankaccount.STATUS_CHOICES)[self.status]

    def beg_code_verbose(self):
        return dict(Bankaccount.DEBITCREDIT_CHOICES)[self.beg_code]

    def run_code_verbose(self):
        return dict(Bankaccount.DEBITCREDIT_CHOICES)[self.run_code]
