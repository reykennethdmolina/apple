from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Triplecvariousaccount(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    chartexpcostofsale = models.ForeignKey('chartofaccount.Chartofaccount',
                                            related_name='triplecvariousaccount_chartexpcostofsale', null=True, blank=True)
    chartexpgenandadmin = models.ForeignKey('chartofaccount.Chartofaccount',
                                            related_name='triplecvariousaccount_chartexpgenandadmin', null=True, blank=True)
    chartexpsellexp = models.ForeignKey('chartofaccount.Chartofaccount',
                                            related_name='triplecvariousaccount_chartexpsellexp', null=True, blank=True)
    TYPE_CHOICES = (
        ('addtl', 'Additional'),
        ('coa', 'Chart of Account'),
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='coa')
    subtype = models.ForeignKey('triplecsubtype.Triplecsubtype',
                                            related_name='triplecvariousaccount_subtype', null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='triplecvariousaccount_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='triplecvariousaccount_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'triplecvariousaccount'
        ordering = ['-pk']
        permissions = (("view_triplecvariousaccount", "Can view triplec various account"),)

    def get_absolute_url(self):
        return reverse('triplecvariousaccount:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Triplecvariousaccount.STATUS_CHOICES)[self.status]