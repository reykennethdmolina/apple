from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from ataxcode.models import Ataxcode
from bankaccount.models import Bankaccount
from bankbranchdisburse.models import Bankbranchdisburse
from branch.models import Branch
from companyparameter.models import Companyparameter
from currency.models import Currency
from inputvattype.models import Inputvattype
from cvtype.models import Cvtype
from cvsubtype.models import Cvsubtype
from operationalfund.models import Ofmain, Ofitem, Ofdetail
from replenish_pcv.models import Reppcvmain, Reppcvdetail
from supplier.models import Supplier
from vat.models import Vat
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from checkvoucher.models import Cvmain, Cvdetail, Cvdetailtemp, Cvdetailbreakdown, Cvdetailbreakdowntemp
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail
from django.template.loader import render_to_string
from easy_pdf.views import PDFTemplateView
import datetime
from pprint import pprint
from django.utils.dateformat import DateFormat
from utils.mixins import ReportContentMixin


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Cvmain
    template_name = 'checkvoucher/index.html'
    page_template = 'checkvoucher/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Cvmain.objects.all().filter(isdeleted=0)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(cvnum__icontains=keysearch) |
                                 Q(cvdate__icontains=keysearch) |
                                 Q(payee_name__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        # data for lookup
        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        context['cvsubtype'] = Cvsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        # data for lookup

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Cvmain
    template_name = 'checkvoucher/create.html'
    fields = ['cvdate', 'cvtype', 'cvsubtype', 'amount', 'amountinwords', 'refnum', 'particulars', 'vat', 'atc', 'checknum', 'checkdate',
              'inputvattype', 'deferredvat', 'currency', 'fxrate', 'branch', 'bankaccount', 'disbursingbranch',
              'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('checkvoucher.add_cvmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)
