from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from departmentbudget.models import Departmentbudget
from department.models import Department
from unit.models import Unit
from chartofaccount.models import Chartofaccount
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Departmentbudget
    template_name = 'departmentbudget/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Departmentbudget.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Departmentbudget
    template_name = 'departmentbudget/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Departmentbudget
    template_name = 'departmentbudget/create.html'
    fields = ['year', 'department', 'unit', 'chartofaccount',
              'remarks', 'formula', 'method',
              'mjan', 'mfeb', 'mmar',
              'mapr', 'mmay', 'mjun',
              'mjul', 'maug', 'msep',
              'moct', 'mnov', 'mdec']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('departmentbudget.add_departmentbudget'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['unit'] = Unit.objects.filter(isdeleted=0).order_by('description')
        context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/departmentbudget')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Departmentbudget
    template_name = 'departmentbudget/edit.html'
    fields = ['year', 'department', 'unit', 'chartofaccount',
              'remarks', 'formula', 'method',
              'mjan', 'mfeb', 'mmar',
              'mapr', 'mmay', 'mjun',
              'mjul', 'maug', 'msep',
              'moct', 'mnov', 'mdec']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('departmentbudget.change_departmentbudget'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['unit'] = Unit.objects.filter(isdeleted=0).order_by('description')
        context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/departmentbudget')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Departmentbudget
    template_name = 'departmentbudget/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('departmentbudget.delete_departmentbudget'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/departmentbudget')
