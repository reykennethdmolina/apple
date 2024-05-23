from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User

class Sisubtype(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='sisubtype_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='sisubtype_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)
    debit1 = models.ForeignKey('chartofaccount.Chartofaccount', related_name='sisubtype_debit1', null=True, blank=True)
    debit2 = models.ForeignKey('chartofaccount.Chartofaccount', related_name='sisubtype_debit2', null=True, blank=True)
    credit1 = models.ForeignKey('chartofaccount.Chartofaccount', related_name='sisubtype_credit1', null=True, blank=True)
    credit2 = models.ForeignKey('chartofaccount.Chartofaccount', related_name='sisubtype_credit2', null=True, blank=True)

    class Meta:
        db_table = 'sisubtype'
        ordering = ['-pk']
        permissions = (("view_sisubtype", "Can view sisubtype"),)

    def get_absolute_url(self):
        return reverse('sisubtype:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Sisubtype.STATUS_CHOICES)[self.status]
