from django.views.generic import View, DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from adtype.models import Adtype
from ataxcode.models import Ataxcode
from bankbranchdisburse.models import Bankbranchdisburse
from branch.models import Branch
from circulationproduct.models import Circulationproduct
from companyparameter.models import Companyparameter
from module.models import Activitylogs
from cvsubtype.models import Cvsubtype
from operationalfund.models import Ofmain, Ofitem, Ofdetail
from replenish_pcv.models import Reppcvmain, Reppcvdetail
from supplier.models import Supplier
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from . models import Ormain, Ordetail, Ordetailtemp, Ordetailbreakdown, Ordetailbreakdowntemp, Orupload
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from bankaccount.models import Bankaccount
from currency.models import Currency
from customer.models import Customer
from ortype.models import Ortype
from orsubtype.models import Orsubtype
from outputvattype.models import Outputvattype
from paytype.models import Paytype
from processing_or.models import Logs_ormain, Logs_ordetail
from vat.models import Vat
from wtax.models import Wtax
from django.template.loader import render_to_string
from easy_pdf.views import PDFTemplateView
from dateutil.relativedelta import relativedelta
import datetime
from pprint import pprint
from django.utils.dateformat import DateFormat
from utils.mixins import ReportContentMixin
from collector.models import Collector
from agent.models import Agent
from product.models import Product
from department.models import Department
from unit.models import Unit
from inputvat.models import Inputvat
from outputvat.models import Outputvat
from ataxcode.models import Ataxcode
from employee.models import Employee
from chartofaccount.models import Chartofaccount
from annoying.functions import get_object_or_None
import decimal
import pandas as pd
from django.utils.dateformat import DateFormat
from financial.utils import Render
from financial.context_processors import namedtuplefetchall
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from datetime import timedelta
import io
import xlsxwriter
import datetime
from django.template.loader import render_to_string
from django.core.files.storage import FileSystemStorage


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Ormain
    template_name = 'officialreceipt/index.html'
    page_template = 'officialreceipt/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Ormain.objects.all().filter(isdeleted=0)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(ornum__icontains=keysearch) |
                                 Q(ordate__icontains=keysearch) |
                                 Q(payee_name__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        # data for lookup
        context['ortype'] = Ortype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['product'] = Product.objects.filter(isdeleted=0).order_by('code')
        context['pk'] = 0
        # data for lookup

        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Ormain
    template_name = 'officialreceipt/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['detail'] = Ordetail.objects.filter(isdeleted=0). \
            filter(ormain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Ordetail.objects.filter(isdeleted=0). \
            filter(ormain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Ordetail.objects.filter(isdeleted=0). \
            filter(ormain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        # data for lookup
        # context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        # context['cvsubtype'] = Cvsubtype.objects.filter(isdeleted=0).order_by('pk')
        # context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        # context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        # context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        # context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        # context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        # context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        # context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        # context['pk'] = self.object.pk
        # data for lookup

        context['uploadlist'] = Orupload.objects.filter(ormain_id=self.object.pk).order_by('enterdate')

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Ormain
    template_name = 'officialreceipt/create.html'
    fields = ['ordate', 'ortype', 'orsource', 'collector', 'branch', 'amount', 'amountinwords', 'vat',
              'wtax', 'outputvattype', 'deferredvat', 'circulationproduct', 'bankaccount', 'particulars', 'government',
              'remarks', 'prnum', 'prdate', 'ornum', 'adtype']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('officialreceipt.add_ormain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['agency'] = Customer.objects.filter(isdeleted=0).order_by('code')   # add filter customer type
        context['client'] = Customer.objects.filter(isdeleted=0).order_by('code')   # add filter customer type
        context['agent'] = Agent.objects.filter(isdeleted=0).order_by('code')
        context['adtype'] = Adtype.objects.filter(isdeleted=0).order_by('code')

        # data for lookup
        context['ortype'] = Ortype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['circulationproduct'] = Circulationproduct.objects.filter(isdeleted=0).order_by('code')
        context['pk'] = 0
        # data for lookup

        closetransaction = Companyparameter.objects.all().first().last_closed_date
        validtransaction = closetransaction + relativedelta(months=1)
        context['validtransaction'] = validtransaction

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # year = str(form.cleaned_data['ordate'].year)
        # yearqs = Ormain.objects.filter(ornum__startswith=year)
        #
        # if yearqs:
        #     ornumlast = yearqs.latest('ornum')
        #     latestornum = str(ornumlast)
        #     print "latest: " + latestornum
        #
        #     ornum = year
        #     last = str(int(latestornum[4:]) + 1)
        #     zero_addon = 6 - len(last)
        #     for num in range(0, zero_addon):
        #         ornum += '0'
        #     ornum += last
        # else:
        #     ornum = year + '000001'
        #
        # print 'ornum: ' + ornum
        # self.object.ornum = ornum

        if self.object.orsource == 'A':
            self.object.payee_type = self.request.POST['payee_adv']
        elif self.object.orsource == 'C':
            self.object.payee_type = self.request.POST['payee_cir']

        if self.object.payee_type == 'AG':
            self.object.agency = Customer.objects.get(pk=int(self.request.POST['agency']))
            self.object.payee_code = self.object.agency.code
            self.object.payee_name = self.object.agency.name
        elif self.object.payee_type == 'C':
            self.object.client = Customer.objects.get(pk=int(self.request.POST['client']))
            self.object.payee_code = self.object.client.code
            self.object.payee_name = self.object.client.name
        elif self.object.payee_type == 'A':
            self.object.agent = Agent.objects.get(pk=int(self.request.POST['agent']))
            self.object.payee_code = self.object.agent.code
            self.object.payee_name = self.object.agent.name

        if self.request.POST['wtax'] == '':
            self.object.wtaxrate = 0
        else:
            self.object.wtaxrate = Wtax.objects.get(pk=int(self.request.POST['wtax'])).rate

        self.object.vatrate = Vat.objects.get(pk=int(self.request.POST['vat'])).rate

        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        non_vat_amount = decimal.Decimal(self.object.amount) / (1 + (decimal.Decimal(self.object.vatrate) /
                                                                     decimal.Decimal(100)) -
                                                                (decimal.Decimal(self.object.wtaxrate) /
                                                                 decimal.Decimal(100)))
        print non_vat_amount

        if self.object.vatrate > 0:
            self.object.vatablesale = non_vat_amount
            self.object.vatexemptsale = 0
            self.object.vatzeroratedsale = 0
        elif self.object.vat.code == "VE":
            self.object.vatexemptsale = non_vat_amount
            self.object.vatablesale = 0
            self.object.vatzeroratedsale = 0
        elif self.object.vat.code == "ZE":
            self.object.vatzeroratedsale = non_vat_amount
            self.object.vatexemptsale = 0
            self.object.vatablesale = 0
        elif self.object.vat.code == "VATNA":
            self.object.vatzeroratedsale = 0
            self.object.vatexemptsale = 0
            self.object.vatablesale = 0

        self.object.vatamount = non_vat_amount * (decimal.Decimal(self.object.vatrate) / decimal.Decimal(100))
        self.object.wtaxamount = non_vat_amount * (decimal.Decimal(self.object.wtaxrate) / decimal.Decimal(100))
        self.object.totalsale = non_vat_amount + self.object.vatamount - self.object.wtaxamount
        self.object.collector_code = self.object.collector.code
        self.object.collector_name = self.object.collector.name

        if self.object.circulationproduct:
            self.object.circulationproduct_code = self.object.circulationproduct.code
            self.object.circulationproduct_name = self.object.circulationproduct.description

        self.object.save()

        if Ordetailtemp.objects.filter(secretkey=self.request.POST['secretkey']).count() == 0:
            addcashinbank(self.request.POST['secretkey'], self.object.totalsale, self.request.user)

        # save ordetailtemp to ordetail
        source = 'ordetailtemp'
        mainid = self.object.id
        num = self.object.ornum
        secretkey = self.request.POST['secretkey']

        ormaindate = self.object.ordate
        savedetail(source, mainid, num, secretkey, self.request.user, ormaindate)

        return HttpResponseRedirect('/officialreceipt/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Ormain
    template_name = 'officialreceipt/update.html'
    fields = ['ordate', 'ortype', 'orsource', 'collector', 'branch', 'amount', 'amountinwords', 'vat',
              'wtax', 'outputvattype', 'deferredvat', 'circulationproduct', 'bankaccount', 'particulars', 'government',
              'remarks', 'vatrate', 'wtaxrate', 'orsource', 'prnum', 'prdate', 'ornum', 'adtype']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('officialreceipt.change_ormain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # accounting entry starts here
    def get_initial(self):
        self.mysecretkey = generatekey(self)

        detailinfo = Ordetail.objects.filter(ormain=self.object.pk).order_by('item_counter')

        for drow in detailinfo:
            detail = Ordetailtemp()
            detail.secretkey = self.mysecretkey
            detail.or_num = drow.or_num
            detail.ormain = drow.ormain_id
            detail.ordetail = drow.pk
            detail.item_counter = drow.item_counter
            detail.or_date = drow.or_date
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
            detail.save()

            detailtempid = detail.id

            breakinfo = Ordetailbreakdown.objects. \
                filter(ordetail_id=drow.id).order_by('pk', 'datatype')
            if breakinfo:
                for brow in breakinfo:
                    breakdown = Ordetailbreakdowntemp()
                    breakdown.or_num = drow.or_num
                    breakdown.secretkey = self.mysecretkey
                    breakdown.ormain = drow.ormain_id
                    breakdown.ordetail = drow.pk
                    breakdown.ordetailtemp = detailtempid
                    breakdown.ordetailbreakdown = brow.pk
                    breakdown.item_counter = brow.item_counter
                    breakdown.or_date = brow.or_date
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
        if self.request.POST.get('agency', False):
            context['agency'] = Customer.objects.get(pk=self.request.POST['agency'], isdeleted=0)
        elif self.object.agency:
            context['agency'] = Customer.objects.get(pk=self.object.agency.id, isdeleted=0)
        if self.request.POST.get('client', False):
            context['client'] = Customer.objects.get(pk=self.request.POST['client'], isdeleted=0)
        elif self.object.client:
            context['client'] = Customer.objects.get(pk=self.object.client.id, isdeleted=0)
        if self.request.POST.get('agent', False):
            context['agent'] = Agent.objects.get(pk=self.request.POST['agent'], isdeleted=0)
        elif self.object.agent:
            context['agent'] = Agent.objects.get(pk=self.object.agent.id, isdeleted=0)

        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        # context['agency'] = Customer.objects.get(isdeleted=0, ).order_by('code')  # add filter customer type
        # context['client'] = Customer.objects.get(isdeleted=0, ).order_by('code')  # add filter customer type
        # context['agent'] = Agent.objects.get(isdeleted=0, ).order_by('code')
        context['circulationproduct'] = Circulationproduct.objects.filter(isdeleted=0).order_by('code')
        context['ornum'] = self.object.ornum
        context['trans_type'] = self.object.transaction_type
        context['adtype'] = Adtype.objects.filter(isdeleted=0).order_by('code')
        context['footers'] = [self.object.enterby.first_name + " " + self.object.enterby.last_name if self.object.enterby else '',
                              self.object.importby.first_name + " " + self.object.importby.last_name if self.object.importby else '',
                              self.object.enterdate, self.object.importdate,
                              self.object.modifyby.first_name + " " + self.object.modifyby.last_name if self.object.modifyby else '',
                              self.object.postby.first_name + " " + self.object.postby.last_name if self.object.postby else '',
                              self.object.modifydate, self.object.postdate,
                              self.object.closeby.first_name + " " + self.object.closeby.last_name if self.object.closeby else '',
                              self.object.closedate,
                              ]
        context['logs'] = self.object.logs

        if Logs_ormain.objects.filter(orno=self.object.ornum, importstatus='P'):
            context['logs_ormain'] = Logs_ormain.objects.filter(orno=self.object.ornum, importstatus='P')
            context['logs_ordetail'] = Logs_ordetail.objects.filter(orno=self.object.ornum, importstatus='P',
                                                                    batchkey=context['logs_ormain'].first().batchkey)
            context['logs_orstatus'] = context['logs_ormain'].first().status if context['logs_ormain'] else ''

        context['artype'] = 'A' if self.object.orsource == 'A' else 'C' if self.object.orsource == 'C' else ''

        # data for lookup
        context['ortype'] = Ortype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['product'] = Product.objects.filter(isdeleted=0).order_by('code')
        context['pk'] = self.object.pk
        # data for lookup

        # accounting entry starts here
        context['secretkey'] = self.mysecretkey
        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'ordetailtemp',
            'tablebreakdowntemp': 'ordetailbreakdowntemp',

            'datatemp': querystmtdetail('ordetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('ordetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        # accounting entry ends here

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if self.object.orsource == 'A':
            self.object.payee_type = self.request.POST['payee_adv']
        elif self.object.orsource == 'C':
            self.object.payee_type = self.request.POST['payee_cir']

        if self.object.payee_type == 'AG':
            self.object.agency = Customer.objects.get(pk=int(self.request.POST['agency']))
            self.object.client = None
            self.object.agent = None
            self.object.payee_code = self.object.agency.code
            self.object.payee_name = self.object.agency.name
        elif self.object.payee_type == 'C':
            self.object.client = Customer.objects.get(pk=int(self.request.POST['client']))
            self.object.payee_code = self.object.client.code
            self.object.payee_name = self.object.client.name
            self.object.agency = None
            self.object.agent = None
        elif self.object.payee_type == 'A':
            self.object.agent = Agent.objects.get(pk=int(self.request.POST['agent']))
            self.object.payee_code = self.object.agent.code
            self.object.payee_name = self.object.agent.name
            self.object.agency = None
            self.object.client = None

        if self.request.POST['wtax'] == '':
            self.object.wtaxrate = 0
        else:
            self.object.wtaxrate = Wtax.objects.get(pk=int(self.request.POST['wtax'])).rate

        self.object.vatrate = Vat.objects.get(pk=int(self.request.POST['vat'])).rate

        self.object.acctentry_incomplete = 0
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['ordate', 'amount', 'amountinwords', 'deferredvat', 'vatrate', 'wtaxrate',
                                        'particulars', 'government', 'remarks', 'bankaccount', 'branch', 'collector',
                                        'ortype', 'vat', 'wtax', 'outputvattype', 'agency', 'agent', 'client',
                                        'orsource', 'payee_code', 'payee_name', 'payee_type', 'product', 'modifyby',
                                        'modifydate', 'acctentry_incomplete'])

        non_vat_amount = decimal.Decimal(self.object.amount) / (1 + (decimal.Decimal(self.object.vatrate) /
                                                                     decimal.Decimal(100)) -
                                                                (decimal.Decimal(self.object.wtaxrate) /
                                                                 decimal.Decimal(100)))
        # print non_vat_amount

        if self.object.vatrate > 0:
            self.object.vatablesale = non_vat_amount
            self.object.vatexemptsale = 0
            self.object.vatzeroratedsale = 0
        elif self.object.vat.code == "VE":
            self.object.vatexemptsale = non_vat_amount
            self.object.vatablesale = 0
            self.object.vatzeroratedsale = 0
        elif self.object.vat.code == "ZE":
            self.object.vatzeroratedsale = non_vat_amount
            self.object.vatexemptsale = 0
            self.object.vatablesale = 0
        elif self.object.vat.code == "VATNA":
            self.object.vatzeroratedsale = 0
            self.object.vatexemptsale = 0
            self.object.vatablesale = 0

        self.object.vatamount = non_vat_amount * (decimal.Decimal(self.object.vatrate) / decimal.Decimal(100))
        self.object.wtaxamount = non_vat_amount * (decimal.Decimal(self.object.wtaxrate) / decimal.Decimal(100))
        self.object.totalsale = non_vat_amount + self.object.vatamount - self.object.wtaxamount
        self.object.collector_code = self.object.collector.code
        self.object.collector_name = self.object.collector.name

        if self.object.circulationproduct:
            self.object.circulationproduct_code = self.object.circulationproduct.code
            self.object.circulationproduct_name = self.object.circulationproduct.description

        self.object.save(update_fields=['vatamount', 'wtaxamount', 'vatablesale', 'vatexemptsale', 'vatzeroratedsale',
                                        'totalsale', 'collector_code', 'collector_name', 'circulationproduct_code',
                                        'circulationproduct', 'circulationproduct_name'])

        # save ordetailtemp to ordetail
        source = 'ordetailtemp'
        mainid = self.object.id
        num = self.object.ornum
        secretkey = self.request.POST['secretkey']
        ormaindate = self.object.ordate

        updatedetail(source, mainid, num, secretkey, self.request.user, ormaindate)

        # Save Activity Logs
        Activitylogs.objects.create(
            user_id=self.request.user.id,
            username=self.request.user,
            remarks='Update OR Transaction #' + self.object.ornum
        )

        # return HttpResponseRedirect('/officialreceipt/')
        return HttpResponseRedirect('/officialreceipt/' + str(self.object.id) + '/update')


def addcashinbank(secretkey, totalsale, user):
    ordetailtemp1 = Ordetailtemp()
    ordetailtemp1.item_counter = 1
    ordetailtemp1.secretkey = secretkey
    ordetailtemp1.or_num = ''
    ordetailtemp1.or_date = datetime.datetime.now()
    ordetailtemp1.chartofaccount = Companyparameter.objects.get(code='PDI').coa_cashinbank.id
    ordetailtemp1.debitamount = totalsale
    ordetailtemp1.balancecode = 'D'
    ordetailtemp1.enterby = user
    ordetailtemp1.modifyby = user
    ordetailtemp1.save()
    print 'saved'


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Ormain
    template_name = 'officialreceipt/report/index.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['ortype'] = Ortype.objects.filter(isdeleted=0).order_by('description')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['agency'] = Customer.objects.filter(isdeleted=0).order_by('code')
        context['adtype'] = Adtype.objects.filter(isdeleted=0).order_by('code')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('code')
        context['outputvat'] = Outputvat.objects.filter(isdeleted=0).order_by('code')
        context['client'] = Customer.objects.filter(isdeleted=0).order_by('code')
        context['agent'] = Agent.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['product'] = Product.objects.filter(isdeleted=0).order_by('code')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultHtmlView(ListView):
    model = Ormain
    template_name = 'officialreceipt/reportresulthtml.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "OFFICIAL RECEIPT"
        context['rc_title'] = "OFFICIAL RECEIPT"

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Ormain
    template_name = 'officialreceipt/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "OFFICIAL RECEIPT"
        context['rc_title'] = "OFFICIAL RECEIPT"

        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_xls = ''
    report_total = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            report_type = "Official Receipt Summary"
            report_xls = "OR Summary"
        else:
            report_type = "Official Receipt Detailed"
            report_xls = "OR Detailed"
        query = Ormain.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ornum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ornum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ordate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ordate__lte=key_data)

        if request.COOKIES.get('rep_f_ortype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ortype_' + request.resolver_match.app_name))
            query = query.filter(ortype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(branch=int(key_data))
        if request.COOKIES.get('rep_f_collector_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_collector_' + request.resolver_match.app_name))
            query = query.filter(collector=int(key_data))
        if request.COOKIES.get('rep_f_product_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_product_' + request.resolver_match.app_name))
            query = query.filter(product=int(key_data))
        if request.COOKIES.get('rep_f_bankaccount_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_bankaccount_' + request.resolver_match.app_name))
            query = query.filter(bankaccount=int(key_data))
        if request.COOKIES.get('rep_f_orstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_orstatus_' + request.resolver_match.app_name))
            query = query.filter(orstatus=str(key_data))
        if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
            if key_data == 'P':
                query = query.filter(postby__isnull=False)
            elif key_data == 'U':
                query = query.filter(postby__isnull=True)
        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            query = query.filter(status=str(key_data))
        if request.COOKIES.get('rep_f_government_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_government_' + request.resolver_match.app_name))
            query = query.filter(government=str(key_data))
        if request.COOKIES.get('rep_f_transaction_type_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_transaction_type_' + request.resolver_match.app_name))
            query = query.filter(transaction_type=str(key_data))

        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(vat=int(key_data))
        if request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name))
            if key_data == 'with':
                query = query.filter(outputvattype__isnull=False)
            elif key_data == 'without':
                query = query.filter(outputvattype__isnull=True)
            else:
                query = query.filter(outputvattype=int(key_data))
        if request.COOKIES.get('rep_f_wtax_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_wtax_' + request.resolver_match.app_name))
            query = query.filter(wtax=int(key_data))
        if request.COOKIES.get('rep_f_deferredvat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferredvat_' + request.resolver_match.app_name))
            query = query.filter(deferredvat=str(key_data))

        if request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name))
            query = query.filter(orsource=str(key_data))
            if request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name) == 'A':
                if request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name):
                    key_data = str(request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name))
                    query = query.filter(payee_type=str(key_data))
                    if request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name) == 'AG':
                        if request.COOKIES.get('rep_f_payee_agency_' + request.resolver_match.app_name)\
                                and request.COOKIES.get('rep_f_payee_agency_' + request.resolver_match.app_name) != 'null':
                            key_data = request.COOKIES.get('rep_f_payee_agency_' + request.resolver_match.app_name)
                            query = query.filter(agency=int(key_data))
                    if request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name) == 'C':
                        if request.COOKIES.get('rep_f_payee_client_' + request.resolver_match.app_name)\
                                and request.COOKIES.get('rep_f_payee_client_' + request.resolver_match.app_name) != 'null':
                            key_data = request.COOKIES.get('rep_f_payee_client_' + request.resolver_match.app_name)
                            query = query.filter(client=int(key_data))
            if request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name) == 'C':
                if request.COOKIES.get('rep_f_payee_cir_' + request.resolver_match.app_name):
                    key_data = str(request.COOKIES.get('rep_f_payee_cir_' + request.resolver_match.app_name))
                    query = query.filter(payee_type=str(key_data))
                    if request.COOKIES.get('rep_f_payee_cir_' + request.resolver_match.app_name) == 'A':
                        if request.COOKIES.get('rep_f_payee_agent_' + request.resolver_match.app_name)\
                                and request.COOKIES.get('rep_f_payee_agent_' + request.resolver_match.app_name) != 'null':
                            key_data = str(request.COOKIES.get('rep_f_payee_agent_' + request.resolver_match.app_name))
                            query = query.filter(agent=str(key_data))
        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
            report_type = "Official Receipt Unbalanced Entries"
            report_xls = "OR Unbalanced Entries"
        else:
            report_type = "Official Receipt All Entries"
            report_xls = "OR All Entries"

        query = Ordetail.objects.filter(isdeleted=0, ormain__isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ormain__ornum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ormain__ornum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ormain__ordate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ormain__ordate__lte=key_data)

        if request.COOKIES.get('rep_f_ortype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ortype_' + request.resolver_match.app_name))
            query = query.filter(ormain__ortype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(ormain__branch=int(key_data))
        if request.COOKIES.get('rep_f_collector_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_collector_' + request.resolver_match.app_name))
            query = query.filter(ormain__collector=int(key_data))
        if request.COOKIES.get('rep_f_product_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_product_' + request.resolver_match.app_name))
            query = query.filter(ormain__product=int(key_data))
        if request.COOKIES.get('rep_f_bankaccount_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_bankaccount_' + request.resolver_match.app_name))
            query = query.filter(ormain__bankaccount=int(key_data))
        if request.COOKIES.get('rep_f_orstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_orstatus_' + request.resolver_match.app_name))
            query = query.filter(ormain__orstatus=str(key_data))
        if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
            if key_data == 'P':
                query = query.filter(ormain__postby__isnull=False)
            elif key_data == 'U':
                query = query.filter(ormain__postby__isnull=True)
        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            query = query.filter(ormain__status=str(key_data))
        if request.COOKIES.get('rep_f_government_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_government_' + request.resolver_match.app_name))
            query = query.filter(ormain__government=str(key_data))
        if request.COOKIES.get('rep_f_transaction_type_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_transaction_type_' + request.resolver_match.app_name))
            query = query.filter(ormain__transaction_type=str(key_data))

        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(ormain__vat=int(key_data))
        if request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name))
            if key_data == 'with':
                query = query.filter(ormain__outputvattype__isnull=False)
            elif key_data == 'without':
                query = query.filter(ormain__outputvattype__isnull=True)
            else:
                query = query.filter(ormain__outputvattype=int(key_data))
        if request.COOKIES.get('rep_f_wtax_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_wtax_' + request.resolver_match.app_name))
            query = query.filter(ormain__wtax=int(key_data))
        if request.COOKIES.get('rep_f_deferredvat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferredvat_' + request.resolver_match.app_name))
            query = query.filter(ormain__deferredvat=str(key_data))

        if request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name))
            query = query.filter(ormain__orsource=str(key_data))
            if request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name) == 'A':
                if request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name):
                    key_data = str(request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name))
                    query = query.filter(ormain__payee_type=str(key_data))
                    if request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name) == 'AG':
                        if request.COOKIES.get('rep_f_payee_agency_' + request.resolver_match.app_name)\
                                and request.COOKIES.get('rep_f_payee_agency_' + request.resolver_match.app_name) != 'null':
                            key_data = request.COOKIES.get('rep_f_payee_agency_' + request.resolver_match.app_name)
                            query = query.filter(ormain__agency=int(key_data))
                    if request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name) == 'C':
                        if request.COOKIES.get('rep_f_payee_client_' + request.resolver_match.app_name)\
                                and request.COOKIES.get('rep_f_payee_client_' + request.resolver_match.app_name) != 'null':
                            key_data = request.COOKIES.get('rep_f_payee_client_' + request.resolver_match.app_name)
                            query = query.filter(ormain__client=int(key_data))
            if request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name) == 'C':
                if request.COOKIES.get('rep_f_payee_cir_' + request.resolver_match.app_name):
                    key_data = str(request.COOKIES.get('rep_f_payee_cir_' + request.resolver_match.app_name))
                    query = query.filter(ormain__payee_type=str(key_data))
                    if request.COOKIES.get('rep_f_payee_cir_' + request.resolver_match.app_name) == 'A':
                        if request.COOKIES.get('rep_f_payee_agent_' + request.resolver_match.app_name)\
                                and request.COOKIES.get('rep_f_payee_agent_' + request.resolver_match.app_name) != 'null':
                            key_data = str(request.COOKIES.get('rep_f_payee_agent_' + request.resolver_match.app_name))
                            query = query.filter(ormain__agent=str(key_data))

        query = query.values('ormain__ornum')\
            .annotate(margin=Sum('debitamount')-Sum('creditamount'), debitsum=Sum('debitamount'), creditsum=Sum('creditamount'))\
            .values('ormain__ornum', 'margin', 'ormain__ordate', 'debitsum', 'creditsum', 'ormain__pk', 'ormain__payee_code', 'ormain__payee_name').order_by('ormain__ornum')

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
            query = query.exclude(margin=0)

        if request.COOKIES.get('rep_f_uborder_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_uborder_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)

        report_total = query.aggregate(Sum('debitsum'), Sum('creditsum'), Sum('margin'))

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        query = Ordetail.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name) != 'null':
            gl_request = request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name)

            query = query.filter(chartofaccount=int(gl_request))

            enable_check = Chartofaccount.objects.get(pk=gl_request)
            if enable_check.bankaccount_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name)
                query = query.filter(bankaccount=get_object_or_None(Bankaccount, pk=int(gl_item)))
            if enable_check.department_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name)
                query = query.filter(department=get_object_or_None(Department, pk=int(gl_item)))
            if enable_check.unit_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name)
                query = query.filter(unit=get_object_or_None(Unit, pk=int(gl_item)))
            if enable_check.branch_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name)
                query = query.filter(branch=get_object_or_None(Branch, pk=int(gl_item)))
            if enable_check.product_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name)
                query = query.filter(product=get_object_or_None(Product, pk=int(gl_item)))
            if enable_check.inputvat_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name)
                query = query.filter(inputvat=get_object_or_None(Inputvat, pk=int(gl_item)))
            if enable_check.outputvat_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name)
                query = query.filter(outputvat=get_object_or_None(Outputvat, pk=int(gl_item)))
            if enable_check.vat_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name)
                query = query.filter(vat=get_object_or_None(Vat, pk=int(gl_item)))
            if enable_check.wtax_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name)
                query = query.filter(wtax=get_object_or_None(Wtax, pk=int(gl_item)))
            if enable_check.ataxcode_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name)
                query = query.filter(ataxcode=get_object_or_None(Ataxcode, pk=int(gl_item)))
            if enable_check.employee_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name)
                query = query.filter(employee=get_object_or_None(Employee, pk=int(gl_item)))
            if enable_check.supplier_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name)\
                    and request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name)
                query = query.filter(supplier=get_object_or_None(Supplier, pk=int(gl_item)))
            if enable_check.customer_enable == 'Y'\
                    and request.COOKIES.get('rep_f_gl_customer_' + request.resolver_match.app_name)\
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
            query = query.filter(ormain__ornum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ormain__ornum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ormain__ordate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ormain__ordate__lte=key_data)

        if request.COOKIES.get('rep_f_ortype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ortype_' + request.resolver_match.app_name))
            query = query.filter(ormain__ortype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(ormain__branch=int(key_data))
        if request.COOKIES.get('rep_f_collector_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_collector_' + request.resolver_match.app_name))
            query = query.filter(ormain__collector=int(key_data))
        if request.COOKIES.get('rep_f_product_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_product_' + request.resolver_match.app_name))
            query = query.filter(ormain__product=int(key_data))
        if request.COOKIES.get('rep_f_bankaccount_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_bankaccount_' + request.resolver_match.app_name))
            query = query.filter(ormain__bankaccount=int(key_data))
        if request.COOKIES.get('rep_f_orstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_orstatus_' + request.resolver_match.app_name))
            query = query.filter(ormain__orstatus=str(key_data))
        if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
            if key_data == 'P':
                query = query.filter(ormain__postby__isnull=False)
            elif key_data == 'U':
                query = query.filter(ormain__postby__isnull=True)
        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            query = query.filter(ormain__status=str(key_data))
        if request.COOKIES.get('rep_f_government_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_government_' + request.resolver_match.app_name))
            query = query.filter(ormain__government=str(key_data))
        if request.COOKIES.get('rep_f_transaction_type_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_transaction_type_' + request.resolver_match.app_name))
            query = query.filter(ormain__transaction_type=str(key_data))

        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(ormain__vat=int(key_data))
        if request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name))
            if key_data == 'with':
                query = query.filter(ormain__outputvattype__isnull=False)
            elif key_data == 'without':
                query = query.filter(ormain__outputvattype__isnull=True)
            else:
                query = query.filter(ormain__outputvattype=int(key_data))
        if request.COOKIES.get('rep_f_wtax_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_wtax_' + request.resolver_match.app_name))
            query = query.filter(ormain__wtax=int(key_data))
        if request.COOKIES.get('rep_f_deferredvat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferredvat_' + request.resolver_match.app_name))
            query = query.filter(ormain__deferredvat=str(key_data))

        if request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name))
            query = query.filter(ormain__orsource=str(key_data))
            if request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name) == 'A':
                if request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name):
                    key_data = str(request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name))
                    query = query.filter(ormain__payee_type=str(key_data))
                    if request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name) == 'AG':
                        if request.COOKIES.get('rep_f_payee_agency_' + request.resolver_match.app_name)\
                                and request.COOKIES.get('rep_f_payee_agency_' + request.resolver_match.app_name) != 'null':
                            key_data = request.COOKIES.get('rep_f_payee_agency_' + request.resolver_match.app_name)
                            query = query.filter(ormain__agency=int(key_data))
                    if request.COOKIES.get('rep_f_payee_adv_' + request.resolver_match.app_name) == 'C':
                        if request.COOKIES.get('rep_f_payee_client_' + request.resolver_match.app_name)\
                                and request.COOKIES.get('rep_f_payee_client_' + request.resolver_match.app_name) != 'null':
                            key_data = request.COOKIES.get('rep_f_payee_client_' + request.resolver_match.app_name)
                            query = query.filter(ormain__client=int(key_data))
            if request.COOKIES.get('rep_f_artype_' + request.resolver_match.app_name) == 'C':
                if request.COOKIES.get('rep_f_payee_cir_' + request.resolver_match.app_name):
                    key_data = str(request.COOKIES.get('rep_f_payee_cir_' + request.resolver_match.app_name))
                    query = query.filter(ormain__payee_type=str(key_data))
                    if request.COOKIES.get('rep_f_payee_cir_' + request.resolver_match.app_name) == 'A':
                        if request.COOKIES.get('rep_f_payee_agent_' + request.resolver_match.app_name)\
                                and request.COOKIES.get('rep_f_payee_agent_' + request.resolver_match.app_name) != 'null':
                            key_data = str(request.COOKIES.get('rep_f_payee_agent_' + request.resolver_match.app_name))
                            query = query.filter(ormain__agent=str(key_data))

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "Official Receipt Accounting Entry - Summary"
            report_xls = "OR Acctg Entry - Summary"

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
            #                      'balancecode')\
            #              .annotate(Sum('debitamount'), Sum('creditamount'))\
            #              .order_by('-balancecode',
            #                        '-chartofaccount__accountcode',
            #                        'bankaccount__code',
            #                        'bankaccount__accountnumber',
            #                        'bankaccount__bank__code',
            #                        'department__departmentname',
            #                        'employee__firstname',
            #                        'supplier__name',
            #                        'customer__name',
            #                        'unit__description',
            #                        'branch__description',
            #                        'product__description',
            #                        'inputvat__description',
            #                        'outputvat__description',
            #                        '-vat__description',
            #                        'wtax__description',
            #                        'ataxcode__code')

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
                                 'balancecode') \
                .annotate(Sum('debitamount'), Sum('creditamount')) \
                .order_by('-balancecode',
                          'branch__code',
                          'department__code',
                          'bankaccount__code',
                          'chartofaccount__accountcode')
        else:
            report_type = "Official Receipt Accounting Entry - Detailed"
            report_xls = "OR Acctg Entry - Detailed"

            query = query.annotate(Sum('debitamount'), Sum('creditamount')).order_by('-balancecode',
                                                                                     '-chartofaccount__accountcode',
                                                                                     'bankaccount__code',
                                                                                     'bankaccount__accountnumber',
                                                                                     'bankaccount__bank__code',
                                                                                     'department__departmentname',
                                                                                     'employee__firstname',
                                                                                     'supplier__name',
                                                                                     'customer__name',
                                                                                     'unit__description',
                                                                                     'branch__description',
                                                                                     'product__description',
                                                                                     'inputvat__description',
                                                                                     'outputvat__description',
                                                                                     '-vat__description',
                                                                                     'wtax__description',
                                                                                     'ataxcode__code',
                                                                                     'or_num')

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's' \
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(amount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
            query = query.filter(amount__lte=float(key_data.replace(',', '')))

        if request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name))
            if key_data == 'd':
                query = query.reverse()

        report_total = query.aggregate(Sum('amount'))

    return query, report_type, report_total, report_xls


