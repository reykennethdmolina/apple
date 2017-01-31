from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import datetime


# Create your models here.
class Mainsupplier_supplier(models.Model):
    mainsupplier = models.ForeignKey('mainsupplier.Mainsupplier', related_name='mainsupplier_id',
                                     validators=[MinValueValidator(1)])
    supplier = models.ForeignKey('supplier.Supplier', related_name='supplier_id', validators=[MinValueValidator(1)])
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='mainsupplier_supplier_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='mainsupplier_supplier_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'mainsupplier_supplier'
        ordering = ['-pk']
        permissions = (("view_mainsupplier_supplier", "Can view mainsupplier_supplier"),)
        unique_together = (('mainsupplier', 'supplier'),)

    def get_absolute_url(self):
        return reverse('mainsupplier_supplier:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Mainsupplier_supplier.STATUS_CHOICES)[self.status]


