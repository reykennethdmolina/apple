from django.views.generic import DetailView, View, CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from ataxcode.models import Ataxcode
from branch.models import Branch
from chartofaccount.models import Chartofaccount
from companyparameter.models import Companyparameter
from creditterm.models import Creditterm
from currency.models import Currency
from inputvattype.models import Inputvattype
from oftype.models import Oftype
from module.models import Activitylogs
from ofsubtype.models import Ofsubtype
from supplier.models import Supplier
from vat.models import Vat
from wtax.models import Wtax
from employee.models import Employee
from department.models import Department
from inputvat.models import Inputvat
from . models import Ofmain, Ofdetail, Ofdetailtemp, Ofdetailbreakdown, Ofdetailbreakdowntemp, Ofitem, Ofitemtemp, Ofupload
from accountspayable.models import Apmain, Apdetail
from journalvoucher.models import Jvmain, Jvdetail
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from django.db.models import Q
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime
from django.utils import timezone
from endless_pagination.views import AjaxListView
from annoying.functions import get_object_or_None
from easy_pdf.views import PDFTemplateView
import json
from pprint import pprint
from utils.mixins import ReportContentMixin
from django.utils.dateformat import DateFormat
from django.contrib.humanize.templatetags.humanize import intcomma
from department.models import Department
from unit.models import Unit
from inputvat.models import Inputvat
from outputvat.models import Outputvat
from ataxcode.models import Ataxcode
from employee.models import Employee
from chartofaccount.models import Chartofaccount
from bankaccount.models import Bankaccount
from product.models import Product
from customer.models import Customer
from annoying.functions import get_object_or_None
from decimal import Decimal
from financial.utils import Render
from django.db import connection
from collections import namedtuple
import io
import xlsxwriter
import pandas as pd
from django.core.mail import send_mail
from django.core.files.storage import FileSystemStorage


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Ofmain
    template_name = 'operationalfund/index.html'
    page_template = 'operationalfund/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        if self.request.user.has_perm('operationalfund.approve_assignedof') and not self.request.user.has_perm('operationalfund.approve_allof'):
            user_employee = get_object_or_None(Employee, user=self.request.user)

            if user_employee is not None:

                if user_employee.of_approver == 3:
                    print user_employee.group
                    oic_approver = Employee.objects.filter(of_approver=1, group=user_employee.group).values_list('id', flat=True)
                    print 'hey'
                    print oic_approver
                    query = Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(enterby=self.request.user.id) | Ofmain.objects.filter(designatedapprover__in=oic_approver)
                    #query = Ofmain.objects.filter(designatedapprover__in=oic_approver)
                #elif user_employee.of_approver == 4 and user_employee.hr_approver == 1:
                    #query = Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(oftype_id__in=[8,9],ofstatus__in=['A', 'R']) | Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(enterby=self.request.user.id)
                elif user_employee.of_approver == 6:
                    print 'hello final'
                    query = Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(oftype_id__in=[8, 9, 10], ofstatus__in=['F','A', 'R'],  hr_approved_lvl1 = 'A', hr_approved_lvl2='A') | Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(enterby=self.request.user.id)
                else:
                    query = Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(enterby=self.request.user.id)
                query = query.filter(isdeleted=0)
                #query = Ofmain.objects.all().filter(isdeleted=0, designatedapprover=user_employee)
                #query2 = Ofmain.objects.all().filter(isdeleted=0, enterby=self.request.user.id)
                #query = query.union(query2).order_by('~id')
            else:
                query = Ofmain.objects.all().filter(isdeleted=0)
        else:

            if self.request.user.has_perm('operationalfund.approve_allof'):
                query = Ofmain.objects.all().filter(isdeleted=0)
            else:
                query = Ofmain.objects.all().filter(isdeleted=0, enterby=self.request.user.id)

            ## Eyeglass and Antibiotic
            user_employee = get_object_or_None(Employee, user=self.request.user)

            if user_employee:
                print 'employee'
                print user_employee.hr_approver
                print 'hr approver ako'

                if user_employee.of_approver == 4:
                    query = Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(oftype_id__in=[8, 9, 10], ofstatus__in=['F', 'A', 'R']) | Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(enterby=self.request.user.id)
                elif user_employee.of_approver == 5:
                    print 'hello'
                    query = Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(oftype_id__in=[8, 9, 10], ofstatus__in=['F','A', 'R'],  hr_approved_lvl1='A') | Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(enterby=self.request.user.id)
                elif user_employee.of_approver == 6:
                    print 'hello final'
                    query = Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(oftype_id__in=[8, 9, 10], ofstatus__in=['F','A', 'R'], hr_approved_lvl1 = 'A', hr_approved_lvl2='A') | Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(enterby=self.request.user.id)
            else:
                print self.request.user.id
                if self.request.user.id == 274:
                    query = Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(oftype_id__in=[9, 10],  nurse_approved = 'F') | Ofmain.objects.filter(designatedapprover=user_employee) | Ofmain.objects.filter(enterby=self.request.user.id)


        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(ofnum__icontains=keysearch) |
                                 Q(ofdate__icontains=keysearch) |
                                 Q(amount__icontains=keysearch) |
                                 Q(requestor_name__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch))

        if self.request.COOKIES.get('keysearchtype_' + self.request.resolver_match.app_name):
            oftype = str(self.request.COOKIES.get('keysearchtype_' + self.request.resolver_match.app_name))
            print oftype
            query = query.filter(oftype_id = oftype)

        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        context['listcount'] = Ofmain.objects.all().count()
        context['canbeapproved'] = Ofmain.objects.filter(Q(ofstatus='F') | Q(ofstatus='A') | Q(ofstatus='D')).\
            filter(isdeleted=0).count()
        user_employee = get_object_or_None(Employee, user=self.request.user)
        if user_employee is not None:
            forapproval = Ofmain.objects.filter(designatedapprover=Employee.objects.get(
                user=self.request.user)).count()
        else:
            forapproval = 0
        context['user_employee'] = user_employee
        context['forapproval'] = forapproval
        context['userrole'] = 'C' if self.request.user.has_perm('operationalfund.is_cashier') else 'U'
        context['user_employee'] = get_object_or_None(Employee, user=self.request.user)
        context['user'] = self.request.user

        # data for lookup
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        # data for lookup

        return context


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Ofmain
    template_name = 'operationalfund/report/index.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('description')
        #context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('description')
        #context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['user'] = Employee.objects.filter(isdeleted=0).exclude(firstname='').order_by('firstname')
        #context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        #context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        #context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        #context['unit'] = Unit.objects.filter(isdeleted=0).order_by('code')
        #context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        #context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('code')
        #context['outputvat'] = Outputvat.objects.filter(isdeleted=0).order_by('code')
        #context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultHtmlView(ListView):
    model = Ofmain
    template_name = 'operationalfund/reportresulthtml.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "OPERATIONAL FUND"
        context['rc_title'] = "OPERATIONAL FUND"

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Ofmain
    template_name = 'operationalfund/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "OPERATIONAL FUND"
        context['rc_title'] = "OPERATIONAL FUND"

        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Ofmain
    template_name = 'operationalfund/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['detail'] = Ofdetail.objects.filter(isdeleted=0).\
            filter(ofmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Ofdetail.objects.filter(isdeleted=0).\
            filter(ofmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Ofdetail.objects.filter(isdeleted=0).\
            filter(ofmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        # data for lookup
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        if self.request.user.id != 274:
            context['aemp'] = Employee.objects.filter(user_id=self.request.user.id).first()#Employee.objects.get(user_id=self.request.user.id)
        else:
            context['aemp'] = []
        context['aap'] = []
        if self.object.hrstatus == 'A':
            context['aap'] = Employee.objects.get(user_id=self.object.actualapprover_id)
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        # data for lookup

        context['mealexpense'] = Companyparameter.objects.get(code='PDI').pcv_meal_expenses_id
        context['mealbudget'] = Companyparameter.objects.get(code='PDI').pcv_meal_budget_limit

        # requested items
        context['itemtemp'] = Ofitem.objects.filter(ofmain=self.object.pk, isdeleted=0).order_by('item_counter')
        context['uploadlist'] = Ofupload.objects.filter(ofmain_id=self.object.pk).order_by('enterdate')

        return context


