import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from module.models import Module, Activitylogs
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from mainmodule.models import Mainmodule
from django.contrib.contenttypes.models import ContentType
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter
from django.contrib.auth.models import Group
from django.db import connection
from collections import namedtuple
import io
import xlsxwriter
# from django.contrib.auth.models import GroupPermission
# from django.contrib.auth.models import UserGroup

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Module
    template_name = 'module/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Module.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Module
    template_name = 'module/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Module
    template_name = 'module/create.html'
    fields = ['code', 'description', 'mainmodule', 'django_content_type', 'name', 'segment']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('module.add_module'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['mainmodule'] = Mainmodule.objects.filter(isdeleted=0).order_by('description')
        context['django_content_type'] = ContentType.objects.\
            exclude(pk__in=[1, 2, 5, 6]).order_by('app_label')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/module')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Module
    template_name = 'module/edit.html'
    fields = ['code', 'description', 'mainmodule', 'django_content_type', 'name', 'segment']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('module.change_module'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['mainmodule'] = Mainmodule.objects.filter(isdeleted=0).order_by('description')
        context['django_content_type'] = ContentType.objects.\
            exclude(pk__in=[1, 2, 5, 6]).order_by('app_label')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'mainmodule', 'django_content_type',
                                        'name', 'segment',
                                        'modifyby', 'modifydate'])
        return HttpResponseRedirect('/module')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Module
    template_name = 'module/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('module.delete_module'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/module')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Module.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Program Information Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('module/list.html', context)

@method_decorator(login_required, name='dispatch')
class GeneratePDFLogs(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Activitylogs.objects.filter(user_id__isnull=False).order_by('-id')[:100]

        context = {
            "title": "SYSTEM ACTIVITY LOG REPORT",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('module/logs.html', context)

@method_decorator(login_required, name='dispatch')
class GeneratePDFModuleAccess(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = query_module_access(request)
        context = {
            "title": "Program Access Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('module/list_moduleaccess.html', context)

@method_decorator(login_required, name='dispatch')
class GeneratePDFUser(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = User.objects.all().order_by('username')
        context = {
            "title": "User Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('module/list_user.html', context)

@method_decorator(login_required, name='dispatch')
class GeneratePDFUserAccess(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        # list = Permission.objects.all()
        list = query_user_access(request)
        context = {
            "title": "User Access Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('module/list_access.html', context)

@method_decorator(login_required, name='dispatch')
class GeneratePDFGroup(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Group.objects.all().order_by('name')
        context = {
            "title": "Group Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('module/list_group.html', context)


@method_decorator(login_required, name='dispatch')
class GeneratePDFGroupAccess(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = query_group_access(request)
        context = {
            "title": "Group Access Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('module/list_groupaccess.html', context)


@method_decorator(login_required, name='dispatch')
class GeneratePDFUserGroup(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = query_user_group(request)
        context = {
            "title": "User Group Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('module/list_usergroup.html', context)


def query_module_access(request):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT mm.id, mm.description, m.id AS module_id, m.name AS module_name, p.id AS permission_id, p.name AS permission_name, p.codename " \
            "FROM auth_permission AS p " \
            "LEFT OUTER JOIN module AS m ON m.django_content_type_id = p.content_type_id " \
            "LEFT OUTER JOIN mainmodule AS mm ON mm.id = m.mainmodule_id " \
            "GROUP BY mm.description, m.name, p.name "

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def query_group_access(request):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT gp.group_id, gp.permission_id, g.name AS group_name, p.name AS permission_name, p.content_type_id, m.name AS module_name " \
            "FROM auth_group_permissions AS gp " \
            "LEFT OUTER JOIN auth_group AS g ON g.id = gp.group_id " \
            "LEFT OUTER JOIN auth_permission AS p ON p.id = gp.permission_id " \
            "LEFT OUTER JOIN module AS m ON m.django_content_type_id = p.content_type_id " \
            "GROUP BY g.name, gp.permission_id"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def query_user_group(request):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT ag.name AS groupname, au.username, au.first_name, au.last_name " \
            "FROM auth_user_groups AS aug " \
            "LEFT OUTER JOIN auth_group AS ag ON ag.id = aug.group_id " \
            "LEFT OUTER JOIN auth_user AS au ON au.id = aug.user_id " \
            "ORDER BY ag.name, au.first_name, au.last_name"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def query_user_access(request):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT uup.user_id, uup.permission_id, u.username, u.first_name, u.last_name, p.name AS permission_name, p.content_type_id, m.name AS module_name " \
            "FROM auth_user_user_permissions AS uup " \
            "LEFT OUTER JOIN auth_user AS u ON u.id = uup.user_id " \
            "LEFT OUTER JOIN auth_permission AS p ON p.id = uup.permission_id " \
            "LEFT OUTER JOIN module AS m ON m.django_content_type_id = p.content_type_id " \
            "GROUP BY u.username, u.first_name, u.last_name, m.name, p.name"

            # "GROUP BY u.username, u.first_name, u.last_name, m.name, p.name LIMIT 300"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


@method_decorator(login_required, name='dispatch')
class GenerateExcelLogs(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})
        cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

        # title
        worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
        worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
        worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
        worksheet.write('A4', 'SYSTEM ACTIVITY LOG REPORTS', bold)

        worksheet.write('C1', 'Software:')
        worksheet.write('C2', 'User:')
        worksheet.write('C3', 'Datetime:')

        worksheet.write('D1', 'iES Financial System v. 1.0')
        worksheet.write('D2', str(request.user.username))
        worksheet.write('D3', datetime.datetime.now(), cell_format)

        filename = "activity_logs.xlsx"

        # header
        worksheet.write('A6', 'User ID', bold)
        worksheet.write('B6', 'Username', bold)
        worksheet.write('C6', 'Log Date', bold)
        worksheet.write('D6', 'Activity', bold)

        row = 6
        col = 0

        list = Activitylogs.objects.filter(user_id__isnull=False).order_by('-id')

        for data in list:
            worksheet.write(row, col, data.user_id)
            worksheet.write(row, col + 1, data.username)
            worksheet.write(row, col + 2, data.activity_date, formatdate)
            worksheet.write(row, col + 3, data.remarks)

            row += 1



        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response




