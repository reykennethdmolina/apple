from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from branch.models import Branch
from companyparameter.models import Companyparameter
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from . models import Armain, Ardetail, Ardetailtemp, Ardetailbreakdown, Ardetailbreakdowntemp, Aritem, Aritemtemp
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from bankaccount.models import Bankaccount
from currency.models import Currency
from customer.models import Customer
from arsubtype.models import Arsubtype
from artype.models import Artype
from chartofaccount.models import Chartofaccount
from employee.models import Employee
from orsubtype.models import Orsubtype
from outputvattype.models import Outputvattype
from paytype.models import Paytype
from vat.models import Vat
from wtax.models import Wtax
from django.template.loader import render_to_string
from easy_pdf.views import PDFTemplateView
from dateutil.relativedelta import relativedelta
import datetime
from pprint import pprint
from django.utils.dateformat import DateFormat
from utils.mixins import ReportContentMixin
from bank.models import Bank
from bankbranch.models import Bankbranch
from collector.models import Collector
from paytype.models import Paytype
from agent.models import Agent
from product.models import Product
import decimal


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Armain
    template_name = 'acknowledgementreceipt/index.html'
    page_template = 'acknowledgementreceipt/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Armain.objects.all().filter(isdeleted=0)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(arnum__icontains=keysearch) |
                                 Q(ardate__icontains=keysearch) |
                                 Q(payor_name__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        # lookup
        context['artype'] = Artype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('name')
        context['depositorybank'] = Bankaccount.objects.filter(isdeleted=0).order_by('bank__code')
        context['pk'] = 0

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Armain
    template_name = 'acknowledgementreceipt/create.html'
    fields = ['ardate', 'artype', 'collector', 'branch', 'amount', 'amountinwords', 'depositorybank', 'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('acknowledgementreceipt.add_armain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['paytype'] = Paytype.objects.filter(isdeleted=0).order_by('pk')
        context['bank'] = Bank.objects.filter(isdeleted=0).order_by('code')
        context['arsubtype'] = Arsubtype.objects.filter(isdeleted=0)

        # lookup
        context['artype'] = Artype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['depositorybank'] = Bankaccount.objects.filter(isdeleted=0).order_by('bank__code')
        context['pk'] = 0

        closetransaction = Companyparameter.objects.all().first().last_closed_date
        validtransaction = closetransaction + relativedelta(months=1)
        context['validtransaction'] = validtransaction

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        year = str(form.cleaned_data['ardate'].year)
        yearqs = Armain.objects.filter(arnum__startswith=year)

        if yearqs:
            arnumlast = yearqs.latest('arnum')
            latestarnum = str(arnumlast)
            print "latest: " + latestarnum

            arnum = year
            last = str(int(latestarnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                arnum += '0'
            arnum += last
        else:
            arnum = year + '000001'

        print 'arnum: ' + arnum
        self.object.arnum = arnum

        if self.object.artype.code.startswith('AOE'):
            self.object.payor = Employee.objects.get(pk=int(self.request.POST['payor_employee']))
            self.object.payor_code = self.object.payor.code
            self.object.payor_name = (self.object.payor.firstname + ' ' + self.object.payor.lastname).upper()
        else:
            self.object.payor_code = 'NONTRADE'
            self.object.payor_name = self.request.POST['payor_others'].upper()

        self.object.arsubtype = Arsubtype.objects.get(
            pk=int(self.request.POST['arsubtype'])) if self.object.artype.code == 'NT' else None

        self.object.collector_code = self.object.collector.code
        self.object.collector_name = self.object.collector.name
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        # save aritemtemp to aritem
        itemtemp = Aritemtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
            order_by('enterdate')
        i = 1
        for itemtemp in itemtemp:
            item = Aritem()
            item.item_counter = i
            item.armain = self.object
            item.arnum = self.object.arnum
            item.ardate = self.object.ardate
            item.num = itemtemp.num
            item.authnum = itemtemp.authnum
            item.date = itemtemp.date
            item.amount = itemtemp.amount
            item.remarks = itemtemp.remarks
            item.bank = itemtemp.bank
            item.bankbranch = itemtemp.bankbranch
            item.paytype = itemtemp.paytype
            item.enterby = itemtemp.enterby
            item.modifyby = itemtemp.modifyby
            item.postby = itemtemp.postby
            item.enterdate = itemtemp.enterdate
            item.modifydate = itemtemp.modifydate
            item.postdate = itemtemp.postdate
            item.save()
            itemtemp.delete()
            i += 1

        # save ardetailtemp to ardetail
        source = 'ardetailtemp'
        mainid = self.object.id
        num = self.object.arnum
        secretkey = self.request.POST['secretkey']
        savedetail(source, mainid, num, secretkey, self.request.user)

        return HttpResponseRedirect('/acknowledgementreceipt/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Armain
    template_name = 'acknowledgementreceipt/update.html'
    fields = ['ardate', 'artype', 'collector', 'branch', 'amount', 'amountinwords', 'depositorybank', 'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('acknowledgementreceipt.change_armain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        self.mysecretkey = generatekey(self)

        # payment breakdown
        iteminfo = Aritem.objects.filter(armain=self.object.pk, isdeleted=0).order_by('item_counter')

        for data in iteminfo:
            detailtemp = Aritemtemp()
            detailtemp.item_counter = data.item_counter
            detailtemp.secretkey = self.mysecretkey
            detailtemp.armain = data.armain.id
            detailtemp.aritem = data.id
            detailtemp.arnum = data.arnum
            detailtemp.ardate = data.ardate
            detailtemp.paytype = data.paytype
            detailtemp.bank = data.bank
            detailtemp.bankbranch = data.bankbranch
            detailtemp.num = data.num
            detailtemp.authnum = data.authnum
            detailtemp.date = data.date
            detailtemp.amount = data.amount
            detailtemp.remarks = data.remarks
            detailtemp.enterdate = data.enterdate
            detailtemp.modifydate = data.modifydate
            detailtemp.postdate = data.postdate
            detailtemp.enterby = data.enterby
            detailtemp.modifyby = data.modifyby
            detailtemp.postby = data.postby
            detailtemp.save()

        # accounting entries
        detailinfo = Ardetail.objects.filter(armain=self.object.pk).order_by('item_counter')

        for drow in detailinfo:
            detail = Ardetailtemp()
            detail.secretkey = self.mysecretkey
            detail.ar_num = drow.ar_num
            detail.armain = drow.armain_id
            detail.ardetail = drow.pk
            detail.item_counter = drow.item_counter
            detail.ar_date = drow.ar_date
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

            breakinfo = Ardetailbreakdown.objects. \
                filter(ardetail_id=drow.id).order_by('pk', 'datatype')
            if breakinfo:
                for brow in breakinfo:
                    breakdown = Ardetailbreakdowntemp()
                    breakdown.ar_num = drow.ar_num
                    breakdown.secretkey = self.mysecretkey
                    breakdown.armain = drow.armain_id
                    breakdown.ardetail = drow.pk
                    breakdown.ardetailtemp = detailtempid
                    breakdown.ardetailbreakdown = brow.pk
                    breakdown.item_counter = brow.item_counter
                    breakdown.ar_date = brow.ar_date
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
        context['secretkey'] = generatekey(self)
        context['paytype'] = Paytype.objects.filter(isdeleted=0).order_by('pk')
        context['bank'] = Bank.objects.filter(isdeleted=0).order_by('code')
        context['arnum'] = self.object.arnum
        context['payor_name'] = self.object.payor_name
        context['saved_arsubtype'] = self.object.arsubtype.id if self.object.arsubtype else None
        context['arsubtype'] = Arsubtype.objects.filter(isdeleted=0)

        if self.request.POST.get('payor', False):
            context['payor'] = Employee.objects.get(pk=self.request.POST['payor_employee'], isdeleted=0)
        elif self.object.payor:
            context['payor'] = Employee.objects.get(pk=self.object.payor.id, isdeleted=0)

        # lookup
        context['artype'] = Artype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['depositorybank'] = Bankaccount.objects.filter(isdeleted=0).order_by('bank__code')
        context['pk'] = self.object.pk

        # requested items
        context['itemtemp'] = Aritemtemp.objects.filter(armain=self.object.pk, isdeleted=0,
                                                        secretkey=self.mysecretkey).order_by('item_counter')
        context['totalpaymentamount'] = Aritemtemp.objects.filter(armain=self.object.pk, isdeleted=0,
                                                                  secretkey=self.mysecretkey).\
            aggregate(Sum('amount'))

        # accounting entry starts here
        context['secretkey'] = self.mysecretkey
        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'ardetailtemp',
            'tablebreakdowntemp': 'ardetailbreakdowntemp',

            'datatemp': querystmtdetail('ardetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('ardetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        # accounting entry ends here

        return context

    def form_valid(self, form):
        if self.object.artype.code.startswith('AOE'):
            self.object.payor = Employee.objects.get(pk=int(self.request.POST['payor_employee']))
            self.object.payor_code = self.object.payor.code
            self.object.payor_name = (self.object.payor.firstname + ' ' + self.object.payor.lastname).upper()
        else:
            self.object.payor_code = 'NONTRADE'
            self.object.payor_name = self.request.POST['payor_others'].upper()

        self.object.arsubtype = Arsubtype.objects.get(
            pk=int(self.request.POST['arsubtype'])) if self.object.artype.code == 'NT' else None

        self.object.collector_code = self.object.collector.code
        self.object.collector_name = self.object.collector.name
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()

        self.object.save(update_fields=['ardate', 'artype', 'collector', 'branch', 'amount', 'amountinwords',
                                        'depositorybank', 'particulars', 'modifyby', 'modifydate', 'payor',
                                        'payor_code', 'payor_name', 'arsubtype', 'collector_code', 'collector_name'])

        # save aritemtemp to aritem
        Aritem.objects.filter(armain=self.object.pk).update(isdeleted=2)

        itemtemp = Aritemtemp.objects.filter(Q(secretkey=self.request.POST['secretkey'], armain=self.object.pk,
                                               isdeleted=0) | Q(secretkey=self.request.POST['secretkey'], armain=None)).\
            order_by('enterdate')

        i = 1
        for itemtemp in itemtemp:
            item = Aritem()
            item.item_counter = i
            item.armain = self.object
            item.arnum = self.object.arnum
            item.ardate = self.object.ardate
            item.num = itemtemp.num
            item.authnum = itemtemp.authnum
            item.date = itemtemp.date
            item.amount = itemtemp.amount
            item.remarks = itemtemp.remarks
            item.bank = itemtemp.bank
            item.bankbranch = itemtemp.bankbranch
            item.paytype = itemtemp.paytype
            item.enterby = itemtemp.enterby
            item.modifyby = itemtemp.modifyby
            item.postby = itemtemp.postby
            item.enterdate = itemtemp.enterdate
            item.modifydate = itemtemp.modifydate
            item.postdate = itemtemp.postdate
            item.save()
            itemtemp.delete()
            i += 1

        Aritem.objects.filter(armain=self.object.pk, isdeleted=2).delete()

        # accounting entry starts here..
        source = 'ardetailtemp'
        mainid = self.object.id
        num = self.object.arnum
        secretkey = self.request.POST['secretkey']
        updatedetail(source, mainid, num, secretkey, self.request.user)

        return HttpResponseRedirect('/acknowledgementreceipt/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Armain
    template_name = 'acknowledgementreceipt/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['detail'] = Ardetail.objects.filter(isdeleted=0).\
            filter(armain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Ardetail.objects.filter(isdeleted=0).\
            filter(armain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Ardetail.objects.filter(isdeleted=0).\
            filter(armain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        # requested items
        context['itemtemp'] = Aritem.objects.filter(armain=self.object.pk, isdeleted=0).order_by('item_counter')
        context['totalpaymentamount'] = Aritem.objects.filter(armain=self.object.pk, isdeleted=0).aggregate(
            Sum('amount'))

        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Armain
    template_name = 'acknowledgementreceipt/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('acknowledgementreceipt.delete_armain') or self.object.status == 'O' \
                or self.object.arstatus == 'A' or self.object.arstatus == 'I' or self.object.arstatus == 'R':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.arstatus = 'D'
        self.object.save()

        return HttpResponseRedirect('/acknowledgementreceipt')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Armain
    template_name = 'acknowledgementreceipt/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['armain'] = Armain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['items'] = Aritem.objects.filter(armain=self.kwargs['pk'], isdeleted=0).order_by('item_counter')
        context['detail'] = Ardetail.objects.filter(isdeleted=0, armain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Ardetail.objects.filter(isdeleted=0, armain_id=self.kwargs['pk']).\
            aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Ardetail.objects.filter(isdeleted=0, armain_id=self.kwargs['pk']).\
            aggregate(Sum('creditamount'))

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedar = Armain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedar.print_ctr += 1
        printedar.save()
        return context


@csrf_exempt
def savepaymentdetailtemp(request):
    if request.method == 'POST':
        if request.POST['id_itemtemp'] != '':  # if item already exists (update)
            itemtemp = Aritemtemp.objects.get(pk=int(request.POST['id_itemtemp']))
        else:  # if item does not exist (create)
            itemtemp = Aritemtemp()
            itemtemp.enterby = request.user
        itemtemp.item_counter = request.POST['itemno']
        itemtemp.secretkey = request.POST['secretkey']
        itemtemp.paytype = Paytype.objects.get(pk=int(request.POST['paytype']))
        itemtemp.amount = request.POST['amount'].replace(',', '')
        itemtemp.modifyby = request.user

        if itemtemp.paytype.code == 'CH':
            itemtemp.bank = Bank.objects.get(pk=int(request.POST['bank']))
            itemtemp.bankbranch = Bankbranch.objects.get(pk=int(request.POST['bankbranch']))
            itemtemp.num = request.POST['num']
            itemtemp.date = request.POST['date']
        elif itemtemp.paytype.code == 'CC':
            itemtemp.num = request.POST['num']
            itemtemp.authnum = request.POST['authnum']
            itemtemp.date = request.POST['date']
        elif itemtemp.paytype.code == 'EX':
            itemtemp.remarks = request.POST['remarks']

        itemtemp.save()
        data = {
            'status': 'success',
            'id': itemtemp.pk,
            'item_counter': itemtemp.item_counter,
            'paytype': itemtemp.paytype.description,
            'amount': itemtemp.amount,
            'bank': itemtemp.bank.code + ' ' + itemtemp.bankbranch.description if itemtemp.bank and itemtemp.bankbranch else ' - ',
            'number': itemtemp.num if itemtemp.num else ' - ',
            'date': itemtemp.date if itemtemp.date else ' - ',
            'authnum': itemtemp.authnum if itemtemp.authnum else ' - ',
            'remarks': itemtemp.remarks if itemtemp.remarks else ' - ',
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def deletepaymentdetailtemp(request):
    if request.method == 'POST':
        itemtemptodelete = Aritemtemp.objects.get(pk=request.POST['id_itemtemp'])
        if itemtemptodelete.armain is None:
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
def autoentry(request):
    if request.method == 'POST':
        # set isdeleted=2 for existing detailtemp data
        data_table = validatetable(request.POST['table'])
        if request.POST['arnum']:
            updateallquery(request.POST['table'], request.POST['arnum'])
        deleteallquery(request.POST['table'], request.POST['secretkey'])
        # set isdeleted=2 for existing detailtemp data

        # DEBIT ENTRY: CASH IN BANK, Bank Account is saved
        ardetailtemp1 = Ardetailtemp()
        ardetailtemp1.item_counter = 1
        ardetailtemp1.secretkey = request.POST['secretkey']
        ardetailtemp1.ar_num = ''
        ardetailtemp1.ar_date = datetime.datetime.now()
        ardetailtemp1.chartofaccount = Companyparameter.objects.get(code='PDI').coa_cashinbank_id
        ardetailtemp1.bankaccount = int(request.POST['bankaccount'])
        ardetailtemp1.debitamount = float(request.POST['amount'].replace(',', ''))
        ardetailtemp1.balancecode = 'D'
        ardetailtemp1.enterby = request.user
        ardetailtemp1.modifyby = request.user
        ardetailtemp1.save()

        # CREDIT ENTRY: Credit Chart of Account of OR Type, Credit Chart of Account of OR Subtype if Non-Trade
        ardetailtemp2 = Ardetailtemp()
        ardetailtemp2.item_counter = 2
        ardetailtemp2.secretkey = request.POST['secretkey']
        ardetailtemp2.ar_num = ''
        ardetailtemp2.ar_date = datetime.datetime.now()
        if Artype.objects.get(pk=int(request.POST['artype'])).code == 'NT':
            ardetailtemp2.chartofaccount = Arsubtype.objects.get(pk=int(request.POST['arsubtype'])).\
                arsubtypechartofaccount_id
        else:
            ardetailtemp2.chartofaccount = Artype.objects.get(pk=int(request.POST['artype'])).creditchartofaccount_id
        if Artype.objects.get(pk=int(request.POST['artype'])).code.startswith('AOE'):
            ardetailtemp2.employee = int(request.POST['employee'])
        ardetailtemp2.creditamount = float(request.POST['amount'].replace(',', ''))
        ardetailtemp2.balancecode = 'C'
        ardetailtemp2.enterby = request.user
        ardetailtemp2.modifyby = request.user
        ardetailtemp2.save()

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


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Armain
    template_name = 'acknowledgementreceipt/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        # context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('description')
        # context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('description')
        # context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        # context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        # context['user'] = User.objects.filter(is_active=1).order_by('first_name')
        # context['user'] = Employee.objects.filter(isdeleted=0).exclude(firstname='').order_by('firstname')
        # context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        # context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        # context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Armain
    template_name = 'acknowledgementreceipt/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "ACKNOWLEDGEMENT RECEIPT"
        context['rc_title'] = "ACKNOWLEDGEMENT RECEIPT"

        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_total = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        report_type = "AR Summary"
        query = Armain.objects.all().filter(isdeleted=0)

        # if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
        #     query = query.filter(ofnum__gte=int(key_data))
        # if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
        #     query = query.filter(ofnum__lte=int(key_data))

        # if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
        #     query = query.filter(ofdate__gte=key_data)
        # if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
        #     query = query.filter(ofdate__lte=key_data)

        # if request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name))
        #     query = query.filter(oftype=int(key_data))
        # if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
        #     query = query.filter(branch=int(key_data))
        # if request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name))
        #     query = query.filter(ofstatus=str(key_data))

        # if request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name))
        #     query = query.filter(requestor=int(key_data))
        # if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
        #     query = query.filter(department=int(key_data))
        # if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
        #     query = query.filter(Q(actualapprover=int(key_data)), Q(designatedapprover=int(key_data)))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        report_type = "AR Detailed"
        query = Aritem.objects.all().filter(isdeleted=0)

        # if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__ofnum__gte=int(key_data))
        # if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__ofnum__lte=int(key_data))

        # if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__ofdate__gte=key_data)
        # if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__ofdate__lte=key_data)

        # if request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__oftype=int(key_data))
        # if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__branch=int(key_data))
        # if request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__ofstatus=str(key_data))

        # if request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__requestor=int(key_data))
        # if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__department=int(key_data))
        # if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
        #     query = query.filter(Q(ofmain__actualapprover=int(key_data)), Q(ofmain__designatedapprover=int(key_data)))

        # if request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name))
        #     query = query.filter(ofsubtype=int(key_data))
        # if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
        #     query = query.filter(Q(payee_code__icontains=key_data) | Q(payee_name__icontains=key_data)
        #                          | Q(supplier_code__icontains=key_data) | Q(supplier_name__icontains=key_data))
        # if request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name))
        #     query = query.filter(ofitemstatus=str(key_data))
        # if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
        #     query = query.filter(vat=int(key_data))
        # if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
        #     query = query.filter(inputvattype=int(key_data))
        # if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
        #     query = query.filter(atc=int(key_data))
        # if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
        #     query = query.filter(deferredvat=str(key_data))

        if request.COOKIES.get('rep_f_order2_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order2_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        query = Ardetail.objects.all().filter(isdeleted=0)

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

        # if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__ofnum__gte=int(key_data))
        # if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__ofnum__lte=int(key_data))

        # if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__ofdate__gte=key_data)
        # if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__ofdate__lte=key_data)

        # if request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__oftype=int(key_data))
        # if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__branch=int(key_data))
        # if request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__ofstatus=str(key_data))

        # if request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__requestor=int(key_data))
        # if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
        #     query = query.filter(ofmain__department=int(key_data))
        # if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
        #     query = query.filter(Q(ofmain__actualapprover=int(key_data)), Q(designatedapprover=int(key_data)))

        # if request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name))
        #     query = query.filter(ofitem__ofsubtype=int(key_data))
        # if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
        #     query = query.filter(Q(ofitem__payee_code__icontains=key_data) | Q(ofitem__payee_name__icontains=key_data)
        #                          | Q(supplier__code__icontains=key_data) | Q(supplier__name__icontains=key_data))
        # if request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name))
        #     query = query.filter(ofitem__ofitemstatus=str(key_data))
        # if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
        #     query = query.filter(ofitem__vat=int(key_data))
        # if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
        #     query = query.filter(ofitem__inputvattype=int(key_data))
        # if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
        #     query = query.filter(ofitem__atc=int(key_data))
        # if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
        #     query = query.filter(ofitem__deferredvat=str(key_data))

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "AR Acctg Entry - Summary"

            query = query.values('chartofaccount__accountcode',
                                 'chartofaccount__title',
                                 'chartofaccount__description',
                                 'bankaccount__accountnumber',
                                 'department__departmentname',
                                 'employee__firstname',
                                 'employee__lastname',
                                 'supplier__name',
                                 'customer__name',
                                 'unit__description',
                                 'branch__description',
                                 'product__description',
                                 'inputvat__description',
                                 'outputvat__description',
                                 'vat__description',
                                 'wtax__description',
                                 'ataxcode__code',
                                 'balancecode')\
                         .annotate(Sum('debitamount'), Sum('creditamount'))\
                         .order_by('-balancecode',
                                   '-chartofaccount__accountcode',
                                   'bankaccount__accountnumber',
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
                                   'ataxcode__code')
        else:
            report_type = "AR Acctg Entry - Detailed"

            query = query.annotate(Sum('debitamount'), Sum('creditamount')).order_by('-balancecode',
                                                                                     '-chartofaccount__accountcode',
                                                                                     'bankaccount__accountnumber',
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
                                                                                     'ar_num')

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

    return query, report_type, report_total


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
    queryset, report_type, report_total = reportresultquery(request)
    report_type = report_type if report_type != '' else 'OF Report'
    worksheet = workbook.add_worksheet(report_type)
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
        amount_placement = 4
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        amount_placement = 8
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 14
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        amount_placement = 15

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'AR Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Payor', bold)
        worksheet.write('D1', 'Status', bold)
        worksheet.write('E1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.write('A1', 'AR Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Payor', bold)
        worksheet.write('D1', 'Number', bold)
        worksheet.write('E1', 'Auth. Number', bold)
        worksheet.write('F1', 'Bank', bold)
        worksheet.write('G1', 'Bank Branch', bold)
        worksheet.write('H1', 'Pay Type', bold)
        worksheet.write('J1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        worksheet.merge_range('A1:A2', 'Chart of Account', bold)
        worksheet.merge_range('B1:N1', 'Details', bold_center)
        worksheet.merge_range('O1:O2', 'Debit', bold_right)
        worksheet.merge_range('P1:P2', 'Credit', bold_right)
        worksheet.write('B2', 'Bank Account', bold)
        worksheet.write('C2', 'Department', bold)
        worksheet.write('D2', 'Employee', bold)
        worksheet.write('E2', 'Supplier', bold)
        worksheet.write('F2', 'Customer', bold)
        worksheet.write('G2', 'Unit', bold)
        worksheet.write('H2', 'Branch', bold)
        worksheet.write('I2', 'Product', bold)
        worksheet.write('J2', 'Input VAT', bold)
        worksheet.write('K2', 'Output VAT', bold)
        worksheet.write('L2', 'VAT', bold)
        worksheet.write('M2', 'WTAX', bold)
        worksheet.write('N2', 'ATAX Code', bold)
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
                "AR-" + obj.arnum,
                DateFormat(obj.ardate).format('Y-m-d'),
                obj.payor_name,
                obj.get_arstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            str_bank = obj.bank.code if obj.bank else ''
            str_bankbranch = obj.bankbranch.code if obj.bankbranch else ''

            data = [
                "AR-" + obj.armain.arnum,
                DateFormat(obj.ardate).format('Y-m-d'),
                obj.armain.payor_name,
                obj.num,
                obj.authnum,
                str_bank,
                str_bankbranch,
                obj.paytype.code,
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            str_firstname = obj['employee__firstname'] if obj['employee__firstname'] is not None else ''
            str_lastname = obj['employee__lastname'] if obj['employee__lastname'] is not None else ''

            data = [
                obj['chartofaccount__accountcode'] + " - " + obj['chartofaccount__description'],
                obj['bankaccount__accountnumber'],
                obj['department__departmentname'],
                str_firstname + " " + str_lastname,
                obj['supplier__name'],
                obj['customer__name'],
                obj['unit__description'],
                obj['branch__description'],
                obj['product__description'],
                obj['inputvat__description'],
                obj['outputvat__description'],
                obj['vat__description'],
                obj['wtax__description'],
                obj['ataxcode__code'],
                obj['debitamount__sum'],
                obj['creditamount__sum'],
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
            str_firstname = obj.employee.firstname if obj.employee is not None else ''
            str_lastname = obj.employee.lastname if obj.employee is not None else ''
            if obj.supplier is not None:
                str_payee = obj.supplier.name
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
                DateFormat(obj.ar_date).format('Y-m-d'),
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
            "", "", "",
            "Total", report_total['amount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        data = [
            "", "", "", "", "", "", "",
            "Total", report_total['amount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        data = [
            "", "", "", "", "", "", "", "", "", "", "", "", "",
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
    response['Content-Disposition'] = "attachment; filename="+report_type+".xlsx"
    return response
