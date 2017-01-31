from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
import datetime


class Employee(models.Model):
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
    department = models.ForeignKey('department.Department', related_name='department_id', validators=[MinValueValidator(1)])
    code = models.CharField(max_length=10, unique=True)
    firstname = models.CharField(max_length=75)
    middlename = models.CharField(max_length=75, blank=True, null=True)
    lastname = models.CharField(max_length=75)
    email = models.CharField(max_length=100, blank=True, null=True)
    multiplestatus = models.CharField(max_length=1, choices=YESNO_CHOICES, default='N', null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='employee_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='employee_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'employee'
        ordering = ['-pk']
        permissions = (("view_employee", "Can view employee"),)

    def get_absolute_url(self):
        return reverse('employee:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Employee.STATUS_CHOICES)[self.status]

