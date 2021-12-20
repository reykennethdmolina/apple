from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User


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
    department = models.ForeignKey('department.Department', \
        related_name='department_id', validators=[MinValueValidator(1)])
    code = models.CharField(max_length=10, unique=True)
    managementlevel = models.ForeignKey('budgetapproverlevels.Budgetapproverlevels', related_name='budgetapproverlevels_id', null=True, blank=True)
    firstname = models.CharField(max_length=75)
    middlename = models.CharField(max_length=75, blank=True, null=True)
    lastname = models.CharField(max_length=75)
    email = models.CharField(max_length=100, blank=True, null=True)
    multiplestatus = models.CharField(max_length=1, \
        choices=YESNO_CHOICES, default='Y', null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='employee_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='employee_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)
    supplier = models.ForeignKey('supplier.Supplier', related_name='createbykensupplier_id', null=True, blank=True)

    cellphone_subsidize_amount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2,
                                                     max_digits=18)
    user = models.OneToOneField(User, null=True, blank=True)
    revolving = models.IntegerField(default=0)
    revolving_amount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2,
                                                     max_digits=18)
    jv_approver = models.IntegerField(default=0)
    cv_approver = models.IntegerField(default=0)
    ap_approver = models.IntegerField(default=0)
    or_approver = models.IntegerField(default=0)
    cs_approver = models.IntegerField(default=0)
    of_approver = models.IntegerField(default=0)
    hr_approver = models.IntegerField(default=0)
    group = models.CharField(max_length=5, default='B')

    anti_dep_amount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2,max_digits=18)
    anti_dep_date = models.DateTimeField(null=True, blank=True)
    eyeglass_date = models.DateTimeField(null=True, blank=True)
    eyeglass_amount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2,max_digits=18)

    class Meta:
        db_table = 'employee'
        ordering = ['-pk']
        permissions = (("view_employee", "Can view employee"),
                       ("can_adduser", "Can add user to employee"),)

    def get_absolute_url(self):
        return reverse('employee:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Employee.STATUS_CHOICES)[self.status]


