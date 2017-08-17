from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User

class Companyparameter(models.Model):
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    code = models.CharField(max_length=10, unique=True)
    company = models.ForeignKey('company.Company', default=1, related_name='company_id')
    description = models.CharField(max_length=250)
    address1 = models.CharField(max_length=250)
    address2 = models.CharField(max_length=250)
    telno1 = models.CharField(max_length=20)
    telno2 = models.CharField(max_length=20, blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)
    contactperson_acctg1 = models.CharField(max_length=75)
    contactperson_acctg2 = models.CharField(max_length=75, blank=True, null=True)
    contactperson_it1 = models.CharField(max_length=75)
    contactperson_it2 = models.CharField(max_length=75, blank=True, null=True)
    contactperson_other1 = models.CharField(max_length=75, blank=True, null=True)
    contactperson_other2 = models.CharField(max_length=75, blank=True, null=True)
    sssnum = models.CharField(max_length=20, blank=True, null=True)
    tinnum = models.CharField(max_length=20, blank=True, null=True)
    rescertnum = models.CharField(max_length=20, blank=True, null=True)
    issued_at = models.CharField(max_length=20, blank=True, null=True)
    issued_date = models.DateField(blank=True, null=True)
    wtaxsign_name = models.CharField(max_length=50, blank=True, null=True)
    wtaxsign_tin = models.CharField(max_length=20, blank=True, null=True)
    wtaxsign_position = models.CharField(max_length=20, blank=True, null=True)

    # defaults for accounting entries
    coa_cashinbank = models.ForeignKey('chartofaccount.Chartofaccount', related_name='parameter_coa_cashinbank',
                                       blank=True, null=True)
    coa_inputvat = models.ForeignKey('chartofaccount.Chartofaccount', related_name='parameter_coa_inputvat',
                                     blank=True, null=True)
    # defaults for accounting entries

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='companyparameter_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='companyparameter_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'companyparameter'
        ordering = ['-pk']
        permissions = (("view_companyparameter", "Can view companyparameter"),)

    def get_absolute_url(self):
        return reverse('companyparameter:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Companyparameter.STATUS_CHOICES)[self.status]

