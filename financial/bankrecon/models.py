from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from bank.models import Bank
from bankaccount.models import Bankaccount
from subledger.models import Subledger

# Create your models here.
class Bankrecon(models.Model):
    reference_number = models.CharField(max_length=50, null=True)
    bank = models.ForeignKey(Bank, related_name='bankrecon_bank')
    bankaccount = models.ForeignKey(Bankaccount, related_name='bankrecon_bankaccount')
    generatedkey = models.CharField(max_length=250)
    transaction_date = models.DateField()
    transaction_time = models.TimeField(null=True)
    posting_date = models.DateField(null=True)
    particulars = models.TextField()
    debit_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    credit_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    balance_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    branch = models.CharField(max_length=250, null=True)
    tinnumber = models.CharField(max_length=25, null=True)
    transactioncode = models.CharField(max_length=250, null=True)
    refno = models.CharField(max_length=250, null=True)
    checknumber = models.CharField(max_length=250, null=True)
    narrative = models.TextField()
    remarks = models.CharField(max_length=250, null=True)
    IMPORT_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
        ('P', 'Posted'),
    )
    importstatus = models.CharField(max_length=1, choices=IMPORT_STATUS_CHOICES, default='S')
    enterby = models.ForeignKey(User, default=1, related_name='bankrecon_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='bankrecon_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'bankrecon'
        ordering = ['-pk']
        permissions = (
            ("view_bankrecon", "Can view bankrecon"),
            ("tag_bankrecon", "Can tag bankrecon"),
            ("upload_bankstatements", "Can upload bank statements")
        )

    def get_absolute_url(self):
        return reverse('bankrecon:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Bankrecon.IMPORT_STATUS_CHOICES)[self.status]