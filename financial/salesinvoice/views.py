from django.views.generic import View, DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from adtype.models import Adtype
from ataxcode.models import Ataxcode
from bankbranchdisburse.models import Bankbranchdisburse
from branch.models import Branch
from companyparameter.models import Companyparameter
from module.models import Activitylogs
from cvsubtype.models import Cvsubtype
from operationalfund.models import Ofmain, Ofitem, Ofdetail
from replenish_pcv.models import Reppcvmain, Reppcvdetail
from supplier.models import Supplier
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from . models import Simain, Sidetail, Sidetailtemp, Sidetailbreakdown, Sidetailbreakdowntemp, Siupload
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
# from bankaccount.models import Bankaccount
from currency.models import Currency
from customer.models import Customer
from sitype.models import Sitype
from sisubtype.models import Sisubtype
from creditterm.models import Creditterm
from outputvattype.models import Outputvattype
from paytype.models import Paytype
# from processing_or.models import Logs_simain, Logs_ordetail
from vat.models import Vat
from wtax.models import Wtax
from django.template.loader import render_to_string
from easy_pdf.views import PDFTemplateView
from dateutil.relativedelta import relativedelta
import datetime
from pprint import pprint
from django.utils.dateformat import DateFormat
from utils.mixins import ReportContentMixin
from agent.models import Agent
from product.models import Product
from department.models import Department
from unit.models import Unit
from inputvat.models import Inputvat
from outputvat.models import Outputvat
from ataxcode.models import Ataxcode
from employee.models import Employee
from chartofaccount.models import Chartofaccount
from annoying.functions import get_object_or_None
import decimal
import pandas as pd
from django.utils.dateformat import DateFormat
from financial.utils import Render
from financial.context_processors import namedtuplefetchall
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from datetime import timedelta
import io
import xlsxwriter
import datetime
from django.template.loader import render_to_string
from django.core.files.storage import FileSystemStorage


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Simain
    template_name = 'salesinvoice/index.html'
    page_template = 'salesinvoice/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Simain.objects.all().filter(isdeleted=0)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(sinum__icontains=keysearch) |
                                    Q(sidate__icontains=keysearch) |
                                    Q(payee_name__icontains=keysearch) |
                                    Q(amount__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        # data for lookup
        context['sitype'] = Sitype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['accountexecutive'] = Employee.objects.filter(status='A', isdeleted=0).exclude(firstname='').order_by('firstname')
        context['customer'] = Customer.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['pk'] = 0
        # end data for lookup

        return context
    

@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Simain
    template_name = 'salesinvoice/create.html'
    fields = ['sidate', 'sitype', 'sisubtype', 'branch', 'creditterm', 'duedate', 
                'amount', 'amountinwords', 'customer', 'accountexecutive', 'vat', 'vatrate', 'outputvattype', 'wtaxrate', 'refno', 'designatedapprover',
                'particulars']
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('salesinvoice.add_simain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')

        # data for lookup
        context['sitype'] = Sitype.objects.filter(isdeleted=0).order_by('pk')
        context['sisubtype'] = Sisubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['customer'] = Customer.objects.filter(isdeleted=0).order_by('code')
        # context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Companyparameter.objects.get(code='PDI').si_creditterm
        context['accountexecutive'] = Employee.objects.filter(status='A', isdeleted=0).exclude(firstname='').order_by('firstname')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['pk'] = 0
        # data for lookup

        # closetransaction = Companyparameter.objects.all().first().last_closed_date
        # validtransaction = closetransaction + relativedelta(months=1)
        # context['validtransaction'] = validtransaction

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        
        year = str(form.cleaned_data['sidate'].year)
        sinumlast = lastNumber('true')

        latestsinum = str(sinumlast[0])
        sinum = year
        
        last = str(int(latestsinum) + 1)
        print last
        zero_addon = 6 - len(last)
        for num in range(zero_addon):
            sinum += '0'
        sinum += last
        
        self.object.sinum = sinum

        if self.request.POST['wtax'] == '':
            self.object.wtaxrate = 0
        else:
            self.object.wtaxrate = Wtax.objects.get(pk=int(self.request.POST['wtax'])).rate
        self.object.vatrate = Vat.objects.get(pk=int(self.request.POST['vat'])).rate
        
        self.object.accountexecutive_id = self.object.accountexecutive.id if self.object.accountexecutive else None
        self.object.customer_id =  self.object.customer.id or None

        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        non_vat_amount = decimal.Decimal(self.object.amount) / (1 + (decimal.Decimal(self.object.vatrate) /
                                                                        decimal.Decimal(100)) -
                                                                (decimal.Decimal(self.object.wtaxrate) /
                                                                    decimal.Decimal(100)))

        if self.object.vatrate > 0:
            self.object.vatablesale = non_vat_amount
            self.object.vatexemptsale = 0
            self.object.vatzeroratedsale = 0
        elif self.object.vat.code == "VE":
            self.object.vatexemptsale = non_vat_amount
            self.object.vatablesale = 0
            self.object.vatzeroratedsale = 0
        elif self.object.vat.code == "ZE":
            self.object.vatzeroratedsale = non_vat_amount
            self.object.vatexemptsale = 0
            self.object.vatablesale = 0
        elif self.object.vat.code == "VATNA":
            self.object.vatzeroratedsale = 0
            self.object.vatexemptsale = 0
            self.object.vatablesale = 0

        self.object.vatamount = non_vat_amount * (decimal.Decimal(self.object.vatrate) / decimal.Decimal(100))
        self.object.wtaxamount = non_vat_amount * (decimal.Decimal(self.object.wtaxrate) / decimal.Decimal(100))
        self.object.totalsale = non_vat_amount + self.object.vatamount - self.object.wtaxamount
        # self.object.collector_code = self.object.collector.code
        # self.object.collector_name = self.object.collector.name

        self.object.save()

        # if Sidetailtemp.objects.filter(secretkey=self.request.POST['secretkey']).count() == 0:
        #     addcashinbank(self.request.POST['secretkey'], self.object.totalsale, self.request.user)

        # save sidetailtemp to sidetail
        source = 'sidetailtemp'
        mainid = self.object.id
        num = self.object.sinum
        secretkey = self.request.POST['secretkey']

        simaindate = self.object.sidate
        savedetail(source, mainid, num, secretkey, self.request.user, simaindate)

        return HttpResponseRedirect('/salesinvoice/' + str(self.object.id) + '/update')
    
    
def lastNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT SUBSTRING(sinum, 5) AS num FROM simain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]

