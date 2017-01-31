from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime


class Serviceinformation(models.Model):
    serviceclassification = models.ForeignKey('serviceclassification.Serviceclassification',
                                              related_name='serviceclassification_id',
                                              validators=[MinValueValidator(1), MaxValueValidator(99999)])
    precode = models.IntegerField(validators=[MaxValueValidator(9999)])
    code = models.IntegerField(validators=[MaxValueValidator(99999999)])
    description = models.CharField(max_length=250)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='serviceinformation_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='serviceinformation_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'serviceinformation'
        ordering = ['-pk']
        permissions = (("view_serviceinformation", "Can view serviceinformation"),)

    def get_absolute_url(self):
        return reverse('serviceinformation:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Serviceinformation.STATUS_CHOICES)[self.status]
