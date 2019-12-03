from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from acctentry.views import updateallquery, validatetable, deleteallquery, generatekey, querystmtdetail, \
    querytotaldetail, savedetail, updatedetail
from supplier.models import Supplier
from branch.models import Branch
from bankbranchdisburse.models import Bankbranchdisburse
from vat.models import Vat
from inputvattype.models import Inputvattype
from companyparameter.models import Companyparameter
from creditterm.models import Creditterm
from currency.models import Currency
from apsubtype.models import Apsubtype
from aptype.models import Aptype
from operationalfund.models import Ofmain, Ofitem, Ofdetail
from processing_transaction.models import Poapvtransaction, Apvcvtransaction
from purchaseorder.models import Pomain, Podetail
from replenish_rfv.models import Reprfvmain, Reprfvdetail
from replenish_pcv.models import Reppcvmain, Reppcvdetail
from department.models import Department
from unit.models import Unit
from inputvat.models import Inputvat
from outputvat.models import Outputvat
from ataxcode.models import Ataxcode
from employee.models import Employee
from chartofaccount.models import Chartofaccount
from bankaccount.models import Bankaccount
from product.models import Product
from customer.models import Customer
from annoying.functions import get_object_or_None
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from . models import Apmain, Apdetail, Apdetailtemp, Apdetailbreakdown, Apdetailbreakdowntemp, Apupload
from django.template.loader import render_to_string
from endless_pagination.views import AjaxListView
from django.db.models import Q, Sum
from easy_pdf.views import PDFTemplateView
from dateutil.relativedelta import relativedelta
import datetime
from django.utils.dateformat import DateFormat
from utils.mixins import ReportContentMixin
from decimal import Decimal
import datetime
from django.utils.dateformat import DateFormat
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from collections import namedtuple
from django.db import connection
import pandas as pd
import io
import xlsxwriter
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class IndexView(AjaxListView):
    model = Apmain
    template_name = 'accountspayable/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'accountspayable/index_list.html'

    def get_queryset(self):

        if self.request.user.is_superuser:
            query = Apmain.objects.all()
        else:
            # user_employee = get_object_or_None(Employee, user=self.request.user)
            #query = Apmain.objects.filter(designatedapprover=self.request.user.id) | Apmain.objects.filter(
             #   enterby=self.request.user.id)
            #query = query.filter(isdeleted=0)
            query = Apmain.objects.all()

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(apnum__icontains=keysearch) |
                                 Q(apdate__icontains=keysearch) |
                                 Q(payeecode__icontains=keysearch) |
                                 Q(payeename__icontains=keysearch) |
                                 Q(vatcode__icontains=keysearch) |
                                 Q(ataxcode__icontains=keysearch) |
                                 Q(bankbranchdisbursebranch__icontains=keysearch) |
                                 Q(refno__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        #lookup
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')
        context['designatedapprover'] = Employee.objects.filter(isdeleted=0, jv_approver=1).order_by('firstname')
        creator = Apmain.objects.filter(isdeleted=0).values_list('enterby_id', flat=True)
        context['creator'] = User.objects.filter(id__in=set(creator)).order_by('first_name', 'last_name')
        context['pk'] = 0

        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Apmain
    template_name = 'accountspayable/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['detail'] = Apdetail.objects.filter(isdeleted=0).\
            filter(apmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Apdetail.objects.filter(isdeleted=0).\
            filter(apmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Apdetail.objects.filter(isdeleted=0).\
            filter(apmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, apmain=self.object.id).order_by('enterdate')
        ap_main_aggregate = Reprfvmain.objects.filter(isdeleted=0, apmain=self.object.id).aggregate(Sum('amount'))
        context['reprfv_total_amount'] = ap_main_aggregate['amount__sum']

        #lookup
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')
        context['pk'] = 0

        apacctgentries = Apdetail.objects.filter(ap_num=self.object.apnum, status='A', isdeleted=0, apmain=self.object)
        taxable_entries = apacctgentries.filter(balancecode='D', debitamount__gt=0.00).exclude(
            chartofaccount=Companyparameter.objects.get(code='PDI').coa_inputvat).order_by('item_counter')
        taxable_total = taxable_entries.aggregate(Sum('debitamount'))
        vat_entries = apacctgentries.filter(balancecode='D', debitamount__gt=0.00, chartofaccount=Companyparameter.
                                            objects.get(code='PDI').coa_inputvat).order_by('item_counter')
        vat_total = vat_entries.aggregate(Sum('debitamount'))
        aptrade_entries = apacctgentries.filter(balancecode='C', creditamount__gt=0.00).exclude(
            chartofaccount=Companyparameter.objects.get(code='PDI').coa_ewtax).order_by('item_counter')
        aptrade_total = aptrade_entries.aggregate(Sum('creditamount'))
        wtax_entries = apacctgentries.filter(balancecode='C', creditamount__gt=0.00, chartofaccount=Companyparameter.
                                             objects.get(code='PDI').coa_ewtax).order_by('item_counter')
        wtax_total = wtax_entries.aggregate(Sum('creditamount'))

        if self.object.vatrate > 0:
            context['vatablesale'] = taxable_total['debitamount__sum']
            context['vatexemptsale'] = 0
            context['vatzeroratedsale'] = 0
        elif self.object.vatcode == 'VE':
            context['vatablesale'] = 0
            context['vatexemptsale'] = taxable_total['debitamount__sum']
            context['vatzeroratedsale'] = 0
        elif self.object.vatcode == 'ZE' or self.object.vatcode == 'VATNA':
            context['vatablesale'] = 0
            context['vatexemptsale'] = 0
            context['vatzeroratedsale'] = taxable_total['debitamount__sum']

        context['totalsale'] = taxable_total['debitamount__sum']
        context['addvat'] = vat_total['debitamount__sum']
        context['totalpayment'] = aptrade_total['creditamount__sum']
        context['wtaxamount'] = wtax_total['creditamount__sum']
        context['wtaxrate'] = self.object.ataxrate
        context['potrans'] = Poapvtransaction.objects.filter(apmain_id=self.object.pk)
        context['cvtrans'] = Apvcvtransaction.objects.filter(apmain_id=self.object.pk)
        context['uploadlist'] = Apupload.objects.filter(apmain_id=self.object.pk).order_by('enterdate')

        #print context['potrans']

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Apmain
    template_name = 'accountspayable/create.html'
    fields = ['apdate', 'aptype', 'apsubtype', 'payee', 'branch',
              'bankaccount', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars', 'remarks',
              'currency', 'fxrate', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('accountspayable.add_apmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        if self.request.POST.get('payee', False):
            context['payee'] = Supplier.objects.get(pk=self.request.POST['payee'], isdeleted=0)
        context['currency'] = Currency.objects.filter(isdeleted=0)
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('code')
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        context['designatedapprover'] = Employee.objects.filter(isdeleted=0, jv_approver=1).order_by('firstname') #User.objects.filter(is_active=1).order_by('first_name')
        context['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, apmain__isnull=True).order_by('enterdate')
        context['reppcvmain'] = Reppcvmain.objects.filter(isdeleted=0, apmain__isnull=True).order_by('enterdate')

        #lookup
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')

        closetransaction = Companyparameter.objects.all().first().last_closed_date
        validtransaction = closetransaction + relativedelta(months=1)
        context['validtransaction'] = validtransaction

        return context

    def form_valid(self, form):
        from django.db.models import CharField
        from django.db.models.functions import Length

        CharField.register_lookup(Length, 'length')

        self.object = form.save(commit=False)
        try:
            apnumlast = Apmain.objects.filter(apnum__length=10).latest('apnum')
            latestapnum = str(apnumlast)
            print latestapnum
            if latestapnum[0:4] == str(datetime.datetime.now().year):
                apnum = str(datetime.datetime.now().year)
                last = str(int(latestapnum[4:])+1)
                zero_addon = 6 - len(last)
                for x in range(0, zero_addon):
                    apnum += '0'
                apnum += last
            else:
                apnum = str(datetime.datetime.now().year) + '000001'
        except Apmain.DoesNotExist:
            apnum = str(datetime.datetime.now().year) + '000001'

        vatobject = Vat.objects.get(pk=self.request.POST['vat'], isdeleted=0)
        if self.request.POST['atax']:
            ataxobject = Ataxcode.objects.get(pk=self.request.POST['atax'], isdeleted=0)
        payeeobject = Supplier.objects.get(pk=self.request.POST['payee'], isdeleted=0)
        # bankbranchdisburseobject = Bankbranchdisburse.objects.get(pk=self.request.POST['bankbranchdisburse'], isdeleted=0)

        self.object.apnum = apnum
        self.object.apstatus = 'F'
        self.object.vatcode = vatobject.code
        self.object.vatrate = vatobject.rate
        if self.request.POST['atax']:
            self.object.ataxcode = ataxobject.code
            self.object.ataxrate = ataxobject.rate
        self.object.payeecode = payeeobject.code
        self.object.payeename = payeeobject.name
        # self.object.bankbranchdisbursebranch = bankbranchdisburseobject.branch
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        # accounting entry starts here..
        source = 'apdetailtemp'
        mainid = self.object.id
        num = self.object.apnum
        secretkey = self.request.POST['secretkey']

        apmaindate = self.object.apdate

        savedetail(source, mainid, num, secretkey, self.request.user, apmaindate)

        # save apmain in reprfvmain, reprfvdetail, ofmain
        for i in range(len(self.request.POST.getlist('rfv_checkbox'))):
            reprfvmain = Reprfvmain.objects.get(pk=int(self.request.POST.getlist('rfv_checkbox')[i]))
            reprfvmain.apmain = self.object
            reprfvmain.save()
            reprfvdetail = Reprfvdetail.objects.filter(reprfvmain=reprfvmain)
            for data in reprfvdetail:
                data.apmain = self.object
                data.save()
                ofmain = Ofmain.objects.get(reprfvdetail=data)
                ofmain.apmain = self.object
                ofmain.save()
        # save apmain in reprfvmain, reprfvdetail, ofmain

        # save apmain in reppcvmain, reppcvdetail, ofmain
        for i in range(len(self.request.POST.getlist('pcv_checkbox'))):
            reppcvmain = Reppcvmain.objects.get(pk=int(self.request.POST.getlist('pcv_checkbox')[i]))
            reppcvmain.apmain = self.object
            reppcvmain.save()
            reppcvdetail = Reppcvdetail.objects.filter(reppcvmain=reppcvmain)
            for data in reppcvdetail:
                data.apmain = self.object
                data.save()
                ofmain = Ofmain.objects.get(reppcvdetail=data)
                ofmain.apmain = self.object
                ofmain.save()
        # save apmain in reprfvmain, reprfvdetail, ofmain

        totaldebitamount = Apdetail.objects.filter(isdeleted=0).filter(apmain_id=self.object.id).aggregate(
            Sum('debitamount'))
        totalcreditamount = Apdetail.objects.filter(isdeleted=0).filter(apmain_id=self.object.id).aggregate(
            Sum('creditamount'))

        if totaldebitamount['debitamount__sum'] == totalcreditamount['creditamount__sum']:
            self.object.amount = totaldebitamount['debitamount__sum']
            self.object.save(update_fields=['amount'])
        else:
            print "Debit and Credit amounts are not equal. AP Amount is not saved."

        return HttpResponseRedirect('/accountspayable/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Apmain
    template_name = 'accountspayable/edit.html'
    fields = ['apdate', 'aptype', 'apsubtype', 'payee', 'branch',
              'bankaccount', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars', 'remarks',
              'currency', 'fxrate', 'designatedapprover', 'apstatus']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('accountspayable.change_apmain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # accounting entry starts here
    def get_initial(self):
        self.mysecretkey = generatekey(self)

        detailinfo = Apdetail.objects.filter(apmain=self.object.pk).order_by('item_counter')

        for drow in detailinfo:
            detail = Apdetailtemp()
            detail.secretkey = self.mysecretkey
            detail.ap_num = drow.ap_num
            detail.apmain = drow.apmain_id
            detail.apdetail = drow.pk
            detail.item_counter = drow.item_counter
            detail.ap_date = drow.ap_date
            detail.chartofaccount = drow.chartofaccount_id
            detail.bankaccount = drow.bankaccount_id
            detail.employee = drow.employee_id
            detail.supplier = drow.supplier_id
            detail.customer = drow.customer_id
            detail.department = drow.department_id
            detail.unit = drow.unit_id
            detail.branch = drow.branch_id
            detail.product = drow.product_id
            detail.inputvat = drow.inputvat_id
            detail.outputvat = drow.outputvat_id
            detail.vat = drow.vat_id
            detail.wtax = drow.wtax_id
            detail.ataxcode = drow.ataxcode_id
            detail.debitamount = drow.debitamount
            detail.creditamount = drow.creditamount
            detail.balancecode = drow.balancecode
            detail.customerbreakstatus = drow.customerbreakstatus
            detail.supplierbreakstatus = drow.supplierbreakstatus
            detail.employeebreakstatus = drow.employeebreakstatus
            detail.isdeleted = 0
            detail.modifyby = self.request.user
            detail.enterby = self.request.user
            detail.modifydate = datetime.datetime.now()
            detail.isautogenerated = drow.isautogenerated
            detail.save()

            detailtempid = detail.id

            breakinfo = Apdetailbreakdown.objects.\
                filter(apdetail_id=drow.id).order_by('pk', 'datatype')
            if breakinfo:
                for brow in breakinfo:
                    breakdown = Apdetailbreakdowntemp()
                    breakdown.ap_num = drow.ap_num
                    breakdown.secretkey = self.mysecretkey
                    breakdown.apmain = drow.apmain_id
                    breakdown.apdetail = drow.pk
                    breakdown.apdetailtemp = detailtempid
                    breakdown.apdetailbreakdown = brow.pk
                    breakdown.item_counter = brow.item_counter
                    breakdown.ap_date = brow.ap_date
                    breakdown.chartofaccount = brow.chartofaccount_id
                    breakdown.particular = brow.particular
                    # Return None if object is empty
                    breakdown.bankaccount = brow.bankaccount_id
                    breakdown.employee = brow.employee_id
                    breakdown.supplier = brow.supplier_id
                    breakdown.customer = brow.customer_id
                    breakdown.department = brow.department_id
                    breakdown.unit = brow.unit_id
                    breakdown.branch = brow.branch_id
                    breakdown.product = brow.product_id
                    breakdown.inputvat = brow.inputvat_id
                    breakdown.outputvat = brow.outputvat_id
                    breakdown.vat = brow.vat_id
                    breakdown.wtax = brow.wtax_id
                    breakdown.ataxcode = brow.ataxcode_id
                    breakdown.debitamount = brow.debitamount
                    breakdown.creditamount = brow.creditamount
                    breakdown.balancecode = brow.balancecode
                    breakdown.datatype = brow.datatype
                    breakdown.customerbreakstatus = brow.customerbreakstatus
                    breakdown.supplierbreakstatus = brow.supplierbreakstatus
                    breakdown.employeebreakstatus = brow.employeebreakstatus
                    breakdown.isdeleted = 0
                    breakdown.modifyby = self.request.user
                    breakdown.enterby = self.request.user
                    breakdown.modifydate = datetime.datetime.now()
                    breakdown.save()
    # accounting entry ends here

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        if self.request.POST.get('payee', False):
            context['payee'] = Supplier.objects.get(pk=self.request.POST['payee'], isdeleted=0)
        elif self.object.payee:
            context['payee'] = Supplier.objects.get(pk=self.object.payee.id, isdeleted=0)
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')
        context['currency'] = Currency.objects.filter(isdeleted=0)
        context['apnum'] = self.object.apnum
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('code')
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = self.object.pk
        context['designatedapprover'] = Employee.objects.filter(isdeleted=0, jv_approver=1).order_by('firstname') #User.objects.filter(is_active=1).order_by('first_name')
        context['originalapstatus'] = Apmain.objects.get(pk=self.object.id).apstatus
        context['actualapprover'] = None if Apmain.objects.get(
            pk=self.object.id).actualapprover is None else Apmain.objects.get(pk=self.object.id).actualapprover.id
        context['savedapsubtype'] = Apmain.objects.get(pk=self.object.id).apsubtype.code
        context['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, apmain=self.object.id).order_by('enterdate')
        ap_main_aggregate = Reprfvmain.objects.filter(isdeleted=0, apmain=self.object.id).aggregate(Sum('amount'))
        context['reprfv_total_amount'] = ap_main_aggregate['amount__sum']

        context['selectedapsubtype'] = self.object.apsubtype.code

        # accounting entry starts here
        context['secretkey'] = self.mysecretkey
        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'apdetailtemp',
            'tablebreakdowntemp': 'apdetailbreakdowntemp',

            'datatemp': querystmtdetail('apdetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('apdetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        # accounting entry ends here

        apacctgentries = Apdetail.objects.filter(ap_num=self.object.apnum, status='A', isdeleted=0, apmain=self.object)
        taxable_entries = apacctgentries.filter(balancecode='D', debitamount__gt=0.00).exclude(
            chartofaccount=Companyparameter.objects.get(code='PDI').coa_inputvat).order_by('item_counter')
        taxable_total = taxable_entries.aggregate(Sum('debitamount'))
        vat_entries = apacctgentries.filter(balancecode='D', debitamount__gt=0.00, chartofaccount=Companyparameter.
                                            objects.get(code='PDI').coa_inputvat).order_by('item_counter')
        vat_total = vat_entries.aggregate(Sum('debitamount'))
        aptrade_entries = apacctgentries.filter(balancecode='C', creditamount__gt=0.00).exclude(
            chartofaccount=Companyparameter.objects.get(code='PDI').coa_ewtax).order_by('item_counter')
        aptrade_total = aptrade_entries.aggregate(Sum('creditamount'))
        wtax_entries = apacctgentries.filter(balancecode='C', creditamount__gt=0.00, chartofaccount=Companyparameter.
                                             objects.get(code='PDI').coa_ewtax).order_by('item_counter')
        wtax_total = wtax_entries.aggregate(Sum('creditamount'))

        if self.object.vatrate > 0:
            context['vatablesale'] = taxable_total['debitamount__sum']
            context['vatexemptsale'] = 0
            context['vatzeroratedsale'] = 0
        elif self.object.vatcode == 'VE':
            context['vatablesale'] = 0
            context['vatexemptsale'] = taxable_total['debitamount__sum']
            context['vatzeroratedsale'] = 0
        elif self.object.vatcode == 'ZE' or self.object.vatcode == 'VATNA':
            context['vatablesale'] = 0
            context['vatexemptsale'] = 0
            context['vatzeroratedsale'] = taxable_total['debitamount__sum']

        context['totalsale'] = taxable_total['debitamount__sum']
        context['addvat'] = vat_total['debitamount__sum']
        context['totalpayment'] = aptrade_total['creditamount__sum']
        context['wtaxamount'] = wtax_total['creditamount__sum']
        context['wtaxrate'] = self.object.ataxrate
        # context['datainfo'] = self.object
        context['footers'] = [
            self.object.enterby.first_name + " " + self.object.enterby.last_name if self.object.enterby else '',
            self.object.enterdate,
            self.object.modifyby.first_name + " " + self.object.modifyby.last_name if self.object.modifyby else '',
            self.object.modifydate,
            self.object.postby.first_name + " " + self.object.postby.last_name if self.object.postby else '',
            self.object.postdate,
            self.object.closeby.first_name + " " + self.object.closeby.last_name if self.object.closeby else '',
            self.object.closedate,
            ]

        return context

    def form_valid(self, form):
        if self.request.POST['originalapstatus'] != 'R':
            self.object = form.save(commit=False)
            self.object.payee = Supplier.objects.get(pk=self.request.POST['payee'])
            self.object.payeecode = self.object.payee.code
            self.object.payeename = self.object.payee.name
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            # self.object.bankbranchdisbursebranch = self.object.bankbranchdisburse.branch
            self.object.vatcode = self.object.vat.code
            self.object.vatrate = self.object.vat.rate
            if self.object.atax:
                self.object.ataxcode = self.object.atax.code
                self.object.ataxrate = self.object.atax.rate

            self.object.save(update_fields=['apdate', 'aptype', 'apsubtype', 'payee', 'payeecode', 'payeename',
                                            'branch', 'bankaccount', 'vat', 'atax',
                                            'inputvattype', 'creditterm', 'duedate',
                                            'refno', 'deferred', 'particulars', 'remarks',
                                            'currency', 'fxrate', 'designatedapprover',
                                            'modifyby', 'modifydate', 'apstatus', 'vatcode', 'vatrate', 'ataxcode',
                                            'ataxrate'])

            if self.object.apstatus == 'F':
                self.object.designatedapprover = User.objects.get(pk=self.request.POST['designatedapprover'])
                self.object.save(update_fields=['designatedapprover'])

            # revert status from APPROVED/DISAPPROVED to For Approval if no response date or approver response is saved
            # remove approval details if APSTATUS is not APPROVED/DISAPPROVED
            if self.object.apstatus == 'A' or self.object.apstatus == 'D':
                if self.object.responsedate is None or self.object.approverresponse is None or self.object.\
                        actualapprover is None:
                    print self.object.responsedate
                    print self.object.approverresponse
                    print self.object.actualapprover
                    self.object.responsedate = None
                    self.object.approverremarks = None
                    self.object.approverresponse = None
                    self.object.actualapprover = None
                    self.object.apstatus = 'F'
                    self.object.save(update_fields=['responsedate', 'approverremarks', 'approverresponse',
                                                    'actualapprover', 'apstatus'])
            elif self.object.apstatus == 'F':
                self.object.responsedate = None
                self.object.approverremarks = None
                self.object.approverresponse = None
                self.object.actualapprover = None
                self.object.save(update_fields=['responsedate', 'approverremarks', 'approverresponse',
                                                'actualapprover'])

            # revert status from RELEASED to Approved if no release date is saved
            # remove release details if APSTATUS is not RELEASED
            if self.object.apstatus == 'R' and self.object.releasedate is None:
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.apstatus = 'A'
                self.object.save(update_fields=['releaseby', 'releasedate', 'apstatus'])
            elif self.object.apstatus != 'R':
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.save(update_fields=['releaseby', 'releasedate'])

            # accounting entry starts here..
            source = 'apdetailtemp'
            mainid = self.object.id
            num = self.object.apnum
            secretkey = self.request.POST['secretkey']
            print self.object.apdate
            print 'apdate'
            apmaindate = self.object.apdate

            updatedetail(source, mainid, num, secretkey, self.request.user, apmaindate)

            totaldebitamount = Apdetail.objects.filter(isdeleted=0).filter(apmain_id=self.object.id).aggregate(
                Sum('debitamount'))
            totalcreditamount = Apdetail.objects.filter(isdeleted=0).filter(apmain_id=self.object.id).aggregate(
                Sum('creditamount'))

            if totaldebitamount['debitamount__sum'] == totalcreditamount['creditamount__sum']:
                self.object.amount = totaldebitamount['debitamount__sum']
                self.object.save(update_fields=['amount'])
            else:
                print "Debit and Credit amounts are not equal. AP Amount is not saved."

        else:
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['modifyby', 'modifydate', 'remarks'])

        return HttpResponseRedirect('/accountspayable/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Apmain
    template_name = 'accountspayable/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('accountspayable.delete_apmain') or self.object.status == 'O' \
                or self.object.apstatus == 'A' or self.object.apstatus == 'I' or self.object.apstatus == 'R':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.apstatus = 'D'
        self.object.save()

        # remove references in reprfvmain, reprfvdetail, ofmain
        reprfvmain = Reprfvmain.objects.filter(apmain=self.object.id)
        for data in reprfvmain:
            data.apmain = None
            data.save()

        reprfvdetail = Reprfvdetail.objects.filter(apmain=self.object.id)
        for data in reprfvdetail:
            data.apmain = None
            data.save()

        ofmain = Ofmain.objects.filter(apmain=self.object.id)
        for data in ofmain:
            data.apmain = None
            data.save()
        # remove references in reprfvmain, reprfvdetail, ofmain

        # remove references in PO tables
        poapvtrans = Poapvtransaction.objects.filter(apmain=self.object)
        for data in poapvtrans:
            podetail = Podetail.objects.filter(pk=data.podetail.id).first()
            podetail.apvtotalamount -= data.apamount
            podetail.apvremainingamount += data.apamount
            podetail.isfullyapv = 0
            podetail.save()
            pomain = Pomain.objects.filter(pk=podetail.pomain.id).first()
            pomain.apvamount -= data.apamount
            pomain.totalremainingamount += data.apamount
            pomain.isfullyapv = 0
            pomain.save()
            data.delete()

        return HttpResponseRedirect('/accountspayable')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Apmain
    template_name = 'accountspayable/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['apmain'] = Apmain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['detail'] = Apdetail.objects.filter(isdeleted=0). \
            filter(apmain_id=self.kwargs['pk']).order_by('-balancecode', 'item_counter')
        context['totaldebitamount'] = Apdetail.objects.filter(isdeleted=0). \
            filter(apmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Apdetail.objects.filter(isdeleted=0). \
            filter(apmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, apmain=self.kwargs['pk']).order_by('enterdate')
        ap_main_aggregate = Reprfvmain.objects.filter(isdeleted=0, apmain=self.kwargs['pk']).aggregate(Sum('amount'))
        context['reprfv_total_amount'] = ap_main_aggregate['amount__sum']

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        taxable_entries = context['detail'].filter(balancecode='D', debitamount__gt=0.00).exclude(
            chartofaccount=Companyparameter.objects.get(code='PDI').coa_inputvat).order_by('item_counter')
        taxable_total = taxable_entries.aggregate(Sum('debitamount'))
        vat_entries = context['detail'].filter(balancecode='D', debitamount__gt=0.00, chartofaccount=Companyparameter.
                                            objects.get(code='PDI').coa_inputvat).order_by('item_counter')
        vat_total = vat_entries.aggregate(Sum('debitamount'))
        aptrade_entries = context['detail'].filter(balancecode='C', creditamount__gt=0.00).exclude(
            chartofaccount=Companyparameter.objects.get(code='PDI').coa_ewtax).order_by('item_counter')
        aptrade_total = aptrade_entries.aggregate(Sum('creditamount'))
        wtax_entries = context['detail'].filter(balancecode='C', creditamount__gt=0.00, chartofaccount=Companyparameter.
                                             objects.get(code='PDI').coa_ewtax).order_by('item_counter')
        wtax_total = wtax_entries.aggregate(Sum('creditamount'))

        if context['apmain'].vatrate > 0:
            context['vatablesale'] = taxable_total['debitamount__sum']
            context['vatexemptsale'] = 0
            context['vatzeroratedsale'] = 0
        elif context['apmain'].vatcode == 'VE':
            context['vatablesale'] = 0
            context['vatexemptsale'] = taxable_total['debitamount__sum']
            context['vatzeroratedsale'] = 0
        elif context['apmain'].vatcode == 'ZE' or context['apmain'].vatcode == 'VATNA':
            context['vatablesale'] = 0
            context['vatexemptsale'] = 0
            context['vatzeroratedsale'] = taxable_total['debitamount__sum']

        context['totalsale'] = taxable_total['debitamount__sum']
        context['addvat'] = vat_total['debitamount__sum']
        context['totalpayment'] = aptrade_total['creditamount__sum']
        context['wtaxamount'] = wtax_total['creditamount__sum']
        context['wtaxrate'] = context['apmain'].ataxrate

        printedap = Apmain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        printedap.print_ctr += 1
        printedap.save()
        return context


# @csrf_exempt
# def approve(request):
#     if request.method == 'POST':
#         ap_for_approval = Apmain.objects.get(apnum=request.POST['apnum'])
#         if request.user.has_perm('accountspayable.approve_allap') or \
#                 request.user.has_perm('accountspayable.approve_assignedap'):
#             if request.user.has_perm('accountspayable.approve_allap') or \
#                     (request.user.has_perm('accountspayable.approve_assignedap') and
#                              ap_for_approval.designatedapprover == request.user):
#                 print "back to in-process = " + str(request.POST['backtoinprocess'])
#                 if request.POST['originalapstatus'] != 'R' or int(request.POST['backtoinprocess']) == 1:
#                     ap_for_approval.apstatus = request.POST['approverresponse']
#                     ap_for_approval.isdeleted = 0
#                     if request.POST['approverresponse'] == 'D':
#                         ap_for_approval.status = 'C'
#                     else:
#                         ap_for_approval.status = 'A'
#                     ap_for_approval.approverresponse = request.POST['approverresponse']
#                     ap_for_approval.responsedate = request.POST['responsedate']
#                     ap_for_approval.actualapprover = User.objects.get(pk=request.user.id)
#                     ap_for_approval.approverremarks = request.POST['approverremarks']
#                     ap_for_approval.releaseby = None
#                     ap_for_approval.releasedate = None
#                     ap_for_approval.save()
#                     data = {
#                         'status': 'success',
#                         'apnum': ap_for_approval.apnum,
#                         'newapstatus': ap_for_approval.apstatus,
#                     }
#                 else:
#                     data = {
#                         'status': 'error',
#                     }
#             else:
#                 data = {
#                     'status': 'error',
#                 }
#         else:
#             data = {
#                 'status': 'error',
#             }
#     else:
#         data = {
#             'status': 'error',
#         }
#
#     return JsonResponse(data)

@csrf_exempt
def approve(request):
    if request.method == 'POST':
        approval = Apmain.objects.get(pk=request.POST['id'])

        if (approval.apstatus != 'R' and approval.status != 'O'):
            approval.apstatus = 'A'
            approval.responsedate = str(datetime.datetime.now())
            approval.approverremarks = str(approval.approverremarks) +';'+ 'Approved'
            approval.actualapprover = User.objects.get(pk=request.user.id)
            approval.save()
            data = {'status': 'success'}
        else:
            data = {'status': 'error'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def disapprove(request):
    if request.method == 'POST':
        approval = Apmain.objects.get(pk=request.POST['id'])
        if (approval.apstatus != 'R' and approval.status != 'O'):
            approval.apstatus = 'D'
            approval.responsedate = str(datetime.datetime.now())
            approval.approverremarks = str(approval.approverremarks) +';'+ request.POST['reason']
            approval.actualapprover = User.objects.get(pk=request.user.id)
            approval.save()
            data = {'status': 'success'}
        else:
            data = {'status': 'error'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def posting(request):
    if request.method == 'POST':
        release = Apmain.objects.filter(pk=request.POST['id']).update(apstatus='R',releaseby=User.objects.get(pk=request.user.id),releasedate= str(datetime.datetime.now()))

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


@csrf_exempt
def gopost(request):

    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        release = Apmain.objects.filter(pk__in=ids).update(apstatus='R',releaseby=User.objects.get(pk=request.user.id),releasedate= str(datetime.datetime.now()))

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def release(request):
    if request.method == 'POST':
        ap_for_release = Apmain.objects.get(apnum=request.POST['apnum'])
        if ap_for_release.apstatus != 'F' and ap_for_release.apstatus != 'D':
            ap_for_release.releaseby = User.objects.get(pk=request.POST['releaseby'])
            ap_for_release.releasedate = request.POST['releasedate']
            ap_for_release.apstatus = 'R'
            ap_for_release.save()
            data = {
                'status': 'success',
            }
        else:
            data = {
                'status': 'error',
            }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)

@csrf_exempt
def gounpost(request):
    if request.method == 'POST':
        approval = Apmain.objects.get(pk=request.POST['id'])
        if (approval.apstatus == 'R' and approval.status != 'O'):
            approval.apstatus = 'A'
            approval.save()
            data = {'status': 'success'}
        else:
            data = {'status': 'error'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def importreprfv(request):
    if request.method == 'POST':
        first_ofmain = Ofmain.objects.filter(reprfvmain=request.POST.getlist('checked_reprfvmain[]')[0], isdeleted=0,
                                             status='A').first()
        first_ofitem = Ofitem.objects.filter(ofmain=first_ofmain.id, isdeleted=0, status='A').first()

        ofdetail = Ofdetail.objects.filter(ofmain__reprfvmain__in=set(request.POST.getlist('checked_reprfvmain[]'))).\
            order_by('ofmain', 'item_counter')
        # amount_totals = ofdetail.aggregate(Sum('debitamount'), Sum('creditamount'))
        ofdetail = ofdetail.values('chartofaccount__accountcode',
                                   'chartofaccount__id',
                                   'chartofaccount__title',
                                   'chartofaccount__description',
                                   'bankaccount__id',
                                   'bankaccount__accountnumber',
                                   'department__id',
                                   'department__departmentname',
                                   'employee__id',
                                   'employee__firstname',
                                   'supplier__id',
                                   'supplier__name',
                                   'customer__id',
                                   'customer__name',
                                   'branch__id',
                                   'branch__description',
                                   'product__id',
                                   'product__description',
                                   'unit__id',
                                   'unit__description',
                                   'inputvat__id',
                                   'inputvat__description',
                                   'outputvat__id',
                                   'outputvat__description',
                                   'vat__id',
                                   'vat__description',
                                   'wtax__id',
                                   'wtax__description',
                                   'ataxcode__id',
                                   'ataxcode__code',
                                   'balancecode') \
                           .annotate(Sum('debitamount'), Sum('creditamount')) \
                           .order_by('-chartofaccount__accountcode',
                                     'bankaccount__accountnumber',
                                     'department__departmentname',
                                     'employee__firstname',
                                     'supplier__name',
                                     'customer__name',
                                     'branch__description',
                                     'product__description',
                                     'inputvat__description',
                                     'outputvat__description',
                                     '-vat__description',
                                     'wtax__description',
                                     'ataxcode__code')

        # set isdeleted=2 for existing detailtemp data
        data_table = validatetable(request.POST['table'])
        deleteallquery(request.POST['table'], request.POST['secretkey'])

        if 'apnum' in request.POST:
            if request.POST['apnum']:
                updateallquery(request.POST['table'], request.POST['apnum'])
        # set isdeleted=2 for existing detailtemp data

        i = 1
        for detail in ofdetail:
            apdetailtemp = Apdetailtemp()
            apdetailtemp.item_counter = i
            apdetailtemp.secretkey = request.POST['secretkey']
            apdetailtemp.ap_date = datetime.datetime.now()
            apdetailtemp.chartofaccount = detail['chartofaccount__id']
            apdetailtemp.bankaccount = detail['bankaccount__id']
            apdetailtemp.department = detail['department__id']
            apdetailtemp.employee = detail['employee__id']
            apdetailtemp.supplier = detail['supplier__id']
            apdetailtemp.customer = detail['customer__id']
            apdetailtemp.unit = detail['unit__id']
            apdetailtemp.branch = detail['branch__id']
            apdetailtemp.product = detail['product__id']
            apdetailtemp.inputvat = detail['inputvat__id']
            apdetailtemp.outputvat = detail['outputvat__id']
            apdetailtemp.vat = detail['vat__id']
            apdetailtemp.wtax = detail['wtax__id']
            apdetailtemp.ataxcode = detail['ataxcode__id']
            apdetailtemp.debitamount = detail['debitamount__sum']
            apdetailtemp.creditamount = detail['creditamount__sum']
            apdetailtemp.balancecode = detail['balancecode']
            apdetailtemp.enterby = request.user
            apdetailtemp.modifyby = request.user
            apdetailtemp.save()
            i += 1

        context = {
            'tabledetailtemp': data_table['str_detailtemp'],
            'tablebreakdowntemp': data_table['str_detailbreakdowntemp'],
            'datatemp': querystmtdetail(data_table['str_detailtemp'], request.POST['secretkey']),
            'datatemptotal': querytotaldetail(data_table['str_detailtemp'], request.POST['secretkey']),
        }

        data = {
            'datatable': render_to_string('acctentry/datatable.html', context),
            'status': 'success',
            'branch': first_ofmain.branch_id,
            'vat': first_ofitem.vat_id,
            'atc': first_ofitem.atc_id,
            'inputvattype': first_ofitem.inputvattype_id,
            'deferredvat': first_ofitem.deferredvat
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)

@csrf_exempt
def importreppcv(request):
    if request.method == 'POST':
        first_ofmain = Ofmain.objects.filter(reppcvmain=request.POST.getlist('checked_reppcvmain[]')[0], isdeleted=0,
                                             status='A').first()
        first_ofitem = Ofitem.objects.filter(ofmain=first_ofmain.id, isdeleted=0, status='A').first()

        ofdetail = Ofdetail.objects.filter(ofmain__reppcvmain__in=set(request.POST.getlist('checked_reppcvmain[]'))).\
            order_by('ofmain', 'item_counter')
        # amount_totals = ofdetail.aggregate(Sum('debitamount'), Sum('creditamount'))
        ofdetail = ofdetail.values('chartofaccount__accountcode',
                                   'chartofaccount__id',
                                   'chartofaccount__title',
                                   'chartofaccount__description',
                                   'bankaccount__id',
                                   'bankaccount__accountnumber',
                                   'department__id',
                                   'department__departmentname',
                                   'employee__id',
                                   'employee__firstname',
                                   'supplier__id',
                                   'supplier__name',
                                   'customer__id',
                                   'customer__name',
                                   'branch__id',
                                   'branch__description',
                                   'product__id',
                                   'product__description',
                                   'unit__id',
                                   'unit__description',
                                   'inputvat__id',
                                   'inputvat__description',
                                   'outputvat__id',
                                   'outputvat__description',
                                   'vat__id',
                                   'vat__description',
                                   'wtax__id',
                                   'wtax__description',
                                   'ataxcode__id',
                                   'ataxcode__code',
                                   'balancecode') \
                           .annotate(Sum('debitamount'), Sum('creditamount')) \
                           .order_by('-chartofaccount__accountcode',
                                     'bankaccount__accountnumber',
                                     'department__departmentname',
                                     'employee__firstname',
                                     'supplier__name',
                                     'customer__name',
                                     'branch__description',
                                     'product__description',
                                     'inputvat__description',
                                     'outputvat__description',
                                     '-vat__description',
                                     'wtax__description',
                                     'ataxcode__code')

        # set isdeleted=2 for existing detailtemp data
        data_table = validatetable(request.POST['table'])
        deleteallquery(request.POST['table'], request.POST['secretkey'])

        if 'apnum' in request.POST:
            if request.POST['apnum']:
                updateallquery(request.POST['table'], request.POST['apnum'])
        # set isdeleted=2 for existing detailtemp data

        i = 1
        for detail in ofdetail:
            apdetailtemp = Apdetailtemp()
            apdetailtemp.item_counter = i
            apdetailtemp.secretkey = request.POST['secretkey']
            apdetailtemp.ap_date = datetime.datetime.now()
            apdetailtemp.chartofaccount = detail['chartofaccount__id']
            apdetailtemp.bankaccount = detail['bankaccount__id']
            apdetailtemp.department = detail['department__id']
            apdetailtemp.employee = detail['employee__id']
            apdetailtemp.supplier = detail['supplier__id']
            apdetailtemp.customer = detail['customer__id']
            apdetailtemp.unit = detail['unit__id']
            apdetailtemp.branch = detail['branch__id']
            apdetailtemp.product = detail['product__id']
            apdetailtemp.inputvat = detail['inputvat__id']
            apdetailtemp.outputvat = detail['outputvat__id']
            apdetailtemp.vat = detail['vat__id']
            apdetailtemp.wtax = detail['wtax__id']
            apdetailtemp.ataxcode = detail['ataxcode__id']
            apdetailtemp.debitamount = detail['debitamount__sum']
            apdetailtemp.creditamount = detail['creditamount__sum']
            apdetailtemp.balancecode = detail['balancecode']
            apdetailtemp.enterby = request.user
            apdetailtemp.modifyby = request.user
            apdetailtemp.save()
            i += 1

        context = {
            'tabledetailtemp': data_table['str_detailtemp'],
            'tablebreakdowntemp': data_table['str_detailbreakdowntemp'],
            'datatemp': querystmtdetail(data_table['str_detailtemp'], request.POST['secretkey']),
            'datatemptotal': querytotaldetail(data_table['str_detailtemp'], request.POST['secretkey']),
        }

        data = {
            'datatable': render_to_string('acctentry/datatable.html', context),
            'status': 'success',
            'branch': first_ofmain.branch_id,
            'vat': first_ofitem.vat_id,
            'atc': first_ofitem.atc_id,
            'inputvattype': first_ofitem.inputvattype_id,
            'deferredvat': first_ofitem.deferredvat
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Apmain
    template_name = 'accountspayable/report/index.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('description')
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('description')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['user'] = User.objects.filter(is_active=1).order_by('first_name')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        context['unit'] = Unit.objects.filter(isdeleted=0).order_by('code')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('code')
        context['outputvat'] = Outputvat.objects.filter(isdeleted=0).order_by('code')
        context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        creator = Apmain.objects.filter(isdeleted=0).values_list('enterby_id', flat=True)
        context['creator'] = User.objects.filter(id__in=set(creator)).order_by('first_name', 'last_name')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultHtmlView(ListView):
    model = Apmain
    template_name = 'accountspayable/reportresulthtml.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['rfv'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "ACCOUNTS PAYABLE"
        context['rc_title'] = "ACCOUNTS PAYABLE"

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Apmain
    template_name = 'accountspayable/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['rfv'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['datefrom'] = self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name)
        context['dateto'] = self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "ACCOUNTS PAYABLE"
        context['rc_title'] = "ACCOUNTS PAYABLE"

        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_xls = ''
    report_total = ''
    rfv = 'hide'

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's' \
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd' \
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' \
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':

        if request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name):
            subtype = str(request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name))
        else:
            subtype = ''

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's'\
                or (request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd'
                    and (subtype == '' or subtype == '2')):
            if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
                report_type = "Accounts Payable Detailed"
                report_xls = "AP Detailed"
            else:
                report_type = "Accounts Payable Summary"
                report_xls = "AP Summary"

            query = Apmain.objects.all().filter(isdeleted=0)

            if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
                query = query.filter(apnum__gte=int(key_data))
            if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
                query = query.filter(apnum__lte=int(key_data))

            if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
                query = query.filter(apdate__gte=key_data)
            if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
                query = query.filter(apdate__lte=key_data)

            if request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    query = query.filter(aptype__in=key_data)
            if request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name))
                query = query.filter(apsubtype=int(key_data))
            if request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name))
                query = query.filter(apstatus=str(key_data))
            if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
                query = query.filter(status=str(key_data))

            if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
                query = query.filter(branch=int(key_data))
            if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
                query = query.filter(Q(payeecode__icontains=key_data) | Q(payeename__icontains=key_data))
            # if request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name):
            #     key_data = str(request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name))
            #     query = query.filter(Q(checknum__icontains=key_data))
            if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
                query = query.filter(Q(refno__icontains=key_data))
            if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
                query = query.filter(currency=int(key_data))

            if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
                query = query.filter(vat=int(key_data))
            if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
                query = query.filter(inputvattype=int(key_data))
            if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
                query = query.filter(atax=int(key_data))
            if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
                query = query.filter(deferred=str(key_data))
            if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
                query = query.filter(bankbranchdisburse=int(key_data))
            if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(amount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
                query = query.filter(amount__lte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    query = query.order_by(*key_data)

            report_total = query.aggregate(Sum('amount'))\

        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            report_type = "Accounts Payable Detailed"
            report_xls = "AP Detailed"
            rfv = "show"

            query = Reprfvmain.objects.all().filter(isdeleted=0).exclude(apmain__isnull=True)

            if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__apnum__gte=int(key_data))
            if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
                query = query.filter(apmain__apnum__lte=int(key_data))

            if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__apdate__gte=key_data)
            if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
                query = query.filter(apmain__apdate__lte=key_data)

            if request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    query = query.filter(apmain__aptype__in=key_data)
            if request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name))
                query = query.filter(apmain__apsubtype=int(key_data))
            if request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name))
                query = query.filter(apmain__apstatus=str(key_data))
            if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
                query = query.filter(apmain__status=str(key_data))

            if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
                query = query.filter(apmain__branch=int(key_data))
            if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
                query = query.filter(Q(apmain__payeecode__icontains=key_data) | Q(apmain__payeename__icontains=key_data))
            # if request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name):
            #     key_data = str(request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name))
            #     query = query.filter(Q(apmain__checknum__icontains=key_data))
            if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
                query = query.filter(Q(apmain__refno__icontains=key_data))
            if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
                query = query.filter(apmain__currency=int(key_data))

            if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
                query = query.filter(apmain__vat=int(key_data))
            if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
                query = query.filter(apmain__inputvattype=int(key_data))
            if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
                query = query.filter(apmain__atax=int(key_data))
            if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
                query = query.filter(apmain__deferred=str(key_data))
            if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
                query = query.filter(apmain__bankbranchdisburse=int(key_data))

            if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__amount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
                query = query.filter(apmain__amount__lte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    for n,data in enumerate(key_data):
                        key_data[n] = "apmain__" + data
                    query = query.order_by(*key_data)
                else:
                    query = query.order_by('apmain')

            report_total = query.values('apmain').annotate(Sum('amount')).aggregate(Sum('apmain__amount'))

        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
            if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
                report_type = "Accounts Payable Unbalanced Entries"
                report_xls = "AP Unbalanced Entries"
            else:
                report_type = "Accounts Payable All Entries"
                report_xls = "AP All Entries"

            query = Apdetail.objects.filter(isdeleted=0, apmain__isdeleted=0)

            if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__apnum__gte=int(key_data))
            if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
                query = query.filter(apmain__apnum__lte=int(key_data))

            if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__apdate__gte=key_data)
            if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
                query = query.filter(apmain__apdate__lte=key_data)

            if request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    query = query.filter(apmain__aptype__in=key_data)
            if request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name))
                query = query.filter(apmain__apsubtype=int(key_data))
            if request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name))
                query = query.filter(apmain__apstatus=str(key_data))
            if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
                query = query.filter(apmain__status=str(key_data))

            if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
                query = query.filter(apmain__branch=int(key_data))
            if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
                query = query.filter(Q(apmain__payeecode__icontains=key_data) | Q(apmain__payeename__icontains=key_data))
            if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
                query = query.filter(Q(apmain__refno__icontains=key_data))
            if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
                query = query.filter(apmain__currency=int(key_data))

            if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
                query = query.filter(apmain__vat=int(key_data))
            if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
                query = query.filter(apmain__inputvattype=int(key_data))
            if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
                query = query.filter(apmain__atax=int(key_data))
            if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
                query = query.filter(apmain__deferred=str(key_data))
            if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
                query = query.filter(apmain__bankbranchdisburse=int(key_data))
            if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__amount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
                query = query.filter(apmain__amount__lte=float(key_data.replace(',', '')))

            query = query.values('apmain__apnum') \
                .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),
                          creditsum=Sum('creditamount')) \
                .values('apmain__apnum', 'margin', 'apmain__apdate', 'debitsum', 'creditsum', 'apmain__pk', 'apmain__aptype__code', 'apmain__apsubtype__code', 'apmain__payeename', 'apmain__bankbranchdisburse__branch', 'apmain__apstatus').order_by(
                'apmain__apnum')

            if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
                query = query.exclude(margin=0)

            if request.COOKIES.get('rep_f_uborder_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_uborder_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    query = query.order_by(*key_data)

            report_total = query.aggregate(Sum('debitsum'), Sum('creditsum'), Sum('margin'))

        if request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name))
            if key_data == 'd':
                query = query.reverse()

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        query = Apdetail.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name) != 'null':
            gl_request = request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name)

            query = query.filter(chartofaccount=int(gl_request))

            enable_check = Chartofaccount.objects.get(pk=gl_request)
            if enable_check.bankaccount_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name)
                query = query.filter(bankaccount=get_object_or_None(Bankaccount, pk=int(gl_item)))
            if enable_check.department_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name)
                query = query.filter(department=get_object_or_None(Department, pk=int(gl_item)))
            if enable_check.unit_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name)
                query = query.filter(unit=get_object_or_None(Unit, pk=int(gl_item)))
            if enable_check.branch_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name)
                query = query.filter(branch=get_object_or_None(Branch, pk=int(gl_item)))
            if enable_check.product_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name)
                query = query.filter(product=get_object_or_None(Product, pk=int(gl_item)))
            if enable_check.inputvat_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name)
                query = query.filter(inputvat=get_object_or_None(Inputvat, pk=int(gl_item)))
            if enable_check.outputvat_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name)
                query = query.filter(outputvat=get_object_or_None(Outputvat, pk=int(gl_item)))
            if enable_check.vat_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name)
                query = query.filter(vat=get_object_or_None(Vat, pk=int(gl_item)))
            if enable_check.wtax_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name)
                query = query.filter(wtax=get_object_or_None(Wtax, pk=int(gl_item)))
            if enable_check.ataxcode_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name)
                query = query.filter(ataxcode=get_object_or_None(Ataxcode, pk=int(gl_item)))
            if enable_check.employee_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name)
                query = query.filter(employee=get_object_or_None(Employee, pk=int(gl_item)))
            if enable_check.supplier_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name)
                query = query.filter(supplier=get_object_or_None(Supplier, pk=int(gl_item)))
            if enable_check.customer_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_customer_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_customer_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_customer_' + request.resolver_match.app_name)
                query = query.filter(customer=get_object_or_None(Customer, pk=int(gl_item)))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
            if request.COOKIES.get('rep_f_debit_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_debit_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(debitamount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_debit_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_debit_amountto_' + request.resolver_match.app_name))
                query = query.filter(debitamount__lte=float(key_data.replace(',', '')))

            if request.COOKIES.get('rep_f_credit_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_credit_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(creditamount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_credit_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_credit_amountto_' + request.resolver_match.app_name))
                query = query.filter(creditamount__lte=float(key_data.replace(',', '')))

        if request.COOKIES.get('rep_f_balancecode_' + request.resolver_match.app_name) == 'd':
            query = query.filter(balancecode='D')
        elif request.COOKIES.get('rep_f_balancecode_' + request.resolver_match.app_name) == 'c':
            query = query.filter(balancecode='C')

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(apmain__apnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(apmain__apnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(apmain__apdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(apmain__apdate__lte=key_data)

        if request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.filter(apmain__aptype__in=key_data)
        if request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name))
            query = query.filter(apmain__apsubtype=int(key_data))
        if request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name))
            query = query.filter(apmain__apstatus=str(key_data))
        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            query = query.filter(apmain__status=str(key_data))

        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(apmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
            query = query.filter(Q(apmain__payeecode__icontains=key_data) | Q(apmain__payeename__icontains=key_data))
        # if request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name))
        #     query = query.filter(Q(apmain__checknum__icontains=key_data))
        if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
            query = query.filter(Q(apmain__refno__icontains=key_data))
        if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
            query = query.filter(apmain__currency=int(key_data))

        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(apmain__vat=int(key_data))
        if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
            query = query.filter(apmain__inputvattype=int(key_data))
        if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
            query = query.filter(apmain__atax=int(key_data))
        if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
            query = query.filter(apmain__deferred=str(key_data))
        if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
            query = query.filter(apmain__bankbranchdisburse=int(key_data))

        if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(apmain__amount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
            query = query.filter(apmain__amount__lte=float(key_data.replace(',', '')))

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "Accounts Payable Accounting Entry - Summary"
            report_xls = "AP Acctg Entry - Summary"

            # query = query.values('chartofaccount__accountcode',
            #                      'chartofaccount__title',
            #                      'chartofaccount__description',
            #                      'bankaccount__code',
            #                      'bankaccount__accountnumber',
            #                      'bankaccount__bank__code',
            #                      'department__departmentname',
            #                      'employee__firstname',
            #                      'employee__lastname',
            #                      'supplier__name',
            #                      'customer__name',
            #                      'unit__description',
            #                      'branch__description',
            #                      'product__description',
            #                      'inputvat__description',
            #                      'outputvat__description',
            #                      'vat__description',
            #                      'wtax__description',
            #                      'ataxcode__code',
            #                      'balancecode') \
            #     .annotate(Sum('debitamount'), Sum('creditamount')) \
            #     .order_by('-balancecode',
            #               'chartofaccount__accountcode',
            #               'bankaccount__code',
            #               'bankaccount__accountnumber',
            #               'bankaccount__bank__code',
            #               'department__departmentname',
            #               'employee__firstname',
            #               'supplier__name',
            #               'customer__name',
            #               'unit__description',
            #               'branch__description',
            #               'product__description',
            #               'inputvat__description',
            #               'outputvat__description',
            #               '-vat__description',
            #               'wtax__description',
            #               'ataxcode__code')

            query = query.values('chartofaccount__accountcode',
                                 'chartofaccount__title',
                                 'chartofaccount__description',
                                 'bankaccount__code',
                                 'bankaccount__accountnumber',
                                 'bankaccount__bank__code',
                                 'department__code',
                                 'department__departmentname',
                                 'branch__description',
                                 'branch__code',
                                 'balancecode')\
                         .annotate(Sum('debitamount'), Sum('creditamount'))\
                         .order_by('-balancecode',
                                   'branch__code',
                                   'department__code',
                                   'bankaccount__code',
                                   'chartofaccount__accountcode')
        else:
            report_type = "Accounts Payable Accounting Entry - Detailed"
            report_xls = "AP Acctg Entry - Detailed"

            query = query.values('ap_num')\
                    .annotate(Sum('debitamount'), Sum('creditamount'))\
                    .values('apmain__payeename',
                            'apmain__apdate',
                            'ap_num',
                            'apmain__payee__tin',
                            'apmain__payee__address1',
                            'apmain__payee__address2',
                            'apmain__particulars',
                            'item_counter',
                            'chartofaccount__accountcode',
                            'chartofaccount__title',
                            'department__code',
                            'department__departmentname',
                            'debitamount__sum',
                            'creditamount__sum')\
                    .order_by('ap_num',
                              'item_counter')\

    return query, report_type, report_total, rfv, report_xls


@csrf_exempt
def reportresultxlsx(request):
    # imports and workbook config
    import xlsxwriter
    try:
        import cStringIO as StringIO
    except ImportError:
        import StringIO
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)

    # query and default variables
    queryset, report_type, report_total, rfv, report_xls = reportresultquery(request)
    report_type = report_type if report_type != '' else 'AP Report'
    worksheet = workbook.add_worksheet(report_xls)
    bold = workbook.add_format({'bold': 1})
    bold_right = workbook.add_format({'bold': 1, 'align': 'right'})
    bold_center = workbook.add_format({'bold': 1, 'align': 'center'})
    money_format = workbook.add_format({'num_format': '#,##0.00'})
    bold_money_format = workbook.add_format({'num_format': '#,##0.00', 'bold': 1})
    worksheet.set_column(1, 1, 15)
    row = 0
    data = []

    # config: placement
    amount_placement = 0
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        amount_placement = 6
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        amount_placement = 11 if rfv == 'show' else 9
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        amount_placement = 8
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 4
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        amount_placement = 7

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'AP Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Type', bold)
        worksheet.write('D1', 'Subtype', bold)
        worksheet.write('E1', 'Payee', bold)
        worksheet.write('F1', 'Status', bold)
        worksheet.write('G1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if rfv == 'show':
            worksheet.merge_range('A1:A2', 'AP Number', bold)
            worksheet.merge_range('B1:B2', 'Date', bold)
            worksheet.merge_range('C1:C2', 'Type', bold)
            worksheet.merge_range('D1:D2', 'Subtype', bold)
            worksheet.merge_range('E1:E2', 'Payee', bold)
            worksheet.merge_range('F1:F2', 'VAT', bold)
            worksheet.merge_range('G1:G2', 'ATC', bold)
            worksheet.merge_range('H1:H2', 'In/VAT', bold)
            worksheet.merge_range('I1:I2', 'Status', bold)
            worksheet.merge_range('J1:L1', 'Replenished RFV', bold_center)
            worksheet.merge_range('M1:M2', 'Amount', bold_right)
            worksheet.write('J2', 'Rep RFV Number', bold)
            worksheet.write('K2', 'Date', bold)
            worksheet.write('L2', 'Rep RFV Amount', bold_right)
            row += 1
        else:
            worksheet.write('A1', 'AP Number', bold)
            worksheet.write('B1', 'Date', bold)
            worksheet.write('C1', 'Type', bold)
            worksheet.write('D1', 'Subtype', bold)
            worksheet.write('E1', 'Payee', bold)
            worksheet.write('F1', 'VAT', bold)
            worksheet.write('G1', 'ATC', bold)
            worksheet.write('H1', 'In/VAT', bold)
            worksheet.write('I1', 'Status', bold)
            worksheet.write('J1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        worksheet.write('A1', 'AP Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'APV Type', bold)
        worksheet.write('D1', 'APV Subtype ', bold)
        worksheet.write('E1', 'Payee', bold)
        worksheet.write('F1', 'Disbursing Branch', bold)
        worksheet.write('G1', 'APV Status', bold)
        worksheet.write('H1', 'Debit', bold_right)
        worksheet.write('I1', 'Credit', bold_right)
        worksheet.write('J1', 'Margin', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        worksheet.merge_range('A1:B1', 'General Ledger', bold_center)
        worksheet.write('A2', 'Acct. Code', bold)
        worksheet.write('B2', 'Account Title', bold)
        worksheet.merge_range('C1:D1', 'Subsidiary Ledger', bold_center)
        worksheet.write('C2', 'Code', bold)
        worksheet.write('D2', 'Particulars', bold)
        worksheet.merge_range('E1:F1', 'Amount', bold_center)
        worksheet.write('E2', 'Debit', bold_right)
        worksheet.write('F2', 'Credit', bold_right)
        row += 1
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        worksheet.merge_range('A1:C1', 'Accounts Payable', bold_center)
        worksheet.merge_range('D1:D2', 'Account Number', bold_center)
        worksheet.merge_range('E1:E2', 'Account Title', bold_center)
        worksheet.merge_range('F1:F2', 'Dept. Code', bold_center)
        worksheet.merge_range('G1:G2', 'Dept. Name', bold_center)
        worksheet.merge_range('H1:H2', 'Debit', bold_right)
        worksheet.merge_range('I1:I2', 'Credit', bold_right)
        worksheet.write('A2', 'Date', bold)
        worksheet.write('B2', 'Number / Payee', bold)
        worksheet.write('C2', 'Particulars', bold)
        row += 1

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            data = [
                obj.apnum,
                DateFormat(obj.apdate).format('Y-m-d'),
                obj.aptype.description if obj.aptype else '',
                obj.apsubtype.description if obj.apsubtype else '',
                obj.payee.name,
                obj.get_apstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            if rfv == 'show':
                data = [
                    obj.apmain.apnum,
                    DateFormat(obj.apmain.apdate).format('Y-m-d'),
                    obj.apmain.aptype.description if obj.apmain.aptype else '',
                    obj.apmain.apsubtype.description if obj.apmain.apsubtype else '',
                    obj.apmain.payee.name,
                    obj.apmain.vat.code if obj.apmain.vat else '',
                    obj.apmain.atax.code if obj.apmain.atax else '',
                    obj.apmain.inputvattype.description if obj.apmain.inputvattype else '',
                    obj.apmain.get_apstatus_display(),
                    'RFV-' + obj.reprfvnum,
                    DateFormat(obj.reprfvdate).format('Y-m-d'),
                    obj.amount,
                    obj.apmain.amount,
                ]
            else:
                data = [
                    obj.apnum,
                    DateFormat(obj.apdate).format('Y-m-d'),
                    obj.aptype.description if obj.aptype else '',
                    obj.apsubtype.description if obj.apsubtype else '',
                    obj.payee.name,
                    obj.vat.code if obj.vat else '',
                    obj.atax.code if obj.atax else '',
                    obj.inputvattype.description if obj.inputvattype else '',
                    obj.get_apstatus_display(),
                    obj.amount,
                ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
            data = [
                obj['apmain__apnum'],
                DateFormat(obj['apmain__apdate']).format('Y-m-d'),
                obj['apmain__aptype__code'],
                obj['apmain__apsubtype__code'],
                obj['apmain__payeename'],
                obj['apmain__bankbranchdisburse__branch'],
                obj['apmain__apstatus'],
                obj['debitsum'],
                obj['creditsum'],
                obj['margin'],
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            # str_firstname = obj['employee__firstname'] if obj['employee__firstname'] is not None else ''
            # str_lastname = obj['employee__lastname'] if obj['employee__lastname'] is not None else ''

            bankaccount__code = obj['bankaccount__code'] if obj['bankaccount__code'] is not None else ''
            department__code = obj['department__code'] if obj['department__code'] is not None else ''
            branch__code = obj['branch__code'] if obj['branch__code'] is not None else ''
            bankaccount__accountnumber = obj['bankaccount__accountnumber'] if obj['bankaccount__accountnumber'] is not None else ''
            department__departmentname = obj['department__departmentname'] if obj['department__departmentname'] is not None else ''

            data = [
                obj['chartofaccount__accountcode'],
                obj['chartofaccount__description'],
                bankaccount__code + ' ' + department__code + ' ' + branch__code,
                bankaccount__accountnumber + ' ' + department__departmentname,
                obj['debitamount__sum'],
                obj['creditamount__sum'],
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
            if obj['item_counter'] == 1:
                data = [
                    DateFormat(obj['apmain__apdate']).format('Y-m-d'),
                    obj['ap_num'] + ' ' + obj['apmain__payeename'],
                    obj['apmain__particulars'],
                    obj['chartofaccount__accountcode'],
                    obj['chartofaccount__title'],
                    obj['department__code'],
                    obj['department__departmentname'],
                    obj['debitamount__sum'],
                    obj['creditamount__sum'],
                ]
            elif obj['item_counter'] == 2:
                data = [
                    ' ',
                    'TIN: ' + obj['apmain__payee__tin'],
                    ' ',
                    obj['chartofaccount__accountcode'],
                    obj['chartofaccount__title'],
                    obj['department__code'],
                    obj['department__departmentname'],
                    obj['debitamount__sum'],
                    obj['creditamount__sum'],
                ]
            elif obj['item_counter'] == 3:
                data = [
                    ' ',
                    obj['apmain__payee__address1'],
                    ' ',
                    obj['chartofaccount__accountcode'],
                    obj['chartofaccount__title'],
                    obj['department__code'],
                    obj['department__departmentname'],
                    obj['debitamount__sum'],
                    obj['creditamount__sum'],
                ]
            elif obj['item_counter'] == 4:
                data = [
                    ' ',
                    obj['apmain__payee__address2'],
                    ' ',
                    obj['chartofaccount__accountcode'],
                    obj['chartofaccount__title'],
                    obj['department__code'],
                    obj['department__departmentname'],
                    obj['debitamount__sum'],
                    obj['creditamount__sum'],
                ]
            elif obj['item_counter'] > 4:
                data = [
                    ' ',
                    ' ',
                    ' ',
                    obj['chartofaccount__accountcode'],
                    obj['chartofaccount__title'],
                    obj['department__code'],
                    obj['department__departmentname'],
                    obj['debitamount__sum'],
                    obj['creditamount__sum'],
                ]

        temp_amount_placement = amount_placement
        for col_num in xrange(len(data)):
            if col_num == temp_amount_placement:
                temp_amount_placement += 1
                worksheet.write_number(row, col_num, data[col_num], money_format)
            else:
                worksheet.write(row, col_num, data[col_num])

    # config: totals
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        data = [
            "", "", "", "", "",
            "Total", report_total['amount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if rfv == 'show':
            data = [
                "", "", "", "", "", "", "", "", "",
                "Total", report_total['apmain__amount__sum'],
            ]
        else:
            data = [
                "", "", "", "", "", "", "", "",
                "Total", report_total['amount__sum'],
            ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        data = [
            "", "", "", "", "", "",
            "Total", report_total['debitsum__sum'], report_total['creditsum__sum'], report_total['margin__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        # data = [
        #     "", "", "", "", "", "", "", "", "", "", "", "", "",
        #     "Total", report_total['debitamount__sum'], report_total['creditamount__sum'],
        # ]
        data = [
            "", "", "",
            "Total", report_total['debitamount__sum'], report_total['creditamount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        data = [
            "", "", "", "", "", "",
            "Grand Total", report_total['debitamount__sum'], report_total['creditamount__sum'],
        ]

    row += 1
    for col_num in xrange(len(data)):
        worksheet.write(row, col_num, data[col_num], bold_money_format)

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+report_xls+".xlsx"
    return response


@csrf_exempt
def generatedefaultentries(request):
    if request.method == 'POST':
        data_table = validatetable(request.POST['table'])

        debit_entries = Apdetailtemp.objects.filter(secretkey=request.POST['secretkey'], balancecode='D',
                                                    debitamount__gt=0.00).order_by('item_counter')
        accountcode = Chartofaccount.objects.filter(pk=debit_entries.first().chartofaccount).first().accountcode
        firstfourdigits = str(accountcode)[0:4]
        advances = False
        if debit_entries.exclude(chartofaccount=Companyparameter.objects.get(code='PDI').coa_inputvat_id).count() == 1 \
                and firstfourdigits == '1141':
            advances = True

        # debit_entries.filter(isautogenerated=1).delete()
        taxable_amount = 0.00
        aptrade_amount = 0.00
        vat_amount = 0.00
        wtax_amount = 0.00

        if debit_entries:
            Apdetailtemp.objects.filter(secretkey=request.POST['secretkey'], balancecode='C',
                                        creditamount__gt=0.00).exclude(apdetail=None).update(isdeleted=2)
            Apdetailtemp.objects.filter(secretkey=request.POST['secretkey'], balancecode='D',
                                        debitamount__gt=0.00, chartofaccount=Companyparameter.objects.get(code='PDI').
                                        coa_inputvat_id).exclude(apdetail=None).update(isdeleted=2)
            Apdetailtemp.objects.filter(secretkey=request.POST['secretkey'], balancecode='C', apdetail=None,
                                        creditamount__gt=0.00).delete()
            Apdetailtemp.objects.filter(secretkey=request.POST['secretkey'], balancecode='D', apdetail=None,
                                        debitamount__gt=0.00, chartofaccount=Companyparameter.objects.get(code='PDI').
                                        coa_inputvat_id).delete()

            itemcounter = debit_entries.last().item_counter + 1
            ap_totals = debit_entries.aggregate(Sum('debitamount'))
            taxable_amount = ap_totals['debitamount__sum']
            aptrade_amount = ap_totals['debitamount__sum']
            vat_amount = float(taxable_amount) * (float(Vat.objects.get(pk=int(request.POST['vat'])).rate) / 100)

            # input VAT accounting entry
            if Vat.objects.filter(pk=int(request.POST['vat'])).first().rate > 0 and not advances:
                inputvatentry = Apdetailtemp()
                inputvatentry.item_counter = itemcounter
                inputvatentry.secretkey = request.POST['secretkey']
                inputvatentry.ap_num = ''
                inputvatentry.ap_date = datetime.date.today()
                inputvatentry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat_id
                inputvatentry.supplier = int(request.POST['supplier'])
                inputvatentry.inputvat = Inputvat.objects.filter(inputvattype=Inputvattype.objects.
                                                                 get(pk=int(request.POST['inputvattype']))).first().id
                inputvatentry.vat = int(request.POST['vat'])
                inputvatentry.debitamount = vat_amount
                inputvatentry.balancecode = 'D'
                inputvatentry.enterby = request.user
                inputvatentry.modifyby = request.user
                inputvatentry.isautogenerated = 1
                inputvatentry.save()
                itemcounter += 1
                aptrade_amount += Decimal.from_float(inputvatentry.debitamount)

            # expanded withholding tax accounting entry
            if request.POST['atc'] and Ataxcode.objects.filter(pk=int(request.POST['atc'])).first().rate > 0 and not \
                    advances:
                ewtaxentry = Apdetailtemp()
                ewtaxentry.item_counter = itemcounter
                ewtaxentry.secretkey = request.POST['secretkey']
                ewtaxentry.ap_num = ''
                ewtaxentry.ap_date = datetime.date.today()
                ewtaxentry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_ewtax_id
                print ewtaxentry.chartofaccount
                ewtaxentry.ataxcode = int(request.POST['atc'])
                wtax_amount = float(taxable_amount) * (float(Ataxcode.objects.get(pk=int(request.POST['atc']))
                                                             .rate) / 100)
                ewtaxentry.creditamount = wtax_amount
                ewtaxentry.balancecode = 'C'
                ewtaxentry.enterby = request.user
                ewtaxentry.modifyby = request.user
                ewtaxentry.isautogenerated = 1
                ewtaxentry.save()
                itemcounter += 1
                aptrade_amount -= Decimal.from_float(ewtaxentry.creditamount)

            # AP trade amount
            aptradeentry = Apdetailtemp()
            aptradeentry.item_counter = itemcounter
            aptradeentry.secretkey = request.POST['secretkey']
            aptradeentry.ap_num = ''
            aptradeentry.ap_date = datetime.date.today()
            aptradeentry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_aptrade_id
            aptradeentry.supplier = int(request.POST['supplier'])
            aptradeentry.creditamount = aptrade_amount
            aptradeentry.balancecode = 'C'
            aptradeentry.enterby = request.user
            aptradeentry.modifyby = request.user
            aptradeentry.isautogenerated = 1
            aptradeentry.save()

            vatablesale = 0.00
            vatexemptsale = 0.00
            vatzeroratedsale = 0.00

            if Vat.objects.get(pk=int(request.POST['vat'])).rate > 0:
                vatablesale = taxable_amount
            elif Vat.objects.get(pk=int(request.POST['vat'])).code == 'VE':
                vatexemptsale = taxable_amount
            elif Vat.objects.get(pk=int(request.POST['vat'])).code == 'ZE' or Vat.objects.get(pk=int(request.POST['vat'])).code == 'VATNA':
                vatzeroratedsale = taxable_amount

            context = {
                'tabledetailtemp': data_table['str_detailtemp'],
                'tablebreakdowntemp': data_table['str_detailbreakdowntemp'],
                'datatemp': querystmtdetail(data_table['str_detailtemp'], request.POST['secretkey']),
                'datatemptotal': querytotaldetail(data_table['str_detailtemp'], request.POST['secretkey']),
            }

            data = {
                'datatable': render_to_string('acctentry/datatable.html', context),
                'vatablesale': str(format(vatablesale, '.2f')),
                'vatexemptsale': str(format(vatexemptsale, '.2f')),
                'vatzeroratedsale': str(format(vatzeroratedsale, '.2f')),
                'totalsale': str(format(taxable_amount, '.2f')),
                'addvat': str(format(vat_amount, '.2f')),
                'totalpayment': str(format(aptrade_amount, '.2f')),
                'wtaxamount': str(format(wtax_amount, '.2f')),
                'status': 'success'
            }
        else:
            data = {
                'status': 'error',
            }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        context = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        aptype = request.GET['aptype']
        apsubtype = request.GET['apsubtype']
        payee = request.GET['payee']
        branch = request.GET['branch']
        approver = request.GET['approver']
        apstatus = request.GET['apstatus']
        status = request.GET['status']
        atc = request.GET['atc']
        inputvattype = request.GET['inputvattype']
        vat = request.GET['vat']
        bankaccount = request.GET['bankaccount']
        creator = request.GET['creator']
        title = "Accounts Payable Voucher List"
        list = Apmain.objects.filter(isdeleted=0).order_by('apnum')[:0]

        if report == '1':
            title = "Accounts Payable Voucher Transaction List - Summary"
            q = Apmain.objects.filter(isdeleted=0).order_by('apnum', 'apdate')
            if dfrom != '':
                q = q.filter(apdate__gte=dfrom)
            if dto != '':
                q = q.filter(apdate__lte=dto)
        elif report == '2':
            title = "Accounts Payable Voucher Transaction List"
            q = Apdetail.objects.select_related('apmain').filter(isdeleted=0).order_by('ap_num', 'ap_date', 'item_counter')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
        elif report == '3':
            title = "Unposted Accounts Payable Voucher Transaction List - Summary"
            q = Apmain.objects.filter(isdeleted=0,status__in=['A','C']).order_by('apnum', 'apdate')
            if dfrom != '':
                q = q.filter(apdate__gte=dfrom)
            if dto != '':
                q = q.filter(apdate__lte=dto)
        elif report == '4':
            title = "Unposted Accounts Payable Voucher   Transaction List"
            q = Apdetail.objects.select_related('apmain').filter(isdeleted=0,status__in=['A','C']).order_by('ap_num', 'ap_date', 'item_counter')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
        elif report == '5':
            title = "Accounts Payable Listing Subject to W/TAX"
            query = query_wtax(dfrom, dto)
            q = Apmain.objects.filter(isdeleted=0, status__in=['A', 'C']).order_by('apnum', 'apdate')
        elif report == '6':
            title = "Accounts Payable Voucher Transaction Listing Subject To Input VAT"
            aplist = getAPList(dfrom, dto)
            efo = getEFO()
            query = query_apsubjecttovat(dfrom, dto, aplist, efo)

            q = Apmain.objects.filter(isdeleted=0, status__in=['A', 'C']).order_by('apnum', 'apdate')
        elif report == '7':
            title = "Accounts Payable Voucher Transaction Listing Subject To Input VAT Summary"
            aplist = getAPList(dfrom, dto)
            efo = getEFO()
            query = query_apsubjecttovatsummary(dfrom, dto, aplist, efo)

            q = Apmain.objects.filter(isdeleted=0, status__in=['A', 'C']).order_by('apnum', 'apdate')
        elif report == '8':
            title = "Accounts Payable Voucher Transaction List - AP Trade"
            q = Apdetail.objects.select_related('apmain').filter(isdeleted=0,chartofaccount_id=285).order_by('ap_num', 'ap_date', 'item_counter')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)

        if aptype != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__aptype__exact=aptype)
            else:
                q = q.filter(aptype=aptype)
        if apsubtype != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__apsubtype__exact=apsubtype)
            else:
                q = q.filter(apsubtype=apsubtype)
        if payee != 'null':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__payeecode__exact=payee)
            else:
                q = q.filter(payeecode=payee)
        if branch != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__branch__exact=branch)
            else:
                q = q.filter(branch=branch)
        if approver != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__designatedapprover__exact=approver)
            else:
                q = q.filter(designatedapprover=approver)
        if apstatus != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__apstatus__exact=apstatus)
            else:
                q = q.filter(apstatus=apstatus)
        if status != '':
            q = q.filter(status=status)
        if atc != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(cvmain__atc__exact=atc)
            else:
                q = q.filter(atc=atc)
        if inputvattype != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(cvmain__inputvattype__exact=inputvattype)
            else:
                q = q.filter(inputvattype=inputvattype)
        if vat != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(cvmain__vat__exact=vat)
            else:
                q = q.filter(vat=vat)
        if bankaccount != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(cvmain__bankaccount__exact=bankaccount)
            else:
                q = q.filter(bankaccount=bankaccount)
        if creator != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__enterby_id=creator)
            else:
                q = q.filter(enterby_id=creator)

        if report == '5':
            list = query
            credit = 0
            debit = 0
            if list:
                df = pd.DataFrame(query)
                credit = df['creditamount'].sum()
                debit = df['debitamount'].sum()
        elif report == '6' or report == '7':
            list = query
            inputcredit = 0
            inputdebit = 0
            efocredit = 0
            efodebit = 0
            if list:
                df = pd.DataFrame(query)
                inputcredit = df['inputvatcreditamount'].sum()
                inputdebit = df['inputvatdebitamount'].sum()
                efocredit = df['efocreditamount'].sum()
                efodebit = df['efodebitamount'].sum()
        else:
            list = q

        if list:
            if report == '2' or report == '4' or report == '8':
                total = list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))
            elif report == '5':
                total = {'credit': credit, 'debit': debit }
            elif report == '6' or report == '7':
                total = {'inputcredit': inputcredit, 'inputdebit': inputdebit, 'efocredit': efocredit, 'efodebit':efodebit}
            else:
                total = list.aggregate(total_amount=Sum('amount'))

        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "datefrom": datetime.datetime.strptime(dfrom, '%Y-%m-%d'),
            "dateto": datetime.datetime.strptime(dto, '%Y-%m-%d'),
            "username": request.user,
        }
        if report == '1':
            return Render.render('accountspayable/report/report_1.html', context)
        elif report == '2':
            return Render.render('accountspayable/report/report_2.html', context)
        elif report == '3':
            return Render.render('accountspayable/report/report_3.html', context)
        elif report == '4':
            return Render.render('accountspayable/report/report_4.html', context)
        elif report == '5':
            return Render.render('accountspayable/report/report_5.html', context)
        elif report == '6':
            return Render.render('accountspayable/report/report_6.html', context)
        elif report == '7':
            return Render.render('accountspayable/report/report_7.html', context)
        elif report == '8':
            return Render.render('accountspayable/report/report_8.html', context)
        else:
            return Render.render('accountspayable/report/report_1.html', context)


@method_decorator(login_required, name='dispatch')
class GenerateExcel(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        context = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        aptype = request.GET['aptype']
        apsubtype = request.GET['apsubtype']
        payee = request.GET['payee']
        branch = request.GET['branch']
        approver = request.GET['approver']
        apstatus = request.GET['apstatus']
        status = request.GET['status']
        atc = request.GET['atc']
        inputvattype = request.GET['inputvattype']
        vat = request.GET['vat']
        bankaccount = request.GET['bankaccount']
        creator = request.GET['creator']
        title = "Accounts Payable Voucher List"
        list = Apmain.objects.filter(isdeleted=0).order_by('apnum')[:0]

        if report == '1':
            title = "Accounts Payable Voucher Transaction List - Summary"
            q = Apmain.objects.filter(isdeleted=0).order_by('apnum', 'apdate')
            if dfrom != '':
                q = q.filter(apdate__gte=dfrom)
            if dto != '':
                q = q.filter(apdate__lte=dto)
        elif report == '2':
            title = "Accounts Payable Voucher Transaction List"
            q = Apdetail.objects.select_related('apmain').filter(isdeleted=0).order_by('ap_num', 'ap_date',
                                                                                       'item_counter')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
        elif report == '3':
            title = "Unposted Accounts Payable Voucher Transaction List - Summary"
            q = Apmain.objects.filter(isdeleted=0, status__in=['A', 'C']).order_by('apnum', 'apdate')
            if dfrom != '':
                q = q.filter(apdate__gte=dfrom)
            if dto != '':
                q = q.filter(apdate__lte=dto)
        elif report == '4':
            title = "Unposted Accounts Payable Voucher   Transaction List"
            q = Apdetail.objects.select_related('apmain').filter(isdeleted=0, status__in=['A', 'C']).order_by('ap_num',
                                                                                                              'ap_date',
                                                                                                              'item_counter')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
        elif report == '5':
            title = "Accounts Payable Listing Subject to W/TAX"
            query = query_wtax(dfrom, dto)
            q = Apmain.objects.filter(isdeleted=0, status__in=['A', 'C']).order_by('apnum', 'apdate')
        elif report == '6':
            title = "Accounts Payable Voucher Transaction Listing Subject To Input VAT"
            aplist = getAPList(dfrom, dto)
            efo = getEFO()
            query = query_apsubjecttovat(dfrom, dto, aplist, efo)

            q = Apmain.objects.filter(isdeleted=0, status__in=['A', 'C']).order_by('apnum', 'apdate')
        elif report == '7':
            title = "Accounts Payable Voucher Transaction Listing Subject To Input VAT Summary"
            aplist = getAPList(dfrom, dto)
            efo = getEFO()
            query = query_apsubjecttovatsummary(dfrom, dto, aplist, efo)

            q = Apmain.objects.filter(isdeleted=0, status__in=['A', 'C']).order_by('apnum', 'apdate')
        elif report == '8':
            title = "Accounts Payable Voucher Transaction List - AP Trade"
            q = Apdetail.objects.select_related('apmain').filter(isdeleted=0,chartofaccount_id=285).order_by('ap_num', 'ap_date', 'item_counter')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)

        if aptype != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__aptype__exact=aptype)
            else:
                q = q.filter(aptype=aptype)
        if apsubtype != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__apsubtype__exact=apsubtype)
            else:
                q = q.filter(apsubtype=apsubtype)
        if payee != 'null':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__payeecode__exact=payee)
            else:
                q = q.filter(payeecode=payee)
        if branch != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__branch__exact=branch)
            else:
                q = q.filter(branch=branch)
        if approver != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__designatedapprover__exact=approver)
            else:
                q = q.filter(designatedapprover=approver)
        if apstatus != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__apstatus__exact=apstatus)
            else:
                q = q.filter(apstatus=apstatus)
        if status != '':
            q = q.filter(status=status)
        if atc != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(cvmain__atc__exact=atc)
            else:
                q = q.filter(atc=atc)
        if inputvattype != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(cvmain__inputvattype__exact=inputvattype)
            else:
                q = q.filter(inputvattype=inputvattype)
        if vat != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(cvmain__vat__exact=vat)
            else:
                q = q.filter(vat=vat)
        if bankaccount != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(cvmain__bankaccount__exact=bankaccount)
            else:
                q = q.filter(bankaccount=bankaccount)
        if creator != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(apmain__enterby_id=creator)
            else:
                q = q.filter(enterby_id=creator)

        if report == '5':
            list = query
            credit = 0
            debit = 0
            if list:
                df = pd.DataFrame(query)
                credit = df['creditamount'].sum()
                debit = df['debitamount'].sum()
        elif report == '6' or report == '7':
            list = query
            credit = 0
            debit = 0
            if list:
                df = pd.DataFrame(query)
                inputcredit = df['inputvatcreditamount'].sum()
                inputdebit = df['inputvatdebitamount'].sum()
                efocredit = df['efocreditamount'].sum()
                efodebit = df['efodebitamount'].sum()
        else:
            list = q

        if list:

            if report == '2' or report == '4' or report == '8':
                total = list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))
            elif report == '5':
                total = [] #{'credit': credit, 'debit': debit}
            elif report == '6' or report == '7':
                total = [] #{'inputcredit': inputcredit, 'inputdebit': inputdebit, 'efocredit': efocredit, 'efodebit':efodebit}
            else:
                total = list.aggregate(total_amount=Sum('amount'))

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', str(title), bold)
        worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)

        filename = "apreport.xlsx"

        if report == '1':
            # header
            worksheet.write('A4', 'AP Number', bold)
            worksheet.write('B4', 'AP Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0
            totalamount = 0
            amount = 0
            for data in list:
                worksheet.write(row, col, data.apnum)
                worksheet.write(row, col + 1, data.apdate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payeename)
                worksheet.write(row, col + 3, data.particulars)
                if data.status == 'C':
                    worksheet.write(row, col + 4, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 4, float(format(data.amount, '.2f')))
                    amount = data.amount

                row += 1
                totalamount += amount

            #print float(format(totalamount, '.2f'))
            #print total['total_amount']
            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totalamount, '.2f')))

            filename = "aptransactionlistsummary.xlsx"

        elif report == '2':
            worksheet.write('A4', 'AP Number', bold)
            worksheet.write('B4', 'AP Date', bold)
            worksheet.write('C4', 'Particular', bold)
            worksheet.write('D4', 'Account Title', bold)
            worksheet.write('E4', 'Subs Ledger', bold)
            worksheet.write('F4', 'Debit', bold)
            worksheet.write('G4', 'Credit', bold)

            row = 4
            col = 0

            totaldebit = 0
            totalcredit = 0
            list = list.values('apmain__apnum', 'apmain__apdate', 'apmain__particulars', 'apmain__payeename',
                               'chartofaccount__accountcode', 'chartofaccount__description', 'status', 'debitamount',
                               'creditamount', 'branch__code', 'bankaccount__code', 'department__code')
            dataset = pd.DataFrame.from_records(list)

            for apnum, detail in dataset.fillna('NaN').groupby(
                    ['apmain__apnum', 'apmain__apdate', 'apmain__payeename', 'apmain__particulars', 'status']):
                worksheet.write(row, col, apnum[0])
                worksheet.write(row, col + 1, apnum[1], formatdate)
                if apnum[4] == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, apnum[2])
                worksheet.write(row, col + 3, apnum[3])
                row += 1
                debit = 0
                credit = 0
                branch = ''
                bankaccount = ''
                department = ''
                for sub, data in detail.iterrows():
                    worksheet.write(row, col + 2, data['chartofaccount__accountcode'])
                    worksheet.write(row, col + 3, data['chartofaccount__description'])
                    if data['branch__code'] != 'NaN':
                        branch = data['branch__code']
                    if data['bankaccount__code'] != 'NaN':
                        bankaccount = data['bankaccount__code']
                    if data['department__code'] != 'NaN':
                        department = data['department__code']
                    worksheet.write(row, col + 4, branch + ' ' + bankaccount + ' ' + department)
                    if apnum[4] == 'C':
                        worksheet.write(row, col + 5, float(format(0, '.2f')))
                        worksheet.write(row, col + 6, float(format(0, '.2f')))
                        debit = 0
                        credit = 0
                    else:
                        worksheet.write(row, col + 5, float(format(data['debitamount'], '.2f')))
                        worksheet.write(row, col + 6, float(format(data['creditamount'], '.2f')))
                        debit = data['debitamount']
                        credit = data['creditamount']

                    row += 1
                    totaldebit += debit
                    totalcredit += credit

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(totaldebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalcredit, '.2f')))

            filename = "aptransactionlist.xlsx"

        elif report == '3':
            # header
            worksheet.write('A4', 'AP Number', bold)
            worksheet.write('B4', 'AP Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0

            totalamount = 0
            amount = 0
            for data in list:
                worksheet.write(row, col, data.apnum)
                worksheet.write(row, col + 1, data.apdate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payeename)
                worksheet.write(row, col + 3, data.particulars)

                if data.status == 'C':
                    worksheet.write(row, col + 4, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 4, float(format(data.amount, '.2f')))
                    amount = data.amount

                row += 1
                totalamount += amount

            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totalamount, '.2f')))

            filename = "unpostedaptransactionlistsummary.xlsx"

        elif report == '4':
            # header
            worksheet.write('A4', 'AP Number', bold)
            worksheet.write('B4', 'AP Date', bold)
            worksheet.write('C4', 'Particular', bold)
            worksheet.write('D4', 'Account Title', bold)
            worksheet.write('E4', 'Subs Ledger', bold)
            worksheet.write('F4', 'Debit', bold)
            worksheet.write('G4', 'Credit', bold)

            row = 4
            col = 0

            totaldebit = 0
            totalcredit = 0
            list = list.values('apmain__apnum', 'apmain__apdate', 'apmain__particulars', 'apmain__payeename',
                               'chartofaccount__accountcode', 'chartofaccount__description', 'status', 'debitamount',
                               'creditamount', 'branch__code', 'bankaccount__code', 'department__code')
            dataset = pd.DataFrame.from_records(list)

            for apnum, detail in dataset.fillna('NaN').groupby(
                    ['apmain__apnum', 'apmain__apdate', 'apmain__payeename', 'apmain__particulars', 'status']):
                worksheet.write(row, col, apnum[0])
                worksheet.write(row, col + 1, apnum[1], formatdate)
                if apnum[4] == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, apnum[2])
                worksheet.write(row, col + 3, apnum[3])
                row += 1
                debit = 0
                credit = 0
                branch = ''
                bankaccount = ''
                department = ''
                for sub, data in detail.iterrows():
                    worksheet.write(row, col + 2, data['chartofaccount__accountcode'])
                    worksheet.write(row, col + 3, data['chartofaccount__description'])
                    if data['branch__code'] != 'NaN':
                        branch = data['branch__code']
                    if data['bankaccount__code'] != 'NaN':
                        bankaccount = data['bankaccount__code']
                    if data['department__code'] != 'NaN':
                        department = data['department__code']
                    worksheet.write(row, col + 4, branch + ' ' + bankaccount + ' ' + department)
                    if apnum[4] == 'C':
                        worksheet.write(row, col + 5, float(format(0, '.2f')))
                        worksheet.write(row, col + 6, float(format(0, '.2f')))
                        debit = 0
                        credit = 0
                    else:
                        worksheet.write(row, col + 5, float(format(data['debitamount'], '.2f')))
                        worksheet.write(row, col + 6, float(format(data['creditamount'], '.2f')))
                        debit = data['debitamount']
                        credit = data['creditamount']

                    row += 1
                    totaldebit += debit
                    totalcredit += credit

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(totaldebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalcredit, '.2f')))


            filename = "unpostedaptransactionlist.xlsx"

        elif report == '5':
            # header
            worksheet.write('A4', 'AP Number', bold)
            worksheet.write('B4', 'Code', bold)
            worksheet.write('C4', 'Payee/Particular', bold)
            worksheet.write('D4', 'Subs Ledger', bold)
            worksheet.write('E4', 'Debit', bold)
            worksheet.write('F4', 'Credit', bold)

            row = 4
            col = 0

            totaldebit = 0
            totalcredit = 0

            dataset = pd.DataFrame(list)

            for apnum, detail in dataset.fillna('NaN').groupby(['apnum', 'payeecode', 'payeename', 'particulars', 'status']):
                worksheet.write(row, col, apnum[0])
                worksheet.write(row, col + 1, apnum[1], formatdate)
                if apnum[4] == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, apnum[2])
                worksheet.write(row, col + 3, apnum[3])
                row += 1
                debit = 0
                credit = 0
                branch = ''
                bankaccount = ''
                department = ''
                for sub, data in detail.iterrows():
                    worksheet.write(row, col + 1, data['accountcode'])
                    worksheet.write(row, col + 2, data['description'])

                    if data['deptcode'] != 'NaN':
                        department = data['deptcode']
                    worksheet.write(row, col + 3, department)
                    if apnum[4] == 'C':
                        worksheet.write(row, col + 4, float(format(0, '.2f')))
                        worksheet.write(row, col + 5, float(format(0, '.2f')))
                        debit = 0
                        credit = 0
                    else:
                        worksheet.write(row, col + 4, float(format(data['debitamount'], '.2f')))
                        worksheet.write(row, col + 5, float(format(data['creditamount'], '.2f')))
                        debit = data['debitamount']
                        credit = data['creditamount']

                    row += 1
                    totaldebit += debit
                    totalcredit += credit

            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totaldebit, '.2f')))
            worksheet.write(row, col + 5, float(format(totalcredit, '.2f')))


            filename = "aptransactionsubjecttowtax.xlsx"
        elif report == '6':
            # header
            worksheet.write('A4', 'AP Number', bold)
            worksheet.write('B4', 'AP Date', bold)
            worksheet.write('C4', 'Payee/Particular', bold)
            worksheet.write('D4', 'Type', bold)
            worksheet.write('E4', 'E F O Debit', bold)
            worksheet.write('F4', 'E F O Credit', bold)
            worksheet.write('G4', 'Input VAT Debit', bold)
            worksheet.write('H4', 'Input VAT Credit', bold)
            worksheet.write('I4', 'VAT Rate', bold)

            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0


            for data in list:
                worksheet.write(row, col, data.apnum)
                worksheet.write(row, col + 1, data.apdate, formatdate)
                worksheet.write(row, col + 2, data.payeename)
                worksheet.write(row, col + 3, data.inputvat)
                worksheet.write(row, col + 4, float(format(data.efodebitamount, '.2f')))
                worksheet.write(row, col + 5, float(format(data.efocreditamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.inputvatdebitamount, '.2f')))
                worksheet.write(row, col + 7, float(format(data.inputvatcreditamount, '.2f')))
                worksheet.write(row, col + 8, data.inputvatrate)

                totalefodebit += data.efodebitamount
                totalefocredit += data.efocreditamount
                totalinputdebit += data.inputvatdebitamount
                totalinputcredit += data.inputvatcreditamount

                row += 1

            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 5, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalinputdebit, '.2f')))
            worksheet.write(row, col + 7, float(format(totalinputcredit, '.2f')))


            filename = "aptransactionsubjecttoinputvat.xlsx"
        elif report == '7':
            # header
            worksheet.write('A4', 'Payee/Particular', bold)
            worksheet.write('B4', 'Type', bold)
            worksheet.write('C4', 'E F O Debit', bold)
            worksheet.write('D4', 'E F O Credit', bold)
            worksheet.write('E4', 'Input VAT Debit', bold)
            worksheet.write('F4', 'Input VAT Credit', bold)
            worksheet.write('G4', 'VAT Rate', bold)
            worksheet.write('H4', 'Address', bold)
            worksheet.write('I4', 'TIN', bold)


            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0


            for data in list:
                worksheet.write(row, col, data.payeename)
                worksheet.write(row, col + 1, data.inputvat)
                worksheet.write(row, col + 2, float(format(data.efodebitamount, '.2f')))
                worksheet.write(row, col + 3, float(format(data.efocreditamount, '.2f')))
                worksheet.write(row, col + 4, float(format(data.inputvatdebitamount, '.2f')))
                worksheet.write(row, col + 5, float(format(data.inputvatcreditamount, '.2f')))
                worksheet.write(row, col + 6, data.inputvatrate)
                worksheet.write(row, col + 7, data.address)
                worksheet.write(row, col + 8, data.tin)

                totalefodebit += data.efodebitamount
                totalefocredit += data.efocreditamount
                totalinputdebit += data.inputvatdebitamount
                totalinputcredit += data.inputvatcreditamount

                row += 1

            worksheet.write(row, col + 1, 'Total')
            worksheet.write(row, col + 2, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 3, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 4, float(format(totalinputdebit, '.2f')))
            worksheet.write(row, col + 5, float(format(totalinputcredit, '.2f')))


            filename = "aptransactionsubjecttoinputvatsummary.xlsx"
        if report == '8':
            # header
            worksheet.write('A4', 'AP Number', bold)
            worksheet.write('B4', 'AP Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Net Amount', bold)

            row = 5
            col = 0
            totalamount = 0
            amount = 0
            for data in list:
                worksheet.write(row, col, data.apmain.apnum)
                worksheet.write(row, col + 1, data.apmain.apdate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.apmain.payeename)
                worksheet.write(row, col + 3, data.apmain.particulars)
                if data.status == 'C':
                    worksheet.write(row, col + 4, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 4, float(format(data.creditamount, '.2f')))
                    amount = data.creditamount

                row += 1
                totalamount += amount

            # print float(format(totalamount, '.2f'))
            # print total['total_amount']
            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totalamount, '.2f')))

            filename = "aptransactionlistaptradesummary.xlsx"

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response

