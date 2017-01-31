from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Maininventory
from unitofmeasure.models import Unitofmeasure
import datetime


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Maininventory
    template_name = 'maininventory/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Maininventory.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Maininventory
    template_name = 'maininventory/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Maininventory
    template_name = 'maininventory/create.html'
    fields = ['code', 'description', 'unitofmeasure']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('maininventory.add_maininventory'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/maininventory')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Maininventory
    template_name = 'maininventory/edit.html'
    fields = ['code', 'description', 'unitofmeasure']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('maininventory.change_maininventory'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/maininventory')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Maininventory
    template_name = 'maininventory/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('maininventory.delete_maininventory'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/maininventory')
