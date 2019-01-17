from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


class ChartofAccountMainGroup(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    DEBITCREDIT_CHOICES = (
        ('D', 'Debit'),
        ('C', 'Credit'),
    )
    balancecode = models.CharField(max_length=1, choices=DEBITCREDIT_CHOICES, default='D')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='chartofaccountmaingroup_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='chartofaccountmaingroup_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)
    # title = models.CharField(max_length=250, null=True, blank=True)

    group = models.ForeignKey('chartofaccountmaingroup.ChartofAccountmainGroup', related_name='chartofaccountmaingroup_groupings', null=True, blank=True)

    class Meta:
        db_table = 'chartofaccountmaingroup'
        ordering = ['-pk']
        permissions = (("view_chartofaccountmaingroup", "Can view chartofaccountmaingroup"),)

    def get_absolute_url(self):
        return reverse('chartofaccountmaingroup:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(ChartofAccountMainGroup.STATUS_CHOICES)[self.status]
