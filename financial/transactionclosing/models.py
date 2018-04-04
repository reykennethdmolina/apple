from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


class Logs_closed(models.Model):
    datefrom = models.DateTimeField()
    dateto = models.DateTimeField()
    transactioncount = models.IntegerField(default=0)
    closedby = models.ForeignKey(User, related_name='transactions_closedby')
    closedon = models.DateTimeField()
    STATUS_CHOICES = (
        ('P', 'Passed'),
        ('F', 'Failed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'logs_closed'
        ordering = ['-pk']
        permissions = (("view_logs_closed", "Can view logs_closed"),)

    def get_absolute_url(self):
        return reverse('logs_closed:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.datefrom

    def __unicode__(self):
        return self.datefrom

    def status_verbose(self):
        return dict(Logs_closed.STATUS_CHOICES)[self.status]

