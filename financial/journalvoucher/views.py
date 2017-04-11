from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
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
        secretkey = 'testken' #self.request.POST['secretkey']
        detailinfo = Jvdetailtemp.objects.all().filter(secretkey=secretkey).order_by('item_counter')

        for row in detailinfo:
            detail = Jvdetail()
            detail.jv_num = jvnum
            detail.jvmain = mainid
            detail.item_counter = len(Jvdetailtemp.objects.all().filter(secretkey=secretkey, isdeleted__in=[0,2])) + 1
            detail.jv_date = row.jv_date
            detail.chartofaccount = Chartofaccount.objects.get(pk=row.chartofaccount)
            # Return None if object is empty
            detail.bankaccount = get_object_or_None(Bankaccount, pk=row.bankaccount)
            detail.employee = get_object_or_None(Employee, pk=row.employee)
            detail.supplier = get_object_or_None(Supplier, pk=row.supplier)
            detail.customer = get_object_or_None(Customer, pk=row.customer)
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
            detail.modifyby = self.request.user
            detail.enterby = self.request.user
            detail.modifydate = datetime.datetime.now()
            detail.save()
            #print x.secretkey
            #print d
        # detail = Potype()


        return HttpResponseRedirect('/journalvoucher/create')