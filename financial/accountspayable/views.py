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
from . models import Apmain


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Apmain
    template_name = 'accountspayable/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Apmain.objects.all().filter(isdeleted=0).order_by('enterdate')[0:10]

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['listcount'] = Apmain.objects.filter(isdeleted=0).count()
        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Apmain
    template_name = 'accountspayable/create.html'
    fields = ['apdate', 'aptype', 'payee', 'branch',
              'bankbranchdisburse', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars',
              'currency']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('accountspayable.add_apmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['payee'] = Supplier.objects.filter(isdeleted=0).order_by('name')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')
        context['currency'] = Currency.objects.filter(isdeleted=0, symbol='PHP')

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
              'currency']

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
        context['payee'] = Supplier.objects.get(pk=self.object.payee.id, isdeleted=0)
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')
        context['currency'] = Currency.objects.filter(isdeleted=0, symbol='PHP')
        context['apnum'] = self.object.apnum
        return context


def comments():
    print 123
    # copy po format for vat field
    # clear cache based on condition
    # cache api