@method_decorator(login_required, name='dispatch')
class CreateViewUser(CreateView):
    model = Ofmain
    template_name = 'operationalfund/usercreate.html'
    fields = ['ofdate', 'oftype', 'requestor', 'designatedapprover', 'refnum', 'cashadv_amount']

    def dispatch(self, request, *args, **kwargs):
        # if not request.user.has_perm('operationalfund.add_ofmain') or \
        #     request.user.has_perm('operationalfund.is_cashier'):
        if not request.user.has_perm('operationalfund.add_ofmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.mysecretkey = generatekey(self)

        context = super(CreateView, self).get_context_data(**kwargs)

        # Controlled Pilot Testing 13, 218, 1, 191, 154, 274
        d = {"13": 13, "218": 218, "1": 1, "191": 191,  "154": 154, "274": 274}

        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')

        # if str(self.request.user.id) in d:
        #     context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        #     print 'dito'
        # else:
        #     context['oftype'] = Oftype.objects.filter(id__in=[1,2,3,4,5,6]).order_by('pk')
        #context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        user_employee = get_object_or_None(Employee, user=self.request.user)
        if self.request.user.has_perm('operationalfund.assign_requestor'):
            context['requestor'] = Employee.objects.filter(isdeleted=0).exclude(firstname='').order_by('firstname')
        else:
            if user_employee is not None:
                context['requestor'] = Employee.objects.filter(isdeleted=0, pk=user_employee)
            else:
                context['requestor'] = None
        context['user_employee'] = user_employee
        #managers = Employee.objects.filter(managementlevel=6).values_list('user_id', flat=True)
        #context['designatedapprover'] = User.objects.filter(id__in=managers, is_active=1).exclude(username='admin').order_by('first_name')
        #context['designatedapprover'] = Employee.objects.filter(isdeleted=0).exclude(firstname='').exclude(user=self.request.user).order_by('firstname')
        #context['designatedapprover'] = Employee.objects.filter(isdeleted=0).filter(managementlevel__level__lte=5).order_by('firstname')
        context['designatedapprover'] = Employee.objects.filter(isdeleted=0).filter(of_approver__gte=1).order_by('firstname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0)
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['secretkey'] = self.mysecretkey
        context['mealexpense'] = Companyparameter.objects.get(code='PDI').pcv_meal_expenses_id
        context['mealbudget'] = Companyparameter.objects.get(code='PDI').pcv_meal_budget_limit
        context['eyeglass'] = 0
        ofdepsub = Ofmain.objects.filter(isdeleted=0, requestor_id=user_employee, ofstatus='F', oftype_id=10).aggregate(Sum('amount'))
        print ofdepsub
        context['anti_dep_amount'] = max(0, float(user_employee.anti_dep_amount))
        if ofdepsub['amount__sum']:
            context['anti_dep_amount'] = max(0, float(user_employee.anti_dep_amount) - float(ofdepsub['amount__sum']))

        print context['anti_dep_amount']

        today = datetime.date.today()
        ed = user_employee.eyeglass_date
        diff = today - ed
        if diff.days > 365:
            context['eyeglass'] = 1

        return context

    def form_valid(self, form):
        user_employee = get_object_or_None(Employee, user=self.request.user)
        if self.request.user.has_perm('operationalfund.assign_requestor') or \
                (user_employee is not None and self.request.user == self.object.requestor):
            self.object = form.save(commit=False)

            year = str(form.cleaned_data['ofdate'].year)
            yearqs = Ofmain.objects.filter(ofnum__startswith=year)

            ofnumlast = lastNumber('true')

            ## SELECT RIGHT(MAX(LPAD(apnum, 10, 0)) , 6)  FROM apmain;
            latestofnum = str(ofnumlast[0])
            ofnum = year
            last = str(int(latestofnum) + 1)

            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                ofnum += '0'
            ofnum += last

            # if yearqs:
            #     ofnumlast = yearqs.latest('ofnum')
            #     latestofnum = str(ofnumlast)
            #     print "latest: " + latestofnum
            #
            #     ofnum = year
            #     last = str(int(latestofnum[4:]) + 1)
            #     zero_addon = 6 - len(last)
            #     for num in range(0, zero_addon):
            #         ofnum += '0'
            #     ofnum += last
            #
            # else:
            #     ofnum = year + '000001'
            #
            # print 'ofnum: ' + ofnum

            total_amount = Ofitemtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
                aggregate(Sum('amount'))
            #print total_amount['amount__sum']
            if Oftype.objects.get(pk=int(self.request.POST['oftype'])).code != 'PCV' or \
                    total_amount['amount__sum'] <= 1000.00:
                if Oftype.objects.get(pk=int(self.request.POST['oftype'])).code != 'CSV' or \
                                total_amount['amount__sum'] <= self.object.requestor.cellphone_subsidize_amount:
                    self.object.ofnum = ofnum
                    self.object.enterby = self.request.user
                    self.object.modifyby = self.request.user
                    self.object.requestor_code = self.object.requestor.code
                    self.object.requestor_name = self.object.requestor.firstname + ' ' + self.object.requestor.lastname
                    department = Department.objects.get(pk=int(self.request.POST['department']))
                    self.object.department = department
                    self.object.department_code = department.code
                    self.object.department_name = department.departmentname
                    if self.request.POST['oftype'] == '6':
                        self.object.refnum = self.request.POST['refnum']
                        self.object.cashadv_amount = self.request.POST['cashadv_amount']
                    #print self.request.POST['department']
                    # if self.object.requestor.department_id > 0 and self.object.requestor.department_id is not None:
                    #     self.object.department = Department.objects.get(code=self.object.requestor.department.code)
                    #     self.object.department_code = self.object.department.code
                    #     self.object.department_name = self.object.department.departmentname
                    # else:
                    #     self.object.department = Department.objects.get(code='IT')
                    #     self.object.department_code = self.object.department.code
                    #     self.object.department_name = self.object.department.departmentname
                    self.object.save()

                    # ----------------- START save ofitemtemp to ofitem START ---------------------
                    itemtemp = Ofitemtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
                        order_by('enterdate')
                    totalamount = 0
                    i = 1
                    for itemtemp in itemtemp:
                        item = Ofitem()
                        item.item_counter = i
                        item.ofnum = self.object.ofnum
                        item.ofdate = self.object.ofdate
                        item.payee_code = itemtemp.payee_code
                        item.payee_name = itemtemp.payee_name
                        item.amount = itemtemp.amount
                        item.particulars = itemtemp.particulars
                        item.refnum = itemtemp.refnum
                        item.fxrate = itemtemp.fxrate
                        item.periodfrom = itemtemp.periodfrom
                        item.periodto = itemtemp.periodto
                        item.noofpax = itemtemp.noofpax
                        item.currency = Currency.objects.get(pk=itemtemp.currency)
                        item.enterby = itemtemp.enterby
                        item.modifyby = itemtemp.modifyby
                        item.ofmain = self.object
                        item.ofsubtype = itemtemp.ofsubtype
                        item.oftype = Oftype.objects.get(pk=itemtemp.oftype)
                        item.payee = get_object_or_None(Supplier, id=itemtemp.payee)
                        item.ofitemstatus = itemtemp.ofitemstatus
                        item.save()
                        itemtemp.delete()
                        totalamount += item.amount
                        i += 1
                    # ----------------- END save ofitemtemp to ofitem END ---------------------

                    self.object.amount = totalamount
                    self.object.save()

                    ''' Send Email Notifacation '''
                    receiver = Employee.objects.filter(isdeleted=0, status='A', id=self.object.designatedapprover_id).first()
                    print 'send email notification'
                    subject = 'OPERATIONAL FUND APPROVER NOTIFICATION'
                    message = 'Hi Sir, \n\n' \
                              'Requestor ' + str(
                        self.object.requestor_name) + ' has filed Operational Fund Request for your approval. \n\n' \
                                                 'Click link here: https://fin101bss.inquirer.com.ph/operationalfund'
                    email_from = 'inq-noreply@inquirer.com.ph'
                    recipient_list = [receiver.email]
                    #recipient_list = ['reykennethdmolina@gmail.com']
                    send_mail(subject, message, email_from, recipient_list)

                    print receiver.email

                    print 'email sent'

                    ''' IF Antibiotic '''
                    if self.object.oftype_id == 9 or self.object.oftype_id == 10:
                        ''' Send Email Notifacation to Clinic '''
                        #receiver = Employee.objects.filter(isdeleted=0, status='A',id=self.object.designatedapprover_id).first()
                        print 'send email notification'
                        subject = 'OPERATIONAL FUND APPROVER NOTIFICATION - CLINIC'
                        message = 'Hi Sir, \n\n' \
                                  'Requestor ' + str(
                            self.object.requestor_name) + ' has filed Operational Fund Request for your approval. \n\n' \
                                                          'Click link here: https://fin101bss.inquirer.com.ph/operationalfund'
                        email_from = 'inq-noreply@inquirer.com.ph'
                        recipient_list = ['inq.clinic@gmail.com']
                        # recipient_list = ['reykennethdmolina@gmail.com']
                        send_mail(subject, message, email_from, recipient_list)

                        print receiver.email

                        print 'email sent'

                    # Save Activity Logs
                    Activitylogs.objects.create(
                        user_id=self.request.user.id,
                        username=self.request.user,
                        remarks='Create OF Transaction #' + str(Oftype.objects.get(pk=int(self.request.POST['oftype'])).code) + '-' +self.object.ofnum
                    )

                    return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/userupdate/')
                else:
                    return HttpResponseRedirect('/operationalfund/usercreate/')
            else:
                return HttpResponseRedirect('/operationalfund/usercreate/')
        else:
            return HttpResponseRedirect('/operationalfund/usercreate/')


@method_decorator(login_required, name='dispatch')
class CreateViewCashier(CreateView):
    model = Ofmain
    template_name = 'operationalfund/cashiercreate.html'
    fields = ['ofdate', 'oftype', 'ofsubtype', 'amount', 'refnum', 'particulars', 'creditterm', 'vat', 'atc',
              'inputvattype', 'deferredvat', 'currency', 'fxrate', 'employee', 'department', 'branch']

    def dispatch(self, request, *args, **kwargs):
        # if not request.user.has_perm('operationalfund.add_ofmain') or \
        #         not request.user.has_perm('operationalfund.is_cashier'):
        raise Http404
        # return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        #managers = Employee.objects.filter(managementlevel=6).values_list('user_id', flat=True)
        #context['designatedapprover'] = User.objects.filter(id__in=managers, is_active=1).exclude(username='admin').order_by('first_name')
        #context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        #context['designatedapprover'] = Employee.objects.filter(isdeleted=0).filter(managementlevel__level__lte=5).order_by('firstname')
        context['designatedapprover'] = Employee.objects.filter(isdeleted=0).filter(of_approver__gte=1).order_by('firstname')
        context['secretkey'] = generatekey(self)

        # data for lookup
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        # data for lookup

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
            self.object.designatedapprover = self.request.user
            self.object.actualapprover = self.request.user
            self.object.approverresponse = 'A'
            self.object.responsedate = datetime.datetime.now()
            self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
            self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
            self.object.save()

            # accounting entry starts here..
            source = 'ofdetailtemp'
            mainid = self.object.id
            num = self.object.ofnum
            secretkey = self.request.POST['secretkey']
            savedetail(source, mainid, num, secretkey, self.request.user)

            return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/cashierupdate')
        else:
            return HttpResponseRedirect('/operationalfund/')


@method_decorator(login_required, name='dispatch')
class UpdateViewUser(UpdateView):
    model = Ofmain
    template_name = 'operationalfund/userupdate.html'
    fields = ['ofdate', 'oftype', 'requestor', 'designatedapprover', 'department', 'refnum', 'cashadv_amount']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        # if not request.user.has_perm('operationalfund.change_ofmain') or self.object.isdeleted == 1 or \
        #         request.user.has_perm('operationalfund.is_cashier'):
        #     if not request.user.username == 'admin':
        # elif request.user.has_perm('operationalfund.is_cashier'):  ---> put before elif if needed
        if not request.user.has_perm('operationalfund.change_ofmain'):
            raise Http404
        # elif self.object.ofstatus != 'F' and self.object.ofstatus != 'D' and request.user.username != 'admin':
        #     raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        self.mysecretkey = generatekey(self)

        # requested items
        iteminfo = Ofitem.objects.filter(ofmain=self.object.pk, isdeleted=0).order_by('item_counter')

        for data in iteminfo:
            detail = Ofitemtemp()
            detail.item_counter = data.item_counter
            detail.secretkey = self.mysecretkey
            detail.ofmain = data.ofmain.id
            detail.ofitem = data.id
            detail.ofnum = data.ofnum
            detail.ofdate = data.ofdate
            detail.oftype = data.oftype.id
            detail.ofsubtype = get_object_or_None(Ofsubtype, id=data.ofsubtype.id)
            detail.payee = data.payee_id
            detail.payee_code = data.payee_code
            detail.payee_name = data.payee_name
            detail.supplier = data.supplier.id if data.supplier else None
            detail.supplier_code = data.supplier_code
            detail.supplier_name = data.supplier_name
            detail.tin = data.tin
            detail.amount = data.amount
            detail.particulars = data.particulars
            detail.refnum = data.refnum
            detail.vat = data.vat_id
            detail.vatrate = data.vatrate
            detail.inputvattype = data.inputvattype_id
            detail.deferredvat = data.deferredvat
            detail.currency = data.currency_id
            detail.atc = data.atc_id
            detail.atcrate = data.atcrate
            detail.fxrate = data.fxrate
            detail.remarks = data.remarks
            detail.periodfrom = data.periodfrom
            detail.periodto = data.periodto
            detail.noofpax = data.noofpax
            detail.ofitemstatus = data.ofitemstatus
            detail.save()
            # requested items end

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['ofnum'] = self.object.ofnum
        context['amount'] = self.object.amount
        # context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
        #     order_by('first_name')
        #context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        # Controlled Pilot Testing 13, 218, 1, 191, 154, 274
        d = {"13": 13, "218": 218, "1": 1, "191": 191, "154": 154, "274": 274}

        # if str(self.request.user.id) in d:
        #     context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        #     print 'dito'
        # else:
        #     context['oftype'] = Oftype.objects.filter(id__in=[1, 2, 3, 4, 5, 6]).order_by('pk')

        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        # context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        # context['requestor'] = User.objects.filter(pk=self.request.user.id)
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0)
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['secretkey'] = self.mysecretkey

        context['requestor'] = Employee.objects.filter(isdeleted=0).exclude(firstname='').order_by('firstname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        #context['designatedapprover'] = Employee.objects.filter(isdeleted=0).filter(managementlevel__level__lte=5).order_by('firstname')
        #context['designatedapprover'] = Employee.objects.filter(isdeleted=0).exclude(firstname='').order_by('firstname')
        context['designatedapprover'] = Employee.objects.filter(isdeleted=0).filter(of_approver__gte=1).order_by(
            'firstname')
        context['user_employee'] = get_object_or_None(Employee, user=self.request.user)

        context['savedoftype'] = self.object.oftype.code
        context['ofstatus'] = Ofmain.objects.get(pk=self.object.id).get_ofstatus_display()
        context['assignedcashier'] = Ofmain.objects.get(
            pk=self.object.id).receiveby.first_name + ' ' + Ofmain.objects.get(
            pk=self.object.id).receiveby.last_name if Ofmain.objects.get(pk=self.object.id).receiveby else None
        context['actualapprover'] = Ofmain.objects.get(
            pk=self.object.id).actualapprover.firstname + ' ' + Ofmain.objects.get(
            pk=self.object.id).actualapprover.lastname if Ofmain.objects.get(
            pk=self.object.id).actualapprover else None
        context['responsedate'] = Ofmain.objects.get(
            pk=self.object.id).responsedate if Ofmain.objects.get(pk=self.object.id).responsedate else None
        context['approverresponse'] = Ofmain.objects.get(
            pk=self.object.id).approverresponse if Ofmain.objects.get(pk=self.object.id).approverresponse else None
        context['releasedto'] = Ofmain.objects.get(
            pk=self.object.id).paymentreceivedby.firstname + ' ' + Ofmain.objects.get(
            pk=self.object.id).paymentreceivedby.lastname if Ofmain.objects.get(
            pk=self.object.id).paymentreceivedby else None
        context['releasedate'] = Ofmain.objects.get(
            pk=self.object.id).releasedate if Ofmain.objects.get(pk=self.object.id).releasedate else None

        context['uploadlist'] = Ofupload.objects.filter(ofmain_id=self.object.pk).order_by('enterdate')

        # requested items
        context['itemtemp'] = Ofitemtemp.objects.filter(ofmain=self.object.pk, isdeleted=0,
                                                        secretkey=self.mysecretkey).order_by('item_counter')

        context['mealexpense'] = Companyparameter.objects.get(code='PDI').pcv_meal_expenses_id
        context['mealbudget'] = Companyparameter.objects.get(code='PDI').pcv_meal_budget_limit

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        total_amount = Ofitemtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).aggregate(
            Sum('amount'))
        print total_amount['amount__sum']

        if Oftype.objects.get(pk=int(self.request.POST['oftype'])).code != 'PCV' or \
                total_amount['amount__sum'] < 1000.00:
            if Oftype.objects.get(pk=int(self.request.POST['oftype'])).code != 'CSV' or total_amount['amount__sum'] <= \
                    self.object.requestor.cellphone_subsidize_amount:
                if self.object.ofstatus != 'A' and self.object.ofstatus != 'I' and self.object.ofstatus != 'R':
                    self.object.modifyby = self.request.user
                    self.object.modifydate = datetime.datetime.now()
                    self.object.requestor_code = self.object.requestor.code
                    self.object.requestor_name = self.object.requestor.firstname + ' ' + self.object.requestor.lastname
                    # if self.object.requestor.department_id > 0 and self.object.requestor.department_id is not None:
                    #     self.object.department = Department.objects.get(code=self.object.requestor.department.code)
                    #     self.object.department_code = self.object.department.code
                    #     self.object.department_name = self.object.department.departmentname
                    department = Department.objects.get(pk=int(self.request.POST['department']))
                    self.object.department = department
                    self.object.department_code = department.code
                    self.object.department_name = department.departmentname
                    if self.request.POST['oftype'] == '6':
                        self.object.refnum = self.request.POST['refnum']
                        self.object.cashadv_amount = self.request.POST['cashadv_amount']

                    # ----------------- START save ofitemtemp to ofitem START ---------------------
                    Ofitem.objects.filter(ofmain=self.object.pk, isdeleted=0).update(isdeleted=2)

                    itemtemp = Ofitemtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
                        order_by('item_counter')
                    totalamount = 0
                    i = 1
                    logs = ""
                    for itemtemp in itemtemp:
                        item = Ofitem()
                        item.item_counter = i
                        item.ofnum = self.object.ofnum
                        item.ofdate = self.object.ofdate
                        item.payee_code = itemtemp.payee_code
                        item.payee_name = itemtemp.payee_name
                        item.amount = itemtemp.amount
                        item.particulars = itemtemp.particulars
                        item.refnum = itemtemp.refnum
                        item.fxrate = itemtemp.fxrate
                        item.periodfrom = itemtemp.periodfrom
                        item.periodto = itemtemp.periodto
                        item.noofpax = itemtemp.noofpax
                        item.currency = Currency.objects.get(pk=itemtemp.currency)
                        item.enterby = itemtemp.enterby
                        item.modifyby = itemtemp.modifyby
                        item.ofmain = self.object
                        item.ofsubtype = itemtemp.ofsubtype
                        item.oftype = Oftype.objects.get(pk=itemtemp.oftype)
                        item.payee = get_object_or_None(Supplier, id=itemtemp.payee)
                        item.ofitemstatus = itemtemp.ofitemstatus
                        item.save()
                        itemtemp.delete()
                        totalamount += item.amount
                        i += 1
                        # logs = itemtemp.particulars + " "


                    Ofitem.objects.filter(ofmain=self.object.pk, isdeleted=2).delete()
                    # ----------------- END save ofitemtemp to ofitem END ---------------------
                    self.object.amount = Decimal(totalamount)
                    if self.request.POST['oftype'] == '6':
                        self.object.save(update_fields=['ofdate', 'amount', 'particulars', 'designatedapprover', 'modifyby', 'modifydate', 'requestor', 'requestor_code', 'requestor_name', 'department', 'department_code', 'department_name', 'refnum', 'cashadv_amount'])
                    else:
                        self.object.save(update_fields=['ofdate', 'amount', 'particulars', 'designatedapprover', 'modifyby', 'modifydate', 'requestor', 'requestor_code', 'requestor_name', 'department', 'department_code', 'department_name'])

                    # Save Activity Logs
                    Activitylogs.objects.create(
                        user_id=self.request.user.id,
                        username=self.request.user,
                        remarks='Update OF Transaction #' + str(Oftype.objects.get(pk=int(self.request.POST['oftype'])).code) + '-' + self.object.ofnum
                    )
        return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/userupdate')


@method_decorator(login_required, name='dispatch')
class UpdateViewCashier(UpdateView):
    model = Ofmain
    template_name = 'operationalfund/cashierupdate.html'
    fields = ['ofdate', 'oftype', 'amount', 'refnum', 'cashadv_amount', 'particulars', 'creditterm', 'ofstatus', 'department',
              'remarks', 'paymentreceivedby', 'paymentreceiveddate', 'branch', 'requestor']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('operationalfund.change_ofmain') or self.object.isdeleted == 1 \
                or not request.user.has_perm('operationalfund.is_cashier') or self.object.ofstatus == 'F' \
                or self.object.ofstatus == 'D':
            raise Http404
        elif self.object.ofstatus == 'A':
            self.object.ofstatus = 'I'
            self.object.receiveby = self.request.user
            self.object.receivedate = datetime.datetime.now()
            self.object.save(update_fields=['ofstatus', 'receiveby', 'receivedate'])
        elif self.object.ofstatus == 'R':
            if self.object.oftype is None or self.object.creditterm is None:
                self.object.ofstatus = 'I'
                self.object.releasedate = None
                self.object.releaseby = None
                self.object.paymentreceivedby = None
                self.object.paymentreceiveddate = None
                self.object.save(update_fields=['ofstatus', 'releasedate', 'releaseby', 'paymentreceivedby',
                                                'paymentreceiveddate'])
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # accounting entry starts here
    def get_initial(self):
        self.mysecretkey = generatekey(self)

        # requested items
        iteminfo = Ofitem.objects.filter(ofmain=self.object.pk, isdeleted=0).order_by('item_counter')

        for data in iteminfo:
            detail = Ofitemtemp()
            detail.item_counter = data.item_counter
            detail.secretkey = self.mysecretkey
            detail.ofmain = data.ofmain.id
            detail.ofitem = data.id
            detail.ofnum = data.ofnum
            detail.ofdate = data.ofdate
            detail.oftype = data.oftype.id
            detail.ofsubtype = get_object_or_None(Ofsubtype, id=data.ofsubtype.id)
            detail.payee = data.payee_id
            detail.payee_code = data.payee_code
            detail.payee_name = data.payee_name
            detail.supplier = data.supplier.id if data.supplier else None
            detail.supplier_code = data.supplier_code
            detail.supplier_name = data.supplier_name
            detail.tin = data.tin
            detail.amount = data.amount
            detail.particulars = data.particulars
            detail.refnum = data.refnum
            detail.vat = data.vat_id
            detail.vatrate = data.vatrate
            detail.inputvattype = data.inputvattype_id
            detail.deferredvat = data.deferredvat
            detail.currency = data.currency_id
            detail.atc = data.atc_id
            detail.atcrate = data.atcrate
            detail.fxrate = data.fxrate
            detail.remarks = data.remarks
            detail.periodfrom = data.periodfrom
            detail.periodto = data.periodto
            detail.noofpax = data.noofpax
            detail.ofitemstatus = data.ofitemstatus
            detail.save()
        # requested items end

        detailinfo = Ofdetail.objects.filter(ofmain=self.object.pk).order_by('item_counter')

        for drow in detailinfo:
            detail = Ofdetailtemp()
            detail.secretkey = self.mysecretkey
            detail.of_num = drow.of_num
            detail.ofmain = drow.ofmain_id
            detail.ofdetail = drow.pk
            detail.item_counter = drow.item_counter
            detail.of_date = drow.of_date
            detail.ofitem = drow.ofitem_id
            detail.chartofaccount = drow.chartofaccount_id
            detail.bankaccount = drow.bankaccount_id
            detail.employee = drow.employee_id
            detail.supplier = drow.supplier_id
            detail.customer = drow.customer_id
            detail.department = drow.department_id
            detail.unit = drow.unit_id
            detail.branch = drow.branch_id
            detail.product = drow.product_id
            detail.inputvat = drow.inputvat_id
            detail.outputvat = drow.outputvat_id
            detail.vat = drow.vat_id
            detail.wtax = drow.wtax_id
            detail.ataxcode = drow.ataxcode_id
            detail.debitamount = drow.debitamount
            detail.creditamount = drow.creditamount
            detail.balancecode = drow.balancecode
            detail.customerbreakstatus = drow.customerbreakstatus
            detail.supplierbreakstatus = drow.supplierbreakstatus
            detail.employeebreakstatus = drow.employeebreakstatus
            detail.isdeleted = 0
            detail.modifyby = self.request.user
            detail.enterby = self.request.user
            detail.modifydate = datetime.datetime.now()
            detail.save()

            detailtempid = detail.id

            breakinfo = Ofdetailbreakdown.objects. \
                filter(ofdetail_id=drow.id).order_by('pk', 'datatype')
            if breakinfo:
                for brow in breakinfo:
                    breakdown = Ofdetailbreakdowntemp()
                    breakdown.of_num = drow.of_num
                    breakdown.secretkey = self.mysecretkey
                    breakdown.ofmain = drow.ofmain_id
                    breakdown.ofdetail = drow.pk
                    breakdown.ofdetailtemp = detailtempid
                    breakdown.ofdetailbreakdown = brow.pk
                    breakdown.item_counter = brow.item_counter
                    breakdown.of_date = brow.of_date
                    breakdown.chartofaccount = brow.chartofaccount_id
                    breakdown.particular = brow.particular
                    # Return None if object is empty
                    breakdown.bankaccount = brow.bankaccount_id
                    breakdown.employee = brow.employee_id
                    breakdown.supplier = brow.supplier_id
                    breakdown.customer = brow.customer_id
                    breakdown.department = brow.department_id
                    breakdown.unit = brow.unit_id
                    breakdown.branch = brow.branch_id
                    breakdown.product = brow.product_id
                    breakdown.inputvat = brow.inputvat_id
                    breakdown.outputvat = brow.outputvat_id
                    breakdown.vat = brow.vat_id
                    breakdown.wtax = brow.wtax_id
                    breakdown.ataxcode = brow.ataxcode_id
                    breakdown.debitamount = brow.debitamount
                    breakdown.creditamount = brow.creditamount
                    breakdown.balancecode = brow.balancecode
                    breakdown.datatype = brow.datatype
                    breakdown.customerbreakstatus = brow.customerbreakstatus
                    breakdown.supplierbreakstatus = brow.supplierbreakstatus
                    breakdown.employeebreakstatus = brow.employeebreakstatus
                    breakdown.isdeleted = 0
                    breakdown.modifyby = self.request.user
                    breakdown.enterby = self.request.user
                    breakdown.modifydate = datetime.datetime.now()
                    breakdown.save()
                    # accounting entry ends here

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['ofnum'] = self.object.ofnum
        context['savedoftype'] = self.object.oftype.code
        context['actualapprover'] = Employee.objects.get(pk=self.object.actualapprover.id).firstname + ' ' + \
            Employee.objects.get(pk=self.object.actualapprover.id).lastname
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['originalofstatus'] = 'A' if self.object.creditterm is None else Ofmain.objects.get(pk=self.object.id).ofstatus
        context['requestor'] = Employee.objects.filter(pk=self.object.requestor.id)
        context['requestordepartment'] = Department.objects.filter(pk=self.object.department.id).order_by('departmentname')

        # for PCVs
        context['pcv_requested'] = 'False' if self.object.reppcvmain is None else 'True'
        context['reppcvnum'] = self.object.reppcvmain.reppcvnum if self.object.reppcvmain else 'N/A'
        context['reppcvdate'] = self.object.reppcvmain.reppcvdate if self.object.reppcvmain else 'N/A'
        context['pcv_replenished'] = 'False' if self.object.cvmain is None else 'True'
        context['cvnum'] = self.object.cvmain.cvnum if self.object.cvmain else 'N/A'
        context['cvdate'] = self.object.cvmain.cvdate if self.object.cvmain else 'N/A'
        # for PCVs

        # for RFVs
        context['rfv_requested'] = 'False' if self.object.reprfvmain is None else 'True'
        context['reprfvnum'] = self.object.reprfvmain.reprfvnum if self.object.reprfvmain else 'N/A'
        context['reprfvdate'] = self.object.reprfvmain.reprfvdate if self.object.reprfvmain else 'N/A'
        context['rfv_replenished'] = 'False' if self.object.apmain is None else 'True'
        context['apnum'] = self.object.apmain.apnum if self.object.apmain else 'N/A'
        context['apdate'] = self.object.apmain.apdate if self.object.apmain else 'N/A'
        # for RFVs

        # for CSVs
        context['csv_replenished'] = 'False' if self.object.jvmain is None else 'True'
        context['jvnum'] = self.object.jvmain.jvnum if self.object.jvmain else 'N/A'
        context['jvdate'] = self.object.jvmain.jvdate if self.object.jvmain else 'N/A'
        # for CSVs

        # data for lookup
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').exclude(firstname='').order_by('lastname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = self.object.pk
        # data for lookup

        context['mealexpense'] = Companyparameter.objects.get(code='PDI').pcv_meal_expenses_id
        context['mealbudget'] = Companyparameter.objects.get(code='PDI').pcv_meal_budget_limit

        # requested items
        itemtemp = Ofitemtemp.objects.filter(ofmain=self.object.pk, isdeleted=0, secretkey=self.mysecretkey).\
            order_by('item_counter')

        payeedetails = []
        for data in itemtemp:
            payee = get_object_or_None(Supplier, pk=data.payee)
            print data.supplier_name
            if data.supplier and data.vatrate > 0:
                payeedetails.append({
                    'vat': '',
                    'atc': '',
                    'inputvattype': '',
                    'deferredvat': ''
                })
            else:
                payeedetails.append({
                    'vat': payee.vat_id if payee else '',
                    'atc': payee.atc_id if payee else '',
                    'inputvattype': payee.inputvattype_id if payee else '',
                    'deferredvat': payee.deferredvat if payee else ''
                })
        context['itemtempwithpayeedetails'] = zip(itemtemp, payeedetails)

        # accounting entry starts here
        context['secretkey'] = self.mysecretkey
        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'ofdetailtemp',
            'tablebreakdowntemp': 'ofdetailbreakdowntemp',

            'datatemp': querystmtdetail('ofdetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('ofdetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        # accounting entry ends here

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if self.request.POST['originalofstatus'] != 'R' and self.request.POST['originalofstatus'] != 'P':
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            # self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
            # self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
            # removed payee, payee_code, payee_name, department, employee, designatedapprover, amount

            department = Department.objects.get(pk=int(self.request.POST['department']))
            self.object.department = department
            self.object.department_code = department.code
            self.object.department_name = department.departmentname
            if self.request.POST['oftype'] == '6':
                self.object.refnum = self.request.POST['refnum']
                self.object.cashadv_amount = self.request.POST['cashadv_amount']

            self.object.save(update_fields=['refnum', 'cashadv_amount', 'department', 'department_code', 'department_name', 'particulars', 'creditterm', 'branch', 'ofstatus',
                                            'remarks', 'modifyby', 'modifydate', 'department'])

            # revert status from RELEASED to In Process if no release date is saved
            if self.object.ofstatus == 'R' and self.object.releasedate is None:
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.paymentreceivedby = None
                self.object.paymentreceiveddate = None
                self.object.ofstatus = 'I'
                self.object.save(update_fields=['releaseby', 'releasedate', 'paymentreceivedby', 'paymentreceiveddate',
                                                'ofstatus'])

            # remove release details if OFSTATUS is not RELEASED
            if self.object.ofstatus != 'R':
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.paymentreceivedby = None
                self.object.paymentreceiveddate = None
                self.object.save(update_fields=['releaseby', 'releasedate', 'paymentreceivedby', 'paymentreceiveddate'])

            # of items saving starts here..
            of_items_to_update = Ofitemtemp.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0,
                                                           ofmain=self.object.pk).order_by('item_counter')
            i = 0
            for of_item in of_items_to_update:
                update_item = Ofitem.objects.get(pk=of_item.ofitem)
                update_item.refnum = self.object.refnum  # main reference number
                update_item.deferredvat = self.request.POST.getlist('item_deferredvat')[i]
                update_item.fxrate = self.request.POST.getlist('item_fxrate')[i]
                update_item.remarks = self.request.POST.getlist('item_remarks')[i]
                update_item.periodfrom = self.request.POST.getlist('item_periodfrom')[i] if self.request.POST.\
                    getlist('item_periodfrom')[i] else None
                update_item.periodto = self.request.POST.getlist('item_periodto')[i] if self.request.POST.\
                    getlist('item_periodto')[i] else None
                update_item.noofpax = self.request.POST.getlist('item_noofpax')[i] if self.request.POST.\
                    getlist('item_noofpax')[i] else None
                if self.request.POST.getlist('item_currency')[i]:
                    update_item.currency = get_object_or_None(Currency, id=int(self.request.POST.
                                                                               getlist('item_currency')[i]))
                if self.request.POST.getlist('item_inputvattype')[i]:
                    update_item.inputvattype = get_object_or_None(Inputvattype, id=int(self.request.POST.
                                                                                       getlist('item_inputvattype')[i]))
                if self.request.POST.getlist('item_vat')[i]:
                    update_item.vat = get_object_or_None(Vat, id=int(self.request.POST.getlist('item_vat')[i]))
                    update_item.vatrate = Vat.objects.get(
                        pk=int(self.request.POST.getlist('item_vat')[i])).rate if Vat.objects.get(
                        pk=int(self.request.POST.getlist('item_vat')[i])) else None
                if self.request.POST.getlist('item_atc')[i]:
                    update_item.atc = get_object_or_None(Ataxcode, id=int(self.request.POST.getlist('item_atc')[i]))
                    update_item.atcrate = Ataxcode.objects.get(
                        pk=int(self.request.POST.getlist('item_atc')[i])).rate if Ataxcode.objects.get(
                        pk=int(self.request.POST.getlist('item_atc')[i])) else None
                if self.request.POST.getlist('item_supplier')[i]:
                    update_item.supplier = get_object_or_None(Supplier, id=int(self.request.POST.getlist('item_supplier')[i]))
                    update_item.supplier_code = Supplier.objects.get(
                        pk=int(self.request.POST.getlist('item_supplier')[i])).code if Supplier.objects.get(
                        pk=int(self.request.POST.getlist('item_supplier')[i])) else None
                    update_item.supplier_name = Supplier.objects.get(
                        pk=int(self.request.POST.getlist('item_supplier')[i])).name if Supplier.objects.get(
                        pk=int(self.request.POST.getlist('item_supplier')[i])) else None
                else:
                    update_item.supplier = None
                    update_item.supplier_code = None
                    update_item.supplier_name = None
                if self.request.POST.getlist('item_tin')[i]:
                    update_item.tin = self.request.POST.getlist('item_tin')[i]
                else:
                    update_item.tin = None
                update_item.ofitemstatus = self.request.POST.getlist('item_status')[i]
                update_item.modifyby = self.request.user
                update_item.modifydate = datetime.datetime.now()
                update_item.save()
                i += 1

            # accounting entry starts here..
            source = 'ofdetailtemp'
            mainid = self.object.id
            num = self.object.ofnum
            secretkey = self.request.POST['secretkey']
            maindate = self.object.ofdate
            updatedetail(source, mainid, num, secretkey, self.request.user, maindate)

            # saved_ofdetail = Ofdetail.objects.filter(ofmain=self.object.pk)

            # update approved amount in of main
            approved_amount = Ofitem.objects.filter(isdeleted=0, ofmain=self.object,
                                                    ofitemstatus='A').aggregate(Sum('amount'))
            self.object.approvedamount = approved_amount['amount__sum']
            self.object.save(update_fields=['approvedamount'])

        elif self.request.POST['originalofstatus'] == 'R':
            #if self.object.reppcvmain is None:
            if self.request.POST['ofstatus'] == 'I':
                self.object.ofstatus = 'I'
                self.object.releasedate = None
                self.object.releaseby = None
                self.object.paymentreceivedby = None
                self.object.paymentreceiveddate = None
                self.object.save(update_fields=['ofstatus', 'releasedate', 'releaseby', 'paymentreceivedby',
                                                'paymentreceiveddate'])

            department = Department.objects.get(pk=int(self.request.POST['department']))
            self.object.department = department
            self.object.department_code = department.code
            self.object.department_name = department.departmentname
            if self.request.POST['oftype'] == '6':
                self.object.refnum = self.request.POST['refnum']
                self.object.cashadv_amount = self.request.POST['cashadv_amount']

            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['modifyby', 'modifydate', 'remarks', 'refnum', 'cashadv_amount', 'department', 'department_code', 'department_name'])

            # items remarks save
            of_items_to_update = Ofitemtemp.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0,
                                                           ofmain=self.object.pk).order_by('item_counter')
            i = 0
            for of_item in of_items_to_update:
                update_item = Ofitem.objects.get(pk=of_item.ofitem)
                update_item.remarks = self.request.POST.getlist('item_remarks')[i]
                update_item.modifyby = self.request.user
                update_item.modifydate = datetime.datetime.now()
                update_item.save()
                i += 1

                # accounting entry starts here..
                source = 'ofdetailtemp'
                mainid = self.object.id
                num = self.object.ofnum
                secretkey = self.request.POST['secretkey']
                maindate = self.object.ofdate
                updatedetail(source, mainid, num, secretkey, self.request.user, maindate)


        return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/cashierupdate')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Ofmain
    template_name = 'operationalfund/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('operationalfund.delete_ofmain') or self.object.status == 'O' \
                or self.object.ofstatus != 'F':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.ofstatus = 'D'
        self.object.save()

        return HttpResponseRedirect('/operationalfund')


