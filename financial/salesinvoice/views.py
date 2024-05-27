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
# from processing_or.models import Logs_simain, Logs_sidetail
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
        # context['accountexecutive'] = Employee.objects.filter(status='A', isdeleted=0).exclude(firstname='').order_by('firstname')
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
                'amount', 'amountinwords', 'customer', 'vat', 'vatrate', 'outputvattype', 'wtaxrate', 'refno', 'designatedapprover',
                'particulars']
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('salesinvoice.add_simain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)

        # data for lookup
        context['sitype'] = Sitype.objects.filter(isdeleted=0).order_by('pk')
        context['sisubtype'] = Sisubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['customer'] = Customer.objects.filter(isdeleted=0).order_by('code')
        # context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('code')
        # context['creditterm'] = Companyparameter.objects.get(code='PDI').si_creditterm
        # context['accountexecutive'] = Employee.objects.filter(status='A', isdeleted=0).exclude(firstname='').order_by('firstname')
        context['designatedapprover'] = Employee.objects.filter(isdeleted=0, jv_approver=1).order_by('firstname')
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
        self.object.wtax_id = self.request.POST['wtax'] or None
        
        # self.object.accountexecutive_id = self.object.accountexecutive.id if self.object.accountexecutive else None
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
    fields = ['sinum', 'sidate', 'sitype', 'sisubtype', 'branch', 'customer', 'creditterm', 'duedate',
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
        # context['accountexecutive'] = Employee.objects.filter(status='A', isdeleted=0).exclude(firstname='').order_by('firstname')
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
        #     context['logs_sidetail'] = Logs_sidetail.objects.filter(orno=self.object.sinum, importstatus='P',
        #                                                             batchkey=context['logs_simain'].first().batchkey)
        #     context['logs_sistatus'] = context['logs_simain'].first().status if context['logs_simain'] else ''

        # data for lookup
        context['sitype'] = Sitype.objects.filter(isdeleted=0).order_by('pk')
        context['sisubtype'] = Sisubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
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
            'tablebreakdowntemp': 'sidetailbreakdowntemp',

            'datatemp': querystmtdetail('sidetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('sidetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        # accounting entry ends here

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if self.request.POST['wtax'] == '':
            self.object.wtaxrate = 0
        else:
            self.object.wtaxrate = Wtax.objects.get(pk=int(self.request.POST['wtax'])).rate

        self.object.vatrate = Vat.objects.get(pk=int(self.request.POST['vat'])).rate
        # self.object.accountexecutive_id = self.object.accountexecutive.id if self.object.accountexecutive else None
        self.object.customer_id =  self.object.customer.id or None
        self.object.acctentry_incomplete = 0
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['sidate', 'creditterm', 'duedate', 'amount', 'amountinwords', 'customer', 'vatrate', 'wtaxrate',
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
def gopost(request):

    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        release = Simain.objects.filter(pk__in=ids).update(sistatus='R',
                                                        releaseby=User.objects.get(pk=request.user.id),
                                                        releasedate= str(datetime.datetime.now()),
                                                        responsedate = str(datetime.datetime.now())
        )

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


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
def searchforapproval(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Simain.objects.filter(isdeleted=0,status='A',sistatus='F').order_by('sidate', 'sinum')
        if dfrom != '':
            q = q.filter(sidate__gte=dfrom)
        if dto != '':
            q = q.filter(sidate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('salesinvoice/approvalresult.html', context),
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


@csrf_exempt
def getcustomercreditterm(request):
    if request.method == 'GET':
        pk = request.GET['id']
        daysdue = Customer.objects.get(pk=pk).creditterm.daysdue
        print 'daysdue', daysdue
        data = {'daysdue': daysdue}
    else: data = {'status': 'error'}
    
    return JsonResponse(data)


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Simain
    template_name = 'salesinvoice/report/index.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['sitype'] = Sitype.objects.filter(isdeleted=0).order_by('description')
        context['sisubtype'] = Sisubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['customer'] = Customer.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['product'] = Product.objects.filter(isdeleted=0).order_by('code')

        return context
    
    
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
        sitype = request.GET['sitype']
        sisubtype = request.GET['sisubtype']
        branch = request.GET['branch']
        customer = request.GET['customer']
        wtax = request.GET['wtax']
        vat = request.GET['vat']
        outputvat = request.GET['outputvat']
        status = request.GET['status']
        sistatus = request.GET['sistatus']
        title = "Sales Invoice List"
        list = Simain.objects.filter(isdeleted=0).order_by('sinum')[:0]

        if report == '1':
            title = "Invoice Register"
            q = Simain.objects.all().filter(isdeleted=0).order_by('sidate', 'sinum')
            if dfrom != '':
                q = q.filter(sidate__gte=dfrom)
            if dto != '':
                q = q.filter(sidate__lte=dto)
        elif report == '2':
            title = "Sales Book"
            # q = Sidetail.objects.select_related('simain').filter(isdeleted=0).order_by('si_date', 'si_num', 'item_counter')
            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')
            if dfrom != '':
                q = q.filter(sidate__gte=dfrom)
            if dto != '':
                q = q.filter(sidate__lte=dto)
        # elif report == '7':
        #     title = "Sales Invoice Register"
        #     q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')
        #     if dfrom != '':
        #         q = q.filter(sidate__gte=dfrom)
        #     if dto != '':
        #         q = q.filter(sidate__lte=dto)
        elif report == '8':
            title = "Sales Invoice Output VAT"
            silist = getSIList(dfrom, dto)
            arr = getARR()

            query = query_siwithoutputvat(dfrom, dto, silist, arr)

            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')
        elif report == '9':
            title = "Sales Invoice Output VAT Summary"
            silist = getSIList(dfrom, dto)
            arr = getARR()

            query = query_siwithoutputvatsummary(dfrom, dto, silist, arr)

            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')
        elif report == '10':
            title = "Sales Invoice Without Output VAT"
            silist = getSINoOutputVatList(dfrom, dto)

            query = query_sinooutputvat(dfrom, dto, silist)

            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')
        elif report == '11':
            title = "Sales Invoice Without Output VAT Summary"
            silist = getSINoOutputVatList(dfrom, dto)

            query = query_sinooutputvatsummary(dfrom, dto, silist)
            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')

        if sitype != '':
            q = q.filter(sitype=sitype)
            print 'sitype'
        if sisubtype != '':
            q = q.filter(sisubtype=sisubtype)
            print 'sisubtype'
        if customer != 'null':
            q = q.filter(customer__code=customer)
            print 'payee'
        if branch != '':
            q = q.filter(branch=branch)
            print branch
        if wtax != '':
            q = q.filter(wtax=wtax)
            print 'wtax'
        if vat != '':
            q = q.filter(vat=vat)
            print 'vat'
        if outputvat != '':
            q = q.filter(outputvattype=outputvat)
            print 'outputvat'
        if status != '':
            q = q.filter(status=status)
            print 'status'
        if sistatus != '':
            q = q.filter(sistatus=sistatus)
            print 'sistatus'

        # if report == '5':
        #     list = raw_query(1, company, dfrom, dto, sitype, artype, payee, collector, branch, product, adtype, wtax, vat, outputvat, bankaccount, status)
        #     dataset = pd.DataFrame(list)
        #     total = {}
        #     total['amount'] = dataset['amount'].sum()
        #     total['cashinbank'] = dataset['cashinbank'].sum()
        #     total['diff'] = dataset['diff'].sum()
        #     total['outputvat'] = dataset['outputvat'].sum()
        #     total['amountdue'] = dataset['amountdue'].sum()
        # elif report == '6':
        #     list = raw_query(2, company, dfrom, dto, sitype, artype, payee, collector, branch, product, adtype, wtax,vat, outputvat, bankaccount, status)
        #     dataset = pd.DataFrame(list)
        #     total = {}
        #     #total['amount'] = dataset['amount'].sum()
        #     if list:
        #         total['debitamount'] = dataset['debitamount'].sum()
        #         total['creditamount'] = dataset['creditamount'].sum()
        #     else:
        #         total['debitamount'] = 0
        #         total['creditamount'] = 0
        #     #total['diff'] = dataset['totaldiff'].sum()
        if report == '8' or report == '9' or report == '10' or report == '11':
            print 'pasok'
            list = query
            outputcredit = 0
            outputdebit = 0
            amount = 0
            if list:
                df = pd.DataFrame(query)
                outputcredit = df['outputvatcreditamount'].sum()
                outputdebit = df['outputvatdebitamount'].sum()
                
                if report == '10' or report == '11':
                    amount = df['amount'].sum()
        else:
            list = q

        if list:

            if report == '2' or report == '4':
                total = list.aggregate(total_amount=Sum('vatablesale'), total_discountamount=Sum('discountamount'), total_vatamount=Sum('vatamount'), total_netsale=Sum('amount'))
            elif report == '8' or report == '9' or report == '10' or report == '11':
                total = {'outputcredit': outputcredit, 'outputdebit': outputdebit, 'amount': amount}
        #     elif report == '5' or report == '6':
        #         print 'do nothing'
            else:
                total = list.filter(~Q(status='C')).aggregate(total_amount=Sum('amount'))

        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "dfrom": dfrom,
            "dto": dto,
            "datefrom": datetime.datetime.strptime(dfrom, '%Y-%m-%d'),
            "dateto": datetime.datetime.strptime(dto, '%Y-%m-%d'),
            "username": request.user, 
        }
        
        if report == '1':
            return Render.render('salesinvoice/report/report_1.html', context)
        elif report == '2':
            return Render.render('salesinvoice/report/report_2.html', context)
        # elif report == '3':
        #     return Render.render('salesinvoice/report/report_3.html', context)
        # elif report == '4':
        #     return Render.render('salesinvoice/report/report_4.html', context)
        # elif report == '5':
        #     return Render.render('salesinvoice/report/report_5.html', context)
        # elif report == '6':
        #     return Render.render('salesinvoice/report/report_6.html', context)
        # elif report == '7':
        #     return Render.render('salesinvoice/report/report_7.html', context)
        elif report == '8':
            return Render.render('salesinvoice/report/report_8.html', context)
        elif report == '9':
            return Render.render('salesinvoice/report/report_9.html', context)
        elif report == '10':
            return Render.render('salesinvoice/report/report_10.html', context)
        elif report == '11':
            return Render.render('salesinvoice/report/report_11.html', context)
        else:
            return Render.render('salesinvoice/report/report_1.html', context)
        
        
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
        sitype = request.GET['sitype']
        artype = request.GET['artype']
        payee = request.GET['payee']
        collector = request.GET['collector']
        branch = request.GET['branch']
        product = request.GET['product']
        adtype = request.GET['adtype']
        wtax = request.GET['wtax']
        vat = request.GET['vat']
        outputvat = request.GET['outputvat']
        bankaccount = request.GET['bankaccount']
        status = request.GET['status']
        sistatus = request.GET['sistatus']
        title = "Sales Invoice List"
        list = Simain.objects.filter(isdeleted=0).order_by('sinum')[:0]

        if report == '1':
            title = "Sales Invoice Transaction List - Summary"
            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')
            if dfrom != '':
                q = q.filter(sidate__gte=dfrom)
            if dto != '':
                q = q.filter(sidate__lte=dto)
        elif report == '2':
            title = "Sales Invoice Transaction List"
            q = Ordetail.objects.select_related('simain').filter(isdeleted=0).order_by('si_date', 'si_num', 'item_counter')
            if dfrom != '':
                q = q.filter(si_date__gte=dfrom)
            if dto != '':
                q = q.filter(si_date__lte=dto)
        elif report == '3':
            title = "Unposted Sales Invoice Transaction List - Summary"
            q = Simain.objects.filter(isdeleted=0,status__in=['A','C']).order_by('sidate', 'sinum')
            if dfrom != '':
                q = q.filter(sidate__gte=dfrom)
            if dto != '':
                q = q.filter(sidate__lte=dto)
        elif report == '4':
            title = "Unposted Sales Invoice Transaction List"
            q = Ordetail.objects.select_related('simain').filter(isdeleted=0,status__in=['A','C']).order_by('si_date', 'si_num',  'item_counter')
            if dfrom != '':
                q = q.filter(si_date__gte=dfrom)
            if dto != '':
                q = q.filter(si_date__lte=dto)
        elif report == '5':
            title = "Sales Invoice List (Unbalanced Cash in Bank VS Amount)"
            q = Simain.objects.select_related('sidetail').filter(isdeleted=0).order_by('sidate', 'sinum')
            if dfrom != '':
                q = q.filter(sidate__gte=dfrom)
            if dto != '':
                q = q.filter(sidate__lte=dto)
        elif report == '6':
            title = "Unbalanced Sales Invoice Transaction List"
            q = Simain.objects.select_related('sidetail').filter(isdeleted=0).order_by('sidate', 'sinum')
            if dfrom != '':
                q = q.filter(sidate__gte=dfrom)
            if dto != '':
                q = q.filter(sidate__lte=dto)
        elif report == '7':
            title = "Sales Invoice Register"
            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')
            if dfrom != '':
                q = q.filter(sidate__gte=dfrom)
            if dto != '':
                q = q.filter(sidate__lte=dto)
        elif report == '8':
            title = "Sales Invoice Output VAT"
            silist = getSIList(dfrom, dto)
            arr = getARR()

            query = query_siwithoutputvat(dfrom, dto, silist, arr)

            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')
        elif report == '9':
            title = "Sales Invoice Output VAT Summary"
            silist = getSIList(dfrom, dto)
            arr = getARR()

            query = query_siwithoutputvatsummary(dfrom, dto, silist, arr)

            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')
        elif report == '10':
            title = "Sales Invoice Without Output VAT"
            silist = getSINoOutputVatList(dfrom, dto)

            query = query_sinooutputvat(dfrom, dto, silist)

            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')
        elif report == '11':
            title = "Sales Invoice Without Output VAT Summary"
            silist = getSINoOutputVatList(dfrom, dto)

            query = query_sinooutputvatsummary(dfrom, dto, silist)
            q = Simain.objects.filter(isdeleted=0).order_by('sidate', 'sinum')

        if sitype != '':
            if report == '2' or report == '4':
                q = q.filter(simain__sitype__exact=sitype)
            else:
                q = q.filter(sitype=sitype)
        if artype != '':
            if report == '2' or report == '4':
                q = q.filter(simain__orsource__exact=artype)
            else:
                q = q.filter(orsource=artype)
        if payee != 'null':
            if report == '2' or report == '4':
                q = q.filter(simain__payee_code__exact=payee)
            else:
                q = q.filter(payee_code=payee)
        if branch != '':
            if report == '2' or report == '4':
                q = q.filter(simain__branch__exact=branch)
            else:
                q = q.filter(branch=branch)
        if collector != '':
            if report == '2' or report == '4':
                q = q.filter(simain__collector__exact=collector)
            else:
                q = q.filter(collector=collector)
        if product != '':
            if report == '2' or report == '4':
                q = q.filter(simain__product__exact=product)
            else:
                q = q.filter(product=product)
        if adtype != '':
            if report == '2' or report == '4':
                q = q.filter(simain__adtype__exact=adtype)
            else:
                q = q.filter(adtype=adtype)
        if wtax != '':
            if report == '2' or report == '4':
                q = q.filter(simain__wtax__exact=wtax)
            else:
                q = q.filter(wtax=wtax)
        if vat != '':
            if report == '2' or report == '4':
                q = q.filter(simain__vat__exact=vat)
            else:
                q = q.filter(vat=vat)
        if outputvat != '':
            if report == '2' or report == '4':
                q = q.filter(simain__outputvattype__exact=outputvat)
            else:
                q = q.filter(outputvattype=outputvat)
        if bankaccount != '':
            if report == '2' or report == '4':
                q = q.filter(simain__bankaccount__exact=bankaccount)
            else:
                q = q.filter(bankaccount=bankaccount)
        if status != '':
            if report == '2' or report == '4':
                q = q.filter(simain__status__exact=status)
            else:
                q = q.filter(status=status)
        if sistatus != '':
            if report == '2' or report == '4':
                q = q.filter(simain__sistatus__exact=sistatus)
            else:
                q = q.filter(sistatus=sistatus)
            print 'sistatus'

        if report == '5':
            list = raw_query(1, company, dfrom, dto, sitype, artype, payee, collector, branch, product, adtype, wtax, vat, outputvat, bankaccount, status)
            dataset = pd.DataFrame(list)
        elif report == '6':
            list = raw_query(2, company, dfrom, dto, sitype, artype, payee, collector, branch, product, adtype, wtax,vat, outputvat, bankaccount, status)
            dataset = pd.DataFrame(list)
        elif report == '8' or report == '9' or report == '10' or report == '11':
            print 'pasok'
            list = query
            outputcredit = 0
            outputdebit = 0
            arrcredit = 0
            ardebit = 0
            if list:
                df = pd.DataFrame(query)
                outputcredit = df['outputvatcreditamount'].sum()
                outputdebit = df['outputvatdebitamount'].sum()
                arrcredit = df['arrcreditamount'].sum()
                arrdebit = df['arrdebitamount'].sum()
        else:
            list = q

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', str(title), bold)
        worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)

        filename = "orreport.xlsx"

        if report == '1':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0
            totalamount = 0
            amount = 0
            for data in list:
                if data.orsource == 'A':
                    worksheet.write(row, col, str('OR')+data.sinum)
                else:
                    worksheet.write(row, col, str('CR')+data.sinum)

                worksheet.write(row, col + 1, data.sidate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)
                worksheet.write(row, col + 3, data.particulars)
                if data.status == 'C':
                    worksheet.write(row, col + 4, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 4, float(format(data.amount, '.2f')))
                    amount = data.amount

                row += 1
                totalamount += amount

            #print float(format(totalamount, '.2f'))
            #print total['total_amount']
            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totalamount, '.2f')))

            filename = "ortransactionlistsummary.xlsx"

        elif report == '2':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Particular', bold)
            worksheet.write('D4', 'Account Title', bold)
            worksheet.write('E4', 'Subs Ledger', bold)
            worksheet.write('F4', 'Debit', bold)
            worksheet.write('G4', 'Credit', bold)

            row = 4
            col = 0


            totaldebit = 0
            totalcredit = 0
            list = list.values('simain__sinum', 'simain__sidate', 'simain__particulars', 'simain__payee_name', 'chartofaccount__accountcode', 'chartofaccount__description', 'status', 'debitamount', 'creditamount', 'branch__code', 'bankaccount__code', 'department__code')
            dataset = pd.DataFrame.from_records(list)

            for sinum, detail in dataset.fillna('NaN').groupby(['simain__sinum', 'simain__sidate', 'simain__payee_name', 'simain__particulars', 'status']):
                worksheet.write(row, col, sinum[0])
                worksheet.write(row, col+1, sinum[1], formatdate)
                if sinum[4] == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col+2, sinum[2])
                worksheet.write(row, col+3, sinum[3])
                row += 1
                debit = 0
                credit = 0
                branch = ''
                bankaccount = ''
                department = ''
                for sub, data in detail.iterrows():
                    worksheet.write(row, col + 2, data['chartofaccount__accountcode'])
                    worksheet.write(row, col + 3, data['chartofaccount__description'])
                    if data['branch__code'] != 'NaN':
                        branch = data['branch__code']
                    if data['bankaccount__code'] != 'NaN':
                        bankaccount = data['bankaccount__code']
                    if data['department__code'] != 'NaN':
                        department = data['department__code']
                    worksheet.write(row, col + 4, branch+' '+bankaccount+' '+department)
                    if sinum[4] == 'C':
                        worksheet.write(row, col + 5, float(format(0, '.2f')))
                        worksheet.write(row, col + 6, float(format(0, '.2f')))
                        debit = 0
                        credit = 0
                    else:
                        worksheet.write(row, col + 5, float(format(data['debitamount'], '.2f')))
                        worksheet.write(row, col + 6, float(format(data['creditamount'], '.2f')))
                        debit = data['debitamount']
                        credit = data['creditamount']

                    row += 1
                    totaldebit += debit
                    totalcredit += credit

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(totaldebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalcredit, '.2f')))


            filename = "ortransactionlist.xlsx"

        elif report == '3':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0

            totalamount = 0
            amount = 0
            for data in list:
                worksheet.write(row, col, data.sinum)
                worksheet.write(row, col + 1, data.sidate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)
                worksheet.write(row, col + 3, data.particulars)

                if data.status == 'C':
                    worksheet.write(row, col + 4, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 4, float(format(data.amount, '.2f')))
                    amount = data.amount

                row += 1
                totalamount += amount

            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totalamount, '.2f')))
            filename = "unpostedortransactionlistsummary.xlsx"

        elif report == '4':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Particular', bold)
            worksheet.write('D4', 'Account Title', bold)
            worksheet.write('E4', 'Subs Ledger', bold)
            worksheet.write('F4', 'Debit', bold)
            worksheet.write('G4', 'Credit', bold)

            row = 4
            col = 0

            totaldebit = 0
            totalcredit = 0
            list = list.values('simain__sinum', 'simain__sidate', 'simain__particulars', 'simain__payee_name',
                               'chartofaccount__accountcode', 'chartofaccount__description', 'status', 'debitamount',
                               'creditamount', 'branch__code', 'bankaccount__code', 'department__code')
            dataset = pd.DataFrame.from_records(list)

            for sinum, detail in dataset.fillna('NaN').groupby(
                    ['simain__sinum', 'simain__sidate', 'simain__payee_name', 'simain__particulars', 'status']):
                worksheet.write(row, col, sinum[0])
                worksheet.write(row, col + 1, sinum[1], formatdate)
                if sinum[4] == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, sinum[2])
                worksheet.write(row, col + 3, sinum[3])
                row += 1
                debit = 0
                credit = 0
                branch = ''
                bankaccount = ''
                department = ''
                for sub, data in detail.iterrows():
                    worksheet.write(row, col + 2, data['chartofaccount__accountcode'])
                    worksheet.write(row, col + 3, data['chartofaccount__description'])
                    if data['branch__code'] != 'NaN':
                        branch = data['branch__code']
                    if data['bankaccount__code'] != 'NaN':
                        bankaccount = data['bankaccount__code']
                    if data['department__code'] != 'NaN':
                        department = data['department__code']
                    worksheet.write(row, col + 4, branch + ' ' + bankaccount + ' ' + department)
                    if sinum[4] == 'C':
                        worksheet.write(row, col + 5, float(format(0, '.2f')))
                        worksheet.write(row, col + 6, float(format(0, '.2f')))
                        debit = 0
                        credit = 0
                    else:
                        worksheet.write(row, col + 5, float(format(data['debitamount'], '.2f')))
                        worksheet.write(row, col + 6, float(format(data['creditamount'], '.2f')))
                        debit = data['debitamount']
                        credit = data['creditamount']

                    row += 1
                    totaldebit += debit
                    totalcredit += credit

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(totaldebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalcredit, '.2f')))


            filename = "unpostedortransactionlist.xlsx"

        elif report == '5':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Amount', bold)
            worksheet.write('E4', 'Cash in Bank', bold)
            worksheet.write('F4', 'Difference', bold)
            worksheet.write('G4', 'Output VAT', bold)
            worksheet.write('H4', 'Amount Due', bold)
            worksheet.write('I4', 'Status', bold)

            row = 4
            col = 0

            totalamount = 0
            amount = 0
            totalcashinbank = 0
            totaldiff = 0
            totaloutputvat = 0
            totalamountdue = 0
            for data in list:
                worksheet.write(row, col, data.sinum)
                worksheet.write(row, col + 1, data.sidate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)

                if data.status == 'C':
                    worksheet.write(row, col + 3, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 3, float(format(data.amount, '.2f')))
                    amount = data.amount

                worksheet.write(row, col + 4, float(format(data.cashinbank, '.2f')))
                worksheet.write(row, col + 5, float(format(data.diff, '.2f')))
                worksheet.write(row, col + 6, float(format(data.outputvat, '.2f')))
                worksheet.write(row, col + 7, float(format(data.amountdue, '.2f')))
                worksheet.write(row, col + 8, data.status)

                row += 1
                totalamount += amount
                totalcashinbank += data.cashinbank
                totaldiff += data.diff
                totaloutputvat += data.outputvat
                totalamountdue += data.amountdue


            worksheet.write(row, col + 2, 'Total')
            worksheet.write(row, col + 3, float(format(totalamount, '.2f')))
            worksheet.write(row, col + 4, float(format(totalcashinbank, '.2f')))
            worksheet.write(row, col + 5, float(format(totaldiff, '.2f')))
            worksheet.write(row, col + 6, float(format(totaloutputvat, '.2f')))
            worksheet.write(row, col + 7, float(format(totalamountdue, '.2f')))

            filename = "OfficialReceiptList.xlsx"
        elif report == '6':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Total Amount', bold)
            worksheet.write('E4', 'Debit Amount', bold)
            worksheet.write('F4', 'Credit Amount', bold)
            worksheet.write('G4', 'Variance', bold)
            worksheet.write('H4', 'Status', bold)

            row = 4
            col = 0

            totalamount = 0
            amount = 0
            totaldebit = 0
            totalcredit = 0
            totalvariance = 0


            for data in list:
                if data.orsource == 'A':
                    worksheet.write(row, col, str('OR')+data.sinum)
                else:
                    worksheet.write(row, col, str('CR')+data.sinum)
                #worksheet.write(row, col, data.sinum)
                worksheet.write(row, col + 1, data.sidate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)

                if data.status == 'C':
                    worksheet.write(row, col + 3, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 3, float(format(data.amount, '.2f')))
                    amount = data.amount

                worksheet.write(row, col + 4, float(format(data.debitamount, '.2f')))
                worksheet.write(row, col + 5, float(format(data.creditamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.totaldiff, '.2f')))
                worksheet.write(row, col + 7, data.status)

                row += 1
                totalamount += amount
                totaldebit += data.debitamount
                totalcredit += data.creditamount
                totalvariance += data.totaldiff


            worksheet.write(row, col + 2, 'Total')
            worksheet.write(row, col + 3, float(format(totalamount, '.2f')))
            worksheet.write(row, col + 4, float(format(totaldebit, '.2f')))
            worksheet.write(row, col + 5, float(format(totalcredit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalvariance, '.2f')))

            filename = "UnbalancedOfficialReceiptTransanctionList.xlsx"

        elif report == '7':
            # header
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Payee', bold)

            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0

            totalamount = 0
            amount = 0
            for data in list:
                if data.orsource == 'A':
                    worksheet.write(row, col, str('OR')+data.sinum)
                else:
                    worksheet.write(row, col, str('CR')+data.sinum)

                worksheet.write(row, col + 1, data.sidate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)

                if data.status == 'C':
                    worksheet.write(row, col + 4, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 4, float(format(data.amount, '.2f')))
                    amount = data.amount

                row += 1
                totalamount += amount

            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totalamount, '.2f')))
            filename = "salesinvoiceregister.xlsx"

        elif report == '8':
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Gov Status', bold)
            worksheet.write('D4', 'Payee/Particular', bold)
            worksheet.write('E4', 'Type', bold)
            worksheet.write('F4', 'AR / Revenue Debit', bold)
            worksheet.write('G4', 'AR / Revenue Credit', bold)
            worksheet.write('H4', 'Output VAT Debit', bold)
            worksheet.write('I4', 'Output VAT Credit', bold)
            worksheet.write('J4', 'VAT Rate', bold)

            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0

            for data in list:
                if data.orsource == 'A':
                    worksheet.write(row, col, str('OR') + data.sinum)
                else:
                    worksheet.write(row, col, str('CR') + data.sinum)
                worksheet.write(row, col + 1, data.sidate, formatdate)
                worksheet.write(row, col + 2, data.government)
                worksheet.write(row, col + 3, data.payee_name)
                worksheet.write(row, col + 4, data.sitype)
                worksheet.write(row, col + 5, float(format(data.arrdebitamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.arrcreditamount, '.2f')))
                worksheet.write(row, col + 7, float(format(data.outputvatdebitamount, '.2f')))
                worksheet.write(row, col + 8, float(format(data.outputvatcreditamount, '.2f')))
                worksheet.write(row, col + 9, data.outputvatrate)

                totalefodebit += data.arrdebitamount
                totalefocredit += data.arrcreditamount
                totalinputdebit += data.outputvatdebitamount
                totalinputcredit += data.outputvatcreditamount

                row += 1

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 7, float(format(totalinputdebit, '.2f')))
            worksheet.write(row, col + 8, float(format(totalinputcredit, '.2f')))

            filename = "ortransactionoutputvat.xlsx"

        elif report == '9':
            worksheet.write('A4', 'Payee/Particular', bold)
            worksheet.write('B4', 'Gov Status', bold)
            worksheet.write('C4', 'Type', bold)
            worksheet.write('D4', 'AR / Revenue Debit', bold)
            worksheet.write('E4', 'AR / Revenue Credit', bold)
            worksheet.write('F4', 'Output VAT Debit', bold)
            worksheet.write('G4', 'Output VAT Credit', bold)
            worksheet.write('H4', 'VAT Rate', bold)
            worksheet.write('I4', 'Address', bold)
            worksheet.write('J4', 'TIN', bold)

            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0

            for data in list:
                worksheet.write(row, col, data.payee_name)
                worksheet.write(row, col + 1, data.government)
                worksheet.write(row, col + 2, data.sitype)
                worksheet.write(row, col + 3, float(format(data.arrdebitamount, '.2f')))
                worksheet.write(row, col + 4, float(format(data.arrcreditamount, '.2f')))
                worksheet.write(row, col + 5, float(format(data.outputvatdebitamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.outputvatcreditamount, '.2f')))
                worksheet.write(row, col + 7, data.outputvatrate)
                worksheet.write(row, col + 8, data.address)
                worksheet.write(row, col + 9, data.tin)

                totalefodebit += data.arrdebitamount
                totalefocredit += data.arrcreditamount
                totalinputdebit += data.outputvatdebitamount
                totalinputcredit += data.outputvatcreditamount

                row += 1

            worksheet.write(row, col + 2, 'Total')
            worksheet.write(row, col + 3, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 4, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 5, float(format(totalinputdebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalinputcredit, '.2f')))

            filename = "ortransactionoutputvatsummary.xlsx"

        elif report == '10':
            worksheet.write('A4', 'OR Number', bold)
            worksheet.write('B4', 'OR Date', bold)
            worksheet.write('C4', 'Gov Status', bold)
            worksheet.write('D4', 'Payee/Particular', bold)
            worksheet.write('E4', 'Type', bold)
            worksheet.write('F4', 'Cash In Bank Debit', bold)
            worksheet.write('G4', 'Cash In Bank Credit', bold)
            worksheet.write('H4', 'Output VAT Debit', bold)
            worksheet.write('I4', 'Output VAT Credit', bold)
            worksheet.write('J4', 'VAT Rate', bold)

            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0

            for data in list:
                if data.orsource == 'A':
                    worksheet.write(row, col, str('OR') + data.sinum)
                else:
                    worksheet.write(row, col, str('CR') + data.sinum)
                worksheet.write(row, col + 1, data.sidate, formatdate)
                worksheet.write(row, col + 2, data.government)
                worksheet.write(row, col + 3, data.payee_name)
                worksheet.write(row, col + 4, data.sitype)
                worksheet.write(row, col + 5, float(format(data.arrdebitamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.arrcreditamount, '.2f')))
                worksheet.write(row, col + 7, '')
                worksheet.write(row, col + 8, '')
                worksheet.write(row, col + 9, '')

                totalefodebit += data.arrdebitamount
                totalefocredit += data.arrcreditamount
                totalinputdebit += data.outputvatdebitamount
                totalinputcredit += data.outputvatcreditamount

                row += 1

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 7, '')
            worksheet.write(row, col + 8, '')

            filename = "ortransactionwithoutoutputvat.xlsx"

        elif report == '11':
            worksheet.write('A4', 'Payee/Particular', bold)
            worksheet.write('B4', 'Gov Status', bold)
            worksheet.write('C4', 'Type', bold)
            worksheet.write('D4', 'Cash In Bank Debit', bold)
            worksheet.write('E4', 'Cash In Bank Credit', bold)
            worksheet.write('F4', 'Output VAT Debit', bold)
            worksheet.write('G4', 'Output VAT Credit', bold)
            worksheet.write('H4', 'VAT Rate', bold)
            worksheet.write('I4', 'Address', bold)
            worksheet.write('J4', 'TIN', bold)

            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0

            for data in list:
                worksheet.write(row, col, data.payee_name)
                worksheet.write(row, col + 1, data.government)
                worksheet.write(row, col + 2, data.sitype)
                worksheet.write(row, col + 3, float(format(data.arrdebitamount, '.2f')))
                worksheet.write(row, col + 4, float(format(data.arrcreditamount, '.2f')))
                worksheet.write(row, col + 5, '')
                worksheet.write(row, col + 6, '')
                worksheet.write(row, col + 7, '')
                worksheet.write(row, col + 8, data.address)
                worksheet.write(row, col + 9, data.tin)

                totalefodebit += data.arrdebitamount
                totalefocredit += data.arrcreditamount
                totalinputdebit += data.outputvatdebitamount
                totalinputcredit += data.outputvatcreditamount

                row += 1

            worksheet.write(row, col + 2, 'Total')
            worksheet.write(row, col + 3, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 4, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 5, '')
            worksheet.write(row, col + 6, '')

            filename = "ortransactionwithoutoutputvatsummary.xlsx"

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
    

