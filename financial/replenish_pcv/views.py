from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from . models import Reppcvmain, Reppcvdetail
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
    model = Reppcvmain
    template_name = 'replenish_pcv/index.html'
    page_template = 'replenish_pcv/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Reppcvmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(reppcvnum__icontains=keysearch) |
                                 Q(reppcvdate__icontains=keysearch) |
                                 Q(cvmain__cvnum__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        context['listcount'] = Ofmain.objects.all().count()
        context['canbeapproved'] = Ofmain.objects.filter(Q(ofstatus='F') | Q(ofstatus='A') | Q(ofstatus='D')).\
            filter(isdeleted=0).count()
        context['forapproval'] = Ofmain.objects.filter(designatedapprover=self.request.user).count()
        context['userrole'] = 'C' if self.request.user.has_perm('operationalfund.is_cashier') else 'U'

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(ListView):
    model = Ofmain
    template_name = 'replenish_pcv/create.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Ofmain.objects.all().filter(isdeleted=0, ofstatus='R', oftype__code='PCV', reppcvmain=None).\
            order_by('ofnum')

        if self.request.GET:
            if self.request.GET['ofdatefrom']:
                query = query.filter(ofdate__gte=self.request.GET['ofdatefrom'])
            if self.request.GET['ofdateto']:
                query = query.filter(ofdate__lte=self.request.GET['ofdateto'])

        return query

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['oftype'] = Oftype.objects.filter(code='PCV', isdeleted=0)
        if self.request.GET:
            context['ofdatefrom'] = self.request.GET['ofdatefrom']
            context['ofdateto'] = self.request.GET['ofdateto']

        return context


@csrf_exempt
def replenish(request):
    if request.method == 'POST':
        year = str(datetime.date.today().year)
        yearqs = Reppcvmain.objects.filter(reppcvnum__startswith=year)

        if yearqs:
            reppcvnumlast = yearqs.latest('reppcvnum')
            latestreppcvnum = str(reppcvnumlast)
            print "latest: " + latestreppcvnum

            reppcvnum = year
            last = str(int(latestreppcvnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                reppcvnum += '0'
            reppcvnum += last

        else:
            reppcvnum = year + '000001'

        print 'reppcvnum: ' + reppcvnum

        newreppcv = Reppcvmain()
        newreppcv.reppcvnum = reppcvnum
        newreppcv.reppcvdate = datetime.date.today()
        newreppcv.enterby = request.user
        newreppcv.modifyby = request.user
        newreppcv.save()

        total_amount = 0
        replenishedofs = Ofmain.objects.filter(id__in=request.POST.getlist('pcv_checkbox'))
        for data in replenishedofs:
            newreppcvdetail = Reppcvdetail()
            newreppcvdetail.amount = data.approvedamount
            newreppcvdetail.enterby = request.user
            newreppcvdetail.modifyby = request.user
            newreppcvdetail.ofmain = Ofmain.objects.get(pk=data.id)
            newreppcvdetail.reppcvmain = newreppcv
            total_amount += newreppcvdetail.amount
            newreppcvdetail.save()
            data.reppcvdetail = newreppcvdetail
            data.reppcvmain = newreppcv
            data.save()

        newreppcv.amount = total_amount
        newreppcv.save()
        print "PCV successfully replenished."
    else:
        print "Something went wrong in saving REPPCV."
    return redirect('/replenish_pcv/')