@method_decorator(login_required, name='dispatch')
class UserPdf(PDFTemplateView):
    model = Ofmain
    template_name = 'operationalfund/userpdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['ofmain'] = Ofmain.objects.get(Q(pk=self.kwargs['pk']), Q(isdeleted=0), (Q(status='A') | Q(status='C')))
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['items'] = Ofitem.objects.filter(ofmain=self.kwargs['pk'], isdeleted=0).order_by('item_counter')
        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        #print context['ofmain'].actualapprover_id
        context['aemp'] = Employee.objects.filter(user_id=context['ofmain'].actualapprover_id).first()
        #context['aemp'] = Employee.objects.get(user_id=self.object.actualapprover_id).first()
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedof = Ofmain.objects.get(Q(pk=self.kwargs['pk']), Q(isdeleted=0), (Q(status='A') | Q(status='C')))
        printedof.print_ctr1 += 1
        printedof.save()
        return context


@method_decorator(login_required, name='dispatch')
class CashierPdf(PDFTemplateView):
    model = Ofmain
    template_name = 'operationalfund/cashierpdf.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.has_perm('operationalfund.is_cashier'):
            raise Http404
        return super(PDFTemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['ofmain'] = Ofmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['approveditems'] = Ofitem.objects.filter(ofmain=self.kwargs['pk'], isdeleted=0, ofitemstatus='A').\
            order_by('item_counter')
        context['detail'] = Ofdetail.objects.filter(isdeleted=0). \
            filter(ofmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Ofdetail.objects.filter(isdeleted=0). \
            filter(ofmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Ofdetail.objects.filter(isdeleted=0). \
            filter(ofmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedof = Ofmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedof.print_ctr2 += 1
        printedof.save()
        return context


@csrf_exempt
def saveitemtemp(request):
    if request.method == 'POST':
        if request.POST['id_itemtemp'] != '':  # if item already exists (update)
            itemtemp = Ofitemtemp.objects.get(pk=int(request.POST['id_itemtemp']))
        else:  # if item does not exist (create)
            itemtemp = Ofitemtemp()
            itemtemp.enterby = request.user
        itemtemp.item_counter = request.POST['itemno']
        itemtemp.secretkey = request.POST['secretkey']
        itemtemp.oftype = request.POST['id_oftype']
        itemtemp.ofsubtype = Ofsubtype.objects.get(pk=request.POST['id_ofsubtype'])
        if request.POST['id_payee'] == request.POST['id_hiddenpayee']:
            itemtemp.payee = request.POST['id_hiddenpayeeid']
            itemtemp.payee_code = Supplier.objects.get(pk=itemtemp.payee).code
            itemtemp.payee_name = Supplier.objects.get(pk=itemtemp.payee).name
        else:
            itemtemp.payee_name = request.POST['id_payee']
        itemtemp.amount = request.POST['id_amount'].replace(',', '')
        itemtemp.particulars = request.POST['id_particulars']
        itemtemp.currency = request.POST['id_currency']
        itemtemp.fxrate = float(request.POST['id_fxrate'])
        itemtemp.periodfrom = request.POST['id_periodfrom'] if request.POST['id_periodfrom'] != '' else None
        itemtemp.periodto = request.POST['id_periodto'] if request.POST['id_periodto'] != '' else None
        itemtemp.noofpax = request.POST['id_noofpax'] if request.POST['id_noofpax'] != '' else None
        itemtemp.modifyby = request.user
        itemtemp.save()
        data = {
            'status': 'success',
            'itemtempid': itemtemp.pk,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def deleteitemtemp(request):
    if request.method == 'POST':
        itemtemptodelete = Ofitemtemp.objects.get(pk=request.POST['id_itemtemp'])
        if itemtemptodelete.ofmain is None:
            itemtemptodelete.delete()
        else:
            itemtemptodelete.isdeleted = 1
            itemtemptodelete.save()
        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def updateitemtemp(request):
    if request.method == 'POST':
        items = json.loads(request.POST['temp_items'])

        item_zip = zip(items[0]['id'], items[0]['vat'], items[0]['atc'], items[0]['inputvattype'],
                       items[0]['deferredvat'], items[0]['remarks'], items[0]['currency'], items[0]['fxrate'],
                       items[0]['itemstatus'], items[0]['supplier'], items[0]['tin'])

        for z_id, z_vat, z_atc, z_inputvattype, z_deferredvat, z_remarks, z_currency, z_fxrate, z_itemstatus, \
                z_supplier, z_tin in item_zip:
            item_to_update = Ofitemtemp.objects.get(pk=z_id)
            item_to_update.vat = int(z_vat) if z_vat else None
            item_to_update.vatrate = Vat.objects.get(pk=int(z_vat)).rate if z_vat else None
            item_to_update.atc = int(z_atc) if z_atc else None
            item_to_update.atcrate = Ataxcode.objects.get(pk=int(z_atc)).rate if z_atc else None
            item_to_update.inputvattype = int(z_inputvattype) if z_inputvattype else None
            item_to_update.deferredvat = z_deferredvat
            item_to_update.remarks = z_remarks
            item_to_update.currency = int(z_currency) if z_currency else None
            item_to_update.fxrate = float(z_fxrate) if z_fxrate else None
            item_to_update.ofitemstatus = z_itemstatus
            item_to_update.supplier = int(z_supplier) if z_supplier else None
            item_to_update.supplier_code = Supplier.objects.get(pk=int(z_supplier)).code if z_supplier else None
            item_to_update.supplier_name = Supplier.objects.get(pk=int(z_supplier)).name if z_supplier else None
            item_to_update.tin = z_tin
            item_to_update.modifyby = request.user
            item_to_update.modifydate = datetime.datetime.now()
            item_to_update.save()

        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def autoentry(request):
    if request.method == 'POST':
        # set isdeleted=2 for existing detailtemp data
        data_table = validatetable(request.POST['table'])
        updateallquery(request.POST['table'], request.POST['ofnum'])
        deleteallquery(request.POST['table'], request.POST['secretkey'])
        # set isdeleted=2 for existing detailtemp data

        main = Ofmain.objects.get(ofnum=request.POST['ofnum'])
        items = Ofitemtemp.objects.filter(isdeleted=0, secretkey=request.POST['secretkey'], ofitemstatus='A').\
            order_by('item_counter')
        item_counter = 1
        total_amount = 0

        # START-------------------- Operational Fund Automatic Entries ----------------------START
        # Entries:
        #   1. DEBIT Entries: Chart of Account based on OF Subtype containing gross amount and
        #       Chart of Account based on VAT containing VAT amount
        #   2. CREDIT Entry: Chart of Account based on OF Type
        #
        # DEBIT Entries:
        #   - Loop through the approved items in OFITEMTEMP
        #   - Create new Ofdetailtemp() object
        #   - Get the Requestor's Department
        #   - Get the Expense Chart of Account of Department
        #   - Get the Debit Chart of Account of the selected OF Subtype which has the Account Code that matches the
        #       first two characters of the Account Code of the Department's Chart of Account
        #   - Debit Amount = amount of the item * (1 + vatrate/100)
        #   - Increment item_counter
        #   - Save Ofdetailtemp()
        #   - Create new Ofdetailtemp() object
        #   - Get the Input VAT Chart of Account from the Parameter table if VAT rate is not 0
        #   - Input VAT = first Input VAT entry that matches the Input VAT Type of the item
        #   - Debit Amount = VAT amount (amount * vatrate/100)
        #   - Increment item_counter
        #   - Save Ofdetailtemp()
        #   - Compute total_amount
        #
        # CREDIT Entry:
        #   - Get the Credit Chart of Account of the selected OF Type
        #   - Bank Account = assigned bank account of the selected branch
        #   - Credit Amount = total_amount
        #
        # ######## START----------- DEBIT entries ------------START
        department_expchartofaccount_accountcode_prefix = str(Chartofaccount.objects.get(pk=Department.objects.get(
            pk=int(request.POST['department'])).expchartofaccount_id).accountcode)[:2]
        for data in items:
            if str(Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpcostofsale.
                    accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                debit_chartofaccount = Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpcostofsale.id
            elif str(Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpgenandadmin.
                     accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                debit_chartofaccount = Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpgenandadmin.id
            elif str(Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpsellexp.
                     accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                debit_chartofaccount = Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpsellexp.id
            else:
                debit_chartofaccount = Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpcostofsale.id
            ofdetailtemp1 = Ofdetailtemp()
            ofdetailtemp1.item_counter = item_counter
            ofdetailtemp1.of_date = main.ofdate
            ofdetailtemp1.ofitem = data.ofitem
            ofdetailtemp1.secretkey = request.POST['secretkey']
            ofdetailtemp1.chartofaccount = debit_chartofaccount
            gross_amount = float(data.amount) / (1 + (float(data.vatrate) / 100.0))
            ofdetailtemp1.debitamount = gross_amount
            ofdetailtemp1.balancecode = 'D'
            ofdetailtemp1.enterby = request.user
            ofdetailtemp1.modifyby = request.user
            ofdetailtemp1.save()
            chart_of_account1 = Chartofaccount.objects.get(pk=debit_chartofaccount)
            getacctgentrydetails(chart_of_account1, ofdetailtemp1, data, int(request.POST['branch']),
                                 int(request.POST['department']), int(request.POST['employee']))
            item_counter += 1

            if data.vatrate > 0:
                ofdetailtemp2 = Ofdetailtemp()
                ofdetailtemp2.item_counter = item_counter
                ofdetailtemp2.of_date = main.ofdate
                ofdetailtemp2.ofitem = data.ofitem
                ofdetailtemp2.secretkey = request.POST['secretkey']
                ofdetailtemp2.chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat_id
                ofdetailtemp2.debitamount = gross_amount * (float(data.vatrate) / 100.0)
                ofdetailtemp2.balancecode = 'D'
                ofdetailtemp2.enterby = request.user
                ofdetailtemp2.modifyby = request.user
                ofdetailtemp2.save()
                chart_of_account2 = Chartofaccount.objects.get(pk=Companyparameter.objects.get(code='PDI').coa_inputvat_id)
                getacctgentrydetails(chart_of_account2, ofdetailtemp2, data, int(request.POST['branch']),
                                     int(request.POST['department']), int(request.POST['employee']))
                item_counter += 1

            total_amount += data.amount
        # ######## END----------- DEBIT entries ------------END
        #
        # ######## START----------- CREDIT entry ------------START
        ofdetailtemp3 = Ofdetailtemp()
        ofdetailtemp3.item_counter = item_counter
        ofdetailtemp3.of_date = main.ofdate
        ofdetailtemp3.secretkey = request.POST['secretkey']
        ofdetailtemp3.chartofaccount = Oftype.objects.get(pk=int(request.POST['oftype'])).creditchartofaccount_id
        ofdetailtemp3.creditamount = float(total_amount)
        ofdetailtemp3.balancecode = 'C'
        ofdetailtemp3.enterby = request.user
        ofdetailtemp3.modifyby = request.user
        ofdetailtemp3.save()
        chart_of_account3 = Chartofaccount.objects.get(pk=Oftype.objects.get(pk=int(request.POST['oftype'])).
                                                       creditchartofaccount_id)
        getacctgentrydetails(chart_of_account3, ofdetailtemp3, data, int(request.POST['branch']),
                             int(request.POST['department']), int(request.POST['employee']))
        # ######## END----------- CREDIT entry ------------END
        # END-------------------- Operational Fund Automatic Entries ----------------------END

        context = {
            'tabledetailtemp': data_table['str_detailtemp'],
            'tablebreakdowntemp': data_table['str_detailbreakdowntemp'],
            'datatemp': querystmtdetail(data_table['str_detailtemp'], request.POST['secretkey']),
            'datatemptotal': querytotaldetail(data_table['str_detailtemp'], request.POST['secretkey']),
        }

        data = {
            'datatable': render_to_string('acctentry/datatable.html', context),
            'status': 'success'
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def approve(request):
    if request.method == 'POST':
        of_for_approval = Ofmain.objects.get(pk=request.POST['ofid'])
        approver_status = Employee.objects.get(user_id=request.user).of_approver
        if request.user.has_perm('operationalfund.approve_allof') or \
                request.user.has_perm('operationalfund.approve_assignedof'  or approver_status == 3):
            if request.user.has_perm('operationalfund.approve_allof') or \
                    (request.user.has_perm('operationalfund.approve_assignedof') and
                     of_for_approval.designatedapprover.user == request.user or approver_status == 3):
                print 'asda'
                if of_for_approval.ofstatus != 'I' and of_for_approval.ofstatus != 'R':
                    of_for_approval.ofstatus = request.POST['response']

                    of_for_approval.isdeleted = 0

                    if approver_status == 1:
                        of_for_approval.ofstatus = 'H'
                        capprover = Employee.objects.filter(of_approver=3,group=Employee.objects.get(user_id=request.user).group).first()

                        print capprover.email
                        ''' Send Email Notifacation OIC Approved '''
                        print 'send email notification'
                        subject = 'OPERATIONAL FUND APPROVER NOTIFICATION - OIC'
                        message = 'Hi Sir, \n\n' \
                                  'Requestor ' + str(of_for_approval.requestor_name) + ' has filed Operational Fund Request for your approval. \n\n' \
                                                          'Click link here: https://fin101bss.inquirer.com.ph/operationalfund'
                        email_from = 'inq-noreply@inquirer.com.ph'
                        recipient_list = [capprover.email]
                        #recipient_list = ['reykennethdmolina@gmail.com']
                        send_mail(subject, message, email_from, recipient_list)


                        print 'email sent'
                    else:
                        of_for_approval.ofstatus = request.POST['response']

                    if request.POST['response'] == 'D':
                        of_for_approval.status = 'C'
                        of_for_approval.ofstatus = 'D'
                    else:
                        of_for_approval.status = 'A'
                    of_for_approval.approverresponse = request.POST['response']
                    of_for_approval.responsedate = datetime.datetime.now()
                    of_for_approval.actualapprover = get_object_or_None(Employee, user=request.user)
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
def releaseof(request):
    if request.method == 'POST':
        offorrelease = Ofmain.objects.get(ofnum=request.POST['ofnum'])
        offorrelease.releaseby = request.user
        offorrelease.releasedate = request.POST['ofreleasedon']
        offorrelease.paymentreceivedby = Employee.objects.get(pk=request.POST['ofreleasedto'])
        offorrelease.paymentreceiveddate = request.POST['ofreleasedon']
        offorrelease.ofstatus = 'R'
        offorrelease.save()
        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def getacctgentrydetails(chartofaccount, ofdetailtemp, ofitemtemp, branch, department, employee):
    if chartofaccount.ataxcode_enable == 'Y':
        ofdetailtemp.ataxcode = ofitemtemp.atc
    if chartofaccount.bankaccount_enable == 'Y':
        ofdetailtemp.bankaccount = Branch.objects.get(pk=branch).bankaccount_id if Branch.objects.get(pk=branch).\
            bankaccount else Companyparameter.objects.get(code='PDI').def_bankaccount_id
    if chartofaccount.branch_enable == 'Y':
        ofdetailtemp.branch = branch
    if chartofaccount.customer_enable == 'Y':
        ofdetailtemp.customer = None
    if chartofaccount.department_enable == 'Y':
        ofdetailtemp.department = department
    if chartofaccount.employee_enable == 'Y':
        ofdetailtemp.employee = employee
    if chartofaccount.inputvat_enable == 'Y':
        ofdetailtemp.inputvat = Inputvat.objects.filter(inputvattype=ofitemtemp.inputvattype).first().id
    if chartofaccount.outputvat_enable == 'Y':
        ofdetailtemp.outputvat = None
    if chartofaccount.product_enable == 'Y':
        ofdetailtemp.product = None
    if chartofaccount.supplier_enable == 'Y':
        ofdetailtemp.supplier = ofitemtemp.supplier
    if chartofaccount.unit_enable == 'Y':
        ofdetailtemp.unit = None
    if chartofaccount.vat_enable == 'Y':
        ofdetailtemp.vat = ofitemtemp.vat
    if chartofaccount.wtax_enable == 'Y':
        ofdetailtemp.wtax = None

    ofdetailtemp.save()


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_xls = ''
    report_total = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        report_type = "Operational Fund Summary"
        report_xls = "OF Summary"
        query = Ofmain.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ofnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofdate__lte=key_data)

        if request.COOKIES.get('rep_f_rdatefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_rdatefrom_' + request.resolver_match.app_name))
            query = query.filter(releasedate__gte=key_data)
        if request.COOKIES.get('rep_f_rdateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_rdateto_' + request.resolver_match.app_name))
            query = query.filter(releasedate__lte=key_data)

        if request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name))
            query = query.filter(oftype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(branch=int(key_data))
        if request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name))
            query = query.filter(ofstatus=str(key_data))

        if request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name))
            query = query.filter(requestor=int(key_data))
        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(department=int(key_data))
        if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
            query = query.filter(Q(actualapprover=int(key_data)), Q(designatedapprover=int(key_data)))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        report_type = "Operational Fund Detailed"
        report_xls = "OF Detailed"
        query = Ofitem.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofdate__lte=key_data)

        if request.COOKIES.get('rep_f_rdatefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_rdatefrom_' + request.resolver_match.app_name))
            query = query.filter(releasedate__gte=key_data)
        if request.COOKIES.get('rep_f_rdateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_rdateto_' + request.resolver_match.app_name))
            query = query.filter(releasedate__lte=key_data)

        if request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name))
            query = query.filter(ofmain__oftype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(ofmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofstatus=str(key_data))

        if request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name))
            query = query.filter(ofmain__requestor=int(key_data))
        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(ofmain__department=int(key_data))
        if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
            query = query.filter(Q(ofmain__actualapprover=int(key_data)), Q(ofmain__designatedapprover=int(key_data)))

        if request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name))
            query = query.filter(ofsubtype=int(key_data))
        if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
            query = query.filter(Q(payee_code__icontains=key_data) | Q(payee_name__icontains=key_data)
                                 | Q(supplier_code__icontains=key_data) | Q(supplier_name__icontains=key_data))
        if request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name))
            query = query.filter(ofitemstatus=str(key_data))
        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(vat=int(key_data))
        if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
            query = query.filter(inputvattype=int(key_data))
        if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
            query = query.filter(atc=int(key_data))
        if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
            query = query.filter(deferredvat=str(key_data))

        if request.COOKIES.get('rep_f_order2_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order2_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get(
                    'rep_f_report_' + request.resolver_match.app_name) == 'ae':
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
            report_type = "Operational Fund Unbalanced Entries"
            report_xls = "OF Unbalanced Entries"
        else:
            report_type = "Operational Fund All Entries"
            report_xls = "OF All Entries"

        query = Ofdetail.objects.filter(isdeleted=0, ofmain__isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofdate__lte=key_data)

        if request.COOKIES.get('rep_f_rdatefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_rdatefrom_' + request.resolver_match.app_name))
            query = query.filter(releasedate__gte=key_data)
        if request.COOKIES.get('rep_f_rdateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_rdateto_' + request.resolver_match.app_name))
            query = query.filter(releasedate__lte=key_data)

        if request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name))
            query = query.filter(ofmain__oftype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(ofmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofstatus=str(key_data))

        if request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name))
            query = query.filter(ofmain__requestor=int(key_data))
        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(ofmain__department=int(key_data))
        if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
            query = query.filter(Q(ofmain__actualapprover=int(key_data)), Q(ofmain__designatedapprover=int(key_data)))

        query = query.values('ofmain__ofnum') \
            .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),
                      creditsum=Sum('creditamount')) \
            .values('ofmain__ofnum', 'margin', 'ofmain__ofdate', 'debitsum', 'creditsum', 'ofmain__pk').order_by('ofmain__ofnum')

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
            query = query.exclude(margin=0)

        if request.COOKIES.get('rep_f_uborder_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_uborder_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)

        report_total = query.aggregate(Sum('debitsum'), Sum('creditsum'), Sum('margin'))

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        query = Ofdetail.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name) != 'null':
            gl_request = request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name)

            query = query.filter(chartofaccount=int(gl_request))

            enable_check = Chartofaccount.objects.get(pk=gl_request)
            if enable_check.bankaccount_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name)
                query = query.filter(bankaccount=get_object_or_None(Bankaccount, pk=int(gl_item)))
            if enable_check.department_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name)
                query = query.filter(department=get_object_or_None(Department, pk=int(gl_item)))
            if enable_check.unit_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name)
                query = query.filter(unit=get_object_or_None(Unit, pk=int(gl_item)))
            if enable_check.branch_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name)
                query = query.filter(branch=get_object_or_None(Branch, pk=int(gl_item)))
            if enable_check.product_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name)
                query = query.filter(product=get_object_or_None(Product, pk=int(gl_item)))
            if enable_check.inputvat_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name)
                query = query.filter(inputvat=get_object_or_None(Inputvat, pk=int(gl_item)))
            if enable_check.outputvat_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name)
                query = query.filter(outputvat=get_object_or_None(Outputvat, pk=int(gl_item)))
            if enable_check.vat_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name)
                query = query.filter(vat=get_object_or_None(Vat, pk=int(gl_item)))
            if enable_check.wtax_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name)
                query = query.filter(wtax=get_object_or_None(Wtax, pk=int(gl_item)))
            if enable_check.ataxcode_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name)
                query = query.filter(ataxcode=get_object_or_None(Ataxcode, pk=int(gl_item)))
            if enable_check.employee_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name)
                query = query.filter(employee=get_object_or_None(Employee, pk=int(gl_item)))
            if enable_check.supplier_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name)
                query = query.filter(supplier=get_object_or_None(Supplier, pk=int(gl_item)))
            if enable_check.customer_enable == 'Y' \
                    and request.COOKIES.get('rep_f_gl_customer_' + request.resolver_match.app_name) \
                    and request.COOKIES.get('rep_f_gl_customer_' + request.resolver_match.app_name) != 'null':
                gl_item = request.COOKIES.get('rep_f_gl_customer_' + request.resolver_match.app_name)
                query = query.filter(customer=get_object_or_None(Customer, pk=int(gl_item)))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
            if request.COOKIES.get('rep_f_debit_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_debit_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(debitamount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_debit_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_debit_amountto_' + request.resolver_match.app_name))
                query = query.filter(debitamount__lte=float(key_data.replace(',', '')))

            if request.COOKIES.get('rep_f_credit_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_credit_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(creditamount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_credit_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_credit_amountto_' + request.resolver_match.app_name))
                query = query.filter(creditamount__lte=float(key_data.replace(',', '')))

        if request.COOKIES.get('rep_f_balancecode_' + request.resolver_match.app_name) == 'd':
            query = query.filter(balancecode='D')
        elif request.COOKIES.get('rep_f_balancecode_' + request.resolver_match.app_name) == 'c':
            query = query.filter(balancecode='C')

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofdate__lte=key_data)

        if request.COOKIES.get('rep_f_rdatefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_rdatefrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__releasedate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_rdateto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__releasedate__lte=key_data)

        if request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name))
            query = query.filter(ofmain__oftype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(ofmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofstatus=str(key_data))

        if request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name))
            query = query.filter(ofmain__requestor=int(key_data))
        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(ofmain__department=int(key_data))
        if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
            query = query.filter(Q(ofmain__actualapprover=int(key_data)), Q(designatedapprover=int(key_data)))

        if request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name))
            query = query.filter(ofitem__ofsubtype=int(key_data))
        if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
            query = query.filter(Q(ofitem__payee_code__icontains=key_data) | Q(ofitem__payee_name__icontains=key_data)
                                 | Q(supplier__code__icontains=key_data) | Q(supplier__name__icontains=key_data))
        if request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name))
            query = query.filter(ofitem__ofitemstatus=str(key_data))
        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(ofitem__vat=int(key_data))
        if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
            query = query.filter(ofitem__inputvattype=int(key_data))
        if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
            query = query.filter(ofitem__atc=int(key_data))
        if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
            query = query.filter(ofitem__deferredvat=str(key_data))

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "Operational Fund Accounting Entry - Summary"
            report_xls = "OF Acctg Entry - Summary"

            # query = query.values('chartofaccount__accountcode',
            #                      'chartofaccount__title',
            #                      'chartofaccount__description',
            #                      'bankaccount__code',
            #                      'bankaccount__accountnumber',
            #                      'bankaccount__bank__code',
            #                      'department__departmentname',
            #                      'employee__firstname',
            #                      'employee__lastname',
            #                      'supplier__name',
            #                      'customer__name',
            #                      'unit__description',
            #                      'branch__description',
            #                      'product__description',
            #                      'inputvat__description',
            #                      'outputvat__description',
            #                      'vat__description',
            #                      'wtax__description',
            #                      'ataxcode__code',
            #                      'balancecode')\
            #              .annotate(Sum('debitamount'), Sum('creditamount'))\
            #              .order_by('-balancecode',
            #                        '-chartofaccount__accountcode',
            #                        'bankaccount__code',
            #                        'bankaccount__accountnumber',
            #                        'bankaccount__bank__code',
            #                        'department__departmentname',
            #                        'employee__firstname',
            #                        'supplier__name',
            #                        'customer__name',
            #                        'unit__description',
            #                        'branch__description',
            #                        'product__description',
            #                        'inputvat__description',
            #                        'outputvat__description',
            #                        '-vat__description',
            #                        'wtax__description',
            #                        'ataxcode__code')

            query = query.values('chartofaccount__accountcode',
                                 'chartofaccount__title',
                                 'chartofaccount__description',
                                 'bankaccount__code',
                                 'bankaccount__accountnumber',
                                 'bankaccount__bank__code',
                                 'department__code',
                                 'department__departmentname',
                                 'branch__description',
                                 'branch__code',
                                 'balancecode') \
                .annotate(Sum('debitamount'), Sum('creditamount')) \
                .order_by('-balancecode',
                          'branch__code',
                          'department__code',
                          'bankaccount__code',
                          'chartofaccount__accountcode')
        else:
            report_type = "Operational Fund Accounting Entry - Detailed"
            report_xls = "OF Acctg Entry - Detailed"

            query = query.annotate(Sum('debitamount'), Sum('creditamount')).order_by('-balancecode',
                                                                                     '-chartofaccount__accountcode',
                                                                                     'bankaccount__code',
                                                                                     'bankaccount__accountnumber',
                                                                                     'bankaccount__bank__code',
                                                                                     'department__departmentname',
                                                                                     'employee__firstname',
                                                                                     'supplier__name',
                                                                                     'customer__name',
                                                                                     'unit__description',
                                                                                     'branch__description',
                                                                                     'product__description',
                                                                                     'inputvat__description',
                                                                                     'outputvat__description',
                                                                                     '-vat__description',
                                                                                     'wtax__description',
                                                                                     'ataxcode__code',
                                                                                     'of_num')

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's' \
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(amount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
            query = query.filter(amount__lte=float(key_data.replace(',', '')))

        if request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name))

            if key_data == 'd':
                query = query.reverse()

        report_total = query.aggregate(Sum('amount'))\

    return query, report_type, report_total, report_xls


