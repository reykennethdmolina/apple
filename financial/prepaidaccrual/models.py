from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from supplier.models import Supplier
from chartofaccount.models import Chartofaccount
from department.models import Department
from branch.models import Branch
from subledger.models import Subledger
from journalvoucher.models import Jvmain

# Create your models here.
class PrepaidExpenseSchedule(models.Model):
    sl = models.OneToOneField(Subledger, null=True, related_name='prepaidexpenseschedule_sl')
    supplier = models.ForeignKey(Supplier, null=True, related_name='prepaidexpenseschedule_supplier')
    coa = models.ForeignKey(Chartofaccount, null=True, related_name='prepaidexpenseschedule_chartofaccount')
    transaction_type = models.CharField(max_length=10)
    date = models.DateField()
    transaction_number = models.CharField(max_length=20)
    CODE_CHOICES = (
        ('D', 'Debit'),
        ('C', 'Credit'),
    )
    code = models.CharField(max_length=1, choices=CODE_CHOICES, default='')
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, default=0.00)
    no_of_month = models.SmallIntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    computed_amortization = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True, default=0.00)
    actual_amortization = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True, default=0.00)
    expense_account = models.ForeignKey(Chartofaccount, null=True, related_name='prepaidexpenseschedule_expenseaccount')
    department = models.ForeignKey(Department, null=True, related_name='prepaidexpenseschedule_department')
    branch = models.ForeignKey(Branch, null=True, related_name='prepaidexpenseschedule_branch')
    remarks = models.TextField()
    particulars = models.TextField()
    STATUS_CHOICES = (
        (1, 'Active'),
        (0, 'Inactive'),
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)
    enterdate = models.DateTimeField(auto_now_add=True)
    modifydate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='prepaidexpenseschedule_modify')
    enterby = models.ForeignKey(User, default=1, related_name='prepaidexpenseschedule_enter')

    class Meta:
        db_table = 'prepaidexpenseschedule'
        ordering = ['-pk']
        permissions = (("view_prepaidexpenseschedule", "Can view prepaid expense schedule"))

    def get_absolute_url(self):
        return reverse('prepaidaccrual:prepaid-expense-schedule-detail', kwargs={'pk': self.pk})
    
    def __str__(self):
        return self.pk

    def __unicode__(self):
        return self.pk

    def status_verbose(self):
        return dict(PrepaidExpenseSchedule.STATUS_CHOICES)[self.status]


class PrepaidExpenseScheduleDetail(models.Model):
    item_counter = models.IntegerField(default=1)
    main = models.ForeignKey(PrepaidExpenseSchedule, related_name='prepaidexpenseschedule_detail')
    date = models.DateField()
    month = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    total_amortization = models.DecimalField(max_digits=18, decimal_places=2)
    ending_balance = models.DecimalField(max_digits=18, decimal_places=2)
    jvmain = models.ForeignKey(Jvmain, related_name='prepaidexpensescheduledetail_jvmain')
    jvnum = models.CharField(max_length=50, blank=True, null=True, default='')
    postdate = models.DateTimeField()
    postby = models.ForeignKey(User, related_name='prepaidexpensescheduledetail_post')
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
    modifyby = models.ForeignKey(User, default=1, related_name='prepaidexpensescheduledetail_modify')
    enterby = models.ForeignKey(User, default=1, related_name='prepaidexpensescheduledetail_enter')

    class Meta:
        db_table = 'prepaidexpensescheduledetail'
        ordering = ['-pk']
        permissions = (("view_prepaidexpensescheduledetail", "Can view prepaid expense schedule detail"))
    
    def __str__(self):
        return self.pk

    def __unicode__(self):
        return self.pk

    def status_verbose(self):
        return dict(PrepaidExpenseScheduleDetail.STATUS_CHOICES)[self.status]
    

# class AccruedExpense(models.Model):
#     item_counter = models.IntegerField(default=1)
#     sl = models.OneToOneField(Subledger, null=True, related_name='accruedexpense_sl')
#     main_id = models.IntegerField()
#     CODE_CHOICES = (
#         ('D', 'Debit'),
#         ('C', 'Credit')
#     )
#     code = models.CharField(max_length=1, choices=CODE_CHOICES, default='')
#     amount = models.DecimalField(max_digits=18, decimal_places=2)
#     balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
#     STATUS_CHOICES = (
#         ('A', 'Active'),
#         ('I', 'Inactive')
#     )
#     status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
#     enterdate = models.DateTimeField(auto_now_add=True)
#     modifydate = models.DateTimeField(auto_now_add=True)
#     modifyby = models.ForeignKey(User, default=1, related_name='accruedexpense_modify')
#     enterby = models.ForeignKey(User, default=1, related_name='accruedexpense_enter')

#     class Meta:
#         db_table = 'accruedexpense'
#         ordering = ['-pk']
#         permissions = (("view_accruedexpense", "Can view accrued expense"))
    
#     def __str__(self):
#         return self.pk

#     def __unicode__(self):
#         return self.pk

#     def status_verbose(self):
#         return dict(AccruedExpense.STATUS_CHOICES)[self.status]