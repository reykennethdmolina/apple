from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

# Create your models here.
class Product(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    pagecount = models.IntegerField(default=0)
    cmsgroup_id = models.IntegerField(default=0, null=True, blank=True)
    mainproduct = models.ForeignKey('mainproduct.Mainproduct', default=0, \
        related_name='mainproduct_id', validators=[MinValueValidator(1)])
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='product_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='product_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'product'
        ordering = ['-pk']
        permissions = (("view_product", "Can view product"),)

    def get_absolute_url(self):
        return reverse('product:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Product.STATUS_CHOICES)[self.status]

    def cmsgroup(self):
        if self.cmsgroup_id != 0:
            return Product.objects.filter(cmsgroup_id=self.cmsgroup_id).order_by('pk').first()
        else:
            return ""
