import datetime
from django.db.models import Sum
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from jvtype.models import Jvtype
from currency.models import Currency
from branch.models import Branch
from chartofaccount.models import Chartofaccount
from bankaccount.models import Bankaccount
from department.models import Department
from employee.models import Employee
from supplier.models import Supplier
from customer.models import Customer
from unit.models import Unit
from product.models import Product
from inputvat.models import Inputvat
from outputvat.models import Outputvat
from vat.models import Vat
from wtax.models import Wtax
from ataxcode.models import Ataxcode
from journalvoucher.models import Jvmain, Jvdetail, Jvdetailtemp, \
    Jvdetailbreakdown, Jvdetailbreakdowntemp
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail
from annoying.functions import get_object_or_None


# Create your views here.

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Jvmain
    template_name = 'journalvoucher/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Jvmain.objects.all().order_by('pk')

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('pk')
        context['date'] = datetime.datetime.now()
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

        return context

@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Jvmain
    template_name = 'journalvoucher/create.html'
    fields = ['jvdate', 'jvtype', 'refnum', 'particular', 'branch', 'currency', 'department']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        # context['chartofaccount'] = Chartofaccount.objects.\
        #     filter(isdeleted=0,status='A').order_by('accountcode')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('pk')
        return context

    # def dispatch(self, request, *args, **kwargs):
    #     if not request.user.has_perm('bank.change_bank'):
    #         raise Http404
    #     return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # def post(self, request, *args, **kwargs):
    #     #self.object.jvnum = random(10)
    #     #print request.POST['secretkey']
    #     return super(CreateView, self).post(request, *args, **kwargs)

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
        mainid = self.object.id
        jvnum = self.object.jvnum

        # accounting entry starts here..
        source = 'jvdetailtemp'
        mainid = self.object.id
        num = self.object.jvnum
        secretkey = self.request.POST['secretkey']
        savedetail(source, mainid, num, secretkey, self.request.user)

        # # Save Data To JVDetail
        # secretkey = self.request.POST['secretkey']
        # detailinfo = Jvdetailtemp.objects.all().filter(secretkey=secretkey).order_by('item_counter')

        # counter = 1
        # for row in detailinfo:
        #     detail = Jvdetail()
        #     detail.jv_num = jvnum
        #     detail.jvmain = Jvmain.objects.get(pk=mainid)
        #     detail.item_counter = counter
        #     detail.jv_date = row.jv_date
        #     detail.chartofaccount = Chartofaccount.objects.get(pk=row.chartofaccount)
        #     # Return None if object is empty
        #     detail.bankaccount = get_object_or_None(Bankaccount, pk=row.bankaccount)
        #     detail.employee = get_object_or_None(Employee, pk=row.employee)
        #     detail.supplier = get_object_or_None(Supplier, pk=row.supplier)
        #     detail.customer = get_object_or_None(Customer, pk=row.customer)
        #     detail.department = get_object_or_None(Department, pk=row.department)
        #     detail.unit = get_object_or_None(Unit, pk=row.unit)
        #     detail.branch = get_object_or_None(Branch, pk=row.branch)
        #     detail.product = get_object_or_None(Product, pk=row.product)
        #     detail.inputvat = get_object_or_None(Inputvat, pk=row.inputvat)
        #     detail.outputvat = get_object_or_None(Outputvat, pk=row.outputvat)
        #     detail.vat = get_object_or_None(Vat, pk=row.vat)
        #     detail.wtax = get_object_or_None(Wtax, pk=row.wtax)
        #     detail.ataxcode = get_object_or_None(Ataxcode, pk=row.ataxcode)
        #     detail.debitamount = row.debitamount
        #     detail.creditamount = row.creditamount
        #     detail.balancecode = row.balancecode
        #     detail.customerbreakstatus = row.customerbreakstatus
        #     detail.supplierbreakstatus = row.supplierbreakstatus
        #     detail.employeebreakstatus = row.employeebreakstatus
        #     detail.modifyby = self.request.user
        #     detail.enterby = self.request.user
        #     detail.modifydate = datetime.datetime.now()
        #     detail.save()
        #     counter += 1
        #
        #     # Saving breakdown entry
        #     if row.customerbreakstatus <> 0:
        #         savebreakdownentry(self.request.user, jvnum, mainid, detail.pk, row.pk, 'C')
        #     if row.employeebreakstatus <> 0:
        #         savebreakdownentry(self.request.user, jvnum, mainid, detail.pk, row.pk, 'E')
        #     if row.supplierbreakstatus <> 0:
        #         savebreakdownentry(self.request.user, jvnum, mainid, detail.pk, row.pk, 'S')

        return HttpResponseRedirect('/journalvoucher/create')