@csrf_exempt
def reportresultxlsx(request):
    import xlsxwriter
    try:
        import cStringIO as StringIO
    except ImportError:
        import StringIO
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)

    # query and default variables
    queryset, report_type, report_total, report_xls = reportresultquery(request)
    report_type = report_type if report_type != '' else 'OR Report'
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
        amount_placement = 12
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        amount_placement = 3
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 4
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        amount_placement = 15

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'OR Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Type', bold)
        worksheet.write('D1', 'AR Type', bold)
        worksheet.write('E1', 'Payee', bold)
        worksheet.write('F1', 'Status', bold)
        worksheet.write('G1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.write('A1', 'OR Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Type', bold)
        worksheet.write('D1', 'AR Type', bold)
        worksheet.write('E1', 'Payee', bold)
        worksheet.write('F1', 'Product', bold)
        worksheet.write('G1', 'VAT', bold)
        worksheet.write('H1', 'WTAX', bold)
        worksheet.write('I1', 'Collector', bold)
        worksheet.write('J1', 'Branch', bold)
        worksheet.write('K1', 'Gov`t', bold)
        worksheet.write('L1', 'Status', bold)
        worksheet.write('M1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        worksheet.write('A1', 'OR Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Payee', bold)
        worksheet.write('D1', 'Debit', bold_right)
        worksheet.write('E1', 'Credit', bold_right)
        worksheet.write('F1', 'Margin', bold_right)
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
        worksheet.merge_range('A1:A2', 'Chart of Account', bold)
        worksheet.merge_range('B1:N1', 'Details', bold_center)
        worksheet.merge_range('O1:O2', 'Date', bold)
        worksheet.merge_range('P1:P2', 'Debit', bold_right)
        worksheet.merge_range('Q1:Q2', 'Credit', bold_right)
        worksheet.write('B2', 'Bank Account', bold)
        worksheet.write('C2', 'Department', bold)
        worksheet.write('D2', 'Employee', bold)
        worksheet.write('E2', 'Supplier', bold)
        worksheet.write('F2', 'Customer', bold)
        worksheet.write('G2', 'Unit', bold)
        worksheet.write('H2', 'Branch', bold)
        worksheet.write('I2', 'Product', bold)
        worksheet.write('J2', 'Input VAT', bold)
        worksheet.write('K2', 'Output VAT', bold)
        worksheet.write('L2', 'VAT', bold)
        worksheet.write('M2', 'WTAX', bold)
        worksheet.write('N2', 'ATAX Code', bold)
        row += 1

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            data = [
                obj.ornum,
                DateFormat(obj.ordate).format('Y-m-d'),
                obj.ortype.description,
                obj.get_orsource_display(),
                "[" + obj.payee_code + "] " + obj.payee_name,
                obj.get_orstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            str_vat = obj.vat.code if obj.vat else ''
            str_wtax = obj.wtax.code if obj.wtax else ''

            data = [
                obj.ornum,
                DateFormat(obj.ordate).format('Y-m-d'),
                obj.ortype.description,
                obj.get_orsource_display(),
                "[" + obj.payee_code + "] " + obj.payee_name,
                obj.product_name,
                str_vat,
                str_wtax,
                obj.collector.name,
                obj.branch.description,
                obj.get_government_display(),
                obj.get_orstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
            data = [
                obj['ormain__ornum'],
                DateFormat(obj['ormain__ordate']).format('Y-m-d'),
                obj['ormain__payee_code'] + ' - ' + obj['ormain__payee_name'],
                obj['debitsum'],
                obj['creditsum'],
                obj['margin'],
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            bankaccount__code = obj['bankaccount__code'] if obj['bankaccount__code'] is not None else ''
            department__code = obj['department__code'] if obj['department__code'] is not None else ''
            branch__code = obj['branch__code'] if obj['branch__code'] is not None else ''
            bankaccount__accountnumber = obj['bankaccount__accountnumber'] if obj[
                                                                                  'bankaccount__accountnumber'] is not None else ''
            department__departmentname = obj['department__departmentname'] if obj[
                                                                                  'department__departmentname'] is not None else ''

            data = [
                obj['chartofaccount__accountcode'],
                obj['chartofaccount__description'],
                bankaccount__code + ' ' + department__code + ' ' + branch__code,
                bankaccount__accountnumber + ' ' + department__departmentname,
                obj['debitamount__sum'],
                obj['creditamount__sum'],
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
            str_firstname = obj.employee.firstname if obj.employee is not None else ''
            str_lastname = obj.employee.lastname if obj.employee is not None else ''

            data = [
                obj.chartofaccount.accountcode + " - " + obj.chartofaccount.description,
                obj.bankaccount.code if obj.bankaccount is not None else '',
                obj.department.departmentname if obj.department is not None else '',
                str_firstname + " " + str_lastname,
                obj.supplier.name if obj.supplier is not None else '',
                obj.customer.name if obj.customer is not None else '',
                obj.unit.description if obj.unit is not None else '',
                obj.branch.description if obj.branch is not None else '',
                obj.product.description if obj.product is not None else '',
                obj.inputvat.description if obj.inputvat is not None else '',
                obj.outputvat.description if obj.outputvat is not None else '',
                obj.vat.description if obj.vat is not None else '',
                obj.wtax.description if obj.wtax is not None else '',
                obj.ataxcode.code if obj.ataxcode is not None else '',
                DateFormat(obj.or_date).format('Y-m-d'),
                obj.debitamount__sum,
                obj.creditamount__sum,
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
        data = [
            "", "", "", "", "", "", "", "", "", "", "",
            "Total", report_total['amount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        data = [
            "", "",
            "Total", report_total['debitsum__sum'], report_total['creditsum__sum'], report_total['margin__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        data = [
            "", "",
            "Total", report_total['debitamount__sum'], report_total['creditamount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        data = [
            "", "", "", "", "", "", "", "", "", "", "", "", "", "",
            "Total", report_total['debitamount__sum'], report_total['creditamount__sum'],
        ]

    row += 1
    for col_num in xrange(len(data)):
        worksheet.write(row, col_num, data[col_num], bold_money_format)

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+report_xls+".xlsx"
    return response


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Ormain
    template_name = 'officialreceipt/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('officialreceipt.delete_ormain') or self.object.status == 'O' \
                or self.object.orstatus == 'A' or self.object.orstatus == 'I' or self.object.orstatus == 'R':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.orstatus = 'D'
        self.object.save()

        return HttpResponseRedirect('/officialreceipt')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Ormain
    template_name = 'officialreceipt/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['ormain'] = Ormain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['detail'] = Ordetail.objects.filter(isdeleted=0). \
            filter(ormain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Ordetail.objects.filter(isdeleted=0). \
            filter(ormain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Ordetail.objects.filter(isdeleted=0). \
            filter(ormain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))
        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "https://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedor = Ormain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        printedor.print_ctr += 1
        printedor.save()
        return context

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
        ortype = request.GET['ortype']
        artype = request.GET['artype']
        payee = request.GET['payee']
        collector = request.GET['collector']
        branch = request.GET['branch']
        product = request.GET['product']
        adtype = request.GET['adtype']
        wtax = request.GET['wtax']
        vat = request.GET['vat']
        outputvat = request.GET['outputvat']
        bankaccount = request.GET['bankaccount']
        status = request.GET['status']
        orstatus = request.GET['orstatus']
        title = "Official Receipt List"
        list = Ormain.objects.filter(isdeleted=0).order_by('ornum')[:0]

        if report == '1':
            title = "Official Receipt Transaction List - Summary"
            q = Ormain.objects.all().filter(isdeleted=0).order_by('ordate', 'ornum')
            if dfrom != '':
                q = q.filter(ordate__gte=dfrom)
            if dto != '':
                q = q.filter(ordate__lte=dto)
        elif report == '2':
            title = "Official Receipt Transaction List"
            q = Ordetail.objects.select_related('ormain').filter(isdeleted=0).order_by('or_date', 'or_num', 'item_counter')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
        elif report == '3':
            title = "Unposted Official Receipt Transaction List - Summary"
            q = Ormain.objects.filter(isdeleted=0,status__in=['A','C']).order_by('ordate', 'ornum')
            if dfrom != '':
                q = q.filter(ordate__gte=dfrom)
            if dto != '':
                q = q.filter(ordate__lte=dto)
        elif report == '4':
            title = "Unposted Official Receipt Transaction List"
            q = Ordetail.objects.select_related('ormain').filter(isdeleted=0,status__in=['A','C']).order_by('or_date', 'or_num',  'item_counter')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
        elif report == '5':
            title = "Official Receipt List (Unbalanced Cash in Bank VS Amount)"
            q = Ormain.objects.select_related('ordetail').filter(isdeleted=0).order_by('ordate', 'ornum')
            if dfrom != '':
                q = q.filter(ordate__gte=dfrom)
            if dto != '':
                q = q.filter(ordate__lte=dto)
        elif report == '6':
            title = "Unbalanced Official Receipt Transaction List"
            q = Ormain.objects.select_related('ordetail').filter(isdeleted=0).order_by('ordate', 'ornum')
            if dfrom != '':
                q = q.filter(ordate__gte=dfrom)
            if dto != '':
                q = q.filter(ordate__lte=dto)
        elif report == '7':
            title = "Official Receipt Register"
            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')
            if dfrom != '':
                q = q.filter(ordate__gte=dfrom)
            if dto != '':
                q = q.filter(ordate__lte=dto)
        elif report == '8':
            title = "Official Receipt Output VAT"
            orlist = getORList(dfrom, dto)
            arr = getARR()

            query = query_orwithoutputvat(dfrom, dto, orlist, arr)

            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')
        elif report == '9':
            title = "Official Receipt Output VAT Summary"
            orlist = getORList(dfrom, dto)
            arr = getARR()

            query = query_orwithoutputvatsummary(dfrom, dto, orlist, arr)

            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')
        elif report == '10':
            title = "Official Receipt Without Output VAT"
            orlist = getORNoOutputVatList(dfrom, dto)
            arr = getARR()

            query = query_ornooutputvat(dfrom, dto, orlist, arr)

            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')
        elif report == '11':
            title = "Official Receipt Without Output VAT Summary"
            orlist = getORNoOutputVatList(dfrom, dto)
            arr = getARR()

            query = query_ornooutputvatsummary(dfrom, dto, orlist, arr)
            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')

        if ortype != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__ortype__exact=ortype)
            else:
                q = q.filter(ortype=ortype)
            print 'ortype'
        if artype != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__orsource__exact=artype)
            else:
                q = q.filter(orsource=artype)
            print 'artype'
        if payee != 'null':
            if report == '2' or report == '4':
                q = q.filter(ormain__payee_code__exact=payee)
            else:
                q = q.filter(payee_code=payee)
            print 'payee'
        if branch != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__branch__exact=branch)
            else:
                q = q.filter(branch=branch)
            print branch
        if collector != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__collector__exact=collector)
            else:
                q = q.filter(collector=collector)
            print 'collector'
        if product != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__product__exact=product)
            else:
                q = q.filter(product=product)
            print 'product'
        if adtype != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__adtype__exact=adtype)
            else:
                q = q.filter(adtype=adtype)
            print 'adtype'
        if wtax != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__wtax__exact=wtax)
            else:
                q = q.filter(wtax=wtax)
            print 'wtax'
        if vat != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__vat__exact=vat)
            else:
                q = q.filter(vat=vat)
            print 'vat'
        if outputvat != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__outputvattype__exact=outputvat)
            else:
                q = q.filter(outputvattype=outputvat)
            print 'outputvat'
        if bankaccount != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__bankaccount__exact=bankaccount)
            else:
                q = q.filter(bankaccount=bankaccount)
            print 'bankaccount'
        if status != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__status__exact=status)
            else:
                q = q.filter(status=status)
            print 'status'
        if orstatus != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__orstatus__exact=orstatus)
            else:
                q = q.filter(orstatus=orstatus)
            print 'orstatus'

        if report == '5':
            list = raw_query(1, company, dfrom, dto, ortype, artype, payee, collector, branch, product, adtype, wtax, vat, outputvat, bankaccount, status)
            dataset = pd.DataFrame(list)
            total = {}
            total['amount'] = dataset['amount'].sum()
            total['cashinbank'] = dataset['cashinbank'].sum()
            total['diff'] = dataset['diff'].sum()
            total['outputvat'] = dataset['outputvat'].sum()
            total['amountdue'] = dataset['amountdue'].sum()
        elif report == '6':
            list = raw_query(2, company, dfrom, dto, ortype, artype, payee, collector, branch, product, adtype, wtax,vat, outputvat, bankaccount, status)
            dataset = pd.DataFrame(list)
            total = {}
            #total['amount'] = dataset['amount'].sum()
            if list:
                total['debitamount'] = dataset['debitamount'].sum()
                total['creditamount'] = dataset['creditamount'].sum()
            else:
                total['debitamount'] = 0
                total['creditamount'] = 0
            #total['diff'] = dataset['totaldiff'].sum()
        elif report == '8' or report == '9' or report == '10' or report == '11':
            print 'pasok'
            list = query
            outputcredit = 0
            outputdebit = 0
            arrcredit = 0
            ardebit = 0
            if list:
                df = pd.DataFrame(query)
                outputcredit = df['outputvatcreditamount'].sum()
                outputdebit = df['outputvatdebitamount'].sum()
                arrcredit = df['arrcreditamount'].sum()
                arrdebit = df['arrdebitamount'].sum()
        else:
            list = q

        if list:
            #total = list.aggregate(total_amount=Sum('amount'))

            if report == '2' or report == '4':
                total = list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))
            elif report == '8' or report == '9' or report == '10' or report == '11':
                total = {'outputcredit': outputcredit, 'outputdebit': outputdebit, 'arrcredit': arrcredit, 'arrdebit':arrdebit}
            elif report == '5' or report == '6':
                print 'do nothing'
            else:
                total = list.filter(~Q(status='C')).aggregate(total_amount=Sum('amount'))

        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "dfrom": dfrom,
            "dto": dto,
            "datefrom": datetime.datetime.strptime(dfrom, '%Y-%m-%d'),
            "dateto": datetime.datetime.strptime(dto, '%Y-%m-%d'),
            "username": request.user, 
        }
        if report == '1':
            return Render.render('officialreceipt/report/report_1.html', context)
        elif report == '2':
            return Render.render('officialreceipt/report/report_2.html', context)
        elif report == '3':
            return Render.render('officialreceipt/report/report_3.html', context)
        elif report == '4':
            return Render.render('officialreceipt/report/report_4.html', context)
        elif report == '5':
            return Render.render('officialreceipt/report/report_5.html', context)
        elif report == '6':
            return Render.render('officialreceipt/report/report_6.html', context)
        elif report == '7':
            return Render.render('officialreceipt/report/report_7.html', context)
        elif report == '8':
            return Render.render('officialreceipt/report/report_8.html', context)
        elif report == '9':
            return Render.render('officialreceipt/report/report_9.html', context)
        elif report == '10':
            return Render.render('officialreceipt/report/report_10.html', context)
        elif report == '11':
            return Render.render('officialreceipt/report/report_11.html', context)
        else:
            return Render.render('officialreceipt/report/report_1.html', context)
        
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
        ortype = request.GET['ortype']
        artype = request.GET['artype']
        payee = request.GET['payee']
        collector = request.GET['collector']
        branch = request.GET['branch']
        product = request.GET['product']
        adtype = request.GET['adtype']
        wtax = request.GET['wtax']
        vat = request.GET['vat']
        outputvat = request.GET['outputvat']
        bankaccount = request.GET['bankaccount']
        status = request.GET['status']
        orstatus = request.GET['orstatus']
        title = "Official Receipt List"
        list = Ormain.objects.filter(isdeleted=0).order_by('ornum')[:0]

        if report == '1':
            title = "Official Receipt Transaction List - Summary"
            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')
            if dfrom != '':
                q = q.filter(ordate__gte=dfrom)
            if dto != '':
                q = q.filter(ordate__lte=dto)
        elif report == '2':
            title = "Official Receipt Transaction List"
            q = Ordetail.objects.select_related('ormain').filter(isdeleted=0).order_by('or_date', 'or_num', 'item_counter')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
        elif report == '3':
            title = "Unposted Official Receipt Transaction List - Summary"
            q = Ormain.objects.filter(isdeleted=0,status__in=['A','C']).order_by('ordate', 'ornum')
            if dfrom != '':
                q = q.filter(ordate__gte=dfrom)
            if dto != '':
                q = q.filter(ordate__lte=dto)
        elif report == '4':
            title = "Unposted Official Receipt Transaction List"
            q = Ordetail.objects.select_related('ormain').filter(isdeleted=0,status__in=['A','C']).order_by('or_date', 'or_num',  'item_counter')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
        elif report == '5':
            title = "Official Receipt List (Unbalanced Cash in Bank VS Amount)"
            q = Ormain.objects.select_related('ordetail').filter(isdeleted=0).order_by('ordate', 'ornum')
            if dfrom != '':
                q = q.filter(ordate__gte=dfrom)
            if dto != '':
                q = q.filter(ordate__lte=dto)
        elif report == '6':
            title = "Unbalanced Official Receipt Transaction List"
            q = Ormain.objects.select_related('ordetail').filter(isdeleted=0).order_by('ordate', 'ornum')
            if dfrom != '':
                q = q.filter(ordate__gte=dfrom)
            if dto != '':
                q = q.filter(ordate__lte=dto)
        elif report == '7':
            title = "Official Receipt Register"
            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')
            if dfrom != '':
                q = q.filter(ordate__gte=dfrom)
            if dto != '':
                q = q.filter(ordate__lte=dto)
        elif report == '8':
            title = "Official Receipt Output VAT"
            orlist = getORList(dfrom, dto)
            arr = getARR()

            query = query_orwithoutputvat(dfrom, dto, orlist, arr)

            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')
        elif report == '9':
            title = "Official Receipt Output VAT Summary"
            orlist = getORList(dfrom, dto)
            arr = getARR()

            query = query_orwithoutputvatsummary(dfrom, dto, orlist, arr)

            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')
        elif report == '10':
            title = "Official Receipt Without Output VAT"
            orlist = getORNoOutputVatList(dfrom, dto)
            arr = getARR()

            query = query_ornooutputvat(dfrom, dto, orlist, arr)

            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')
        elif report == '11':
            title = "Official Receipt Without Output VAT Summary"
            orlist = getORNoOutputVatList(dfrom, dto)
            arr = getARR()

            query = query_ornooutputvatsummary(dfrom, dto, orlist, arr)
            q = Ormain.objects.filter(isdeleted=0).order_by('ordate', 'ornum')

        if ortype != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__ortype__exact=ortype)
            else:
                q = q.filter(ortype=ortype)
        if artype != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__orsource__exact=artype)
            else:
                q = q.filter(orsource=artype)
        if payee != 'null':
            if report == '2' or report == '4':
                q = q.filter(ormain__payee_code__exact=payee)
            else:
                q = q.filter(payee_code=payee)
        if branch != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__branch__exact=branch)
            else:
                q = q.filter(branch=branch)
        if collector != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__collector__exact=collector)
            else:
                q = q.filter(collector=collector)
        if product != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__product__exact=product)
            else:
                q = q.filter(product=product)
        if adtype != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__adtype__exact=adtype)
            else:
                q = q.filter(adtype=adtype)
        if wtax != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__wtax__exact=wtax)
            else:
                q = q.filter(wtax=wtax)
        if vat != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__vat__exact=vat)
            else:
                q = q.filter(vat=vat)
        if outputvat != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__outputvattype__exact=outputvat)
            else:
                q = q.filter(outputvattype=outputvat)
        if bankaccount != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__bankaccount__exact=bankaccount)
            else:
                q = q.filter(bankaccount=bankaccount)
        if status != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__status__exact=status)
            else:
                q = q.filter(status=status)
        if orstatus != '':
            if report == '2' or report == '4':
                q = q.filter(ormain__orstatus__exact=orstatus)
            else:
                q = q.filter(orstatus=orstatus)
            print 'orstatus'

        if report == '5':
            list = raw_query(1, company, dfrom, dto, ortype, artype, payee, collector, branch, product, adtype, wtax, vat, outputvat, bankaccount, status)
            dataset = pd.DataFrame(list)
        elif report == '6':
            list = raw_query(2, company, dfrom, dto, ortype, artype, payee, collector, branch, product, adtype, wtax,vat, outputvat, bankaccount, status)
            dataset = pd.DataFrame(list)
        elif report == '8' or report == '9' or report == '10' or report == '11':
            print 'pasok'
            list = query
            outputcredit = 0
            outputdebit = 0
            arrcredit = 0
            ardebit = 0
            if list:
                df = pd.DataFrame(query)
                outputcredit = df['outputvatcreditamount'].sum()
                outputdebit = df['outputvatdebitamount'].sum()
                arrcredit = df['arrcreditamount'].sum()
                arrdebit = df['arrdebitamount'].sum()
        else:
            list = q

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

        filename = "orreport.xlsx"

        if report == '1':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0
            totalamount = 0
            amount = 0
            for data in list:
                worksheet.write(row, col, data.ornum)
                worksheet.write(row, col + 1, data.ordate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)
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

            filename = "ortransactionlistsummary.xlsx"

        elif report == '2':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Particular', bold)
            worksheet.write('D4', 'Account Title', bold)
            worksheet.write('E4', 'Subs Ledger', bold)
            worksheet.write('F4', 'Debit', bold)
            worksheet.write('G4', 'Credit', bold)

            row = 4
            col = 0


            totaldebit = 0
            totalcredit = 0
            list = list.values('ormain__ornum', 'ormain__ordate', 'ormain__particulars', 'ormain__payee_name', 'chartofaccount__accountcode', 'chartofaccount__description', 'status', 'debitamount', 'creditamount', 'branch__code', 'bankaccount__code', 'department__code')
            dataset = pd.DataFrame.from_records(list)

            for ornum, detail in dataset.fillna('NaN').groupby(['ormain__ornum', 'ormain__ordate', 'ormain__payee_name', 'ormain__particulars', 'status']):
                worksheet.write(row, col, ornum[0])
                worksheet.write(row, col+1, ornum[1], formatdate)
                if ornum[4] == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col+2, ornum[2])
                worksheet.write(row, col+3, ornum[3])
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
                    worksheet.write(row, col + 4, branch+' '+bankaccount+' '+department)
                    if ornum[4] == 'C':
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


            filename = "ortransactionlist.xlsx"

        elif report == '3':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0

            totalamount = 0
            amount = 0
            for data in list:
                worksheet.write(row, col, data.ornum)
                worksheet.write(row, col + 1, data.ordate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)
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
            filename = "unpostedortransactionlistsummary.xlsx"

        elif report == '4':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Particular', bold)
            worksheet.write('D4', 'Account Title', bold)
            worksheet.write('E4', 'Subs Ledger', bold)
            worksheet.write('F4', 'Debit', bold)
            worksheet.write('G4', 'Credit', bold)

            row = 4
            col = 0

            totaldebit = 0
            totalcredit = 0
            list = list.values('ormain__ornum', 'ormain__ordate', 'ormain__particulars', 'ormain__payee_name',
                               'chartofaccount__accountcode', 'chartofaccount__description', 'status', 'debitamount',
                               'creditamount', 'branch__code', 'bankaccount__code', 'department__code')
            dataset = pd.DataFrame.from_records(list)

            for ornum, detail in dataset.fillna('NaN').groupby(
                    ['ormain__ornum', 'ormain__ordate', 'ormain__payee_name', 'ormain__particulars', 'status']):
                worksheet.write(row, col, ornum[0])
                worksheet.write(row, col + 1, ornum[1], formatdate)
                if ornum[4] == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, ornum[2])
                worksheet.write(row, col + 3, ornum[3])
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
                    if ornum[4] == 'C':
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


            filename = "unpostedortransactionlist.xlsx"

        elif report == '5':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Amount', bold)
            worksheet.write('E4', 'Cash in Bank', bold)
            worksheet.write('F4', 'Difference', bold)
            worksheet.write('G4', 'Output VAT', bold)
            worksheet.write('H4', 'Amount Due', bold)
            worksheet.write('I4', 'Status', bold)

            row = 4
            col = 0

            totalamount = 0
            amount = 0
            totalcashinbank = 0
            totaldiff = 0
            totaloutputvat = 0
            totalamountdue = 0
            for data in list:
                worksheet.write(row, col, data.ornum)
                worksheet.write(row, col + 1, data.ordate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)

                if data.status == 'C':
                    worksheet.write(row, col + 3, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 3, float(format(data.amount, '.2f')))
                    amount = data.amount

                worksheet.write(row, col + 4, float(format(data.cashinbank, '.2f')))
                worksheet.write(row, col + 5, float(format(data.diff, '.2f')))
                worksheet.write(row, col + 6, float(format(data.outputvat, '.2f')))
                worksheet.write(row, col + 7, float(format(data.amountdue, '.2f')))
                worksheet.write(row, col + 8, data.status)

                row += 1
                totalamount += amount
                totalcashinbank += data.cashinbank
                totaldiff += data.diff
                totaloutputvat += data.outputvat
                totalamountdue += data.amountdue


            worksheet.write(row, col + 2, 'Total')
            worksheet.write(row, col + 3, float(format(totalamount, '.2f')))
            worksheet.write(row, col + 4, float(format(totalcashinbank, '.2f')))
            worksheet.write(row, col + 5, float(format(totaldiff, '.2f')))
            worksheet.write(row, col + 6, float(format(totaloutputvat, '.2f')))
            worksheet.write(row, col + 7, float(format(totalamountdue, '.2f')))

            filename = "OfficialReceiptList.xlsx"
        elif report == '6':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Total Amount', bold)
            worksheet.write('E4', 'Debit Amount', bold)
            worksheet.write('F4', 'Credit Amount', bold)
            worksheet.write('G4', 'Variance', bold)
            worksheet.write('H4', 'Status', bold)

            row = 4
            col = 0

            totalamount = 0
            amount = 0
            totaldebit = 0
            totalcredit = 0
            totalvariance = 0


            for data in list:
                worksheet.write(row, col, data.ornum)
                worksheet.write(row, col + 1, data.ordate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)

                if data.status == 'C':
                    worksheet.write(row, col + 3, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 3, float(format(data.amount, '.2f')))
                    amount = data.amount

                worksheet.write(row, col + 4, float(format(data.debitamount, '.2f')))
                worksheet.write(row, col + 5, float(format(data.creditamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.totaldiff, '.2f')))
                worksheet.write(row, col + 7, data.status)

                row += 1
                totalamount += amount
                totaldebit += data.debitamount
                totalcredit += data.creditamount
                totalvariance += data.totaldiff


            worksheet.write(row, col + 2, 'Total')
            worksheet.write(row, col + 3, float(format(totalamount, '.2f')))
            worksheet.write(row, col + 4, float(format(totaldebit, '.2f')))
            worksheet.write(row, col + 5, float(format(totalcredit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalvariance, '.2f')))

            filename = "UnbalancedOfficialReceiptTransanctionList.xlsx"

        elif report == '7':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Payee', bold)

            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0

            totalamount = 0
            amount = 0
            for data in list:
                worksheet.write(row, col, data.ornum)
                worksheet.write(row, col + 1, data.ordate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)

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
            filename = "officialreceiptregister.xlsx"

        elif report == '8':
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Gov Status', bold)
            worksheet.write('D4', 'Payee/Particular', bold)
            worksheet.write('E4', 'Type', bold)
            worksheet.write('F4', 'AR / Revenue Debit', bold)
            worksheet.write('G4', 'AR / Revenue Credit', bold)
            worksheet.write('H4', 'Output VAT Debit', bold)
            worksheet.write('I4', 'Output VAT Credit', bold)
            worksheet.write('J4', 'VAT Rate', bold)

            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0

            for data in list:
                worksheet.write(row, col, data.ornum)
                worksheet.write(row, col + 1, data.ordate, formatdate)
                worksheet.write(row, col + 2, data.government)
                worksheet.write(row, col + 3, data.payee_name)
                worksheet.write(row, col + 4, data.ortype)
                worksheet.write(row, col + 5, float(format(data.arrdebitamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.arrcreditamount, '.2f')))
                worksheet.write(row, col + 7, float(format(data.outputvatdebitamount, '.2f')))
                worksheet.write(row, col + 8, float(format(data.outputvatcreditamount, '.2f')))
                worksheet.write(row, col + 9, data.outputvatrate)

                totalefodebit += data.arrdebitamount
                totalefocredit += data.arrcreditamount
                totalinputdebit += data.outputvatdebitamount
                totalinputcredit += data.outputvatcreditamount

                row += 1

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 7, float(format(totalinputdebit, '.2f')))
            worksheet.write(row, col + 8, float(format(totalinputcredit, '.2f')))

            filename = "ortransactionoutputvat.xlsx"

        elif report == '9':
            worksheet.write('A4', 'Payee/Particular', bold)
            worksheet.write('B4', 'Gov Status', bold)
            worksheet.write('C4', 'Type', bold)
            worksheet.write('D4', 'AR / Revenue Debit', bold)
            worksheet.write('E4', 'AR / Revenue Credit', bold)
            worksheet.write('F4', 'Output VAT Debit', bold)
            worksheet.write('G4', 'Output VAT Credit', bold)
            worksheet.write('H4', 'VAT Rate', bold)
            worksheet.write('I4', 'Address', bold)
            worksheet.write('J4', 'TIN', bold)

            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0

            for data in list:
                worksheet.write(row, col, data.payee_name)
                worksheet.write(row, col + 1, data.government)
                worksheet.write(row, col + 2, data.ortype)
                worksheet.write(row, col + 3, float(format(data.arrdebitamount, '.2f')))
                worksheet.write(row, col + 4, float(format(data.arrcreditamount, '.2f')))
                worksheet.write(row, col + 5, float(format(data.outputvatdebitamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.outputvatcreditamount, '.2f')))
                worksheet.write(row, col + 7, data.outputvatrate)
                worksheet.write(row, col + 8, data.address)
                worksheet.write(row, col + 9, data.tin)

                totalefodebit += data.arrdebitamount
                totalefocredit += data.arrcreditamount
                totalinputdebit += data.outputvatdebitamount
                totalinputcredit += data.outputvatcreditamount

                row += 1

            worksheet.write(row, col + 2, 'Total')
            worksheet.write(row, col + 3, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 4, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 5, float(format(totalinputdebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalinputcredit, '.2f')))

            filename = "ortransactionoutputvatsummary.xlsx"

        elif report == '10':
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Gov Status', bold)
            worksheet.write('D4', 'Payee/Particular', bold)
            worksheet.write('E4', 'Type', bold)
            worksheet.write('F4', 'Cash In Bank Debit', bold)
            worksheet.write('G4', 'Cash In Bank Credit', bold)
            worksheet.write('H4', 'Output VAT Debit', bold)
            worksheet.write('I4', 'Output VAT Credit', bold)
            worksheet.write('J4', 'VAT Rate', bold)

            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0

            for data in list:
                worksheet.write(row, col, data.ornum)
                worksheet.write(row, col + 1, data.ordate, formatdate)
                worksheet.write(row, col + 2, data.government)
                worksheet.write(row, col + 3, data.payee_name)
                worksheet.write(row, col + 4, data.ortype)
                worksheet.write(row, col + 5, float(format(data.arrdebitamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.arrcreditamount, '.2f')))
                worksheet.write(row, col + 7, '')
                worksheet.write(row, col + 8, '')
                worksheet.write(row, col + 9, '')

                totalefodebit += data.arrdebitamount
                totalefocredit += data.arrcreditamount
                totalinputdebit += data.outputvatdebitamount
                totalinputcredit += data.outputvatcreditamount

                row += 1

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 7, '')
            worksheet.write(row, col + 8, '')

            filename = "ortransactionwithoutoutputvat.xlsx"

        elif report == '11':
            worksheet.write('A4', 'Payee/Particular', bold)
            worksheet.write('B4', 'Gov Status', bold)
            worksheet.write('C4', 'Type', bold)
            worksheet.write('D4', 'Cash In Bank Debit', bold)
            worksheet.write('E4', 'Cash In Bank Credit', bold)
            worksheet.write('F4', 'Output VAT Debit', bold)
            worksheet.write('G4', 'Output VAT Credit', bold)
            worksheet.write('H4', 'VAT Rate', bold)
            worksheet.write('I4', 'Address', bold)
            worksheet.write('J4', 'TIN', bold)

            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0

            for data in list:
                worksheet.write(row, col, data.payee_name)
                worksheet.write(row, col + 1, data.government)
                worksheet.write(row, col + 2, data.ortype)
                worksheet.write(row, col + 3, float(format(data.arrdebitamount, '.2f')))
                worksheet.write(row, col + 4, float(format(data.arrcreditamount, '.2f')))
                worksheet.write(row, col + 5, '')
                worksheet.write(row, col + 6, '')
                worksheet.write(row, col + 7, '')
                worksheet.write(row, col + 8, data.address)
                worksheet.write(row, col + 9, data.tin)

                totalefodebit += data.arrdebitamount
                totalefocredit += data.arrcreditamount
                totalinputdebit += data.outputvatdebitamount
                totalinputcredit += data.outputvatcreditamount

                row += 1

            worksheet.write(row, col + 2, 'Total')
            worksheet.write(row, col + 3, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 4, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 5, '')
            worksheet.write(row, col + 6, '')

            filename = "ortransactionwithoutoutputvatsummary.xlsx"

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


