import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from acctentry.views import generatekey
from supplier.models import Supplier
from branch.models import Branch
from bankbranchdisburse.models import Bankbranchdisburse
from vat.models import Vat
from ataxcode.models import Ataxcode
from inputvattype.models import Inputvattype
from creditterm.models import Creditterm
from currency.models import Currency
from aptype.models import Aptype
from chartofaccount.models import Chartofaccount
from bankaccount.models import Bankaccount
from employee.models import Employee
from customer.models import Customer
from department.models import Department
from unit.models import Unit
from product.models import Product
from inputvat.models import Inputvat
from outputvat.models import Outputvat
from wtax.models import Wtax
from . models import Apmain, Apdetail, Apdetailtemp, Apdetailbreakdown, Apdetailbreakdowntemp
from annoying.functions import get_object_or_None

# pagination and search
from endless_pagination.views import AjaxListView
from django.db.models import Q

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
class CreateView(CreateView):
    model = Apmain
    template_name = 'accountspayable/create.html'
    fields = ['apdate', 'aptype', 'payee', 'branch',
              'bankbranchdisburse', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars',
              'currency', 'fxrate']

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
        context['pk'] = 0

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
        self.object.apstatus = 'V'
        self.object.fxrate = 1
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
        mainid = self.object.id
        apnum = self.object.apnum
        secretkey = self.request.POST['secretkey']
        detailinfo = Apdetailtemp.objects.all().filter(secretkey=secretkey).order_by('item_counter')

        counter = 1
        for row in detailinfo:
            detail = Apdetail()
            detail.ap_num = apnum
            detail.apmain = Apmain.objects.get(pk=mainid)
            detail.item_counter = counter
            detail.ap_date = row.ap_date
            detail.chartofaccount = Chartofaccount.objects.get(pk=row.chartofaccount)
            # Return None if object is empty
            detail.bankaccount = get_object_or_None(Bankaccount, pk=row.bankaccount)
            detail.employee = get_object_or_None(Employee, pk=row.employee)
            detail.supplier = get_object_or_None(Supplier, pk=row.supplier)
            detail.customer = get_object_or_None(Customer, pk=row.customer)
            detail.department = get_object_or_None(Department, pk=row.department)
            detail.unit = get_object_or_None(Unit, pk=row.unit)
            detail.branch = get_object_or_None(Branch, pk=row.branch)
            detail.product = get_object_or_None(Product, pk=row.product)
            detail.inputvat = get_object_or_None(Inputvat, pk=row.inputvat)
            detail.outputvat = get_object_or_None(Outputvat, pk=row.outputvat)
            detail.vat = get_object_or_None(Vat, pk=row.vat)
            detail.wtax = get_object_or_None(Wtax, pk=row.wtax)
            detail.ataxcode = get_object_or_None(Ataxcode, pk=row.ataxcode)
            detail.debitamount = row.debitamount
            detail.creditamount = row.creditamount
            detail.balancecode = row.balancecode
            detail.customerbreakstatus = row.customerbreakstatus
            detail.supplierbreakstatus = row.supplierbreakstatus
            detail.employeebreakstatus = row.employeebreakstatus
            detail.modifyby = self.request.user
            detail.enterby = self.request.user
            detail.modifydate = datetime.datetime.now()
            detail.save()
            counter += 1

            # Saving breakdown entry
            if row.customerbreakstatus <> 0:
                savebreakdownentry(self.request.user, apnum, mainid, detail.pk, row.pk, 'C')
            if row.employeebreakstatus <> 0:
                savebreakdownentry(self.request.user, apnum, mainid, detail.pk, row.pk, 'E')
            if row.supplierbreakstatus <> 0:
                savebreakdownentry(self.request.user, apnum, mainid, detail.pk, row.pk, 'S')

        return HttpResponseRedirect('/accountspayable/' + str(self.object.id) + '/update')


def savebreakdownentry(user, apnum, mainid, detailid, tempdetailid, dtype):

    breakdowninfo = Apdetailbreakdowntemp.objects.all().\
        filter(apdetailtemp=tempdetailid, datatype=dtype).order_by('item_counter')

    counter = 1
    for row in breakdowninfo:
        breakdown = Apdetailbreakdown()
        breakdown.ap_num = apnum
        breakdown.apmain = Apmain.objects.get(pk=mainid)
        breakdown.apdetail = Apdetail.objects.get(pk=detailid)
        breakdown.item_counter = counter
        breakdown.ap_date = row.ap_date
        breakdown.chartofaccount = Chartofaccount.objects.get(pk=row.chartofaccount)
        breakdown.particular = row.particular
        # Return None if object is empty
        breakdown.bankaccount = get_object_or_None(Bankaccount, pk=row.bankaccount)
        breakdown.employee = get_object_or_None(Employee, pk=row.employee)
        breakdown.supplier = get_object_or_None(Supplier, pk=row.supplier)
        breakdown.customer = get_object_or_None(Customer, pk=row.customer)
        breakdown.department = get_object_or_None(Department, pk=row.department)
        breakdown.unit = get_object_or_None(Unit, pk=row.unit)
        breakdown.branch = get_object_or_None(Branch, pk=row.branch)
        breakdown.product = get_object_or_None(Product, pk=row.product)
        breakdown.inputvat = get_object_or_None(Inputvat, pk=row.inputvat)
        breakdown.outputvat = get_object_or_None(Outputvat, pk=row.outputvat)
        breakdown.vat = get_object_or_None(Vat, pk=row.vat)
        breakdown.wtax = get_object_or_None(Wtax, pk=row.wtax)
        breakdown.ataxcode = get_object_or_None(Ataxcode, pk=row.ataxcode)
        breakdown.debitamount = row.debitamount
        breakdown.creditamount = row.creditamount
        breakdown.balancecode = row.balancecode
        breakdown.datatype = dtype
        breakdown.customerbreakstatus = row.customerbreakstatus
        breakdown.supplierbreakstatus = row.supplierbreakstatus
        breakdown.employeebreakstatus = row.employeebreakstatus
        breakdown.modifyby = user
        breakdown.enterby = user
        breakdown.modifydate = datetime.datetime.now()
        breakdown.save()
        counter += 1

    return True


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Apmain
    template_name = 'accountspayable/edit.html'
    fields = ['apdate', 'aptype', 'payee', 'branch',
              'bankbranchdisburse', 'vat', 'atax',
              'inputvattype', 'creditterm', 'duedate',
              'refno', 'deferred', 'particulars',
              'currency', 'fxrate']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('customer.change_apmain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save(update_fields=['apdate', 'aptype', 'payee', 'branch',
                                        'bankbranchdisburse', 'vat', 'atax',
                                        'inputvattype', 'creditterm', 'duedate',
                                        'refno', 'deferred', 'particulars',
                                        'currency'])
        return HttpResponseRedirect('/accountspayable/' + str(self.object.id) + '/update')

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
        context['pk'] = self.object.pk
        return context


def comments():
    print 123
    # copy po format for vat field
    # clear cache based on condition
    # cache api
