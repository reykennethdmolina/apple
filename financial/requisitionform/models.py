from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
import datetime


class Rfmain(models.Model):
    rfnum = models.CharField(max_length=10, unique=True)
    rfdate = models.DateField()
    inventoryitemtype = models.ForeignKey('inventoryitemtype.Inventoryitemtype',
                                          related_name='rfmain_inventoryitemtype_id')
    refnum = models.CharField(max_length=150, null=True, blank=True)
    RF_TYPE_CHOICES = (
        ('REG', 'Regular'),
    )
    rftype = models.CharField(max_length=10, choices=RF_TYPE_CHOICES, default='REG')
    unit = models.ForeignKey('unit.Unit', related_name='rfmain_unit_id', null=True, blank=True)
    URGENCY_CHOICES = (
        ('N', 'Normal'),
        ('R', 'Rush'),
    )
    urgencytype = models.CharField(max_length=1, choices=URGENCY_CHOICES, default='N')
    dateneeded = models.DateField()
    branch = models.ForeignKey('branch.Branch', related_name='rfmain_branch_id')
    department = models.ForeignKey('department.Department', related_name='rfmain_department_id')
    particulars = models.TextField()
    RF_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    rfstatus = models.CharField(max_length=1, choices=RF_STATUS_CHOICES, default='F')
    designatedapprover = models.ForeignKey(User, default=2, related_name='designated_approver')
    actualapprover = models.ForeignKey(User, related_name='actual_approver', null=True, blank=True)
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
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='rfmain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='rfmain_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)
    totalquantity = models.IntegerField(default=0)
    totalremainingquantity = models.IntegerField(default=0)     # upon creation, this is equal to totalquantity

    class Meta:
        db_table = 'rfmain'
        ordering = ['-pk']
        permissions = (("view_requisitionform", "Can view requisitionform"),
                       ("view_assignrf", "Can view only assigned rf"),              # view assigned rfs to user
                       ("view_allassignrf", "Can view all rf"),                     # view all rfs
                       ("can_approverf", "Can approve rf"),
                       ("can_disapproverf", "Can disapprove rf"),)

    def get_absolute_url(self):
        return reverse('requisitionform:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.rfnum

    def __unicode__(self):
        return self.rfnum


class Rfdetail(models.Model):
    rfmain = models.ForeignKey('requisitionform.Rfmain', related_name='rfdetail_rfmain_id', null=True, blank=True)
    item_counter = models.IntegerField()
    invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='rfdetail_invitem_id')
    invitem_code = models.CharField(max_length=25)
    invitem_name = models.CharField(max_length=250)
    invitem_unitofmeasure = models.ForeignKey('unitofmeasure.Unitofmeasure', related_name='rfdetail_unitofmeasure_id')
    invitem_unitofmeasure_code = models.CharField(max_length=50)
    quantity = models.IntegerField()
    remarks = models.TextField(null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='rfdetail_enter')
    enterdate = models.DateTimeField(default=datetime.datetime.now())
    modifyby = models.ForeignKey(User, default=1, related_name='rfdetail_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='rfdetail_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='rfdetail_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    # additional columns for RF-PRF transactions
    isfullyprf = models.IntegerField(default=0)
    prftotalquantity = models.IntegerField(default=0)
    prfremainingquantity = models.IntegerField(default=0)  # upon creation, this is equal to quantity


    class Meta:
        db_table = 'rfdetail'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('requisitionform:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name

    def __unicode__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name


class Rfdetailtemp(models.Model):
    rfmain = models.ForeignKey('requisitionform.Rfmain', related_name='rfdetailtemp_rfmain_id', null=True, blank=True)
    rfdetail = models.ForeignKey('requisitionform.Rfdetail', related_name='rfdetailtemp_rfdetail_id', null=True,
                                 blank=True)
    item_counter = models.IntegerField()
    invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='rfdetailtemp_invitem_id')
    invitem_code = models.CharField(max_length=25)
    invitem_name = models.CharField(max_length=250)
    invitem_unitofmeasure = models.ForeignKey('unitofmeasure.Unitofmeasure',
                                              related_name='rfdetailtemp_unitofmeasure_id')
    invitem_unitofmeasure_code = models.CharField(max_length=50)
    quantity = models.IntegerField()
    remarks = models.TextField(null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='rfdetailtemp_enter')
    enterdate = models.DateTimeField(default=datetime.datetime.now())
    modifyby = models.ForeignKey(User, default=1, related_name='rfdetailtemp_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='rfdetailtemp_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='rfdetailtemp_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    secretkey = models.CharField(max_length=255)

    # additional columns for RF-PRF transactions
    isfullyprf = models.IntegerField(default=0)
    prftotalquantity = models.IntegerField(default=0)
    prfremainingquantity = models.IntegerField(default=0)  # upon creation, this is equal to quantity

    class Meta:
        db_table = 'rfdetailtemp'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('requisitionform:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name

    def __unicode__(self):
        return str(self.pk) + ' ' + str(self.item_counter) + ' ' + self.invitem_name