def raw_query(type, company, dfrom, dto, ortype, artype, payee, collector, branch, product, adtype, wtax, vat, outputvat, bankaccount, status):
    #print type
    print "raw query"
    ''' Create query '''
    cursor = connection.cursor()

    conortype = ""
    conartype = ""
    conpayee = ""
    concollector = ""
    conbranch = ""
    conproduct = ""
    conadtype = ""
    conwtax = ""
    convat = ""
    conoutputvat = ""
    conbankaccount = ""
    constatus = ""

    if ortype != '':
        conortype = "AND m.ortype = '" +str(ortype)+ "'"
    if artype != '':
        conartype = "AND m.artype = '" + str(artype) + "'"
    if payee != 'null':
        conpayee = "AND m.payee_code = '" + str(payee) + "'"
    if branch != '':
        conbranch = "AND m.branch = '" + str(branch) + "'"
    if collector != '':
        concollector = "AND m.collector = '" + str(collector) + "'"
    if product != '':
        conproduct = "AND m.product = '" + str(product) + "'"
    if adtype != '':
        conadtype = "AND m.adtype = '" + str(adtype) + "'"
    if wtax != '':
        conwtax = "AND m.wtax = '" + str(wtax) + "'"
    if vat != '':
        convat = "AND m.vat = '" + str(vat) + "'"
    if outputvat != '':
        conoutputvat = "AND m.outputvattype = '" + str(outputvattype) + "'"
    if bankaccount != '':
        conbankaccount = "AND m.bankaccount = '" + str(bankaccount) + "'"
    if status != '':
        constatus = "AND m.status = '" + str(status) + "'"

    if type == 1:
        query = "SELECT m.id, m.ornum, m.ordate, IF(m.status = 'C', 0, m.amount) AS amount, m.payee_name, IFNULL(cash.total_amount, 0) AS cashinbank, IFNULL(ouput.total_amount, 0) AS outputvat, m.status, " \
                "(m.amount - IFNULL(cash.total_amount, 0)) AS diff, (m.amount - IFNULL(ouput.total_amount,0)) AS amountdue " \
                "FROM ormain AS m " \
                "LEFT OUTER JOIN (" \
                "   SELECT or_num, balancecode, chartofaccount_id, SUM(debitamount) AS total_amount " \
                "   FROM ordetail WHERE balancecode = 'D' AND chartofaccount_id = "+str(company.coa_cashinbank_id)+ " " \
                "   GROUP BY or_num" \
                ") AS cash ON cash.or_num = m.ornum " \
                "LEFT OUTER JOIN (" \
                "   SELECT or_num, balancecode, chartofaccount_id, SUM(creditamount) AS total_amount " \
                "   FROM ordetail WHERE balancecode = 'C' AND chartofaccount_id = "+str(company.coa_outputvat_id)+ " " \
                "   GROUP BY or_num " \
                ")AS ouput ON ouput.or_num = m.ornum " \
                "WHERE m.ordate >= '"+str(dfrom)+"' AND m.ordate <= '"+str(dto)+"' " \
                "AND (m.amount <> cash.total_amount OR cash.total_amount IS NULL) " \
                + str(conortype) + " " + str(conartype) + " " + str(conpayee) + " " + str(conbranch) + " "+ str(concollector) + " " + str(conproduct) + " " \
                + str(conadtype) + " " + str(conwtax) + " " + str(convat) + " " + str(conoutputvat) + " "+ str(conbankaccount) + " " + str(constatus) + " " \
                "ORDER BY m.ordate,  m.ornum"
    elif type == 2:
        query = "SELECT z.*, ABS(z.detaildiff + z.diff) AS totaldiff FROM (" \
                "SELECT m.id, m.ornum, m.ordate, m.payee_name, IF(m.status = 'C', 0, m.amount) AS amount, m.status, IFNULL(debit.total_amount, 0) AS debitamount, IFNULL(credit.total_amount, 0) AS creditamount, " \
                "(IFNULL(debit.total_amount, 0) - IFNULL(credit.total_amount, 0)) AS detaildiff, (m.amount - IFNULL(debit.total_amount, 0)) AS diff " \
                "FROM ormain AS m " \
                "LEFT OUTER JOIN ( " \
                "   SELECT or_num, balancecode, chartofaccount_id, SUM(debitamount) AS total_amount " \
                "   FROM ordetail WHERE balancecode = 'D' " \
                "   GROUP BY or_num " \
                ") AS debit ON debit.or_num = m.ornum	 " \
                "LEFT OUTER JOIN ( " \
                "   SELECT or_num, balancecode, chartofaccount_id, SUM(creditamount) AS total_amount " \
                "   FROM ordetail WHERE balancecode = 'C' " \
                "   GROUP BY or_num " \
                ") AS credit ON credit.or_num = m.ornum	" \
                "WHERE m.ordate >= '"+str(dfrom)+"' AND m.ordate <= '"+str(dto)+"' " \
                + str(conortype) + " " + str(conartype) + " " + str(conpayee) + " " + str(conbranch) + " " + str(concollector) + " " + str(conproduct) + " " \
                + str(conadtype) + " " + str(conwtax) + " " + str(convat) + " " + str(conoutputvat) + " " + str(conbankaccount) + " " + str(constatus) + " " \
                "AND m.status != 'C' ORDER BY m.ordate,  m.ornum) AS z WHERE z.detaildiff != 0 OR z.diff != 0;"
        #print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

