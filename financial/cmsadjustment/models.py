from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
import datetime


class Cmmain(models.Model):
    cmnum = models.CharField(max_length=10, unique=True)
    cmdate = models.DateField()
    particulars = models.TextField(null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    remarks = models.TextField(null=True, blank=True)
    CM_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
        ('R', 'Released'),
    )
    cmstatus = models.CharField(max_length=1, choices=CM_STATUS_CHOICES, default='F')
    designatedapprover = models.ForeignKey(User, related_name='cmmain_designated_approver', null=True, blank=True)
    actualapprover = models.ForeignKey(User, related_name='cmmain_actual_approver', null=True, blank=True)
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    approverremarks = models.CharField(max_length=250, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='cmmain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='cmmain_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='cmmain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    releaseby = models.ForeignKey(User, related_name='cmmain_release', null=True, blank=True)
    releasedate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='cmmain_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'cmmain'
        ordering = ['-pk']
        permissions = (("view_cmsadjustment", "Can view cms adjustment"),)

    def get_absolute_url(self):
        return reverse('cmsadjustment:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.cmnum

    def __unicode__(self):
        return self.cmnum


class Cmitem(models.Model):
    item_counter = models.IntegerField()
    cmmain = models.ForeignKey('cmsadjustment.Cmmain', related_name='cmitem_cmmain_id')
    cmnum = models.CharField(max_length=10)
    cmdate = models.DateTimeField()
    product = models.ForeignKey('product.Product', related_name='cmitem_product_id')
    product_code = models.CharField(max_length=100)
    product_name = models.CharField(max_length=500)
    debitamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    creditamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    remarks = models.CharField(max_length=500, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='cmitem_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='cmitem_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    postby = models.ForeignKey(User, related_name='cmitem_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    closeby = models.ForeignKey(User, related_name='cmitem_close', null=True, blank=True)
    closedate = models.DateTimeField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'cmitem'
        ordering = ['-pk']
        # permissions = (("view_jvmain", "Can view jvmain"),)

    def get_absolute_url(self):
        return reverse('cmitem:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Cmitem.STATUS_CHOICES)[self.status]




