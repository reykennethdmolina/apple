from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404, HttpResponse
from . models import Supplier
from creditterm.models import Creditterm
from currency.models import Currency
from ataxcode.models import Ataxcode
from vat.models import Vat
from inputvattype.models import Inputvattype
from django.core import serializers
from django.db.models import Q
import datetime


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Supplier
    template_name = 'supplier/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Supplier.objects.all().filter(isdeleted=0).order_by('-pk')[0:10]

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['listcount'] = Supplier.objects.filter(isdeleted=0).count()
        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Supplier
    template_name = 'supplier/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Supplier
    template_name = 'supplier/create.html'
    fields = ['code', 'name', 'address1', 'address2', 'address3', 'tin', 'telno', 'faxno', 'zipcode',
              'contactperson', 'creditterm', 'inputvattype', 'inputvattype_deferred', 'vat', 'atc', 'currency']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('supplier.add_supplier'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.multiplestatus = 'N'
        self.object.fxrate = Currency.objects.get(pk=self.request.POST['currency']).fxrate
        self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
        self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/supplier')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('description')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('description')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('description')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Supplier
    template_name = 'supplier/edit.html'
    fields = ['code', 'name', 'address1', 'address2', 'address3', 'tin', 'telno', 'faxno', 'zipcode',
              'contactperson', 'creditterm', 'inputvattype', 'inputvattype_deferred', 'vat', 'atc', 'currency']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('supplier.change_supplier'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.multiplestatus = 'N'
        self.object.fxrate = Currency.objects.get(pk=self.request.POST['currency']).fxrate
        self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
        self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
        self.object.modifyby = self.request.user
        self.object.save(update_fields=['name', 'address1', 'address2', 'address3', 'tin', 'telno', 'faxno', 'zipcode',
                                        'contactperson', 'creditterm', 'inputvattype', 'inputvattype_deferred', 'vat',
                                        'atc', 'currency', 'fxrate', 'vatrate', 'atcrate', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/supplier')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('description')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('description')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('description')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Supplier
    template_name = 'supplier/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('supplier.delete_supplier'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/supplier')


def paginate(request, command, current, limit, search):
    current = int(current)
    limit = int(limit)

    if command == "search" and search != "null":
        search_not_slug = search.replace('-', ' ')
        supplier = Supplier.objects.all().filter(Q(id__icontains=search) |
                                                 Q(code__icontains=search) |
                                                 Q(name__icontains=search) |
                                                 Q(code__icontains=search_not_slug) |
                                                 Q(name__icontains=search_not_slug))\
                                                .filter(isdeleted=0).order_by('-pk')
    else:
        supplier = Supplier.objects.all().filter(isdeleted=0).order_by('-pk')[current:current+limit]

    json_models = serializers.serialize("json", supplier)
    print json_models
    return HttpResponse(json_models, content_type="application/javascript")

