from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from ataxcode.models import Ataxcode
from creditterm.models import Creditterm
from currency.models import Currency
from department.models import Department
from employee.models import Employee
from inputvattype.models import Inputvattype
from oftype.models import Oftype
from ofsubtype.models import Ofsubtype
from supplier.models import Supplier
from vat.models import Vat
from wtax.models import Wtax
from . models import Ofmain
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Ofmain
    template_name = 'operationalfund/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Ofmain.objects.all().order_by('-enterdate')[0:10]

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['listcount'] = Ofmain.objects.all().count()
        context['forapproval'] = Ofmain.objects.filter(designatedapprover=self.request.user).count()
        return context


@method_decorator(login_required, name='dispatch')
class CreateViewUser(CreateView):
    model = Ofmain
    template_name = 'operationalfund/usercreate.html'
    fields = ['ofdate', 'amount', 'particulars', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('operationalfund.add_ofmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if float(self.request.POST['amount'])  <= 1000:
            year = str(form.cleaned_data['ofdate'].year)
            yearqs = Ofmain.objects.filter(ofnum__startswith=year)

            if yearqs:
                ofnumlast = yearqs.latest('ofnum')
                latestofnum = str(ofnumlast)
                print "latest: " + latestofnum

                ofnum = year
                last = str(int(latestofnum[4:]) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    ofnum += '0'
                ofnum += last

            else:
                ofnum = year + '000001'

            print 'ofnum: ' + ofnum
            print self.request.POST['payee']
            print self.request.POST['hiddenpayee']
            print self.request.POST['hiddenpayeeid']
            if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
                self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
                self.object.payee_code = self.object.payee.code
                self.object.payee_name = self.object.payee.name
            else:
                self.object.payee_name = self.request.POST['payee']

            self.object.ofnum = ofnum
            self.object.enterby = self.request.user
            self.object.modifyby = self.request.user
            self.object.employee = Employee.objects.get(code='011161100')
            self.object.employee_code = self.object.employee.code
            self.object.employee_name = self.object.employee.firstname.strip(' \t\n\r') + ' ' + \
                self.object.employee.lastname.strip(' \t\n\r')
            self.object.department = self.object.employee.department
            self.object.department_code = self.object.department.code
            self.object.department_name = self.object.department.departmentname
            self.object.save()

        return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/userupdate')


@method_decorator(login_required, name='dispatch')
class CreateViewCashier(CreateView):
    model = Ofmain
    template_name = 'operationalfund/cashiercreate.html'
    fields = ['ofdate', 'oftype', 'ofsubtype', 'amount', 'refnum', 'particulars', 'creditterm', 'vat', 'atc',
              'inputvattype', 'deferredvat', 'currency', 'fxrate', 'wtax', 'designatedapprover', 'employee',
              'department']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('operationalfund.add_ofmain') or not request.user.has_perm('operationalfund.is_cashier'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if float(self.request.POST['amount']) <= 1000:
            year = str(form.cleaned_data['ofdate'].year)
            yearqs = Ofmain.objects.filter(ofnum__startswith=year)

            if yearqs:
                ofnumlast = yearqs.latest('ofnum')
                latestofnum = str(ofnumlast)
                print "latest: " + latestofnum

                ofnum = year
                last = str(int(latestofnum[4:]) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    ofnum += '0'
                ofnum += last

            else:
                ofnum = year + '000001'

            print 'ofnum: ' + ofnum
            print self.request.POST['payee']
            print self.request.POST['hiddenpayee']
            print self.request.POST['hiddenpayeeid']
            if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
                self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
                self.object.payee_code = self.object.payee.code
                self.object.payee_name = self.object.payee.name
            else:
                self.object.payee_name = self.request.POST['payee']

            self.object.ofnum = ofnum
            self.object.enterby = self.request.user
            self.object.modifyby = self.request.user
            self.object.employee_code = Employee.objects.get(pk=self.request.POST['employee']).code
            self.object.employee_name = Employee.objects.get(pk=self.request.POST['employee']).firstname.\
                strip(' \t\n\r') + ' ' + Employee.objects.get(pk=self.request.POST['employee']).lastname.\
                strip(' \t\n\r')
            self.object.department_code = Department.objects.get(pk=self.request.POST['department']).code
            self.object.department_name = Department.objects.get(pk=self.request.POST['department']).departmentname
            self.object.ofstatus = 'I'
            self.object.receiveby = self.request.user
            self.object.receivedate = datetime.datetime.now()
            self.object.save()

        return HttpResponseRedirect('/operationalfund/')


@method_decorator(login_required, name='dispatch')
class UpdateViewUser(UpdateView):
    model = Ofmain
    template_name = 'operationalfund/userupdate.html'
    fields = ['ofnum', 'ofdate', 'amount', 'particulars', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('operationalfund.change_ofmain') or self.object.isdeleted == 1 \
                or self.object.ofstatus == 'A':
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['payee'] = Ofmain.objects.get(pk=self.object.id).payee.id if Ofmain.objects.get(pk=self.object.id).payee is not None else ''
        context['payee_name'] = Ofmain.objects.get(pk=self.object.id).payee_name
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        print self.request.POST['payee']
        print self.request.POST['hiddenpayee']
        print self.request.POST['hiddenpayeeid']
        if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
            self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
            self.object.payee_code = self.object.payee.code
            self.object.payee_name = self.object.payee.name
        else:
            self.object.payee = None
            self.object.payee_code = None
            self.object.payee_name = self.request.POST['payee']

        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['ofdate', 'payee', 'payee_code', 'payee_name', 'amount', 'particulars',
                                        'designatedapprover'])

        return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/userupdate')


@method_decorator(login_required, name='dispatch')
class UpdateViewCashier(UpdateView):
    model = Ofmain
    template_name = 'operationalfund/cashierupdate.html'
    fields = ['ofnum', 'ofdate', 'oftype', 'ofsubtype', 'amount', 'refnum', 'particulars', 'creditterm', 'vat', 'atc',
              'inputvattype', 'deferredvat', 'currency', 'fxrate', 'wtax', 'ofstatus', 'designatedapprover',
              'employee', 'department', 'remarks']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('operationalfund.change_ofmain') or self.object.isdeleted == 1 \
                or not request.user.has_perm('operationalfund.is_cashier') or self.object.ofstatus == 'F' \
                or self.object.ofstatus == 'D':
            raise Http404
        else:
            self.object.ofstatus = 'I'
            self.object.save(update_fields=['ofstatus'])
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['payee'] = Ofmain.objects.get(pk=self.object.id).payee.id if Ofmain.objects.get(
            pk=self.object.id).payee is not None else ''
        context['payee_name'] = Ofmain.objects.get(pk=self.object.id).payee_name
        context['originalofstatus'] = 'A' if self.object.creditterm is None else 'I'
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        print self.request.POST['payee']
        print self.request.POST['hiddenpayee']
        print self.request.POST['hiddenpayeeid']
        if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
            self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
            self.object.payee_code = self.object.payee.code
            self.object.payee_name = self.object.payee.name
        else:
            self.object.payee = None
            self.object.payee_code = None
            self.object.payee_name = self.request.POST['payee']

        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['ofdate', 'payee', 'payee_code', 'payee_name', 'amount', 'particulars',
                                        'designatedapprover'])

        return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/userupdate')


@csrf_exempt
def approve(request):
    if request.method == 'POST':
        of_for_approval = Ofmain.objects.get(pk=request.POST['ofid'])
        if request.user.has_perm('operationalfund.approve_allof') or \
                request.user.has_perm('operationalfund.approve_assignedof'):
            if request.user.has_perm('operationalfund.approve_allof') or \
                    (request.user.has_perm('operationalfund.approve_assignedof') and
                     of_for_approval.designatedapprover == request.user):
                if of_for_approval.ofstatus != 'I' and of_for_approval.ofstatus != 'R':
                    of_for_approval.ofstatus = request.POST['response']
                    of_for_approval.isdeleted = 0
                    if request.POST['response'] == 'D':
                        of_for_approval.status = 'C'
                    of_for_approval.approverresponse = request.POST['response']
                    of_for_approval.responsedate = datetime.datetime.now()
                    of_for_approval.actualapprover = User.objects.get(pk=request.user.id)
                    of_for_approval.save()
                    data = {
                        'status': 'success',
                        'ofnum': of_for_approval.ofnum,
                        'newofstatus': of_for_approval.get_ofstatus_display(),
                    }
                else:
                    data = {
                        'status': 'error',
                    }
            else:
                data = {
                    'status': 'error',
                }
        else:
            data = {
                'status': 'error',
            }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def getsupplierdata(request):
    if request.method == 'POST':
        supplier = Supplier.objects.get(pk=request.POST['supplierid'])
        data = {
            'status': 'success',
            'creditterm': supplier.creditterm.id,
            'vat': supplier.vat.id,
            'atc': supplier.atc.id,
            'inputvattype': supplier.inputvattype.id,
            'deferredvat': supplier.deferredvat,
            'currency': supplier.currency.id,
            'fxrate': supplier.fxrate,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)
