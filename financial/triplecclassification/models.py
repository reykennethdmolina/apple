from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Triplecclassification(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=250)
    various_account = models.ForeignKey('triplecvariousaccount.Triplecvariousaccount',
                                            related_name='triplecclassification_various_account', null=True, blank=True)
    various_account2 = models.ForeignKey('triplecvariousaccount.Triplecvariousaccount',
                                            related_name='triplecclassification_various_account2', null=True, blank=True)
    various_account3 = models.ForeignKey('triplecvariousaccount.Triplecvariousaccount',
                                            related_name='triplecclassification_various_account3', null=True, blank=True)
    various_account4 = models.ForeignKey('triplecvariousaccount.Triplecvariousaccount',
                                            related_name='triplecclassification_various_account4', null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='triplecclassification_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='triplecclassification_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'triplecclassification'
        ordering = ['-pk']
        permissions = (("view_triplecclassification", "Can view triplec classification"),)

    def get_absolute_url(self):
        return reverse('triplecclassification:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(Triplecclassification.STATUS_CHOICES)[self.status]