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
    fields = ['ordate', 'ortype', 'orsource', 'collector', 'branch', 'payee_type', 'amount', 'amountinwords', 'vat',
              'wtax', 'outputvattype', 'deferredvat', 'product', 'bankaccount', 'particulars', 'government',
              'designatedapprover', 'remarks']

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
        context['agency'] = Customer.objects.filter(isdeleted=0).order_by('code')
        context['client'] = Customer.objects.filter(isdeleted=0).order_by('code')
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

        self.object.vatrate = Vat.objects.get(pk=int(self.request.POST['vat'])).rate
        self.object.wtaxrate = Wtax.objects.get(pk=int(self.request.POST['wtax'])).rate

        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        non_vat_amount = self.object.amount / (1 + (self.object.vatrate / 100) - (self.object.wtaxrate / 100))
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

        self.object.vatamount = non_vat_amount * (self.object.vatrate / 100)
        self.object.wtaxamount = non_vat_amount * (self.object.wtaxrate / 100)
        self.object.totalsale = non_vat_amount + self.object.vatamount + self.object.wtaxamount
        self.object.save()

        # save ordetailtemp to ordetail
        # source = 'ordetailtemp'
        # mainid = self.object.id
        # num = self.object.ornum
        # secretkey = self.request.POST['secretkey']
        # savedetail(source, mainid, num, secretkey, self.request.user)

        return HttpResponseRedirect('/officialreceipt/')
        # return HttpResponseRedirect('/officialreceipt/' + str(self.object.id) + '/update')


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
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Ormain
    template_name = 'officialreceipt/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'] = reportresultquery(self.request)

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
    report_total = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            report_type = "OR Summary"
        else:
            report_type = "OR Detailed"    
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
        if request.COOKIES.get('rep_f_government_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_government_' + request.resolver_match.app_name))
            query = query.filter(government=str(key_data))

        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(vat=int(key_data))
        if request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name))
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
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        query = Ordetail.objects.all().filter(isdeleted=0)

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
        if request.COOKIES.get('rep_f_government_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_government_' + request.resolver_match.app_name))
            query = query.filter(ormain__government=str(key_data))

        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(ormain__vat=int(key_data))
        if request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name))
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
            report_type = "OR Acctg Entry - Summary"

            query = query.values('chartofaccount__accountcode',
                                 'chartofaccount__title',
                                 'chartofaccount__description',
                                 'bankaccount__accountnumber',
                                 'department__departmentname',
                                 'employee__firstname',
                                 'employee__lastname',
                                 'supplier__name',
                                 'customer__name',
                                 'unit__description',
                                 'branch__description',
                                 'product__description',
                                 'inputvat__description',
                                 'outputvat__description',
                                 'vat__description',
                                 'wtax__description',
                                 'ataxcode__code',
                                 'balancecode')\
                         .annotate(Sum('debitamount'), Sum('creditamount'))\
                         .order_by('-balancecode',
                                   '-chartofaccount__accountcode',
                                   'bankaccount__accountnumber',
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
                                   'ataxcode__code')
        else:
            report_type = "OR Acctg Entry - Detailed"

            query = query.annotate(Sum('debitamount'), Sum('creditamount')).order_by('-balancecode',
                                                                                     '-chartofaccount__accountcode',
                                                                                     'bankaccount__accountnumber',
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

    return query, report_type, report_total


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
    queryset, report_type, report_total = reportresultquery(request)
    report_type = report_type if report_type != '' else 'OR Report'
    worksheet = workbook.add_worksheet(report_type)
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
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 14
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
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        worksheet.merge_range('A1:A2', 'Chart of Account', bold)
        worksheet.merge_range('B1:N1', 'Details', bold_center)
        worksheet.merge_range('O1:O2', 'Debit', bold_right)
        worksheet.merge_range('P1:P2', 'Credit', bold_right)
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
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            str_firstname = obj['employee__firstname'] if obj['employee__firstname'] is not None else ''
            str_lastname = obj['employee__lastname'] if obj['employee__lastname'] is not None else ''

            data = [
                obj['chartofaccount__accountcode'] + " - " + obj['chartofaccount__description'],
                obj['bankaccount__accountnumber'],
                obj['department__departmentname'],
                str_firstname + " " + str_lastname,
                obj['supplier__name'],
                obj['customer__name'],
                obj['unit__description'],
                obj['branch__description'],
                obj['product__description'],
                obj['inputvat__description'],
                obj['outputvat__description'],
                obj['vat__description'],
                obj['wtax__description'],
                obj['ataxcode__code'],
                obj['debitamount__sum'],
                obj['creditamount__sum'],
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
            str_firstname = obj.employee.firstname if obj.employee is not None else ''
            str_lastname = obj.employee.lastname if obj.employee is not None else ''

            data = [
                obj.chartofaccount.accountcode + " - " + obj.chartofaccount.description,
                obj.bankaccount.accountnumber if obj.bankaccount is not None else '',
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
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        data = [
            "", "", "", "", "", "", "", "", "", "", "", "", "",
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
    response['Content-Disposition'] = "attachment; filename="+report_type+".xlsx"
    return response
