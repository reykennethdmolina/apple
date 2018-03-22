from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


class MainGroupSubgroup(models.Model):
    main = models.ForeignKey('chartofaccountmaingroup.ChartofAccountMainGroup', related_name='mapped_maingroup')
    sub = models.ForeignKey('chartofaccountsubgroup.ChartofAccountSubGroup', related_name='mapped_subgroup')
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='maingroupsubgroup_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='maingroupsubgroup_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'chartofaccountmainsubgroup'
        ordering = ['-pk']
        permissions = (("view_chartofaccountmainsubgroup", "Can view chartofaccountmainsubgroup"),)

    def get_absolute_url(self):
        return reverse('chartofaccountmainsubgroup:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.main

    def __unicode__(self):
        return self.main

    def status_verbose(self):
        return dict(MainGroupSubgroup.STATUS_CHOICES)[self.status]