@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Simain
    template_name = 'salesinvoice/update.html'
    fields = ['sinum', 'sidate', 'sitype', 'sisubtype', 'branch', 'customer', 'creditterm', 'duedate', 'accountexecutive',
                'amount', 'amountinwords', 'vat', 'vatrate', 'outputvattype', 'wtax', 'wtaxrate', 'refno', 'designatedapprover',
                'particulars', 'remarks']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('salesinvoice.change_simain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # accounting entry starts here
    def get_initial(self):
        self.mysecretkey = generatekey(self)

        detailinfo = Sidetail.objects.filter(simain=self.object.pk).order_by('item_counter')

        for drow in detailinfo:
            detail = Sidetailtemp()
            detail.secretkey = self.mysecretkey
            detail.si_num = drow.si_num
            detail.simain = drow.simain_id
            detail.sidetail = drow.pk
            detail.item_counter = drow.item_counter
            detail.si_date = drow.si_date
            detail.chartofaccount = drow.chartofaccount_id
            # detail.bankaccount = drow.bankaccount_id
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

            breakinfo = Sidetailbreakdown.objects. \
                filter(sidetail_id=drow.id).order_by('pk', 'datatype')
            if breakinfo:
                for brow in breakinfo:
                    breakdown = Sidetailbreakdowntemp()
                    breakdown.si_num = drow.si_num
                    breakdown.secretkey = self.mysecretkey
                    breakdown.simain = drow.simain_id
                    breakdown.sidetail = drow.pk
                    breakdown.sidetailtemp = detailtempid
                    breakdown.sidetailbreakdown = brow.pk
                    breakdown.item_counter = brow.item_counter
                    breakdown.si_date = brow.si_date
                    breakdown.chartofaccount = brow.chartofaccount_id
                    breakdown.particular = brow.particular
                    # Return None if object is empty
                    breakdown.customer = brow.customer_id
                    breakdown.department = brow.department_id
                    breakdown.unit = brow.unit_id
                    breakdown.branch = brow.branch_id
                    breakdown.product = brow.product_id
                    breakdown.inputvat = brow.inputvat_id
                    breakdown.outputvat = brow.outputvat_id
                    breakdown.vat = brow.vat_id
                    breakdown.wtax = brow.wtax_id
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

        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['accountexecutive'] = Employee.objects.filter(status='A', isdeleted=0).exclude(firstname='').order_by('firstname')
        context['sinum'] = self.object.sinum
        context['footers'] = [self.object.enterby.first_name + " " + self.object.enterby.last_name if self.object.enterby else '',
                                self.object.enterdate,
                                self.object.modifyby.first_name + " " + self.object.modifyby.last_name if self.object.modifyby else '',
                                self.object.modifydate, 
                                self.object.postby.first_name + " " + self.object.postby.last_name if self.object.postby else '',
                                self.object.postdate,
                            #   self.object.closeby.first_name + " " + self.object.closeby.last_name if self.object.closeby else '',
                            #   self.object.closedate,
                            ]
        # context['logs'] = self.object.logs

        # if Logs_simain.objects.filter(orno=self.object.sinum, importstatus='P'):
        #     context['logs_simain'] = Logs_simain.objects.filter(orno=self.object.sinum, importstatus='P')
        #     context['logs_ordetail'] = Logs_ordetail.objects.filter(orno=self.object.sinum, importstatus='P',
        #                                                             batchkey=context['logs_simain'].first().batchkey)
        #     context['logs_sistatus'] = context['logs_simain'].first().status if context['logs_simain'] else ''

        # data for lookup
        context['sitype'] = Sitype.objects.filter(isdeleted=0).order_by('pk')
        context['sisubtype'] = Sisubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['creditterm'] = Companyparameter.objects.get(code='PDI').si_creditterm
        context['accountexecutive'] = Employee.objects.filter(status='A', isdeleted=0).exclude(firstname='').order_by('code')
        context['customer'] = Customer.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['pk'] = self.object.pk
        # data for lookup

        # accounting entry starts here
        context['secretkey'] = self.mysecretkey
        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'sidetailtemp',
            'tablebreakdowntemp': 'ordetailbreakdowntemp',

            'datatemp': querystmtdetail('sidetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('sidetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        # accounting entry ends here

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # if self.object.orsource == 'A':
        #     self.object.payee_type = self.request.POST['payee_adv']
        # elif self.object.orsource == 'C':
        #     self.object.payee_type = self.request.POST['payee_cir']

        # if self.object.payee_type == 'AG':
        #     self.object.agency = Customer.objects.get(pk=int(self.request.POST['agency']))
        #     self.object.client = None
        #     self.object.agent = None
        #     self.object.payee_code = self.object.agency.code
        #     self.object.payee_name = self.object.agency.name
        # elif self.object.payee_type == 'C':
        #     self.object.client = Customer.objects.get(pk=int(self.request.POST['client']))
        #     self.object.payee_code = self.object.client.code
        #     self.object.payee_name = self.object.client.name
        #     self.object.agency = None
        #     self.object.agent = None
        # elif self.object.payee_type == 'A':
        #     self.object.agent = Agent.objects.get(pk=int(self.request.POST['agent']))
        #     self.object.payee_code = self.object.agent.code
        #     self.object.payee_name = self.object.agent.name
        #     self.object.agency = None
        #     self.object.client = None

        if self.request.POST['wtax'] == '':
            self.object.wtaxrate = 0
        else:
            self.object.wtaxrate = Wtax.objects.get(pk=int(self.request.POST['wtax'])).rate

        self.object.vatrate = Vat.objects.get(pk=int(self.request.POST['vat'])).rate
        print 'hindaw', self.object.accountexecutive, self.object.customer
        self.object.accountexecutive_id = self.object.accountexecutive.id if self.object.accountexecutive else None
        self.object.customer_id =  self.object.customer.id or None
        self.object.acctentry_incomplete = 0
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['sidate', 'amount', 'amountinwords', 'accountexecutive', 'customer', 'vatrate', 'wtaxrate',
                                        'branch', 'sitype', 'vat', 'wtax', 'outputvattype', 'particulars', 'remarks', 
                                        'modifyby', 'modifydate', 'acctentry_incomplete'])

        non_vat_amount = decimal.Decimal(self.object.amount) / (1 + (decimal.Decimal(self.object.vatrate) /
                                                                     decimal.Decimal(100)) -
                                                                (decimal.Decimal(self.object.wtaxrate) /
                                                                 decimal.Decimal(100)))

        if self.object.vatrate > 0:
            self.object.vatablesale = non_vat_amount
            self.object.vatexemptsale = 0
            self.object.vatzeroratedsale = 0
        elif self.object.vat.code == "VE":
            self.object.vatexemptsale = non_vat_amount
            self.object.vatablesale = 0
            self.object.vatzeroratedsale = 0
        elif self.object.vat.code == "ZE":
            self.object.vatzeroratedsale = non_vat_amount
            self.object.vatexemptsale = 0
            self.object.vatablesale = 0
        elif self.object.vat.code == "VATNA":
            self.object.vatzeroratedsale = 0
            self.object.vatexemptsale = 0
            self.object.vatablesale = 0

        self.object.vatamount = non_vat_amount * (decimal.Decimal(self.object.vatrate) / decimal.Decimal(100))
        self.object.wtaxamount = non_vat_amount * (decimal.Decimal(self.object.wtaxrate) / decimal.Decimal(100))
        self.object.totalsale = non_vat_amount + self.object.vatamount - self.object.wtaxamount
        # self.object.collector_code = self.object.collector.code
        # self.object.collector_name = self.object.collector.name

        # if self.object.circulationproduct:
        #     self.object.circulationproduct_code = self.object.circulationproduct.code
        #     self.object.circulationproduct_name = self.object.circulationproduct.description

        self.object.save(update_fields=['vatamount', 'wtaxamount', 'vatablesale', 'vatexemptsale', 'vatzeroratedsale',
                                        'totalsale'])

        # save sidetailtemp to sidetail
        source = 'sidetailtemp'
        mainid = self.object.id
        num = self.object.sinum
        secretkey = self.request.POST['secretkey']
        simaindate = self.object.sidate

        updatedetail(source, mainid, num, secretkey, self.request.user, simaindate)

        # Save Activity Logs
        Activitylogs.objects.create(
            user_id=self.request.user.id,
            username=self.request.user,
            remarks='Update SI Transaction #' + self.object.sinum
        )

        return HttpResponseRedirect('/salesinvoice/'+str(self.object.id)+'/update')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Simain
    template_name = 'salesinvoice/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['detail'] = Sidetail.objects.filter(isdeleted=0). \
            filter(simain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Sidetail.objects.filter(isdeleted=0). \
            filter(simain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Sidetail.objects.filter(isdeleted=0). \
            filter(simain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['uploadlist'] = Siupload.objects.filter(simain_id=self.object.pk).order_by('enterdate')

        return context
    
    
def format_tin(tin):
    if '-' in tin:
        return tin
    
    tin = ''.join([c for c in tin if c.isdigit()])  # Remove any non-digit characters
    
    if len(tin) == 14 and tin.isdigit():
        print 'here'
        return tin[:3] + '-' + tin[3:6] + '-' + tin[6:9] + '-' + tin[9:]
    elif len(tin) < 14 and tin.isdigit():
        tin = tin.zfill(14)  # Pad with zeros to make it 14 digits long
        return tin[:3] + '-' + tin[3:6] + '-' + tin[6:9] + '-' + tin[9:]
    else:
        return tin


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Simain
    template_name = 'salesinvoice/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['simain'] = Simain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        context['tin'] = format_tin(context['simain'].customer.tin)
        print 'result tin', context['tin']
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['detail'] = Sidetail.objects.filter(isdeleted=0). \
            filter(simain_id=self.kwargs['pk']).order_by('item_counter')
        # context['totaldebitamount'] = Sidetail.objects.filter(isdeleted=0). \
        #     filter(simain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        # context['totalcreditamount'] = Sidetail.objects.filter(isdeleted=0). \
        #     filter(simain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))
        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = Companyparameter.objects.get(code='PDI').logo_path

        printedor = Simain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        printedor.print_ctr += 1
        printedor.save()
        return context

# @method_decorator(login_required, name='dispatch')
# class Pdf(IndexView):
#     model = Simain
#     template_name = 'salesinvoice/pdf.html'

#     def get_context_data(self, **kwargs):
#         context = super(IndexView, self).get_context_data(**kwargs)

#         context['simain'] = Simain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
#         context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
#         context['detail'] = Sidetail.objects.filter(isdeleted=0). \
#             filter(simain_id=self.kwargs['pk']).order_by('item_counter')
#         context['totaldebitamount'] = Sidetail.objects.filter(isdeleted=0). \
#             filter(simain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
#         context['totalcreditamount'] = Sidetail.objects.filter(isdeleted=0). \
#             filter(simain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))
#         context['pagesize'] = 'Letter'
#         context['orientation'] = 'portrait'
#         context['logo'] = Companyparameter.objects.get(code='PDI').logo_path

#         printedor = Simain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
#         printedor.print_ctr += 1
#         printedor.save()
#         return context
    


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Simain
    template_name = 'salesinvoice/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('salesinvoice.delete_simain') or self.object.status == 'O' \
                or self.object.sistatus == 'A' or self.object.sistatus == 'I' or self.object.sistatus == 'R':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.sistatus = 'D'
        self.object.save()

        return HttpResponseRedirect('/salesinvoice')
    

@csrf_exempt
def goapprove(request):

    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        release = Simain.objects.filter(pk__in=ids).update(sistatus='A',
                                                        responsedate = str(datetime.datetime.now()),
                                                        approverremarks = 'Batch Approved',
                                                        actualapprover = User.objects.get(pk=request.user.id),
                                                        designatedapprover = User.objects.get(pk=request.user.id)
        )

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


@csrf_exempt
def gounpost(request):
    if request.method == 'POST':
        approval = Simain.objects.get(pk=request.POST['id'])
        if (approval.sistatus == 'R' and approval.status != 'O'):
            approval.sistatus = 'A'
            approval.save()
            data = {'status': 'success'}

            # Save Activity Logs
            Activitylogs.objects.create(
                user_id=request.user.id,
                username=request.user,
                remarks='Unpost SI Transaction #' + str(approval.sinum)
            )
        else:
            data = {'status': 'error'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


@csrf_exempt
def searchforposting(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Simain.objects.filter(isdeleted=0,status='A',sistatus='A').order_by('sinum', 'sidate')
        if dfrom != '':
            q = q.filter(sidate__gte=dfrom)
        if dto != '':
            q = q.filter(sidate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('salesinvoice/postingresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def approve(request):
    if request.method == 'POST':

        approval = Simain.objects.get(pk=request.POST['id'])

        details = Sidetail.objects.filter(simain_id=approval.id).order_by('item_counter')
        print details

        msg = ""
        msgchartname = ""
        msgchart = ""
        error = 0
        totalerror = 0
        for item in details:

            chartvalidate = Chartofaccount.objects.get(pk=item.chartofaccount_id)

            if chartvalidate.bankaccount_enable == 'Y':
                if item.bankaccount_id is None:
                    error += 1
                    msg += "Bank is Needed "

            if chartvalidate.department_enable == 'Y':
                if item.department_id is None:
                    error += 1
                    msg += "Department is Needed "
                ## check expense
                print chartvalidate.accountcode
                if chartvalidate.accountcode[0:1] == '5':
                    print "expense ako"
                    dept = Department.objects.get(pk=item.department_id)
                    deptchart = Chartofaccount.objects.filter(isdeleted=0, status='A', pk=dept.expchartofaccount_id).first()

                    if chartvalidate.accountcode[0:2] != deptchart.accountcode[0:2]:
                        error += 1
                        msg += "Expense code did not match with the department code "

            if chartvalidate.supplier_enable == 'Y':

                print chartvalidate.setup_supplier
                if chartvalidate.setup_supplier is None:
                    if item.supplier_id is None:
                        error += 1
                        msg += "Supplier is Needed "

            if chartvalidate.customer_enable == 'Y':
                print chartvalidate.setup_customer
                if chartvalidate.setup_customer is None:
                    if item.customer_id is None:
                        error += 1
                        msg += "Customer is Needed "

            if chartvalidate.branch_enable == 'Y':
                if item.branch_id is None:
                    error += 1
                    msg += "Branch is Needed "

            if chartvalidate.unit_enable == 'Y':
                if item.unit_id is None:
                    error += 1
                    msg += "Unit is Needed "

            if chartvalidate.inputvat_enable == 'Y':
                if item.inputvat_id is None:
                    error += 1
                    msg += "Input VAT is Needed "

            if chartvalidate.outputvat_enable == 'Y':
                if item.outputvat_id is None:
                    error += 1
                    msg += "Output VAT is Needed "

            if chartvalidate.vat_enable == 'Y':
                if item.vat_id is None:
                    error += 1
                    msg += "VAT is Needed "

            if chartvalidate.wtax_enable == 'Y':
                if item.wtax_id is None:
                    error += 1
                    msg += "WTAX is Needed "

            if chartvalidate.ataxcode_enable == 'Y':
                if item.ataxcode_id is None:
                    error += 1
                    msg += "ATAX is Needed "

            totalerror += error
            if error > 0:
                msgchartname = " Chart of Account: " + str(chartvalidate) + " "
                ## Double Validation
                msgchart += str(msgchartname) + " " + str(msg)
                msg = ""
                msgchartname = ""
                error = 0
            # print error
            # print msg

        if totalerror > 0:
            data = {'status': 'error', 'msg': msgchart}
            return JsonResponse(data)
        else:
            if (approval.sistatus != 'R' and approval.status != 'O'):
                approval.sistatus = 'A'
                approval.responsedate = str(datetime.datetime.now())
                approval.approverremarks = str(approval.approverremarks) + ';' + 'Approved'
                approval.actualapprover = User.objects.get(pk=request.user.id)
                approval.save()
                data = {'status': 'success'}

                # Save Activity Logs
                Activitylogs.objects.create(
                    user_id=request.user.id,
                    username=request.user,
                    remarks='Aproved SI Transaction #' + str(approval.sinum)
                )
            else:
                data = {'status': 'error'}

            return JsonResponse(data)


    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


@csrf_exempt
def disapprove(request):
    if request.method == 'POST':
        approval = Simain.objects.get(pk=request.POST['id'])
        if (approval.sistatus != 'R' and approval.status != 'O'):
            approval.sistatus = 'D'
            approval.responsedate = str(datetime.datetime.now())
            approval.approverremarks = str(approval.approverremarks) +';'+ request.POST['reason']
            approval.actualapprover = User.objects.get(pk=request.user.id)
            approval.save()
            data = {'status': 'success'}

            # Save Activity Logs
            Activitylogs.objects.create(
                user_id=request.user.id,
                username=request.user,
                remarks='Disaproved SI Transaction #' + str(approval.sinum)
            )
        else:
            data = {'status': 'error'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


def upload(request):
    if request.method != 'POST' or not request.FILES['myfile']:
        return HttpResponseRedirect('/salesinvoice/' + str(dataid) )
    myfile = request.FILES['myfile']
    dataid = request.POST['dataid']
    fs = FileSystemStorage(location='media/siupload/')
    filename = fs.save(myfile.name, myfile)

    upl = Siupload(simain_id=dataid, filename=filename, enterby=request.user, modifyby=request.user)
    upl.save()

    uploaded_file_url = fs.url(filename)
    return HttpResponseRedirect('/salesinvoice/' + str(dataid) )


@csrf_exempt
def filedelete(request):

    if request.method == 'POST':

        pk = request.POST['id']
        fileid = request.POST['fileid']

        Siupload.objects.filter(pk=fileid).delete()

        return HttpResponseRedirect('/salesinvoice/' + str(pk) )

    return HttpResponseRedirect('/salesinvoice/' + str(pk) )