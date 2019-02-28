from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models


class Logs_ormain(models.Model):
    IMPORT_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
        ('P', 'Posted'),
    )

    orno = models.CharField(null=True, blank=True, max_length=500)
    ordate = models.CharField(null=True, blank=True, max_length=500)
    prno = models.CharField(null=True, blank=True, max_length=500)
    accounttype = models.CharField(null=True, blank=True, max_length=500)
    collector = models.CharField(null=True, blank=True, max_length=500)
    collectordesc = models.CharField(null=True, blank=True, max_length=500)
    payeetype = models.CharField(null=True, blank=True, max_length=500)
    adtype = models.CharField(null=True, blank=True, max_length=500)
    agencycode = models.CharField(null=True, blank=True, max_length=500)
    clientcode = models.CharField(null=True, blank=True, max_length=500)
    agentcode = models.CharField(null=True, blank=True, max_length=500)
    payeename = models.CharField(null=True, blank=True, max_length=500)
    amount = models.CharField(null=True, blank=True, max_length=500)
    amountinwords = models.CharField(null=True, blank=True, max_length=500)
    bankaccount = models.CharField(null=True, blank=True, max_length=500)
    particulars = models.CharField(null=True, blank=True, max_length=500)
    artype = models.CharField(null=True, blank=True, max_length=500)
    status = models.CharField(null=True, blank=True, max_length=500)
    statusdate = models.CharField(null=True, blank=True, max_length=500)
    enterby = models.CharField(null=True, blank=True, max_length=500)
    enterdate = models.CharField(null=True, blank=True, max_length=500)
    product = models.CharField(null=True, blank=True, max_length=500)
    initmark = models.CharField(null=True, blank=True, max_length=500)
    glsmark = models.CharField(null=True, blank=True, max_length=500)
    glsdate = models.CharField(null=True, blank=True, max_length=500)
    totalwtax = models.CharField(null=True, blank=True, max_length=500)
    wtaxrate = models.CharField(null=True, blank=True, max_length=500)
    gov = models.CharField(null=True, blank=True, max_length=500)
    branchcode = models.CharField(null=True, blank=True, max_length=500)
    branchdesc = models.CharField(null=True, blank=True, max_length=500)
    address1 = models.CharField(null=True, blank=True, max_length=500)
    address2 = models.CharField(null=True, blank=True, max_length=500)
    address3 = models.CharField(null=True, blank=True, max_length=500)
    tin = models.CharField(null=True, blank=True, max_length=500)
    vatcode = models.CharField(null=True, blank=True, max_length=500)
    vatrate = models.CharField(null=True, blank=True, max_length=500)
    subscription = models.CharField(null=True, blank=True, max_length=500)
    paytype = models.CharField(null=True, blank=True, max_length=500)
    batchkey = models.CharField(max_length=255, null=True, blank=True)
    importstatus = models.CharField(max_length=1, choices=IMPORT_STATUS_CHOICES, default='S')
    importremarks = models.CharField(max_length=255, null=True, blank=True)
    importdate = models.DateTimeField(auto_now_add=True)
    importby = models.ForeignKey(User, default=1, related_name='logs_ormain_by')

    class Meta:
        db_table = 'logs_ormain'
        ordering = ['-pk']


class Logs_ordetail(models.Model):
    IMPORT_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
        ('P', 'Posted'),
    )

    orno = models.CharField(null=True, blank=True, max_length=500)
    doctype = models.CharField(null=True, blank=True, max_length=500)
    docnum = models.CharField(null=True, blank=True, max_length=500)
    balance = models.CharField(null=True, blank=True, max_length=500)
    assignamount = models.CharField(null=True, blank=True, max_length=500)
    assignvatamount = models.CharField(null=True, blank=True, max_length=500)
    status = models.CharField(null=True, blank=True, max_length=500)
    statusdate = models.CharField(null=True, blank=True, max_length=500)
    usercode = models.CharField(null=True, blank=True, max_length=500)
    userdate = models.CharField(null=True, blank=True, max_length=500)
    docitem = models.CharField(null=True, blank=True, max_length=500)
    initmark = models.CharField(null=True, blank=True, max_length=500)
    glsmark = models.CharField(null=True, blank=True, max_length=500)
    glsdate = models.CharField(null=True, blank=True, max_length=500)
    assignwtaxamount = models.CharField(null=True, blank=True, max_length=500)
    assignwvatamount = models.CharField(null=True, blank=True, max_length=500)
    vatcode = models.CharField(null=True, blank=True, max_length=500)
    vatrate = models.CharField(null=True, blank=True, max_length=500)
    batchkey = models.CharField(max_length=255, null=True, blank=True)
    importstatus = models.CharField(max_length=1, choices=IMPORT_STATUS_CHOICES, default='S')
    importremarks = models.CharField(max_length=255, null=True, blank=True)
    importdate = models.DateTimeField(auto_now_add=True)
    importby = models.ForeignKey(User, default=1, related_name='logs_ordetail_by')
    adtype = models.CharField(null=True, blank=True, max_length=500)
    adtypedesc = models.CharField(null=True, blank=True, max_length=500)
    product = models.CharField(null=True, blank=True, max_length=500)

    class Meta:
        db_table = 'logs_ordetail'
        ordering = ['-pk']