@csrf_exempt
def gopost(request):

    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        release = Ormain.objects.filter(pk__in=ids).update(orstatus='R',
                                                           releaseby=User.objects.get(pk=request.user.id),
                                                           releasedate= str(datetime.datetime.now()),
                                                        responsedate = str(datetime.datetime.now())
        )

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def goapprove(request):

    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        release = Ormain.objects.filter(pk__in=ids).update(orstatus='A',
                                                        responsedate = str(datetime.datetime.now()),
                                                        approverremarks = 'Batch Approved',
                                                        actualapprover = User.objects.get(pk=request.user.id),
                                                        designatedapprover = User.objects.get(pk=request.user.id)
        )

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def gounpost(request):
    if request.method == 'POST':
        approval = Ormain.objects.get(pk=request.POST['id'])
        if (approval.orstatus == 'R' and approval.status != 'O'):
            approval.orstatus = 'A'
            approval.save()
            data = {'status': 'success'}

            # Save Activity Logs
            Activitylogs.objects.create(
                user_id=request.user.id,
                username=request.user,
                remarks='Unpost OR Transaction #' + str(approval.ornum)
            )
        else:
            data = {'status': 'error'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def searchforposting(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Ormain.objects.filter(isdeleted=0,status='A',orstatus='A').order_by('ornum', 'ordate')
        if dfrom != '':
            q = q.filter(ordate__gte=dfrom)
        if dto != '':
            q = q.filter(ordate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('officialreceipt/postingresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def searchforapproval(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Ormain.objects.filter(isdeleted=0,status='A',orstatus='F').order_by('ordate', 'ornum')
        if dfrom != '':
            q = q.filter(ordate__gte=dfrom)
        if dto != '':
            q = q.filter(ordate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('officialreceipt/approvalresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def approve(request):
    if request.method == 'POST':

        approval = Ormain.objects.get(pk=request.POST['id'])

        details = Ordetail.objects.filter(ormain_id=approval.id).order_by('item_counter')
        print details

        msg = ""
        msgchartname = ""
        msgchart = ""
        error = 0
        totalerror = 0
        for item in details:

            chartvalidate = Chartofaccount.objects.get(pk=item.chartofaccount_id)

            if chartvalidate.bankaccount_enable == 'Y':
                if item.bankaccount_id is None:
                    error += 1
                    msg += "Bank is Needed "

            if chartvalidate.department_enable == 'Y':
                if item.department_id is None:
                    error += 1
                    msg += "Department is Needed "
                ## check expense
                print chartvalidate.accountcode
                if chartvalidate.accountcode[0:1] == '5':
                    print "expense ako"
                    dept = Department.objects.get(pk=item.department_id)
                    deptchart = Chartofaccount.objects.filter(isdeleted=0, status='A',
                                                              pk=dept.expchartofaccount_id).first()

                    if chartvalidate.accountcode[0:2] != deptchart.accountcode[0:2]:
                        error += 1
                        msg += "Expense code did not match with the department code "

            if chartvalidate.supplier_enable == 'Y':

                print chartvalidate.setup_supplier
                if chartvalidate.setup_supplier is None:
                    if item.supplier_id is None:
                        error += 1
                        msg += "Supplier is Needed "

            if chartvalidate.customer_enable == 'Y':
                print chartvalidate.setup_customer
                if chartvalidate.setup_customer is None:
                    if item.customer_id is None:
                        error += 1
                        msg += "Customer is Needed "

            if chartvalidate.branch_enable == 'Y':
                if item.branch_id is None:
                    error += 1
                    msg += "Branch is Needed "

            if chartvalidate.unit_enable == 'Y':
                if item.unit_id is None:
                    error += 1
                    msg += "Unit is Needed "

            if chartvalidate.inputvat_enable == 'Y':
                if item.inputvat_id is None:
                    error += 1
                    msg += "Input VAT is Needed "

            if chartvalidate.outputvat_enable == 'Y':
                if item.outputvat_id is None:
                    error += 1
                    msg += "Output VAT is Needed "

            if chartvalidate.vat_enable == 'Y':
                if item.vat_id is None:
                    error += 1
                    msg += "VAT is Needed "

            if chartvalidate.wtax_enable == 'Y':
                if item.wtax_id is None:
                    error += 1
                    msg += "WTAX is Needed "

            if chartvalidate.ataxcode_enable == 'Y':
                if item.ataxcode_id is None:
                    error += 1
                    msg += "ATAX is Needed "

            totalerror += error
            if error > 0:
                msgchartname = " Chart of Account: " + str(chartvalidate) + " "
                ## Double Validation
                msgchart += str(msgchartname) + " " + str(msg)
                msg = ""
                msgchartname = ""
                error = 0
            # print error
            # print msg

        if totalerror > 0:
            data = {'status': 'error', 'msg': msgchart}
            return JsonResponse(data)
        else:
            if (approval.orstatus != 'R' and approval.status != 'O'):
                approval.orstatus = 'A'
                approval.responsedate = str(datetime.datetime.now())
                approval.approverremarks = str(approval.approverremarks) + ';' + 'Approved'
                approval.actualapprover = User.objects.get(pk=request.user.id)
                approval.save()
                data = {'status': 'success'}

                # Save Activity Logs
                Activitylogs.objects.create(
                    user_id=request.user.id,
                    username=request.user,
                    remarks='Aproved OR Transaction #' + str(approval.ornum)
                )
            else:
                data = {'status': 'error'}

            return JsonResponse(data)


    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def disapprove(request):
    if request.method == 'POST':
        approval = Ormain.objects.get(pk=request.POST['id'])
        if (approval.orstatus != 'R' and approval.status != 'O'):
            approval.orstatus = 'D'
            approval.responsedate = str(datetime.datetime.now())
            approval.approverremarks = str(approval.approverremarks) +';'+ request.POST['reason']
            approval.actualapprover = User.objects.get(pk=request.user.id)
            approval.save()
            data = {'status': 'success'}

            # Save Activity Logs
            Activitylogs.objects.create(
                user_id=request.user.id,
                username=request.user,
                remarks='Disaproved OR Transaction #' + str(approval.ornum)
            )
        else:
            data = {'status': 'error'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

def query_orwithoutputvatsummary(dfrom, dto, orlist, arr):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    output = 320
    if not orlist:
        orlist = '0'

    query = "SELECT m.ornum, m.ordate, m.payee_name, m.particulars, ort.code AS ortype, m.government, m.payee_code, " \
            "CONCAT(IFNULL(m.add1, ''), ' ', IFNULL(m.add2, ''), ' ', IFNULL(m.add3, '')) AS address, m.tin, " \
            "SUM(IFNULL(arr.debitamount, 0)) AS arrdebitamount, SUM(IFNULL(arr.creditamount, 0)) AS arrcreditamount, " \
            "SUM(IFNULL(outputvat.debitamount, 0)) AS outputvatdebitamount, SUM(IFNULL(outputvat.creditamount, 0)) AS outputvatcreditamount," \
            "ROUND((SUM(IFNULL(outputvat.debitamount, 0)) - SUM(IFNULL(outputvat.creditamount, 0))) / (SUM(IFNULL(arr.debitamount, 0)) - SUM(IFNULL(arr.creditamount, 0))) * 100) AS outputvatrate " \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ortype AS ort ON ort.id = m.ortype_id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.ormain_id, d.or_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM ordetail AS d " \
            "WHERE d.ormain_id IN ("+str(orlist)+") " \
            "AND d.chartofaccount_id IN ("+str(arr)+") " \
            "GROUP BY d.ormain_id " \
            "ORDER BY d.or_num, d.or_date " \
            ") AS arr ON arr.ormain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.ormain_id, d.or_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM ordetail AS d " \
            "WHERE d.ormain_id IN ("+str(orlist)+") " \
            "AND d.chartofaccount_id = "+str(output)+" " \
            "GROUP BY d.ormain_id " \
            "ORDER BY d.or_num, d.or_date " \
            ") AS outputvat ON outputvat.ormain_id = m.id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            "AND m.orstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+str(orlist)+") " \
            "GROUP BY m.payee_code, m.payee_name ORDER BY m.payee_name, ort.code, m.ornum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_orwithoutputvat(dfrom, dto, orlist, arr):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    output = 320
    if not orlist:
        orlist = '0'

    query = "SELECT m.ornum, m.ordate, m.payee_name, m.particulars, ort.code AS ortype, m.government, " \
            "IFNULL(arr.debitamount, 0) AS arrdebitamount, IFNULL(arr.creditamount, 0) AS arrcreditamount, " \
            "IFNULL(outputvat.debitamount, 0) AS outputvatdebitamount, IFNULL(outputvat.creditamount, 0) AS outputvatcreditamount, " \
            "ROUND((IFNULL(outputvat.debitamount, 0) - IFNULL(outputvat.creditamount, 0)) / (IFNULL(arr.debitamount, 0) - IFNULL(arr.creditamount, 0)) * 100) AS outputvatrate " \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ortype AS ort ON ort.id = m.ortype_id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.ormain_id, d.or_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM ordetail AS d " \
            "WHERE d.ormain_id IN ("+str(orlist)+") " \
            "AND d.chartofaccount_id IN ("+str(arr)+") " \
            "GROUP BY d.ormain_id " \
            "ORDER BY d.or_num, d.or_date " \
            ") AS arr ON arr.ormain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.ormain_id, d.or_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM ordetail AS d " \
            "WHERE d.ormain_id IN ("+str(orlist)+") " \
            "AND d.chartofaccount_id = "+str(output)+" " \
            "GROUP BY d.ormain_id " \
            "ORDER BY d.or_num, d.or_date " \
            ") AS outputvat ON outputvat.ormain_id = m.id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            "AND m.orstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+str(orlist)+") " \
            "ORDER BY m.payee_name, ort.code, m.ornum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_ornooutputvat(dfrom, dto, orlist, arr):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    cashinbank = 30
    if not orlist:
        orlist = '0'

    query = "SELECT m.ornum, m.ordate, m.payee_name, m.particulars, ort.code AS ortype, m.government, " \
            "IFNULL(arr.debitamount, 0) AS arrdebitamount, IFNULL(arr.creditamount, 0) AS arrcreditamount, " \
            "IFNULL(outputvat.debitamount, 0) AS outputvatdebitamount, IFNULL(outputvat.creditamount, 0) AS outputvatcreditamount, " \
            "ROUND((IFNULL(outputvat.debitamount, 0) - IFNULL(outputvat.creditamount, 0)) / (IFNULL(arr.debitamount, 0) - IFNULL(arr.creditamount, 0)) * 100) AS outputvatrate " \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ortype AS ort ON ort.id = m.ortype_id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.ormain_id, d.or_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM ordetail AS d " \
            "WHERE d.ormain_id IN ("+str(orlist)+") " \
            "AND d.chartofaccount_id = "+str(cashinbank)+" " \
            "GROUP BY d.ormain_id " \
            "ORDER BY d.or_num, d.or_date " \
            ") AS arr ON arr.ormain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.ormain_id, d.or_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM ordetail AS d " \
            "WHERE d.ormain_id IN ("+str(orlist)+") " \
            "AND d.chartofaccount_id = "+str(cashinbank)+" " \
            "GROUP BY d.ormain_id " \
            "ORDER BY d.or_num, d.or_date " \
            ") AS outputvat ON outputvat.ormain_id = m.id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            "AND m.orstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+str(orlist)+") " \
            "ORDER BY m.payee_name, ort.code, m.ornum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_ornooutputvatsummary(dfrom, dto, orlist, arr):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    cashinbank = 30
    if not orlist:
        orlist = '0'

    query = "SELECT m.ornum, m.ordate, m.payee_name, m.particulars, ort.code AS ortype, m.government, m.payee_code, " \
            "CONCAT(IFNULL(m.add1, ''), ' ', IFNULL(m.add2, ''), ' ', IFNULL(m.add3, '')) AS address, m.tin, " \
            "SUM(IFNULL(arr.debitamount, 0)) AS arrdebitamount, SUM(IFNULL(arr.creditamount, 0)) AS arrcreditamount, " \
            "SUM(IFNULL(outputvat.debitamount, 0)) AS outputvatdebitamount, SUM(IFNULL(outputvat.creditamount, 0)) AS outputvatcreditamount," \
            "ROUND((SUM(IFNULL(outputvat.debitamount, 0)) - SUM(IFNULL(outputvat.creditamount, 0))) / (SUM(IFNULL(arr.debitamount, 0)) - SUM(IFNULL(arr.creditamount, 0))) * 100) AS outputvatrate " \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ortype AS ort ON ort.id = m.ortype_id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.ormain_id, d.or_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM ordetail AS d " \
            "WHERE d.ormain_id IN ("+str(orlist)+") " \
            "AND d.chartofaccount_id = "+str(cashinbank)+" " \
            "GROUP BY d.ormain_id " \
            "ORDER BY d.or_num, d.or_date " \
            ") AS arr ON arr.ormain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.ormain_id, d.or_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM ordetail AS d " \
            "WHERE d.ormain_id IN ("+str(orlist)+") " \
            "AND d.chartofaccount_id = "+str(cashinbank)+" " \
            "GROUP BY d.ormain_id " \
            "ORDER BY d.or_num, d.or_date " \
            ") AS outputvat ON outputvat.ormain_id = m.id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            "AND m.orstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+str(orlist)+") " \
            "GROUP BY m.payee_code, m.payee_name ORDER BY m.payee_name, ort.code, m.ornum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def getORList(dfrom, dto):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    outputvat = 320 # 2146000000 OUTPUT VAT PAYABLE

    query = "SELECT m.ornum, m.ordate, m.payee_name, m.particulars, " \
            "d.balancecode, d.chartofaccount_id, d.ormain_id " \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ordetail AS d ON d.ormain_id = m.id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            "AND m.orstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND d.chartofaccount_id = "+str(outputvat)+" " \
            "ORDER BY m.ornum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    list = ''
    for r in result:
        list += str(r.ormain_id) + ','

    return list[:-1]

