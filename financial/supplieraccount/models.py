from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

class Supplieraccount(models.Model):
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplieraccount_supplier_id',
                             validators=[MinValueValidator(1)])
    accountno = models.CharField(max_length=10, unique=True)
    employee = models.ForeignKey('employee.Employee', related_name='supplieraccount_employee_id',
                             validators=[MinValueValidator(1)], null=True, blank=True)
    name = models.CharField(max_length=250, blank=True, null=True)
    phoneno = models.CharField(max_length=20, blank=True, null=True)
    duono = models.CharField(max_length=20, blank=True, null=True)
    serialno = models.CharField(max_length=20, blank=True, null=True)
    imeino = models.CharField(max_length=20, blank=True, null=True)
    subsidyamount = models.DecimalField(default=0.00, null=True, blank=True, \
        decimal_places=2, max_digits=18)
    ACCOUNT_GROUP_CHOICES = (
        ('B', 'HO/Business Group'),
        ('E', 'Editorial Group'),
        ('R', 'Branches'),
        ('L', 'LRP Bldg/Finance Group'),
        ('M', 'Modem Lines'),
        ('W', 'WeRoam'),
        ('C', 'Corporate Account'),
        ('O', 'Others'),
    )
    accountgroup = models.CharField(max_length=1, choices=ACCOUNT_GROUP_CHOICES)
    ACCOUNT_CATEGORY_CHOICES = (
        ('T', 'Trunk Line'),
        ('D', 'Direct Line'),
        ('F', 'Telefax'),
        ('C', 'Cellphone'),
        ('M', 'Modem Lines'),
        ('W', 'WeRoam'),
        ('O', 'Others'),
    )
    accountcategory = models.CharField(max_length=1, choices=ACCOUNT_CATEGORY_CHOICES)
    remarks = models.CharField(max_length=250, blank=True, null=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='supplieraccount_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='supplieraccount_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'supplieraccount'
        ordering = ['-pk']
        permissions = (("view_supplieraccount", "Can view supplieraccount"),)

    def get_absolute_url(self):
        return reverse('supplieraccount:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Supplieraccount.STATUS_CHOICES)[self.status]