def raw_query(type, company, dfrom, dto, sitype, artype, payee, collector, branch, product, adtype, wtax, vat, outputvat, bankaccount, status):
    #print type
    print "raw query"
    ''' Create query '''
    cursor = connection.cursor()

    consitype = ""
    conpayee = ""
    concollector = ""
    conbranch = ""
    conproduct = ""
    conadtype = ""
    conwtax = ""
    convat = ""
    conoutputvat = ""
    conbankaccount = ""
    constatus = ""

    if sitype != '':
        consitype = "AND m.sitype = '" +str(sitype)+ "'"
    if payee != 'null':
        conpayee = "AND m.payee_code = '" + str(payee) + "'"
    if branch != '':
        conbranch = "AND m.branch = '" + str(branch) + "'"
    if collector != '':
        concollector = "AND m.collector = '" + str(collector) + "'"
    if product != '':
        conproduct = "AND m.product = '" + str(product) + "'"
    if adtype != '':
        conadtype = "AND m.adtype = '" + str(adtype) + "'"
    if wtax != '':
        conwtax = "AND m.wtax = '" + str(wtax) + "'"
    if vat != '':
        convat = "AND m.vat = '" + str(vat) + "'"
    if outputvat != '':
        conoutputvat = "AND m.outputvattype = '" + str(outputvattype) + "'"
    if bankaccount != '':
        conbankaccount = "AND m.bankaccount = '" + str(bankaccount) + "'"
    if status != '':
        constatus = "AND m.status = '" + str(status) + "'"

    if type == 1:
        query = "SELECT m.orsource, m.id, m.sinum, m.sidate, IF(m.status = 'C', 0, m.amount) AS amount, c.name, IFNULL(cash.total_amount, 0) AS cashinbank, IFNULL(ouput.total_amount, 0) AS outputvat, m.status, " \
                "(m.amount - IFNULL(cash.total_amount, 0)) AS diff, (m.amount - IFNULL(ouput.total_amount,0)) AS amountdue " \
                "FROM simain AS m " \
                "LEFT OUTER JOIN customer AS c ON c.id = m.customer_id " \
                "LEFT OUTER JOIN (" \
                "   SELECT si_num, balancecode, chartofaccount_id, SUM(debitamount) AS total_amount " \
                "   FROM sidetail WHERE balancecode = 'D' AND chartofaccount_id = "+str(company.coa_cashinbank_id)+ " " \
                "   GROUP BY si_num" \
                ") AS cash ON cash.si_num = m.sinum " \
                "LEFT OUTER JOIN (" \
                "   SELECT si_num, balancecode, chartofaccount_id, SUM(creditamount) AS total_amount " \
                "   FROM sidetail WHERE balancecode = 'C' AND chartofaccount_id = "+str(company.coa_outputvat_id)+ " " \
                "   GROUP BY si_num " \
                ")AS ouput ON ouput.si_num = m.sinum " \
                "WHERE m.sidate >= '"+str(dfrom)+"' AND m.sidate <= '"+str(dto)+"' " \
                "AND (m.amount <> cash.total_amount OR cash.total_amount IS NULL) " \
                + str(consitype) + " " + str(conpayee) + " " + str(conbranch) + " "+ str(concollector) + " " + str(conproduct) + " " \
                + str(conadtype) + " " + str(conwtax) + " " + str(convat) + " " + str(conoutputvat) + " "+ str(conbankaccount) + " " + str(constatus) + " " \
                "ORDER BY m.sidate,  m.sinum"
    elif type == 2:
        query = "SELECT z.*, ABS(z.detaildiff + z.diff) AS totaldiff FROM (" \
                "SELECT m.orsource, m.id, m.sinum, m.sidate, c.name, IF(m.status = 'C', 0, m.amount) AS amount, m.status, IFNULL(debit.total_amount, 0) AS debitamount, IFNULL(credit.total_amount, 0) AS creditamount, " \
                "(IFNULL(debit.total_amount, 0) - IFNULL(credit.total_amount, 0)) AS detaildiff, (m.amount - IFNULL(debit.total_amount, 0)) AS diff " \
                "FROM simain AS m " \
                "LEFT OUTER JOIN customer AS c ON c.id = m.customer_id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT simain_id, si_num, balancecode, chartofaccount_id, SUM(debitamount) AS total_amount " \
                "   FROM sidetail WHERE balancecode = 'D' " \
                "   GROUP BY simain_id " \
                ") AS debit ON debit.simain_id = m.id  " \
                "LEFT OUTER JOIN ( " \
                "   SELECT simain_id, si_num, balancecode, chartofaccount_id, SUM(creditamount) AS total_amount " \
                "   FROM sidetail WHERE balancecode = 'C' " \
                "   GROUP BY simain_id " \
                ") AS credit ON credit.simain_id = m.id 	" \
                "WHERE m.sidate >= '"+str(dfrom)+"' AND m.sidate <= '"+str(dto)+"' " \
                + str(consitype) + " " + str(conpayee) + " " + str(conbranch) + " " + str(concollector) + " " + str(conproduct) + " " \
                + str(conadtype) + " " + str(conwtax) + " " + str(convat) + " " + str(conoutputvat) + " " + str(conbankaccount) + " " + str(constatus) + " " \
                "AND m.status != 'C' ORDER BY m.sidate,  m.sinum) AS z WHERE z.detaildiff != 0 OR z.diff != 0;"
        print 'dito'
        print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def getSIList(dfrom, dto):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    outputvat = 320 # 2146000000 OUTPUT VAT PAYABLE

    query = "SELECT m.sinum, m.sidate, c.name, m.particulars, " \
            "d.balancecode, d.chartofaccount_id, d.simain_id " \
            "FROM simain AS m " \
            "LEFT OUTER JOIN sidetail AS d ON d.simain_id = m.id " \
            "LEFT OUTER JOIN customer AS c ON c.id = m.customer_id " \
            "WHERE DATE(m.sidate) >= '"+str(dfrom)+"' AND DATE(m.sidate) <= '"+str(dto)+"' " \
            "AND m.sistatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND d.chartofaccount_id = "+str(outputvat)+" " \
            "ORDER BY m.sinum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    print query
    print 'hoy'

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    list = ''
    for r in result:
        list += str(r.simain_id) + ','

    return list[:-1]


