from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from adtype.models import Adtype
from ataxcode.models import Ataxcode
from bankbranchdisburse.models import Bankbranchdisburse
from branch.models import Branch
from circulationproduct.models import Circulationproduct
from companyparameter.models import Companyparameter
from cvsubtype.models import Cvsubtype
from operationalfund.models import Ofmain, Ofitem, Ofdetail
from replenish_pcv.models import Reppcvmain, Reppcvdetail
from supplier.models import Supplier
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from . models import Ormain, Ordetail, Ordetailtemp, Ordetailbreakdown, Ordetailbreakdowntemp
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
        savedetail(source, mainid, num, secretkey, self.request.user)

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
        updatedetail(source, mainid, num, secretkey, self.request.user)

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
    template_name = 'officialreceipt/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['ortype'] = Ortype.objects.filter(isdeleted=0).order_by('description')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['agency'] = Customer.objects.filter(isdeleted=0).order_by('code')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        context['unit'] = Unit.objects.filter(isdeleted=0).order_by('code')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('code')
        context['outputvat'] = Outputvat.objects.filter(isdeleted=0).order_by('code')
        context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['client'] = Customer.objects.filter(isdeleted=0).order_by('code')
        context['agent'] = Agent.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['product'] = Product.objects.filter(isdeleted=0).order_by('code')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['approver'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')

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
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedor = Ormain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        printedor.print_ctr += 1
        printedor.save()
        return context