@csrf_exempt
def searchforposting(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Apmain.objects.filter(isdeleted=0,status='A',apstatus='A').order_by('apnum', 'apdate')
        if dfrom != '':
            q = q.filter(apdate__gte=dfrom)
        if dto != '':
            q = q.filter(apdate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('accountspayable/postingresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

def getAPList(dfrom, dto):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    inputvat = 274 # 1940000000 INPUT VAT

    query = "SELECT m.apnum, m.apdate, m.payeename, m.particulars, " \
            "d.balancecode, d.chartofaccount_id, d.apmain_id " \
            "FROM apmain AS m " \
            "LEFT OUTER JOIN apdetail AS d ON d.apmain_id = m.id " \
            "WHERE DATE(m.apdate) >= '"+str(dfrom)+"' AND DATE(m.apdate) <= '"+str(dto)+"' " \
            "AND m.apstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND d.chartofaccount_id = "+str(inputvat)+" " \
            "ORDER BY m.apnum;"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    list = ''
    for r in result:
        list += str(r.apmain_id) + ','

    return list[:-1]


def getEFO():
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()


    query = "SELECT id, accountcode, description, main, clas, item, SUBSTR(sub, 1, 2) AS sub " \
            "FROM chartofaccount " \
            "WHERE (main = 5) OR (main = 1 AND clas = 5 AND SUBSTR(sub, 1, 2) = 10) " \
            "OR (main = 1 AND clas = 7 AND SUBSTR(sub, 1, 2) = 10) " \
            "OR (main = 1 AND clas = 1 AND item = 9) " \
            "OR (main = 1 AND clas = 1 AND item = 8) " \
            "OR (main = 1 AND clas = 6)"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    list = ''
    for r in result:
        list += str(r.id) + ','

    return list[:-1]

def query_apsubjecttovatsummary(dfrom, dto, aplist, efo):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    aptrade = 274

    if not aplist:
        aplist = '0'

    query = "SELECT z.*, CONCAT(IFNULL(sup.address1, ''), ' ', IFNULL(sup.address2, '')) AS address, sup.tin " \
            "FROM ( " \
            "SELECT m.apnum, m.apdate, m.payeecode, m.payeename, m.particulars, inv.code AS inputvat,  " \
            "SUM(IFNULL(efo.debitamount, 0)) AS efodebitamount, SUM(IFNULL(efo.creditamount, 0)) AS efocreditamount, " \
            "SUM(IFNULL(inputvat.debitamount, 0)) AS inputvatdebitamount, SUM(IFNULL(inputvat.creditamount, 0)) AS inputvatcreditamount, " \
            "ROUND((SUM(IFNULL(inputvat.debitamount, 0)) - SUM(IFNULL(inputvat.creditamount, 0))) / (SUM(IFNULL(efo.debitamount, 0)) - SUM(IFNULL(efo.creditamount, 0))) * 100) AS inputvatrate " \
            "FROM apmain AS m " \
            "LEFT OUTER JOIN inputvattype AS invt ON invt.id = m.inputvattype_id " \
            "LEFT OUTER JOIN inputvat AS inv ON inv.inputvattype_id = invt.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.apmain_id, d.ap_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM apdetail AS d " \
            "WHERE d.apmain_id IN ("+aplist+") " \
            "AND d.chartofaccount_id IN ("+efo+") " \
            "GROUP BY d.apmain_id " \
            "ORDER BY d.ap_num, d.ap_date " \
            ") AS efo ON efo.apmain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.apmain_id, d.ap_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM apdetail AS d " \
            "WHERE d.apmain_id IN ("+aplist+") " \
            "AND d.chartofaccount_id = '"+str(aptrade)+"' " \
            "GROUP BY d.apmain_id " \
            "ORDER BY d.ap_num, d.ap_date " \
            ") AS inputvat ON inputvat.apmain_id = m.id " \
            "WHERE DATE(m.apdate) >= '"+str(dfrom)+"' AND DATE(m.apdate) <= '"+str(dto)+"' " \
            "AND m.apstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+aplist+") " \
            "GROUP BY m.payeecode, inv.code " \
            "ORDER BY m.payeename) AS z " \
            "LEFT OUTER JOIN supplier AS sup ON sup.code = z.payeecode;"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_apsubjecttovat(dfrom, dto, aplist, efo):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    aptrade = 274

    if not aplist:
        aplist = '0'

    query = "SELECT m.apnum, m.apdate, m.payeename, m.particulars, inv.code AS inputvat, " \
            "IFNULL(efo.debitamount, 0) AS efodebitamount, IFNULL(efo.creditamount, 0) AS efocreditamount, " \
            "IFNULL(inputvat.debitamount, 0) AS inputvatdebitamount, IFNULL(inputvat.creditamount, 0) AS inputvatcreditamount, " \
            "ROUND((IFNULL(inputvat.debitamount, 0) - IFNULL(inputvat.creditamount, 0)) / (IFNULL(efo.debitamount, 0) - IFNULL(efo.creditamount, 0)) * 100) AS inputvatrate " \
            "FROM apmain AS m " \
            "LEFT OUTER JOIN inputvattype AS invt ON invt.id = m.inputvattype_id " \
            "LEFT OUTER JOIN inputvat AS inv ON inv.inputvattype_id = invt.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.apmain_id, d.ap_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM apdetail AS d " \
            "WHERE d.apmain_id IN ("+aplist+") " \
            "AND d.chartofaccount_id IN ("+efo+") " \
            "GROUP BY d.apmain_id " \
            "ORDER BY d.ap_num, d.ap_date " \
            ") AS efo ON efo.apmain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.apmain_id, d.ap_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM apdetail AS d " \
            "WHERE d.apmain_id IN ("+aplist+") " \
            "AND d.chartofaccount_id = '"+str(aptrade)+"' " \
            "GROUP BY d.apmain_id " \
            "ORDER BY d.ap_num, d.ap_date " \
            ") AS inputvat ON inputvat.apmain_id = m.id " \
            "WHERE DATE(m.apdate) >= '"+str(dfrom)+"' AND DATE(m.apdate) <= '"+str(dto)+"' " \
            "AND m.apstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+aplist+") " \
            "ORDER BY m.apnum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_wtax(dfrom, dto):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    wtax = Chartofaccount.objects.filter(isdeleted=0, is_wtax=1)
    string = ''
    for w in wtax:
        string += str(w.id)+','

    #print string[:-1]

    query = "SELECT m.apnum, m.apdate, m.payeecode, m.payeename, m.particulars, " \
            "d.chartofaccount_id, d.balancecode, d.debitamount, d.creditamount, " \
            "c.accountcode, c.description, dept.code AS deptcode, m.status " \
            "FROM apmain AS m " \
            "LEFT OUTER JOIN apdetail AS d ON d.apmain_id = m.id " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = d.chartofaccount_id " \
            "LEFT OUTER JOIN department AS dept ON dept.id = d.department_id " \
            "WHERE DATE(m.apdate) >= '"+str(dfrom)+"' AND DATE(m.apdate) <= '"+str(dto)+"' " \
            "AND m.status != 'C' " \
            "AND m.id IN (SELECT DISTINCT apmain_id FROM apdetail WHERE chartofaccount_id IN ("+string[:-1]+")) " \
            "ORDER BY m.apdate, m.apnum, d.balancecode DESC"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

