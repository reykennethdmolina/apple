from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from suppliertype.models import Suppliertype
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Suppliertype
    template_name = 'suppliertype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Suppliertype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Suppliertype
    template_name = 'suppliertype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Suppliertype
    template_name = 'suppliertype/create.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('suppliertype.add_suppliertype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/suppliertype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Suppliertype
    template_name = 'suppliertype/edit.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('suppliertype.change_suppliertype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/suppliertype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Suppliertype
    template_name = 'suppliertype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('suppliertype.delete_suppliertype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/suppliertype')
