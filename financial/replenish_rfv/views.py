from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView
from utils.mixins import ReportContentMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from . models import Reprfvmain, Reprfvdetail
from ataxcode.models import Ataxcode
from branch.models import Branch
from chartofaccount.models import Chartofaccount
from companyparameter.models import Companyparameter
from creditterm.models import Creditterm
from currency.models import Currency
from inputvattype.models import Inputvattype
from oftype.models import Oftype
from ofsubtype.models import Ofsubtype
from supplier.models import Supplier
from vat.models import Vat
from wtax.models import Wtax
from employee.models import Employee
from department.models import Department
from inputvat.models import Inputvat
from operationalfund. models import Ofmain, Ofdetail, Ofdetailtemp, Ofdetailbreakdown, Ofdetailbreakdowntemp, Ofitem, Ofitemtemp
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime
from endless_pagination.views import AjaxListView
from annoying.functions import get_object_or_None
from easy_pdf.views import PDFTemplateView
import json
from pprint import pprint
from dateutil.relativedelta import relativedelta


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Reprfvmain
    template_name = 'replenish_rfv/index.html'
    page_template = 'replenish_rfv/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Reprfvmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(reprfvnum__icontains=keysearch) |
                                 Q(reprfvdate__icontains=keysearch) |
                                 Q(apmain__apnum__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query


@method_decorator(login_required, name='dispatch')
class CreateView(ListView):
    model = Ofmain
    template_name = 'replenish_rfv/create.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Ofmain.objects.all().filter(isdeleted=0, ofstatus='R', oftype__code='RFV', reprfvmain=None).\
            order_by('ofnum')

        if self.request.GET:
            if self.request.GET['ofdatefrom']:
                query = query.filter(ofdate__gte=self.request.GET['ofdatefrom'])
            if self.request.GET['ofdateto']:
                query = query.filter(ofdate__lte=self.request.GET['ofdateto'])

        return query

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['oftype'] = Oftype.objects.filter(code='RFV', isdeleted=0)
        if self.request.GET:
            context['ofdatefrom'] = self.request.GET['ofdatefrom']
            context['ofdateto'] = self.request.GET['ofdateto']

        return context


@csrf_exempt
def replenish(request):
    if request.method == 'POST':
        year = str(datetime.date.today().year)
        yearqs = Reprfvmain.objects.filter(reprfvnum__startswith=year)

        if yearqs:
            reprfvnumlast = yearqs.latest('reprfvnum')
            latestreprfvnum = str(reprfvnumlast)
            print "latest: " + latestreprfvnum

            reprfvnum = year
            last = str(int(latestreprfvnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                reprfvnum += '0'
            reprfvnum += last

        else:
            reprfvnum = year + '000001'

        print 'reprfvnum: ' + reprfvnum

        newreprfv = Reprfvmain()
        newreprfv.reprfvnum = reprfvnum
        newreprfv.reprfvdate = datetime.date.today()
        newreprfv.enterby = request.user
        newreprfv.modifyby = request.user
        newreprfv.save()

        total_amount = 0
        replenishedofs = Ofmain.objects.filter(id__in=request.POST.getlist('rfv_checkbox'))
        for data in replenishedofs:
            newreprfvdetail = Reprfvdetail()
            newreprfvdetail.amount = data.approvedamount
            newreprfvdetail.enterby = request.user
            newreprfvdetail.modifyby = request.user
            newreprfvdetail.ofmain = Ofmain.objects.get(pk=data.id)
            newreprfvdetail.reprfvmain = newreprfv
            total_amount += newreprfvdetail.amount
            newreprfvdetail.save()
            data.newreprfvdetail = newreprfvdetail
            data.reprfvmain = newreprfv
            data.save()

        newreprfv.amount = total_amount
        newreprfv.save()
        print "RFV successfully replenished."
    else:
        print "Something went wrong in saving REPRFV."
    return redirect('/replenish_rfv/')


@csrf_exempt
def fetch_details(request):
    if request.method == 'POST':
        details = Reprfvdetail.objects.filter(isdeleted=0, reprfvmain__reprfvnum=request.POST['reprfvnum'])

        details_list = []

        for data in details:
            details_list.append([data.id,
                                 'OF-' + data.ofmain.oftype.code + '-' + data.ofmain.ofnum,
                                 data.ofmain.ofdate,
                                 data.ofmain.particulars,
                                 data.amount,
                                 ])

        data = {
            'status': 'success',
            'detail': details_list
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)
