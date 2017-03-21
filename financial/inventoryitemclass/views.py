from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from inventoryitemclass.models import Inventoryitemclass
from chartofaccount.models import Chartofaccount
from inventoryitemtype.models import Inventoryitemtype
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Inventoryitemclass
    template_name = 'inventoryitemclass/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Inventoryitemclass.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Inventoryitemclass
    template_name = 'inventoryitemclass/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Inventoryitemclass
    template_name = 'inventoryitemclass/create.html'
    fields = ['code', 'description', 'inventoryitemtype', 'chartexpcostofsale', 'chartexpgenandadmin', 'chartexpsellexp']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('fxtype.add_fxtype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/inventoryitemclass')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0).order_by('description')
        context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0, main=5).order_by('accountcode')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Inventoryitemclass
    template_name = 'inventoryitemclass/edit.html'
    fields = ['code', 'description', 'inventoryitemtype', 'chartexpcostofsale', 'chartexpgenandadmin', 'chartexpsellexp']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitemclass.change_inventoryitemclass'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0).order_by('description')
        context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0, main=5).order_by('accountcode')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/inventoryitemclass')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Inventoryitemclass
    template_name = 'inventoryitemclass/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitemclass.delete_inventoryitemclass'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/inventoryitemclass')