from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User


class Department(models.Model):
    code = models.CharField(max_length=10, unique=True)
    departmentname = models.CharField(max_length=250)
    sectionname = models.CharField(max_length=250)
    groupname = models.CharField(max_length=250)
    expchartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', null=True, blank=True,
                                          related_name='chartofaccount_department')
    product = models.ForeignKey('product.Product', related_name='department_product_id', null=True, blank=True,
                                validators=[MinValueValidator(0)])
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    branchstatus = models.CharField(max_length=1, choices=YESNO_CHOICES, default='Y')
    enterby = models.ForeignKey(User, default=1, related_name='department_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='department_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'department'
        ordering = ['-pk']
        permissions = (("view_department", "Can view department"),)

    def get_absolute_url(self):
        return reverse('department:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def serialize(self):
        return {
            'code': self.code,
            'departmentname': self.departmentname,
            'sectionname': self.sectionname,
            'groupname': self.groupname,
            'branchstatus': dict(Department.YESNO_CHOICES)[self.branchstatus],
            'enterdate': self.enterdate,
            'modifydate': self.modifydate,
            'enterby': self.enterby.username,
            'modifyby': self.modifyby.username,
            'expchartofaccount': self.expchartofaccount,
            'product': self.product,
        }
