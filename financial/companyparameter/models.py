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
    wtaxsign_name = models.CharField(max_length=70, blank=True, null=True)
    wtaxsign_tin = models.CharField(max_length=20, blank=True, null=True)
    wtaxsign_position = models.CharField(max_length=70, blank=True, null=True)

    # defaults for accounting entries
    coa_cashinbank = models.ForeignKey('chartofaccount.Chartofaccount', related_name='parameter_coa_cashinbank',
                                       blank=True, null=True)
    coa_unsubscribe = models.ForeignKey('chartofaccount.Chartofaccount', related_name='parameter_coa_unsubscribe',
                                       blank=True, null=True)
    coa_inputvat = models.ForeignKey('chartofaccount.Chartofaccount', related_name='parameter_coa_inputvat',
                                     blank=True, null=True)
    coa_deferredinputvat = models.ForeignKey('chartofaccount.Chartofaccount',
                                             related_name='parameter_coa_deferredinputvat', blank=True, null=True)
    coa_outputvat = models.ForeignKey('chartofaccount.Chartofaccount', related_name='parameter_coa_outputvat',
                                      blank=True, null=True)
    coa_ewtax = models.ForeignKey('chartofaccount.Chartofaccount', related_name='parameter_coa_ewtax', blank=True,
                                  null=True)
    coa_aptrade = models.ForeignKey('chartofaccount.Chartofaccount', related_name='parameter_coa_aptrade', blank=True,
                                    null=True)
    coa_subsrev = models.ForeignKey('chartofaccount.Chartofaccount', related_name='parameter_coa_subsrev', blank=True,
                                    null=True)
    def_bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='parameter_def_bankaccount')
    # defaults for accounting entries

    # default approvers
    budgetapprover = models.ForeignKey(User, default=1, related_name='companyparameter_budgetapprover')
    pcv_initial_approver = models.ForeignKey(User, default=1, related_name='companyparameter_pcv_initial_approver')
    pcv_final_approver = models.ForeignKey(User, default=1, related_name='companyparameter_pcv_final_approver')
    rfv_initial_approver = models.ForeignKey(User, default=1, related_name='companyparameter_rfv_initial_approver')
    rfv_final_approver = models.ForeignKey(User, default=1, related_name='companyparameter_rfv_final_approver')

    # default approvers

    # petty cash meal expenses defaults
    pcv_meal_expenses = models.ForeignKey('ofsubtype.Ofsubtype', related_name='companyparameter_pcv_meal_expenses',
                                          null=True, blank=True)
    pcv_meal_budget_limit = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    # petty cash meal expenses defaults

    # report footers
    report_footer1 = models.CharField(max_length=250, blank=True, null=True)
    report_footer2 = models.CharField(max_length=250, blank=True, null=True)
    report_footer3 = models.CharField(max_length=250, blank=True, null=True)
    report_footer4 = models.CharField(max_length=250, blank=True, null=True)
    report_footer5 = models.CharField(max_length=250, blank=True, null=True)
    report_footer6 = models.CharField(max_length=250, blank=True, null=True)
    report_footer7 = models.CharField(max_length=250, blank=True, null=True)
    report_footer8 = models.CharField(max_length=250, blank=True, null=True)
    report_footer9 = models.CharField(max_length=250, blank=True, null=True)
    report_footer10 = models.CharField(max_length=250, blank=True, null=True)
    report_footer11 = models.CharField(max_length=250, blank=True, null=True)
    report_footer12 = models.CharField(max_length=250, blank=True, null=True)
    report_footer13 = models.CharField(max_length=250, blank=True, null=True)
    report_footer14 = models.CharField(max_length=250, blank=True, null=True)
    # report footers

    # closing
    last_closed_date = models.DateField(null=True)
    year_end_date = models.DateField(null=True)
    income_tax_rate = models.IntegerField(null=True)
    coa_provisionincometax = models.ForeignKey('chartofaccount.Chartofaccount', related_name='param_provisionincometax',
                                               blank=True, null=True)
    coa_incometaxespayable = models.ForeignKey('chartofaccount.Chartofaccount', related_name='param_incometaxespayable',
                                               blank=True, null=True)
    coa_retainedearnings = models.ForeignKey('chartofaccount.Chartofaccount', related_name='param_coa_retainedearnings',
                                               blank=True, null=True)
    coa_currentearnings = models.ForeignKey('chartofaccount.Chartofaccount', related_name='param_coa_currentearnings',
                                             blank=True, null=True)

    enable_manual_jv = models.IntegerField(default=0)
    enable_manual_cv = models.IntegerField(default=0)

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='companyparameter_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='companyparameter_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
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

