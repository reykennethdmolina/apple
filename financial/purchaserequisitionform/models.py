from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
import datetime


class Prfmain(models.Model):
    PRF_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )

    PRF_TYPE_CHOICES = (
        ('MSRF', 'MSRF'),
    )

    prfnum = models.CharField(max_length=10, unique=True)
    prfdate = models.DateField()
    prftype = models.CharField(max_length=10, choices=PRF_TYPE_CHOICES, default='MSRF')
    inventoryitemtype = models.ForeignKey('inventoryitemtype.Inventoryitemtype', related_name='prfmain_inventoryitemtype_id')
    department = models.ForeignKey('department.Department', related_name='prfmain_department_id')
    particulars = models.TextField()
    prfstatus = models.CharField(max_length=1, choices=PRF_STATUS_CHOICES, default='F')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postdate = models.DateTimeField(null=True, blank=True)
    enterby = models.ForeignKey(User, default=1, related_name='prfmain_enter')
    modifyby = models.ForeignKey(User, default=1, related_name='prfmain_modify')
    postby = models.ForeignKey(User, related_name='prfmain_post', null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    branch = models.ForeignKey('branch.Branch', related_name='prfbranch_id')
    designatedapprover = models.ForeignKey(User, default=2, related_name='prfdesignated_approver')
    actualapprover = models.ForeignKey(User, related_name='prfactual_approver', null=True, blank=True)
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)

    class Meta:
        db_table = 'prfmain'
        ordering = ['-pk']
        # permissions = (("view_purchaserequisitionform", "Can view purchaserequisitionform"),)

    def get_absolute_url(self):
        return reverse('purchaserequisitionform:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.prfnum

    def __unicode__(self):
        return self.prfnum


# class Prfdetail(models.Model):
#     STATUS_CHOICES = (
#         ('A', 'Active'),
#         ('I', 'Inactive'),
#         ('C', 'Cancelled'),
#         ('O', 'Posted'),
#         ('P', 'Printed'),
#     )
#
#     prfmain = models.ForeignKey('purchaserequisitionform.Prfmain', related_name='prfmain_id', null=True, blank=True)
#     rfdetail = models.ForeignKey('requisitionform.Rfdetail', related_name='rfdetail_prfdetail', null=True, blank=True)
#     invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='prfdetail_invitem_id')
#     invitem_code = models.CharField(max_length=25)
#     invitem_name = models.CharField(max_length=250)
#     item_counter = models.IntegerField()
#     quantity = models.IntegerField()
#     status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
#     enterby = models.ForeignKey(User, default=1, related_name='rfdetail_enter')
#     enterdate = models.DateTimeField(auto_now_add=True)
#     modifyby = models.ForeignKey(User, default=1, related_name='rfdetail_modify')
#     modifydate = models.DateTimeField(default=datetime.datetime.now())
#     postby = models.ForeignKey(User, default=1, related_name='rfdetail_post')
#     postdate = models.DateTimeField(default=datetime.datetime.now())
#     isdeleted = models.IntegerField(default=0)
#
#     class Meta:
#         db_table = 'prfdetail'
#         ordering = ['-pk']
#
#     def get_absolute_url(self):
#         return reverse('purchaserequisitionform:detail', kwargs={'pk': self.pk})
#
#     def __str__(self):
#         return self.rfnum + ' ' + self.item_counter
#
#     def __unicode__(self):
#         return self.rfnum + ' ' + self.item_counter
#
#
# class Prfdetailtemp(models.Model):
#     STATUS_CHOICES = (
#         ('A', 'Active'),
#         ('I', 'Inactive'),
#         ('C', 'Cancelled'),
#         ('O', 'Posted'),
#         ('P', 'Printed'),
#     )
#
#     prfmain = models.ForeignKey('purchaserequisitionform.Prfmain', related_name='temp_prfmain_id', null=True, blank=True)
#     rfdetail = models.ForeignKey('requisitionform.Rfdetail', related_name='temp_rfdetail_id', null=True, blank=True)
#     prfdetail = models.ForeignKey('purchaserequisitionform.Prfdetail', related_name='temp_prfdetail_id', null=True, blank=True)
#     invitem = models.ForeignKey('inventoryitem.Inventoryitem', related_name='temp_prfdetail_invitem_id')
#     invitem_code = models.CharField(max_length=25)
#     invitem_name = models.CharField(max_length=250)
#     item_counter = models.IntegerField()
#     quantity = models.IntegerField()
#     status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
#     enterby = models.ForeignKey(User, default=1, related_name='prfdetailtemp_enter')
#     enterdate = models.DateTimeField(auto_now_add=True)
#     modifyby = models.ForeignKey(User, default=1, related_name='prfdetailtemp_modify')
#     modifydate = models.DateTimeField(default=datetime.datetime.now())
#     postby = models.ForeignKey(User, related_name='prfdetailtemp_post', null=True, blank=True)
#     postdate = models.DateTimeField(null=True, blank=True)
#     isdeleted = models.IntegerField(default=0)
#     secretkey = models.CharField(max_length=255)
#
#     class Meta:
#         db_table = 'prfdetailtemp'
#         ordering = ['-pk']
#
#     def get_absolute_url(self):
#         return reverse('purchaserequisitionform:detail', kwargs={'pk': self.pk})
#
#     def __str__(self):
#         return self.rfnum + ' ' + self.item_counter
#
#     def __unicode__(self):
#         return self.rfnum + ' ' + self.item_counter
