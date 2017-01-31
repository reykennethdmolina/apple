from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Serviceinformation
from serviceclassification.models import Serviceclassification
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Serviceinformation
    template_name = 'serviceinformation/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Serviceinformation.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Serviceinformation
    template_name = 'serviceinformation/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Serviceinformation
    template_name = 'serviceinformation/create.html'
    fields = ['precode', 'code', 'description', 'serviceclassification']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('serviceinformation.add_serviceinformation'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/serviceinformation')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['serviceclassification'] = Serviceclassification.objects.filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Serviceinformation
    template_name = 'serviceinformation/edit.html'
    fields = ['precode', 'code', 'description', 'serviceclassification']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('serviceinformation.change_serviceinformation'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/serviceinformation')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['serviceclassification'] = Serviceclassification.objects.filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Serviceinformation
    template_name = 'serviceinformation/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('serviceinformation.delete_serviceinformation'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/serviceinformation')
