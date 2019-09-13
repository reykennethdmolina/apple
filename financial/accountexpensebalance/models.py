from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User


class Accountexpensebalance(models.Model):
    year = models.PositiveSmallIntegerField(validators=[MaxValueValidator(2100), MinValueValidator(1980)])
    month = models.PositiveIntegerField(validators=[MaxValueValidator(1), MinValueValidator(12)])
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount',
                                       related_name='accountexpensebalance_chartofaccount_id')
    department = models.ForeignKey('department.Department', related_name='accountexpensebalance_department_id')
    amount = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=2, max_digits=18)
    code = models.CharField(max_length=1)
    unit = models.CharField(max_length=5, null=True, blank=True)
    date = models.DateField()
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='accountexpensebalance_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='accountexpensebalance_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'accountexpensebalance'
        ordering = ['-pk']
        permissions = (("view_accountexpensebalance", "Can view accountexpensebalance"),)
        # unique_together = (('year', 'month', 'chartofaccount', 'department'),)

    def get_absolute_url(self):
        return reverse('accountexpensebalance:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.year)

    def __unicode__(self):
        return str(self.year)

    def status_verbose(self):
        return dict(Accountexpensebalance.STATUS_CHOICES)[self.status]
