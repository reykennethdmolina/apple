from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


class Reportmaintenance(models.Model):
    name = models.CharField(max_length=50, unique=True)
    enterby = models.ForeignKey(User, default=1, related_name='reportmaintenance_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='reportmaintenance_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'reportmaintenance'
        ordering = ['-pk']
        permissions = (("view_reportmaintenance", "Can view reportmaintenance"),)

    def get_absolute_url(self):
        return reverse('reportmaintenance:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Reportmaintenancemodule(models.Model):
    reportmaintenance = models.ForeignKey('reportdashboard.Reportmaintenance', related_name='reportmaintenancemodule_reportdashboard')
    reportmodule = models.ForeignKey('module.Module', related_name='reportmaintenancemodule_module')
    enterby = models.ForeignKey(User, default=1, related_name='reportmaintenancemodule_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='reportmaintenancemodule_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'reportmaintenancemodule'
        ordering = ['-pk']
        permissions = (("view_reportmaintenancemodule", "Can view reportmaintenancemodule"),)

    def get_absolute_url(self):
        return reverse('reportmaintenancemodule:detail', kwargs={'pk': self.pk})
