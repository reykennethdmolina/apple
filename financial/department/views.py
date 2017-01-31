from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from department.models import Department
from chartofaccount.models import Chartofaccount
from productgroup.models import Productgroup
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Department
    template_name = 'department/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Department.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Department
    template_name = 'department/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Department
    template_name = 'department/create.html'
    fields = ['code', 'departmentname', 'expchartofaccount', 'sectionname', 'groupname', 'productgroup', 'branchstatus']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('department.add_department'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['expchartofaccount'] = Chartofaccount.objects.filter(isdeleted=0, main=5).order_by('accountcode')
        context['productgroup'] = Productgroup.objects.filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/department')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Department
    template_name = 'department/edit.html'
    fields = ['code', 'departmentname', 'expchartofaccount', 'sectionname', 'groupname', 'productgroup', 'branchstatus']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('department.change_department'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['expchartofaccount'] = Chartofaccount.objects.filter(isdeleted=0, main=5).order_by('accountcode')
        context['productgroup'] = Productgroup.objects.filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/department')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Department
    template_name = 'department/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('department.delete_department'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.save()
        return HttpResponseRedirect('/department')
