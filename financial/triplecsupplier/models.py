from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from supplier.models import Supplier
from department.models import Department
from bankaccount.models import Bankaccount
from triplecrate.models import Triplecrate as Rate
from triplecbureau.models import Triplecbureau as Bureau
from triplecsection.models import Triplecsection as Section

# Create your models here.
class Triplecsupplier(models.Model):
    supplier = models.OneToOneField(Supplier)
    bureau = models.ForeignKey(Bureau, related_name='triplecsupplier_bureau', null=True, blank=True)
    section = models.ForeignKey(Section, related_name='triplecsupplier_section', null=True, blank=True)
    department = models.ForeignKey(Department, related_name='triplecsupplier_department', null=True, blank=True)
    rate = models.ForeignKey(Rate, related_name='triplec_rate', null=True, blank=True)
    bankaccount = models.ForeignKey(Bankaccount, related_name='triplecsupplier_bankaccount', null=True, blank=True)
    various_account = models.ForeignKey('triplecvariousaccount.Triplecvariousaccount',
                                            related_name='triplecsupplier_various_account', null=True, blank=True)

    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='triplecsupplier_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='triplecsupplier_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'triplecsupplier'
        ordering = ['-pk']
        permissions = (("view_triplecsupplier", "Can view triplec supplier"),)

    def get_absolute_url(self):
        return reverse('triplecsupplier:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.supplier

    def __unicode__(self):
        return self.supplier

    def status_verbose(self):
        return dict(Triplecsupplier.STATUS_CHOICES)[self.status]