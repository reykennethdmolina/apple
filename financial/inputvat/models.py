from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

class Inputvat(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    inputvattype = models.ForeignKey('inputvattype.Inputvattype', \
        related_name='inputvattype_id', validators=[MinValueValidator(1)])
    inputvatchartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', \
        related_name='chartofaccount_inputvat_id', validators=[MinValueValidator(1)])
    title = models.CharField(max_length=50, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='inputvat_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='inputvat_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'inputvat'
        ordering = ['-pk']
        permissions = (("view_inputvat", "Can view inputvat"),)

    def get_absolute_url(self):
        return reverse('inputvat:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Inputvat.STATUS_CHOICES)[self.status]
