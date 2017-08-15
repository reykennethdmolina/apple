from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from acctentry.views import generatekey, savedetail
from artype.models import Artype
from ataxcode.models import Ataxcode
from bankaccount.models import Bankaccount
from bankbranchdisburse.models import Bankbranchdisburse
from branch.models import Branch
from creditterm.models import Creditterm
from currency.models import Currency
from debitcreditmemosubtype.models import Debitcreditmemosubtype
from inputvattype.models import Inputvattype
from cvtype.models import Cvtype
from supplier.models import Supplier
from vat.models import Vat
from . models import Dcmain
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Dcmain
    template_name = 'debitcreditmemo/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Dcmain.objects.all().order_by('-enterdate')[0:10]


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Dcmain
    template_name = 'debitcreditmemo/create.html'
    fields = ['dcdate', 'dctype', 'dcsubtype', 'particulars', 'vat', 'customer', 'branch']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('debitcreditmemo.add_dcmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['dcartype'] = Artype.objects.filter(isdeleted=0).order_by('code')
        context['dcsubtype'] = Debitcreditmemosubtype.objects.filter(isdeleted=0).order_by('code')
        # context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        # context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
        #     order_by('first_name')
        # context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        # context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        # context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        # context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['secretkey'] = generatekey(self)
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        return context

    # def form_valid(self, form):
        # self.object = form.save(commit=False)
        #
        # if float(self.request.POST['amount']) <= 1000:
        #     year = str(form.cleaned_data['ofdate'].year)
        #     yearqs = Dcmain.objects.filter(ofnum__startswith=year)
        #
        #     if yearqs:
        #         ofnumlast = yearqs.latest('ofnum')
        #         latestofnum = str(ofnumlast)
        #         print "latest: " + latestofnum
        #
        #         ofnum = year
        #         last = str(int(latestofnum[4:]) + 1)
        #         zero_addon = 6 - len(last)
        #         for num in range(0, zero_addon):
        #             ofnum += '0'
        #         ofnum += last
        #
        #     else:
        #         ofnum = year + '000001'
        #
        #     print 'ofnum: ' + ofnum
        #     print self.request.POST['payee']
        #     print self.request.POST['hiddenpayee']
        #     print self.request.POST['hiddenpayeeid']
        #     if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
        #         self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
        #         self.object.payee_code = self.object.payee.code
        #         self.object.payee_name = self.object.payee.name
        #     else:
        #         self.object.payee_name = self.request.POST['payee']
        #
        #     self.object.ofnum = ofnum
        #     self.object.enterby = self.request.user
        #     self.object.modifyby = self.request.user
        #     self.object.employee_code = Employee.objects.get(pk=self.request.POST['employee']).code
        #     self.object.employee_name = Employee.objects.get(pk=self.request.POST['employee']).firstname.\
        #         strip(' \t\n\r') + ' ' + Employee.objects.get(pk=self.request.POST['employee']).lastname.\
        #         strip(' \t\n\r')
        #     self.object.department_code = Department.objects.get(pk=self.request.POST['department']).code
        #     self.object.department_name = Department.objects.get(pk=self.request.POST['department']).departmentname
        #     self.object.ofstatus = 'I'
        #     self.object.receiveby = self.request.user
        #     self.object.receivedate = datetime.datetime.now()
        #     self.object.designatedapprover = self.request.user
        #     self.object.actualapprover = self.request.user
        #     self.object.approverresponse = 'A'
        #     self.object.responsedate = datetime.datetime.now()
        #     self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
        #     self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
        #     self.object.save()
        #
        #     # accounting entry starts here..
        #     source = 'ofdetailtemp'
        #     mainid = self.object.id
        #     num = self.object.ofnum
        #     secretkey = self.request.POST['secretkey']
        #     savedetail(source, mainid, num, secretkey, self.request.user)
        #
        #     return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/cashierupdate')
        # else:
        #     return HttpResponseRedirect('/operationalfund/')
