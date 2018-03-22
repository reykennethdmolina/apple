from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User


class Debitcreditmemosubtype(models.Model):
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    DEBITCREDIT_CHOICES = (
        ('D', 'Debit'),
        ('C', 'Credit'),
    )
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    group = models.CharField(max_length=1, choices=DEBITCREDIT_CHOICES, validators=[MinValueValidator(1)], null=True,
                             blank=True)
    applicationstatus = models.CharField(max_length=1, choices=YESNO_CHOICES, validators=[MinValueValidator(1)],
                                         null=True, blank=True)
    debit1chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='debit1chartofaccount_id',
                                             validators=[MinValueValidator(1)], null=True, blank=True)
    debit2chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='debit2chartofaccount_id',
                                             validators=[MinValueValidator(1)], null=True, blank=True)
    credit1chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='credit1chartofaccount_id',
                                              validators=[MinValueValidator(1)], null=True, blank=True)
    credit2chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='credit2chartofaccount',
                                              validators=[MinValueValidator(1)], null=True, blank=True)
    dcclasstype = models.ForeignKey('dcclasstype.Dcclasstype', related_name='dcclasstype', null=True, blank=True)
    particular = models.CharField(max_length=250, blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='debitcreditmemosubtype_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='debitcreditmemosubtype_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'debitcreditmemosubtype'
        ordering = ['-pk']
        permissions = (("view_debitcreditmemosubtype", "Can view debitcreditmemosubtype"),)

    def get_absolute_url(self):
        return reverse('debitcreditmemosubtype:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Debitcreditmemosubtype.STATUS_CHOICES)[self.status]
