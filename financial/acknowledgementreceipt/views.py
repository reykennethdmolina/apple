from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from branch.models import Branch
from companyparameter.models import Companyparameter
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from . models import Armain, Ardetail, Ardetailtemp, Ardetailbreakdown, Ardetailbreakdowntemp, Aritem, Aritemtemp
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from bankaccount.models import Bankaccount
from currency.models import Currency
from customer.models import Customer
from arsubtype.models import Arsubtype
from artype.models import Artype
from chartofaccount.models import Chartofaccount
from employee.models import Employee
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
from bank.models import Bank
from bankbranch.models import Bankbranch
from collector.models import Collector
from paytype.models import Paytype
from agent.models import Agent
from product.models import Product
import decimal


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Armain
    template_name = 'acknowledgementreceipt/index.html'
    page_template = 'acknowledgementreceipt/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Armain.objects.all().filter(isdeleted=0)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(arnum__icontains=keysearch) |
                                 Q(ardate__icontains=keysearch) |
                                 Q(payor_name__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Armain
    template_name = 'acknowledgementreceipt/create.html'
    fields = ['ardate', 'artype', 'collector', 'branch', 'amount', 'amountinwords', 'depositorybank', 'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('acknowledgementreceipt.add_armain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['paytype'] = Paytype.objects.filter(isdeleted=0).order_by('pk')
        context['bank'] = Bank.objects.filter(isdeleted=0).order_by('code')

        # data for lookup
        context['artype'] = Artype.objects.filter(isdeleted=0).order_by('pk')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['arsubtype'] = Arsubtype.objects.filter(isdeleted=0)
        context['depositorybank'] = Bankaccount.objects.filter(isdeleted=0).order_by('bank__code')
        # data for lookup

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        year = str(form.cleaned_data['ardate'].year)
        yearqs = Armain.objects.filter(arnum__startswith=year)

        if yearqs:
            arnumlast = yearqs.latest('arnum')
            latestarnum = str(arnumlast)
            print "latest: " + latestarnum

            arnum = year
            last = str(int(latestarnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                arnum += '0'
            arnum += last
        else:
            arnum = year + '000001'

        print 'arnum: ' + arnum
        self.object.arnum = arnum

        if self.object.artype.code.startswith('AOE'):
            self.object.payor = Employee.objects.get(pk=int(self.request.POST['payor_employee']))
            self.object.payor_code = self.object.payor.code
            self.object.payor_name = (self.object.payor.firstname + ' ' + self.object.payor.lastname).upper()
        else:
            self.object.payor_code = 'NONTRADE'
            self.object.payor_name = self.request.POST['payor_others'].upper()

        self.object.arsubtype = Arsubtype.objects.get(
            pk=int(self.request.POST['arsubtype'])) if self.object.artype.code == 'NT' else None

        self.object.collector_code = self.object.collector.code
        self.object.collector_name = self.object.collector.name
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        # if Ordetailtemp.objects.filter(secretkey=self.request.POST['secretkey']).count() == 0:
        #     addcashinbank(self.request.POST['secretkey'], self.object.totalsale, self.request.user)
        #
        # # save ordetailtemp to ordetail
        # source = 'ordetailtemp'
        # mainid = self.object.id
        # num = self.object.ornum
        # secretkey = self.request.POST['secretkey']
        # savedetail(source, mainid, num, secretkey, self.request.user)

        return HttpResponseRedirect('/acknowledgementreceipt/')
        # return HttpResponseRedirect('/acknowledgementreceipt/' + str(self.object.id) + '/update')


@csrf_exempt
def savepaymentdetailtemp(request):
    if request.method == 'POST':
        if request.POST['id_itemtemp'] != '':  # if item already exists (update)
            itemtemp = Aritemtemp.objects.get(pk=int(request.POST['id_itemtemp']))
        else:  # if item does not exist (create)
            itemtemp = Aritemtemp()
            itemtemp.enterby = request.user
        itemtemp.item_counter = request.POST['itemno']
        itemtemp.secretkey = request.POST['secretkey']
        itemtemp.paytype = request.POST['paytype']
        itemtemp.amount = request.POST['amount'].replace(',', '')
        itemtemp.modifyby = request.user

        if Paytype.objects.get(pk=int(itemtemp.paytype)).code == 'CH':
            itemtemp.bank = request.POST['bank']
            itemtemp.bankbranch = request.POST['bankbranch']
            itemtemp.num = request.POST['num']
            itemtemp.date = request.POST['date']
        elif Paytype.objects.get(pk=int(itemtemp.paytype)).code == 'CC':
            itemtemp.num = request.POST['num']
            itemtemp.authnum = request.POST['authnum']
            itemtemp.date = request.POST['date']
        elif Paytype.objects.get(pk=int(itemtemp.paytype)).code == 'EX':
            itemtemp.remarks = request.POST['remarks']

        itemtemp.save()
        data = {
            'status': 'success',
            'id': itemtemp.pk,
            'item_counter': itemtemp.item_counter,
            'paytype': Paytype.objects.get(pk=int(itemtemp.paytype)).description,
            'amount': itemtemp.amount,
            'bank': Bank.objects.get(pk=int(itemtemp.bank)).code + ' ' +
                    Bankbranch.objects.get(pk=int(itemtemp.bankbranch)).description if itemtemp.bank and itemtemp.bankbranch else ' - ',
            'number': itemtemp.num if itemtemp.num else ' - ',
            'date': itemtemp.date if itemtemp.date else ' - ',
            'authnum': itemtemp.authnum if itemtemp.authnum else ' - ',
            'remarks': itemtemp.remarks if itemtemp.remarks else ' - ',
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def deletepaymentdetailtemp(request):
    if request.method == 'POST':
        itemtemptodelete = Aritemtemp.objects.get(pk=request.POST['id_itemtemp'])
        if itemtemptodelete.armain is None:
            itemtemptodelete.delete()
        else:
            itemtemptodelete.isdeleted = 1
            itemtemptodelete.save()
        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


