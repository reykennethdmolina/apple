import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404, JsonResponse
from department.models import Department
from django.views.decorators.csrf import csrf_exempt
from . models import Employee
from django.contrib.auth.models import User

# pagination and search
from endless_pagination.views import AjaxListView
from django.db.models import Q


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Employee
    template_name = 'employee/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'employee/index_list.html'
    def get_queryset(self):
        query = Employee.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(code__icontains=keysearch) |
                                 Q(firstname__icontains=keysearch) |
                                 Q(middlename__icontains=keysearch) |
                                 Q(lastname__icontains=keysearch))
        return query


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Employee
    template_name = 'employee/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Employee
    template_name = 'employee/create.html'
    fields = ['code', 'department', 'firstname', 'middlename', 'lastname', 'email', 'cellphone_subsidize_amount']

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
    fields = ['code', 'department', 'firstname', 'middlename', 'lastname', 'email', 'cellphone_subsidize_amount']

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
                                        'modifyby', 'modifydate', 'cellphone_subsidize_amount'])
        return HttpResponseRedirect('/employee')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['department'] = Department.objects.\
            filter(isdeleted=0).order_by('departmentname')
        if self.request.POST.get('department', False):
            context['department'] = Department.objects.get(pk=self.request.POST['department'], isdeleted=0)
        elif self.object.department:
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


@csrf_exempt
def getUnusedEmployee(request):
    if request.method == 'POST':
        employee = Employee.objects.filter(isdeleted=0, user=None).exclude(firstname='').order_by('firstname')

        employee_list = []

        for data in employee:
            employee_list.append([data.id,
                                  data.code,
                                  data.firstname,
                                  data.middlename,
                                  data.lastname,
                                  data.email,
                                  ])
        data = {
            'status': 'success',
            'employee': employee_list,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def saveUserEmployee(request):
    if request.method == 'POST':
        post_employee = request.POST['employee']
        post_user = request.POST['user']

        if User.objects.filter(pk=post_user, is_active=1):
            if Employee.objects.filter(pk=post_employee, user=post_user) or Employee.objects.filter(pk=post_employee, user=None):
                Employee.objects.filter(user=post_user).update(user=None)
                Employee.objects.filter(pk=post_employee).update(user=post_user)
                type = "success"
            else:
                type = "used"
        else:
            type = "inactive"

        data = {
            'status': 'success',
            'type': type,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)