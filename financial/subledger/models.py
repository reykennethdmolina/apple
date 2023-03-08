from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Subledger(models.Model):
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='subledger_chartofaccount')
    item_counter = models.IntegerField()
    document_type = models.CharField(max_length=10)
    document_id = models.IntegerField()
    document_num = models.CharField(max_length=10)
    document_date = models.DateField()
    subtype = models.CharField(max_length=50)
    dcsubtype = models.CharField(max_length=50)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='subledger_bankaccount', null=True,
                                    blank=True)
    department = models.ForeignKey('department.Department', related_name='subledger_department', null=True, blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='subledger_employee', null=True, blank=True)
    supplier = models.ForeignKey('supplier.Supplier', related_name='subledger_supplier', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='subledger_customer', null=True, blank=True)
    inventory = models.ForeignKey('inventoryitem.Inventoryitem', related_name='subledger_inventoryitem', null=True,
                                  blank=True)
    product = models.ForeignKey('product.Product', related_name='subledger_product', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='subledger_branch', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='subledger_unit', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='subledger_inputvat', null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='subledger_outputvat', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='subledger_ataxcode', null=True, blank=True)
    atccode = models.CharField(max_length=10, null=True, blank=True)
    atcrate = models.IntegerField(default=0, null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='subledger_vat', null=True, blank=True)
    vatcode = models.CharField(max_length=10, null=True, blank=True)
    vatrate = models.IntegerField(default=0, null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='subledger_wtax', null=True, blank=True)
    wtaxcode = models.CharField(max_length=10, null=True, blank=True)
    wtaxrate = models.IntegerField(default=0, null=True, blank=True)
    balancecode = models.CharField(max_length=1)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    particulars = models.TextField(null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    comments = models.CharField(max_length=250, null=True, blank=True)
    currency = models.ForeignKey('currency.Currency', related_name='subledger_currency', default=1)
    fxrate = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    fxamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    document_reftype = models.CharField(max_length=10, blank=True, null=True)
    document_refnum = models.CharField(max_length=100, blank=True, null=True)
    document_refdate = models.DateField(null=True, blank=True)
    document_refamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    document_refjv = models.ForeignKey('journalvoucher.Jvmain', related_name='subledger_docrefjv', null=True,
                                       blank=True)
    document_refjvnum = models.CharField(max_length=10, null=True, blank=True)
    document_refjvdate = models.DateField(null=True, blank=True)
    document_refap = models.ForeignKey('accountspayable.Apmain', related_name='subledger_docrefap', null=True,
                                       blank=True)
    document_refapnum = models.CharField(max_length=10, null=True, blank=True)
    document_refapdate = models.DateField(null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    document_status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    document_supplier = models.ForeignKey('supplier.Supplier', related_name='subledger_docsupplier', null=True,
                                          blank=True)
    document_supplieratc = models.ForeignKey('ataxcode.Ataxcode', related_name='subledger_docataxcode', null=True,
                                             blank=True)
    document_supplieratccode = models.CharField(max_length=10, null=True, blank=True)
    document_supplieratcrate = models.IntegerField(default=0, null=True, blank=True)
    document_suppliervat = models.ForeignKey('vat.Vat', related_name='subledger_docsuppliervat', null=True, blank=True)
    document_suppliervatcode = models.CharField(max_length=10, null=True, blank=True)
    document_suppliervatrate = models.IntegerField(default=0, null=True, blank=True)
    document_supplierinputvat = models.ForeignKey('inputvat.Inputvat', related_name='subledger_docsupplierinputvat',
                                                  null=True,
                                                  blank=True)
    document_customer = models.ForeignKey('customer.Customer', related_name='subledger_doccustomer', null=True,
                                          blank=True)
    document_customervat = models.ForeignKey('vat.Vat', related_name='subledger_doccustomervat', null=True, blank=True)
    document_customervatcode = models.CharField(max_length=10, null=True, blank=True)
    document_customervatrate = models.IntegerField(default=0)
    document_customerwtax = models.ForeignKey('wtax.Wtax', related_name='subledger_doccustomerwtax', null=True,
                                              blank=True)
    document_customerwtaxcode = models.CharField(max_length=10, null=True, blank=True)
    document_customerwtaxrate = models.IntegerField(default=0, null=True, blank=True)
    document_customeroutputvat = models.ForeignKey('outputvat.Outputvat', related_name='subledger_doccustomeroutputvat',
                                                   null=True,
                                                   blank=True)
    document_branch = models.ForeignKey('branch.Branch', related_name='subledger_docbranch', null=True, blank=True)
    document_payee = models.CharField(max_length=250, null=True, blank=True)
    document_bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='subledger_docbankaccount',
                                             null=True,
                                             blank=True)
    document_checknum = models.CharField(max_length=150, null=True, blank=True)
    document_checkdate = models.DateTimeField(null=True, blank=True)
    document_amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    document_duedate = models.DateField(null=True, blank=True)
    document_currency = models.ForeignKey('currency.Currency', related_name='subledger_doccurrency', default=1)
    document_fxrate = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    document_fxamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    document_collector = models.ForeignKey('collector.Collector', related_name='subledger_doccollector', null=True,
                                           blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='subledger_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='subledger_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)
    breakdownsource_id = models.IntegerField(null=True, blank=True)
    reference_number = models.CharField(max_length=50, null=True)

    class Meta:
        db_table = 'subledger'
        ordering = ['-pk']
        permissions = (("view_subledger", "Can view subledger"),)

    def get_absolute_url(self):
        return reverse('subledger:detail', kwargs={'pk': self.pk})

    def __str__(self):
        #return self.chartofaccount
        return unicode(self.chartofaccount)

    def __unicode__(self):
        #return self.chartofaccount
        return unicode(self.chartofaccount)

    def status_verbose(self):
        return dict(Subledger.STATUS_CHOICES)[self.status]


class logs_subledger(models.Model):
    chartofaccount = models.ForeignKey('chartofaccount.Chartofaccount', related_name='logs_subledger_chartofaccount')
    item_counter = models.IntegerField()
    document_type = models.CharField(max_length=10)
    document_id = models.IntegerField()
    document_num = models.CharField(max_length=10)
    document_date = models.DateField()
    subtype = models.CharField(max_length=50)
    dcsubtype = models.CharField(max_length=50)
    bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='logs_subledger_bankaccount', null=True,
                                    blank=True)
    department = models.ForeignKey('department.Department', related_name='logs_subledger_department', null=True,
                                   blank=True)
    employee = models.ForeignKey('employee.Employee', related_name='logs_subledger_employee', null=True, blank=True)
    # supplier = models.ForeignKey('supplier.Supplier', related_name='logs_subledger_supplier', null=True, blank=True)
    customer = models.ForeignKey('customer.Customer', related_name='logs_subledger_customer', null=True, blank=True)
    inventory = models.ForeignKey('inventoryitem.Inventoryitem', related_name='logs_subledger_inventoryitem', null=True,
                                  blank=True)
    product = models.ForeignKey('product.Product', related_name='logs_subledger_product', null=True, blank=True)
    branch = models.ForeignKey('branch.Branch', related_name='logs_subledger_branch', null=True, blank=True)
    unit = models.ForeignKey('unit.Unit', related_name='logs_subledger_unit', null=True, blank=True)
    inputvat = models.ForeignKey('inputvat.Inputvat', related_name='logs_subledger_inputvat', null=True, blank=True)
    outputvat = models.ForeignKey('outputvat.Outputvat', related_name='logs_subledger_outputvat', null=True, blank=True)
    ataxcode = models.ForeignKey('ataxcode.Ataxcode', related_name='logs_subledger_ataxcode', null=True, blank=True)
    atccode = models.CharField(max_length=10, null=True, blank=True)
    atcrate = models.IntegerField(default=0, null=True, blank=True)
    vat = models.ForeignKey('vat.Vat', related_name='logs_subledger_vat', null=True, blank=True)
    vatcode = models.CharField(max_length=10, null=True, blank=True)
    vatrate = models.IntegerField(default=0, null=True, blank=True)
    wtax = models.ForeignKey('wtax.Wtax', related_name='logs_subledger_wtax', null=True, blank=True)
    wtaxcode = models.CharField(max_length=10, null=True, blank=True)
    wtaxrate = models.IntegerField(default=0, null=True, blank=True)
    balancecode = models.CharField(max_length=1)
    amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    particulars = models.TextField(null=True, blank=True)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    comments = models.CharField(max_length=250, null=True, blank=True)
    currency = models.ForeignKey('currency.Currency', related_name='logs_subledger_currency', default=1)
    fxrate = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    fxamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    document_reftype = models.CharField(max_length=10, blank=True, null=True)
    document_refnum = models.CharField(max_length=100, blank=True, null=True)
    document_refdate = models.DateField(null=True, blank=True)
    document_refamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    document_refjv = models.ForeignKey('journalvoucher.Jvmain', related_name='logs_subledger_docrefjv', null=True,
                                       blank=True)
    document_refjvnum = models.CharField(max_length=10, null=True, blank=True)
    document_refjvdate = models.DateField(null=True, blank=True)
    document_refap = models.ForeignKey('accountspayable.Apmain', related_name='logs_subledger_docrefap', null=True,
                                       blank=True)
    document_refapnum = models.CharField(max_length=10, null=True, blank=True)
    document_refapdate = models.DateField(null=True, blank=True)
    STATUS_CHOICES = (
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('C', 'Cancelled'),
        ('O', 'Posted'),
        ('P', 'Printed'),
    )
    document_status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    document_supplier = models.ForeignKey('supplier.Supplier', related_name='logs_subledger_docsupplier', null=True,
                                          blank=True)
    document_supplieratc = models.ForeignKey('ataxcode.Ataxcode', related_name='logs_subledger_docataxcode', null=True,
                                             blank=True)
    document_supplieratccode = models.CharField(max_length=10, null=True, blank=True)
    document_supplieratcrate = models.IntegerField(default=0, null=True, blank=True)
    document_suppliervat = models.ForeignKey('vat.Vat', related_name='logs_subledger_docsuppliervat', null=True,
                                             blank=True)
    document_suppliervatcode = models.CharField(max_length=10, null=True, blank=True)
    document_suppliervatrate = models.IntegerField(default=0, null=True, blank=True)
    document_supplierinputvat = models.ForeignKey('inputvat.Inputvat',
                                                  related_name='logs_subledger_docsupplierinputvat', null=True,
                                                  blank=True)
    document_customer = models.ForeignKey('customer.Customer', related_name='logs_subledger_doccustomer', null=True,
                                          blank=True)
    document_customervat = models.ForeignKey('vat.Vat', related_name='logs_subledger_doccustomervat', null=True,
                                             blank=True)
    document_customervatcode = models.CharField(max_length=10, null=True, blank=True)
    document_customervatrate = models.IntegerField(default=0, null=True, blank=True)
    document_customerwtax = models.ForeignKey('wtax.Wtax', related_name='logs_subledger_doccustomerwtax', null=True,
                                              blank=True)
    document_customerwtaxcode = models.CharField(max_length=10, null=True, blank=True)
    document_customerwtaxrate = models.IntegerField(default=0, null=True, blank=True)
    document_customeroutputvat = models.ForeignKey('outputvat.Outputvat',
                                                   related_name='logs_subledger_doccustomeroutputvat', null=True,
                                                   blank=True)
    document_branch = models.ForeignKey('branch.Branch', related_name='logs_subledger_docbranch', null=True, blank=True)
    document_payee = models.CharField(max_length=250, null=True, blank=True)
    document_bankaccount = models.ForeignKey('bankaccount.Bankaccount', related_name='logs_subledger_docbankaccount',
                                             null=True,
                                             blank=True)
    document_checknum = models.CharField(max_length=150, null=True, blank=True)
    document_checkdate = models.DateTimeField(null=True, blank=True)
    document_amount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00)
    document_duedate = models.DateField(null=True, blank=True)
    document_currency = models.ForeignKey('currency.Currency', related_name='logs_subledger_doccurrency', default=1)
    document_fxrate = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    document_fxamount = models.DecimalField(decimal_places=2, max_digits=18, default=0.00, null=True, blank=True)
    document_collector = models.ForeignKey('collector.Collector', related_name='logs_subledger_doccollector', null=True,
                                           blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    enterby = models.ForeignKey(User, default=1, related_name='logs_subledger_enter')
    enterdate = models.DateTimeField(auto_now_add=True)
    modifyby = models.ForeignKey(User, default=1, related_name='logs_subledger_modify')
    modifydate = models.DateTimeField(auto_now_add=True)
    isdeleted = models.IntegerField(default=0)

    IMPORT_STATUS_CHOICES = (
        ('F', 'Failed'),
        ('S', 'Success'),
        ('P', 'Posted'),
    )
    batchkey = models.CharField(max_length=255, null=True, blank=True)
    importstatus = models.CharField(max_length=1, choices=IMPORT_STATUS_CHOICES, default='S')
    importremarks = models.CharField(max_length=255, null=True, blank=True)
    importdate = models.DateTimeField(auto_now_add=True)
    importby = models.ForeignKey(User, default=1, related_name='logs_subledger_importby')
    breakdownsource_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'logs_subledger'
        ordering = ['-pk']
        permissions = (("view_logs_subledger", "Can view logs_subledger"),)

    def get_absolute_url(self):
        return reverse('logs_subledger:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.chartofaccount

    def __unicode__(self):
        return self.chartofaccount

    def status_verbose(self):
        return dict(logs_subledger.STATUS_CHOICES)[self.status]