# def savebreakdownentry(user, jvnum, mainid, detailid, tempdetailid, dtype):
#
#     breakdowninfo = Jvdetailbreakdowntemp.objects.all().\
#         filter(jvdetailtemp=tempdetailid, datatype=dtype).order_by('item_counter')
#
#     #print breakdowninfo
#     counter = 1
#     for row in breakdowninfo:
#         breakdown = Jvdetailbreakdown()
#         breakdown.jv_num = jvnum
#         breakdown.jvmain = Jvmain.objects.get(pk=mainid)
#         breakdown.jvdetail = Jvdetail.objects.get(pk=detailid)
#         breakdown.item_counter = counter
#         breakdown.jv_date = row.jv_date
#         breakdown.chartofaccount = Chartofaccount.objects.get(pk=row.chartofaccount)
#         breakdown.particular = row.particular
#         # Return None if object is empty
#         breakdown.bankaccount = get_object_or_None(Bankaccount, pk=row.bankaccount)
#         breakdown.employee = get_object_or_None(Employee, pk=row.employee)
#         breakdown.supplier = get_object_or_None(Supplier, pk=row.supplier)
#         breakdown.customer = get_object_or_None(Customer, pk=row.customer)
#         breakdown.department = get_object_or_None(Department, pk=row.department)
#         breakdown.unit = get_object_or_None(Unit, pk=row.unit)
#         breakdown.branch = get_object_or_None(Branch, pk=row.branch)
#         breakdown.product = get_object_or_None(Product, pk=row.product)
#         breakdown.inputvat = get_object_or_None(Inputvat, pk=row.inputvat)
#         breakdown.outputvat = get_object_or_None(Outputvat, pk=row.outputvat)
#         breakdown.vat = get_object_or_None(Vat, pk=row.vat)
#         breakdown.wtax = get_object_or_None(Wtax, pk=row.wtax)
#         breakdown.ataxcode = get_object_or_None(Ataxcode, pk=row.ataxcode)
#         breakdown.debitamount = row.debitamount
#         breakdown.creditamount = row.creditamount
#         breakdown.balancecode = row.balancecode
#         breakdown.datatype = dtype
#         breakdown.customerbreakstatus = row.customerbreakstatus
#         breakdown.supplierbreakstatus = row.supplierbreakstatus
#         breakdown.employeebreakstatus = row.employeebreakstatus
#         breakdown.modifyby = user
#         breakdown.enterby = user
#         breakdown.modifydate = datetime.datetime.now()
#         breakdown.save()
#         counter += 1
#
#     return True


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Jvmain
    template_name = 'journalvoucher/edit.html'
    fields = ['jvnum', 'jvdate', 'refnum', 'jvtype',
              'particular', 'branch', 'currency', 'department']

    # def dispatch(self, request, *args, **kwargs):
    #     if not request.user.has_perm('fxtype.change_fxtype'):
    #         raise Http404
    #     return super(UpdateView, self).dispatch(request, *args, **kwargs)

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
        contextdatatable = {
            'datatemp': querystmtdetail('jvdetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('jvdetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['jvtype', 'refnum', 'modifyby', 'particular',
                                        'branch', 'currency', 'department', 'modifydate'])
        mainid = self.object.id
        jvnum = self.object.jvnum

        secretkey = self.request.POST['secretkey']
        detailinfo = Jvdetailtemp.objects.all().filter(secretkey=secretkey).order_by('item_counter')

        counter = 1
        for row in detailinfo:
            if row.jvmain:
                if row.isdeleted == 0:
                    #update
                    detail = Jvdetail.objects.get(pk=row.jvdetail)
                    detail.item_counter = counter
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
                    detail.modifydate = datetime.datetime.now()
                    detail.save()

                    datatype = 'X'
                    if row.customerbreakstatus <> 0:
                        datatype = 'C'
                    if row.employeebreakstatus <> 0:
                        datatype = 'E'
                    if row.supplierbreakstatus <> 0:
                        datatype = 'S'

                    breakdowninfo = Jvdetailbreakdowntemp.objects.all().\
                        filter(jvdetailtemp=row.pk, datatype=datatype).order_by('item_counter')
                    counterb = 1
                    for brow in breakdowninfo:
                        if brow.jvmain:
                            if brow.isdeleted == 0:
                                #update
                                breakdown = Jvdetailbreakdown.objects.get(pk=brow.jvdetailbreakdown)
                                breakdown.item_counter = counterb
                                breakdown.chartofaccount = Chartofaccount.objects.\
                                    get(pk=brow.chartofaccount)
                                breakdown.particular = brow.particular
                                # Return None if object is empty
                                breakdown.bankaccount = get_object_or_None(Bankaccount, \
                                    pk=brow.bankaccount)
                                breakdown.employee = get_object_or_None(Employee, \
                                    pk=brow.employee)
                                breakdown.supplier = get_object_or_None(Supplier, \
                                    pk=brow.supplier)
                                breakdown.customer = get_object_or_None(Customer, \
                                    pk=brow.customer)
                                breakdown.department = get_object_or_None(Department, \
                                    pk=brow.department)
                                breakdown.unit = get_object_or_None(Unit, pk=brow.unit)
                                breakdown.branch = get_object_or_None(Branch, pk=brow.branch)
                                breakdown.product = get_object_or_None(Product, pk=brow.product)
                                breakdown.inputvat = get_object_or_None(Inputvat, \
                                    pk=brow.inputvat)
                                breakdown.outputvat = get_object_or_None(Outputvat, \
                                    pk=brow.outputvat)
                                breakdown.vat = get_object_or_None(Vat, pk=brow.vat)
                                breakdown.wtax = get_object_or_None(Wtax, pk=brow.wtax)
                                breakdown.ataxcode = get_object_or_None(Ataxcode, pk=brow.ataxcode)
                                breakdown.debitamount = brow.debitamount
                                breakdown.creditamount = brow.creditamount
                                breakdown.balancecode = brow.balancecode
                                breakdown.datatype = datatype
                                breakdown.customerbreakstatus = brow.customerbreakstatus
                                breakdown.supplierbreakstatus = brow.supplierbreakstatus
                                breakdown.employeebreakstatus = brow.employeebreakstatus
                                breakdown.modifyby = self.request.user
                                breakdown.modifydate = datetime.datetime.now()
                                breakdown.save()
                                counterb = 1
                            if brow.isdeleted == 2:
                                #delete
                                instance = Jvdetailbreakdown.objects.get(pk=brow.jvdetailbreakdown)
                                instance.delete()
                        if not brow.jvmain:
                            #add
                            breakdown = Jvdetailbreakdown()
                            breakdown.jv_num = jvnum
                            breakdown.jvmain = Jvmain.objects.get(pk=mainid)
                            breakdown.jvdetail = Jvdetail.objects.get(pk=detail.pk)
                            breakdown.item_counter = counterb
                            breakdown.jv_date = brow.jv_date
                            breakdown.chartofaccount = Chartofaccount.objects.get(\
                                pk=brow.chartofaccount)
                            breakdown.particular = brow.particular
                            # Return None if object is empty
                            breakdown.bankaccount = get_object_or_None(Bankaccount, \
                                pk=brow.bankaccount)
                            breakdown.employee = get_object_or_None(Employee, pk=brow.employee)
                            breakdown.supplier = get_object_or_None(Supplier, pk=brow.supplier)
                            breakdown.customer = get_object_or_None(Customer, pk=brow.customer)
                            breakdown.department = get_object_or_None(Department, \
                                pk=brow.department)
                            breakdown.unit = get_object_or_None(Unit, pk=brow.unit)
                            breakdown.branch = get_object_or_None(Branch, pk=brow.branch)
                            breakdown.product = get_object_or_None(Product, pk=brow.product)
                            breakdown.inputvat = get_object_or_None(Inputvat, pk=brow.inputvat)
                            breakdown.outputvat = get_object_or_None(Outputvat, pk=brow.outputvat)
                            breakdown.vat = get_object_or_None(Vat, pk=brow.vat)
                            breakdown.wtax = get_object_or_None(Wtax, pk=brow.wtax)
                            breakdown.ataxcode = get_object_or_None(Ataxcode, pk=brow.ataxcode)
                            breakdown.debitamount = brow.debitamount
                            breakdown.creditamount = brow.creditamount
                            breakdown.balancecode = brow.balancecode
                            breakdown.datatype = datatype
                            breakdown.customerbreakstatus = brow.customerbreakstatus
                            breakdown.supplierbreakstatus = brow.supplierbreakstatus
                            breakdown.employeebreakstatus = brow.employeebreakstatus
                            breakdown.modifyby = self.request.user
                            breakdown.enterby = self.request.user
                            breakdown.modifydate = datetime.datetime.now()
                            breakdown.save()
                            counterb = 1

                    counter += 1
                if row.isdeleted == 2:
                    #delete
                    instance = Jvdetail.objects.get(pk=row.jvdetail)
                    instance.delete()
                    instancebreakdown = Jvdetailbreakdown.objects.filter(jvdetail=row.jvdetail)
                    instancebreakdown.delete()
            if not row.jvmain:
                #add
                detail = Jvdetail()
                detail.jv_num = jvnum
                detail.jvmain = Jvmain.objects.get(pk=mainid)
                detail.item_counter = counter
                detail.jv_date = row.jv_date
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

                # Saving breakdown entry
                if row.customerbreakstatus <> 0:
                    savebreakdownentry(self.request.user, jvnum, mainid, detail.pk, row.pk, 'C')
                if row.employeebreakstatus <> 0:
                    savebreakdownentry(self.request.user, jvnum, mainid, detail.pk, row.pk, 'E')
                if row.supplierbreakstatus <> 0:
                    savebreakdownentry(self.request.user, jvnum, mainid, detail.pk, row.pk, 'S')

                counter += 1

        return HttpResponseRedirect('/journalvoucher/'+str(self.object.pk)+'/update')
