from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from acctentry.views import updateallquery, validatetable, deleteallquery, generatekey, querystmtdetail, \
    querytotaldetail, savedetail, updatedetail
from supplier.models import Supplier
from branch.models import Branch
from bankbranchdisburse.models import Bankbranchdisburse
from vat.models import Vat
from ataxcode.models import Ataxcode
from inputvat.models import Inputvat
from inputvattype.models import Inputvattype
from companyparameter.models import Companyparameter
from creditterm.models import Creditterm
from currency.models import Currency
from apsubtype.models import Apsubtype
from aptype.models import Aptype
from operationalfund.models import Ofmain, Ofitem, Ofdetail
from processing_transaction.models import Poapvtransaction
from purchaseorder.models import Pomain, Podetail
from replenish_rfv.models import Reprfvmain, Reprfvdetail
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from . models import Apmain, Apdetail, Apdetailtemp, Apdetailbreakdown, Apdetailbreakdowntemp
from django.template.loader import render_to_string
from endless_pagination.views import AjaxListView
from django.db.models import Q, Sum
from easy_pdf.views import PDFTemplateView
import datetime
from django.utils.dateformat import DateFormat
from utils.mixins import ReportContentMixin
from decimal import Decimal


class IndexView(AjaxListView):
    model = Apmain
    template_name = 'accountspayable/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'accountspayable/index_list.html'

    def get_queryset(self):
        query = Apmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(apnum__icontains=keysearch) |
                                 Q(apdate__icontains=keysearch) |
                                 Q(payeecode__icontains=keysearch) |
                                 Q(payeename__icontains=keysearch) |
                                 Q(vatcode__icontains=keysearch) |
                                 Q(ataxcode__icontains=keysearch) |
                                 Q(bankbranchdisbursebranch__icontains=keysearch) |
                                 Q(refno__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        #lookup
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')
        context['pk'] = 0

        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Apmain
    template_name = 'accountspayable/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['detail'] = Apdetail.objects.filter(isdeleted=0).\
            filter(apmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Apdetail.objects.filter(isdeleted=0).\
            filter(apmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Apdetail.objects.filter(isdeleted=0).\
            filter(apmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, apmain=self.object.id).order_by('enterdate')
        ap_main_aggregate = Reprfvmain.objects.filter(isdeleted=0, apmain=self.object.id).aggregate(Sum('amount'))
        context['reprfv_total_amount'] = ap_main_aggregate['amount__sum']

        #lookup
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')
        context['pk'] = 0

        apacctgentries = Apdetail.objects.filter(ap_num=self.object.apnum, status='A', isdeleted=0, apmain=self.object)
        taxable_entries = apacctgentries.filter(balancecode='D', debitamount__gt=0.00).exclude(
            chartofaccount=Companyparameter.objects.get(code='PDI').coa_inputvat).order_by('item_counter')
        taxable_total = taxable_entries.aggregate(Sum('debitamount'))
        vat_entries = apacctgentries.filter(balancecode='D', debitamount__gt=0.00, chartofaccount=Companyparameter.
                                            objects.get(code='PDI').coa_inputvat).order_by('item_counter')
        vat_total = vat_entries.aggregate(Sum('debitamount'))
        aptrade_entries = apacctgentries.filter(balancecode='C', creditamount__gt=0.00).exclude(
            chartofaccount=Companyparameter.objects.get(code='PDI').coa_ewtax).order_by('item_counter')
        aptrade_total = aptrade_entries.aggregate(Sum('creditamount'))
        wtax_entries = apacctgentries.filter(balancecode='C', creditamount__gt=0.00, chartofaccount=Companyparameter.
                                             objects.get(code='PDI').coa_ewtax).order_by('item_counter')
        wtax_total = wtax_entries.aggregate(Sum('creditamount'))

        if self.object.vatrate > 0:
            context['vatablesale'] = taxable_total['debitamount__sum']
            context['vatexemptsale'] = 0
            context['vatzeroratedsale'] = 0
        elif self.object.vatcode == 'VE':
            context['vatablesale'] = 0
            context['vatexemptsale'] = taxable_total['debitamount__sum']
            context['vatzeroratedsale'] = 0
        elif self.object.vatcode == 'ZE' or self.object.vatcode == 'VATNA':
            context['vatablesale'] = 0
            context['vatexemptsale'] = 0
            context['vatzeroratedsale'] = taxable_total['debitamount__sum']

        context['totalsale'] = taxable_total['debitamount__sum']
        context['addvat'] = vat_total['debitamount__sum']
        context['totalpayment'] = aptrade_total['creditamount__sum']
        context['wtaxamount'] = wtax_total['creditamount__sum']
        context['wtaxrate'] = self.object.ataxrate

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Apmain
    template_name = 'accountspayable/create.html'
    fields = ['apdate', 'aptype', 'apsubtype', 'payee', 'branch',
              'bankbranchdisburse', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars', 'remarks',
              'currency', 'fxrate', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('accountspayable.add_apmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        if self.request.POST.get('payee', False):
            context['payee'] = Supplier.objects.get(pk=self.request.POST['payee'], isdeleted=0)
        context['currency'] = Currency.objects.filter(isdeleted=0)
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('code')
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        context['designatedapprover'] = User.objects.filter(is_active=1).order_by('first_name')
        context['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, apmain=None).order_by('enterdate')

        #lookup
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        try:
            apnumlast = Apmain.objects.latest('apnum')
            latestapnum = str(apnumlast)
            if latestapnum[0:4] == str(datetime.datetime.now().year):
                apnum = str(datetime.datetime.now().year)
                last = str(int(latestapnum[4:])+1)
                zero_addon = 6 - len(last)
                for x in range(0, zero_addon):
                    apnum += '0'
                apnum += last
            else:
                apnum = str(datetime.datetime.now().year) + '000001'
        except Apmain.DoesNotExist:
            apnum = str(datetime.datetime.now().year) + '000001'

        vatobject = Vat.objects.get(pk=self.request.POST['vat'], isdeleted=0)
        if self.request.POST['atax']:
            ataxobject = Ataxcode.objects.get(pk=self.request.POST['atax'], isdeleted=0)
        payeeobject = Supplier.objects.get(pk=self.request.POST['payee'], isdeleted=0)
        bankbranchdisburseobject = Bankbranchdisburse.objects.get(pk=self.request.POST['bankbranchdisburse'], isdeleted=0)

        self.object.apnum = apnum
        self.object.apstatus = 'F'
        self.object.vatcode = vatobject.code
        self.object.vatrate = vatobject.rate
        if self.request.POST['atax']:
            self.object.ataxcode = ataxobject.code
            self.object.ataxrate = ataxobject.rate
        self.object.payeecode = payeeobject.code
        self.object.payeename = payeeobject.name
        self.object.bankbranchdisbursebranch = bankbranchdisburseobject.branch
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        # accounting entry starts here..
        source = 'apdetailtemp'
        mainid = self.object.id
        num = self.object.apnum
        secretkey = self.request.POST['secretkey']
        savedetail(source, mainid, num, secretkey, self.request.user)

        # save apmain in reprfvmain, reprfvdetail, ofmain
        for i in range(len(self.request.POST.getlist('rfv_checkbox'))):
            reprfvmain = Reprfvmain.objects.get(pk=int(self.request.POST.getlist('rfv_checkbox')[i]))
            reprfvmain.apmain = self.object
            reprfvmain.save()
            reprfvdetail = Reprfvdetail.objects.filter(reprfvmain=reprfvmain)
            for data in reprfvdetail:
                data.apmain = self.object
                data.save()
                ofmain = Ofmain.objects.get(reprfvdetail=data)
                ofmain.apmain = self.object
                ofmain.save()
        # save apmain in reprfvmain, reprfvdetail, ofmain

        totaldebitamount = Apdetail.objects.filter(isdeleted=0).filter(apmain_id=self.object.id).aggregate(
            Sum('debitamount'))
        totalcreditamount = Apdetail.objects.filter(isdeleted=0).filter(apmain_id=self.object.id).aggregate(
            Sum('creditamount'))

        if totaldebitamount['debitamount__sum'] == totalcreditamount['creditamount__sum']:
            self.object.amount = totaldebitamount['debitamount__sum']
            self.object.save(update_fields=['amount'])
        else:
            print "Debit and Credit amounts are not equal. AP Amount is not saved."

        return HttpResponseRedirect('/accountspayable/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Apmain
    template_name = 'accountspayable/edit.html'
    fields = ['apdate', 'aptype', 'apsubtype', 'payee', 'branch',
              'bankbranchdisburse', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars', 'remarks',
              'currency', 'fxrate', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('accountspayable.change_apmain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # accounting entry starts here
    def get_initial(self):
        self.mysecretkey = generatekey(self)

        detailinfo = Apdetail.objects.filter(apmain=self.object.pk).order_by('item_counter')

        for drow in detailinfo:
            detail = Apdetailtemp()
            detail.secretkey = self.mysecretkey
            detail.ap_num = drow.ap_num
            detail.apmain = drow.apmain_id
            detail.apdetail = drow.pk
            detail.item_counter = drow.item_counter
            detail.ap_date = drow.ap_date
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
            detail.isautogenerated = drow.isautogenerated
            detail.save()

            detailtempid = detail.id

            breakinfo = Apdetailbreakdown.objects.\
                filter(apdetail_id=drow.id).order_by('pk', 'datatype')
            if breakinfo:
                for brow in breakinfo:
                    breakdown = Apdetailbreakdowntemp()
                    breakdown.ap_num = drow.ap_num
                    breakdown.secretkey = self.mysecretkey
                    breakdown.apmain = drow.apmain_id
                    breakdown.apdetail = drow.pk
                    breakdown.apdetailtemp = detailtempid
                    breakdown.apdetailbreakdown = brow.pk
                    breakdown.item_counter = brow.item_counter
                    breakdown.ap_date = brow.ap_date
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
        if self.request.POST.get('payee', False):
            context['payee'] = Supplier.objects.get(pk=self.request.POST['payee'], isdeleted=0)
        elif self.object.payee:
            context['payee'] = Supplier.objects.get(pk=self.object.payee.id, isdeleted=0)
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')
        context['currency'] = Currency.objects.filter(isdeleted=0)
        context['apnum'] = self.object.apnum
        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('code')
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = self.object.pk
        context['designatedapprover'] = User.objects.filter(is_active=1).order_by('first_name')
        context['originalapstatus'] = Apmain.objects.get(pk=self.object.id).apstatus
        context['actualapprover'] = None if Apmain.objects.get(
            pk=self.object.id).actualapprover is None else Apmain.objects.get(pk=self.object.id).actualapprover.id
        context['savedapsubtype'] = Apmain.objects.get(pk=self.object.id).apsubtype.code
        context['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, apmain=self.object.id).order_by('enterdate')
        ap_main_aggregate = Reprfvmain.objects.filter(isdeleted=0, apmain=self.object.id).aggregate(Sum('amount'))
        context['reprfv_total_amount'] = ap_main_aggregate['amount__sum']

        context['selectedapsubtype'] = self.object.apsubtype.code

        # accounting entry starts here
        context['secretkey'] = self.mysecretkey
        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'apdetailtemp',
            'tablebreakdowntemp': 'apdetailbreakdowntemp',

            'datatemp': querystmtdetail('apdetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('apdetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        # accounting entry ends here

        apacctgentries = Apdetail.objects.filter(ap_num=self.object.apnum, status='A', isdeleted=0, apmain=self.object)
        taxable_entries = apacctgentries.filter(balancecode='D', debitamount__gt=0.00).exclude(
            chartofaccount=Companyparameter.objects.get(code='PDI').coa_inputvat).order_by('item_counter')
        taxable_total = taxable_entries.aggregate(Sum('debitamount'))
        vat_entries = apacctgentries.filter(balancecode='D', debitamount__gt=0.00, chartofaccount=Companyparameter.
                                            objects.get(code='PDI').coa_inputvat).order_by('item_counter')
        vat_total = vat_entries.aggregate(Sum('debitamount'))
        aptrade_entries = apacctgentries.filter(balancecode='C', creditamount__gt=0.00).exclude(
            chartofaccount=Companyparameter.objects.get(code='PDI').coa_ewtax).order_by('item_counter')
        aptrade_total = aptrade_entries.aggregate(Sum('creditamount'))
        wtax_entries = apacctgentries.filter(balancecode='C', creditamount__gt=0.00, chartofaccount=Companyparameter.
                                             objects.get(code='PDI').coa_ewtax).order_by('item_counter')
        wtax_total = wtax_entries.aggregate(Sum('creditamount'))

        if self.object.vatrate > 0:
            context['vatablesale'] = taxable_total['debitamount__sum']
            context['vatexemptsale'] = 0
            context['vatzeroratedsale'] = 0
        elif self.object.vatcode == 'VE':
            context['vatablesale'] = 0
            context['vatexemptsale'] = taxable_total['debitamount__sum']
            context['vatzeroratedsale'] = 0
        elif self.object.vatcode == 'ZE' or self.object.vatcode == 'VATNA':
            context['vatablesale'] = 0
            context['vatexemptsale'] = 0
            context['vatzeroratedsale'] = taxable_total['debitamount__sum']

        context['totalsale'] = taxable_total['debitamount__sum']
        context['addvat'] = vat_total['debitamount__sum']
        context['totalpayment'] = aptrade_total['creditamount__sum']
        context['wtaxamount'] = wtax_total['creditamount__sum']
        context['wtaxrate'] = self.object.ataxrate

        return context

    def form_valid(self, form):
        if self.request.POST['originalapstatus'] != 'R':
            self.object = form.save(commit=False)
            self.object.payee = Supplier.objects.get(pk=self.request.POST['payee'])
            self.object.payeecode = self.object.payee.code
            self.object.payeename = self.object.payee.name
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.bankbranchdisbursebranch = self.object.bankbranchdisburse.branch
            self.object.save(update_fields=['apdate', 'aptype', 'apsubtype', 'payee', 'payeecode', 'payeename',
                                            'branch', 'bankbranchdisburse', 'vat', 'atax', 'bankbranchdisbursebranch',
                                            'inputvattype', 'creditterm', 'duedate',
                                            'refno', 'deferred', 'particulars', 'remarks',
                                            'currency', 'fxrate', 'designatedapprover',
                                            'modifyby', 'modifydate', 'apstatus'])

            if self.object.apstatus == 'F':
                self.object.designatedapprover = User.objects.get(pk=self.request.POST['designatedapprover'])
                self.object.save(update_fields=['designatedapprover'])

            # revert status from APPROVED/DISAPPROVED to For Approval if no response date or approver response is saved
            # remove approval details if APSTATUS is not APPROVED/DISAPPROVED
            if self.object.apstatus == 'A' or self.object.apstatus == 'D':
                if self.object.responsedate is None or self.object.approverresponse is None or self.object.\
                        actualapprover is None:
                    print self.object.responsedate
                    print self.object.approverresponse
                    print self.object.actualapprover
                    self.object.responsedate = None
                    self.object.approverremarks = None
                    self.object.approverresponse = None
                    self.object.actualapprover = None
                    self.object.apstatus = 'F'
                    self.object.save(update_fields=['responsedate', 'approverremarks', 'approverresponse',
                                                    'actualapprover', 'apstatus'])
            elif self.object.apstatus == 'F':
                self.object.responsedate = None
                self.object.approverremarks = None
                self.object.approverresponse = None
                self.object.actualapprover = None
                self.object.save(update_fields=['responsedate', 'approverremarks', 'approverresponse',
                                                'actualapprover'])

            # revert status from RELEASED to Approved if no release date is saved
            # remove release details if APSTATUS is not RELEASED
            if self.object.apstatus == 'R' and self.object.releasedate is None:
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.apstatus = 'A'
                self.object.save(update_fields=['releaseby', 'releasedate', 'apstatus'])
            elif self.object.apstatus != 'R':
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.save(update_fields=['releaseby', 'releasedate'])

            # accounting entry starts here..
            source = 'apdetailtemp'
            mainid = self.object.id
            num = self.object.apnum
            secretkey = self.request.POST['secretkey']
            updatedetail(source, mainid, num, secretkey, self.request.user)

            totaldebitamount = Apdetail.objects.filter(isdeleted=0).filter(apmain_id=self.object.id).aggregate(
                Sum('debitamount'))
            totalcreditamount = Apdetail.objects.filter(isdeleted=0).filter(apmain_id=self.object.id).aggregate(
                Sum('creditamount'))

            if totaldebitamount['debitamount__sum'] == totalcreditamount['creditamount__sum']:
                self.object.amount = totaldebitamount['debitamount__sum']
                self.object.save(update_fields=['amount'])
            else:
                print "Debit and Credit amounts are not equal. AP Amount is not saved."

        else:
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['modifyby', 'modifydate', 'remarks'])

        return HttpResponseRedirect('/accountspayable/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Apmain
    template_name = 'accountspayable/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('accountspayable.delete_apmain') or self.object.status == 'O' \
                or self.object.apstatus == 'A' or self.object.apstatus == 'I' or self.object.apstatus == 'R':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.apstatus = 'D'
        self.object.save()

        # remove references in reprfvmain, reprfvdetail, ofmain
        reprfvmain = Reprfvmain.objects.filter(apmain=self.object.id)
        for data in reprfvmain:
            data.apmain = None
            data.save()

        reprfvdetail = Reprfvdetail.objects.filter(apmain=self.object.id)
        for data in reprfvdetail:
            data.apmain = None
            data.save()

        ofmain = Ofmain.objects.filter(apmain=self.object.id)
        for data in ofmain:
            data.apmain = None
            data.save()
        # remove references in reprfvmain, reprfvdetail, ofmain

        # remove references in PO tables
        poapvtrans = Poapvtransaction.objects.filter(apmain=self.object)
        for data in poapvtrans:
            podetail = Podetail.objects.filter(pk=data.podetail.id).first()
            podetail.apvtotalamount -= data.apamount
            podetail.apvremainingamount += data.apamount
            podetail.isfullyapv = 0
            podetail.save()
            pomain = Pomain.objects.filter(pk=podetail.pomain.id).first()
            pomain.apvamount -= data.apamount
            pomain.totalremainingamount += data.apamount
            pomain.isfullyapv = 0
            pomain.save()
            data.delete()

        return HttpResponseRedirect('/accountspayable')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Apmain
    template_name = 'accountspayable/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['apmain'] = Apmain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['detail'] = Apdetail.objects.filter(isdeleted=0). \
            filter(apmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Apdetail.objects.filter(isdeleted=0). \
            filter(apmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Apdetail.objects.filter(isdeleted=0). \
            filter(apmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, apmain=self.kwargs['pk']).order_by('enterdate')
        ap_main_aggregate = Reprfvmain.objects.filter(isdeleted=0, apmain=self.kwargs['pk']).aggregate(Sum('amount'))
        context['reprfv_total_amount'] = ap_main_aggregate['amount__sum']

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedap = Apmain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        printedap.print_ctr += 1
        printedap.save()
        return context


@csrf_exempt
def approve(request):
    if request.method == 'POST':
        ap_for_approval = Apmain.objects.get(apnum=request.POST['apnum'])
        if request.user.has_perm('accountspayable.approve_allap') or \
                request.user.has_perm('accountspayable.approve_assignedap'):
            if request.user.has_perm('accountspayable.approve_allap') or \
                    (request.user.has_perm('accountspayable.approve_assignedap') and
                             ap_for_approval.designatedapprover == request.user):
                print "back to in-process = " + str(request.POST['backtoinprocess'])
                if request.POST['originalapstatus'] != 'R' or int(request.POST['backtoinprocess']) == 1:
                    ap_for_approval.apstatus = request.POST['approverresponse']
                    ap_for_approval.isdeleted = 0
                    if request.POST['approverresponse'] == 'D':
                        ap_for_approval.status = 'C'
                    else:
                        ap_for_approval.status = 'A'
                    ap_for_approval.approverresponse = request.POST['approverresponse']
                    ap_for_approval.responsedate = request.POST['responsedate']
                    ap_for_approval.actualapprover = User.objects.get(pk=request.user.id)
                    ap_for_approval.approverremarks = request.POST['approverremarks']
                    ap_for_approval.releaseby = None
                    ap_for_approval.releasedate = None
                    ap_for_approval.save()
                    data = {
                        'status': 'success',
                        'apnum': ap_for_approval.apnum,
                        'newapstatus': ap_for_approval.apstatus,
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
def release(request):
    if request.method == 'POST':
        ap_for_release = Apmain.objects.get(apnum=request.POST['apnum'])
        if ap_for_release.apstatus != 'F' and ap_for_release.apstatus != 'D':
            ap_for_release.releaseby = User.objects.get(pk=request.POST['releaseby'])
            ap_for_release.releasedate = request.POST['releasedate']
            ap_for_release.apstatus = 'R'
            ap_for_release.save()
            data = {
                'status': 'success',
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
def importreprfv(request):
    if request.method == 'POST':
        first_ofmain = Ofmain.objects.filter(reprfvmain=request.POST.getlist('checked_reprfvmain[]')[0], isdeleted=0,
                                             status='A').first()
        first_ofitem = Ofitem.objects.filter(ofmain=first_ofmain.id, isdeleted=0, status='A').first()

        ofdetail = Ofdetail.objects.filter(ofmain__reprfvmain__in=set(request.POST.getlist('checked_reprfvmain[]'))).\
            order_by('ofmain', 'item_counter')
        # amount_totals = ofdetail.aggregate(Sum('debitamount'), Sum('creditamount'))
        ofdetail = ofdetail.values('chartofaccount__accountcode',
                                   'chartofaccount__id',
                                   'chartofaccount__title',
                                   'chartofaccount__description',
                                   'bankaccount__id',
                                   'bankaccount__accountnumber',
                                   'department__id',
                                   'department__departmentname',
                                   'employee__id',
                                   'employee__firstname',
                                   'supplier__id',
                                   'supplier__name',
                                   'customer__id',
                                   'customer__name',
                                   'branch__id',
                                   'branch__description',
                                   'product__id',
                                   'product__description',
                                   'unit__id',
                                   'unit__description',
                                   'inputvat__id',
                                   'inputvat__description',
                                   'outputvat__id',
                                   'outputvat__description',
                                   'vat__id',
                                   'vat__description',
                                   'wtax__id',
                                   'wtax__description',
                                   'ataxcode__id',
                                   'ataxcode__code',
                                   'balancecode') \
                           .annotate(Sum('debitamount'), Sum('creditamount')) \
                           .order_by('-chartofaccount__accountcode',
                                     'bankaccount__accountnumber',
                                     'department__departmentname',
                                     'employee__firstname',
                                     'supplier__name',
                                     'customer__name',
                                     'branch__description',
                                     'product__description',
                                     'inputvat__description',
                                     'outputvat__description',
                                     '-vat__description',
                                     'wtax__description',
                                     'ataxcode__code')

        # set isdeleted=2 for existing detailtemp data
        data_table = validatetable(request.POST['table'])
        deleteallquery(request.POST['table'], request.POST['secretkey'])

        if 'apnum' in request.POST:
            if request.POST['apnum']:
                updateallquery(request.POST['table'], request.POST['apnum'])
        # set isdeleted=2 for existing detailtemp data

        i = 1
        for detail in ofdetail:
            apdetailtemp = Apdetailtemp()
            apdetailtemp.item_counter = i
            apdetailtemp.secretkey = request.POST['secretkey']
            apdetailtemp.ap_date = datetime.datetime.now()
            apdetailtemp.chartofaccount = detail['chartofaccount__id']
            apdetailtemp.bankaccount = detail['bankaccount__id']
            apdetailtemp.department = detail['department__id']
            apdetailtemp.employee = detail['employee__id']
            apdetailtemp.supplier = detail['supplier__id']
            apdetailtemp.customer = detail['customer__id']
            apdetailtemp.unit = detail['unit__id']
            apdetailtemp.branch = detail['branch__id']
            apdetailtemp.product = detail['product__id']
            apdetailtemp.inputvat = detail['inputvat__id']
            apdetailtemp.outputvat = detail['outputvat__id']
            apdetailtemp.vat = detail['vat__id']
            apdetailtemp.wtax = detail['wtax__id']
            apdetailtemp.ataxcode = detail['ataxcode__id']
            apdetailtemp.debitamount = detail['debitamount__sum']
            apdetailtemp.creditamount = detail['creditamount__sum']
            apdetailtemp.balancecode = detail['balancecode']
            apdetailtemp.enterby = request.user
            apdetailtemp.modifyby = request.user
            apdetailtemp.save()
            i += 1

        context = {
            'tabledetailtemp': data_table['str_detailtemp'],
            'tablebreakdowntemp': data_table['str_detailbreakdowntemp'],
            'datatemp': querystmtdetail(data_table['str_detailtemp'], request.POST['secretkey']),
            'datatemptotal': querytotaldetail(data_table['str_detailtemp'], request.POST['secretkey']),
        }

        data = {
            'datatable': render_to_string('acctentry/datatable.html', context),
            'status': 'success',
            'branch': first_ofmain.branch_id,
            'vat': first_ofitem.vat_id,
            'atc': first_ofitem.atc_id,
            'inputvattype': first_ofitem.inputvattype_id,
            'deferredvat': first_ofitem.deferredvat
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Apmain
    template_name = 'accountspayable/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['aptype'] = Aptype.objects.filter(isdeleted=0).order_by('description')
        context['apsubtype'] = Apsubtype.objects.filter(isdeleted=0).order_by('description')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Apmain
    template_name = 'accountspayable/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['rfv'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "ACCOUNTS PAYABLE"
        context['rc_title'] = "ACCOUNTS PAYABLE"

        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_total = ''
    rfv = 'hide'

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's' \
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd' \
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':

        if request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name):
            subtype = str(request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name))
        else:
            subtype = ''

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's'\
                or (request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd'
                    and (subtype == '' or subtype == '2')):
            if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
                report_type = "AP Detailed"
            else:
                report_type = "AP Summary"

            query = Apmain.objects.all().filter(isdeleted=0)

            if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
                query = query.filter(apnum__gte=int(key_data))
            if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
                query = query.filter(apnum__lte=int(key_data))

            if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
                query = query.filter(apdate__gte=key_data)
            if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
                query = query.filter(apdate__lte=key_data)

            if request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name))
                query = query.filter(aptype=int(key_data))
            if request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name))
                query = query.filter(apsubtype=int(key_data))
            if request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name))
                query = query.filter(apstatus=str(key_data))
            if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
                query = query.filter(status=str(key_data))

            if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
                query = query.filter(branch=int(key_data))
            if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
                query = query.filter(Q(payeecode__icontains=key_data) | Q(payeename__icontains=key_data))
            # if request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name):
            #     key_data = str(request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name))
            #     query = query.filter(Q(checknum__icontains=key_data))
            if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
                query = query.filter(Q(refno__icontains=key_data))
            if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
                query = query.filter(currency=int(key_data))

            if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
                query = query.filter(vat=int(key_data))
            if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
                query = query.filter(inputvattype=int(key_data))
            if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
                query = query.filter(atax=int(key_data))
            if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
                query = query.filter(deferred=str(key_data))
            if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
                query = query.filter(bankbranchdisburse=int(key_data))
            if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(amount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
                query = query.filter(amount__lte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    query = query.order_by(*key_data)

            report_total = query.aggregate(Sum('amount'))\

        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            report_type = "AP Detailed"
            rfv = "show"

            query = Reprfvmain.objects.all().filter(isdeleted=0).exclude(apmain__isnull=True)

            if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__apnum__gte=int(key_data))
            if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
                query = query.filter(apmain__apnum__lte=int(key_data))

            if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__apdate__gte=key_data)
            if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
                query = query.filter(apmain__apdate__lte=key_data)

            if request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name))
                query = query.filter(apmain__aptype=int(key_data))
            if request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name))
                query = query.filter(apmain__apsubtype=int(key_data))
            if request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name))
                query = query.filter(apmain__apstatus=str(key_data))
            if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
                query = query.filter(apmain__status=str(key_data))

            if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
                query = query.filter(apmain__branch=int(key_data))
            if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
                query = query.filter(Q(apmain__payeecode__icontains=key_data) | Q(apmain__payeename__icontains=key_data))
            # if request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name):
            #     key_data = str(request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name))
            #     query = query.filter(Q(apmain__checknum__icontains=key_data))
            if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
                query = query.filter(Q(apmain__refno__icontains=key_data))
            if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
                query = query.filter(apmain__currency=int(key_data))

            if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
                query = query.filter(apmain__vat=int(key_data))
            if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
                query = query.filter(apmain__inputvattype=int(key_data))
            if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
                query = query.filter(apmain__atax=int(key_data))
            if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
                query = query.filter(apmain__deferred=str(key_data))
            if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
                query = query.filter(apmain__bankbranchdisburse=int(key_data))

            if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__amount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
                query = query.filter(apmain__amount__lte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    for n,data in enumerate(key_data):
                        key_data[n] = "apmain__" + data
                    query = query.order_by(*key_data)
                else:
                    query = query.order_by('apmain')

            report_total = query.values('apmain').annotate(Sum('amount')).aggregate(Sum('apmain__amount'))

        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
            report_type = "AP Unbalanced"

            query = Apdetail.objects.filter(isdeleted=0, apmain__isdeleted=0)

            if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__apnum__gte=int(key_data))
            if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
                query = query.filter(apmain__apnum__lte=int(key_data))

            if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__apdate__gte=key_data)
            if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
                query = query.filter(apmain__apdate__lte=key_data)

            if request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name))
                query = query.filter(apmain__aptype=int(key_data))
            if request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name))
                query = query.filter(apmain__apsubtype=int(key_data))
            if request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name))
                query = query.filter(apmain__apstatus=str(key_data))
            if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
                query = query.filter(apmain__status=str(key_data))

            if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
                query = query.filter(apmain__branch=int(key_data))
            if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
                query = query.filter(Q(apmain__payeecode__icontains=key_data) | Q(apmain__payeename__icontains=key_data))
            if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
                query = query.filter(Q(apmain__refno__icontains=key_data))
            if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
                query = query.filter(apmain__currency=int(key_data))

            if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
                query = query.filter(apmain__vat=int(key_data))
            if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
                query = query.filter(apmain__inputvattype=int(key_data))
            if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
                query = query.filter(apmain__atax=int(key_data))
            if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
                query = query.filter(apmain__deferred=str(key_data))
            if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
                query = query.filter(apmain__bankbranchdisburse=int(key_data))
            if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(apmain__amount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
                query = query.filter(apmain__amount__lte=float(key_data.replace(',', '')))

            query = query.values('apmain__apnum') \
                .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),
                          creditsum=Sum('creditamount')) \
                .values('apmain__apnum', 'margin', 'apmain__apdate', 'debitsum', 'creditsum').order_by('apmain__apnum').exclude(margin=0)

            if request.COOKIES.get('rep_f_uborder_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_uborder_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    query = query.order_by(*key_data)

            report_total = query.aggregate(Sum('debitsum'), Sum('creditsum'), Sum('margin'))

        if request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name))
            if key_data == 'd':
                query = query.reverse()

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        query = Apdetail.objects.all().filter(isdeleted=0)

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
            query = query.filter(apmain__apnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(apmain__apnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(apmain__apdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(apmain__apdate__lte=key_data)

        if request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_aptype_' + request.resolver_match.app_name))
            query = query.filter(apmain__aptype=int(key_data))
        if request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_apsubtype_' + request.resolver_match.app_name))
            query = query.filter(apmain__apsubtype=int(key_data))
        if request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_apstatus_' + request.resolver_match.app_name))
            query = query.filter(apmain__apstatus=str(key_data))
        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            query = query.filter(apmain__status=str(key_data))

        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(apmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
            query = query.filter(Q(apmain__payeecode__icontains=key_data) | Q(apmain__payeename__icontains=key_data))
        # if request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name))
        #     query = query.filter(Q(apmain__checknum__icontains=key_data))
        if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
            query = query.filter(Q(apmain__refno__icontains=key_data))
        if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
            query = query.filter(apmain__currency=int(key_data))

        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(apmain__vat=int(key_data))
        if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
            query = query.filter(apmain__inputvattype=int(key_data))
        if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
            query = query.filter(apmain__atax=int(key_data))
        if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
            query = query.filter(apmain__deferred=str(key_data))
        if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
            query = query.filter(apmain__bankbranchdisburse=int(key_data))

        if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(apmain__amount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
            query = query.filter(apmain__amount__lte=float(key_data.replace(',', '')))

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "AP Acctg Entry - Summary"

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
            report_type = "AP Acctg Entry - Detailed"

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
                                                                                     'ap_num')

    return query, report_type, report_total, rfv


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
    queryset, report_type, report_total, rfv = reportresultquery(request)
    report_type = report_type if report_type != '' else 'AP Report'
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
        amount_placement = 6
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        amount_placement = 11 if rfv == 'show' else 9
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
        amount_placement = 2
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 14
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        amount_placement = 15

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'AP Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Type', bold)
        worksheet.write('D1', 'Subtype', bold)
        worksheet.write('E1', 'Payee', bold)
        worksheet.write('F1', 'Status', bold)
        worksheet.write('G1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if rfv == 'show':
            worksheet.merge_range('A1:A2', 'AP Number', bold)
            worksheet.merge_range('B1:B2', 'Date', bold)
            worksheet.merge_range('C1:C2', 'Type', bold)
            worksheet.merge_range('D1:D2', 'Subtype', bold)
            worksheet.merge_range('E1:E2', 'Payee', bold)
            worksheet.merge_range('F1:F2', 'VAT', bold)
            worksheet.merge_range('G1:G2', 'ATC', bold)
            worksheet.merge_range('H1:H2', 'In/VAT', bold)
            worksheet.merge_range('I1:I2', 'Status', bold)
            worksheet.merge_range('J1:L1', 'Replenished RFV', bold_center)
            worksheet.merge_range('M1:M2', 'Amount', bold_right)
            worksheet.write('J2', 'Rep RFV Number', bold)
            worksheet.write('K2', 'Date', bold)
            worksheet.write('L2', 'Rep RFV Amount', bold_right)
            row += 1
        else:
            worksheet.write('A1', 'AP Number', bold)
            worksheet.write('B1', 'Date', bold)
            worksheet.write('C1', 'Type', bold)
            worksheet.write('D1', 'Subtype', bold)
            worksheet.write('E1', 'Payee', bold)
            worksheet.write('F1', 'VAT', bold)
            worksheet.write('G1', 'ATC', bold)
            worksheet.write('H1', 'In/VAT', bold)
            worksheet.write('I1', 'Status', bold)
            worksheet.write('J1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
        worksheet.write('A1', 'AP Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Debit', bold_right)
        worksheet.write('D1', 'Credit', bold_right)
        worksheet.write('E1', 'Margin', bold_right)
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
                obj.apnum,
                DateFormat(obj.apdate).format('Y-m-d'),
                obj.aptype.description if obj.aptype else '',
                obj.apsubtype.description if obj.apsubtype else '',
                obj.payee.name,
                obj.get_apstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            if rfv == 'show':
                data = [
                    obj.apmain.apnum,
                    DateFormat(obj.apmain.apdate).format('Y-m-d'),
                    obj.apmain.aptype.description if obj.apmain.aptype else '',
                    obj.apmain.apsubtype.description if obj.apmain.apsubtype else '',
                    obj.apmain.payee.name,
                    obj.apmain.vat.code if obj.apmain.vat else '',
                    obj.apmain.atax.code if obj.apmain.atax else '',
                    obj.apmain.inputvattype.description if obj.apmain.inputvattype else '',
                    obj.apmain.get_apstatus_display(),
                    'RFV-' + obj.reprfvnum,
                    DateFormat(obj.reprfvdate).format('Y-m-d'),
                    obj.amount,
                    obj.apmain.amount,
                ]
            else:
                data = [
                    obj.apnum,
                    DateFormat(obj.apdate).format('Y-m-d'),
                    obj.aptype.description if obj.aptype else '',
                    obj.apsubtype.description if obj.apsubtype else '',
                    obj.payee.name,
                    obj.vat.code if obj.vat else '',
                    obj.atax.code if obj.atax else '',
                    obj.inputvattype.description if obj.inputvattype else '',
                    obj.get_apstatus_display(),
                    obj.amount,
                ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
            data = [
                obj.apmain__apnum,
                DateFormat(obj.apmain__apdate).format('Y-m-d'),
                obj.debitsum,
                obj.creditsum,
                obj.margin,
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
                obj.supplier.name if obj.supplier is not None else '',
                DateFormat(obj.ap_date).format('Y-m-d'),
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
            "", "", "", "", "",
            "Total", report_total['amount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if rfv == 'show':
            data = [
                "", "", "", "", "", "", "", "", "", "", "",
                "Total", report_total['apmain__amount__sum'],
            ]
        else:
            data = [
                "", "", "", "", "", "", "", "", "", "",
                "Total", report_total['amount__sum'],
            ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
        data = [
            "",
            "Total", report_total['debitsum__sum'], report_total['creditsum__sum'], report_total['margin__sum'],
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


@csrf_exempt
def generatedefaultentries(request):
    if request.method == 'POST':
        data_table = validatetable(request.POST['table'])

        debit_entries = Apdetailtemp.objects.filter(secretkey=request.POST['secretkey'], balancecode='D',
                                                    debitamount__gt=0.00).order_by('item_counter')
        # debit_entries.filter(isautogenerated=1).delete()
        taxable_amount = 0.00
        aptrade_amount = 0.00
        vat_amount = 0.00
        wtax_amount = 0.00

        if debit_entries:
            Apdetailtemp.objects.filter(secretkey=request.POST['secretkey'], balancecode='C',
                                        creditamount__gt=0.00).exclude(apdetail=None).update(isdeleted=2)
            Apdetailtemp.objects.filter(secretkey=request.POST['secretkey'], balancecode='D',
                                        debitamount__gt=0.00, chartofaccount=Companyparameter.objects.get(code='PDI').
                                        coa_inputvat_id).exclude(apdetail=None).update(isdeleted=2)
            Apdetailtemp.objects.filter(secretkey=request.POST['secretkey'], balancecode='C', apdetail=None,
                                        creditamount__gt=0.00).delete()
            Apdetailtemp.objects.filter(secretkey=request.POST['secretkey'], balancecode='D', apdetail=None,
                                        debitamount__gt=0.00, chartofaccount=Companyparameter.objects.get(code='PDI').
                                        coa_inputvat_id).delete()

            itemcounter = debit_entries.last().item_counter + 1
            ap_totals = debit_entries.aggregate(Sum('debitamount'))
            taxable_amount = ap_totals['debitamount__sum']
            aptrade_amount = ap_totals['debitamount__sum']
            vat_amount = float(taxable_amount) * (float(Vat.objects.get(pk=int(request.POST['vat'])).rate) / 100)

            # input VAT accounting entry
            if Vat.objects.filter(pk=int(request.POST['vat'])).first().rate > 0:
                inputvatentry = Apdetailtemp()
                inputvatentry.item_counter = itemcounter
                inputvatentry.secretkey = request.POST['secretkey']
                inputvatentry.ap_num = ''
                inputvatentry.ap_date = datetime.date.today()
                inputvatentry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat_id
                inputvatentry.supplier = int(request.POST['supplier'])
                inputvatentry.inputvat = Inputvat.objects.filter(inputvattype=Inputvattype.objects.
                                                                 get(pk=int(request.POST['inputvattype']))).first().id
                inputvatentry.vat = int(request.POST['vat'])
                inputvatentry.debitamount = vat_amount
                inputvatentry.balancecode = 'D'
                inputvatentry.enterby = request.user
                inputvatentry.modifyby = request.user
                inputvatentry.isautogenerated = 1
                inputvatentry.save()
                itemcounter += 1
                aptrade_amount += Decimal.from_float(inputvatentry.debitamount)

            # expanded withholding tax accounting entry
            if request.POST['atc'] and Ataxcode.objects.filter(pk=int(request.POST['atc'])).first().rate > 0:
                ewtaxentry = Apdetailtemp()
                ewtaxentry.item_counter = itemcounter
                ewtaxentry.secretkey = request.POST['secretkey']
                ewtaxentry.ap_num = ''
                ewtaxentry.ap_date = datetime.date.today()
                ewtaxentry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_ewtax_id
                print ewtaxentry.chartofaccount
                ewtaxentry.ataxcode = int(request.POST['atc'])
                wtax_amount = float(taxable_amount) * (float(Ataxcode.objects.get(pk=int(request.POST['atc']))
                                                             .rate) / 100)
                ewtaxentry.creditamount = wtax_amount
                ewtaxentry.balancecode = 'C'
                ewtaxentry.enterby = request.user
                ewtaxentry.modifyby = request.user
                ewtaxentry.isautogenerated = 1
                ewtaxentry.save()
                itemcounter += 1
                aptrade_amount -= Decimal.from_float(ewtaxentry.creditamount)

            # AP trade amount
            aptradeentry = Apdetailtemp()
            aptradeentry.item_counter = itemcounter
            aptradeentry.secretkey = request.POST['secretkey']
            aptradeentry.ap_num = ''
            aptradeentry.ap_date = datetime.date.today()
            aptradeentry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_aptrade_id
            aptradeentry.supplier = int(request.POST['supplier'])
            aptradeentry.creditamount = aptrade_amount
            aptradeentry.balancecode = 'C'
            aptradeentry.enterby = request.user
            aptradeentry.modifyby = request.user
            aptradeentry.isautogenerated = 1
            aptradeentry.save()

            vatablesale = 0.00
            vatexemptsale = 0.00
            vatzeroratedsale = 0.00

            if Vat.objects.get(pk=int(request.POST['vat'])).rate > 0:
                vatablesale = taxable_amount
            elif Vat.objects.get(pk=int(request.POST['vat'])).code == 'VE':
                vatexemptsale = taxable_amount
            elif Vat.objects.get(pk=int(request.POST['vat'])).code == 'ZE' or Vat.objects.get(pk=int(request.POST['vat'])).code == 'VATNA':
                vatzeroratedsale = taxable_amount

            context = {
                'tabledetailtemp': data_table['str_detailtemp'],
                'tablebreakdowntemp': data_table['str_detailbreakdowntemp'],
                'datatemp': querystmtdetail(data_table['str_detailtemp'], request.POST['secretkey']),
                'datatemptotal': querytotaldetail(data_table['str_detailtemp'], request.POST['secretkey']),
            }

            data = {
                'datatable': render_to_string('acctentry/datatable.html', context),
                'vatablesale': str(format(vatablesale, '.2f')),
                'vatexemptsale': str(format(vatexemptsale, '.2f')),
                'vatzeroratedsale': str(format(vatzeroratedsale, '.2f')),
                'totalsale': str(format(taxable_amount, '.2f')),
                'addvat': str(format(vat_amount, '.2f')),
                'totalpayment': str(format(aptrade_amount, '.2f')),
                'wtaxamount': str(format(wtax_amount, '.2f')),
                'status': 'success'
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

