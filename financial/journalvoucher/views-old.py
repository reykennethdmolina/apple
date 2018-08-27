import datetime
from django.db.models import Sum
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from jvtype.models import Jvtype
from jvsubtype.models import Jvsubtype
from companyparameter.models import Companyparameter
from currency.models import Currency
from branch.models import Branch
from department.models import Department
from operationalfund.models import Ofmain, Ofdetail, Ofitem
from . models import Jvmain, Jvdetail, Jvdetailtemp, Jvdetailbreakdown, Jvdetailbreakdowntemp
from acctentry.views import updateallquery, validatetable, deleteallquery, generatekey, querystmtdetail, \
    querytotaldetail, savedetail, updatedetail
from endless_pagination.views import AjaxListView
from django.db.models import Q
from easy_pdf.views import PDFTemplateView
from django.contrib.auth.models import User
from utils.mixins import ReportContentMixin
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
from dateutil.relativedelta import relativedelta
import datetime
from django.utils.dateformat import DateFormat


class IndexView(AjaxListView):
    model = Jvmain
    template_name = 'journalvoucher/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'journalvoucher/index_list.html'

    def get_queryset(self):
        query = Jvmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(jvnum__icontains=keysearch) |
                                 Q(jvdate__icontains=keysearch) |
                                 Q(jvtype__description__icontains=keysearch) |
                                 Q(department__departmentname__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        #lookup
        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('description')
        context['jvsubtype'] = Jvsubtype.objects.filter(isdeleted=0).order_by('description')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('description')
        context['pk'] = 0

        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Jvmain
    template_name = 'journalvoucher/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['detail'] = Jvdetail.objects.filter(isdeleted=0).\
            filter(jvmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Jvdetail.objects.filter(isdeleted=0).\
            filter(jvmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Jvdetail.objects.filter(isdeleted=0).\
            filter(jvmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))
        context['ofcsvmain'] = Ofmain.objects.filter(isdeleted=0, jvmain=self.object.id).order_by('enterdate')
        jv_main_aggregate = Ofmain.objects.filter(isdeleted=0, jvmain=self.object.id).aggregate(Sum('amount'))
        context['repcsv_total_amount'] = jv_main_aggregate['amount__sum']

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Jvmain
    template_name = 'journalvoucher/create.html'
    fields = ['jvdate', 'jvtype', 'jvsubtype', 'refnum', 'particular', 'branch', 'currency', 'department',
              'designatedapprover', 'fxrate']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['department'] = Department.objects.filter(isdeleted=0).exclude(pk=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('pk')
        context['jvsubtype'] = Jvsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['ofcsvmain'] = Ofmain.objects.filter(isdeleted=0, oftype__code='CSV', jvmain=None, ofstatus='O')\
            .order_by('id')   # on-hand CSVs that do not have JVs yet

        #lookup
        context['pk'] = 0

        closetransaction = Companyparameter.objects.all().first().last_closed_date
        validtransaction = closetransaction + relativedelta(months=1)
        context['validtransaction'] = validtransaction

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # Get JVYear
        jvyear = form.cleaned_data['jvdate'].year
        num = len(Jvmain.objects.all().filter(jvdate__year=jvyear)) + 1
        padnum = '{:06d}'.format(num)

        self.object.jvnum = str(jvyear)+str(padnum)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()

        # accounting entry starts here..
        source = 'jvdetailtemp'
        mainid = self.object.id
        num = self.object.jvnum
        secretkey = self.request.POST['secretkey']
        savedetail(source, mainid, num, secretkey, self.request.user)

        # save jvmain in ofmain
        for i in range(len(self.request.POST.getlist('csv_checkbox'))):
            ofmain = Ofmain.objects.get(pk=int(self.request.POST.getlist('csv_checkbox')[i]))
            ofmain.jvmain = self.object
            ofmain.ofstatus = 'P'
            ofmain.save()
        # save jvmain in ofmain

        totaldebitamount = Jvdetail.objects.filter(isdeleted=0).filter(jvmain_id=self.object.id).aggregate(
            Sum('debitamount'))
        totalcreditamount = Jvdetail.objects.filter(isdeleted=0).filter(jvmain_id=self.object.id).aggregate(
            Sum('creditamount'))

        if totaldebitamount['debitamount__sum'] == totalcreditamount['creditamount__sum']:
            self.object.amount = totaldebitamount['debitamount__sum']
            self.object.save(update_fields=['amount'])
        else:
            print "Debit and Credit amounts are not equal. JV Amount is not saved."

        return HttpResponseRedirect('/journalvoucher/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Jvmain
    template_name = 'journalvoucher/edit.html'
    fields = ['jvdate', 'jvtype', 'jvsubtype', 'refnum', 'particular', 'branch', 'currency', 'department',
              'designatedapprover', 'jvstatus', 'fxrate']

    def get_initial(self):
        self.mysecretkey = generatekey(self)

        detailinfo = Jvdetail.objects.filter(jvmain=self.object.pk).order_by('item_counter')

        for drow in detailinfo:
            detail = Jvdetailtemp()
            detail.secretkey = self.mysecretkey
            detail.jv_num = drow.jv_num
            detail.jvmain = drow.jvmain_id
            detail.jvdetail = drow.pk
            detail.item_counter = drow.item_counter
            detail.jv_date = drow.jv_date
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

            breakinfo = Jvdetailbreakdown.objects.\
                filter(jvdetail_id=drow.id).order_by('pk', 'datatype')
            if breakinfo:
                for brow in breakinfo:
                    breakdown = Jvdetailbreakdowntemp()
                    breakdown.jv_num = drow.jv_num
                    breakdown.secretkey = self.mysecretkey
                    breakdown.jvmain = drow.jvmain_id
                    breakdown.jvdetail = drow.pk
                    breakdown.jvdetailtemp = detailtempid
                    breakdown.jvdetailbreakdown = brow.pk
                    breakdown.item_counter = brow.item_counter
                    breakdown.jv_date = brow.jv_date
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

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['self'] = Jvmain.objects.get(pk=self.object.pk)
        context['department'] = Department.objects.filter(isdeleted=0).order_by('pk')
        context['secretkey'] = self.mysecretkey
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('pk')
        context['jvsubtype'] = Jvsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['jvnum'] = self.object.jvnum
        context['originaljvstatus'] = Jvmain.objects.get(pk=self.object.id).jvstatus
        context['savedjvsubtype'] = Jvmain.objects.get(pk=self.object.id).jvsubtype.code
        context['ofcsvmain'] = Ofmain.objects.filter(isdeleted=0, jvmain=self.object.id).order_by('enterdate')
        jv_main_aggregate = Ofmain.objects.filter(isdeleted=0, jvmain=self.object.id).aggregate(Sum('amount'))
        context['repcsv_total_amount'] = jv_main_aggregate['amount__sum']
        context['originaljvstatus'] = Jvmain.objects.get(pk=self.object.id).jvstatus

        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'jvdetailtemp',
            'tablebreakdowntemp': 'jvdetailbreakdowntemp',

            'datatemp': querystmtdetail('jvdetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('jvdetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)

        #lookup
        # context['pk'] = 0
        context['pk'] = self.object.pk
        context['datainfo'] = self.object
        return context

    def form_valid(self, form):
        if self.request.POST['originaljvstatus'] != 'R':
            self.object = form.save(commit=False)
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['jvdate', 'jvtype', 'jvsubtype', 'refnum', 'particular', 'branch',
                                            'currency', 'department', 'designatedapprover', 'jvstatus', 'fxrate'])

            if self.object.jvstatus == 'F':
                self.object.designatedapprover = User.objects.get(pk=self.request.POST['designatedapprover'])
                self.object.save(update_fields=['designatedapprover'])

            # revert status from APPROVED/DISAPPROVED to For Approval if no response date or approver response is saved
            # remove approval details if JVSTATUS is not APPROVED/DISAPPROVED
            if self.object.jvstatus == 'A' or self.object.jvstatus == 'D':
                if self.object.responsedate is None or self.object.approverresponse is None or self.object. \
                        actualapprover is None:
                    print self.object.responsedate
                    print self.object.approverresponse
                    print self.object.actualapprover
                    self.object.responsedate = None
                    self.object.approverremarks = None
                    self.object.approverresponse = None
                    self.object.actualapprover = None
                    self.object.jvstatus = 'F'
                    self.object.save(update_fields=['responsedate', 'approverremarks', 'approverresponse',
                                                    'actualapprover', 'jvstatus'])
            elif self.object.jvstatus == 'F':
                self.object.responsedate = None
                self.object.approverremarks = None
                self.object.approverresponse = None
                self.object.actualapprover = None
                self.object.save(update_fields=['responsedate', 'approverremarks', 'approverresponse',
                                                'actualapprover'])

            # revert status from RELEASED to Approved if no release date is saved
            # remove release details if JVSTATUS is not RELEASED
            if self.object.jvstatus == 'R' and self.object.releasedate is None:
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.jvstatus = 'A'
                self.object.save(update_fields=['releaseby', 'releasedate', 'jvstatus'])
            elif self.object.jvstatus != 'R':
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.save(update_fields=['releaseby', 'releasedate'])

            # accounting entry starts here..
            source = 'jvdetailtemp'
            mainid = self.object.id
            num = self.object.jvnum
            secretkey = self.request.POST['secretkey']
            updatedetail(source, mainid, num, secretkey, self.request.user)

            totaldebitamount = Jvdetail.objects.filter(isdeleted=0).filter(jvmain_id=self.object.id).aggregate(
                Sum('debitamount'))
            totalcreditamount = Jvdetail.objects.filter(isdeleted=0).filter(jvmain_id=self.object.id).aggregate(
                Sum('creditamount'))

            if totaldebitamount['debitamount__sum'] == totalcreditamount['creditamount__sum']:
                self.object.amount = totaldebitamount['debitamount__sum']
                self.object.save(update_fields=['amount'])
            else:
                print "Debit and Credit amounts are not equal. JV Amount is not saved."

        else:
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['modifyby', 'modifydate', 'remarks'])

        return HttpResponseRedirect('/journalvoucher/'+str(self.object.pk)+'/update')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Jvmain
    template_name = 'journalvoucher/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('journalvoucher.delete_jvmain') or self.object.status == 'O' \
                or self.object.jvstatus == 'A' or self.object.jvstatus == 'I' or self.object.jvstatus == 'R':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.jvstatus = 'D'
        self.object.save()

        # remove reference in ofmain
        ofmain = Ofmain.objects.filter(jvmain=self.object.id)
        for data in ofmain:
            data.jvmain = None
            data.save()
        # remove reference in ofmain

        return HttpResponseRedirect('/journalvoucher')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Jvmain
    template_name = 'journalvoucher/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['jvmain'] = Jvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['detail'] = Jvdetail.objects.filter(isdeleted=0). \
            filter(jvmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Jvdetail.objects.filter(isdeleted=0). \
            filter(jvmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Jvdetail.objects.filter(isdeleted=0). \
            filter(jvmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['ofmain'] = Ofmain.objects.filter(isdeleted=0, jvmain=self.kwargs['pk']).order_by(
            'enterdate')
        jv_main_aggregate = Ofmain.objects.filter(isdeleted=0, jvmain=self.kwargs['pk']).aggregate(
            Sum('amount'))
        context['ofcsvmain_total_amount'] = jv_main_aggregate['amount__sum']

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedjv = Jvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        printedjv.print_ctr += 1
        printedjv.save()
        return context


