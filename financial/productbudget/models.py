from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
import datetime


class Productbudget(models.Model):
    year = models.PositiveSmallIntegerField(validators=[MaxValueValidator(2100), MinValueValidator(1980)])
    product = models.ForeignKey('product.Product', related_name='product_productbudget_id')
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='chartofaccount_productbudget_id')
    remarks = models.CharField(max_length=255, blank=True, null=True)
    formula = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=255, blank=True, null=True)
    mjan = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    mfeb = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    mmar = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    mapr = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    mmay = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    mjun = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    mjul = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    maug = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    msep = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    moct = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    mnov = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    mdec = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='productbudget_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='productbudget_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'productbudget'
        ordering = ['-pk']
        permissions = (("view_productbudget", "Can view productbudget"),)
        unique_together = (('year', 'product', 'chartofaccount'),)

    def get_absolute_url(self):
        return reverse('productbudget:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Productbudget.STATUS_CHOICES)[self.status]
