from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Subledgersummary(models.Model):
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='subledgersumm_chartofaccount')
    year = models.CharField(max_length=4)
    month = models.CharField(max_length=2)
    beginning_amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    beginning_code = models.CharField(max_length=10, null=True, blank=True)
    beginning_date = models.DateTimeField(null=True, blank=True)
    end_amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    end_code = models.CharField(max_length=10, null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    year_to_date_amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    year_to_date_code = models.CharField(max_length=10, null=True, blank=True)
    year_to_date_date = models.DateTimeField(null=True, blank=True)
    journal_voucher_credit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    journal_voucher_debit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    check_voucher_credit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    check_voucher_debit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    accounts_payable_voucher_credit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    accounts_payable_voucher_debit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    official_receipt_credit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    official_receipt_debit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    debit_credit_memo_credit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    debit_credit_memo_debit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    acknowledgement_receipt_credit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    acknowledgement_receipt_debit_total = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='subledgersumm_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='subledgersumm_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'subledgersummary'
        ordering = ['-pk']
        permissions = (("view_subledgersummary", "Can view subledgersummary"),)

    def get_absolute_url(self):
        return reverse('subledgersummary:detail', kwargs={'pk': self.pk})

    def __str__(self):
        #return self.chartofaccount
        return unicode(self.chartofaccount)

    def __unicode__(self):
        #return self.chartofaccount
        return unicode(self.chartofaccount)

    def status_verbose(self):
        return dict(Subledgersummary.STATUS_CHOICES)[self.status]
