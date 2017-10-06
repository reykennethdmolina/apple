from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from ataxcode.models import Ataxcode
from branch.models import Branch
from chartofaccount.models import Chartofaccount
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
from easy_pdf.views import PDFTemplateView
import json
from pprint import pprint
from utils.mixins import ReportContentMixin
from django.utils.dateformat import DateFormat
from django.contrib.humanize.templatetags.humanize import intcomma
import decimal


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
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        # data for lookup

        return context


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Ofmain
    template_name = 'operationalfund/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('description')
        context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('description')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['user'] = User.objects.filter(is_active=1).order_by('first_name')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Ofmain
    template_name = 'operationalfund/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "OPERATIONAL FUND"
        context['rc_title'] = "OPERATIONAL FUND"

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
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        # data for lookup

        # requested items
        context['itemtemp'] = Ofitem.objects.filter(ofmain=self.object.pk, isdeleted=0).order_by('item_counter')

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

        total_amount = Ofitemtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
            aggregate(Sum('amount'))
        print total_amount['amount__sum']
        if Oftype.objects.get(pk=int(self.request.POST['oftype'])).code != 'PCV' or \
                total_amount['amount__sum'] <= 1000.00:
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
            return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/userupdate/')
        else:
            return HttpResponseRedirect('/operationalfund/usercreate/')


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
    fields = ['ofdate', 'oftype', 'requestor', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        # if not request.user.has_perm('operationalfund.change_ofmain') or self.object.isdeleted == 1 or \
        #         request.user.has_perm('operationalfund.is_cashier'):
        #     if not request.user.username == 'admin':
        # elif request.user.has_perm('operationalfund.is_cashier'):  ---> put before elif if needed
        if not request.user.has_perm('operationalfund.change_ofmain'):
            raise Http404
        # elif self.object.ofstatus != 'F' and self.object.ofstatus != 'D' and request.user.username != 'admin':
        #     raise Http404
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
            detail.supplier = data.supplier.id if data.supplier else None
            detail.supplier_code = data.supplier_code
            detail.supplier_name = data.supplier_name
            detail.tin = data.tin
            detail.amount = data.amount
            detail.particulars = data.particulars
            detail.refnum = data.refnum
            detail.vat = data.vat_id
            detail.vatrate = data.vatrate
            detail.inputvattype = data.inputvattype_id
            detail.deferredvat = data.deferredvat
            detail.currency = data.currency_id
            detail.atc = data.atc_id
            detail.atcrate = data.atcrate
            detail.fxrate = data.fxrate
            detail.remarks = data.remarks
            detail.periodfrom = data.periodfrom
            detail.periodto = data.periodto
            detail.ofitemstatus = data.ofitemstatus
            detail.save()
            # requested items end

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['ofnum'] = self.object.ofnum
        context['amount'] = self.object.amount
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

        # requested items
        context['itemtemp'] = Ofitemtemp.objects.filter(ofmain=self.object.pk, isdeleted=0,
                                                        secretkey=self.mysecretkey).order_by('item_counter')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        total_amount = Ofitemtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).aggregate(
            Sum('amount'))
        print total_amount['amount__sum']
        if Oftype.objects.get(pk=int(self.request.POST['oftype'])).code != 'PCV' or \
                total_amount['amount__sum'] < 1000.00:
            if self.object.ofstatus != 'A' and self.object.ofstatus != 'I' and self.object.ofstatus != 'R':
                self.object.modifyby = self.request.user
                self.object.modifydate = datetime.datetime.now()

                # ----------------- START save ofitemtemp to ofitem START ---------------------
                Ofitem.objects.filter(ofmain=self.object.pk, isdeleted=0).update(isdeleted=2)

                itemtemp = Ofitemtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
                    order_by('item_counter')
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

                Ofitem.objects.filter(ofmain=self.object.pk, isdeleted=2).delete()
                # ----------------- END save ofitemtemp to ofitem END ---------------------

                self.object.amount = totalamount
                self.object.save(update_fields=['ofdate', 'amount', 'particulars', 'designatedapprover',
                                                'modifyby', 'modifydate'])

        return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/userupdate')