@csrf_exempt
def importrepcsv(request):
    if request.method == 'POST':
        first_ofmain = Ofmain.objects.filter(id=request.POST.getlist('checked_repcsvmain[]')[0],
                                             isdeleted=0,
                                             status='A').first()

        ofdetail = Ofdetail.objects.filter(
            ofmain__in=set(request.POST.getlist('checked_repcsvmain[]'))). \
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

        if 'jvnum' in request.POST:
            if request.POST['jvnum']:
                updateallquery(request.POST['table'], request.POST['jvnum'])
        # set isdeleted=2 for existing detailtemp data

        i = 1
        for detail in ofdetail:
            jvdetailtemp = Jvdetailtemp()
            jvdetailtemp.item_counter = i
            jvdetailtemp.secretkey = request.POST['secretkey']
            jvdetailtemp.jv_date = datetime.datetime.now()
            jvdetailtemp.chartofaccount = detail['chartofaccount__id']
            jvdetailtemp.bankaccount = detail['bankaccount__id']
            jvdetailtemp.department = detail['department__id']
            jvdetailtemp.employee = detail['employee__id']
            jvdetailtemp.supplier = detail['supplier__id']
            jvdetailtemp.customer = detail['customer__id']
            jvdetailtemp.unit = detail['unit__id']
            jvdetailtemp.branch = detail['branch__id']
            jvdetailtemp.product = detail['product__id']
            jvdetailtemp.inputvat = detail['inputvat__id']
            jvdetailtemp.outputvat = detail['outputvat__id']
            jvdetailtemp.vat = detail['vat__id']
            jvdetailtemp.wtax = detail['wtax__id']
            jvdetailtemp.ataxcode = detail['ataxcode__id']
            jvdetailtemp.debitamount = detail['debitamount__sum']
            jvdetailtemp.creditamount = detail['creditamount__sum']
            jvdetailtemp.balancecode = detail['balancecode']
            jvdetailtemp.enterby = request.user
            jvdetailtemp.modifyby = request.user
            jvdetailtemp.save()
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
            'branch': first_ofmain.branch_id
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def approve(request):
    if request.method == 'POST':
        jv_for_approval = Jvmain.objects.get(jvnum=request.POST['jvnum'])
        if request.user.has_perm('journalvoucher.approve_alljv') or \
                request.user.has_perm('journalvoucher.approve_assignedjv'):
            if request.user.has_perm('journalvoucher.approve_alljv') or \
                    (request.user.has_perm('journalvoucher.approve_assignedjv') and
                             jv_for_approval.designatedapprover == request.user):
                print "back to in-process = " + str(request.POST['backtoinprocess'])
                if request.POST['originaljvstatus'] != 'R' or int(request.POST['backtoinprocess']) == 1:
                    jv_for_approval.jvstatus = request.POST['approverresponse']
                    jv_for_approval.isdeleted = 0
                    if request.POST['approverresponse'] == 'D':
                        jv_for_approval.status = 'C'
                    else:
                        jv_for_approval.status = 'A'
                    jv_for_approval.approverresponse = request.POST['approverresponse']
                    jv_for_approval.responsedate = request.POST['responsedate']
                    jv_for_approval.actualapprover = User.objects.get(pk=request.user.id)
                    jv_for_approval.approverremarks = request.POST['approverremarks']
                    jv_for_approval.releaseby = None
                    jv_for_approval.releasedate = None
                    jv_for_approval.save()
                    data = {
                        'status': 'success',
                        'jvnum': jv_for_approval.jvnum,
                        'newjvstatus': jv_for_approval.jvstatus,
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
        jv_for_release = Jvmain.objects.get(jvnum=request.POST['jvnum'])
        if jv_for_release.jvstatus != 'F' and jv_for_release.jvstatus != 'D':
            jv_for_release.releaseby = User.objects.get(pk=request.POST['releaseby'])
            jv_for_release.releasedate = request.POST['releasedate']
            jv_for_release.jvstatus = 'R'
            jv_for_release.save()
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


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Jvmain
    template_name = 'journalvoucher/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('description')
        context['jvsubtype'] = Jvsubtype.objects.filter(isdeleted=0).order_by('description')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['user'] = User.objects.filter(is_active=1).order_by('first_name')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        context['unit'] = Unit.objects.filter(isdeleted=0).order_by('code')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('code')
        context['outputvat'] = Outputvat.objects.filter(isdeleted=0).order_by('code')
        context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultHtmlView(ListView):
    model = Jvmain
    template_name = 'journalvoucher/reportresulthtml.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['csv'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "JOURNAL VOUCHER"
        context['rc_title'] = "JOURNAL VOUCHER"

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Jvmain
    template_name = 'journalvoucher/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['csv'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "JOURNAL VOUCHER"
        context['rc_title'] = "JOURNAL VOUCHER"

        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_total = ''
    report_xls = ''

    csv = 'hide'

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's'\
       or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':

        if request.COOKIES.get('rep_f_jvsubtype_' + request.resolver_match.app_name):
            subtype = str(request.COOKIES.get('rep_f_jvsubtype_' + request.resolver_match.app_name))
        else:
            subtype = ''

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's'\
                or (request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd'
                    and (subtype == '' or subtype == '2')):
            if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
                report_type = "Journal Voucher Detailed"
                report_xls = "JV Detailed"
            else:
                report_type = "Journal Voucher Summary"
                report_xls = "JV Summary"

            query = Jvmain.objects.all().filter(isdeleted=0)

            if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
                query = query.filter(jvnum__gte=int(key_data))
            if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
                query = query.filter(jvnum__lte=int(key_data))

            if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
                query = query.filter(jvdate__gte=key_data)
            if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
                query = query.filter(jvdate__lte=key_data)

            if request.COOKIES.get('rep_f_jvtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_jvtype_' + request.resolver_match.app_name))
                query = query.filter(jvtype=int(key_data))
            if request.COOKIES.get('rep_f_jvsubtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_jvsubtype_' + request.resolver_match.app_name))
                query = query.filter(jvsubtype=int(key_data))
            if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
                query = query.filter(branch=int(key_data))
            if request.COOKIES.get('rep_f_jvstatus_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_jvstatus_' + request.resolver_match.app_name))
                query = query.filter(jvstatus=str(key_data))
            if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
                if key_data == 'P':
                    query = query.filter(postby__isnull=False)
                elif key_data == 'U':
                    query = query.filter(postby__isnull=True)
            if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
                query = query.filter(status=str(key_data))

            if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
                query = query.filter(department=int(key_data))
            if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
                query = query.filter(Q(actualapprover=int(key_data)), Q(designatedapprover=int(key_data)))

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
            report_type = "Journal Voucher Detailed"
            report_xls = "JV Detailed"
            csv = "show"

            query = Ofmain.objects.all().filter(isdeleted=0).exclude(jvmain=None)

            if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
                query = query.filter(jvmain__jvnum__gte=int(key_data))
            if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
                query = query.filter(jvmain__jvnum__lte=int(key_data))

            if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
                query = query.filter(jvmain__jvdate__gte=key_data)
            if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
                query = query.filter(jvmain__jvdate__lte=key_data)

            if request.COOKIES.get('rep_f_jvtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_jvtype_' + request.resolver_match.app_name))
                query = query.filter(jvmain__jvtype=int(key_data))
            if request.COOKIES.get('rep_f_jvsubtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_jvsubtype_' + request.resolver_match.app_name))
                query = query.filter(jvmain__jvsubtype=int(key_data))
            if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
                query = query.filter(jvmain__branch=int(key_data))
            if request.COOKIES.get('rep_f_jvstatus_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_jvstatus_' + request.resolver_match.app_name))
                query = query.filter(jvmain__jvstatus=str(key_data))
            if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
                if key_data == 'P':
                    query = query.filter(jvmain__postby__isnull=False)
                elif key_data == 'U':
                    query = query.filter(jvmain__postby__isnull=True)
            if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
                query = query.filter(jvmain__status=str(key_data))
            if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
                query = query.filter(jvmain__department=int(key_data))
            if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
                query = query.filter(Q(jvmain__actualapprover=int(key_data)), Q(jvmain__designatedapprover=int(key_data)))

            if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(jvmain__amount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
                query = query.filter(jvmain__amount__lte=float(key_data.replace(',', '')))

            if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    for n,data in enumerate(key_data):
                        key_data[n] = "jvmain__" + data
                    query = query.order_by(*key_data)
                else:
                    query = query.order_by('jvmain')

            report_total = query.values('jvmain').annotate(Sum('amount')).aggregate(Sum('jvmain__amount'))

        if request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name))
            if key_data == 'd':
                query = query.reverse()

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get(
                    'rep_f_report_' + request.resolver_match.app_name) == 'ae':
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
            report_type = "Journal Voucher Unbalanced Entries"
            report_xls = "JV Unbalanced Entries"
        else:
            report_type = "Journal Voucher All Entries"
            report_xls = "JV All Entries"

        query = Jvdetail.objects.filter(isdeleted=0, jvmain__isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvdate__lte=key_data)

        if request.COOKIES.get('rep_f_jvtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_jvtype_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvtype=int(key_data))
        if request.COOKIES.get('rep_f_jvsubtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_jvsubtype_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvsubtype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(jvmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_jvstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_jvstatus_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvstatus=str(key_data))
        if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
            if key_data == 'P':
                query = query.filter(jvmain__postby__isnull=False)
            elif key_data == 'U':
                query = query.filter(jvmain__postby__isnull=True)
        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            query = query.filter(jvmain__status=str(key_data))

        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(jvmain__department=int(key_data))
        if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
            query = query.filter(Q(jvmain__actualapprover=int(key_data)), Q(jvmain__designatedapprover=int(key_data)))

        if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(jvmain__amount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
            query = query.filter(jvmain__amount__lte=float(key_data.replace(',', '')))

        query = query.values('jvmain__jvnum') \
            .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),
                      creditsum=Sum('creditamount')) \
            .values('jvmain__jvnum', 'margin', 'jvmain__jvdate', 'debitsum', 'creditsum', 'jvmain__pk').order_by(
            'jvmain__jvnum')

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
        query = Jvdetail.objects.all().filter(isdeleted=0)

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
            query = query.filter(jvmain__jvnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvdate__lte=key_data)

        if request.COOKIES.get('rep_f_jvtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_jvtype_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvtype=int(key_data))
        if request.COOKIES.get('rep_f_jvsubtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_jvsubtype_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvsubtype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(jvmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_jvstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_jvstatus_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvstatus=str(key_data))
        if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
            if key_data == 'P':
                query = query.filter(jvmain__postby__isnull=False)
            elif key_data == 'U':
                query = query.filter(jvmain__postby__isnull=True)
        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            query = query.filter(jvmain__status=str(key_data))

        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(jvmain__department=int(key_data))
        if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
            query = query.filter(Q(jvmain__actualapprover=int(key_data)), Q(designatedapprover=int(key_data)))

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "Journal Voucher Accounting Entry - Summary"
            report_xls = "JV Acctg Entry - Summary"

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
            report_type = "Journal Voucher Accounting Entry - Detailed"
            report_xls = "JV Acctg Entry - Detailed"

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
                                                                                     'jv_num')

    return query, report_type, report_total, csv, report_xls


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
    queryset, report_type, report_total, csv, report_xls = reportresultquery(request)
    report_type = report_type if report_type != '' else 'JV Report'
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
        amount_placement = 9 if csv == 'show' else 7
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        amount_placement = 2
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 4
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        amount_placement = 15

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'JV Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Type', bold)
        worksheet.write('D1', 'Subtype', bold)
        worksheet.write('E1', 'Status', bold)
        worksheet.write('F1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if csv == 'show':
            worksheet.merge_range('A1:A2', 'JV Number', bold)
            worksheet.merge_range('B1:B2', 'Date', bold)
            worksheet.merge_range('C1:C2', 'Type', bold)
            worksheet.merge_range('D1:D2', 'Subtype', bold)
            worksheet.merge_range('E1:E2', 'Branch', bold)
            worksheet.merge_range('F1:F2', 'Department.', bold)
            worksheet.merge_range('G1:G2', 'Status', bold)
            worksheet.merge_range('H1:J1', 'Operational Fund', bold_center)
            worksheet.merge_range('K1:K2', 'Amount', bold_right)
            worksheet.write('H2', 'OF Number', bold)
            worksheet.write('I2', 'Date', bold)
            worksheet.write('J2', 'OF Amount', bold_right)
            row += 1
        else:
            worksheet.write('A1', 'JV Number', bold)
            worksheet.write('B1', 'Date', bold)
            worksheet.write('C1', 'Type', bold)
            worksheet.write('D1', 'Subtype', bold)
            worksheet.write('E1', 'Branch', bold)
            worksheet.write('F1', 'Department', bold)
            worksheet.write('G1', 'Status', bold)
            worksheet.write('H1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        worksheet.write('A1', 'JV Number', bold)
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
        worksheet.merge_range('B1:N1', 'Details', bold_center)
        worksheet.merge_range('O1:O2', 'Date', bold)
        worksheet.merge_range('P1:P2', 'Debit', bold_right)
        worksheet.merge_range('Q1:Q2', 'Credit', bold_right)
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

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            data = [
                obj.jvnum,
                DateFormat(obj.jvdate).format('Y-m-d'),
                obj.jvtype.description if obj.jvtype else '',
                obj.jvsubtype.description if obj.jvsubtype else '',
                obj.get_jvstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            if csv == 'show':
                data = [
                    obj.jvmain.jvnum,
                    DateFormat(obj.jvmain.jvdate).format('Y-m-d'),
                    obj.jvmain.jvtype.description if obj.jvmain.jvtype else '',
                    obj.jvmain.jvsubtype.description if obj.jvmain.jvsubtype else '',
                    obj.jvmain.branch.description,
                    obj.jvmain.department.departmentname,
                    obj.jvmain.get_jvstatus_display(),
                    'OF-' + obj.ofnum,
                    DateFormat(obj.ofdate).format('Y-m-d'),
                    obj.amount,
                    obj.jvmain.amount,
                ]
            else:
                str_department = obj.department.departmentname if obj.department else ''
                data = [
                    obj.jvnum,
                    DateFormat(obj.jvdate).format('Y-m-d'),
                    obj.jvtype.description if obj.jvtype else '',
                    obj.jvsubtype.description if obj.jvsubtype else '',
                    obj.branch.description,
                    str_department,
                    obj.get_jvstatus_display(),
                    obj.amount,
                ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
            data = [
                obj['jvmain__jvnum'],
                DateFormat(obj['jvmain__jvdate']).format('Y-m-d'),
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

            data = [
                obj.chartofaccount.accountcode + " - " + obj.chartofaccount.description,
                obj.bankaccount.accountnumber if obj.bankaccount is not None else '',
                obj.department.departmentname if obj.department is not None else '',
                str_firstname + " " + str_lastname,
                obj.supplier.name if obj.supplier is not None else '',
                obj.customer.name if obj.customer is not None else '',
                obj.unit.description if obj.unit is not None else '',
                obj.branch.description if obj.branch is not None else '',
                obj.product.description if obj.product is not None else '',
                obj.inputvat.description if obj.inputvat is not None else '',
                obj.outputvat.description if obj.outputvat is not None else '',
                obj.vat.description if obj.vat is not None else '',
                obj.wtax.description if obj.wtax is not None else '',
                obj.ataxcode.code if obj.ataxcode is not None else '',
                DateFormat(obj.jv_date).format('Y-m-d'),
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
        if csv == 'show':
            data = [
                "", "", "", "", "", "", "", "", "",
                "Total", report_total['jvmain__amount__sum'],
            ]
        else:
            data = [
                "", "", "", "", "", "",
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
