from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models


class Temp_ormain(models.Model):
    orno = models.CharField(null=True, blank=True, max_length=500)
    ordate = models.CharField(null=True, blank=True, max_length=500)
    prno = models.CharField(null=True, blank=True, max_length=500)
    accounttype = models.CharField(null=True, blank=True, max_length=500)
    collector = models.CharField(null=True, blank=True, max_length=500)
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
    gov = models.CharField(null=True, blank=True, max_length=500)
    branchcode = models.CharField(null=True, blank=True, max_length=500)
    address1 = models.CharField(null=True, blank=True, max_length=500)
    address2 = models.CharField(null=True, blank=True, max_length=500)
    address3 = models.CharField(null=True, blank=True, max_length=500)
    tin = models.CharField(null=True, blank=True, max_length=500)

    importsequence = models.IntegerField(blank=True, null=True)
    # importkey = models.CharField(max_length=255, null=True, blank=True)
    importdate = models.DateTimeField(auto_now_add=True)
    importby = models.ForeignKey(User, default=1, related_name='temp_ormain_by')

    class Meta:
        db_table = 'temp_ormain'
        ordering = ['-pk']
