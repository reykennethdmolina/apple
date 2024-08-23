from django.views.generic import View, DetailView, CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Q, Sum, Case, Value, When, F
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
# from ataxcode.models import Ataxcode
from branch.models import Branch
from companyparameter.models import Companyparameter
from module.models import Activitylogs
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from . models import Simain, Sidetail, Sidetailtemp, Sidetailbreakdown, Sidetailbreakdowntemp, Siupload, Silogs
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from customer.models import Customer
from sitype.models import Sitype
from sisubtype.models import Sisubtype
from subledger.models import Subledger
from outputvattype.models import Outputvattype
# from processing_or.models import Logs_simain, Logs_sidetail
from vat.models import Vat
from wtax.models import Wtax
from django.template.loader import render_to_string
from easy_pdf.views import PDFTemplateView
from datetime import datetime as dt
from product.models import Product
from department.models import Department
from employee.models import Employee
from chartofaccount.models import Chartofaccount
from journalvoucher.models import Jvmain, Jvdetail
import pandas as pd
from financial.utils import Render
from financial.context_processors import namedtuplefetchall
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.files.storage import FileSystemStorage
import io
import decimal
import datetime
import xlsxwriter


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
                                    Q(customer__name__icontains=keysearch) |
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
        context['sitype'] = Sitype.objects.filter(isdeleted=0).order_by('code')
        context['sisubtype'] = Sisubtype.objects.filter(isdeleted=0).order_by('code')
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

        non_vat_amount = decimal.Decimal(self.object.amount) / (1 + (decimal.Decimal(self.object.vatrate) / decimal.Decimal(100)))

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
        
        # save si logs
        Silogs.objects.create(
            user=self.request.user,
            username=self.request.user,
            action_type='create',
            action_datetime=datetime.datetime.now(),
            remarks="SI create ID: "+str(self.object.id)+", SI #"+str(sinum)
        )

        return HttpResponseRedirect('/salesinvoice/' + str(self.object.id) + '/update')
    
    
def lastNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT SUBSTRING(sinum, 5) AS num FROM simain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    print 'result', result
    if result:
        return result[0]
    else:
        return ['000000']


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
            detail.customer = drow.customer_id
            detail.department = drow.department_id
            detail.unit = drow.unit_id
            detail.branch = drow.branch_id
            detail.outputvat = drow.outputvat_id
            detail.vat = drow.vat_id
            detail.wtax = drow.wtax_id
            detail.debitamount = drow.debitamount
            detail.creditamount = drow.creditamount
            detail.balancecode = drow.balancecode
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
                    breakdown.outputvat = brow.outputvat_id
                    breakdown.vat = brow.vat_id
                    breakdown.wtax = brow.wtax_id
                    breakdown.debitamount = brow.debitamount
                    breakdown.creditamount = brow.creditamount
                    breakdown.balancecode = brow.balancecode
                    breakdown.datatype = brow.datatype
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

        # data for lookup
        context['sitype'] = Sitype.objects.filter(isdeleted=0).order_by('code')
        context['sisubtype'] = Sisubtype.objects.filter(isdeleted=0).order_by('code')
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

        non_vat_amount = decimal.Decimal(self.object.amount) / (1 + (decimal.Decimal(self.object.vatrate) / decimal.Decimal(100)))

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

        self.object.save(update_fields=['vatamount', 'wtaxamount', 'vatablesale', 'vatexemptsale', 'vatzeroratedsale', 'totalsale'])

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
        
        # save si logs
        Silogs.objects.create(
            user=self.request.user,
            username=self.request.user,
            action_type='update',
            action_datetime=datetime.datetime.now(),
            remarks="SI update ID: "+str(self.object.id)+", SI #"+str(num)
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
        
        # save si logs
        # Silogs.objects.create(
        #     user=self.request.user,
        #     username=self.request.user,
        #     action_type='view',
        #     action_datetime=datetime.datetime.now(),
        #     remarks="SI view detail ID: "+str(self.kwargs['pk'])
        # )

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
        
        main = Simain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        net_of_vat = float(main.amount) - float(main.vatamount)

        context['simain'] = main
        context['tin'] = format_tin(context['simain'].customer.tin)
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['detail'] = Sidetail.objects.filter(isdeleted=0). \
            filter(simain_id=self.kwargs['pk']).order_by('item_counter')
        context['computed'] = {'net_of_vat': net_of_vat}
        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = Companyparameter.objects.get(code='PDI').logo_path

        main.print_ctr += 1
        main.save()
        
        # save si logs
        # Silogs.objects.create(
        #     user=self.request.user,
        #     username=self.request.user,
        #     action_type='view',
        #     action_datetime=datetime.datetime.now(),
        #     remarks="SI view PDF invoice ID: "+str(self.kwargs['pk'])
        # )
        
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
        
        # save si logs
        Silogs.objects.create(
            user=self.request.user,
            username=self.request.user,
            action_type='delete',
            action_datetime=datetime.datetime.now(),
            remarks="SI delete ID: "+str(self.kwargs['pk'])
        )

        return HttpResponseRedirect('/salesinvoice')


@csrf_exempt
def gopost(request):

    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        release = Simain.objects.filter(pk__in=ids).update(sistatus='R',
                                                        responsedate = str(datetime.datetime.now())
        )

        data = {'status': 'success'}
        
        # save si logs
        Silogs.objects.create(
            user=request.user,
            username=request.user,
            action_type='post',
            action_datetime=datetime.datetime.now(),
            remarks="SI post IDs: "+str(ids)
        )
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
        # save si logs
        Silogs.objects.create(
            user=request.user,
            username=request.user,
            action_type='approve',
            action_datetime=datetime.datetime.now(),
            remarks="SI approve IDs: "+str(ids)
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
            
            # save si logs
            Silogs.objects.create(
                user=request.user,
                username=request.user,
                action_type='unpost',
                action_datetime=datetime.datetime.now(),
                remarks="SI unpost ID: "+str(request.POST['id'])
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
        if dfrom != '' and dto != '':
            q = Simain.objects.filter(sidate__gte=dfrom, sidate__lte=dto, isdeleted=0,status='A',sistatus='A').order_by('sinum', 'sidate')
            
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
                    remarks='Approved SI Transaction #' + str(approval.sinum)
                )
                
                # save si logs
                Silogs.objects.create(
                    user=request.user,
                    username=request.user,
                    action_type='approve',
                    action_datetime=datetime.datetime.now(),
                    remarks="SI approve ID: "+str(request.POST['id'])
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
            
            # save si logs
            Silogs.objects.create(
                user=request.user,
                username=request.user,
                action_type='disapprove',
                action_datetime=datetime.datetime.now(),
                remarks="SI disapprove ID: "+str(request.POST['id'])
            )
        else:
            data = {'status': 'error'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


@csrf_exempt
def posting(request):
    if request.method == 'POST':
        Simain.objects.filter(pk=request.POST['id']).update(sistatus='R')

        data = {'status': 'success'}
        
        # save si logs
        Silogs.objects.create(
            user=request.user,
            username=request.user,
            action_type='posting',
            action_datetime=datetime.datetime.now(),
            remarks="SI posting ID: "+str(request.POST['id'])
        )
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
    
    # save si logs
    Silogs.objects.create(
        user=request.user,
        username=request.user,
        action_type='file upload',
        action_datetime=datetime.datetime.now(),
        remarks="SI file upload ID: "+str(dataid)+", File ID: "+str(upl.pk)
    )

    uploaded_file_url = fs.url(filename)
    return HttpResponseRedirect('/salesinvoice/' + str(dataid) )


@csrf_exempt
def filedelete(request):

    if request.method == 'POST':

        pk = request.POST['id']
        fileid = request.POST['fileid']

        Siupload.objects.filter(pk=fileid).delete()
        
        # save si logs
        Silogs.objects.create(
            user=request.user,
            username=request.user,
            action_type='file delete',
            action_datetime=datetime.datetime.now(),
            remarks="SI file delete ID: "+str(pk)+", File ID: "+str(fileid)
        )

        return HttpResponseRedirect('/salesinvoice/' + str(pk) )

    return HttpResponseRedirect('/salesinvoice/' + str(pk) )


@csrf_exempt
def getcustomercreditterm(request):
    if request.method == 'GET':
        pk = request.GET['id']
        daysdue = Customer.objects.get(pk=pk).creditterm.daysdue
        
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
            
            q = Simain.objects.filter(isdeleted=0).annotate(total_vatsale=F('vatablesale') + F('vatexemptsale') + F('vatzeroratedsale')).order_by('sidate', 'sinum')
            if dfrom != '':
                q = q.filter(sidate__gte=dfrom)
            if dto != '':
                q = q.filter(sidate__lte=dto)
        elif report == '3':
            title = "Sales Book Summary"
            
            silist = getSIList(dfrom, dto)

            query = query_salesbooksummary(dfrom, dto, silist)
        elif report == '4':
            title = "Sales Book - Summary Entries"
            q = Sidetail.objects.all().filter(isdeleted=0,simain__sistatus='R').exclude(simain__status='C')
            if dfrom != '':
                q = q.filter(si_date__gte=dfrom)
            if dto != '':
                q = q.filter(si_date__lte=dto)
            q = q.values('chartofaccount__accountcode','chartofaccount__description') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                            debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                                default=Sum('debitamount') - Sum('creditamount')),
                            creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('chartofaccount__accountcode')
        elif report == '8':
            title = "Sales Invoice Output VAT"
            silist = getSIList(dfrom, dto)
            arr = getARR()

            query = query_siwithoutputvat(dfrom, dto, silist, arr)

        elif report == '9':
            title = "Sales Invoice Output VAT Summary"
            silist = getSIList(dfrom, dto)
            arr = getARR()

            query = query_siwithoutputvatsummary(dfrom, dto, silist, arr)

        elif report == '10':
            title = "Sales Invoice Without Output VAT"
            silist = getSINoOutputVatList(dfrom, dto)

            query = query_sinooutputvat(dfrom, dto, silist)

        elif report == '11':
            title = "Sales Invoice Without Output VAT Summary"
            silist = getSINoOutputVatList(dfrom, dto)

            query = query_sinooutputvatsummary(dfrom, dto, silist)
            
        elif report == '12':
            title = "Sales Invoice Audit Trail"
            query = Silogs.objects.all()
            if dfrom != '':
                query = query.filter(action_datetime__gte=dfrom)
            if dto != '':
                query = query.filter(action_datetime__lte=dto)

        if report == '8' or report == '9' or report == '10' or report == '11':
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
        elif report == '3':
            list = query
            total_amount = 0
            total_discountamount = 0
            total_vatamount = 0
            total_netsale = 0
            if list:
                df = pd.DataFrame(query)
                total_amount = df['total_vatsale'].sum()
                total_discountamount = df['discountamount'].sum()
                total_vatamount = df['vatamount'].sum()
                total_netsale = df['amount'].sum()
        elif report == '12':
            list = query
        else:
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
                
            list = q
            
        if list:

            if report == '2':
                total = list.aggregate(total_amount=Sum('total_vatsale'), total_discountamount=Sum('discountamount'), total_vatamount=Sum('vatamount'), total_netsale=Sum('amount'))
            elif report == '8' or report == '9' or report == '10' or report == '11':
                total = {'outputcredit': outputcredit, 'outputdebit': outputdebit, 'amount': amount}
            elif report == '3':
                total = {'total_amount': total_amount, 'total_discountamount': total_discountamount, 'total_vatamount': total_vatamount, 'total_netsale': total_netsale }
            elif report == '4':
                total = list.aggregate(Sum('debitdifference'), Sum('creditdifference'))
            elif report == '12':
                # do nothing
                print 'audit trail'
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
        elif report == '3':
            return Render.render('salesinvoice/report/report_3.html', context)
        elif report == '4':
            return Render.render('salesinvoice/report/report_4.html', context)
        elif report == '8':
            return Render.render('salesinvoice/report/report_8.html', context)
        elif report == '9':
            return Render.render('salesinvoice/report/report_9.html', context)
        elif report == '10':
            return Render.render('salesinvoice/report/report_10.html', context)
        elif report == '11':
            return Render.render('salesinvoice/report/report_11.html', context)
        elif report == '12':
            return Render.render('salesinvoice/report/report_12.html', context)
        else:
            return Render.render('salesinvoice/report/report_1.html', context)
        
        
@method_decorator(login_required, name='dispatch')
class GeneratePDFCashInBank(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = ''
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        title = "SALES BOOK - SUMMARY ENTRIES"
        subtitle = ""

        cashinbank = Companyparameter.objects.first().coa_cashinbank_id
        if report == '4':
            title = "SALES BOOK - SUMMARY ENTRIES"
            subtitle = "Summary of Cash In Bank"
            q = Sidetail.objects.all().filter(isdeleted=0,chartofaccount=cashinbank).exclude(simain__status='C')
            if dfrom != '':
                q = q.filter(si_date__gte=dfrom)
            if dto != '':
                q = q.filter(si_date__lte=dto)
            q = q.values('bankaccount__code',
                            'bankaccount__bank__code',
                            'bankaccount__bankaccounttype__code') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                            debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                                default=Sum('debitamount') - Sum('creditamount')),
                            creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('bankaccount__code')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        else:
            q = Sidetail.objects.filter(isdeleted=0).order_by('si_date', 'si_num')[:0]

        list = q
        context = {
            "title": title,
            "subtitle": subtitle,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "datefrom": dfrom,
            "dateto": dto,
            "username": request.user,
        }
        return Render.render('salesinvoice/report/summary_cashinbank.html', context)


@method_decorator(login_required, name='dispatch')
class GeneratePDFDepartment(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = ''
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        title = "SALES BOOK - SUMMARY ENTRIES"
        subtitle = ""

        if report == '4':
            title = "SALES BOOK - SUMMARY ENTRIES"
            subtitle = "Summary of Department"
            q = Sidetail.objects.all().filter(isdeleted=0,department__isnull=False).exclude(simain__status='C')
            if dfrom != '':
                q = q.filter(si_date__gte=dfrom)
            if dto != '':
                q = q.filter(si_date__lte=dto)
            q = q.values('department__code',
                            'department__departmentname',
                            'department__sectionname', 'department__branchstatus') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                            debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                                default=Sum('debitamount') - Sum('creditamount')),
                            creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('department__code')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        else:
            q = Sidetail.objects.filter(isdeleted=0).order_by('si_date', 'si_num')[:0]

        list = q
        context = {
            "title": title,
            "subtitle": subtitle,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "report": report,
            "datefrom": dfrom,
            "dateto": dto,
            "username": request.user,
        }
        return Render.render('salesinvoice/report/summary_department.html', context)


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
                worksheet.write(row, col, data.sinum)
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
                worksheet.write(row, col, data.sinum)

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
                worksheet.write(row, col, data.sinum)
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
                worksheet.write(row, col, data.sinum)
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
        query = "SELECT m.id, m.sinum, m.sidate, IF(m.status = 'C', 0, m.amount) AS amount, c.name, IFNULL(cash.total_amount, 0) AS cashinbank, IFNULL(ouput.total_amount, 0) AS outputvat, m.status, " \
                "(m.amount - IFNULL(cash.total_amount, 0)) AS diff, (m.amount - IFNULL(ouput.total_amount,0)) AS amountdue " \
                "FROM simain AS m " \
                "LEFT OUTER JOIN customer AS c ON c.id = m.customer_id " \
                "LEFT OUTER JOIN (" \
                "   SELECT si_num, balancecode, chartofaccount_id, SUM(debitamount) AS total_amount " \
                "   FROM sidetail WHERE balancecode = 'D' " \
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
                "SELECT m.id, m.sinum, m.sidate, c.name, IF(m.status = 'C', 0, m.amount) AS amount, m.status, IFNULL(debit.total_amount, 0) AS debitamount, IFNULL(credit.total_amount, 0) AS creditamount, " \
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


def query_salesbooksummary(dfrom, dto, silist):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()
    
    if not silist:
        silist = '0'

    query = "SELECT c.name, c.tin, " \
            "CONCAT(IFNULL(c.address1, ''), ' ', IFNULL(c.address2, ''), ' ', IFNULL(c.address3, '')) AS address, " \
            "SUM(IFNULL(m.vatablesale, 0) + IFNULL(m.vatexemptsale, 0) + IFNULL(m.vatzeroratedsale, 0)) AS total_vatsale, " \
            "SUM(IFNULL(m.discountamount, 0)) AS discountamount, SUM(IFNULL(m.vatamount, 0)) AS vatamount, SUM(IFNULL(m.amount, 0)) AS amount " \
            "FROM simain AS m " \
            "LEFT OUTER JOIN customer AS c ON c.id = m.customer_id " \
            "WHERE DATE(m.sidate) >= '"+str(dfrom)+"' AND DATE(m.sidate) <= '"+str(dto)+"' " \
            "AND m.status != 'C' " \
            "GROUP BY c.code ORDER BY c.name, m.sinum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    print 'query', query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def query_siwithoutputvatsummary(dfrom, dto, silist, arr):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()
    
    output = 320
    if not silist:
        silist = '0'

    query = "SELECT m.sinum, m.sidate, m.particulars, c.name, c.address1, c.address2, c.address3, c.tin, " \
            "SUM(IFNULL(outputvat.debitamount, 0)) AS outputvatdebitamount, SUM(IFNULL(outputvat.creditamount, 0)) AS outputvatcreditamount," \
            "m.vatrate AS outputvatrate " \
            "FROM simain AS m " \
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
            "GROUP BY c.code, c.name ORDER BY c.name, m.sinum"

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

    query = "SELECT m.sinum, m.sidate, m.particulars, m.amount, sit.code AS sitype, c.code, c.name, " \
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


@csrf_exempt
def generatedefaultentries(request):
    if request.method == 'POST':
        data_table = validatetable(request.POST['table'])
        subtype_id = request.POST['sisubtype']
        amount = float(request.POST['amount'])
        vat_id = int(request.POST['vat'])
        vatable = float(request.POST['vatable'])
        vatexempt = float(request.POST['vatexempt'])
        vatzero = float(request.POST['vatzero'])
        addvat = float(request.POST['addvat'])
        itemcounter =1
        
        try:
            entries = Sisubtype.objects.get(pk=subtype_id)
            
            if entries.debit1:
                print entries.debit1.description, entries.debit1.customer_enable
                debit1entry = Sidetailtemp()
                debit1entry.item_counter = itemcounter
                debit1entry.secretkey = request.POST['secretkey']
                if entries.debit1.customer_enable == 'Y':
                    debit1entry.customer = request.POST['customer'] # add validation if required in coa
                debit1entry.si_num = ''
                debit1entry.si_date = datetime.date.today()
                debit1entry.chartofaccount = entries.debit1.id
                debit1entry.debitamount = amount
                debit1entry.balancecode = 'D'
                debit1entry.enterby = request.user
                debit1entry.modifyby = request.user
                debit1entry.isautogenerated = 1
                debit1entry.save()
                itemcounter += 1
            elif entries.debit2:
                print entries.debit2.description, entries.debit2.customer_enable
                debit2entry = Sidetailtemp()
                debit2entry.item_counter = itemcounter
                debit2entry.secretkey = request.POST['secretkey']
                if entries.debit2.customer_enable == 'Y':
                    debit2entry.customer = request.POST['customer']
                debit2entry.si_num = ''
                debit2entry.si_date = datetime.date.today()
                debit2entry.chartofaccount = entries.debit2.id
                debit2entry.debitamount = amount
                debit2entry.balancecode = 'D'
                debit2entry.enterby = request.user
                debit2entry.modifyby = request.user
                debit2entry.isautogenerated = 1
                debit2entry.save()
                itemcounter += 1
                
            if entries.credit1:
                accountcode = entries.credit1.accountcode
                firstfourdigits = str(accountcode)[0:4]
                
                if firstfourdigits == '2146':
                    # outputvat
                    if Vat.objects.get(pk=vat_id).rate > 0:
                        creditamount = addvat
                    else:
                        creditamount = 0
                else:
                    if vatable > 0:
                        creditamount = vatable
                    elif Vat.objects.get(pk=vat_id).code == 'VE':
                        creditamount = vatexempt
                    elif Vat.objects.get(pk=vat_id).code == 'ZE' or Vat.objects.get(pk=vat_id).code == 'VATNA':
                        creditamount = vatzero
                
                if creditamount:
                    credit1entry = Sidetailtemp()
                    credit1entry.item_counter = itemcounter
                    credit1entry.secretkey = request.POST['secretkey']
                    credit1entry.si_num = ''
                    credit1entry.si_date = datetime.date.today()
                    credit1entry.chartofaccount = entries.credit1.id
                    credit1entry.creditamount = creditamount
                    credit1entry.balancecode = 'C'
                    credit1entry.enterby = request.user
                    credit1entry.modifyby = request.user
                    credit1entry.isautogenerated = 1
                    credit1entry.save()
                    itemcounter += 1
                
            if entries.credit2:
                accountcode = entries.credit2.accountcode
                firstfourdigits = str(accountcode)[0:4]
                
                if firstfourdigits == '2146':
                    # outputvat
                    if Vat.objects.get(pk=vat_id).rate > 0:
                        creditamount = addvat
                    else:
                        creditamount = 0
                    
                else:
                    # other income
                    if vatable > 0:
                        creditamount = vatable
                    elif Vat.objects.get(pk=vat_id).code == 'VE':
                        creditamount = vatexempt
                    elif Vat.objects.get(pk=vat_id).code == 'ZE' or Vat.objects.get(pk=vat_id).code == 'VATNA':
                        creditamount = vatzero
                
                if creditamount:
                    credit2entry = Sidetailtemp()
                    credit2entry.item_counter = itemcounter
                    credit2entry.secretkey = request.POST['secretkey']
                    credit2entry.si_num = ''
                    credit2entry.si_date = datetime.date.today()
                    credit2entry.chartofaccount = entries.credit2.id
                    credit2entry.creditamount = creditamount
                    credit2entry.balancecode = 'C'
                    credit2entry.enterby = request.user
                    credit2entry.modifyby = request.user
                    credit2entry.isautogenerated = 1
                    credit2entry.save()
                    itemcounter += 1

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
        except Exception as e:
            print 'error', e
            data = {
                'message': str(e),
                'status': 'exception',
            }
    else:        
        data = {
                'status': 'error',
            }

    return JsonResponse(data)
    

@csrf_exempt
def searchforpostingJV(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']
        if dfrom and dto:
            q = Simain.objects.filter(sidate__gte=dfrom, sidate__lte=dto, isdeleted=0, status='A', sistatus='R').exclude(jvmain_id__isnull=False).order_by('sinum', 'sidate')

            context = {
                'data': q
            }
            data = {
                'status': 'success',
                'viewhtml': render_to_string('salesinvoice/jvpostingresult.html', context),
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


def lastJVNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT SUBSTRING(jvnum, 5) AS num FROM jvmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]


@csrf_exempt
def gopostjv(request):

    if request.method == 'POST':
        from django.db.models import CharField
        from django.db.models.functions import Length

        CharField.register_lookup(Length, 'length')

        ids = request.POST.getlist('ids[]')
        pdate = request.POST['postdate']
            
        counter = 1
        amount = 0
            
        for id in ids:
            entries = Sidetail.objects.filter(simain_id=id, isdeleted=0).exclude(simain__status='C')
        
            entries = entries.values('si_num', 'simain__particulars', 'chartofaccount__accountcode','chartofaccount__description', 'balancecode', \
                'ataxcode_id', 'bankaccount_id', 'branch_id', 'chartofaccount_id', 'customer_id', 'department_id', \
                    'employee_id', 'inputvat_id', 'outputvat_id', 'product_id', 'unit_id', 'vat_id', 'wtax_id') \
            .annotate(Sum('debitamount'), Sum('creditamount'),
                        debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                            default=Sum('debitamount') - Sum('creditamount')),
                        creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                            default=Sum('creditamount') - Sum('debitamount'))) \
            .order_by('chartofaccount__accountcode')
            
            jvnumlast = lastJVNumber('true')
            latestjvnum = str(jvnumlast[0])
            jvnum = pdate[:4]
            last = str(int(latestjvnum) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                jvnum += '0'
            jvnum += last

            # strpdate = dt.strptime(pdate, '%Y-%m-%d')
            sinum = entries[0]['si_num']
            # billingremarks = ''
            
            main = Jvmain.objects.create(
                jvnum = jvnum,
                jvdate = pdate,
                jvtype_id = 1, # No JV Type - CHANGE THIS
                jvsubtype_id = 20, # Manual JV - CHANGE THIS
                branch_id = 5, # Head Office
                refnum = sinum,
                particular = '[SI'+str(sinum)+ '] '+ entries[0]['simain__particulars'],
                currency_id = 1,
                fxrate = 1,
                designatedapprover_id = 356, # Edsa Lanuza
                actualapprover_id = 356, # Edsa Lanuza
                approverremarks = 'Auto approved from SI Posting',
                responsedate = datetime.datetime.now(),
                jvstatus = 'A',
                enterby_id = request.user.id,
                enterdate = datetime.datetime.now(),
                modifyby_id = request.user.id,
                modifydate = datetime.datetime.now()
            )
            
            for entry in entries:
                amount += entry['debitdifference']
                Jvdetail.objects.create(
                    jvmain_id = main.id,
                    jv_num = main.jvnum,
                    jv_date = main.jvdate,
                    item_counter = counter,
                    debitamount = entry['debitdifference'],
                    creditamount = entry['creditdifference'],
                    balancecode = entry['balancecode'],
                    ataxcode_id = entry['ataxcode_id'],
                    bankaccount_id = entry['bankaccount_id'],
                    branch_id = entry['branch_id'],
                    chartofaccount_id = entry['chartofaccount_id'],
                    customer_id = entry['customer_id'],
                    department_id = entry['department_id'],
                    employee_id = entry['employee_id'],
                    inputvat_id = entry['inputvat_id'],
                    outputvat_id = entry['outputvat_id'],
                    product_id = entry['product_id'],
                    unit_id = entry['unit_id'],
                    vat_id = entry['vat_id'],
                    wtax_id = entry['wtax_id'],
                    status='A',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )
                counter += 1
            
            Simain.objects.filter(pk=id).update(
                jvmain_id = main.id,
                remarks = 'Sales Invoice ['+str(sinum)+']'
            )
            
            main.amount = amount
            main.save()
            
            amount = 0
            counter = 0

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)


@method_decorator(login_required, name='dispatch')
class TaggingIndexView(AjaxListView):
    model = Simain
    template_name = 'salesinvoice/tagging/index.html'
    page_template = 'salesinvoice/tagging/index_list.html'
    context_object_name = 'data_list'

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        # data for lookup
        context['sitype'] = Sitype.objects.filter(isdeleted=0).order_by('pk')
        context['customer'] = Customer.objects.filter(isdeleted=0).order_by('code')
        context['chart'] = Chartofaccount.objects.filter(isdeleted=0, accounttype='P', nontrade='Y').order_by('accountcode')
        # end data for lookup

        return context


@csrf_exempt
def transgenerate(request):
    dfrom = request.GET["dfrom"]
    dto = request.GET["dto"]
    document_type = request.GET["document_type"]
    chartofaccount = request.GET["chartofaccount"]
    report = request.GET["report"] 
    payeecode = request.GET["payeecode"]
    payeename = request.GET["payeename"]
    
    subs_filter_kwargs = {
        'document_date__range': [dfrom, dto]
    }
    si_filter_kwargs = {
        'sidate__range': [dfrom, dto]
    }
    
    # if payeecode:
        # subs_filter_kwargs['customer__code'] = payeecode
        # si_filter_kwargs['customer__code'] = payeecode
    if payeename:
        subs_filter_kwargs['customer__name'] = payeename
        si_filter_kwargs['customer__name'] = payeename
    if chartofaccount:
        subs_filter_kwargs['chartofaccount_id'] = chartofaccount
    if document_type:
        subs_filter_kwargs['document_type'] = document_type
        
    transaction = 1
    subs_data = queryLedger(dto, dfrom, transaction, chartofaccount, payeecode, payeename)
    
    # subs_data = Subledger.objects.filter(\
    #     **subs_filter_kwargs
    # ).values('id', 'reference_number', 'document_type', 'document_num', 'document_date', 'document_payee', 'customer_id', 'balancecode', 'amount', 'particulars').order_by('document_date', 'customer__code')

    si_data = Simain.objects.filter(\
        **si_filter_kwargs
    ).values('id', 'sinum', 'amount', 'customer_id', 'particulars').order_by('id')

    viewhtml = ''
    context = {}
    print 'subs_data', subs_data
    print 'si_data', si_data
    context['transdfrom'] = dfrom
    context['transdto'] = dto
    context['subledger_data'] = subs_data
    context['si_data'] = si_data
    context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
    viewhtml = render_to_string('salesinvoice/tagging/index_list.html', context)
    
    data = {
        'status': 'success',
        'viewhtml': viewhtml
    }
    
    return JsonResponse(data)


def queryLedger(dto, dfrom, transaction, chartofaccount, payeecode, payeename):
    
    conchart = ""
    orderby = "ORDER BY document_date ASC, FIELD(a.document_type, 'AP','CV','JV','OR')"
    conpayeecode = ""
    conpayeename = ""

    if chartofaccount:
        conchart = "SELECT id FROM chartofaccount WHERE id = '"+str(chartofaccount)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"
    else:
        conchart  = "SELECT id FROM chartofaccount WHERE main = '"+str(transaction)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"

    if payeecode:
        conpayeecode = "AND IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) = '"+str(payeecode)+"'"

    if payeename:
        conpayeename = "AND IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) LIKE '%"+str(payeename)+"%'"

    print conchart
    
    ''' Create query '''
    cursor = connection.cursor()
    try:
        query = "SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, a.document_refnum, a.document_refdate, " \
                "a.balancecode, IF (a.balancecode = 'C', a.amount, 0) AS creditamount, IF (a.balancecode = 'D', a.amount, 0) AS debitamount, " \
                "a.document_customer_id, a.document_supplier_id,  " \
                "b.accountcode, b.description, b.customer_enable, b.supplier_enable, b.nontrade, b.setup_customer, b.setup_supplier, " \
                "IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) AS pcode,  " \
                "IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) AS pname, " \
                "IF (b.customer_enable = 'Y', dcust.tin, IF (b.supplier_enable = 'Y', dsup.tin, IF (b.setup_customer != '', scust.tin, ssup.tin))) AS ptin, om.orsource   " \
                "FROM subledger AS a " \
                "LEFT OUTER JOIN chartofaccount AS b ON b.id = a.chartofaccount_id " \
                "LEFT OUTER JOIN customer AS dcust ON dcust.id = a.customer_id " \
                "LEFT OUTER JOIN customer AS scust ON scust.id =  b.setup_customer " \
                "LEFT OUTER JOIN supplier AS dsup ON dsup.id = a.document_supplier_id " \
                "LEFT OUTER JOIN supplier AS ssup ON ssup.id = b.setup_supplier " \
                "left outer join ordetail as od on (od.id = a.document_id and a.document_type = 'OR') " \
                "left outer join ormain as om on om.id = od.ormain_id " \
                "WHERE a.chartofaccount_id IN ("+str(conchart)+") " \
                ""+str(conpayeecode)+" "+str(conpayeename)+" AND DATE(document_date) >= '"+str(dfrom)+"' AND DATE(document_date) <= '"+str(dto)+"' "+str(orderby)

        ##"LEFT OUTER JOIN customer AS dcust ON dcust.id = a.document_customer_id "
        print query
        print '****'

        cursor.execute(query)
        result = namedtuplefetchall(cursor)
        
        return result
    finally:
        cursor.close()
        