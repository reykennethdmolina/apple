from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
import datetime


class Reppcvmain(models.Model):
    reppcvnum = models.CharField(max_length=10, unique=True)
    reppcvdate = models.DateField()
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    cvmain = models.ForeignKey('checkvoucher.Cvmain', related_name='reppcvmain_cvmain_id', null=True, blank=True)
    apmain = models.ForeignKey('accountspayable.Apmain', related_name='reppcvmain_apmain_id', null=True, blank=True)
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    initialapprover = models.ForeignKey(User, related_name='pcv_initialapprover', null=True, blank=True)
    initialapproverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    initialapproverresponsedate = models.DateTimeField(null=True, blank=True)
    initialapproverremarks = models.CharField(max_length=2500, null=True, blank=True)
    finalapprover = models.ForeignKey(User, related_name='pcv_finalapprover', null=True, blank=True)
    finalapproverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    finalapproverresponsedate = models.DateTimeField(null=True, blank=True)
    finalapproverremarks = models.CharField(max_length=2500, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='reppcvmain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='reppcvmain_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='reppcvmain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='reppcvmain_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'reppcvmain'
        ordering = ['-pk']
        permissions = (("view_replenish_pcv", "Can view replenishment of PCV"),)

    def get_absolute_url(self):
        return reverse('replenish_pcv:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.reppcvnum

    def __unicode__(self):
        return self.reppcvnum


class Reppcvdetail(models.Model):
    reppcvmain = models.ForeignKey('replenish_pcv.Reppcvmain', related_name='reppcvdetail_reppcvmain_id')
    ofmain = models.ForeignKey('operationalfund.Ofmain', related_name='reppcvdetail_ofmain_id')
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    cvmain = models.ForeignKey('checkvoucher.Cvmain', related_name='reppcvdetail_cvmain_id', null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='reppcvdetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='reppcvdetail_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='reppcvdetail_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='reppcvdetail_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'reppcvdetail'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('replenish_pcv:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return self.pk
