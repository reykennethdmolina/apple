from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Supplier
from ataxcode.models import Ataxcode
from vat.models import Vat
from inputvat.models import Inputvat
import datetime


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Supplier
    template_name = 'supplier/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Supplier.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Supplier
    template_name = 'supplier/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Supplier
    template_name = 'supplier/create.html'
    fields = ['code', 'name', 'address1', 'address2', 'address3', 'tin', 'telno', 'faxno', 'zipcode',
              'multiplestatus', 'ataxcode', 'vat', 'inputvat', 'inputvatrate']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('supplier.add_supplier'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/supplier')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('description')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('description')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Supplier
    template_name = 'supplier/edit.html'
    fields = ['code', 'name', 'address1', 'address2', 'address3', 'tin', 'telno', 'faxno', 'zipcode',
              'multiplestatus', 'ataxcode', 'vat', 'inputvat', 'inputvatrate']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('supplier.change_supplier'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/supplier')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('description')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('description')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('description')
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

