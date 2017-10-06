from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
import datetime


class Reprfvmain(models.Model):
    reprfvnum = models.CharField(max_length=10, unique=True)
    reprfvdate = models.DateField()
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    apmain = models.ForeignKey('accountspayable.Apmain', related_name='reprfvmain_apmain_id', null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='reprfvmain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='reprfvmain_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'reprfvmain'
        ordering = ['-pk']
        permissions = (("view_replenish_rfv", "Can view replenishment of RFV"),)

    def get_absolute_url(self):
        return reverse('replenish_rfv:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.reprfvnum

    def __unicode__(self):
        return self.reprfvnum


class Reprfvdetail(models.Model):
    reprfvmain = models.ForeignKey('replenish_rfv.Reprfvmain', related_name='reprfvdetail_reprfvmain_id')
    ofmain = models.ForeignKey('operationalfund.Ofmain', related_name='reprfvdetail_ofmain_id')
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    apmain = models.ForeignKey('accountspayable.Apmain', related_name='reprfvdetail_apmain_id', null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='reprfvdetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='reprfvdetail_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'reprfvdetail'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('replenish_rfv:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return self.pk