from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Triplecrate(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='triplecrate_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='triplecrate_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'triplecrate'
        ordering = ['-pk']
        permissions = (("view_triplecrate", "Can view triplec rate"),)

    def get_absolute_url(self):
        return reverse('triplecrate:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Triplecrate.STATUS_CHOICES)[self.status]