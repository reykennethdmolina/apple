from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

class Fxrate(models.Model):
    currency = models.ForeignKey('currency.Currency', related_name='fxrate_currency_id',
                             validators=[MinValueValidator(1)])
    startdate = models.DateField()
    enddate = models.DateField()
    fxrate = models.DecimalField(default=0.00, null=True, blank=True, \
        decimal_places=5, max_digits=18)
    fxrateselling = models.DecimalField(default=0.00, null=True, blank=True, \
        decimal_places=5, max_digits=18)
    remarks = models.CharField(max_length=250, blank=True, null=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='fxrate_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='fxrate_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'fxrate'
        ordering = ['-pk']
        permissions = (("view_fxrate", "Can view fxrate"),)

    def get_absolute_url(self):
        return reverse('fxrate:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.pk

    def __unicode__(self):
        return unicode(self.pk)

    def status_verbose(self):
        return dict(Fxrate.STATUS_CHOICES)[self.status]