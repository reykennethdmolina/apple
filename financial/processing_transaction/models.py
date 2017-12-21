from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models

# Create your models here.


class Poapvtransaction(models.Model):
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    pomain = models.ForeignKey('purchaseorder.Pomain', related_name='pomain_poapvtransaction')
    apmain = models.ForeignKey('accountspayable.Apmain', related_name='apmain_poapvtransaction')

    apamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')

    class Meta:
        db_table = 'poapvtransaction'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('poapvtransaction:index', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pomain

    def __unicode__(self):
        return self.pomain


class Apvcvtransaction(models.Model):
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    apmain = models.ForeignKey('accountspayable.Apmain', related_name='apmain_apvcvtransaction')
    cvmain = models.ForeignKey('checkvoucher.Cvmain', related_name='cvmain_apvcvtransaction')

    cvamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')

    class Meta:
        db_table = 'apvcvtransaction'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('apvcvtransaction:index', kwargs={'pk': self.pk})

    def __str__(self):
        return self.apmain

    def __unicode__(self):
        return self.apmain
