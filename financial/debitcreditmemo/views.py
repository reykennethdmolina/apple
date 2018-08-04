from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail
from django.template.loader import render_to_string
from ataxcode.models import Ataxcode
from bankaccount.models import Bankaccount
from branch.models import Branch
from companyparameter.models import Companyparameter
from creditterm.models import Creditterm
from currency.models import Currency
from customer.models import Customer
from dcclasstype.models import Dcclasstype
from debitcreditmemosubtype.models import Debitcreditmemosubtype
from department.models import Department
from employee.models import Employee
from inventoryitem.models import Inventoryitem
from outputvattype.models import Outputvattype
from supplier.models import Supplier
from vat.models import Vat
from . models import Dcmain, Dcdetail, Dcdetailbreakdown, Dcdetailtemp, Dcdetailbreakdowntemp
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.http import JsonResponse
from easy_pdf.views import PDFTemplateView
from endless_pagination.views import AjaxListView
from dateutil.relativedelta import relativedelta
import datetime

from utils.mixins import ReportContentMixin
from django.utils.dateformat import DateFormat


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Dcmain
    template_name = 'debitcreditmemo/index.html'
    page_template = 'debitcreditmemo/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Dcmain.objects.all().filter(isdeleted=0)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(dcnum__icontains=keysearch) |
                                 Q(dcdate__icontains=keysearch) |
                                 Q(customer_name__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        # data for lookup
        context['dcclasstype'] = Dcclasstype.objects.filter(isdeleted=0).order_by('code')
        context['dcsubtype'] = Debitcreditmemosubtype.objects.filter(isdeleted=0).exclude(dcclasstype=None).\
            order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['pk'] = 0
        # data for lookup

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Dcmain
    template_name = 'debitcreditmemo/create.html'
    fields = ['dcdate', 'dctype', 'dcclasstype', 'dcsubtype', 'particulars', 'vat', 'branch', 'outputvattype',
              'particulars', 'currency', 'fxrate', 'remarks']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('debitcreditmemo.add_dcmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['dcsubtype'] = Debitcreditmemosubtype.objects.filter(isdeleted=0).exclude(dcclasstype=None). \
            order_by('pk')
        context['dcclasstype'] = Dcclasstype.objects.filter(isdeleted=0).order_by('code')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['pk'] = 0
        context['secretkey'] = generatekey(self)
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')

        closetransaction = Companyparameter.objects.all().first().last_closed_date
        validtransaction = closetransaction + relativedelta(months=1)
        context['validtransaction'] = validtransaction

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        year = str(form.cleaned_data['dcdate'].year)
        yearqs = Dcmain.objects.filter(dcnum__startswith=year)

        if yearqs:
            dcnumlast = yearqs.latest('dcnum')
            latestdcnum = str(dcnumlast)
            print "latest: " + latestdcnum

            dcnum = year
            last = str(int(latestdcnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                dcnum += '0'
            dcnum += last

        else:
            dcnum = year + '000001'

        print 'dcnum: ' + dcnum

        self.object.dcnum = dcnum
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user

        if self.object.dcclasstype.code == 'AR' or self.object.dcclasstype.code == 'NR':
            self.object.customer = Customer.objects.filter(pk=int(self.request.POST['customer']), isdeleted=0).first()
            self.object.payee_code = self.object.customer.code
            self.object.payee_name = self.object.customer.name
        elif self.object.dcclasstype.code == 'NP':
            self.object.supplier = Supplier.objects.filter(pk=int(self.request.POST['supplier']), isdeleted=0).first()
            self.object.payee_code = self.object.supplier.code
            self.object.payee_name = self.object.supplier.name
        elif self.object.dcclasstype.code == 'AO':
            self.object.employee = Employee.objects.filter(pk=int(self.request.POST['employee']), isdeleted=0).first()
            self.object.payee_code = self.object.employee.code
            self.object.payee_name = self.object.employee.firstname + ' ' + self.object.employee.lastname
        elif self.object.dcclasstype.code == 'EX':
            self.object.department = Department.objects.filter(pk=int(self.request.POST['department']), isdeleted=0).\
                first()
            self.object.payee_code = self.object.department.code
            self.object.payee_name = self.object.department.departmentname
        elif self.object.dcclasstype.code == 'CB':
            self.object.bankaccount = Bankaccount.objects.filter(pk=int(self.request.POST['department']), isdeleted=0).\
                first()
            self.object.payee_code = self.object.bankaccount.code
            self.object.payee_name = self.object.bankaccount.accountnumber
        elif self.object.dcclasstype.code == 'IN':
            self.object.inventory = Inventoryitem.objects.filter(pk=int(self.request.POST['inventory']), isdeleted=0).\
                first()
            self.object.payee_code = self.object.inventory.code
            self.object.payee_name = self.object.inventory.description

        self.object.vatrate = self.object.vat.rate
        self.object.save()

        # accounting entry starts here..
        source = 'dcdetailtemp'
        mainid = self.object.id
        num = self.object.dcnum
        secretkey = self.request.POST['secretkey']
        savedetail(source, mainid, num, secretkey, self.request.user)

        totalamount = Dcdetail.objects.filter(isdeleted=0).filter(dcmain_id=self.object.id).\
            aggregate(Sum('debitamount'))
        self.object.amount = totalamount['debitamount__sum']
        self.object.save()

        return HttpResponseRedirect('/debitcreditmemo/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Dcmain
    template_name = 'debitcreditmemo/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['detail'] = Dcdetail.objects.filter(isdeleted=0).\
            filter(dcmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Dcdetail.objects.filter(isdeleted=0).\
            filter(dcmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Dcdetail.objects.filter(isdeleted=0).\
            filter(dcmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['dcsubtype'] = Debitcreditmemosubtype.objects.filter(isdeleted=0).order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['pk'] = self.object.pk

        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Dcmain
    template_name = 'debitcreditmemo/update.html'
    fields = ['dcdate', 'dctype', 'dcsubtype', 'particulars', 'vat', 'branch', 'outputvattype',
              'particulars', 'dcclasstype', 'currency', 'fxrate', 'remarks']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('debitcreditmemo.change_dcmain') or self.object.isdeleted == 1:
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # accounting entry starts here
    def get_initial(self):
        self.mysecretkey = generatekey(self)

        detailinfo = Dcdetail.objects.filter(dcmain=self.object.pk).order_by('item_counter')

        for drow in detailinfo:
            detail = Dcdetailtemp()
            detail.secretkey = self.mysecretkey
            detail.dc_num = drow.dc_num
            detail.dcmain = drow.dcmain_id
            detail.dcdetail = drow.pk
            detail.item_counter = drow.item_counter
            detail.dc_date = drow.dc_date
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
            detail.reftype = drow.reftype
            detail.refnum = drow.refnum
            detail.refdate = drow.refdate
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

            breakinfo = Dcdetailbreakdown.objects. \
                filter(dcdetail_id=drow.id).order_by('pk', 'datatype')
            if breakinfo:
                for brow in breakinfo:
                    breakdown = Dcdetailbreakdowntemp()
                    breakdown.dc_num = drow.dc_num
                    breakdown.secretkey = self.mysecretkey
                    breakdown.dcmain = drow.dcmain_id
                    breakdown.dcdetail = drow.pk
                    breakdown.dcdetailtemp = detailtempid
                    breakdown.dcdetailbreakdown = brow.pk
                    breakdown.item_counter = brow.item_counter
                    breakdown.dc_date = brow.dc_date
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
        context['dcsubtype'] = Debitcreditmemosubtype.objects.filter(isdeleted=0).exclude(dcclasstype=None). \
            order_by('pk')
        context['dcclasstype'] = Dcclasstype.objects.filter(isdeleted=0).order_by('code')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['pk'] = self.object.pk
        context['secretkey'] = generatekey(self)
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')

        context['dcnum'] = self.object.dcnum

        if self.request.POST.get('employee', False):
            context['employee'] = Employee.objects.get(pk=self.request.POST['employee'], isdeleted=0)
        elif self.object.employee:
            context['employee'] = Employee.objects.get(pk=self.object.employee.id, isdeleted=0)
        if self.request.POST.get('customer', False):
            context['customer'] = Customer.objects.get(pk=self.request.POST['customer'], isdeleted=0)
        elif self.object.customer:
            context['customer'] = Customer.objects.get(pk=self.object.customer.id, isdeleted=0)
        if self.request.POST.get('bankaccount', False):
            context['bankaccount'] = Bankaccount.objects.get(pk=self.request.POST['bankaccount'], isdeleted=0)
        elif self.object.bankaccount:
            context['bankaccount'] = Bankaccount.objects.get(pk=self.object.bankaccount.id, isdeleted=0)
        if self.request.POST.get('department', False):
            context['department'] = Department.objects.get(pk=self.request.POST['department'], isdeleted=0)
        elif self.object.department:
            context['department'] = Department.objects.get(pk=self.object.department.id, isdeleted=0)
        if self.request.POST.get('inventory', False):
            context['inventory'] = Inventoryitem.objects.get(pk=self.request.POST['inventory'], isdeleted=0)
        elif self.object.inventory:
            context['inventory'] = Inventoryitem.objects.get(pk=self.object.inventory.id, isdeleted=0)
        if self.request.POST.get('supplier', False):
            context['supplier'] = Supplier.objects.get(pk=self.request.POST['supplier'], isdeleted=0)
        elif self.object.supplier:
            context['supplier'] = Supplier.objects.get(pk=self.object.supplier.id, isdeleted=0)

        # accounting entry starts here
        context['secretkey'] = self.mysecretkey
        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'dcdetailtemp',
            'tablebreakdowntemp': 'dcdetailbreakdowntemp',

            'datatemp': querystmtdetail('dcdetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('dcdetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        # accounting entry ends here

        return context

    def form_valid(self, form):
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.vatrate = self.object.vat.rate

        if self.object.dcclasstype.code == 'AR' or self.object.dcclasstype.code == 'NR':
            self.object.customer = Customer.objects.filter(pk=int(self.request.POST['customer']), isdeleted=0).first()
            self.object.payee_code = self.object.customer.code
            self.object.payee_name = self.object.customer.name
            self.object.supplier = None
            self.object.employee = None
            self.object.department = None
            self.object.bankaccount = None
            self.object.inventory = None
        elif self.object.dcclasstype.code == 'NP':
            self.object.supplier = Supplier.objects.filter(pk=int(self.request.POST['supplier']), isdeleted=0).first()
            self.object.payee_code = self.object.supplier.code
            self.object.payee_name = self.object.supplier.name
            self.object.customer = None
            self.object.employee = None
            self.object.department = None
            self.object.bankaccount = None
            self.object.inventory = None
        elif self.object.dcclasstype.code == 'AO':
            self.object.employee = Employee.objects.filter(pk=int(self.request.POST['employee']), isdeleted=0).first()
            self.object.payee_code = self.object.employee.code
            self.object.payee_name = self.object.employee.firstname + ' ' + self.object.employee.lastname
            self.object.customer = None
            self.object.supplier = None
            self.object.department = None
            self.object.bankaccount = None
            self.object.inventory = None
        elif self.object.dcclasstype.code == 'EX':
            self.object.department = Department.objects.filter(pk=int(self.request.POST['department']), isdeleted=0).\
                first()
            self.object.payee_code = self.object.department.code
            self.object.payee_name = self.object.department.departmentname
            self.object.customer = None
            self.object.employee = None
            self.object.supplier = None
            self.object.bankaccount = None
            self.object.inventory = None
        elif self.object.dcclasstype.code == 'CB':
            self.object.bankaccount = Bankaccount.objects.filter(pk=int(self.request.POST['department']), isdeleted=0).\
                first()
            self.object.payee_code = self.object.bankaccount.code
            self.object.payee_name = self.object.bankaccount.accountnumber
            self.object.customer = None
            self.object.employee = None
            self.object.department = None
            self.object.supplier = None
            self.object.inventory = None
        elif self.object.dcclasstype.code == 'IN':
            self.object.inventory = Inventoryitem.objects.filter(pk=int(self.request.POST['inventory']), isdeleted=0).\
                first()
            self.object.payee_code = self.object.inventory.code
            self.object.payee_name = self.object.inventory.description
            self.object.customer = None
            self.object.employee = None
            self.object.department = None
            self.object.bankaccount = None
            self.object.supplier = None

        self.object.save(update_fields=['dcdate', 'dctype', 'dcclasstype', 'dcsubtype', 'particulars', 'vat', 'vatrate',
                                        'branch', 'outputvattype', 'currency', 'fxrate', 'remarks', 'modifyby',
                                        'modifydate', 'customer', 'supplier', 'employee', 'department', 'bankaccount',
                                        'inventory', 'payee_code', 'payee_name'])

        # accounting entry starts here..
        source = 'dcdetailtemp'
        mainid = self.object.id
        num = self.object.dcnum
        secretkey = self.request.POST['secretkey']
        updatedetail(source, mainid, num, secretkey, self.request.user)

        totalamount = Dcdetail.objects.filter(isdeleted=0).filter(dcmain_id=self.object.id). \
            aggregate(Sum('debitamount'))
        self.object.amount = totalamount['debitamount__sum']
        self.object.save(update_fields=['amount'])

        return HttpResponseRedirect('/debitcreditmemo/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Dcmain
    template_name = 'debitcreditmemo/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('debitcreditmemo.delete_dcmain') or self.object.status == 'O' \
                or self.object.dcstatus == 'A' or self.object.dcstatus == 'I' or self.object.dcstatus == 'R':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.dcstatus = 'D'
        self.object.save()

        return HttpResponseRedirect('/debitcreditmemo')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Dcmain
    template_name = 'debitcreditmemo/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['dcmain'] = Dcmain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['detail'] = Dcdetail.objects.filter(isdeleted=0). \
            filter(dcmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Dcdetail.objects.filter(isdeleted=0). \
            filter(dcmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Dcdetail.objects.filter(isdeleted=0). \
            filter(dcmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printeddc = Dcmain.objects.get(pk=self.kwargs['pk'], isdeleted=0)
        printeddc.print_ctr += 1
        printeddc.save()
        return context


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Dcmain
    template_name = 'debitcreditmemo/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['dcsubtype'] = Debitcreditmemosubtype.objects.filter(isdeleted=0).order_by('description')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Dcmain
    template_name = 'debitcreditmemo/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "DEBIT CREDIT MEMO BOOK"
        context['rc_title'] = "DEBIT CREDIT MEMO BOOK"

        return context


@csrf_exempt
def getdcsubtypes(request):
    if request.method == 'POST':
        dcclasstype = request.POST['dcclasstype']
        dcsubtype = Debitcreditmemosubtype.objects.filter(dcclasstype=dcclasstype, isdeleted=0).order_by('description')
        if dcsubtype is None:
            dcsubtype = Debitcreditmemosubtype.objects.filter(isdeleted=0).order_by('description')
        data = {
            'status': 'success',
            'dcsubtype': serializers.serialize("json", dcsubtype),
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_total = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            report_type = "DC Summary"
        else:
            report_type = "DC Detailed"
        query = Dcmain.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(dcnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(dcnum__lte=int(key_data))
        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(dcdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(dcdate__lte=key_data)
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(branch=int(key_data))
        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(vat=int(key_data))
        if request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name))
            query = query.filter(outputvattype=int(key_data))
        if request.COOKIES.get('rep_f_dctype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dctype_' + request.resolver_match.app_name))
            query = query.filter(dctype=str(key_data))
        if request.COOKIES.get('rep_f_dcstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dcstatus_' + request.resolver_match.app_name))
            query = query.filter(dcstatus=str(key_data))
        if request.COOKIES.get('rep_f_dcsubtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dcsubtype_' + request.resolver_match.app_name))
            query = query.filter(dcsubtype=int(key_data))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        query = Dcdetail.objects.all().filter(isdeleted=0)

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
            query = query.filter(dcmain__dcnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(dcmain__dcnum__lte=int(key_data))
        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(dcmain__dcdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(dcmain__dcdate__lte=key_data)
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(dcmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(dcmain__vat=int(key_data))
        if request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name))
            query = query.filter(dcmain__outputvattype=int(key_data))
        if request.COOKIES.get('rep_f_dctype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dctype_' + request.resolver_match.app_name))
            query = query.filter(dcmain__dctype=str(key_data))
        if request.COOKIES.get('rep_f_dcstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dcstatus_' + request.resolver_match.app_name))
            query = query.filter(dcmain__dcstatus=str(key_data))
        if request.COOKIES.get('rep_f_dcsubtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dcsubtype_' + request.resolver_match.app_name))
            query = query.filter(dcmain__dcsubtype=int(key_data))

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "DC Acctg Entry - Summary"

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
            report_type = "DC Acctg Entry - Detailed"

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
                                                                                     'dc_num')

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

        report_total = query.aggregate(Sum('amount'))

    return query, report_type, report_total


@csrf_exempt
def reportresultxlsx(request):
    import xlsxwriter
    try:
        import cStringIO as StringIO
    except ImportError:
        import StringIO
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)

    # query and default variables
    queryset, report_type, report_total = reportresultquery(request)
    report_type = report_type if report_type != '' else 'DC Report'
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
        amount_placement = 10
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 14
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        amount_placement = 15

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'DC Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Type', bold)
        worksheet.write('D1', 'Subtype', bold)
        worksheet.write('E1', 'Customer', bold)
        worksheet.write('F1', 'Status', bold)
        worksheet.write('G1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.write('A1', 'DC Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Type', bold)
        worksheet.write('D1', 'Subtype', bold)
        worksheet.write('E1', 'Branch', bold)
        worksheet.write('F1', 'VAT', bold)
        worksheet.write('G1', 'Out. VAT', bold)
        worksheet.write('H1', 'DC', bold)
        worksheet.write('I1', 'Customer', bold)
        worksheet.write('J1', 'Status', bold)
        worksheet.write('K1', 'Amount', bold_right)
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
                obj.dcnum,
                DateFormat(obj.dcdate).format('Y-m-d'),
                obj.get_dctype_display(),
                obj.dcsubtype.description,
                "[" + obj.customer_code + "] " + obj.customer_name,
                obj.get_dcstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            data = [
                obj.dcnum,
                DateFormat(obj.dcdate).format('Y-m-d'),
                obj.get_dctype_display(),
                obj.dcsubtype.description,
                obj.branch.description,
                obj.vat.description,
                obj.outputvattype.description,
                obj.dcclasstype.description,
                "[" + obj.customer_code + "] " + obj.customer_name,
                obj.get_dcstatus_display(),
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
                DateFormat(obj.dc_date).format('Y-m-d'),
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
        data = [
            "", "", "", "", "", "", "", "", "",
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
