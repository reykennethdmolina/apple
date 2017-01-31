from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core import serializers
from . models import Bankaccount
from bank.models import Bank
from bankbranch.models import Bankbranch
from bankaccounttype.models import Bankaccounttype
from currency.models import Currency
from chartofaccount.models import Chartofaccount
import datetime


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
    fields = ['code', 'bank', 'bankbranch', 'bankaccounttype', 'currency', 'chartofaccount', 'accountnumber',
              'remarks', 'beg_amount', 'beg_code', 'beg_date', 'run_amount', 'run_code', 'run_date']

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
        context['bankaccounttype'] = Bankaccounttype.objects.filter(isdeleted=0).order_by('id')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('id')
        context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Bankaccount
    template_name = 'bankaccount/edit.html'
    fields = ['code', 'bank', 'bankbranch', 'bankaccounttype', 'currency', 'chartofaccount', 'accountnumber',
              'remarks', 'beg_amount', 'beg_code', 'beg_date', 'run_amount', 'run_code', 'run_date']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankaccount.change_bankaccount'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/bankaccount')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['bank'] = Bank.objects.filter(isdeleted=0).order_by('description')
        context['bankaccounttype'] = Bankaccounttype.objects.filter(isdeleted=0).order_by('id')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('id')
        context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0).order_by('description')
        context['bankbranch_id'] = self.object.bankbranch.id
        context['bankbranch_description'] = self.object.bankbranch.description
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


def all_json_branches(request, bank):
    current_bank = Bank.objects.get(pk=bank)
    branches = Bankbranch.objects.all().filter(bank=current_bank).order_by('description')
    json_models = serializers.serialize("json", branches)
    print json_models
    return HttpResponse(json_models, content_type="application/javascript")