def getARR():
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()
    query = "SELECT id, accountcode, description, main, clas, item, SUBSTR(sub, 1, 2) AS sub " \
            "FROM chartofaccount  " \
            "WHERE (main = 1 AND clas = 1 AND item = 2 AND cont = 1) OR (main = 4 AND clas = 1 AND item = 1)"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    list = ''
    for r in result:
        list += str(r.id) + ','

    return list[:-1]


def query_siwithoutputvatsummary(dfrom, dto, silist, arr):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()
    
    output = 320
    if not silist:
        silist = '0'

    query = "SELECT m.sinum, m.sidate, m.particulars, sit.code AS sitype, c.name, c.address1, c.address2, c.address3, c.tin, " \
            "SUM(IFNULL(outputvat.debitamount, 0)) AS outputvatdebitamount, SUM(IFNULL(outputvat.creditamount, 0)) AS outputvatcreditamount," \
            "m.vatrate AS outputvatrate " \
            "FROM simain AS m " \
            "LEFT OUTER JOIN sitype AS sit ON sit.id = m.sitype_id " \
            "LEFT OUTER JOIN customer AS c ON c.id = m.customer_id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.simain_id, d.si_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM sidetail AS d " \
            "WHERE d.simain_id IN ("+str(silist)+") " \
            "AND d.chartofaccount_id IN ("+str(arr)+") " \
            "GROUP BY d.simain_id " \
            "ORDER BY d.si_num, d.si_date " \
            ") AS arr ON arr.simain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.simain_id, d.si_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM sidetail AS d " \
            "WHERE d.simain_id IN ("+str(silist)+") " \
            "AND d.chartofaccount_id = "+str(output)+" " \
            "GROUP BY d.simain_id " \
            "ORDER BY d.si_num, d.si_date " \
            ") AS outputvat ON outputvat.simain_id = m.id " \
            "WHERE DATE(m.sidate) >= '"+str(dfrom)+"' AND DATE(m.sidate) <= '"+str(dto)+"' " \
            "AND m.sistatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+str(silist)+") " \
            "GROUP BY c.code, c.name ORDER BY c.name, sit.code, m.sinum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def query_siwithoutputvat(dfrom, dto, silist, arr):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    output = 320
    if not silist:
        silist = '0'
    
    query = "SELECT m.sinum, m.sidate, m.particulars, sit.code AS sitype, c.name, " \
            "IFNULL(outputvat.debitamount, 0) AS outputvatdebitamount, IFNULL(outputvat.creditamount, 0) AS outputvatcreditamount, " \
            "m.vatrate AS outputvatrate " \
            "FROM simain AS m " \
            "LEFT OUTER JOIN sitype AS sit ON sit.id = m.sitype_id " \
            "LEFT OUTER JOIN customer AS c ON c.id = m.customer_id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.simain_id, d.si_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM sidetail AS d " \
            "WHERE d.simain_id IN ("+str(silist)+") " \
            "AND d.chartofaccount_id IN ("+str(arr)+") " \
            "GROUP BY d.simain_id " \
            "ORDER BY d.si_num, d.si_date " \
            ") AS arr ON arr.simain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.simain_id, d.si_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM sidetail AS d " \
            "WHERE d.simain_id IN ("+str(silist)+") " \
            "AND d.chartofaccount_id = "+str(output)+" " \
            "GROUP BY d.simain_id " \
            "ORDER BY d.si_num, d.si_date " \
            ") AS outputvat ON outputvat.simain_id = m.id " \
            "WHERE DATE(m.sidate) >= '"+str(dfrom)+"' AND DATE(m.sidate) <= '"+str(dto)+"' " \
            "AND m.sistatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+str(silist)+") " \
            "ORDER BY c.name, sit.code, m.sinum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    return result


