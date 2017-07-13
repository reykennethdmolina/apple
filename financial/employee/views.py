import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core import serializers
from django.db.models import Q
from department.models import Department
from . models import Employee


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Employee
    template_name = 'employee/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Employee.objects.all().filter(isdeleted=0).order_by('-pk')[0:10]

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['listcount'] = Employee.objects.filter(isdeleted=0).count()
        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Employee
    template_name = 'employee/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Employee
    template_name = 'employee/create.html'
    fields = ['code', 'department', 'firstname', 'middlename', 'lastname', 'email']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('employee.add_employee'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.multiplestatus = 'N'
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/employee')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        if self.request.POST.get('department', False):
            context['department'] = Department.objects.get(pk=self.request.POST['department'], isdeleted=0)
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Employee
    template_name = 'employee/edit.html'
    fields = ['code', 'department', 'firstname', 'middlename', 'lastname', 'email']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('employee.change_employee'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.multiplestatus = 'Y'
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save(update_fields=['department', 'firstname',
                                        'middlename', 'lastname', 'email', 'multiplestatus',
                                        'modifyby', 'modifydate'])
        return HttpResponseRedirect('/employee')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['department'] = Department.objects.\
            filter(isdeleted=0).order_by('departmentname')
        if self.request.POST.get('department', False):
            context['department'] = Department.objects.get(pk=self.request.POST['department'], isdeleted=0)
        else:
            context['department'] = Department.objects.get(pk=self.object.department.id, isdeleted=0)
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

def paginate(request, command, current, limit, search):
    current = int(current)
    limit = int(limit)

    if command == "search" and search != "null":
        search_not_slug = search.replace('-', ' ')
        employee = Employee.objects.all().filter(Q(id__icontains=search) |
                                                 Q(code__icontains=search) |
                                                 Q(firstname__icontains=search) |
                                                 Q(middlename__icontains=search) |
                                                 Q(lastname__icontains=search) |
                                                 Q(code__icontains=search_not_slug) |
                                                 Q(firstname__icontains=search_not_slug) |
                                                 Q(middlename__icontains=search_not_slug) |
                                                 Q(lastname__icontains=search_not_slug))\
                                                .filter(isdeleted=0).order_by('-pk')
    else:
        employee = Employee.objects.all().filter(isdeleted=0).\
            order_by('-pk')[current:current+limit]

    json_models = serializers.serialize("json", employee)
    print json_models
    return HttpResponse(json_models, content_type="application/javascript")

