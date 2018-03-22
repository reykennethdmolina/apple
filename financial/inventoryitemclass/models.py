from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User


class Inventoryitemclass(models.Model):
    inventoryitemtype = models.ForeignKey('inventoryitemtype.Inventoryitemtype', \
        related_name='invclass_inventoryitemtype_id', default='1')
    chartofaccountinventory = models.ForeignKey('chartofaccount.Chartofaccount', \
        related_name='invclass_chartofaccountinv_id', default='1')
    chartexpcostofsale = models.ForeignKey('chartofaccount.Chartofaccount', \
        related_name='invclass_chartexpcostofsale_id', default='1')
    chartexpgenandadmin = models.ForeignKey('chartofaccount.Chartofaccount', \
        related_name='invclass_chartexpgenandadmin_id', default='1')
    chartexpsellexp = models.ForeignKey('chartofaccount.Chartofaccount', \
        related_name='invclass_chartexpsellexp_id', default='1')
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='inventoryitemclass_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='inventoryitemclass_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    depreciationchartofaccount = models.ForeignKey('chartofaccount.Chartofaccount',
                                                   related_name='invclass_depreciationchartofaccount_id', null=True,
                                                   blank=True)

    class Meta:
        db_table = 'inventoryitemclass'
        ordering = ['-pk']
        permissions = (("view_inventoryitemclass", "Can view inventoryitemclass"),)

    def get_absolute_url(self):
        return reverse('inventoryitemclass:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Inventoryitemclass.STATUS_CHOICES)[self.status]