@csrf_exempt
def digibanker(request):
    print 'digibanker'
    #MC 01 1218181 PHP 0111007943003 20181218 0000100361172 00193

    #text_file = open("accountspayable/txtfile/digibanker.txt", "w")
    text_file = open("static/digibanker/digibanker.txt", "w")

    bnum = request.POST['batchnumber']
    pdate = request.POST['postingdate']

    batchnum = bnum
    currency = 'PHP'
    fundacct = '0111007943003'
    postingdate = pdate
    totalamount = 0
    totalno = 0

    ids = request.POST.getlist('ids[]')
    print ids

    aptype = 13 # SB
    disburbank = '0601' # DELA ROSA

    #detail = Apmain.objects.filter(pk__in=ids).filter(aptype_id=aptype,isdeleted=0,status='A',apstatus='R').order_by('apnum', 'apdate')

    #q = Apmain.objects.filter(aptype_id=aptype, isdeleted=0, status='A', apstatus='R').values_list('id',flat=True).order_by('apnum', 'apdate')

    aptrade = 285  # ACCOUNTS PAYABLE-TRADE

    detail = Apdetail.objects.filter(apmain_id__in=ids, chartofaccount_id=aptrade).order_by('ap_num', 'ap_date')

    detaildata = ""
    for item in detail:
        transamount = str(item.creditamount).replace('.', '').rjust(13, '0')[:13]
        payeename = item.apmain.payeename.ljust(40, ' ')[:40]
        particulars = 'AP'+str(item.apmain.apnum)+'::'+str(item.apmain.payeecode)+'::'+str(item.apmain.payeename)+'::'+str(item.apmain.refno)+'::'+str(item.apmain.particulars)
        #particulars = particulars.rstrip('\r\n').ljust(2400, ' ')[:2400]
        particulars = ' '.join(particulars.splitlines())
        totalamount += item.creditamount
        totalno += 1
        detaildata += "MC10"+str(currency)+str(disburbank)+str(transamount)+str(payeename)+str(particulars)+"\n"

    header = "MC01" + str(batchnum) + str(currency) + str(fundacct) + str(postingdate) + str(totalamount).replace('.', '').rjust(13, '0')[:13] + str(totalno).rjust(5, '0')[:5] + "\n"
    text_file.writelines(header)
    text_file.writelines(detaildata)

    text_file.close()

    print 'url'
    baseurl = request.build_absolute_uri()
    print baseurl
    fileurl = baseurl.replace("accountspayable", "static")+'digibanker.txt'
    print fileurl

    data = {'status': 'success', 'fileurl': fileurl}

    return JsonResponse(data)
    # file_name = 'digibanker'
    #
    # response = HttpResponse(
    #     text_file,
    #     content_type='application/octet-stream'
    # )
    # response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    #
    # return response

    # file_name = 'digibanker'+str(datetime.datetime.now())
    # path_to_file = 'accountspayable/txtfile/digibanker'
    # response = HttpResponse(mimetype='application/force-download')
    # response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)
    # response['X-Sendfile'] = smart_str(path_to_file)
    # return response

    #return Render.render('accountspayable/report/report_1.html')


