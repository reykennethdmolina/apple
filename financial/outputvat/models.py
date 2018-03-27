from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

class Outputvat(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', \
        related_name='outputvatchartofaccount_id', validators=[MinValueValidator(1)], \
        null=True, blank=True)
    title = models.CharField(max_length=50, null=True, blank=True)
    outputvattype = models.ForeignKey('outputvattype.Outputvattype', related_name='outputvat_outputvattype')
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='outputvat_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='outputvat_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'outputvat'
        ordering = ['-pk']
        permissions = (("view_outputvat", "Can view outputvat"),)

    def get_absolute_url(self):
        return reverse('outputvat:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Outputvat.STATUS_CHOICES)[self.status]
