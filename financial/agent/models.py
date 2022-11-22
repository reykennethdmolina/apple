from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Agent(models.Model):
    code = models.CharField(max_length=10, unique=True)
    agenttype = models.ForeignKey('agenttype.Agenttype', related_name='agent_agenttype_id')
    name = models.CharField(max_length=250)
    street = models.CharField(max_length=250, null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    comments = models.CharField(max_length=250, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    supplier = models.ForeignKey('supplier.Supplier', related_name='agentsupplier_id', null=True, blank=True)
    enterby = models.ForeignKey(User, default=1, related_name='agent_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='agent_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'agent'
        ordering = ['-pk']
        permissions = (("view_agent", "Can view agent"),)

    def get_absolute_url(self):
        return reverse('agent:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Agent.STATUS_CHOICES)[self.status]

# Create your models here.
class Newsboy(models.Model):
    doc_num = models.CharField(max_length=10, unique=True)
    doc_date = models.DateField(null=True, blank=True)
    glf_act = models.CharField(max_length=250, null=True, blank=True)
    glf_code = models.CharField(max_length=250, null=True, blank=True)

    glf_amt = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    glf_rem1 = models.CharField(max_length=250, null=True, blank=True)
    glf_rem2 = models.CharField(max_length=250, null=True, blank=True)
    glf_rem3 = models.CharField(max_length=250, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    status_d = models.DateField(null=True, blank=True)

    user_n = models.CharField(max_length=250, null=True, blank=True)
    user_d = models.DateField(null=True, blank=True)
    item_id = models.CharField(max_length=250, null=True, blank=True)
    smf_code = models.CharField(max_length=250, null=True, blank=True)
    smf_name = models.CharField(max_length=250, null=True, blank=True)
    smf_atccod = models.CharField(max_length=250, null=True, blank=True)
    smf_trate = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    doc_type = models.CharField(max_length=250, null=True, blank=True)

    enterby = models.ForeignKey(User, default=1, related_name='newsboy_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='newsboy_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'newsboy'
        ordering = ['-pk']
        # permissions = (("view_agent", "Can view agent"),)

    # def get_absolute_url(self):
    #     return reverse('agent:detail', kwargs={'pk': self.pk})

    def str(self):
        return self.doc_num

    def unicode(self):
        return self.doc_num

    def status_verbose(self):
        return dict(Newsboy.STATUS_CHOICES)[self.status]
