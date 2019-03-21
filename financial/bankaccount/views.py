import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from bank.models import Bank
from bankbranch.models import Bankbranch
from bankaccounttype.models import Bankaccounttype
from currency.models import Currency
from chartofaccount.models import Chartofaccount
from . models import Bankaccount
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Bankaccount
    template_name = 'bankaccount/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Bankaccount.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Bankaccount
    template_name = 'bankaccount/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Bankaccount
    template_name = 'bankaccount/create.html'
    fields = ['code', 'bank', 'bankbranch', 'bankaccounttype',
              'currency', 'chartofaccount', 'accountnumber',
              'remarks', 'beg_amount', 'beg_code', 'beg_date',
              'run_amount', 'run_code', 'run_date']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankaccount.add_bankaccount'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/bankaccount')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['bank'] = Bank.objects.filter(isdeleted=0).order_by('description')
        context['bankaccounttype'] = Bankaccounttype.objects.\
            filter(isdeleted=0).order_by('id')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('id')
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Bankaccount
    template_name = 'bankaccount/edit.html'
    fields = ['code', 'bank', 'bankbranch', 'bankaccounttype', 'currency',
              'chartofaccount', 'accountnumber',
              'remarks', 'beg_amount', 'beg_code', 'beg_date', 'run_amount',
              'run_code', 'run_date']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankaccount.change_bankaccount'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['bank', 'bankbranch', 'bankaccounttype', 'currency',
                                        'chartofaccount', 'accountnumber', 'remarks',
                                        'beg_amount', 'beg_code', 'beg_date', 'run_amount',
                                        'run_code', 'run_date', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/bankaccount')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['bank'] = Bank.objects.filter(isdeleted=0).order_by('description')
        context['bankaccounttype'] = Bankaccounttype.objects.filter(isdeleted=0).order_by('id')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('id')
        context['bankbranch_id'] = self.object.bankbranch.id
        context['bankbranch_description'] = self.object.bankbranch.description
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        elif self.object.chartofaccount:
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.object.chartofaccount.id, isdeleted=0)
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Bankaccount
    template_name = 'bankaccount/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankaccount.delete_bankaccount'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/bankaccount')


@csrf_exempt
def get_branch(request):
    if request.method == 'POST':
        bank = request.POST['bank']
        bankbranch = Bankbranch.objects.filter(bank=bank).order_by('description')
        data = {
            'status': 'success',
            'bankbranch': serializers.serialize("json", bankbranch),
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Bank Account Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('bankaccount/list.html', context)

@method_decorator(login_required, name='dispatch')
class GeneratePDF2(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Bankaccount.objects.filter(isdeleted=0).order_by('code')

        debit = 0
        credit = 0
        grandtotal = 0
        for l in list:
            print l.run_amount
            if l.run_code == 'D':
                debit += l.run_amount
            else:
                credit += l.run_amount

        grandtotal = abs(debit - credit)

        total = {'debit': debit, 'credit': credit, 'grandtotal': grandtotal}

        context = {
            "title": "Cash In Bank Balances",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "username": request.user,
        }
        return Render.render('bankaccount/cashinbankbalances.html', context)