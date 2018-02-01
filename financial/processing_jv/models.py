from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models


class Logs_jvmain(models.Model):
    IMPORT_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
        ('P', 'Posted'),
    )

    jvnum = models.CharField(null=True, blank=True, max_length=500)
    jvdate = models.CharField(null=True, blank=True, max_length=500)
    particulars = models.CharField(null=True, blank=True, max_length=500)
    remarks = models.CharField(null=True, blank=True, max_length=500)
    comments = models.CharField(null=True, blank=True, max_length=500)
    status = models.CharField(null=True, blank=True, max_length=500)
    datecreated = models.CharField(null=True, blank=True, max_length=500)
    datemodified = models.CharField(null=True, blank=True, max_length=500)
    batchkey = models.CharField(max_length=255, null=True, blank=True)
    importstatus = models.CharField(max_length=1, choices=IMPORT_STATUS_CHOICES, default='S')
    importremarks = models.CharField(max_length=255, null=True, blank=True)
    importdate = models.DateTimeField(auto_now_add=True)
    importby = models.ForeignKey(User, default=1, related_name='logs_jvmain_by')
    jvsubtype = models.CharField(null=True, blank=True, max_length=500)

    class Meta:
        db_table = 'logs_jvmain'
        ordering = ['-pk']


class Logs_jvdetail(models.Model):
    IMPORT_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
        ('P', 'Posted'),
    )

    jvnum = models.CharField(null=True, blank=True, max_length=500)
    jvdate = models.CharField(null=True, blank=True, max_length=500)
    chartofaccount = models.CharField(null=True, blank=True, max_length=500)
    bankaccount = models.CharField(null=True, blank=True, max_length=500)
    department = models.CharField(null=True, blank=True, max_length=500)
    charttype = models.CharField(null=True, blank=True, max_length=500)
    amount = models.CharField(null=True, blank=True, max_length=500)
    status = models.CharField(null=True, blank=True, max_length=500)
    datecreated = models.CharField(null=True, blank=True, max_length=500)
    datemodified = models.CharField(null=True, blank=True, max_length=500)
    sortnum = models.CharField(null=True, blank=True, max_length=500)
    branch = models.CharField(null=True, blank=True, max_length=500)
    batchkey = models.CharField(max_length=255, null=True, blank=True)
    importstatus = models.CharField(max_length=1, choices=IMPORT_STATUS_CHOICES, default='S')
    importremarks = models.CharField(max_length=255, null=True, blank=True)
    importdate = models.DateTimeField(auto_now_add=True)
    importby = models.ForeignKey(User, default=1, related_name='logs_jvdetail_by')

    class Meta:
        db_table = 'logs_jvdetail'
        ordering = ['-pk']


class Temp_jvmain(models.Model):
    POSTING_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
    )

    importedjvnum = models.CharField(null=True, blank=True, max_length=500)
    jvdate = models.CharField(null=True, blank=True, max_length=500)
    particulars = models.CharField(null=True, blank=True, max_length=1000)  # particulars,comments,remarks
    importby = models.ForeignKey(User, default=1, related_name='temp_jvmain_by')
    batchkey = models.CharField(null=True, blank=True, max_length=500)
    postingstatus = models.CharField(max_length=1, choices=POSTING_STATUS_CHOICES, default='F')
    postingremarks = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'temp_jvmain'
        ordering = ['-pk']


class Temp_jvdetail(models.Model):
    POSTING_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
    )

    item_counter = models.CharField(null=True, blank=True, max_length=500)
    importedjvnum = models.CharField(null=True, blank=True, max_length=500)
    jvdate = models.CharField(null=True, blank=True, max_length=500)
    chartofaccount = models.CharField(null=True, blank=True, max_length=500)
    department = models.CharField(null=True, blank=True, max_length=500)
    balancecode = models.CharField(null=True, blank=True, max_length=500)
    debitamount = models.CharField(null=True, blank=True, max_length=500)
    creditamount = models.CharField(null=True, blank=True, max_length=500)

    # added fields for Advertising
    bankaccount = models.CharField(null=True, blank=True, max_length=500)
    branch = models.CharField(null=True, blank=True, max_length=500)

    batchkey = models.CharField(null=True, blank=True, max_length=500)
    postingstatus = models.CharField(max_length=1, choices=POSTING_STATUS_CHOICES, default='F')
    postingremarks = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'temp_jvdetail'
        ordering = ['-pk']