@method_decorator(login_required, name='dispatch')
class UpdateViewCashier(UpdateView):
    model = Ofmain
    template_name = 'operationalfund/cashierupdate.html'
    fields = ['ofdate', 'oftype', 'amount', 'refnum', 'particulars', 'creditterm', 'ofstatus', 'department',
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
            if self.object.oftype is None or self.object.creditterm is None:
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
            detail.supplier = data.supplier.id if data.supplier else None
            detail.supplier_code = data.supplier_code
            detail.supplier_name = data.supplier_name
            detail.tin = data.tin
            detail.amount = data.amount
            detail.particulars = data.particulars
            detail.refnum = data.refnum
            detail.vat = data.vat_id
            detail.vatrate = data.vatrate
            detail.inputvattype = data.inputvattype_id
            detail.deferredvat = data.deferredvat
            detail.currency = data.currency_id
            detail.atc = data.atc_id
            detail.atcrate = data.atcrate
            detail.fxrate = data.fxrate
            detail.remarks = data.remarks
            detail.periodfrom = data.periodfrom
            detail.periodto = data.periodto
            detail.ofitemstatus = data.ofitemstatus
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
            detail.ofitem = drow.ofitem_id
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
        context['ofnum'] = self.object.ofnum
        context['savedoftype'] = self.object.oftype.code
        context['actualapprover'] = User.objects.get(pk=self.object.actualapprover.id).first_name + ' ' + \
            User.objects.get(pk=self.object.actualapprover.id).last_name
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['originalofstatus'] = 'A' if self.object.creditterm is None else Ofmain.objects.get(pk=self.object.id).ofstatus
        context['requestor'] = User.objects.filter(pk=self.object.requestor.id)
        context['requestordepartment'] = Department.objects.filter(pk=self.object.department.id).order_by('departmentname')

        # for PCVs
        context['pcv_requested'] = 'False' if self.object.reppcvmain is None else 'True'
        context['reppcvnum'] = self.object.reppcvmain.reppcvnum if self.object.reppcvmain else 'N/A'
        context['reppcvdate'] = self.object.reppcvmain.reppcvdate if self.object.reppcvmain else 'N/A'
        context['pcv_replenished'] = 'False' if self.object.cvmain is None else 'True'
        context['cvnum'] = self.object.cvmain.cvnum if self.object.cvmain else 'N/A'
        context['cvdate'] = self.object.cvmain.cvdate if self.object.cvmain else 'N/A'
        # for PCVs

        # for RFVs
        context['rfv_requested'] = 'False' if self.object.reprfvmain is None else 'True'
        context['reprfvnum'] = self.object.reprfvmain.reprfvnum if self.object.reprfvmain else 'N/A'
        context['reprfvdate'] = self.object.reprfvmain.reprfvdate if self.object.reprfvmain else 'N/A'
        context['rfv_replenished'] = 'False' if self.object.apmain is None else 'True'
        context['apnum'] = self.object.apmain.apnum if self.object.apmain else 'N/A'
        context['apdate'] = self.object.apmain.apdate if self.object.apmain else 'N/A'
        # for RFVs

        # for CSVs
        context['csv_replenished'] = 'False' if self.object.jvmain is None else 'True'
        context['jvnum'] = self.object.jvmain.jvnum if self.object.jvmain else 'N/A'
        context['jvdate'] = self.object.jvmain.jvdate if self.object.jvmain else 'N/A'
        # for CSVs

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
        itemtemp = Ofitemtemp.objects.filter(ofmain=self.object.pk, isdeleted=0, secretkey=self.mysecretkey).\
            order_by('item_counter')

        payeedetails = []
        for data in itemtemp:
            payee = get_object_or_None(Supplier, pk=data.payee)
            print data.supplier_name
            if data.supplier and data.vatrate > 0:
                payeedetails.append({
                    'vat': '',
                    'atc': '',
                    'inputvattype': '',
                    'deferredvat': ''
                })
            else:
                payeedetails.append({
                    'vat': payee.vat_id if payee else '',
                    'atc': payee.atc_id if payee else '',
                    'inputvattype': payee.inputvattype_id if payee else '',
                    'deferredvat': payee.deferredvat if payee else ''
                })
        context['itemtempwithpayeedetails'] = zip(itemtemp, payeedetails)

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
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            # self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
            # self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
            # removed payee, payee_code, payee_name, department, employee, designatedapprover, amount
            self.object.save(update_fields=['refnum', 'particulars', 'creditterm', 'branch', 'ofstatus',
                                            'remarks', 'modifyby', 'modifydate'])

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

            # of items saving starts here..
            of_items_to_update = Ofitemtemp.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0,
                                                           ofmain=self.object.pk).order_by('item_counter')
            i = 0
            for of_item in of_items_to_update:
                update_item = Ofitem.objects.get(pk=of_item.ofitem)
                update_item.refnum = self.object.refnum  # main reference number
                update_item.deferredvat = self.request.POST.getlist('item_deferredvat')[i]
                update_item.fxrate = self.request.POST.getlist('item_fxrate')[i]
                update_item.remarks = self.request.POST.getlist('item_remarks')[i]
                update_item.periodfrom = self.request.POST.getlist('item_periodfrom')[i] if self.request.POST.\
                    getlist('item_periodfrom')[i] else None
                update_item.periodto = self.request.POST.getlist('item_periodto')[i] if self.request.POST.\
                    getlist('item_periodto')[i] else None
                if self.request.POST.getlist('item_currency')[i]:
                    update_item.currency = get_object_or_None(Currency, id=int(self.request.POST.
                                                                               getlist('item_currency')[i]))
                if self.request.POST.getlist('item_inputvattype')[i]:
                    update_item.inputvattype = get_object_or_None(Inputvattype, id=int(self.request.POST.
                                                                                       getlist('item_inputvattype')[i]))
                if self.request.POST.getlist('item_vat')[i]:
                    update_item.vat = get_object_or_None(Vat, id=int(self.request.POST.getlist('item_vat')[i]))
                    update_item.vatrate = Vat.objects.get(
                        pk=int(self.request.POST.getlist('item_vat')[i])).rate if Vat.objects.get(
                        pk=int(self.request.POST.getlist('item_vat')[i])) else None
                if self.request.POST.getlist('item_atc')[i]:
                    update_item.atc = get_object_or_None(Ataxcode, id=int(self.request.POST.getlist('item_atc')[i]))
                    update_item.atcrate = Ataxcode.objects.get(
                        pk=int(self.request.POST.getlist('item_atc')[i])).rate if Ataxcode.objects.get(
                        pk=int(self.request.POST.getlist('item_atc')[i])) else None
                if self.request.POST.getlist('item_supplier')[i]:
                    update_item.supplier = get_object_or_None(Supplier, id=int(self.request.POST.getlist('item_supplier')[i]))
                    update_item.supplier_code = Supplier.objects.get(
                        pk=int(self.request.POST.getlist('item_supplier')[i])).code if Supplier.objects.get(
                        pk=int(self.request.POST.getlist('item_supplier')[i])) else None
                    update_item.supplier_name = Supplier.objects.get(
                        pk=int(self.request.POST.getlist('item_supplier')[i])).name if Supplier.objects.get(
                        pk=int(self.request.POST.getlist('item_supplier')[i])) else None
                else:
                    update_item.supplier = None
                    update_item.supplier_code = None
                    update_item.supplier_name = None
                if self.request.POST.getlist('item_tin')[i]:
                    update_item.tin = self.request.POST.getlist('item_tin')[i]
                else:
                    update_item.tin = None
                update_item.ofitemstatus = self.request.POST.getlist('item_status')[i]
                update_item.modifyby = self.request.user
                update_item.modifydate = datetime.datetime.now()
                update_item.save()
                i += 1

            # accounting entry starts here..
            source = 'ofdetailtemp'
            mainid = self.object.id
            num = self.object.ofnum
            secretkey = self.request.POST['secretkey']
            updatedetail(source, mainid, num, secretkey, self.request.user)

            # saved_ofdetail = Ofdetail.objects.filter(ofmain=self.object.pk)

            # update approved amount in of main
            approved_amount = Ofitem.objects.filter(isdeleted=0, ofmain=self.object,
                                                    ofitemstatus='A').aggregate(Sum('amount'))
            self.object.approvedamount = approved_amount['amount__sum']
            self.object.save(update_fields=['approvedamount'])

        else:
            if self.object.reppcvmain is None:
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

                # items remarks save
                of_items_to_update = Ofitemtemp.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0,
                                                               ofmain=self.object.pk).order_by('item_counter')
                i = 0
                for of_item in of_items_to_update:
                    update_item = Ofitem.objects.get(pk=of_item.ofitem)
                    update_item.remarks = self.request.POST.getlist('item_remarks')[i]
                    update_item.modifyby = self.request.user
                    update_item.modifydate = datetime.datetime.now()
                    update_item.save()
                    i += 1

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


