from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
import datetime


class Ataxcode(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField()
    rate = models.IntegerField(default=0, validators=[MaxValueValidator(99), MinValueValidator(0)])
    remarks = models.CharField(max_length=150, null=True, blank=True)
    others = models.CharField(max_length=150, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='ataxcode_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ataxcode_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'ataxcode'
        ordering = ['-pk']
        permissions = (("view_ataxcode", "Can view ataxcode"),)

    def get_absolute_url(self):
        return reverse('ataxcode:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Ataxcode.STATUS_CHOICES)[self.status]