@csrf_exempt
def searchfordigibanker(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']
        creator = request.POST['creator']

        aptype = 13

        #xx = Apmain.objects.filter(aptype_id=aptype,isdeleted=0,status='A',apstatus='R').order_by('apnum', 'apdate')
        q = Apmain.objects.filter(aptype_id=aptype,isdeleted=0,apstatus='R').values_list('id', flat=True).order_by('apnum', 'apdate')

        if dfrom != '':
            q = q.filter(apdate__gte=dfrom)
        if dto != '':
            q = q.filter(apdate__lte=dto)

        if creator != '':
            q = q.filter(enterby_id=creator)


        aptrade = 285 #ACCOUNTS PAYABLE-TRADE

        list = Apdetail.objects.filter(apmain_id__in=set(q), chartofaccount_id=aptrade).order_by('ap_num', 'ap_date')

        total = list.aggregate(Sum('creditamount'))

        print total

        context = {
            'data': list,
            'total': total,
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('accountspayable/digibankerposting.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

def upload(request):
    folder = 'media/apupload/'
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        id = request.POST['dataid']
        fs = FileSystemStorage(location=folder)  # defaults to   MEDIA_ROOT
        filename = fs.save(myfile.name, myfile)

        upl = Apupload(apmain_id=id, filename=filename, enterby=request.user, modifyby=request.user)
        upl.save()

        uploaded_file_url = fs.url(filename)
        return HttpResponseRedirect('/accountspayable/' + str(id) )
    return HttpResponseRedirect('/accountspayable/' + str(id) )


class LedgerView(ListView):
    model = Apmain
    template_name = 'accountspayable/ledger/index.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)


        return context

def query_ledger(report, type, dfrom, dto, apnontrade, payee):

    if dfrom <= '2018-12-31':
        dfrom = '2019-01-01'
    # print "Summary"

    ''' Create query '''
    cursor = connection.cursor()

    if report == 'detail':
        query = "SELECT z.payee_id, z.tran, z.trannum, z.trandate, " \
                "(IFNULL(z.debitamount, 0)) AS debitamount, (IFNULL(z.creditamount, 0)) AS creditamount, ((IFNULL(z.debitamount, 0)) + (IFNULL(z.creditamount, 0))) AS amount, z.balancecode, z.particulars " \
                "FROM ( " \
                "SELECT s.document_supplier_id AS payee_id, s.document_type AS tran, s.document_num AS trannum, s.document_date AS trandate,  " \
                "(IFNULL(s.amount, 0)) AS debitamount, 0 AS creditamount, s.balancecode, s.particulars       " \
                "FROM subledger AS s " \
                "WHERE s.chartofaccount_id = '"+str(apnontrade)+"' AND s.document_date >= '"+str(dfrom)+"' AND s.document_date <= '"+str(dto)+"' AND s.document_supplier_id = '"+str(payee)+"' " \
                "AND s.document_supplier_id IS NOT NULL " \
                "AND s.balancecode = 'C' " \
                "UNION " \
                "SELECT ss.document_supplier_id AS payee_id, ss.document_type AS tran, ss.document_num AS trannum, ss.document_date AS trandate, " \
                "0 AS debitamount, (IFNULL(ss.amount, 0)) AS creditamount, ss.balancecode, ss.particulars       " \
                "FROM subledger AS ss " \
                "WHERE ss.chartofaccount_id = '"+str(apnontrade)+"' AND ss.document_date >= '"+str(dfrom)+"' AND ss.document_date <= '"+str(dto)+"' AND ss.document_supplier_id = '"+str(payee)+"' " \
                "AND ss.document_supplier_id IS NOT NULL " \
                "AND ss.balancecode = 'D' " \
                ") AS z " \
                "ORDER BY z.trandate, z.tran"
        # query = "SELECT z.* " \
        #         "FROM ( " \
        #         "   SELECT 'AP' AS tran, d.ap_num AS trannum, d.ap_date AS trandate, IFNULL(d.debitamount, 0) AS debitamount, IFNULL(d.creditamount, 0) AS creditamount, (d.debitamount + d.creditamount) AS amount, d.balancecode, m.particulars " \
        #         "   FROM apdetail AS d " \
        #         "   LEFT OUTER JOIN apmain AS m ON m.id = d.apmain_id " \
        #         "   WHERE d.chartofaccount_id = '"+str(apnontrade)+"' AND m.payee_id = '"+str(payee)+"' AND d.supplier_id = '"+str(payee)+"' " \
        #         "   AND d.ap_date >= '"+str(dfrom)+"' AND d.ap_date <= '"+str(dto)+"' " \
        #         "   UNION " \
        #         "   SELECT 'CV' AS tran, d.cv_num, d.cv_date, IFNULL(d.debitamount, 0) AS debitamount, IFNULL(d.creditamount, 0) AS creditamount, (d.debitamount + d.creditamount) AS amount, d.balancecode, m.particulars " \
        #         "   FROM cvdetail AS d " \
        #         "   LEFT OUTER JOIN cvmain AS m ON m.id = d.cvmain_id " \
        #         "   WHERE d.chartofaccount_id = '"+str(apnontrade)+"' AND m.payee_id = '"+str(payee)+"' AND d.supplier_id = '"+str(payee)+"' " \
        #         "   AND d.cv_date >= '"+str(dfrom)+"' AND d.cv_date <= '"+str(dto)+"' " \
        #         "   UNION " \
        #         "   SELECT 'JV' AS tran, d.jv_num, d.jv_date, IFNULL(d.debitamount, 0) AS debitamount, IFNULL(d.creditamount, 0) AS creditamount, (d.debitamount + d.creditamount) AS amount, d.balancecode, m.particular " \
        #         "   FROM jvdetail AS d " \
        #         "   LEFT OUTER JOIN jvmain AS m ON m.id = d.jvmain_id " \
        #         "   WHERE d.chartofaccount_id = '"+str(apnontrade)+"' AND d.supplier_id = '"+str(payee)+"' " \
        #         "   AND d.jv_date >= '"+str(dfrom)+"' AND d.jv_date <= '"+str(dto)+"' " \
        #         ") AS z ORDER BY z.trandate, z.tran"
    else:
        con_ap = ""
        con_cv = ""
        con_jv = ""
        con_beg = ""
        if payee != 'all':
            con_ap = "AND m.payee_id = '" + str(payee) + "' AND d.supplier_id = '" + str(payee) + "'"
            con_cv = " AND m.payee_id = '" + str(payee) + "' AND d.supplier_id = '" + str(payee) + "'"
            con_jv = "AND d.supplier_id = '" + str(payee) + "' "
            con_beg = " AND d.code_id = '" + str(payee) + "' "

        query = "SELECT s.code, s.name, z.payee_id, z.tran, z.trannum, z.trandate, SUM(z.debitamount) AS debitamount, SUM(z.creditamount) AS creditamount, (SUM(z.debitamount) - SUM(z.creditamount)) AS balance, IF(SUM(z.debitamount) > SUM(z.creditamount), 'D', 'C') AS balancecode " \
                "FROM ( " \
                "   SELECT m.payee_id, 'AP' AS tran, d.ap_num AS trannum, d.ap_date AS trandate, SUM(IFNULL(d.debitamount, 0)) AS debitamount, SUM(IFNULL(d.creditamount, 0)) AS creditamount, d.balancecode " \
                "   FROM apdetail AS d " \
                "   LEFT OUTER JOIN apmain AS m ON m.id = d.apmain_id " \
                "   WHERE d.chartofaccount_id = '" + str(apnontrade) + "'" + str(con_ap) + " " \
                "   AND d.ap_date >= '" + str(dfrom) + "' AND d.ap_date <= '" + str(dto) + "' " \
                "   GROUP BY d.supplier_id" \
                "   UNION " \
                "   SELECT m.payee_id, 'CV' AS tran, d.cv_num, d.cv_date, SUM(IFNULL(d.debitamount, 0)) AS debitamount, SUM(IFNULL(d.creditamount, 0)) AS creditamount, d.balancecode " \
                "   FROM cvdetail AS d " \
                "   LEFT OUTER JOIN cvmain AS m ON m.id = d.cvmain_id " \
                "   WHERE d.chartofaccount_id = '" + str(apnontrade) + "'" + str(con_cv) + " " \
                "   AND d.cv_date >= '" + str(dfrom) + "' AND d.cv_date <= '" + str(dto) + "' " \
                "   GROUP BY d.supplier_id" \
                "   UNION " \
                "   SELECT d.supplier_id, 'JV' AS tran, d.jv_num, d.jv_date, SUM(IFNULL(d.debitamount, 0)) AS debitamount, SUM(IFNULL(d.creditamount, 0)) AS creditamount, d.balancecode " \
                "   FROM jvdetail AS d " \
                "   LEFT OUTER JOIN jvmain AS m ON m.id = d.jvmain_id " \
                "   WHERE d.chartofaccount_id = '" + str(apnontrade) + "'" + str(con_jv) + " " \
                "   AND d.jv_date >= '" + str(dfrom) + "' AND d.jv_date <= '" + str(dto) + "' " \
                "   GROUP BY d.supplier_id	UNION SELECT d.code_id, 'BEG' AS tran, '' AS trannum, d.beg_date, SUM(IF (d.beg_code = 'D', d.beg_amt, 0)) AS debitamount, SUM(IF (d.beg_code = 'C', d.beg_amt, 0)) AS creditamount, d.beg_code " \
                "   FROM beginningbalance AS d " \
                "   WHERE d.accountcode = '2111100000'" + str(con_beg) + " " \
                "   GROUP BY d.code_id	" \
                ") AS z LEFT OUTER JOIN supplier AS s ON s.id = z.payee_id WHERE z.payee_id IS NOT NULL GROUP BY z.payee_id ORDER BY s.name, s.code"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_begbalance(account, payee):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    con = ""
    if payee != 'all':
        con = "AND code_id = '" + str(payee) + "'"

    query = "SELECT * FROM beginningbalance WHERE accountcode = '"+str(account)+"' "+str(con)+""

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


@method_decorator(login_required, name='dispatch')
class GenerateLedgerPDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        context = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        type = request.GET['type']
        payee = request.GET['payee']

        title = "Accounts Payable Ledger"
        list = Apmain.objects.filter(isdeleted=0).order_by('apnum')[:0]

        supplier = 'ALL'

        begcode = 'C'
        begamount = 0
        runbalance = 0

        if report == '1':
            sup = Supplier.objects.filter(code=payee).first()
            supplier = str(sup.code)+' - '+str(sup.name)
            apnontrade = Chartofaccount.objects.filter(id=company.coa_aptrade_id).first()

            begbalance = query_begbalance(apnontrade.accountcode, sup.id)
            apcode = apnontrade.balancecode

            if (begbalance):
                begcode = begbalance[0].beg_code
                begamount = begbalance[0].beg_amt

            if (apcode != begcode):
                begamount = begamount * -1

            addbeg = []
            if dfrom > '2018-12-31':
                addbeg = query_ledger('detail', type, '2019-01-01', dfrom, apnontrade.id, sup.id)

                if addbeg:
                    dfx = pd.DataFrame(addbeg)
                    runbalancex = begamount
                    amountx = 0
                    for index, row in dfx.iterrows():
                        if row.balancecode != apcode:
                            amountx = row.amount * -1
                        else:
                            amountx = row.amount
                        runbalancex += amountx

                    begamount = runbalancex
                    if begamount < 0:
                        begcode = 'C'

            q = query_ledger('detail', type, dfrom, dto, apnontrade.id, sup.id)
            new_list = []
            if q:
                df = pd.DataFrame(q)
                runbalance = begamount
                amount = 0
                for index, row in df.iterrows():
                    if row.balancecode != apcode:
                        amount = row.amount * -1
                    else:
                        amount = row.amount

                    runbalance += amount

                    new_list.append({'tran': row.tran, 'trannum': row.trannum, 'trandate': row.trandate,
                         'debitamount': row.debitamount, 'creditamount': row.creditamount, 'balamount': runbalance, 'particular': row.particulars })

                list = new_list

        elif report == '2':
            apnontrade = Chartofaccount.objects.filter(id=company.coa_aptrade_id).first()
            apcode = apnontrade.balancecode
            if type == '1':
                sup = Supplier.objects.filter(code=payee).first()
                supplier = str(sup.code) + ' - ' + str(sup.name)
                q = query_ledger('summary', type, dfrom, dto, apnontrade.id, sup.id)
                #begbalance = query_begbalance(apnontrade.accountcode, sup.id)
            else:
                q = query_ledger('summary', type, dfrom, dto, apnontrade.id, 'all')
                #begbalance = query_begbalance(apnontrade.accountcode, 'all')

            new_list = []
            if q:
                df = pd.DataFrame(q)
                for index, row in df.iterrows():

                    if row['balancecode'] != apcode:
                        amount = row['balance'] * -1
                    else:
                        amount = abs(row['balance'])

                   # print str(row['code'])+' | '+str(amount)

                    new_list.append({'code': row['code'], 'name': row['name'], 'balance': amount,
                                    'balancecode': row['balancecode'],})

                list = new_list

        else:
            list = []

        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "datefrom": datetime.datetime.strptime(dfrom, '%Y-%m-%d'),
            "dateto": datetime.datetime.strptime(dto, '%Y-%m-%d'),
            "username": request.user,
            'begamount': begamount,
            'endamount': runbalance,
            'supplier': supplier,
        }
        if report == '1':
            return Render.render('accountspayable/ledger/report_1.html', context)
        elif report == '2':
            return Render.render('accountspayable/ledger/report_2.html', context)
        else:
            return Render.render('accountspayable/ledger/report_1.html', context)

@method_decorator(login_required, name='dispatch')
class GenerateExcelLedger(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        context = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        type = request.GET['type']
        payee = request.GET['payee']

        title = "Accounts Payable Ledger"
        list = Apmain.objects.filter(isdeleted=0).order_by('apnum')[:0]

        supplier = 'ALL'

        begcode = 'C'
        begamount = 0
        runbalance = 0

        if report == '1':
            if type == '1':
                title = "Accounts Payable Ledger - Per Supplier"
            else:
                title = "Accounts Payable Ledger - All Summary"
            sup = Supplier.objects.filter(code=payee).first()
            supplier = str(sup.code)+' - '+str(sup.name)
            apnontrade = Chartofaccount.objects.filter(id=company.coa_aptrade_id).first()

            begbalance = query_begbalance(apnontrade.accountcode, sup.id)
            apcode = apnontrade.balancecode

            if (begbalance):
                begcode = begbalance[0].beg_code
                begamount = begbalance[0].beg_amt

            if (apcode != begcode):
                begamount = begamount * -1

            addbeg = []
            if dfrom > '2018-12-31':
                addbeg = query_ledger('detail', type, '2019-01-01', dfrom, apnontrade.id, sup.id)

                if addbeg:
                    dfx = pd.DataFrame(addbeg)
                    runbalancex = begamount
                    amountx = 0
                    for index, row in dfx.iterrows():
                        if row.balancecode != apcode:
                            amountx = row.amount * -1
                        else:
                            amountx = row.amount
                        runbalancex += amountx

                    begamount = runbalancex
                    if begamount < 0:
                        begcode = 'C'

            q = query_ledger('detail', type, dfrom, dto, apnontrade.id, sup.id)
            new_list = []
            if q:
                df = pd.DataFrame(q)
                runbalance = begamount
                amount = 0
                for index, row in df.iterrows():
                    if row.balancecode != apcode:
                        amount = row.amount * -1
                    else:
                        amount = row.amount

                    runbalance += amount

                    new_list.append({'tran': row.tran, 'trannum': row.trannum, 'trandate': row.trandate,
                         'debitamount': row.debitamount, 'creditamount': row.creditamount, 'balamount': runbalance, 'particular': row.particulars })

                list = new_list

        elif report == '2':
            if type == '1':
                title = "Accounts Payable Ledger - Summary - Per Supplier"
            else:
                title = "Accounts Payable Ledger - Summary - All Summary"
            apnontrade = Chartofaccount.objects.filter(id=company.coa_aptrade_id).first()
            apcode = apnontrade.balancecode
            if type == '1':
                sup = Supplier.objects.filter(code=payee).first()
                supplier = str(sup.code) + ' - ' + str(sup.name)
                q = query_ledger('summary', type, dfrom, dto, apnontrade.id, sup.id)
                #begbalance = query_begbalance(apnontrade.accountcode, sup.id)
            else:
                q = query_ledger('summary', type, dfrom, dto, apnontrade.id, 'all')
                #begbalance = query_begbalance(apnontrade.accountcode, 'all')

            new_list = []
            if q:
                df = pd.DataFrame(q)
                for index, row in df.iterrows():

                    if row['balancecode'] != apcode:
                        amount = row['balance'] * -1
                    else:
                        amount = abs(row['balance'])

                   # print str(row['code'])+' | '+str(amount)

                    new_list.append({'code': row['code'], 'name': row['name'], 'balance': amount,
                                    'balancecode': row['balancecode'],})

                list = new_list

        else:
            list = []

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', str(title), bold)
        worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)
        if report == '1':
            worksheet.write('A3', str(supplier), bold)

        filename = "accountspayableledger.xlsx"

        if report == '1':
            # header
            worksheet.write('A5', 'Date', bold)
            worksheet.write('B5', 'Ref', bold)
            worksheet.write('C5', 'Number', bold)
            worksheet.write('D5', 'Particulars', bold)
            worksheet.write('E5', 'Debit', bold)
            worksheet.write('F5', 'Credit', bold)
            worksheet.write('G5', 'Balance', bold)

            row = 5
            col = 0

            worksheet.write(row, col + 5, 'beginning balance')
            worksheet.write(row, col + 6, float(format(begamount, '.2f')))
            row += 1

            for data in list:
                worksheet.write(row, col, data['trandate'], formatdate)
                worksheet.write(row, col + 1, data['tran'])
                worksheet.write(row, col + 2, data['trannum'])
                worksheet.write(row, col + 3, data['particular'])
                worksheet.write(row, col + 4, float(format(data['debitamount'], '.2f')))
                worksheet.write(row, col + 5, float(format(data['creditamount'], '.2f')))
                worksheet.write(row, col + 6, float(format(data['balamount'], '.2f')))
                row += 1

            worksheet.write(row, col + 5, 'ending balance')
            worksheet.write(row, col + 6, float(format(runbalance, '.2f')))

            filename = "accountspayableledger.xlsx"

        elif report == '2':
            worksheet.write('A4', '', bold)
            worksheet.write('B4', 'Supplier', bold)
            worksheet.write('C4', 'Balance', bold)

            row = 4
            col = 0

            for data in list:
                worksheet.write(row, col, data['code'])
                worksheet.write(row, col + 1, data['name'])
                worksheet.write(row, col + 2, float(format(data['balance'], '.2f')))
                row += 1

            filename = "accountspayableledgersummary.xlsx"


        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response