from __future__ import unicode_literals
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from supplier.models import Supplier
from triplecbureau.models import Triplecbureau as Bureau
from triplecsection.models import Triplecsection as Section
from triplecsubtype.models import Triplecsubtype as Subtype
from triplecpublication.models import Triplecpublication as Publication
# from triplecpage.models import Triplecpage as Page


# Create your models here.
class TripleC(models.Model):
    cms_issue_date = models.DateField()
    cms_article_status = models.CharField(max_length=50, null=True)
    cms_publication = models.TextField(blank=True, null=True)
    cms_section = models.TextField(blank=True, null=True)
    cms_page = models.CharField(max_length=50, blank=True, null=True, default="")
    cms_article_id = models.CharField(max_length=50, null=True)
    cms_article_title = models.TextField()
    cms_byline = models.TextField(blank=True, null=True)
    cms_author_name = models.TextField(blank=True, null=True, default="")
    cms_created_by = models.TextField(blank=True, null=True, default="")
    cms_no_of_words = models.IntegerField(default=0, null=True)
    cms_no_of_characters = models.IntegerField(default=0, null=True)
    supplier = models.ForeignKey(Supplier, related_name='triplec_supplier')
    TYPE_CHOICES = (
        ('COL', 'Columnist'),
        ('CON', 'Contributor'),
        ('COR', 'Correspondent')
    )
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    no_ccc = models.IntegerField(default=0)
    code = models.CharField(max_length=30, null=True)
    author_name = models.TextField(blank=True, null=True)
    issue_date = models.DateField()
    article_title = models.TextField()
    byline = models.TextField(blank=True, null=True, default="")
    no_of_words = models.IntegerField(blank=True, null=True, default=0)
    no_of_characters = models.IntegerField(blank=True, null=True, default=0)
    length1 = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, default=0.00)
    length2 = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, default=0.00)
    length3 = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, default=0.00)
    length4 = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, default=0.00)
    width1 = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, default=0.00)
    width2 = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, default=0.00)
    width3 = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, default=0.00)
    width4 = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, default=0.00)
    total_size = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, default=0.00)
    subtype = models.ForeignKey(Subtype, related_name='triplec_subtype')
    bureau = models.ForeignKey(Bureau, blank=True, null=True, related_name='triplec_bureau')
    publication = models.ForeignKey(Publication, related_name='triplec_publication')
    section = models.ForeignKey(Section, related_name='triplec_section')
    page = models.CharField(max_length=15, blank=True, null=True)
    rate_code = models.CharField(max_length=30, null=True)
    wtax = models.IntegerField(blank=True, null=True, default=0)
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    remarks = models.TextField(blank=True, null=True, default="")
    confirmation = models.CharField(max_length=30, null=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('E', 'Ready for Posting'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
        ('D', 'Pending'),
        ('Y', 'No Payment'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    IMPORT_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
        ('P', 'Posted'),
    )
    importstatus = models.CharField(max_length=1, choices=IMPORT_STATUS_CHOICES, default='S')
    check_no = models.CharField(max_length=30, null=True)
    apv_no = models.CharField(max_length=30, null=True)
    date_check = models.DateField()
    date_apv = models.DateField()
    date_printed = models.DateField()
    date_posted = models.DateField()
    no_items = models.IntegerField(default=0)
    enterby = models.ForeignKey(User, default=1, related_name='triplec_enter')
    enterdate = models.DateField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='triplec_modify')
    modifydate = models.DateField(auto_now_add=True)
    manual = models.IntegerField(default=0)
    isdeleted = models.IntegerField(default=0)

    class Meta:
        db_table = 'triplec'
        ordering = ['-pk']
        get_latest_by = 'confirmation'
        permissions = (
            ("view_triplec", "Can view Triple C"),
            ("tag_triplec", "Can tag Triple C"),
            ("create_transaction_entry_triplec", "Can create transaction entry Triple C"),
            ("process_transaction_triplec", "Can process transaction Triple C")
        )

    def get_absolute_url(self):
        return reverse('triplec:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.code

    def __unicode__(self):
        return self.code

    def status_verbose(self):
        return dict(TripleC.STATUS_CHOICES)[self.status]
    

class Triplecquota(models.Model):
    confirmation = models.CharField(max_length=30, unique=True)
    no_item = models.IntegerField(default=0)
    TYPE_CHOICES = (
        ('P', 'Photo'),
        ('A', 'Article'),
        ('A,P', 'Article and Photo'),
        ('B', 'Breaking News'),
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    transportation_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    transportation2_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    cellcard_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)
    enterby = models.ForeignKey(User, default=1, related_name='triplecquota_enter')
    modifyby = models.ForeignKey(User, default=1, related_name='triplecquota_modify')
    
    class Meta:
        db_table = 'triplecquota'
        ordering = ['-pk']
        permissions = (
            ("change_triplec_quota", "Can change Triple C Quota"),
            ("delete_triplec_quota", "Can delete Triple C Quota"),
        )

    def status_verbose(self):
        return dict(Triplecquota.STATUS_CHOICES)[self.status]