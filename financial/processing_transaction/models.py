from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models

# Create your models here.


class Poapvtransaction(models.Model):  # can also be Pocvtransaction
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    pomain = models.ForeignKey('purchaseorder.Pomain', related_name='pomain_poapvtransaction')
    podetail = models.ForeignKey('purchaseorder.Podetail', related_name='podetail_poapvtransaction')
    apmain = models.ForeignKey('accountspayable.Apmain', related_name='apmain_poapvtransaction', null=True, blank=True)
    cvmain = models.ForeignKey('checkvoucher.Cvmain', related_name='cvmain_poapvtransaction', null=True, blank=True)
    apamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)  # can also be cvamount
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')

    class Meta:
        db_table = 'poapvtransaction'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('poapvtransaction:index', kwargs={'pk': self.pk})

    def __str__(self):
        return unicode(self.pk)

    def __unicode__(self):
        return unicode(self.pk)


class Poapvdetailtemp(models.Model):  # can also be Pocvdetailtemp
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    item_counter = models.IntegerField()
    sort_num = models.IntegerField()
    secretkey = models.CharField(max_length=255, null=True, blank=True)
    apmain = models.CharField(max_length=10, null=True, blank=True)  # can also be cvmain
    ap_num = models.CharField(max_length=10)
    ap_date = models.DateTimeField(blank=True, null=True)
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
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'poapvdetailtemp'
        ordering = ['-pk']
        # permissions = (("view_apmain", "Can view apmain"),)

    def get_absolute_url(self):
        return reverse('poapvdetailtemp:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Poapvdetailtemp.STATUS_CHOICES)[self.status]


class Apvcvtransaction(models.Model):
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    apmain = models.ForeignKey('accountspayable.Apmain', related_name='apmain_apvcvtransaction')
    cvmain = models.ForeignKey('checkvoucher.Cvmain', related_name='cvmain_apvcvtransaction', null=True, blank=True)
    new_apmain = models.ForeignKey('accountspayable.Apmain', related_name='new_apmain_apvcvtransaction', null=True,
                                   blank=True)
    cvamount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')

    class Meta:
        db_table = 'apvcvtransaction'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('apvcvtransaction:index', kwargs={'pk': self.pk})

    def __str__(self):
        return unicode(self.pk)

    def __unicode__(self):
        return unicode(self.pk)