@method_decorator(login_required, name='dispatch')
class UserPdf(PDFTemplateView):
    model = Ofmain
    template_name = 'operationalfund/userpdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['ofmain'] = Ofmain.objects.get(Q(pk=self.kwargs['pk']), Q(isdeleted=0), (Q(status='A') | Q(status='C')))
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['items'] = Ofitem.objects.filter(ofmain=self.kwargs['pk'], isdeleted=0).order_by('item_counter')

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedof = Ofmain.objects.get(Q(pk=self.kwargs['pk']), Q(isdeleted=0), (Q(status='A') | Q(status='C')))
        printedof.print_ctr1 += 1
        printedof.save()
        return context


@method_decorator(login_required, name='dispatch')
class CashierPdf(PDFTemplateView):
    model = Ofmain
    template_name = 'operationalfund/cashierpdf.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.has_perm('operationalfund.is_cashier'):
            raise Http404
        return super(PDFTemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['ofmain'] = Ofmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['approveditems'] = Ofitem.objects.filter(ofmain=self.kwargs['pk'], isdeleted=0, ofitemstatus='A').\
            order_by('item_counter')
        context['detail'] = Ofdetail.objects.filter(isdeleted=0). \
            filter(ofmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Ofdetail.objects.filter(isdeleted=0). \
            filter(ofmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Ofdetail.objects.filter(isdeleted=0). \
            filter(ofmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedof = Ofmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedof.print_ctr2 += 1
        printedof.save()
        return context


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
def updateitemtemp(request):
    if request.method == 'POST':
        items = json.loads(request.POST['temp_items'])

        item_zip = zip(items[0]['id'], items[0]['vat'], items[0]['atc'], items[0]['inputvattype'],
                       items[0]['deferredvat'], items[0]['remarks'], items[0]['currency'], items[0]['fxrate'],
                       items[0]['itemstatus'], items[0]['supplier'], items[0]['tin'])

        for z_id, z_vat, z_atc, z_inputvattype, z_deferredvat, z_remarks, z_currency, z_fxrate, z_itemstatus, \
                z_supplier, z_tin in item_zip:
            item_to_update = Ofitemtemp.objects.get(pk=z_id)
            item_to_update.vat = int(z_vat) if z_vat else None
            item_to_update.vatrate = Vat.objects.get(pk=int(z_vat)).rate if z_vat else None
            item_to_update.atc = int(z_atc) if z_atc else None
            item_to_update.atcrate = Ataxcode.objects.get(pk=int(z_atc)).rate if z_atc else None
            item_to_update.inputvattype = int(z_inputvattype) if z_inputvattype else None
            item_to_update.deferredvat = z_deferredvat
            item_to_update.remarks = z_remarks
            item_to_update.currency = int(z_currency) if z_currency else None
            item_to_update.fxrate = float(z_fxrate) if z_fxrate else None
            item_to_update.ofitemstatus = z_itemstatus
            item_to_update.supplier = int(z_supplier) if z_supplier else None
            item_to_update.supplier_code = Supplier.objects.get(pk=int(z_supplier)).code if z_supplier else None
            item_to_update.supplier_name = Supplier.objects.get(pk=int(z_supplier)).name if z_supplier else None
            item_to_update.tin = z_tin
            item_to_update.modifyby = request.user
            item_to_update.modifydate = datetime.datetime.now()
            item_to_update.save()

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
        # set isdeleted=2 for existing detailtemp data

        main = Ofmain.objects.get(ofnum=request.POST['ofnum'])
        items = Ofitemtemp.objects.filter(isdeleted=0, secretkey=request.POST['secretkey'], ofitemstatus='A').\
            order_by('item_counter')
        item_counter = 1
        total_amount = 0

        # START-------------------- Operational Fund Automatic Entries ----------------------START
        # Entries:
        #   1. DEBIT Entries: Chart of Account based on OF Subtype containing gross amount and
        #       Chart of Account based on VAT containing VAT amount
        #   2. CREDIT Entry: Chart of Account based on OF Type
        #
        # DEBIT Entries:
        #   - Loop through the approved items in OFITEMTEMP
        #   - Create new Ofdetailtemp() object
        #   - Get the Requestor's Department
        #   - Get the Expense Chart of Account of Department
        #   - Get the Debit Chart of Account of the selected OF Subtype which has the Account Code that matches the
        #       first two characters of the Account Code of the Department's Chart of Account
        #   - Debit Amount = amount of the item * (1 + vatrate/100)
        #   - Increment item_counter
        #   - Save Ofdetailtemp()
        #   - Create new Ofdetailtemp() object
        #   - Get the Input VAT Chart of Account from the Parameter table
        #   - Input VAT = first Input VAT entry that matches the Input VAT Type of the item
        #   - Debit Amount = VAT amount (amount * vatrate/100)
        #   - Increment item_counter
        #   - Save Ofdetailtemp()
        #   - Compute total_amount
        #
        # CREDIT Entry:
        #   - Get the Credit Chart of Account of the selected OF Type
        #   - Bank Account = assigned bank account of the selected branch
        #   - Credit Amount = total_amount
        #
        # ######## START----------- DEBIT entries ------------START
        department_expchartofaccount_accountcode_prefix = str(Chartofaccount.objects.get(pk=Department.objects.get(
            pk=main.department.id).expchartofaccount_id).accountcode)[:2]
        for data in items:
            if str(Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpcostofsale.
                    accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                debit_chartofaccount = Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpcostofsale.id
            elif str(Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpgenandadmin.
                     accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                debit_chartofaccount = Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpgenandadmin.id
            elif str(Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpsellexp.
                     accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                debit_chartofaccount = Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpsellexp.id
            else:
                debit_chartofaccount = Ofsubtype.objects.get(pk=data.ofsubtype.id).chartexpcostofsale.id
            ofdetailtemp1 = Ofdetailtemp()
            ofdetailtemp1.item_counter = item_counter
            ofdetailtemp1.of_date = main.ofdate
            ofdetailtemp1.ofitem = data.ofitem
            ofdetailtemp1.secretkey = request.POST['secretkey']
            ofdetailtemp1.chartofaccount = debit_chartofaccount
            gross_amount = float(data.amount) / (1 + (float(data.vatrate) / 100.0))
            ofdetailtemp1.debitamount = gross_amount
            ofdetailtemp1.balancecode = 'D'
            ofdetailtemp1.enterby = request.user
            ofdetailtemp1.modifyby = request.user
            ofdetailtemp1.save()
            chart_of_account1 = Chartofaccount.objects.get(pk=debit_chartofaccount)
            getacctgentrydetails(chart_of_account1, ofdetailtemp1, data, int(request.POST['branch']),
                                 int(request.POST['department']), int(request.POST['employee']))
            item_counter += 1

            ofdetailtemp2 = Ofdetailtemp()
            ofdetailtemp2.item_counter = item_counter
            ofdetailtemp2.of_date = main.ofdate
            ofdetailtemp2.ofitem = data.ofitem
            ofdetailtemp2.secretkey = request.POST['secretkey']
            ofdetailtemp2.chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat_id
            ofdetailtemp2.debitamount = gross_amount * (float(data.vatrate) / 100.0)
            ofdetailtemp2.balancecode = 'D'
            ofdetailtemp2.enterby = request.user
            ofdetailtemp2.modifyby = request.user
            ofdetailtemp2.save()
            chart_of_account2 = Chartofaccount.objects.get(pk=Companyparameter.objects.get(code='PDI').coa_inputvat_id)
            getacctgentrydetails(chart_of_account2, ofdetailtemp2, data, int(request.POST['branch']),
                                 int(request.POST['department']), int(request.POST['employee']))
            item_counter += 1

            total_amount += data.amount
        # ######## END----------- DEBIT entries ------------END
        #
        # ######## START----------- CREDIT entry ------------START
        ofdetailtemp3 = Ofdetailtemp()
        ofdetailtemp3.item_counter = item_counter
        ofdetailtemp3.of_date = main.ofdate
        ofdetailtemp3.secretkey = request.POST['secretkey']
        ofdetailtemp3.chartofaccount = Oftype.objects.get(pk=int(request.POST['oftype'])).creditchartofaccount_id
        ofdetailtemp3.creditamount = float(total_amount)
        ofdetailtemp3.balancecode = 'C'
        ofdetailtemp3.enterby = request.user
        ofdetailtemp3.modifyby = request.user
        ofdetailtemp3.save()
        chart_of_account3 = Chartofaccount.objects.get(pk=Oftype.objects.get(pk=int(request.POST['oftype'])).
                                                       creditchartofaccount_id)
        getacctgentrydetails(chart_of_account3, ofdetailtemp3, data, int(request.POST['branch']),
                             int(request.POST['department']), int(request.POST['employee']))
        # ######## END----------- CREDIT entry ------------END
        # END-------------------- Operational Fund Automatic Entries ----------------------END

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


@csrf_exempt
def getacctgentrydetails(chartofaccount, ofdetailtemp, ofitemtemp, branch, department, employee):
    if chartofaccount.ataxcode_enable == 'Y':
        ofdetailtemp.ataxcode = ofitemtemp.atc
    if chartofaccount.bankaccount_enable == 'Y':
        ofdetailtemp.bankaccount = Branch.objects.get(pk=branch).bankaccount_id if Branch.objects.get(pk=branch).\
            bankaccount else Companyparameter.objects.get(code='PDI').def_bankaccount_id
    if chartofaccount.branch_enable == 'Y':
        ofdetailtemp.branch = branch
    if chartofaccount.customer_enable == 'Y':
        ofdetailtemp.customer = None
    if chartofaccount.department_enable == 'Y':
        ofdetailtemp.department = department
    if chartofaccount.employee_enable == 'Y':
        ofdetailtemp.employee = employee
    if chartofaccount.inputvat_enable == 'Y':
        ofdetailtemp.inputvat = Inputvat.objects.filter(inputvattype=ofitemtemp.inputvattype).first().id
    if chartofaccount.outputvat_enable == 'Y':
        ofdetailtemp.outputvat = None
    if chartofaccount.product_enable == 'Y':
        ofdetailtemp.product = None
    if chartofaccount.supplier_enable == 'Y':
        ofdetailtemp.supplier = ofitemtemp.supplier
    if chartofaccount.unit_enable == 'Y':
        ofdetailtemp.unit = None
    if chartofaccount.vat_enable == 'Y':
        ofdetailtemp.vat = ofitemtemp.vat
    if chartofaccount.wtax_enable == 'Y':
        ofdetailtemp.wtax = None

    ofdetailtemp.save()


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_total = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        report_type = "OF Summary"
        query = Ofmain.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ofnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofdate__lte=key_data)

        if request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name))
            query = query.filter(oftype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(branch=int(key_data))
        if request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name))
            query = query.filter(ofstatus=str(key_data))

        if request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name))
            query = query.filter(requestor=int(key_data))
        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(department=int(key_data))
        if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
            query = query.filter(Q(actualapprover=int(key_data)), Q(designatedapprover=int(key_data)))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        report_type = "OF Detailed"
        query = Ofitem.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofdate__lte=key_data)

        if request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name))
            query = query.filter(ofmain__oftype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(ofmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofstatus=str(key_data))

        if request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name))
            query = query.filter(ofmain__requestor=int(key_data))
        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(ofmain__department=int(key_data))
        if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
            query = query.filter(Q(ofmain__actualapprover=int(key_data)), Q(ofmain__designatedapprover=int(key_data)))

        if request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name))
            query = query.filter(ofsubtype=int(key_data))
        if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
            query = query.filter(Q(payee_code__icontains=key_data) | Q(payee_name__icontains=key_data)
                                 | Q(supplier_code__icontains=key_data) | Q(supplier_name__icontains=key_data))
        if request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name))
            query = query.filter(ofitemstatus=str(key_data))
        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(vat=int(key_data))
        if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
            query = query.filter(inputvattype=int(key_data))
        if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
            query = query.filter(atc=int(key_data))
        if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
            query = query.filter(deferredvat=str(key_data))

        if request.COOKIES.get('rep_f_order2_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order2_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        query = Ofdetail.objects.all().filter(isdeleted=0)

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
            query = query.filter(ofmain__ofnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofdate__lte=key_data)

        if request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_oftype_' + request.resolver_match.app_name))
            query = query.filter(ofmain__oftype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(ofmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ofstatus_' + request.resolver_match.app_name))
            query = query.filter(ofmain__ofstatus=str(key_data))

        if request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_employee_' + request.resolver_match.app_name))
            query = query.filter(ofmain__requestor=int(key_data))
        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(ofmain__department=int(key_data))
        if request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_approver_' + request.resolver_match.app_name))
            query = query.filter(Q(ofmain__actualapprover=int(key_data)), Q(designatedapprover=int(key_data)))

        if request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_subtype_' + request.resolver_match.app_name))
            query = query.filter(ofitem__ofsubtype=int(key_data))
        if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
            query = query.filter(Q(ofitem__payee_code__icontains=key_data) | Q(ofitem__payee_name__icontains=key_data)
                                 | Q(supplier__code__icontains=key_data) | Q(supplier__name__icontains=key_data))
        if request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_itemstatus_' + request.resolver_match.app_name))
            query = query.filter(ofitem__ofitemstatus=str(key_data))
        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(ofitem__vat=int(key_data))
        if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
            query = query.filter(ofitem__inputvattype=int(key_data))
        if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
            query = query.filter(ofitem__atc=int(key_data))
        if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
            query = query.filter(ofitem__deferredvat=str(key_data))

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "OF Acctg Entry - Summary"

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
            report_type = "OF Acctg Entry - Detailed"

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
                                                                                     'of_num')

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

        report_total = query.aggregate(Sum('amount'))\

    return query, report_type, report_total


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
    queryset, report_type, report_total = reportresultquery(request)
    report_type = report_type if report_type != '' else 'OF Report'
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
        amount_placement = 4
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        amount_placement = 9
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 14
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        amount_placement = 15

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'OF Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Requestor', bold)
        worksheet.write('D1', 'Status', bold)
        worksheet.write('E1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.write('A1', 'OF Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Requestor', bold)
        worksheet.write('D1', 'Subtype', bold)
        worksheet.write('E1', 'Payee', bold)
        worksheet.write('F1', 'VAT', bold)
        worksheet.write('G1', 'ATC', bold)
        worksheet.write('H1', 'In/VAT', bold)
        worksheet.write('I1', 'Status', bold)
        worksheet.write('J1', 'Amount', bold_right)
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
        worksheet.merge_range('B1:M1', 'Details', bold_center)
        worksheet.merge_range('N1:N2', 'Payee', bold)
        worksheet.merge_range('O1:O2', 'Date', bold)
        worksheet.merge_range('P1:P2', 'Debit', bold_right)
        worksheet.merge_range('Q1:Q2', 'Credit', bold_right)
        worksheet.write('B2', 'Bank Account', bold)
        worksheet.write('C2', 'Department', bold)
        worksheet.write('D2', 'Employee', bold)
        worksheet.write('E2', 'Customer', bold)
        worksheet.write('F2', 'Unit', bold)
        worksheet.write('G2', 'Branch', bold)
        worksheet.write('H2', 'Product', bold)
        worksheet.write('I2', 'Input VAT', bold)
        worksheet.write('J2', 'Output VAT', bold)
        worksheet.write('K2', 'VAT', bold)
        worksheet.write('L2', 'WTAX', bold)
        worksheet.write('M2', 'ATAX Code', bold)
        row += 1

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            data = [
                "OF-" + obj.oftype.code + "-" + obj.ofnum,
                DateFormat(obj.ofdate).format('Y-m-d'),
                obj.requestor.first_name + " " + obj.requestor.last_name,
                obj.get_ofstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            str_payee = obj.supplier_name if obj.supplier_name is not None else obj.payee_name
            str_atc = obj.atc.code if obj.atc else ''
            str_vat = obj.vat.code if obj.vat else ''
            str_inputvattype = obj.inputvattype.code if obj.inputvattype else ''

            data = [
                "OF-" + obj.ofmain.oftype.code + "-" + obj.ofmain.ofnum,
                DateFormat(obj.ofdate).format('Y-m-d'),
                obj.ofmain.requestor.first_name + " " + obj.ofmain.requestor.last_name,
                obj.ofsubtype.code,
                str_payee.upper(),
                str_vat,
                str_atc,
                str_inputvattype,
                obj.get_ofitemstatus_display(),
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
            if obj.supplier is not None:
                str_payee = obj.supplier.name
            elif obj.ofitem is not None:
                if obj.ofitem.payee is not None:
                    str_payee = obj.ofitem.payee_name
                else:
                    str_payee = ''
            else:
                str_payee = ''

            data = [
                obj.chartofaccount.accountcode + " - " + obj.chartofaccount.description,
                obj.bankaccount.accountnumber if obj.bankaccount is not None else '',
                obj.department.departmentname if obj.department is not None else '',
                str_firstname + " " + str_lastname,
                obj.customer.name if obj.customer is not None else '',
                obj.unit.description if obj.unit is not None else '',
                obj.branch.description if obj.branch is not None else '',
                obj.product.description if obj.product is not None else '',
                obj.inputvat.description if obj.inputvat is not None else '',
                obj.outputvat.description if obj.outputvat is not None else '',
                obj.vat.description if obj.vat is not None else '',
                obj.wtax.description if obj.wtax is not None else '',
                obj.ataxcode.code if obj.ataxcode is not None else '',
                str_payee,
                DateFormat(obj.of_date).format('Y-m-d'),
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
            "", "", "",
            "Total", report_total['amount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        data = [
            "", "", "", "", "", "", "", "",
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
