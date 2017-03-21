from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
import datetime


class Rfmain(models.Model):
    rfnum = models.CharField(max_length=10, unique=True)
    rfdate = models.DateField()
    inventoryitemtype = models.ForeignKey('inventoryitemtype.Inventoryitemtype', related_name='inventoryitemtype_id')
    refnum = models.CharField(max_length=150, null=True, blank=True)
    jonum = models.CharField(max_length=150, null=True, blank=True)
    sonum = models.CharField(max_length=150, null=True, blank=True)
    URGENCY_CHOICES = (
        ('N', 'Normal'),
        ('R', 'Rush'),
    )
    urgencytype = models.CharField(max_length=1, choices=URGENCY_CHOICES, default='N')
    dateneeded = models.DateField()
    branch = models.ForeignKey('branch.Branch', related_name='rfbranch_id')
    department = models.ForeignKey('department.Department', related_name='rfdepartment_id')
    particulars = models.TextField()
    RF_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    rfstatus = models.CharField(max_length=1, choices=RF_STATUS_CHOICES, default='F')
    designatedapprover = models.ForeignKey(User, default=1, related_name='designated_approver')
    actualapprover = models.ForeignKey(User, default=1, related_name='actual_approver', null=True, blank=True)
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='rfmain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='rfmain_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, default=1, related_name='rfmain_post')
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'rfmain'
        ordering = ['-pk']
        # permissions = (("view_requisitionform", "Can view requisitionform"),)

    def get_absolute_url(self):
        return reverse('requisitionform:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.rfnum

    def __unicode__(self):
        return self.rfnum


class Rfdetail(models.Model):
    rfmain = models.ForeignKey('requisitionform.Rfmain', related_name='rfmain_id', null=True, blank=True)
    item_counter = models.IntegerField()
    # Add 'item_id' when inventory models are completed.
    item_name = models.CharField(max_length=250)
    unitofmeasure = models.CharField(max_length=15)
    quantity = models.IntegerField()
    remarks = models.CharField(max_length=250, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='rfdetail_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='rfdetail_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, default=1, related_name='rfdetail_post')
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)


    class Meta:
        db_table = 'rfdetail'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('requisitionform:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.rfnum + ' ' + self.item_counter

    def __unicode__(self):
        return self.rfnum + ' ' + self.item_counter


class Rfdetailtemp(models.Model):
    rfmain = models.ForeignKey('requisitionform.Rfmain', related_name='temp_rfmain_id', null=True, blank=True)
    item_counter = models.IntegerField()
    # Add 'item_id' when inventory models are completed.
    item_name = models.CharField(max_length=250)
    unitofmeasure = models.CharField(max_length=15)
    quantity = models.IntegerField()
    remarks = models.CharField(max_length=250, null=True, blank=True)
    secretkey = models.CharField(max_length=255)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='rfdetailtemp_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='rfdetailtemp_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, default=1, related_name='rfdetailtemp_post')
    postdate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'rfdetailtemp'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('requisitionform:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.rfnum + ' ' + self.item_counter

    def __unicode__(self):
        return self.rfnum + ' ' + self.item_counter
