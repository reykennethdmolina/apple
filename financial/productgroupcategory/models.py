from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


class Productgroupcategory(models.Model):
    productgroup = models.ForeignKey('productgroup.Productgroup', related_name='productgroupcategory_product')
    category = models.ForeignKey('locationcategory.Locationcategory', related_name='productgroupcategory_category')
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='productgroupcategory_chartofaccount')
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='productgroupcategory_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='productgroupcategory_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'productgroupcategory'
        ordering = ['-pk']
        permissions = (("view_productgroupcategory", "Can view productgroupcategory"),)
        unique_together = ('productgroup', 'category',)

    def get_absolute_url(self):
        return reverse('productgroupcategory:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Productgroupcategory.STATUS_CHOICES)[self.status]