def getORNoOutputVatList(dfrom, dto):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    outputvat = 320 # 2146000000 OUTPUT VAT PAYABLE

    query = "SELECT m.ornum, m.ordate, m.payee_name, m.particulars, " \
            "d.balancecode, d.chartofaccount_id, d.ormain_id " \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ordetail AS d ON d.ormain_id = m.id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            "AND m.orstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id NOT IN (" \
            "SELECT DISTINCT m.id " \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ordetail AS d ON d.ormain_id = m.id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            "AND d.chartofaccount_id = "+str(outputvat)+") " \
            "ORDER BY m.ornum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    list = ''
    for r in result:
        list += str(r.ormain_id) + ','

    return list[:-1]


def getARR():
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()


    query = "SELECT id, accountcode, description, main, clas, item, SUBSTR(sub, 1, 2) AS sub " \
            "FROM chartofaccount  " \
            "WHERE (main = 1 AND clas = 1 AND item = 2 AND cont = 1) OR (main = 4 AND clas = 1 AND item = 1)"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    list = ''
    for r in result:
        list += str(r.id) + ','

    return list[:-1]
    #return result

def upload(request):
    folder = 'media/orupload/'
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        id = request.POST['dataid']
        fs = FileSystemStorage(location=folder)  # defaults to   MEDIA_ROOT
        filename = fs.save(myfile.name, myfile)

        upl = Orupload(ormain_id=id, filename=filename, enterby=request.user, modifyby=request.user)
        upl.save()

        uploaded_file_url = fs.url(filename)
        return HttpResponseRedirect('/officialreceipt/' + str(id) )
    return HttpResponseRedirect('/officialreceipt/' + str(id) )


@csrf_exempt
def filedelete(request):

    if request.method == 'POST':

        id = request.POST['id']
        fileid = request.POST['fileid']

        Orupload.objects.filter(id=fileid).delete()

        return HttpResponseRedirect('/officialreceipt/' + str(id) )

    return HttpResponseRedirect('/officialreceipt/' + str(id) )