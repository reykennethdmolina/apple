from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Mainsupplier_supplier
from mainsupplier.models import Mainsupplier
from supplier.models import Supplier
import datetime


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Mainsupplier_supplier
    template_name = 'mainsupplier_supplier/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Mainsupplier_supplier.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Mainsupplier_supplier
    template_name = 'mainsupplier_supplier/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Mainsupplier_supplier
    template_name = 'mainsupplier_supplier/create.html'
    fields = ['mainsupplier', 'supplier']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mainsupplier_supplier.add_mainsupplier_supplier'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/mainsupplier_supplier')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['mainsupplier'] = Mainsupplier.objects.filter(isdeleted=0).order_by('description')
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('name')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Mainsupplier_supplier
    template_name = 'mainsupplier_supplier/edit.html'
    fields = ['mainsupplier', 'supplier']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mainsupplier_supplier.change_mainsupplier_supplier'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/mainsupplier_supplier')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['mainsupplier'] = Mainsupplier.objects.filter(isdeleted=0).order_by('description')
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('name')

        # formfields = UpdateView.fields[:]
        # formvalues = [self.object.mainsupplier, self.object.supplier]
        # context['zipped_list'] = zip(formfields, formvalues)
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Mainsupplier_supplier
    template_name = 'mainsupplier_supplier/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mainsupplier_supplier.delete_mainsupplier_supplier'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/mainsupplier_supplier')
