from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


class CategoryMainGroupSubGroup(models.Model):
    main = models.ForeignKey('categorymaingroup.CategoryMainGroup', related_name='category_mapped_maingroup')
    sub = models.ForeignKey('chartofaccount.Chartofaccount', related_name='category_mapped_subgroup')
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='category_maingroupsubgroup_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='category_maingroupsubgroup_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'categorymainsubgroup'
        ordering = ['-pk']
        permissions = (("view_categorymainsubgroup", "Can view categorymainsubgroup"),)

    def get_absolute_url(self):
        return reverse('categorymainsubgroup:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.main

    def __unicode__(self):
        return self.main

    def status_verbose(self):
        return dict(CategoryMainGroupSubGroup.STATUS_CHOICES)[self.status]
