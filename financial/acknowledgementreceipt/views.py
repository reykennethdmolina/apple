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

        # data for lookup
        context['artype'] = Artype.objects.filter(isdeleted=0).order_by('pk')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['arsubtype'] = Arsubtype.objects.filter(isdeleted=0)
        context['depositorybank'] = Bankaccount.objects.filter(isdeleted=0).order_by('bank__code')
        # data for lookup

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

        if self.request.POST.get('payor', False):
            context['payor'] = Employee.objects.get(pk=self.request.POST['payor_employee'], isdeleted=0)
        elif self.object.payor:
            context['payor'] = Employee.objects.get(pk=self.object.payor.id, isdeleted=0)

        # data for lookup
        context['artype'] = Artype.objects.filter(isdeleted=0).order_by('pk')
        context['collector'] = Collector.objects.filter(isdeleted=0).order_by('code')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['arsubtype'] = Arsubtype.objects.filter(isdeleted=0)
        context['depositorybank'] = Bankaccount.objects.filter(isdeleted=0).order_by('bank__code')
        # data for lookup

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

