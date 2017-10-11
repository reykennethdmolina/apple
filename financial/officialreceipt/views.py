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
from . models import Ormain, Oritem, Oritemtemp, Ordetail, Ordetailtemp, Ordetailbreakdown, Ordetailbreakdowntemp
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
    fields = ['ordate', 'ortype', 'orsubtype', 'collector', 'branch', 'customer', 'customer_address1',
              'customer_address2', 'customer_address3', 'customer_telno1', 'customer_telno2', 'customer_celno',
              'customer_faxno', 'customer_tin', 'customer_zipcode', 'amount', 'amountinwords', 'outputvattype',
              'deferredvat', 'vat', 'wtax', 'currency', 'fxrate', 'bankaccount', 'particulars', 'comments',
              'government', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('officialreceipt.add_ormain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['collector'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')

        # data for lookup
        context['ortype'] = Ortype.objects.filter(isdeleted=0).order_by('pk')
        context['orsubtype'] = Orsubtype.objects.filter(isdeleted=0).order_by('pk')
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
        self.object.customer = Customer.objects.get(pk=int(self.request.POST['customer']))
        self.object.customer_code = self.object.customer.code
        self.object.customer_name = self.object.customer.name
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

        # save oritemtemp to oritem

        # delete oritemtemp

        # save ordetailtemp to ordetail
        # source = 'ordetailtemp'
        # mainid = self.object.id
        # num = self.object.ornum
        # secretkey = self.request.POST['secretkey']
        # savedetail(source, mainid, num, secretkey, self.request.user)

        return HttpResponseRedirect('/officialreceipt/')
        # return HttpResponseRedirect('/officialreceipt/' + str(self.object.id) + '/update')


@csrf_exempt
def saveitem(request):
    if request.method == 'POST':
        if request.POST['id_itemtemp'] != '':  # if item already exists, update
            itemtemp = Oritemtemp.objects.get(pk=int(request.POST['id_itemtemp']))
        else:  # if item does not exist, create
            itemtemp = Oritemtemp()
            itemtemp.enterby = request.user
            itemtemp.enterdate = datetime.datetime.now()
        itemtemp.item_counter = request.POST['item_counter']
        itemtemp.secretkey = request.POST['secretkey']
        itemtemp.paytype = request.POST['paytype']
        itemtemp.amount = request.POST['amount']
        itemtemp.modifyby = request.user
        itemtemp.modifydate = datetime.datetime.now()

        paytype = Paytype.objects.get(pk=int(request.POST['paytype']))
        if paytype.code == 'CHK':  # if paytype is CHECK
            itemtemp.bank = request.POST['bank']
            itemtemp.bankbranch = request.POST['bankbranch']
            itemtemp.checknum = request.POST['checknum']
            itemtemp.checkdate = request.POST['checkdate']
        elif paytype.code == 'CC':  # if paytype is CREDIT CARD
            itemtemp.creditcard = request.POST['creditcard']
            itemtemp.creditcardnum = request.POST['creditcardnum']
            itemtemp.authnum = request.POST['authnum']
            itemtemp.expirydate = request.POST['expirydate']
        elif paytype.code == 'EXD':  # if paytype is EXDEAL
            itemtemp.remarks = request.POST['remarks']

        itemtemp.save()
        data = {
            'status': 'success',
            'itemtempid': itemtemp.pk,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)
