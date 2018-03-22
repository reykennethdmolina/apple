from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User

class Bankbranchdisburse(models.Model):
    bank = models.ForeignKey('bank.Bank', related_name='bank_bankbranchdisburse_id')
    branch = models.CharField(max_length=10, unique=True)
    address1 = models.CharField(max_length=250, blank=True, null=True)
    address2 = models.CharField(max_length=250, blank=True, null=True)
    address3 = models.CharField(max_length=250, blank=True, null=True)
    telephone1 = models.CharField(max_length=75, blank=True, null=True)
    telephone2 = models.CharField(max_length=75, blank=True, null=True)
    contact_person = models.CharField(max_length=250, blank=True, null=True)
    contact_position = models.CharField(max_length=250, blank=True, null=True)
    remarks = models.CharField(max_length=250, blank=True, null=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='bankbranchdisburse_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='bankbranchdisburse_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'bankbranchdisburse'
        ordering = ['-pk']
        permissions = (("view_bankbranchdisburse", "Can view bankbranchdisburse"),)

    def get_absolute_url(self):
        return reverse('bankbranchdisburse:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Bankbranchdisburse.STATUS_CHOICES)[self.status]