def getSINoOutputVatList(dfrom, dto):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    outputvat = 320 # 2146000000 OUTPUT VAT PAYABLE

    query = "SELECT m.sinum, m.sidate, c.name, m.particulars, " \
            "d.balancecode, d.chartofaccount_id, d.simain_id " \
            "FROM simain AS m " \
            "LEFT OUTER JOIN customer AS c ON c.id = m.customer_id " \
            "LEFT OUTER JOIN sidetail AS d ON d.simain_id = m.id " \
            "WHERE DATE(m.sidate) >= '"+str(dfrom)+"' AND DATE(m.sidate) <= '"+str(dto)+"' " \
            "AND m.sistatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id NOT IN (" \
            "SELECT DISTINCT m.id " \
            "FROM simain AS m " \
            "LEFT OUTER JOIN sidetail AS d ON d.simain_id = m.id " \
            "WHERE DATE(m.sidate) >= '"+str(dfrom)+"' AND DATE(m.sidate) <= '"+str(dto)+"' " \
            "AND d.chartofaccount_id = "+str(outputvat)+") " \
            "ORDER BY m.sinum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print 'getSINoOutputVatList', query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    list = ''
    for r in result:
        list += str(r.simain_id) + ','

    return list[:-1]


def query_sinooutputvat(dfrom, dto, silist):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()
    print 'silist', silist
    if not silist or str(silist) == 'None':
        silist = 0

    query = "SELECT m.sinum, m.sidate, c.name, m.particulars, m.amount, sit.code AS sitype, " \
            "IFNULL(outputvat.debitamount, 0) AS outputvatdebitamount, IFNULL(outputvat.creditamount, 0) AS outputvatcreditamount, " \
            "m.vatrate AS outputvatrate " \
            "FROM simain AS m " \
            "LEFT OUTER JOIN sitype AS sit ON sit.id = m.sitype_id " \
            "LEFT OUTER JOIN customer AS c ON c.id = m.customer_id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.simain_id, d.si_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM sidetail AS d " \
            "WHERE d.simain_id IN ("+str(silist)+") " \
            "GROUP BY d.simain_id " \
            "ORDER BY d.si_num, d.si_date " \
            ") AS arr ON arr.simain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.simain_id, d.si_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM sidetail AS d " \
            "WHERE d.simain_id IN ("+str(silist)+") " \
            "GROUP BY d.simain_id " \
            "ORDER BY d.si_num, d.si_date " \
            ") AS outputvat ON outputvat.simain_id = m.id " \
            "WHERE DATE(m.sidate) >= '"+str(dfrom)+"' AND DATE(m.sidate) <= '"+str(dto)+"' " \
            "AND m.sistatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+str(silist)+") " \
            "ORDER BY c.name, sit.code, m.sinum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def query_sinooutputvatsummary(dfrom, dto, silist):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    if not silist:
        silist = '0'

    query = "SELECT m.sinum, m.sidate, m.particulars, m.amount,sit.code AS sitype, c.code, c.name, " \
            "CONCAT(IFNULL(c.address1, ''), ' ', IFNULL(c.address2, ''), ' ', IFNULL(c.address3, '')) AS address, c.tin, " \
            "SUM(IFNULL(outputvat.debitamount, 0)) AS outputvatdebitamount, SUM(IFNULL(outputvat.creditamount, 0)) AS outputvatcreditamount," \
            "m.vatrate AS outputvatrate " \
            "FROM simain AS m " \
            "LEFT OUTER JOIN sitype AS sit ON sit.id = m.sitype_id " \
            "LEFT OUTER JOIN customer AS c ON c.id = m.customer_id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.simain_id, d.si_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM sidetail AS d " \
            "WHERE d.simain_id IN ("+str(silist)+") " \
            "GROUP BY d.simain_id " \
            "ORDER BY d.si_num, d.si_date " \
            ") AS arr ON arr.simain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.simain_id, d.si_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM sidetail AS d " \
            "WHERE d.simain_id IN ("+str(silist)+") " \
            "GROUP BY d.simain_id " \
            "ORDER BY d.si_num, d.si_date " \
            ") AS outputvat ON outputvat.simain_id = m.id " \
            "WHERE DATE(m.sidate) >= '"+str(dfrom)+"' AND DATE(m.sidate) <= '"+str(dto)+"' " \
            "AND m.sistatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+str(silist)+") " \
            "GROUP BY c.code, c.name ORDER BY c.name, sit.code, m.sinum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result