@csrf_exempt
def reportresultxlsx(request):
    # imports and workbook config
    import xlsxwriter
    try:
        import cStringIO as StringIO
    except ImportError:
        import StringIO
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)

    # query and default variables
    queryset, report_type, report_total, report_xls = reportresultquery(request)
    report_type = report_type if report_type != '' else 'OF Report'
    worksheet = workbook.add_worksheet(report_xls)
    bold = workbook.add_format({'bold': 1})
    bold_right = workbook.add_format({'bold': 1, 'align': 'right'})
    bold_center = workbook.add_format({'bold': 1, 'align': 'center'})
    money_format = workbook.add_format({'num_format': '#,##0.00'})
    bold_money_format = workbook.add_format({'num_format': '#,##0.00', 'bold': 1})
    worksheet.set_column(1, 1, 15)
    row = 0
    data = []

    # config: placement
    amount_placement = 0
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        amount_placement = 5
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        amount_placement = 9
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        amount_placement = 2
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 4
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        amount_placement = 15

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'OF Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Released Date', bold)
        worksheet.write('D1', 'Requestor', bold)
        worksheet.write('E1', 'Status', bold)
        worksheet.write('F1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.write('A1', 'OF Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Requestor', bold)
        worksheet.write('D1', 'Subtype', bold)
        worksheet.write('E1', 'Payee', bold)
        worksheet.write('F1', 'VAT', bold)
        worksheet.write('G1', 'ATC', bold)
        worksheet.write('H1', 'In/VAT', bold)
        worksheet.write('I1', 'Status', bold)
        worksheet.write('J1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        worksheet.write('A1', 'OF Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Debit', bold_right)
        worksheet.write('D1', 'Credit', bold_right)
        worksheet.write('E1', 'Margin', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        worksheet.merge_range('A1:B1', 'General Ledger', bold_center)
        worksheet.write('A2', 'Acct. Code', bold)
        worksheet.write('B2', 'Account Title', bold)
        worksheet.merge_range('C1:D1', 'Subsidiary Ledger', bold_center)
        worksheet.write('C2', 'Code', bold)
        worksheet.write('D2', 'Particulars', bold)
        worksheet.merge_range('E1:F1', 'Amount', bold_center)
        worksheet.write('E2', 'Debit', bold_right)
        worksheet.write('F2', 'Credit', bold_right)
        row += 1
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        worksheet.merge_range('A1:A2', 'Chart of Account', bold)
        worksheet.merge_range('B1:M1', 'Details', bold_center)
        worksheet.merge_range('N1:N2', 'Payee', bold)
        worksheet.merge_range('O1:O2', 'Date', bold)
        worksheet.merge_range('P1:P2', 'Debit', bold_right)
        worksheet.merge_range('Q1:Q2', 'Credit', bold_right)
        worksheet.write('B2', 'Bank Account', bold)
        worksheet.write('C2', 'Department', bold)
        worksheet.write('D2', 'Employee', bold)
        worksheet.write('E2', 'Customer', bold)
        worksheet.write('F2', 'Unit', bold)
        worksheet.write('G2', 'Branch', bold)
        worksheet.write('H2', 'Product', bold)
        worksheet.write('I2', 'Input VAT', bold)
        worksheet.write('J2', 'Output VAT', bold)
        worksheet.write('K2', 'VAT', bold)
        worksheet.write('L2', 'WTAX', bold)
        worksheet.write('M2', 'ATAX Code', bold)
        row += 1

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            data = [
                "OF-" + obj.oftype.code + "-" + obj.ofnum,
                DateFormat(obj.ofdate).format('Y-m-d'),
                DateFormat(obj.releasedate).format('Y-m-d'),
                obj.requestor.firstname + " " + obj.requestor.lastname,
                obj.get_ofstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            str_payee = obj.supplier_name if obj.supplier_name is not None else obj.payee_name
            str_atc = obj.atc.code if obj.atc else ''
            str_vat = obj.vat.code if obj.vat else ''
            str_inputvattype = obj.inputvattype.code if obj.inputvattype else ''

            data = [
                "OF-" + obj.ofmain.oftype.code + "-" + obj.ofmain.ofnum,
                DateFormat(obj.ofdate).format('Y-m-d'),
                obj.ofmain.requestor.firstname + " " + obj.ofmain.requestor.lastname,
                obj.ofsubtype.code,
                str_payee.upper(),
                str_vat,
                str_atc,
                str_inputvattype,
                obj.get_ofitemstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
            data = [
                obj['ofmain__ofnum'],
                DateFormat(obj['ofmain__ofdate']).format('Y-m-d'),
                obj['debitsum'],
                obj['creditsum'],
                obj['margin'],
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            bankaccount__code = obj['bankaccount__code'] if obj['bankaccount__code'] is not None else ''
            department__code = obj['department__code'] if obj['department__code'] is not None else ''
            branch__code = obj['branch__code'] if obj['branch__code'] is not None else ''
            bankaccount__accountnumber = obj['bankaccount__accountnumber'] if obj[
                                                                                  'bankaccount__accountnumber'] is not None else ''
            department__departmentname = obj['department__departmentname'] if obj[
                                                                                  'department__departmentname'] is not None else ''

            data = [
                obj['chartofaccount__accountcode'],
                obj['chartofaccount__description'],
                bankaccount__code + ' ' + department__code + ' ' + branch__code,
                bankaccount__accountnumber + ' ' + department__departmentname,
                obj['debitamount__sum'],
                obj['creditamount__sum'],
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
            str_firstname = obj.employee.firstname if obj.employee is not None else ''
            str_lastname = obj.employee.lastname if obj.employee is not None else ''
            if obj.supplier is not None:
                str_payee = obj.supplier.name
            elif obj.ofitem is not None:
                if obj.ofitem.payee is not None:
                    str_payee = obj.ofitem.payee_name
                else:
                    str_payee = ''
            else:
                str_payee = ''

            data = [
                obj.chartofaccount.accountcode + " - " + obj.chartofaccount.description,
                obj.bankaccount.accountnumber if obj.bankaccount is not None else '',
                obj.department.departmentname if obj.department is not None else '',
                str_firstname + " " + str_lastname,
                obj.customer.name if obj.customer is not None else '',
                obj.unit.description if obj.unit is not None else '',
                obj.branch.description if obj.branch is not None else '',
                obj.product.description if obj.product is not None else '',
                obj.inputvat.description if obj.inputvat is not None else '',
                obj.outputvat.description if obj.outputvat is not None else '',
                obj.vat.description if obj.vat is not None else '',
                obj.wtax.description if obj.wtax is not None else '',
                obj.ataxcode.code if obj.ataxcode is not None else '',
                str_payee,
                DateFormat(obj.of_date).format('Y-m-d'),
                obj.debitamount__sum,
                obj.creditamount__sum,
            ]

        temp_amount_placement = amount_placement
        for col_num in xrange(len(data)):
            if col_num == temp_amount_placement:
                temp_amount_placement += 1
                worksheet.write_number(row, col_num, data[col_num], money_format)
            else:
                worksheet.write(row, col_num, data[col_num])

    # config: totals
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        data = [
            "", "", "", "",
            "Total", report_total['amount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        data = [
            "", "", "", "", "", "", "", "",
            "Total", report_total['amount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        data = [
            "",
            "Total", report_total['debitsum__sum'], report_total['creditsum__sum'], report_total['margin__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        data = [
            "", "", "",
            "Total", report_total['debitamount__sum'], report_total['creditamount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        data = [
            "", "", "", "", "", "", "", "", "", "", "", "", "", "",
            "Total", report_total['debitamount__sum'], report_total['creditamount__sum'],
        ]

    row += 1
    for col_num in xrange(len(data)):
        worksheet.write(row, col_num, data[col_num], bold_money_format)

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+report_xls+".xlsx"
    return response

@csrf_exempt
def searchforposting(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Ofmain.objects.filter(isdeleted=0,status='A',ofstatus='R',oftype_id=3).exclude(apmain_id__isnull=False).order_by('ofnum', 'ofdate')
        if dfrom != '':
            q = q.filter(ofdate__gte=dfrom)
        if dto != '':
            q = q.filter(ofdate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('operationalfund/postingresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def searchforpostingReim(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Ofmain.objects.filter(isdeleted=0,status='A',ofstatus='R',oftype_id=5).exclude(apmain_id__isnull=False).order_by('ofnum', 'ofdate')
        if dfrom != '':
            q = q.filter(ofdate__gte=dfrom)
        if dto != '':
            q = q.filter(ofdate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('operationalfund/postingresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def searchforpostingRev(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Ofmain.objects.filter(isdeleted=0,status='A',ofstatus='R',oftype_id=2).exclude(apmain_id__isnull=False).order_by('ofnum', 'ofdate')
        if dfrom != '':
            q = q.filter(ofdate__gte=dfrom)
        if dto != '':
            q = q.filter(ofdate__lte=dto)

        print q

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('operationalfund/postingresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def searchforpostingLiq(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Ofmain.objects.filter(isdeleted=0,status='A',ofstatus='R',oftype_id=6).exclude(jvmain_id__isnull=False).order_by('ofnum', 'ofdate')
        if dfrom != '':
            q = q.filter(ofdate__gte=dfrom)
        if dto != '':
            q = q.filter(ofdate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('operationalfund/postingresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def gopost(request):

    if request.method == 'POST':
        from django.db.models import CharField
        from django.db.models.functions import Length

        CharField.register_lookup(Length, 'length')

        ids = request.POST.getlist('ids[]')
        pdate = request.POST['postdate']

        data = Ofmain.objects.filter(pk__in=ids).filter(isdeleted=0,status='A',ofstatus='R')

        if data:
            for of in data:

                apnumlast = lastAPNumber('true')
                latestapnum = str(apnumlast[0])
                apnum = pdate[:4]
                last = str(int(latestapnum) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    apnum += '0'
                apnum += last

                # try:
                #     apnumlast = Apmain.objects.filter(apnum__length=10).latest('apnum')
                #     latestapnum = str(apnumlast)
                #     print latestapnum
                #     if latestapnum[0:4] == str(datetime.datetime.now().year):
                #         apnum = str(datetime.datetime.now().year)
                #         last = str(int(latestapnum[4:]) + 1)
                #         zero_addon = 6 - len(last)
                #         for x in range(0, zero_addon):
                #             apnum += '0'
                #         apnum += last
                #     else:
                #         apnum = str(datetime.datetime.now().year) + '000001'
                # except Apmain.DoesNotExist:
                #     apnum = str(datetime.datetime.now().year) + '000001'

                billingremarks = '';
                ofitem = Ofitem.objects.filter(ofmain=of.pk).order_by('item_counter')
                for item in ofitem:
                    billingremarks += str(item.payee_name) + ' billing period (' + str(item.periodfrom) + '-' + str(item.periodto) + '), '

                #main = Apmain.objects.get(pk=6939)
                employee = Employee.objects.get(pk=of.requestor_id)
                supplier = Supplier.objects.get(pk=employee.supplier_id)

                main = Apmain.objects.create(
                    apnum = apnum,
                    apdate = pdate,
                    aptype_id = 14, # Non-UB
                    apsubtype_id = 10, # Cellphone Subsidy
                    branch_id = 5, # Head Office
                    inputvattype_id = 3, # Service
                    creditterm_id = 2, # 90 Days 2
                    payee_id=supplier.id,
                    payeecode=supplier.code,
                    payeename=supplier.name,
                    vat_id = 8, # NA 8
                    vatcode = 'VATNA', # NA 8
                    vatrate = 0,
                    atax_id = 66, # NO ATC 66
                    ataxcode = 'WX000', # NO ATC 66
                    ataxrate = 0,
                    duedate = pdate,
                    refno = of.ofnum,
                    particulars = 'Cellphone Subsidy '+str(of.requestor_name)+' '+str(billingremarks),
                    currency_id = 1,
                    fxrate = 1,
                    designatedapprover_id = 225, # Arlene Astapan
                    actualapprover_id = 225, # Arlene Astapan
                    approverremarks = 'Automatic approval from Operational Fund Posting',
                    responsedate = datetime.datetime.now(),
                    apstatus = 'A',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )


                detail = Ofdetail.objects.filter(ofmain=of.pk).order_by('item_counter')
                counter = 1
                amount = 0
                for item  in detail:
                    amount += item.debitamount
                    Apdetail.objects.create(
                        apmain_id = main.id,
                        ap_num = main.apnum,
                        ap_date = main.apdate,
                        item_counter = counter,
                        debitamount = item.debitamount,
                        creditamount = item.creditamount,
                        balancecode = item.balancecode,
                        customerbreakstatus = item.customerbreakstatus,
                        supplierbreakstatus = item.supplierbreakstatus,
                        employeebreakstatus = item.employeebreakstatus,
                        ataxcode_id = item.ataxcode_id,
                        bankaccount_id = item.bankaccount_id,
                        branch_id = item.branch_id,
                        chartofaccount_id = item.chartofaccount_id,
                        customer_id = item.customer_id,
                        supplier_id = item.supplier_id,
                        department_id = item.department_id,
                        employee_id = item.employee_id,
                        inputvat_id = item.inputvat_id,
                        outputvat_id = item.outputvat_id,
                        product_id = item.product_id,
                        unit_id = item.unit_id,
                        vat_id = item.vat_id,
                        wtax_id = item.wtax_id,
                        status='A',
                        enterby_id = request.user.id,
                        enterdate = datetime.datetime.now(),
                        modifyby_id = request.user.id,
                        modifydate = datetime.datetime.now()
                    )
                    counter += 1

                main.amount = amount
                main.save()

                ofmain = Ofmain.objects.filter(id=of.pk).update(
                    apmain_id = main.id,
                    remarks = str(of.remarks)+' CS - AP '+str( main.apnum),
                )

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


@csrf_exempt
def gopostreim(request):

    if request.method == 'POST':
        from django.db.models import CharField
        from django.db.models.functions import Length

        CharField.register_lookup(Length, 'length')

        ids = request.POST.getlist('ids[]')
        pdate = request.POST['postdate']

        data = Ofmain.objects.filter(pk__in=ids).filter(isdeleted=0,status='A',ofstatus='R')

        if data:
            for of in data:
                apnumlast = lastAPNumber('true')
                latestapnum = str(apnumlast[0])
                apnum = pdate[:4]
                last = str(int(latestapnum) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    apnum += '0'
                apnum += last
                #try:
                #     apnumlast = Apmain.objects.filter(apnum__length=10).latest('apnum')
                #     latestapnum = str(apnumlast)
                #     print latestapnum
                #     if latestapnum[0:4] == str(datetime.datetime.now().year):
                #         apnum = str(datetime.datetime.now().year)
                #         last = str(int(latestapnum[4:]) + 1)
                #         zero_addon = 6 - len(last)
                #         for x in range(0, zero_addon):
                #             apnum += '0'
                #         apnum += last
                #     else:
                #         apnum = str(datetime.datetime.now().year) + '000001'
                # except Apmain.DoesNotExist:
                #     apnum = str(datetime.datetime.now().year) + '000001'

                billingremarks = '';

                employee = Employee.objects.get(pk=of.requestor_id)
                supplier = Supplier.objects.get(pk=employee.supplier_id)

                main = Apmain.objects.create(
                    apnum = apnum,
                    apdate = pdate,
                    aptype_id = 14, # Non-UB
                    apsubtype_id = 11, # Reimbursement
                    branch_id = 5, # Head Office
                    inputvattype_id = 3, # Service
                    creditterm_id = 2, # 90 Days 2
                    payee_id = supplier.id,
                    payeecode = supplier.code,
                    payeename = supplier.name,
                    vat_id = 8, # NA 8
                    vatcode = 'VATNA', # NA 8
                    vatrate = 0,
                    atax_id = 66, # NO ATC 66
                    ataxcode = 'WX000', # NO ATC 66
                    ataxrate = 0,
                    duedate = pdate,
                    refno = of.ofnum,
                    particulars = 'Reimbursement '+str(of.requestor_name)+' '+str(billingremarks),
                    currency_id = 1,
                    fxrate = 1,
                    designatedapprover_id = 225, # Arlene Astapan
                    actualapprover_id = 225, # Arlene Astapan
                    approverremarks = 'Automatic approval from Operational Fund Posting',
                    responsedate = datetime.datetime.now(),
                    apstatus = 'A',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )


                detail = Ofdetail.objects.filter(ofmain=of.pk).order_by('item_counter')
                counter = 1
                amount = 0

                for item  in detail:
                    amount += item.debitamount
                    sup = item.supplier_id
                    if item.chartofaccount_id == 285:
                        sup = supplier.id
                    Apdetail.objects.create(
                        apmain_id = main.id,
                        ap_num = main.apnum,
                        ap_date = main.apdate,
                        item_counter = counter,
                        debitamount = item.debitamount,
                        creditamount = item.creditamount,
                        balancecode = item.balancecode,
                        customerbreakstatus = item.customerbreakstatus,
                        supplierbreakstatus = item.supplierbreakstatus,
                        employeebreakstatus = item.employeebreakstatus,
                        ataxcode_id = item.ataxcode_id,
                        bankaccount_id = item.bankaccount_id,
                        branch_id = item.branch_id,
                        chartofaccount_id = item.chartofaccount_id,
                        customer_id = item.customer_id,
                        department_id = item.department_id,
                        supplier_id= sup,
                        employee_id = item.employee_id,
                        inputvat_id = item.inputvat_id,
                        outputvat_id = item.outputvat_id,
                        product_id = item.product_id,
                        unit_id = item.unit_id,
                        vat_id = item.vat_id,
                        wtax_id = item.wtax_id,
                        status='A',
                        enterby_id = request.user.id,
                        enterdate = datetime.datetime.now(),
                        modifyby_id = request.user.id,
                        modifydate = datetime.datetime.now()
                    )
                    counter += 1

                main.amount = amount
                main.save()

                ofmain = Ofmain.objects.filter(id=of.pk).update(
                    apmain_id = main.id,
                    remarks = str(of.remarks)+' REIM - AP '+str( main.apnum),
                )

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


@csrf_exempt
def gopostrev(request):

    if request.method == 'POST':
        from django.db.models import CharField
        from django.db.models.functions import Length

        CharField.register_lookup(Length, 'length')

        ids = request.POST.getlist('ids[]')
        pdate = request.POST['postdate']

        data = Ofmain.objects.filter(pk__in=ids).filter(isdeleted=0,status='A',ofstatus='R')

        if data:
            for of in data:
                apnumlast = lastAPNumber('true')
                latestapnum = str(apnumlast[0])
                apnum = pdate[:4]
                last = str(int(latestapnum) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    apnum += '0'
                apnum += last
                # try:
                #     apnumlast = Apmain.objects.filter(apnum__length=10).latest('apnum')
                #     latestapnum = str(apnumlast)
                #     print latestapnum
                #     if latestapnum[0:4] == str(datetime.datetime.now().year):
                #         apnum = str(datetime.datetime.now().year)
                #         last = str(int(latestapnum[4:]) + 1)
                #         zero_addon = 6 - len(last)
                #         for x in range(0, zero_addon):
                #             apnum += '0'
                #         apnum += last
                #     else:
                #         apnum = str(datetime.datetime.now().year) + '000001'
                # except Apmain.DoesNotExist:
                #     apnum = str(datetime.datetime.now().year) + '000001'

                billingremarks = '';

                employee = Employee.objects.get(pk=of.requestor_id)
                supplier = Supplier.objects.get(pk=employee.supplier_id)

                main = Apmain.objects.create(
                    apnum = apnum,
                    apdate = pdate,
                    aptype_id = 14, # Non-UB
                    apsubtype_id = 1, # Revolving
                    branch_id = 5, # Head Office
                    inputvattype_id = 3, # Service
                    creditterm_id = 2, # 90 Days 2
                    payee_id = supplier.id,
                    payeecode = supplier.code,
                    payeename = supplier.name,
                    vat_id = 8, # NA 8
                    vatcode = 'VATNA', # NA 8
                    vatrate = 0,
                    atax_id = 66, # NO ATC 66
                    ataxcode = 'WX000', # NO ATC 66
                    ataxrate = 0,
                    duedate = pdate,
                    refno = of.ofnum,
                    particulars = 'Revolving Fund '+str(of.requestor_name)+' '+str(billingremarks),
                    currency_id = 1,
                    fxrate = 1,
                    designatedapprover_id = 225, # Arlene Astapan
                    actualapprover_id = 225, # Arlene Astapan
                    approverremarks = 'Automatic approval from Operational Fund Posting',
                    responsedate = datetime.datetime.now(),
                    apstatus = 'A',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )


                detail = Ofdetail.objects.filter(ofmain=of.pk).order_by('item_counter')
                counter = 1
                amount = 0
                for item  in detail:
                    amount += item.debitamount
                    sup = item.supplier_id
                    if item.chartofaccount_id == 285:
                        sup = supplier.id
                    Apdetail.objects.create(
                        apmain_id = main.id,
                        ap_num = main.apnum,
                        ap_date = main.apdate,
                        item_counter = counter,
                        debitamount = item.debitamount,
                        creditamount = item.creditamount,
                        balancecode = item.balancecode,
                        customerbreakstatus = item.customerbreakstatus,
                        supplierbreakstatus = item.supplierbreakstatus,
                        employeebreakstatus = item.employeebreakstatus,
                        ataxcode_id = item.ataxcode_id,
                        bankaccount_id = item.bankaccount_id,
                        branch_id = item.branch_id,
                        chartofaccount_id = item.chartofaccount_id,
                        customer_id = item.customer_id,
                        department_id = item.department_id,
                        employee_id = item.employee_id,
                        inputvat_id = item.inputvat_id,
                        outputvat_id = item.outputvat_id,
                        product_id = item.product_id,
                        unit_id = item.unit_id,
                        supplier_id = sup,
                        vat_id = item.vat_id,
                        wtax_id = item.wtax_id,
                        status='A',
                        enterby_id = request.user.id,
                        enterdate = datetime.datetime.now(),
                        modifyby_id = request.user.id,
                        modifydate = datetime.datetime.now()
                    )
                    counter += 1

                main.amount = amount
                main.save()

                ofmain = Ofmain.objects.filter(id=of.pk).update(
                    apmain_id = main.id,
                    remarks = str(of.remarks)+' REV - AP '+str( main.apnum),
                )

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def gopostliq(request):

    if request.method == 'POST':
        from django.db.models import CharField
        from django.db.models.functions import Length

        CharField.register_lookup(Length, 'length')

        ids = request.POST.getlist('ids[]')
        pdate = request.POST['postdate']

        data = Ofmain.objects.filter(pk__in=ids).filter(isdeleted=0,status='A',ofstatus='R')

        if data:
            for of in data:
                jvnumlast = lastJVNumber('true')
                latestjvnum = str(jvnumlast[0])
                jvnum = pdate[:4]
                last = str(int(latestjvnum) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    jvnum += '0'
                jvnum += last

                # try:
                #     jvnumlast = Jvmain.objects.filter(jvnum__length=10).latest('jvnum')
                #     latestjvnum = str(jvnumlast)
                #     print latestjvnum
                #     if latestjvnum[0:4] == str(datetime.datetime.now().year):
                #         jvnum = str(datetime.datetime.now().year)
                #         last = str(int(latestjvnum[4:]) + 1)
                #         zero_addon = 6 - len(last)
                #         for x in range(0, zero_addon):
                #             jvnum += '0'
                #         jvnum += last
                #     else:
                #         jvnum = str(datetime.datetime.now().year) + '000001'
                # except Jvmain.DoesNotExist:
                #     jvnum = str(datetime.datetime.now().year) + '000001'

                print 'hoy'
                print jvnum

                billingremarks = '';

                main = Jvmain.objects.create(
                    jvnum = jvnum,
                    jvdate = pdate,
                    jvtype_id = 5, # Operational Fund
                    jvsubtype_id = 19, # Operational Fund - Liquidation
                    branch_id = 5, # Head Office
                    department_id = of.department_id, # NA 8
                    refnum = of.ofnum,
                    particular = 'Liquidation '+str(of.requestor_code)+' '+str(of.requestor_name),
                    currency_id = 1,
                    fxrate = 1,
                    designatedapprover_id = 225, # Arlene Astapan
                    actualapprover_id = 225, # Arlene Astapan
                    approverremarks = 'Auto approved from Operational Fund Posting',
                    responsedate = datetime.datetime.now(),
                    jvstatus = 'A',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )

                detail = Ofdetail.objects.filter(ofmain=of.pk).order_by('item_counter')
                counter = 1
                amount = 0
                for item  in detail:
                    amount += item.debitamount
                    Jvdetail.objects.create(
                        jvmain_id = main.id,
                        jv_num = main.jvnum,
                        jv_date = main.jvdate,
                        item_counter = counter,
                        debitamount = item.debitamount,
                        creditamount = item.creditamount,
                        balancecode = item.balancecode,
                        customerbreakstatus = item.customerbreakstatus,
                        supplierbreakstatus = item.supplierbreakstatus,
                        employeebreakstatus = item.employeebreakstatus,
                        ataxcode_id = item.ataxcode_id,
                        bankaccount_id = item.bankaccount_id,
                        branch_id = item.branch_id,
                        chartofaccount_id = item.chartofaccount_id,
                        customer_id = item.customer_id,
                        department_id = item.department_id,
                        employee_id = item.employee_id,
                        inputvat_id = item.inputvat_id,
                        outputvat_id = item.outputvat_id,
                        product_id = item.product_id,
                        unit_id = item.unit_id,
                        vat_id = item.vat_id,
                        wtax_id = item.wtax_id,
                        status='A',
                        enterby_id = request.user.id,
                        enterdate = datetime.datetime.now(),
                        modifyby_id = request.user.id,
                        modifydate = datetime.datetime.now()
                    )
                    counter += 1

                main.amount = amount
                main.save()

                ofmain = Ofmain.objects.filter(id=of.pk).update(
                    jvmain_id = main.id,
                    remarks = str(of.remarks)+' LIQ - JV '+str( main.jvnum),
                )

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        context = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        drfrom = request.GET['rfrom']
        drto = request.GET['rto']
        oftype = request.GET['oftype']
        requestor = request.GET['requestor']
        approver = request.GET['approver']
        department = request.GET['department']
        status = request.GET['status']
        remarks = request.GET['remarks']
        oftyped = Oftype.objects.filter(pk=oftype).first()
        print oftyped
        title = "Operation Fund - Summary"
        list = Ofmain.objects.filter(isdeleted=0).order_by('ofnum')[:0]
        datefrom = ''
        dateto = ''

        if report == '1':
            title = "Operation Fund - Summary | " + str(oftyped.description)
            q = Ofmain.objects.filter(isdeleted=0).order_by('ofnum', 'ofdate')
        elif report == '2':
            title = "Operation Fund - Detailed | " + str(oftyped.description)
            q = Ofitem.objects.select_related('ofmain').filter(isdeleted=0).order_by('ofnum', 'ofdate', 'item_counter')
        elif report == '3':
            title = "Operation Fund - Accounting Entry Summary | " + str(oftyped.description)
            q = Ofdetail.objects.filter(isdeleted=0).order_by('of_num', 'of_date')

        if dfrom != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__ofdate__gte=dfrom)
            else:
                q = q.filter(ofdate__gte=dfrom)
                datefrom = datetime.datetime.strptime(dfrom, '%Y-%m-%d')
        if dto != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__ofdate__lte=dto)
            else:
                q = q.filter(ofdate__lte=dto)
                dateto = datetime.datetime.strptime(dto, '%Y-%m-%d')

        if oftype != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__oftype=oftype)
            else:
                q = q.filter(oftype=oftype)

        if drfrom != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__releasedate__gte=datetime.datetime.strptime(drfrom, '%Y-%m-%d'))
            else:
                q = q.filter(releasedate__gte=datetime.datetime.strptime(drfrom, '%Y-%m-%d'))
        if drto != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__releasedate__lte=drto + ' 23:59:59')
            else:
                q = q.filter(releasedate__lte=drto+' 23:59:59')

        if status != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__ofstatus=status)
            else:
                q = q.filter(ofstatus=status)

        if requestor != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__requestor=requestor)
            else:
                q = q.filter(requestor=requestor)

        if approver != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__actualapprover=approver)
            else:
                q = q.filter(actualapprover=approver)

        if department != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__department=department)
            else:
                q = q.filter(department=department)

        if remarks != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__remarks__contains=remarks)
            else:
                q = q.filter(remarks__contains=remarks)

        if report == '3':
            list = q.values('chartofaccount__accountcode',
                                 'chartofaccount__description',
                                 'bankaccount__code',
                                 'branch__code',
                                 'department__departmentname',
                                 'employee__firstname',
                                 'employee__lastname',
                                 'supplier__name',
                                 'customer__name',
                                 'balancecode') \
                .annotate(Sum('debitamount'), Sum('creditamount')) \
                .order_by('-balancecode',
                          '-chartofaccount__accountcode')

        else:
            list = q

        if list:
            if report == '3':
                total = list.aggregate(total_debit=Sum('debitamount__sum'), total_credit=Sum('creditamount__sum'))
                print total
            else:
                total = list.aggregate(total_amount=Sum('amount'))


            #total = [] #list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))
        print list
        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "datefrom": datefrom,
            "oftype": oftype,
            "dateto": dateto,
            "username": request.user,
        }
        if report == '1':
            return Render.render('operationalfund/report/report_1.html', context)
        elif report == '2':
            return Render.render('operationalfund/report/report_2.html', context)
        elif report == '3':
            return Render.render('operationalfund/report/report_3.html', context)
        else:
            return Render.render('operationalfund/report/report_1.html', context)


@method_decorator(login_required, name='dispatch')
class GenerateExcel(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        context = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        drfrom = request.GET['rfrom']
        drto = request.GET['rto']
        oftype = request.GET['oftype']
        requestor = request.GET['requestor']
        approver = request.GET['approver']
        department = request.GET['department']
        status = request.GET['status']
        remarks = request.GET['remarks']
        oftyped = Oftype.objects.filter(pk=oftype).first()
        print oftyped
        title = "Operation Fund - Summary"
        list = Ofmain.objects.filter(isdeleted=0).order_by('ofnum')[:0]
        datefrom = ''
        dateto = ''

        if report == '1':
            title = "Operation Fund - Summary | " + str(oftyped.description)
            q = Ofmain.objects.filter(isdeleted=0).order_by('ofnum', 'ofdate')
        elif report == '2':
            title = "Operation Fund - Detailed | " + str(oftyped.description)
            q = Ofitem.objects.select_related('ofmain').filter(isdeleted=0).order_by('ofnum', 'ofdate', 'item_counter')
        elif report == '3':
            title = "Operation Fund - Accounting Entry Summary | " + str(oftyped.description)
            q = Ofdetail.objects.filter(isdeleted=0).order_by('of_num', 'of_date')

        if dfrom != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__ofdate__gte=dfrom)
            else:
                q = q.filter(ofdate__gte=dfrom)
                datefrom = datetime.datetime.strptime(dfrom, '%Y-%m-%d')
        if dto != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__ofdate__lte=dto)
            else:
                q = q.filter(ofdate__lte=dto)
                dateto = datetime.datetime.strptime(dto, '%Y-%m-%d')

        if oftype != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__oftype=oftype)
            else:
                q = q.filter(oftype=oftype)

        if drfrom != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__releasedate__gte=datetime.datetime.strptime(drfrom, '%Y-%m-%d'))
            else:
                q = q.filter(releasedate__gte=datetime.datetime.strptime(drfrom, '%Y-%m-%d'))
        if drto != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__releasedate__lte=drto + ' 23:59:59')
            else:
                q = q.filter(releasedate__lte=drto + ' 23:59:59')

        if status != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__ofstatus=status)
            else:
                q = q.filter(ofstatus=status)

        if requestor != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__requestor=requestor)
            else:
                q = q.filter(requestor=requestor)

        if approver != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__actualapprover=approver)
            else:
                q = q.filter(actualapprover=approver)

        if department != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__department=department)
            else:
                q = q.filter(department=department)

        if remarks != '':
            if report == '2' or report == '3':
                q = q.filter(ofmain__remarks__contains=remarks)
            else:
                q = q.filter(remarks__contains=remarks)

        if report == '3':
            list = q.values('chartofaccount__accountcode',
                            'chartofaccount__description',
                            'bankaccount__code',
                            'branch__code',
                            'department__departmentname',
                            'employee__firstname',
                            'employee__lastname',
                            'supplier__name',
                            'customer__name',
                            'balancecode') \
                .annotate(Sum('debitamount'), Sum('creditamount')) \
                .order_by('-balancecode',
                          '-chartofaccount__accountcode')

        else:
            list = q

        if list:
            if report == '3':
                total = list.aggregate(total_debit=Sum('debitamount__sum'), total_credit=Sum('creditamount__sum'))
                print total
            else:
                total = list.aggregate(total_amount=Sum('amount'))

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', 'OPERATIONAL FUND TRANSACTION LIST', bold)
        worksheet.write('A3', 'AS OF ' + str(dfrom) + ' to ' + str(dto), bold)

        filename = "operationalfund.xlsx"

        if report == '1':
            worksheet.write('A2', 'OPERATION FUND - SUMMARY', bold)

            # header
            worksheet.write('A4', 'OF Num', bold)
            worksheet.write('B4', 'OF Date', bold)
            worksheet.write('C4', 'Released/Posting', bold)
            worksheet.write('D4', 'Requestor', bold)
            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0
            total = 0

            for data in list:
                worksheet.write(row, col, 'OF'+str(data.oftype)+''+str(data.ofnum))
                worksheet.write(row, col + 1, data.ofdate, formatdate)
                worksheet.write(row, col + 2, data.releasedate, formatdate)
                worksheet.write(row, col + 3, data.requestor_name)
                worksheet.write(row, col + 4, float(format(data.amount, '.2f')))
                total += data.amount
                row += 1

            worksheet.write(row, col + 3, 'TOTAL', bold)
            worksheet.write(row, col + 4,  float(format(total, '.2f')), bold)

            filename = "operationalfundsummary.xlsx"

        elif report == '2':
            list = list.values('ofmain__ofnum', 'ofmain__ofdate', 'particulars', 'oftype__description', 'oftype__code',
                               'ofmain__requestor_name', 'ofmain__amount', 'ofsubtype__description', 'ofsubtype__code', 'payee_name',
                               'amount', 'periodfrom', 'periodto', 'remarks', 'refnum')
            dataset = pd.DataFrame.from_records(list)

            print dataset

            worksheet.write('A2', 'OPERATION FUND - DETAILED', bold)

            # header
            worksheet.write('A4', 'OF TYPE', bold)
            worksheet.write('B4', 'PAYEE', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0
            total = 0

            for ofnum, detail in dataset.fillna('NaN').groupby(['ofmain__ofnum', 'ofmain__ofdate', 'oftype__description', 'oftype__code', 'ofmain__requestor_name', 'ofmain__amount']):
                worksheet.write(row, col, 'OF' + str(ofnum[3]) + '' + str(ofnum[0]))
                worksheet.write(row, col + 1, str(ofnum[1]))
                worksheet.write(row, col + 2, str(ofnum[2]), formatdate)
                worksheet.write(row, col + 3, str(ofnum[4]))
                worksheet.write(row, col + 4, str(ofnum[5]))
                total += ofnum[5]
                row += 1
                for sub, data in detail.iterrows():
                    worksheet.write(row, col, data['ofsubtype__description'])
                    worksheet.write(row, col + 1, data['payee_name'])
                    #worksheet.write(row, col + 3, str(data['particulars'])+ ' '+str(data['periodfrom'])+ ' '+str(data['periodto'])+ ' '+str(data['refnum'])+ ' '+str(data['remarks']))
                    worksheet.write(row, col + 4, data['amount'])
                    row += 1
            worksheet.write(row, col + 3, 'TOTAL', bold)
            worksheet.write(row, col + 4, float(format(total, '.2f')), bold)

            filename = "operationalfunddetailed.xlsx"

        elif report == '3':
            worksheet.write('A2', 'OPERATION FUND - ACCOUNTING ENTRY SUMMARY', bold)

            # header
            worksheet.write('A4', 'Account', bold)
            worksheet.write('B4', 'Description', bold)
            worksheet.write('C4', 'Subledger', bold)
            worksheet.write('D4', 'Debit', bold)
            worksheet.write('E4', 'Credit', bold)

            row = 5
            col = 0
            debit = 0
            credit = 0
            bankacount = ''
            branch = ''
            department = ''
            firstname = ''
            lastname = ''
            supplier = ''
            customer = ''

            for data in list:

                if data['bankaccount__code']:
                    bankacount = data['bankaccount__code']
                if data['branch__code']:
                    branch = data['branch__code']
                if data['department__departmentname']:
                    department = data['department__departmentname']
                if data['employee__firstname']:
                    firstname = data['employee__firstname']
                if data['employee__lastname']:
                    lastname = data['employee__lastname']
                if data['supplier__name']:
                    supplier = data['supplier__name']
                if data['customer__name']:
                    customer = data['customer__name']

                worksheet.write(row, col, data['chartofaccount__accountcode'])
                worksheet.write(row, col + 1, data['chartofaccount__description'])
                #worksheet.write(row, col + 2, str(data['bankaccount__code'])+ ' ' +str(data['branch__code'])+ ' ' +str(data['department__departmentname'])+ ' ' +str(data['employee__firstname'])+ ' ' +str(data['employee__lastname'])+ ' ' +str(data['supplier__name'])+ ' ' +str(data['customer__name']))
                worksheet.write(row, col + 2, str(bankacount)+ ' ' +str(branch)+ ' ' +str(department)+ ' ' +str(firstname)+ ' ' +str(lastname)+ ' ' +str(supplier)+ ' ' +str(customer))
                worksheet.write(row, col + 3, float(format(data['debitamount__sum'], '.2f')))
                worksheet.write(row, col + 4, float(format(data['creditamount__sum'], '.2f')))
                debit += data['debitamount__sum']
                credit += data['creditamount__sum']
                row += 1

            worksheet.write(row, col + 2, 'TOTAL', bold)
            worksheet.write(row, col + 3,  float(format(debit, '.2f')), bold)
            worksheet.write(row, col + 4,  float(format(credit, '.2f')), bold)

            filename = "operationalfundaccountingentrysummary.xlsx"

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


def sendNotif(object):

    receiver = Employee.objects.filter(isdeleted=0, status='A',id=object.designatedapprover_id).first()
    print 'send email notification'
    subject = 'OPERATIONAL FUND APPROVER NOTIFICATION'
    message = 'Hi Sir, \n\n' \
              'Requestor '+str(object.requestor_name)+' has filed Operational Fund Request for your approval. \n\n' \
              'Click link here: https://fin101bss.inquirer.com.ph/operationalfund'
    email_from = 'inq-noreply@inquirer.com.ph'
    recipient_list = [receiver.email]
    send_mail( subject, message, email_from, recipient_list )

    print 'email sent'

    #return true
    #return redirect('redirect to a new page')

def upload(request):
    folder = 'media/ofupload/'
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        id = request.POST['dataid']
        fs = FileSystemStorage(location=folder)  # defaults to   MEDIA_ROOT
        filename = fs.save(myfile.name, myfile)

        upl = Ofupload(ofmain_id=id, filename=filename, enterby=request.user, modifyby=request.user)
        upl.save()

        uploaded_file_url = fs.url(filename)
        return HttpResponseRedirect('/operationalfund/' + str(id) )
    return HttpResponseRedirect('/operationalfund/' + str(id) )

def uploadhere(request):
    folder = 'media/ofupload/'
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        id = request.POST['dataid']
        fs = FileSystemStorage(location=folder)  # defaults to   MEDIA_ROOT
        filename = fs.save(myfile.name, myfile)

        upl = Ofupload(ofmain_id=id, filename=filename, enterby=request.user, modifyby=request.user)
        upl.save()

        uploaded_file_url = fs.url(filename)
        return HttpResponseRedirect('/operationalfund/' + str(id) +'/userupdate' )
    return HttpResponseRedirect('/operationalfund/' + str(id) +'/userupdate' )



@csrf_exempt
def filedelete(request):

    if request.method == 'POST':

        id = request.POST['id']
        fileid = request.POST['fileid']

        Ofupload.objects.filter(id=fileid).delete()

        return HttpResponseRedirect('/operationalfund/' + str(id) )

    return HttpResponseRedirect('/operationalfund/' + str(id) )


@csrf_exempt
def hrapprove(request):
    if request.method == 'POST':

        of_for_approval = Ofmain.objects.get(pk=request.POST['id'])

        if request.POST['status'] == 'A':
            of_for_approval.hrstatus = request.POST['status']
            of_for_approval.approverresponse = request.POST['status']
            of_for_approval.responsedate = datetime.datetime.now()
            of_for_approval.ofstatus = 'R'
            of_for_approval.save()

            aemp = Employee.objects.get(pk=request.user.id)
            of_for_approval.actualapprover_id = aemp.id
            of_for_approval.save()

            print of_for_approval.amount
            print of_for_approval.requestor_id
            print of_for_approval.requestor_name
            print 'update items'

            emp = Employee.objects.get(pk=of_for_approval.requestor_id)

            if of_for_approval.oftype_id == 10:
                print 'dependet'
                bal = emp.anti_dep_amount - of_for_approval.amount
                emp.anti_dep_amount = bal
                emp.anti_dep_date = datetime.datetime.now()
                emp.save()
            elif of_for_approval.oftype_id == 8:
                print 'eyeglass'
                emp.eyeglass_amount = of_for_approval.amount
                emp.eyeglass_date = datetime.datetime.now()
                emp.save()


            of_items = Ofitem.objects.filter(ofmain_id=request.POST['id'])
            print of_items

            input = 3
            if of_for_approval.oftype == 8:
                input = 3
            else:
                input = 2


            udept = Department.objects.get(pk=of_for_approval.department_id)
            expchart = Chartofaccount.objects.get(pk=udept.expchartofaccount_id)

            counter = 1
            if of_items:
                for itm in of_items:
                    updateitm = Ofitem.objects.get(pk=itm.id)
                    updateitm.vatrate = 0
                    updateitm.vat_id = 8
                    updateitm.inputvattype_id = input
                    updateitm.atc_id = 66
                    updateitm.atcrate    = 0
                    updateitm.vat_id = 8
                    updateitm.remarks = 'HR Approved'
                    updateitm.save()

                    ofsub = Ofsubtype.objects.get(pk=updateitm.ofsubtype_id)
                    expc = 0
                    if expchart.accountcode == '5100000000':
                        expc = ofsub.chartexpcostofsale_id
                    elif expchart.accountcode == '5200000000':
                        print 'GENERAL & ADMINISTRATIVE'
                        expc = ofsub.chartexpgenandadmin_id
                    else:
                        print 'SELLING EXPENSES'
                        expc = ofsub.chartexpsellexp_id


                    Ofdetail.objects.create(
                        ofmain_id=of_for_approval.id,
                        of_num=of_for_approval.ofnum,
                        of_date=of_for_approval.ofdate,
                        item_counter=counter,
                        debitamount=updateitm.amount,
                        creditamount=0,
                        balancecode='D',
                        chartofaccount_id=expc,
                        department_id=of_for_approval.department_id,
                        status='A',
                        enterby_id=request.user.id,
                        enterdate=datetime.datetime.now(),
                        modifyby_id=request.user.id,
                        modifydate=datetime.datetime.now()
                    )

                    counter += 1

            #supplier = Supplier.objects.get(pk=of_for_approval.requestor_id)
            print emp.supplier_id
            Ofdetail.objects.create(
                ofmain_id=of_for_approval.id,
                of_num=of_for_approval.ofnum,
                of_date=of_for_approval.ofdate,
                item_counter=counter,
                debitamount=0,
                creditamount=of_for_approval.amount,
                balancecode='C',
                chartofaccount_id=285,
                supplier_id=emp.supplier_id,
                status='A',
                enterby_id=request.user.id,
                enterdate=datetime.datetime.now(),
                modifyby_id=request.user.id,
                modifydate=datetime.datetime.now()
            )



        else:
            of_for_approval.hrstatus = request.POST['status']
            of_for_approval.save()


        # if of_for_approval.oftype_id == 10 or of_for_approval.oftype_id == 9 or of_for_approval.oftype_id == 8:
        #     #receiver = Employee.objects.filter(isdeleted=0, status='A', id=520).first()
        #     receiver = Employee.objects.filter(isdeleted=0, status='A', id=93).first()
        #     print 'send email notification'
        #     subject = 'OPERATIONAL FUND APPROVER NOTIFICATION - HR APPROVE'
        #     message = 'Hi Sir, \n\n' \
        #               'Requestor ' + str(
        #         of_for_approval.requestor_name) + ' has filed Operational Fund Request for your approval. \n\n' \
        #                                           'Click link here: https://fin101bss.inquirer.com.ph/operationalfund'
        #     email_from = 'inq-noreply@inquirer.com.ph'
        #     recipient_list = [receiver.email]
        #     send_mail(subject, message, email_from, recipient_list)
        #
        #     print 'email sent'
        # else:
        #
        #     ''' Send Email Notifacation '''
        #     receiver = Employee.objects.filter(isdeleted=0, status='A', id=self.object.designatedapprover_id).first()
        #     print 'send email notification'
        #     subject = 'OPERATIONAL FUND APPROVER NOTIFICATION'
        #     message = 'Hi Sir, \n\n' \
        #               'Requestor ' + str(
        #         self.object.requestor_name) + ' has filed Operational Fund Request for your approval. \n\n' \
        #                                       'Click link here: https://fin101bss.inquirer.com.ph/operationalfund'
        #     email_from = 'inq-noreply@inquirer.com.ph'
        #     recipient_list = [receiver.email]
        #     send_mail(subject, message, email_from, recipient_list)
        #
        #     print receiver.email
        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def hrapprove1(request):
    if request.method == 'POST':

        of_for_approval = Ofmain.objects.get(pk=request.POST['id'])

        of_for_approval.hr_approved_lvl1 = request.POST['status']
        of_for_approval.hr_approved_lvl1_by = request.user.id
        of_for_approval.hr_approved_lvl1_date = datetime.datetime.now()
        of_for_approval.save()

        if request.POST['status'] == 'D':
            of_for_approval.status = 'C'
            of_for_approval.save()
        else:
            receiver = Employee.objects.filter(isdeleted=0, status='A', id=520).first()
            print 'send email notification'
            subject = 'OPERATIONAL FUND APPROVER NOTIFICATION'
            message = 'Hi Sir, \n\n' \
                      'Requestor ' + str(of_for_approval.requestor_name) + ' has filed Operational Fund Request for your approval. \n\n' \
                                         'Click link here: https://fin101bss.inquirer.com.ph/operationalfund'
            email_from = 'inq-noreply@inquirer.com.ph'
            recipient_list = [receiver.email]
            send_mail(subject, message, email_from, recipient_list)

            print 'email sent'

        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def hrapprove2(request):
    if request.method == 'POST':

        of_for_approval = Ofmain.objects.get(pk=request.POST['id'])

        of_for_approval.hr_approved_lvl2 = request.POST['status']
        of_for_approval.hr_approved_lvl2_by = request.user.id
        of_for_approval.hr_approved_lvl2_date = datetime.datetime.now()
        of_for_approval.save()

        if request.POST['status'] == 'D':
            of_for_approval.status = 'C'
            of_for_approval.save()

        else:
            receiver = Employee.objects.filter(isdeleted=0, status='A', id=483).first()
            print 'send email notification'
            subject = 'OPERATIONAL FUND APPROVER NOTIFICATION'
            message = 'Hi Sir, \n\n' \
                      'Requestor ' + str(of_for_approval.requestor_name) + ' has filed Operational Fund Request for your approval. \n\n' \
                                         'Click link here: https://fin101bss.inquirer.com.ph/operationalfund'
            email_from = 'inq-noreply@inquirer.com.ph'
            recipient_list = [receiver.email]
            send_mail(subject, message, email_from, recipient_list)

            print 'email sent'

        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def nurseapprove(request):
    if request.method == 'POST':

        of_for_approval = Ofmain.objects.get(pk=request.POST['id'])

        of_for_approval.nurse_approved = request.POST['status']
        of_for_approval.nurse_approved_date = datetime.datetime.now()
        of_for_approval.save()

        if request.POST['status'] == 'D':
            of_for_approval.status = 'C'
            of_for_approval.save()
        else:
            receiver = Employee.objects.filter(isdeleted=0, status='A', id=811).first()
            #receiver = Employee.objects.filter(isdeleted=0, status='A', id=93).first()
            print 'send email notification'
            subject = 'OPERATIONAL FUND APPROVER NOTIFICATION'
            message = 'Hi Sir, \n\n' \
                      'Requestor ' + str(of_for_approval.requestor_name) + ' has filed Operational Fund Request for your approval. \n\n' \
                                         'Click link here: https://fin101bss.inquirer.com.ph/operationalfund'
            email_from = 'inq-noreply@inquirer.com.ph'
            recipient_list = [receiver.email]
            send_mail(subject, message, email_from, recipient_list)

            print 'email sent'

        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def searchforpostingEye(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']
        print 'eye'
        q = Ofmain.objects.filter(isdeleted=0,status='A',ofstatus='R',hrstatus='A',oftype_id=8).exclude(apmain_id__isnull=False).order_by('ofnum', 'ofdate')
        if dfrom != '':
            q = q.filter(ofdate__gte=dfrom)
        if dto != '':
            q = q.filter(ofdate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('operationalfund/postingresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def searchforpostingAntibiotic(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Ofmain.objects.filter(isdeleted=0,status='A',ofstatus='R',hrstatus='A',oftype_id__in=[9, 10]).exclude(apmain_id__isnull=False).order_by('ofnum', 'ofdate')
        if dfrom != '':
            q = q.filter(ofdate__gte=dfrom)
        if dto != '':
            q = q.filter(ofdate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('operationalfund/postingresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def goposteye(request):

    if request.method == 'POST':
        from django.db.models import CharField
        from django.db.models.functions import Length

        CharField.register_lookup(Length, 'length')

        ids = request.POST.getlist('ids[]')
        pdate = request.POST['postdate']

        data = Ofmain.objects.filter(pk__in=ids).filter(isdeleted=0,hrstatus='A',status='A',ofstatus='R')

        if data:
            for of in data:
                apnumlast = lastAPNumber('true')
                latestapnum = str(apnumlast[0])
                apnum = pdate[:4]
                last = str(int(latestapnum) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    apnum += '0'
                apnum += last
                # try:
                #     apnumlast = Apmain.objects.filter(apnum__length=10).latest('apnum')
                #     latestapnum = str(apnumlast)
                #     print latestapnum
                #     if latestapnum[0:4] == str(datetime.datetime.now().year):
                #         apnum = str(datetime.datetime.now().year)
                #         last = str(int(latestapnum[4:]) + 1)
                #         zero_addon = 6 - len(last)
                #         for x in range(0, zero_addon):
                #             apnum += '0'
                #         apnum += last
                #     else:
                #         apnum = str(datetime.datetime.now().year) + '000001'
                # except Apmain.DoesNotExist:
                #     apnum = str(datetime.datetime.now().year) + '000001'

                billingremarks = '';

                #main = Apmain.objects.get(pk=6939)
                employee = Employee.objects.get(pk=of.requestor_id)
                supplier = Supplier.objects.get(pk=employee.supplier_id)

                main = Apmain.objects.create(
                    apnum = apnum,
                    apdate = pdate,
                    aptype_id = 14, # Non-UB
                    apsubtype_id = 13, # Eyeglass
                    branch_id = 5, # Head Office
                    inputvattype_id = 3, # Service
                    creditterm_id = 2, # 90 Days 2
                    payee_id=supplier.id,
                    payeecode=supplier.code,
                    payeename=supplier.name,
                    vat_id = 8, # NA 8
                    vatcode = 'VATNA', # NA 8
                    vatrate = 0,
                    atax_id = 66, # NO ATC 66
                    ataxcode = 'WX000', # NO ATC 66
                    ataxrate = 0,
                    duedate = pdate,
                    refno = of.ofnum,
                    particulars = 'Eyeglass Subsidy '+str(of.requestor_name)+' '+str(billingremarks),
                    currency_id = 1,
                    fxrate = 1,
                    designatedapprover_id = 225, # Arlene Astapan
                    # actualapprover_id = 225, # Arlene Astapan
                    approverremarks = 'For approval from Operational Fund Posting',
                    responsedate = datetime.datetime.now(),
                    apstatus = 'F',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )


                detail = Ofdetail.objects.filter(ofmain=of.pk).order_by('item_counter')
                counter = 1
                amount = 0
                for item  in detail:
                    amount += item.debitamount
                    sup = item.supplier_id
                    if item.chartofaccount_id == 285:
                        sup = supplier.id
                    Apdetail.objects.create(
                        apmain_id = main.id,
                        ap_num = main.apnum,
                        ap_date = main.apdate,
                        item_counter = counter,
                        debitamount = item.debitamount,
                        creditamount = item.creditamount,
                        balancecode = item.balancecode,
                        customerbreakstatus = item.customerbreakstatus,
                        supplierbreakstatus = item.supplierbreakstatus,
                        employeebreakstatus = item.employeebreakstatus,
                        ataxcode_id = item.ataxcode_id,
                        bankaccount_id = item.bankaccount_id,
                        branch_id = item.branch_id,
                        chartofaccount_id = item.chartofaccount_id,
                        customer_id = item.customer_id,
                        department_id = item.department_id,
                        employee_id = item.employee_id,
                        inputvat_id = item.inputvat_id,
                        outputvat_id = item.outputvat_id,
                        product_id = item.product_id,
                        supplier_id= sup,
                        unit_id = item.unit_id,
                        vat_id = item.vat_id,
                        wtax_id = item.wtax_id,
                        status='A',
                        enterby_id = request.user.id,
                        enterdate = datetime.datetime.now(),
                        modifyby_id = request.user.id,
                        modifydate = datetime.datetime.now()
                    )
                    counter += 1

                main.amount = amount
                main.save()

                ofmain = Ofmain.objects.filter(id=of.pk).update(
                    apmain_id = main.id,
                    remarks = str(of.remarks)+' EYEGLASS SUBSIDY - AP '+str( main.apnum),
                )

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)\

@csrf_exempt
def gopostanti(request):

    if request.method == 'POST':
        from django.db.models import CharField
        from django.db.models.functions import Length

        CharField.register_lookup(Length, 'length')

        ids = request.POST.getlist('ids[]')
        pdate = request.POST['postdate']

        data = Ofmain.objects.filter(pk__in=ids).filter(isdeleted=0,hrstatus='A',status='A',ofstatus='R')

        if data:
            for of in data:
                apnumlast = lastAPNumber('true')
                latestapnum = str(apnumlast[0])
                apnum = pdate[:4]
                last = str(int(latestapnum) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    apnum += '0'
                apnum += last
                # try:
                #     apnumlast = Apmain.objects.filter(apnum__length=10).latest('apnum')
                #     latestapnum = str(apnumlast)
                #     print latestapnum
                #     if latestapnum[0:4] == str(datetime.datetime.now().year):
                #         apnum = str(datetime.datetime.now().year)
                #         last = str(int(latestapnum[4:]) + 1)
                #         zero_addon = 6 - len(last)
                #         for x in range(0, zero_addon):
                #             apnum += '0'
                #         apnum += last
                #     else:
                #         apnum = str(datetime.datetime.now().year) + '000001'
                # except Apmain.DoesNotExist:
                #     apnum = str(datetime.datetime.now().year) + '000001'

                billingremarks = '';

                #main = Apmain.objects.get(pk=6939)
                employee = Employee.objects.get(pk=of.requestor_id)
                supplier = Supplier.objects.get(pk=employee.supplier_id)

                main = Apmain.objects.create(
                    apnum = apnum,
                    apdate = pdate,
                    aptype_id = 14, # Non-UB
                    apsubtype_id = 14, # Antibiotic
                    branch_id = 5, # Head Office
                    inputvattype_id = 3, # Service
                    creditterm_id = 2, # 90 Days 2
                    payee_id=supplier.id,
                    payeecode=supplier.code,
                    payeename=supplier.name,
                    vat_id = 8, # NA 8
                    vatcode = 'VATNA', # NA 8
                    vatrate = 0,
                    atax_id = 66, # NO ATC 66
                    ataxcode = 'WX000', # NO ATC 66
                    ataxrate = 0,
                    duedate = pdate,
                    refno = of.ofnum,
                    particulars = 'Antibiotic Subsidy '+str(of.requestor_name)+' '+str(billingremarks),
                    currency_id = 1,
                    fxrate = 1,
                    designatedapprover_id = 225, # Arlene Astapan
                    # actualapprover_id = 225, # Arlene Astapan
                    approverremarks = 'For approval from Operational Fund Posting',
                    responsedate = datetime.datetime.now(),
                    apstatus = 'F',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )


                detail = Ofdetail.objects.filter(ofmain=of.pk).order_by('item_counter')
                counter = 1
                amount = 0
                dept = 93
                for item  in detail:
                    amount += item.debitamount
                    if item.chartofaccount_id == 285:
                        dept = ''
                    sup = item.supplier_id
                    if item.chartofaccount_id == 285:
                        sup = supplier.id
                    Apdetail.objects.create(
                        apmain_id = main.id,
                        ap_num = main.apnum,
                        ap_date = main.apdate,
                        item_counter = counter,
                        debitamount = item.debitamount,
                        creditamount = item.creditamount,
                        balancecode = item.balancecode,
                        customerbreakstatus = item.customerbreakstatus,
                        supplierbreakstatus = item.supplierbreakstatus,
                        employeebreakstatus = item.employeebreakstatus,
                        ataxcode_id = item.ataxcode_id,
                        bankaccount_id = item.bankaccount_id,
                        branch_id = item.branch_id,
                        chartofaccount_id = item.chartofaccount_id,
                        customer_id = item.customer_id,
                        department_id = dept, #item.department_id,
                        employee_id = item.employee_id,
                        inputvat_id = item.inputvat_id,
                        outputvat_id = item.outputvat_id,
                        product_id = item.product_id,
                        supplier_id = sup,
                        unit_id = item.unit_id,
                        vat_id = item.vat_id,
                        wtax_id = item.wtax_id,
                        status='A',
                        enterby_id = request.user.id,
                        enterdate = datetime.datetime.now(),
                        modifyby_id = request.user.id,
                        modifydate = datetime.datetime.now()
                    )
                    counter += 1

                main.amount = amount
                main.save()

                ofmain = Ofmain.objects.filter(id=of.pk).update(
                    apmain_id = main.id,
                    remarks = str(of.remarks)+' ANTIBIOTIC SUBSIDY - AP '+str( main.apnum),
                )

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)



def lastNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  SUBSTRING(ofnum, 5) AS num FROM ofmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]

def lastAPNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  SUBSTRING(apnum, 5) AS num FROM apmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]


def lastJVNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  SUBSTRING(jvnum, 5) AS num FROM jvmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
