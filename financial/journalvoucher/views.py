from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
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
from journalvoucher.models import Jvmain, Jvdetail, Jvdetailtemp, Jvdetailbreakdown, Jvdetailbreakdowntemp
from chartofaccount.models import Chartofaccount
from potype.models import Potype
from acctentry.views import generatekey
from annoying.functions import get_object_or_None
import datetime
from random import randint

# Create your views here.

@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Jvmain
    template_name = 'journalvoucher/create.html'
    fields = ['jvdate', 'jvtype', 'refnum', 'particular', 'branch', 'currency', 'department']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        #context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0,status='A').order_by('accountcode')
        context['department'] =Department.objects.filter(isdeleted=0).order_by('pk')
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

        # # Save Data To JVDetail
        secretkey = 'ken' #self.request.POST['secretkey']
        detailinfo = Jvdetailtemp.objects.all().filter(secretkey=secretkey).order_by('item_counter')

        counter = 1
        for row in detailinfo:
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
            counter += 1

            # Saving breakdown entry
            if row.customerbreakstatus <> 0:
                savebreakdownentry(self.request.user, jvnum, mainid, detail.pk, row.pk, 'C')
            if row.employeebreakstatus <> 0:
                savebreakdownentry(self.request.user, jvnum, mainid, detail.pk, row.pk, 'E')
            if row.supplierbreakstatus <> 0:
                savebreakdownentry(self.request.user, jvnum, mainid, detail.pk, row.pk, 'S')

        return HttpResponseRedirect('/journalvoucher/create')

def savebreakdownentry(user, jvnum, mainid, detailid, tempdetailid, type):

    breakdowninfo = Jvdetailbreakdowntemp.objects.all().filter(jvdetailtemp=tempdetailid, datatype=type).order_by('item_counter')
    counter = 1
    for row in breakdowninfo:
        breakdown = Jvdetailbreakdown()
        breakdown.jv_num = jvnum
        breakdown.jvmain = Jvmain.objects.get(pk=mainid)
        breakdown.jvdetail= Jvdetail.objects.get(pk=detailid)
        breakdown.item_counter = counter
        breakdown.jv_date = row.jv_date
        breakdown.chartofaccount = Chartofaccount.objects.get(pk=row.chartofaccount)
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
        breakdown.datatype = type
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
    model = Jvmain
    template_name = 'journalvoucher/edit.html'
    fields = ['jvnum', 'jvdate', 'refnum', 'jvtype', 'particular', 'branch', 'currency', 'department']

    # def dispatch(self, request, *args, **kwargs):
    #     if not request.user.has_perm('fxtype.change_fxtype'):
    #         raise Http404
    #     return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # def get_initial(self):
    #     self.mysecretkey = generatekey(self)

        # breakdown = Jvdetailbreakdowntemp()
        # breakdown.secretkey = self.mysecretkey
        # breakdown.jv_num = 0
        # breakdown.jvmain = self.object.pk
        # breakdown.jvdetail = 1
        # breakdown.item_counter = 1
        # breakdown.jv_date = '2017-04-20'
        # breakdown.chartofaccount = 1
        # #Return None if object is empty
        #
        # breakdown.modifydate = datetime.datetime.now()
        # breakdown.save()

        # print self.object.pk


    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['self'] = Jvmain.objects.get(pk=self.object.pk)
        context['department'] = Department.objects.filter(isdeleted=0).order_by('pk')
        context['secretkey'] = 'ken'#self.mysecretkey
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('pk')
        return context

    def form_valid(self, form):
        # self.object = form.save(commit=False)
        # self.object.isdeleted = 1
        # self.object.save()
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['jvtype', 'refnum', 'modifyby', 'particular', 'branch', 'currency', 'department', 'modifydate'])
        #self.object.save()
        return HttpResponseRedirect('/journalvoucher/'+self.object.pk+'/update')