class Temp_ormain(models.Model):
    POSTING_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
    )

    orno = models.CharField(null=True, blank=True, max_length=500)
    ordate = models.CharField(null=True, blank=True, max_length=500)
    prno = models.CharField(null=True, blank=True, max_length=500)
    accounttype = models.CharField(null=True, blank=True, max_length=500)
    bankaccountcode = models.CharField(null=True, blank=True, max_length=500)
    branchcode = models.CharField(null=True, blank=True, max_length=500)
    collectorcode = models.CharField(null=True, blank=True, max_length=500)
    collectordesc = models.CharField(null=True, blank=True, max_length=500)
    artype = models.CharField(null=True, blank=True, max_length=500) # orsource
    agencycode = models.CharField(null=True, blank=True, max_length=500)
    clientcode = models.CharField(null=True, blank=True, max_length=500)
    agentcode = models.CharField(null=True, blank=True, max_length=500)
    payeecode = models.CharField(null=True, blank=True, max_length=500)
    payeename = models.CharField(null=True, blank=True, max_length=500)
    payeetype = models.CharField(null=True, blank=True, max_length=500)
    productcode = models.CharField(null=True, blank=True, max_length=500)
    adtypecode = models.CharField(null=True, blank=True, max_length=500)
    amount = models.CharField(null=True, blank=True, max_length=500)
    amountinwords = models.CharField(null=True, blank=True, max_length=500)
    vatrate = models.CharField(null=True, blank=True, max_length=500)
    vatcode = models.CharField(null=True, blank=True, max_length=500)
    totalwtax = models.CharField(null=True, blank=True, max_length=500)
    wtaxrate = models.CharField(null=True, blank=True, max_length=500)
    particulars = models.CharField(null=True, blank=True, max_length=500)
    subscription = models.CharField(null=True, blank=True, max_length=500)
    paytype = models.CharField(null=True, blank=True, max_length=500)
    importby = models.ForeignKey(User, default=1, related_name='temp_ormain_by')
    importdate = models.CharField(null=True, blank=True, max_length=500)
    batchkey = models.CharField(null=True, blank=True, max_length=500)
    postingstatus = models.CharField(max_length=1, choices=POSTING_STATUS_CHOICES, default='F')
    postingremarks = models.CharField(max_length=255, null=True, blank=True)
    enterby = models.CharField(null=True, blank=True, max_length=500)
    enterdate = models.CharField(null=True, blank=True, max_length=500)
    status = models.CharField(null=True, blank=True, max_length=500)
    add1 = models.CharField(null=True, blank=True, max_length=500)
    add2 = models.CharField(null=True, blank=True, max_length=500)
    add3 = models.CharField(null=True, blank=True, max_length=500)
    tin = models.CharField(null=True, blank=True, max_length=500)

    class Meta:
        db_table = 'temp_ormain'
        ordering = ['-pk']


class Temp_ordetail(models.Model):
    POSTING_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
    )

    orno = models.CharField(null=True, blank=True, max_length=500)
    ordate = models.CharField(null=True, blank=True, max_length=500)
    adtypecode = models.CharField(null=True, blank=True, max_length=500)
    amount = models.CharField(null=True, blank=True, max_length=500)
    vatamount = models.CharField(null=True, blank=True, max_length=500)
    debitamount = models.CharField(null=True, blank=True, max_length=500)
    creditamount = models.CharField(null=True, blank=True, max_length=500)
    balancecode = models.CharField(null=True, blank=True, max_length=500)
    chartofaccountcode = models.CharField(null=True, blank=True, max_length=500)
    payeecode = models.CharField(null=True, blank=True, max_length=500)
    payeename = models.CharField(null=True, blank=True, max_length=500)
    productcode = models.CharField(null=True, blank=True, max_length=500)
    vatrate = models.CharField(null=True, blank=True, max_length=500)
    vatcode = models.CharField(null=True, blank=True, max_length=500)
    outputvatcode = models.CharField(null=True, blank=True, max_length=500)
    customercode = models.CharField(null=True, blank=True, max_length=500)
    bankaccountcode = models.CharField(null=True, blank=True, max_length=500)
    batchkey = models.CharField(null=True, blank=True, max_length=500)
    postingstatus = models.CharField(max_length=1, choices=POSTING_STATUS_CHOICES, default='F')
    postingremarks = models.CharField(max_length=255, null=True, blank=True)
    product = models.CharField(null=True, blank=True, max_length=500)
    status = models.CharField(null=True, blank=True, max_length=500)

    class Meta:
        db_table = 'temp_ordetail'
        ordering = ['-pk']