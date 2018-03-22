from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User

class Inventoryitem(models.Model):
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )

    inventoryitemclass = models.ForeignKey('inventoryitemclass.Inventoryitemclass', \
        related_name='invitem_inventoryitemclass_id', default='1')
    unitofmeasure = models.ForeignKey('unitofmeasure.Unitofmeasure', \
        related_name='invitem_unitofmeasure_id', default='1')
    code = models.CharField(max_length=25, unique=True)
    description = models.CharField(max_length=250)
    quantity = models.IntegerField(default=1)
    stocklevel = models.IntegerField(default=1)
    expensestatus = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    specialstatus = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    unitcost = models.DecimalField(default=0.00, null=True, blank=True, \
        decimal_places=2, max_digits=18)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='inventoryitem_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='inventoryitem_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'inventoryitem'
        ordering = ['-pk']
        permissions = (("view_inventoryitem", "Can view inventoryitem"),)

    def get_absolute_url(self):
        return reverse('inventoryitem:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Inventoryitem.STATUS_CHOICES)[self.status]

    def expensestatus_verbose(self):
        return dict(Inventoryitem.YESNO_CHOICES)[self.expensestatus]
