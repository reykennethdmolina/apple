from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from ataxcode.models import Ataxcode
from branch.models import Branch
from companyparameter.models import Companyparameter
from creditterm.models import Creditterm
from currency.models import Currency
from inputvattype.models import Inputvattype
from oftype.models import Oftype
from ofsubtype.models import Ofsubtype
from supplier.models import Supplier
from vat.models import Vat
from wtax.models import Wtax
from employee.models import Employee
from department.models import Department
from inputvat.models import Inputvat
from . models import Ofmain, Ofdetail, Ofdetailtemp, Ofdetailbreakdown, Ofdetailbreakdowntemp, Ofitem, Ofitemtemp
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime
from endless_pagination.views import AjaxListView
from annoying.functions import get_object_or_None


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Ofmain
    template_name = 'operationalfund/index.html'
    page_template = 'operationalfund/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Ofmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(ofnum__icontains=keysearch) |
                                 Q(ofdate__icontains=keysearch) |
                                 Q(payee_name__icontains=keysearch) |
                                 Q(amount__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        context['listcount'] = Ofmain.objects.all().count()
        context['canbeapproved'] = Ofmain.objects.filter(Q(ofstatus='F') | Q(ofstatus='A') | Q(ofstatus='D')).\
            filter(isdeleted=0).count()
        context['forapproval'] = Ofmain.objects.filter(designatedapprover=self.request.user).count()
        context['userrole'] = 'C' if self.request.user.has_perm('operationalfund.is_cashier') else 'U'

        # data for lookup
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        # data for lookup

        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Ofmain
    template_name = 'operationalfund/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['detail'] = Ofdetail.objects.filter(isdeleted=0).\
            filter(ofmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Ofdetail.objects.filter(isdeleted=0).\
            filter(ofmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Ofdetail.objects.filter(isdeleted=0).\
            filter(ofmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        # data for lookup
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        # data for lookup

        return context


@method_decorator(login_required, name='dispatch')
class CreateViewUser(CreateView):
    model = Ofmain
    template_name = 'operationalfund/usercreate.html'
    fields = ['ofdate', 'oftype', 'requestor', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        # if not request.user.has_perm('operationalfund.add_ofmain') or \
        #     request.user.has_perm('operationalfund.is_cashier'):
        if not request.user.has_perm('operationalfund.add_ofmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.mysecretkey = generatekey(self)

        context = super(CreateView, self).get_context_data(**kwargs)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['requestor'] = User.objects.filter(pk=self.request.user.id)
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0)
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['secretkey'] = self.mysecretkey

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        year = str(form.cleaned_data['ofdate'].year)
        yearqs = Ofmain.objects.filter(ofnum__startswith=year)

        if yearqs:
            ofnumlast = yearqs.latest('ofnum')
            latestofnum = str(ofnumlast)
            print "latest: " + latestofnum

            ofnum = year
            last = str(int(latestofnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                ofnum += '0'
            ofnum += last

        else:
            ofnum = year + '000001'

        print 'ofnum: ' + ofnum

        self.object.ofnum = ofnum
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.requestor_username = self.object.requestor.username
        self.object.requestor_name = self.object.requestor.first_name + ' ' + self.object.requestor.last_name
        self.object.department = Department.objects.get(code='IT')  # for editing, should base on user
        self.object.department_code = self.object.department.code
        self.object.department_name = self.object.department.departmentname
        self.object.save()

        # ----------------- START save ofitemtemp to ofitem START ---------------------
        itemtemp = Ofitemtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
            order_by('enterdate')
        totalamount = 0
        i = 1
        for itemtemp in itemtemp:
            item = Ofitem()
            item.item_counter = i
            item.ofnum = self.object.ofnum
            item.ofdate = self.object.ofdate
            item.payee_code = itemtemp.payee_code
            item.payee_name = itemtemp.payee_name
            item.amount = itemtemp.amount
            item.particulars = itemtemp.particulars
            item.refnum = itemtemp.refnum
            item.fxrate = itemtemp.fxrate
            item.periodfrom = itemtemp.periodfrom
            item.periodto = itemtemp.periodto
            item.currency = Currency.objects.get(pk=itemtemp.currency)
            item.enterby = itemtemp.enterby
            item.modifyby = itemtemp.modifyby
            item.ofmain = self.object
            item.ofsubtype = itemtemp.ofsubtype
            item.oftype = Oftype.objects.get(pk=itemtemp.oftype)
            item.payee = get_object_or_None(Supplier, id=itemtemp.payee)
            item.ofitemstatus = itemtemp.ofitemstatus
            item.save()
            itemtemp.delete()
            totalamount += item.amount
            i += 1
        # ----------------- END save ofitemtemp to ofitem END ---------------------

        self.object.amount = totalamount
        self.object.save()

        # return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/userupdate')
        return HttpResponseRedirect('/operationalfund/')


@method_decorator(login_required, name='dispatch')
class CreateViewCashier(CreateView):
    model = Ofmain
    template_name = 'operationalfund/cashiercreate.html'
    fields = ['ofdate', 'oftype', 'ofsubtype', 'amount', 'refnum', 'particulars', 'creditterm', 'vat', 'atc',
              'inputvattype', 'deferredvat', 'currency', 'fxrate', 'employee', 'department', 'branch']

    def dispatch(self, request, *args, **kwargs):
        # if not request.user.has_perm('operationalfund.add_ofmain') or \
        #         not request.user.has_perm('operationalfund.is_cashier'):
        raise Http404
        # return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['secretkey'] = generatekey(self)

        # data for lookup
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        # data for lookup

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if float(self.request.POST['amount']) <= 1000:
            year = str(form.cleaned_data['ofdate'].year)
            yearqs = Ofmain.objects.filter(ofnum__startswith=year)

            if yearqs:
                ofnumlast = yearqs.latest('ofnum')
                latestofnum = str(ofnumlast)
                print "latest: " + latestofnum

                ofnum = year
                last = str(int(latestofnum[4:]) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    ofnum += '0'
                ofnum += last

            else:
                ofnum = year + '000001'

            print 'ofnum: ' + ofnum
            print self.request.POST['payee']
            print self.request.POST['hiddenpayee']
            print self.request.POST['hiddenpayeeid']
            if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
                self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
                self.object.payee_code = self.object.payee.code
                self.object.payee_name = self.object.payee.name
            else:
                self.object.payee_name = self.request.POST['payee']

            self.object.ofnum = ofnum
            self.object.enterby = self.request.user
            self.object.modifyby = self.request.user
            self.object.employee_code = Employee.objects.get(pk=self.request.POST['employee']).code
            self.object.employee_name = Employee.objects.get(pk=self.request.POST['employee']).firstname.\
                strip(' \t\n\r') + ' ' + Employee.objects.get(pk=self.request.POST['employee']).lastname.\
                strip(' \t\n\r')
            self.object.department_code = Department.objects.get(pk=self.request.POST['department']).code
            self.object.department_name = Department.objects.get(pk=self.request.POST['department']).departmentname
            self.object.ofstatus = 'I'
            self.object.receiveby = self.request.user
            self.object.receivedate = datetime.datetime.now()
            self.object.designatedapprover = self.request.user
            self.object.actualapprover = self.request.user
            self.object.approverresponse = 'A'
            self.object.responsedate = datetime.datetime.now()
            self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
            self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
            self.object.save()

            # accounting entry starts here..
            source = 'ofdetailtemp'
            mainid = self.object.id
            num = self.object.ofnum
            secretkey = self.request.POST['secretkey']
            savedetail(source, mainid, num, secretkey, self.request.user)

            return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/cashierupdate')
        else:
            return HttpResponseRedirect('/operationalfund/')


@method_decorator(login_required, name='dispatch')
class UpdateViewUser(UpdateView):
    model = Ofmain
    template_name = 'operationalfund/userupdate.html'
    fields = ['ofnum', 'ofdate', 'oftype', 'requestor', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        # if not request.user.has_perm('operationalfund.change_ofmain') or self.object.isdeleted == 1 or \
        #         request.user.has_perm('operationalfund.is_cashier'):
        #     if not request.user.username == 'admin':
        if not request.user.has_perm('operationalfund.change_ofmain'):
            raise Http404
        elif request.user.has_perm('operationalfund.is_cashier'):
            if self.object.ofstatus != 'F' and self.object.ofstatus != 'D' and request.user.username != 'admin':
                raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        self.mysecretkey = generatekey(self)

        # requested items
        iteminfo = Ofitem.objects.filter(ofmain=self.object.pk, isdeleted=0).order_by('item_counter')

        for data in iteminfo:
            detail = Ofitemtemp()
            detail.item_counter = data.item_counter
            detail.secretkey = self.mysecretkey
            detail.ofmain = data.ofmain.id
            detail.ofitem = data.id
            detail.ofnum = data.ofnum
            detail.ofdate = data.ofdate
            detail.oftype = data.oftype.id
            detail.ofsubtype = get_object_or_None(Ofsubtype, id=data.ofsubtype.id)
            detail.payee = data.payee_id
            detail.payee_code = data.payee_code
            detail.payee_name = data.payee_name
            detail.amount = data.amount
            detail.particulars = data.particulars
            detail.refnum = data.refnum
            detail.vat = data.vat_id
            detail.vatrate = data.vatrate
            detail.inputvattype = data.inputvattype_id
            detail.deferredvat = data.deferredvat
            detail.currency = data.currency_id
            detail.atc = data.atc_id
            detail.fxrate = data.fxrate
            detail.remarks = data.remarks
            detail.periodfrom = data.periodfrom
            detail.periodto = data.periodto
            detail.save()
            # requested items end

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['requestor'] = User.objects.filter(pk=self.request.user.id)
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0)
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['secretkey'] = self.mysecretkey

        context['savedoftype'] = self.object.oftype.code
        context['ofstatus'] = Ofmain.objects.get(pk=self.object.id).get_ofstatus_display()
        context['assignedcashier'] = Ofmain.objects.get(
            pk=self.object.id).receiveby.first_name + ' ' + Ofmain.objects.get(
            pk=self.object.id).receiveby.last_name if Ofmain.objects.get(pk=self.object.id).receiveby else None
        context['actualapprover'] = Ofmain.objects.get(
            pk=self.object.id).actualapprover.first_name + ' ' + Ofmain.objects.get(
            pk=self.object.id).actualapprover.last_name if Ofmain.objects.get(
            pk=self.object.id).actualapprover else None
        context['responsedate'] = Ofmain.objects.get(
            pk=self.object.id).responsedate if Ofmain.objects.get(pk=self.object.id).responsedate else None
        context['approverresponse'] = Ofmain.objects.get(
            pk=self.object.id).approverresponse if Ofmain.objects.get(pk=self.object.id).approverresponse else None
        context['releasedto'] = Ofmain.objects.get(
            pk=self.object.id).paymentreceivedby.firstname + ' ' + Ofmain.objects.get(
            pk=self.object.id).paymentreceivedby.lastname if Ofmain.objects.get(
            pk=self.object.id).paymentreceivedby else None
        context['releasedate'] = Ofmain.objects.get(
            pk=self.object.id).releasedate if Ofmain.objects.get(pk=self.object.id).releasedate else None

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if self.object.ofstatus != 'A' and self.object.ofstatus != 'I' and self.object.ofstatus != 'R':
            if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
                self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
                self.object.payee_code = self.object.payee.code
                self.object.payee_name = self.object.payee.name
            else:
                self.object.payee = None
                self.object.payee_code = None
                self.object.payee_name = self.request.POST['payee']

            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['ofdate', 'payee', 'payee_code', 'payee_name', 'amount', 'particulars',
                                            'designatedapprover'])

        return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/userupdate')


@method_decorator(login_required, name='dispatch')
class UpdateViewCashier(UpdateView):
    model = Ofmain
    template_name = 'operationalfund/cashierupdate2.html'
    fields = ['ofnum', 'ofdate', 'oftype', 'amount', 'refnum', 'particulars', 'creditterm', 'ofstatus', 'department',
              'remarks', 'paymentreceivedby', 'paymentreceiveddate', 'branch', 'requestor']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('operationalfund.change_ofmain') or self.object.isdeleted == 1 \
                or not request.user.has_perm('operationalfund.is_cashier') or self.object.ofstatus == 'F' \
                or self.object.ofstatus == 'D':
            raise Http404
        elif self.object.ofstatus == 'A':
            self.object.ofstatus = 'I'
            self.object.receiveby = self.request.user
            self.object.receivedate = datetime.datetime.now()
            self.object.save(update_fields=['ofstatus', 'receiveby', 'receivedate'])
        elif self.object.ofstatus == 'R':
            if self.object.oftype is None or self.object.ofsubtype is None or self.object.creditterm is None or \
                    self.object.vat is None or self.object.atc is None or self.object.inputvattype is None or \
                    self.object.currency is None:
                self.object.ofstatus = 'I'
                self.object.releasedate = None
                self.object.releaseby = None
                self.object.paymentreceivedby = None
                self.object.paymentreceiveddate = None
                self.object.save(update_fields=['ofstatus', 'releasedate', 'releaseby', 'paymentreceivedby',
                                                'paymentreceiveddate'])
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # accounting entry starts here
    def get_initial(self):
        self.mysecretkey = generatekey(self)

        # requested items
        iteminfo = Ofitem.objects.filter(ofmain=self.object.pk, isdeleted=0).order_by('item_counter')

        for data in iteminfo:
            detail = Ofitemtemp()
            detail.item_counter = data.item_counter
            detail.secretkey = self.mysecretkey
            detail.ofmain = data.ofmain.id
            detail.ofitem = data.id
            detail.ofnum = data.ofnum
            detail.ofdate = data.ofdate
            detail.oftype = data.oftype.id
            detail.ofsubtype = get_object_or_None(Ofsubtype, id=data.ofsubtype.id)
            detail.payee = data.payee_id
            detail.payee_code = data.payee_code
            detail.payee_name = data.payee_name
            detail.amount = data.amount
            detail.particulars = data.particulars
            detail.refnum = data.refnum
            detail.vat = data.vat_id
            detail.vatrate = data.vatrate
            detail.inputvattype = data.inputvattype_id
            detail.deferredvat = data.deferredvat
            detail.currency = data.currency_id
            detail.atc = data.atc_id
            detail.fxrate = data.fxrate
            detail.remarks = data.remarks
            detail.periodfrom = data.periodfrom
            detail.periodto = data.periodto
            detail.save()
        # requested items end

        detailinfo = Ofdetail.objects.filter(ofmain=self.object.pk).order_by('item_counter')

        for drow in detailinfo:
            detail = Ofdetailtemp()
            detail.secretkey = self.mysecretkey
            detail.of_num = drow.of_num
            detail.ofmain = drow.ofmain_id
            detail.ofdetail = drow.pk
            detail.item_counter = drow.item_counter
            detail.of_date = drow.of_date
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

            breakinfo = Ofdetailbreakdown.objects. \
                filter(ofdetail_id=drow.id).order_by('pk', 'datatype')
            if breakinfo:
                for brow in breakinfo:
                    breakdown = Ofdetailbreakdowntemp()
                    breakdown.of_num = drow.of_num
                    breakdown.secretkey = self.mysecretkey
                    breakdown.ofmain = drow.ofmain_id
                    breakdown.ofdetail = drow.pk
                    breakdown.ofdetailtemp = detailtempid
                    breakdown.ofdetailbreakdown = brow.pk
                    breakdown.item_counter = brow.item_counter
                    breakdown.of_date = brow.of_date
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
        context['actualapprover'] = User.objects.get(pk=self.object.actualapprover.id).first_name + ' ' + \
            User.objects.get(pk=self.object.actualapprover.id).last_name
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        # context['payee'] = Ofmain.objects.get(pk=self.object.id).payee.id if Ofmain.objects.get(
        #     pk=self.object.id).payee is not None else ''
        # context['payee_name'] = Ofmain.objects.get(pk=self.object.id).payee_name
        context['originalofstatus'] = 'A' if self.object.creditterm is None else Ofmain.objects.get(pk=self.object.id).ofstatus
        context['requestor'] = User.objects.filter(pk=self.object.requestor.id)
        context['requestordepartment'] = Department.objects.filter(pk=self.object.department.id).order_by('departmentname')

        # data for lookup
        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = self.object.pk
        # data for lookup

        # requested items
        context['itemtemp'] = Ofitemtemp.objects.filter(ofmain=self.object.pk, isdeleted=0, secretkey=self.mysecretkey).order_by('item_counter')

        # accounting entry starts here
        context['secretkey'] = self.mysecretkey
        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'ofdetailtemp',
            'tablebreakdowntemp': 'ofdetailbreakdowntemp',

            'datatemp': querystmtdetail('ofdetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('ofdetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        # accounting entry ends here

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if self.request.POST['originalofstatus'] != 'R':
            if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
                self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
                self.object.payee_code = self.object.payee.code
                self.object.payee_name = self.object.payee.name
            else:
                self.object.payee = None
                self.object.payee_code = None
                self.object.payee_name = self.request.POST['payee']

            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
            self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
            # removed payee, payee_code, payee_name, department, employee, designatedapprover, amount
            self.object.save(update_fields=['ofdate', 'ofsubtype', 'amount', 'refnum', 'particulars',
                                            'creditterm', 'vat', 'atc', 'inputvattype', 'deferredvat', 'currency',
                                            'fxrate', 'branch', 'ofstatus', 'remarks', 'modifyby', 'modifydate',
                                            'vatrate', 'atcrate'])

            # revert status from RELEASED to In Process if no release date is saved
            if self.object.ofstatus == 'R' and self.object.releasedate is None:
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.paymentreceivedby = None
                self.object.paymentreceiveddate = None
                self.object.ofstatus = 'I'
                self.object.save(update_fields=['releaseby', 'releasedate', 'paymentreceivedby', 'paymentreceiveddate',
                                                'ofstatus'])

            # remove release details if OFSTATUS is not RELEASED
            if self.object.ofstatus != 'R':
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.paymentreceivedby = None
                self.object.paymentreceiveddate = None
                self.object.save(update_fields=['releaseby', 'releasedate', 'paymentreceivedby', 'paymentreceiveddate'])

        else:
            if self.request.POST['ofstatus'] == 'I':
                self.object.ofstatus = 'I'
                self.object.releasedate = None
                self.object.releaseby = None
                self.object.paymentreceivedby = None
                self.object.paymentreceiveddate = None
                self.object.save(update_fields=['ofstatus', 'releasedate', 'releaseby', 'paymentreceivedby',
                                                'paymentreceiveddate'])
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['modifyby', 'modifydate', 'remarks'])

        # accounting entry starts here..
        source = 'ofdetailtemp'
        mainid = self.object.id
        num = self.object.ofnum
        secretkey = self.request.POST['secretkey']
        updatedetail(source, mainid, num, secretkey, self.request.user)

        return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/cashierupdate')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Ofmain
    template_name = 'operationalfund/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('operationalfund.delete_ofmain') or self.object.status == 'O' \
                or self.object.ofstatus != 'F':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.ofstatus = 'D'
        self.object.save()

        return HttpResponseRedirect('/operationalfund')


@csrf_exempt
def saveitemtemp(request):
    if request.method == 'POST':
        if request.POST['id_itemtemp'] != '':  # if item already exists (update)
            itemtemp = Ofitemtemp.objects.get(pk=int(request.POST['id_itemtemp']))
        else:  # if item does not exist (create)
            itemtemp = Ofitemtemp()
            itemtemp.enterby = request.user
        itemtemp.item_counter = request.POST['itemno']
        itemtemp.secretkey = request.POST['secretkey']
        itemtemp.oftype = request.POST['id_oftype']
        itemtemp.ofsubtype = Ofsubtype.objects.get(pk=request.POST['id_ofsubtype'])
        if request.POST['id_payee'] == request.POST['id_hiddenpayee']:
            itemtemp.payee = request.POST['id_hiddenpayeeid']
            itemtemp.payee_code = Supplier.objects.get(pk=itemtemp.payee).code
            itemtemp.payee_name = Supplier.objects.get(pk=itemtemp.payee).name
        else:
            itemtemp.payee_name = request.POST['id_payee']
        itemtemp.amount = request.POST['id_amount'].replace(',', '')
        itemtemp.particulars = request.POST['id_particulars']
        itemtemp.currency = request.POST['id_currency']
        itemtemp.fxrate = float(request.POST['id_fxrate'])
        itemtemp.periodfrom = request.POST['id_periodfrom'] if request.POST['id_periodfrom'] != '' else None
        itemtemp.periodto = request.POST['id_periodto'] if request.POST['id_periodto'] != '' else None
        itemtemp.modifyby = request.user
        itemtemp.save()
        data = {
            'status': 'success',
            'itemtempid': itemtemp.pk,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def deleteitemtemp(request):
    if request.method == 'POST':
        itemtemptodelete = Ofitemtemp.objects.get(pk=request.POST['id_itemtemp'])
        if itemtemptodelete.ofmain is None:
            itemtemptodelete.delete()
        else:
            itemtemptodelete.isdeleted = 1
            itemtemptodelete.save()
        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def autoentry(request):
    if request.method == 'POST':
        # set isdeleted=2 for existing detailtemp data
        data_table = validatetable(request.POST['table'])
        updateallquery(request.POST['table'], request.POST['ofnum'])
        deleteallquery(request.POST['table'], request.POST['secretkey'])
        vatamount = float(request.POST['amount']) * (float(request.POST['vatrate'])/100)

        if request.POST['oftype'] == "Petty Cash":
            # Entries: Cash In Bank (C), Input VAT (if VAT rate > 0.00) (C), Chart of Account assigned to OF Subtype (D)
            # Cash In Bank
            ofdetailtemp1 = Ofdetailtemp()
            ofdetailtemp1.item_counter = 1
            ofdetailtemp1.secretkey = request.POST['secretkey']
            ofdetailtemp1.of_num = ''
            ofdetailtemp1.of_date = Ofmain.objects.get(ofnum=request.POST['ofnum']).ofdate
            ofdetailtemp1.chartofaccount = Companyparameter.objects.get(code='PDI').coa_cashinbank_id
            ofdetailtemp1.bankaccount = Branch.objects.get(id=request.POST['branch']).bankaccount_id if Branch.objects.\
                get(id=request.POST['branch']).bankaccount else Companyparameter.objects.\
                get(code='PDI').def_bankaccount_id
            ofdetailtemp1.creditamount = float(request.POST['amount']) - vatamount
            ofdetailtemp1.balancecode = 'C'
            ofdetailtemp1.enterby = request.user
            ofdetailtemp1.modifyby = request.user
            ofdetailtemp1.save()

            # Input VAT (if vatamount > 0.00)
            if vatamount > 0:
                ofdetailtemp2 = Ofdetailtemp()
                ofdetailtemp2.item_counter = 2
                ofdetailtemp2.secretkey = request.POST['secretkey']
                ofdetailtemp2.of_num = ''
                ofdetailtemp2.of_date = Ofmain.objects.get(ofnum=request.POST['ofnum']).ofdate
                ofdetailtemp2.chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat_id
                inputvat = Inputvat.objects.filter(inputvattype=request.POST['inputvattype']).first()
                ofdetailtemp2.inputvat = inputvat.id
                ofdetailtemp2.creditamount = vatamount
                ofdetailtemp2.balancecode = 'C'
                ofdetailtemp2.enterby = request.user
                ofdetailtemp2.modifyby = request.user
                ofdetailtemp2.save()

            # Chart of Account assigned to OF Subtype
            ofdetailtemp3 = Ofdetailtemp()
            ofdetailtemp3.item_counter = 3 if vatamount > 0 else 2
            ofdetailtemp3.secretkey = request.POST['secretkey']
            ofdetailtemp3.of_num = ''
            ofdetailtemp3.of_date = Ofmain.objects.get(ofnum=request.POST['ofnum']).ofdate
            ofdetailtemp3.chartofaccount = Ofsubtype.objects.get(id=request.POST['ofsubtype']).debitchartofaccount_id
            ofdetailtemp3.debitamount = float(request.POST['amount'])
            ofdetailtemp3.balancecode = 'D'
            ofdetailtemp3.enterby = request.user
            ofdetailtemp3.modifyby = request.user
            ofdetailtemp3.save()

            context = {
                'tabledetailtemp': data_table['str_detailtemp'],
                'tablebreakdowntemp': data_table['str_detailbreakdowntemp'],
                'datatemp': querystmtdetail(data_table['str_detailtemp'], request.POST['secretkey']),
                'datatemptotal': querytotaldetail(data_table['str_detailtemp'], request.POST['secretkey']),
            }

            data = {
                'datatable': render_to_string('acctentry/datatable.html', context),
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


@csrf_exempt
def approve(request):
    if request.method == 'POST':
        of_for_approval = Ofmain.objects.get(pk=request.POST['ofid'])
        if request.user.has_perm('operationalfund.approve_allof') or \
                request.user.has_perm('operationalfund.approve_assignedof'):
            if request.user.has_perm('operationalfund.approve_allof') or \
                    (request.user.has_perm('operationalfund.approve_assignedof') and
                     of_for_approval.designatedapprover == request.user):
                if of_for_approval.ofstatus != 'I' and of_for_approval.ofstatus != 'R':
                    of_for_approval.ofstatus = request.POST['response']
                    of_for_approval.isdeleted = 0
                    if request.POST['response'] == 'D':
                        of_for_approval.status = 'C'
                    else:
                        of_for_approval.status = 'A'
                    of_for_approval.approverresponse = request.POST['response']
                    of_for_approval.responsedate = datetime.datetime.now()
                    of_for_approval.actualapprover = User.objects.get(pk=request.user.id)
                    of_for_approval.save()
                    data = {
                        'status': 'success',
                        'ofnum': of_for_approval.ofnum,
                        'newofstatus': of_for_approval.get_ofstatus_display(),
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
def releaseof(request):
    if request.method == 'POST':
        offorrelease = Ofmain.objects.get(ofnum=request.POST['ofnum'])
        offorrelease.releaseby = request.user
        offorrelease.releasedate = request.POST['ofreleasedon']
        offorrelease.paymentreceivedby = Employee.objects.get(pk=request.POST['ofreleasedto'])
        offorrelease.paymentreceiveddate = request.POST['ofreleasedon']
        offorrelease.ofstatus = 'R'
        offorrelease.save()
        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)
