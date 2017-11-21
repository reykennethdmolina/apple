from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail
from django.template.loader import render_to_string
from ataxcode.models import Ataxcode
from branch.models import Branch
from companyparameter.models import Companyparameter
from creditterm.models import Creditterm
from currency.models import Currency
from customer.models import Customer
from dcartype.models import Dcartype
from debitcreditmemosubtype.models import Debitcreditmemosubtype
from outputvattype.models import Outputvattype
from vat.models import Vat
from . models import Dcmain, Dcdetail, Dcdetailbreakdown, Dcdetailtemp, Dcdetailbreakdowntemp
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from easy_pdf.views import PDFTemplateView
from endless_pagination.views import AjaxListView
import datetime


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
        context['dcsubtype'] = Debitcreditmemosubtype.objects.filter(isdeleted=0).order_by('pk')
        context['dcartype'] = Dcartype.objects.filter(isdeleted=0).order_by('code')
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
    fields = ['dcdate', 'dctype', 'dcsubtype', 'dcartype', 'particulars', 'vat', 'branch', 'outputvattype', 'customer',
              'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('debitcreditmemo.add_dcmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['dcsubtype'] = Debitcreditmemosubtype.objects.filter(isdeleted=0).order_by('pk')
        context['dcartype'] = Dcartype.objects.filter(isdeleted=0).order_by('code')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['pk'] = 0
        context['secretkey'] = generatekey(self)

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

        self.object.customer_code = self.object.customer.code
        self.object.customer_name = self.object.customer.name
        self.object.vatrate = self.object.vat.rate
        self.object.save()

        # accounting entry starts here..
        source = 'dcdetailtemp'
        mainid = self.object.id
        num = self.object.dcnum
        secretkey = self.request.POST['secretkey']
        savedetail(source, mainid, num, secretkey, self.request.user)

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
        context['dcartype'] = Dcartype.objects.filter(isdeleted=0).order_by('code')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['pk'] = self.object.pk

        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Dcmain
    template_name = 'debitcreditmemo/update.html'
    fields = ['dcdate', 'dctype', 'dcsubtype', 'dcartype', 'particulars', 'vat', 'branch', 'outputvattype', 'customer',
              'particulars']

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
        context['dcsubtype'] = Debitcreditmemosubtype.objects.filter(isdeleted=0).order_by('pk')
        context['dcartype'] = Dcartype.objects.filter(isdeleted=0).order_by('code')
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['pk'] = self.object.pk
        context['secretkey'] = generatekey(self)

        if self.request.POST.get('customer', False):
            context['customer'] = Customer.objects.get(pk=self.request.POST['customer'], isdeleted=0)
        elif self.object.customer:
            context['customer'] = Customer.objects.get(pk=self.object.customer.id, isdeleted=0)

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
        self.object.customer_code = self.object.customer.code
        self.object.customer_name = self.object.customer.name

        self.object.save(update_fields=['dcdate', 'dctype', 'dcsubtype', 'dcartype', 'particulars', 'vat', 'vatrate',
                                        'branch', 'outputvattype', 'customer', 'customer_code', 'customer_name',
                                        'particulars', 'modifyby', 'modifydate'])

        # accounting entry starts here..
        source = 'dcdetailtemp'
        mainid = self.object.id
        num = self.object.dcnum
        secretkey = self.request.POST['secretkey']
        updatedetail(source, mainid, num, secretkey, self.request.user)

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
