from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


class Logs_posted(models.Model):
    datefrom = models.DateTimeField()
    dateto = models.DateTimeField()
    doctype = models.CharField(max_length=2)
    transactioncount = models.IntegerField(default=0)
    postedby = models.ForeignKey(User, related_name='transactions_postedby')
    postedon = models.DateTimeField()
    STATUS_CHOICES = (
        ('P', 'Passed'),
        ('F', 'Failed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'logs_posted'
        ordering = ['-pk']
        permissions = (("view_logs_posted", "Can view logs_posted"),)

    def get_absolute_url(self):
        return reverse('logs_posted:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.datefrom

    def __unicode__(self):
        return self.datefrom

    def status_verbose(self):
        return dict(Logs_posted.STATUS_CHOICES)[self.status]

