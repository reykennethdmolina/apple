from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Employee
from department.models import Department
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Employee
    template_name = 'employee/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Employee.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Employee
    template_name = 'employee/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Employee
    template_name = 'employee/create.html'
    fields = ['code', 'department', 'firstname', 'middlename', 'lastname', 'email', 'multiplestatus']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('employee.add_employee'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/employee')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Employee
    template_name = 'employee/edit.html'
    fields = ['code', 'department', 'firstname', 'middlename', 'lastname', 'email', 'multiplestatus']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('employee.change_employee'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/employee')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Employee
    template_name = 'employee/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('employee.delete_employee'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/employee')

