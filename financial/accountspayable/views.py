import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from supplier.models import Supplier
from branch.models import Branch
from bankbranchdisburse.models import Bankbranchdisburse
from vat.models import Vat
from ataxcode.models import Ataxcode
from inputvattype.models import Inputvattype
from companyparameter.models import Companyparameter
from creditterm.models import Creditterm
from currency.models import Currency
from apsubtype.models import Apsubtype
from aptype.models import Aptype
from operationalfund.models import Ofmain, Ofitem, Ofdetail
from replenish_rfv.models import Reprfvmain, Reprfvdetail
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from . models import Apmain, Apdetail, Apdetailtemp, Apdetailbreakdown, Apdetailbreakdowntemp
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail
from django.template.loader import render_to_string
from annoying.functions import get_object_or_None
from endless_pagination.views import AjaxListView
from django.db.models import Q, Sum

# pdf
from django.conf import settings
from easy_pdf.views import PDFTemplateView


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    download_filename = 'my_pdf.pdf'
    template_name = 'accountspayable/create2.html'
    # base_url = 'file://' + settings.STATIC_ROOT

    def get_context_data(self, **kwargs):
        return super(Pdf, self).get_context_data(
            pagesize='A4',
            title='Hi there!',
            **kwargs
        )


@method_decorator(login_required, name='dispatch')
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
                                 Q(vatcode__icontains=keysearch) |
                                 Q(ataxcode__icontains=keysearch) |
                                 Q(bankbranchdisbursebranch__icontains=keysearch) |
                                 Q(refno__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch))
        return query

    # def render_to_response(self, context, **response_kwargs):
    #     response = super(IndexView, self).render_to_response(context, **response_kwargs)
    #     response.set_cookie('keysearch_' + self.request.resolver_match.app_name, 'qwe')
    #     print self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name)
    #     return response

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        #lookup
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

        #lookup
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankbranchdisburse'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('branch')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('code')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('daysdue')
        context['pk'] = 0

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Apmain
    template_name = 'accountspayable/create.html'
    fields = ['apdate', 'aptype', 'apsubtype', 'payee', 'branch',
              'bankbranchdisburse', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars',
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
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, apmain=None).order_by('enterdate')

        #lookup
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
        ataxobject = Ataxcode.objects.get(pk=self.request.POST['atax'], isdeleted=0)
        payeeobject = Supplier.objects.get(pk=self.request.POST['payee'], isdeleted=0)
        bankbranchdisburseobject = Bankbranchdisburse.objects.get(pk=self.request.POST['bankbranchdisburse'], isdeleted=0)

        self.object.apnum = apnum
        self.object.apstatus = 'F'
        self.object.vatcode = vatobject.code
        self.object.vatrate = vatobject.rate
        self.object.ataxcode = ataxobject.code
        self.object.ataxrate = ataxobject.rate
        self.object.payeecode = payeeobject.code
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

        return HttpResponseRedirect('/accountspayable/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Apmain
    template_name = 'accountspayable/edit.html'
    fields = ['apdate', 'aptype', 'apsubtype', 'payee', 'branch',
              'bankbranchdisburse', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars',
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
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['originalapstatus'] = Apmain.objects.get(pk=self.object.id).apstatus
        context['actualapprover'] = None if Apmain.objects.get(
            pk=self.object.id).actualapprover is None else Apmain.objects.get(pk=self.object.id).actualapprover.id
        context['savedapsubtype'] = Apmain.objects.get(pk=self.object.id).apsubtype.code
        context['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, apmain=self.object.id).order_by('enterdate')
        ap_main_aggregate = Reprfvmain.objects.filter(isdeleted=0, apmain=self.object.id).aggregate(Sum('amount'))
        context['reprfv_total_amount'] = ap_main_aggregate['amount__sum']

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

        return context

    def form_valid(self, form):
        if self.request.POST['originalapstatus'] != 'R':
            self.object = form.save(commit=False)
            self.object.payee = Supplier.objects.get(pk=self.request.POST['payee'])
            self.object.payeecode = self.object.payee.code
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['apdate', 'aptype', 'apsubtype', 'payee', 'payeecode', 'branch',
                                            'bankbranchdisburse', 'vat', 'atax',
                                            'inputvattype', 'creditterm', 'duedate',
                                            'refno', 'deferred', 'particulars',
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


def comments():
    print 123
    # copy po format for vat field
    # clear cache based on condition
    # cache api
