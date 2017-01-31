from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
import datetime


class Bankbranch(models.Model):
    bank = models.ForeignKey('bank.Bank', related_name='bank_bankbranch_id', validators=[MinValueValidator(1)])
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    address = models.CharField(max_length=250, blank=True, null=True)
    contact_person = models.CharField(max_length=250, blank=True, null=True)
    contact_position = models.CharField(max_length=250, blank=True, null=True)
    telephone1 = models.CharField(max_length=75, blank=True, null=True)
    telephone2 = models.CharField(max_length=75, blank=True, null=True)
    remarks = models.CharField(max_length=250, blank=True, null=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='bankbranch_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='bankbranch_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'bankbranch'
        ordering = ['-pk']
        permissions = (("view_bankbranch", "Can view bankbranch"),)

    def get_absolute_url(self):
        return reverse('bankbranch:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Bankbranch.STATUS_CHOICES)[self.status]
