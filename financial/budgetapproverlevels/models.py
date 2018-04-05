from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


class Budgetapproverlevels(models.Model):
    LEVEL_CHOICES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
    )
    level = models.IntegerField(unique=True, choices=LEVEL_CHOICES)
    name = models.CharField(max_length=250, unique=True)
    description = models.CharField(max_length=500)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    expwithinbudget = models.DecimalField(default=0.00, decimal_places=2, max_digits=18)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='budgetapproverlevels_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='budgetapproverlevels_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'budgetapproverlevels'
        ordering = ['-pk']
        permissions = (("view_budgetapproverlevels", "Can view budgetapproverlevels"),)

    def get_absolute_url(self):
        return reverse('budgetapproverlevels:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.level

    def __unicode__(self):
        return self.level

    def status_verbose(self):
        return dict(Budgetapproverlevels.STATUS_CHOICES)[self.status]