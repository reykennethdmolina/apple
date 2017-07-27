from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import datetime


class Ofmain(models.Model):
    ofnum = models.CharField(max_length=10, unique=True)
    ofdate = models.DateField()
    oftype = models.ForeignKey('oftype.Oftype', related_name='ofmain_oftype_id', null=True, blank=True)
    ofsubtype = models.ForeignKey('ofsubtype.Ofsubtype', related_name='ofmain_ofsubtype_id', null=True, blank=True)
    payee = models.ForeignKey('supplier.Supplier', related_name='ofmain_payee_id', null=True, blank=True)
    payee_code = models.CharField(max_length=25, null=True, blank=True)
    payee_name = models.CharField(max_length=150)
    employee = models.ForeignKey('employee.Employee', related_name='ofmain_employee_id')
    employee_code = models.CharField(max_length=20)
    employee_name = models.CharField(max_length=150)
    department = models.ForeignKey('department.Department', related_name='ofmain_department_id')
    department_code = models.CharField(max_length=10)
    department_name = models.CharField(max_length=150)
    amount = models.DecimalField(decimal_places=2, max_digits=18, validators=[MaxValueValidator(1000),
                                                                              MinValueValidator(1)], default=0.00)
    particulars = models.TextField()
    refnum = models.CharField(max_length=150, null=True, blank=True)
    creditterm = models.ForeignKey('creditterm.Creditterm', related_name='ofmain_creditterm_id', null=True, blank=True)
    atc = models.ForeignKey('ataxcode.Ataxcode', related_name='ofmain_atc_id', validators=[MinValueValidator(1)],
                            null=True, blank=True)
    atcrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)], null=True,
                                  blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='ofmain_vat_id', validators=[MinValueValidator(1)], null=True,
                            blank=True)
    vatrate = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(100)], null=True,
                                  blank=True)
    inputvattype = models.ForeignKey('inputvattype.Inputvattype', related_name='ofmain_inputvattype_id', null=True,
                                     blank=True)
    YESNO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    deferredvat = models.CharField(max_length=1, choices=YESNO_CHOICES, null=True, blank=True, default='N')
    currency = models.ForeignKey('currency.Currency', related_name='ofmain_currency_id', default=1)
    fxrate = models.DecimalField(default=0.00, null=True, blank=True, decimal_places=5, max_digits=18)
    OF_STATUS_CHOICES = (
        ('F', 'For Approval'),
        ('A', 'Approved'),
        ('D', 'Disapproved'),
        ('I', 'In Process'),
        ('R', 'RELEASED'),
    )
    ofstatus = models.CharField(max_length=1, choices=OF_STATUS_CHOICES, default='F')
    designatedapprover = models.ForeignKey(User, default=2, related_name='ofmain_designated_approver')
    actualapprover = models.ForeignKey(User, related_name='ofmain_actual_approver', null=True, blank=True)
    RESPONSE_CHOICES = (
        ('A', 'Approved'),
        ('D', 'Disapproved'),
    )
    approverresponse = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    responsedate = models.DateTimeField(null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='ofmain_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='ofmain_modify')
    modifydate = models.DateTimeField(default=datetime.datetime.now())
    postby = models.ForeignKey(User, related_name='ofmain_post', null=True, blank=True)
    postdate = models.DateTimeField(null=True, blank=True)
    # triggers In Process status START
    receiveby = models.ForeignKey(User, related_name='ofmain_receive', null=True, blank=True)
    receivedate = models.DateTimeField(null=True, blank=True)
    # triggers In Process status END
    releaseby = models.ForeignKey(User, related_name='ofmain_release', null=True, blank=True)
    releasedate = models.DateTimeField(null=True, blank=True)
    paymentreceivedby = models.ForeignKey('employee.Employee', related_name='ofmain_paymentreceived', null=True,
                                          blank=True)
    paymentreceiveddate = models.DateTimeField(null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='ofmain_branch_id', default=5)
    isdeleted = models.IntegerField(default=0)
    print_ctr = models.IntegerField(default=0)

    class Meta:
        db_table = 'ofmain'
        ordering = ['-pk']
        permissions = (("view_operationalfund", "Can view operational fund"),
                       ("approve_assignedof", "Can approve assigned of"),
                       ("approve_allof", "Can approve all of"),
                       ("is_cashier", "Is from cashier's office"),)

    def get_absolute_url(self):
        return reverse('operationalfund:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.ofnum

    def __unicode__(self):
        return self.ofnum
