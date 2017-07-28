import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from acctentry.views import generatekey
from supplier.models import Supplier
from branch.models import Branch
from bankbranchdisburse.models import Bankbranchdisburse
from vat.models import Vat
from ataxcode.models import Ataxcode
from inputvattype.models import Inputvattype
from creditterm.models import Creditterm
from currency.models import Currency
from aptype.models import Aptype
from . models import Apmain

# pagination and search
from endless_pagination.views import AjaxListView
from django.db.models import Q

# pdf
from django.conf import settings
from easy_pdf.views import PDFTemplateView


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    download_filename = 'my_pdf.pdf'
    template_name = 'accountspayable/create2.html'
    # base_url = 'file://' + settings.STATIC_ROOT

    def get_context_data(self, **kwargs):
        return super(Pdf, self).get_context_data(
            pagesize='A4',
            title='Hi there!',
            **kwargs
        )

@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Apmain
    template_name = 'accountspayable/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'accountspayable/index_list.html'
    def get_queryset(self):
        query = Apmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(apnum__icontains=keysearch) |
                                 Q(apdate__icontains=keysearch) |
                                 Q(payeecode__icontains=keysearch) |
                                 Q(vatcode__icontains=keysearch) |
                                 Q(ataxcode__icontains=keysearch) |
                                 Q(bankbranchdisbursebranch__icontains=keysearch) |
                                 Q(refno__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch))
        return query

    # def render_to_response(self, context, **response_kwargs):
    #     response = super(IndexView, self).render_to_response(context, **response_kwargs)
    #     response.set_cookie('keysearch_' + self.request.resolver_match.app_name, 'qwe')
    #     print self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name)
    #     return response

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        #lookup
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')

        context['pk'] = 0

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Apmain
    template_name = 'accountspayable/create.html'
    fields = ['apdate', 'aptype', 'payee', 'branch',
              'bankbranchdisburse', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars',
              'currency', 'fxrate']

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
        context['pk'] = 0

        #lookup
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        try:
            apnumlast = Apmain.objects.latest('apnum')
            latestapnum = str(apnumlast)
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
        ataxobject = Ataxcode.objects.get(pk=self.request.POST['atax'], isdeleted=0)
        payeeobject = Supplier.objects.get(pk=self.request.POST['payee'], isdeleted=0)
        bankbranchdisburseobject = Bankbranchdisburse.objects.get(pk=self.request.POST['bankbranchdisburse'], isdeleted=0)

        self.object.apnum = apnum
        self.object.apstatus = 'V'
        self.object.fxrate = 1
        self.object.vatcode = vatobject.code
        self.object.vatrate = vatobject.rate
        self.object.ataxcode = ataxobject.code
        self.object.ataxrate = ataxobject.rate
        self.object.payeecode = payeeobject.code
        self.object.bankbranchdisbursebranch = bankbranchdisburseobject.branch
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/accountspayable/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Apmain
    template_name = 'accountspayable/edit.html'
    fields = ['apdate', 'aptype', 'payee', 'branch',
              'bankbranchdisburse', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars',
              'currency', 'fxrate']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('customer.change_apmain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save(update_fields=['apdate', 'aptype', 'payee', 'branch',
                                        'bankbranchdisburse', 'vat', 'atax',
                                        'inputvattype', 'creditterm', 'duedate',
                                        'refno', 'deferred', 'particulars',
                                        'currency'])
        return HttpResponseRedirect('/accountspayable/' + str(self.object.id) + '/update')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        if self.request.POST.get('payee', False):
            context['payee'] = Supplier.objects.get(pk=self.request.POST['payee'], isdeleted=0)
        elif self.object.payee:
            context['payee'] = Supplier.objects.get(pk=self.object.payee.id, isdeleted=0)
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')
        context['currency'] = Currency.objects.filter(isdeleted=0)
        context['apnum'] = self.object.apnum
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('code')
        context['pk'] = self.object.pk
        return context


def comments():
    print 123
    # copy po format for vat field
    # clear cache based on condition
    # cache api
