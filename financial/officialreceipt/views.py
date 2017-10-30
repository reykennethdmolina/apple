from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from ataxcode.models import Ataxcode
from bankbranchdisburse.models import Bankbranchdisburse
from branch.models import Branch
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
from vat.models import Vat
from wtax.models import Wtax
from django.template.loader import render_to_string
from easy_pdf.views import PDFTemplateView
import datetime
from pprint import pprint
from django.utils.dateformat import DateFormat
from utils.mixins import ReportContentMixin
from collector.models import Collector
from agent.models import Agent
from product.models import Product
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
                                 Q(customer_name__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query

    # def get_context_data(self, **kwargs):
    #     context = super(AjaxListView, self).get_context_data(**kwargs)
    #
    #     # data for lookup
    #     context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
    #     context['cvsubtype'] = Cvsubtype.objects.filter(isdeleted=0).order_by('pk')
    #     context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
    #     context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
    #     context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
    #     context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
    #     context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
    #     context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
    #     context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
    #     context['pk'] = 0
    #     # data for lookup
    #
    #     return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Ormain
    template_name = 'officialreceipt/create.html'
    fields = ['ordate', 'ortype', 'orsource', 'collector', 'branch', 'amount', 'amountinwords', 'vat',
              'wtax', 'outputvattype', 'deferredvat', 'product', 'bankaccount', 'particulars', 'government',
              'remarks']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('officialreceipt.add_ormain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['agency'] = Customer.objects.filter(isdeleted=0).order_by('code')   # add filter customer type
        context['client'] = Customer.objects.filter(isdeleted=0).order_by('code')   # add filter customer type
        context['agent'] = Agent.objects.filter(isdeleted=0).order_by('code')
        context['product'] = Product.objects.filter(isdeleted=0).order_by('code')

        # data for lookup
        context['ortype'] = Ortype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        # data for lookup

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        year = str(form.cleaned_data['ordate'].year)
        yearqs = Ormain.objects.filter(ornum__startswith=year)

        if yearqs:
            ornumlast = yearqs.latest('ornum')
            latestornum = str(ornumlast)
            print "latest: " + latestornum

            ornum = year
            last = str(int(latestornum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                ornum += '0'
            ornum += last
        else:
            ornum = year + '000001'

        print 'ornum: ' + ornum
        self.object.ornum = ornum
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
        self.object.product_code = self.object.product.code
        self.object.product_name = self.object.product.description
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
              'wtax', 'outputvattype', 'deferredvat', 'product', 'bankaccount', 'particulars', 'government',
              'remarks', 'vatrate', 'wtaxrate', 'payee_type', 'orsource']

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
        # context['agency'] = Customer.objects.filter(isdeleted=0).order_by('code')  # add filter customer type
        # context['client'] = Customer.objects.filter(isdeleted=0).order_by('code')  # add filter customer type
        # context['agent'] = Agent.objects.filter(isdeleted=0).order_by('code')
        context['product'] = Product.objects.filter(isdeleted=0).order_by('code')
        context['ornum'] = self.object.ornum

        # data for lookup
        context['ortype'] = Ortype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
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

        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['ordate', 'amount', 'amountinwords', 'deferredvat', 'vatrate', 'wtaxrate',
                                        'particulars', 'government', 'remarks', 'bankaccount', 'branch', 'collector',
                                        'ortype', 'vat', 'wtax', 'outputvattype', 'agency', 'agent', 'client',
                                        'orsource', 'payee_code', 'payee_name', 'payee_type', 'product', 'modifyby',
                                        'modifydate'])

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
        self.object.product_code = self.object.product.code
        self.object.product_name = self.object.product.description
        self.object.save(update_fields=['vatamount', 'wtaxamount', 'vatablesale', 'vatexemptsale', 'vatzeroratedsale',
                                        'totalsale', 'collector_code', 'collector_name', 'product_code',
                                        'product_name'])

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



