from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class Customer(models.Model):
    CREDITSTATUS_CHOICES = (
        ('Y', 'Yes'),
        ('B', 'Bad'),
        ('A', 'Auto-CF'),
    )
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
    customertype = models.ForeignKey('customertype.Customertype', \
        related_name='customertype_id', validators=[MinValueValidator(1)])
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=250)
    address1 = models.CharField(max_length=250)
    address2 = models.CharField(max_length=250, blank=True, null=True)
    address3 = models.CharField(max_length=250, blank=True, null=True)
    telno1 = models.CharField(max_length=20)
    telno2 = models.CharField(max_length=20, blank=True, null=True)
    telno3 = models.CharField(max_length=20, blank=True, null=True)
    faxno1 = models.CharField(max_length=20, blank=True, null=True)
    faxno2 = models.CharField(max_length=20, blank=True, null=True)
    tin = models.CharField(max_length=20, blank=True, null=True)
    pagerno = models.CharField(max_length=20, blank=True, null=True)
    payterms = models.CharField(max_length=20)
    creditterm = models.ForeignKey('creditterm.Creditterm', null=True, \
        blank=True, related_name='creditterm_id', default=2)
    creditlimit = models.DecimalField(max_digits=20, decimal_places=2, \
        null=True, blank=True)
    creditstatus = models.CharField(max_length=1, choices=CREDITSTATUS_CHOICES, \
        null=True, blank=True)
    creditrating = models.CharField(max_length=5, null=True, blank=True)
    contactperson = models.CharField(max_length=250, blank=True, null=True)
    contactposition = models.CharField(max_length=250, blank=True, null=True)
    contactemail = models.CharField(max_length=250, blank=True, null=True)
    remarks = models.CharField(max_length=250, blank=True, null=True)
    currency = models.ForeignKey('currency.Currency', related_name='customer_currency_id', \
        null=True, blank=True)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='bankaccount_id', \
        null=True, blank=True)
    industry = models.ForeignKey('industry.Industry', related_name='industry_id', \
        null=True, blank=True)
    multiplestatus = models.CharField(max_length=1, choices=YESNO_CHOICES, \
        default='Y')
    beg_amount = models.DecimalField(max_digits=20, decimal_places=2, \
        null=True, blank=True)
    beg_code = models.CharField(max_length=1, choices=DEBITCREDIT_CHOICES, \
        null=True, blank=True)
    beg_date = models.DateField(null=True, blank=True)
    end_amount = models.DecimalField(max_digits=20, decimal_places=2, \
        null=True, blank=True)
    end_code = models.CharField(max_length=1, choices=DEBITCREDIT_CHOICES, \
        null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, \
        default='A')
    enterby = models.ForeignKey(User, default=1, related_name='customer_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='customer_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    vat = models.ForeignKey('vat.Vat', related_name='customer_vat_id', validators=[MinValueValidator(1)], null=True,
                            blank=True)
    vatrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)])

    class Meta:
        db_table = 'customer'
        ordering = ['-pk']
        permissions = (("view_customer", "Can view customer"),)

    def get_absolute_url(self):
        return reverse('customer:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Customer.STATUS_CHOICES)[self.status]

    def serialize(self):
        return {
            'code': self.code,
            'name': self.name,
            'address1': self.address1,
            'address2': self.address2,
            'address3': self.address3,
            'telno1': self.telno1,
            'telno2': self.telno2,
            'telno3': self.telno3,
            'faxno1': self.faxno1,
            'faxno2': self.faxno2,
            'tin': self.tin,
            'pagerno': self.pagerno,
            'payterms': self.payterms,
            'creditlimit': self.creditlimit,
            # 'creditstatus': dict(Customer.CREDITSTATUS_CHOICES)[self.creditstatus],
            'creditrating': self.creditrating,
            'contactperson': self.contactperson,
            'contactposition': self.contactposition,
            'contactemail': self.contactemail,
            'remarks': self.remarks,
            'bankaccount': self.bankaccount,
            'creditterm': self.creditterm,
            'currency': self.currency,
            'customertype': self.customertype,
            'industry': self.industry,
            'multiplestatus': dict(Customer.YESNO_CHOICES)[self.multiplestatus],
            'beg_amount': self.beg_amount,
            'beg_code': self.beg_code,
            'beg_date': self.beg_date,
            'end_amount': self.end_amount,
            'end_code': self.end_code,
            'end_date': self.end_date,
            'status': dict(Customer.STATUS_CHOICES)[self.status],
            'enterdate': self.enterdate,
            'modifydate': self.modifydate,
            'enterby': self.enterby.username,
            'modifyby': self.modifyby.username,
        }
