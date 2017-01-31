from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
import datetime


class Jvtype(models.Model):
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )

    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=255)
    taxstatus = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N')
    department = models.ForeignKey('department.Department', related_name='department_jvtype_id', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='branch_jvtype_id', null=True, blank=True)
    particulars = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='jvtype_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='jvtype_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'jvtype'
        ordering = ['-pk']
        permissions = (("view_jvtype", "Can view jvtype"),)

    def get_absolute_url(self):
        return reverse('jvtype:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Jvtype.STATUS_CHOICES)[self.status]
