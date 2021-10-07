from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User

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
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)
    is_wtax = models.IntegerField(default=0)
    nontrade = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    setup_customer = models.CharField(max_length=250)
    setup_supplier = models.CharField(max_length=250)

    # added for debitcreditmemo
    reftype_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    refnum_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    refdate_enable = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    # added for debitcreditmemo

    # added for main and sub grouping
    subgroup = models.ForeignKey('chartofaccountsubgroup.ChartofAccountSubGroup',
                                  related_name='chartofaccount_subgroup')
    # added for main and sub grouping

    # added for subledgersummary
    beginning_amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    beginning_code = models.CharField(max_length=10, null=True, blank=True)
    beginning_date = models.DateTimeField(null=True, blank=True)
    end_amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    end_code = models.CharField(max_length=10, null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    year_to_date_amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    year_to_date_code = models.CharField(max_length=10, null=True, blank=True)
    year_to_date_date = models.DateTimeField(null=True, blank=True)
    # added for subledgersummary

    class Meta:
        db_table = 'chartofaccount'
        ordering = ['-pk']
        permissions = (("view_chartofaccount", "Can view chartofaccount"),)

    def get_absolute_url(self):
        return reverse('chartofaccount:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.accountcode

    def __unicode__(self):
        return self.accountcode

    def status_verbose(self):
        return dict(Chartofaccount.STATUS_CHOICES)[self.status]

    def serialize(self):
        return {
            'accountcode': self.accountcode,
            'title': self.title,
            'description': self.description,
            'balancecode': dict(Chartofaccount.DEBITCREDIT_CHOICES)[self.balancecode],
            'charttype': dict(Chartofaccount.DEBITCREDIT_CHOICES)[self.charttype],
            'accounttype': dict(Chartofaccount.POSTINGTITLE_CHOICES)[self.accounttype],
            'ctax': dict(Chartofaccount.YESNO_CHOICES)[self.ctax],
            'taxstatus': dict(Chartofaccount.YESNO_CHOICES)[self.taxstatus],
            'wtaxstatus': dict(Chartofaccount.YESNO_CHOICES)[self.wtaxstatus],
            'mainposting': dict(Chartofaccount.YESNO_CHOICES)[self.mainposting],
            'fixedasset': dict(Chartofaccount.YESNO_CHOICES)[self.fixedasset],
            'taxespayable': dict(Chartofaccount.YESNO_CHOICES)[self.taxespayable],
            'bankaccount_enable': dict(Chartofaccount.YESNO_CHOICES)[self.bankaccount_enable],
            'department_enable': dict(Chartofaccount.YESNO_CHOICES)[self.department_enable],
            'employee_enable': dict(Chartofaccount.YESNO_CHOICES)[self.employee_enable],
            'supplier_enable': dict(Chartofaccount.YESNO_CHOICES)[self.supplier_enable],
            'customer_enable': dict(Chartofaccount.YESNO_CHOICES)[self.customer_enable],
            'branch_enable': dict(Chartofaccount.YESNO_CHOICES)[self.branch_enable],
            'product_enable': dict(Chartofaccount.YESNO_CHOICES)[self.product_enable],
            'unit_enable': dict(Chartofaccount.YESNO_CHOICES)[self.unit_enable],
            'inputvat_enable': dict(Chartofaccount.YESNO_CHOICES)[self.inputvat_enable],
            'outputvat_enable': dict(Chartofaccount.YESNO_CHOICES)[self.outputvat_enable],
            'vat_enable': dict(Chartofaccount.YESNO_CHOICES)[self.vat_enable],
            'wtax_enable': dict(Chartofaccount.YESNO_CHOICES)[self.wtax_enable],
            'ataxcode_enable': dict(Chartofaccount.YESNO_CHOICES)[self.ataxcode_enable],
            'status': dict(Chartofaccount.STATUS_CHOICES)[self.status],
            'enterdate': self.enterdate,
            'modifydate': self.modifydate,
            'enterby': self.enterby.username,
            'modifyby': self.modifyby.username,
            'kindofexpense': self.kindofexpense,
            'mainunit': self.mainunit,
            'product': self.product,
            'typeofexpense': self.typeofexpense,
            'reftype_enable': dict(Chartofaccount.YESNO_CHOICES)[self.reftype_enable],
            'refnum_enable': dict(Chartofaccount.YESNO_CHOICES)[self.refnum_enable],
            'refdate_enable': dict(Chartofaccount.YESNO_CHOICES)[self.refdate_enable],
        }
    # @classmethod
    # def deserialize(klass, data):
    #     kindofexpense = data.get('kindofexpense', None)
    #     if kindofexpense:
    #         try:
    #             return klass.objects.get(kindofexpense=kindofexpense)
    #         except klass.DoesNotExist:
    #             pass
    #     return klass(**data)
