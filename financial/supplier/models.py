from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import datetime


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
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='ataxcode_id', validators=[MinValueValidator(1)])
    vat = models.ForeignKey('vat.Vat', related_name='vat_id', validators=[MinValueValidator(1)])
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='inputvat_id', validators=[MinValueValidator(1)])
    inputvatrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)])
    multiplestatus = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N', null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='supplier_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='supplier_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

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

