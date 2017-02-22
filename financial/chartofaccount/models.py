from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
import datetime


class Chartofaccount(models.Model):
    DEBITCREDIT_CHOICES = (
        ('D', 'Debit'),
        ('C', 'Credit'),
    )

    POSTINGTITLE_CHOICES = (
        ('P', 'Posting'),
        ('T', 'Title'),
    )

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

    main = models.IntegerField(validators=[MaxValueValidator(9), MinValueValidator(0)])
    clas = models.IntegerField(validators=[MaxValueValidator(9), MinValueValidator(0)])
    item = models.IntegerField(validators=[MaxValueValidator(9), MinValueValidator(0)])
    cont = models.IntegerField(validators=[MaxValueValidator(9), MinValueValidator(0)])
    sub = models.CharField(max_length=6)
    accountcode = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    balancecode = models.CharField(max_length=1, choices=DEBITCREDIT_CHOICES, default='D')
    charttype = models.CharField(max_length=1, choices=DEBITCREDIT_CHOICES, default='D')
    accounttype = models.CharField(max_length=1, choices=POSTINGTITLE_CHOICES, default='P')
    ctax = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    taxstatus = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    wtaxstatus = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    mainposting = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    fixedasset = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    taxespayable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    product = models.ForeignKey('product.Product', related_name='product_id', null=True, blank=True, validators=[MaxValueValidator(99999), MinValueValidator(0)])
    typeofexpense = models.ForeignKey('typeofexpense.Typeofexpense', related_name='typeofexpense_id', null=True, blank=True, validators=[MaxValueValidator(99999), MinValueValidator(0)])
    kindofexpense = models.ForeignKey('kindofexpense.Kindofexpense', related_name='kindofexpense_id', null=True, blank=True, validators=[MaxValueValidator(99999), MinValueValidator(0)])
    bankaccount_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    department_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    employee_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    supplier_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    customer_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    branch_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    product_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    unit_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    mainunit = models.ForeignKey('mainunit.Mainunit', related_name='mainunit_chartofaccount_id', null=True, blank=True, validators=[MaxValueValidator(99999), MinValueValidator(0)])
    inputvat_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    outputvat_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    vat_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    wtax_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    ataxcode_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='chartofaccount_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='chartofaccount_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'chartofaccount'
        ordering = ['-pk']
        permissions = (("view_chartofaccount", "Can view chartofaccount"),)

    def get_absolute_url(self):
        return reverse('chartofaccount:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Chartofaccount.STATUS_CHOICES)[self.status]
