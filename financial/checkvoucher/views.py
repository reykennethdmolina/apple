from django.views.generic import View, DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from accountspayable.models import Apmain, Apdetail
from ataxcode.models import Ataxcode
from bankaccount.models import Bankaccount
from bankbranchdisburse.models import Bankbranchdisburse
from branch.models import Branch
from companyparameter.models import Companyparameter
from currency.models import Currency
from inputvattype.models import Inputvattype
from cvtype.models import Cvtype
from cvsubtype.models import Cvsubtype
from operationalfund.models import Ofmain, Ofitem, Ofdetail
from processing_transaction.models import Apvcvtransaction
from replenish_pcv.models import Reppcvmain, Reppcvdetail
from companyparameter.models import Companyparameter
from module.models import Activitylogs
from supplier.models import Supplier
from vat.models import Vat
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from . models import Cvmain, Cvdetail, Cvdetailtemp, Cvdetailbreakdown, Cvdetailbreakdowntemp, Temp_digibanker, Cvupload
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail
from django.template.loader import render_to_string
from easy_pdf.views import PDFTemplateView
from dateutil.relativedelta import relativedelta
import datetime
from department.models import Department
from unit.models import Unit
from inputvat.models import Inputvat
from outputvat.models import Outputvat
from employee.models import Employee
from chartofaccount.models import Chartofaccount
from product.models import Product
from customer.models import Customer
from annoying.functions import get_object_or_None
from pprint import pprint
from django.utils.dateformat import DateFormat
from utils.mixins import ReportContentMixin
import datetime
from django.utils.dateformat import DateFormat
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from django.db import connection
from collections import namedtuple
import pandas as pd
import io
from django.shortcuts import render
import os
import xlsxwriter
import logging
from django.core.urlresolvers import reverse
from acctentry.views import generatekey
from num2words import num2words
from datetime import timedelta
from string import digits
from django.core.files.storage import FileSystemStorage


upload_directory = 'processing_or/imported_main/'
upload_d_directory = 'processing_or/imported_detail/'
upload_size = 3


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Cvmain
    template_name = 'checkvoucher/index.html'
    page_template = 'checkvoucher/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):

        if self.request.user.is_superuser:
            query = Cvmain.objects.all() #.filter(isdeleted=0)
        else:
            #user_employee = get_object_or_None(Employee, user=self.request.user)
            #query = Cvmain.objects.filter(designatedapprover=self.request.user.id) | Cvmain.objects.filter(enterby=self.request.user.id)
            query = Cvmain.objects.all()

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(cvnum__icontains=keysearch) |
                                 Q(cvdate__icontains=keysearch) |
                                 Q(payee_name__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        # data for lookup
        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        context['cvsubtype'] = Cvsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['designatedapprover'] = Employee.objects.filter(isdeleted=0, cv_approver=1).order_by('firstname')
        creator = Cvmain.objects.filter(isdeleted=0).values_list('enterby_id', flat=True)
        context['creator'] = User.objects.filter(id__in=set(creator)).order_by('first_name', 'last_name')
        context['pk'] = 0
        # data for lookup

        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Cvmain
    template_name = 'checkvoucher/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['detail'] = Cvdetail.objects.filter(isdeleted=0).\
            filter(cvmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Cvdetail.objects.filter(isdeleted=0).\
            filter(cvmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Cvdetail.objects.filter(isdeleted=0).\
            filter(cvmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['reppcvmain'] = Reppcvmain.objects.filter(isdeleted=0, cvmain=self.object.id).order_by('enterdate')
        cv_main_aggregate = Reppcvmain.objects.filter(isdeleted=0, cvmain=self.object.id).aggregate(Sum('amount'))
        context['reppcv_total_amount'] = cv_main_aggregate['amount__sum']

        # data for lookup
        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        context['cvsubtype'] = Cvsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['aptrans'] = Apvcvtransaction.objects.filter(cvmain_id=self.object.pk)
        context['pk'] = self.object.pk
        context['uploadlist'] = Cvupload.objects.filter(cvmain_id=self.object.pk).order_by('enterdate')

        # data for lookup

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Cvmain
    template_name = 'checkvoucher/create.html'
    fields = ['cvdate', 'cvtype', 'cvsubtype', 'amount', 'amountinwords', 'refnum', 'particulars', 'vat', 'atc', 'checknum', 'checkdate',
              'inputvattype', 'deferredvat', 'currency', 'fxrate', 'branch', 'bankaccount', 'disbursingbranch',
              'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('checkvoucher.add_cvmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['designatedapprover'] = Employee.objects.filter(isdeleted=0, cv_approver=1).order_by('firstname')#User.objects.filter(is_active=1).order_by('first_name')
        context['reppcvmain'] = Reppcvmain.objects.filter(isdeleted=0, cvmain=None).order_by('enterdate')
        context['parameter'] = Companyparameter.objects.values_list('code', 'enable_manual_cv').get(code='PDI',isdeleted=0,status='A')
        # data for lookup
        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        context['cvsubtype'] = Cvsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        # context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        # data for lookup

        closetransaction = Companyparameter.objects.all().first().last_closed_date
        validtransaction = closetransaction + relativedelta(months=1)
        context['validtransaction'] = validtransaction

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        year = str(form.cleaned_data['cvdate'].year)
        yearqs = Cvmain.objects.filter(cvnum__startswith=year)

        if yearqs:
            cvnumlast = yearqs.latest('cvnum')
            latestcvnum = str(cvnumlast)
            print "latest: " + latestcvnum

            cvnum = year
            last = str(int(latestcvnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                cvnum += '0'
            cvnum += last

        else:
            cvnum = year + '000001'

        print 'cvnum: ' + cvnum
        print self.request.POST['payee']
        self.object.payee = Supplier.objects.get(pk=self.request.POST['payee'])
        self.object.payee_code = self.object.payee.code
        self.object.payee_name = self.object.payee.name

        self.object.cvnum = cvnum
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.cvstatus = 'F'
        self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
        self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate

        self.object.confi = self.request.POST.get('confi', 0)
        self.object.winvoice = self.request.POST.get('winvoice', 0)
        self.object.wor = self.request.POST.get('wor', 0)

        self.object.save()

        # accounting entry starts here..
        source = 'cvdetailtemp'
        mainid = self.object.id
        num = self.object.cvnum
        secretkey = self.request.POST['secretkey']
        cvmaindate = self.object.cvdate
        savedetail(source, mainid, num, secretkey, self.request.user, cvmaindate)

        # save cvmain in reppcvmain, reppcvdetail, ofmain
        for i in range(len(self.request.POST.getlist('pcv_checkbox'))):
            reppcvmain = Reppcvmain.objects.get(pk=int(self.request.POST.getlist('pcv_checkbox')[i]))
            reppcvmain.cvmain = self.object
            reppcvmain.save()
            reppcvdetail = Reppcvdetail.objects.filter(reppcvmain=reppcvmain)
            for data in reppcvdetail:
                data.cvmain = self.object
                data.save()
                ofmain = Ofmain.objects.get(reppcvdetail=data)
                ofmain.cvmain = self.object
                ofmain.save()
        # save cvmain in reppcvmain, reppcvdetail, ofmain

        return HttpResponseRedirect('/checkvoucher/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Cvmain
    template_name = 'checkvoucher/edit.html'
    fields = ['cvnum', 'cvdate', 'cvtype', 'cvsubtype', 'amount', 'amountinwords', 'refnum', 'particulars', 'vat', 'atc',
              'bankaccount', 'inputvattype', 'deferredvat', 'currency', 'fxrate', 'cvstatus', 'remarks',
              'branch', 'checknum', 'checkdate', 'ornum', 'vatrate', 'atcrate', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('checkvoucher.change_cvmain') or self.object.isdeleted == 1:
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # accounting entry starts here
    def get_initial(self):
        self.mysecretkey = generatekey(self)

        detailinfo = Cvdetail.objects.filter(cvmain=self.object.pk).order_by('item_counter')

        for drow in detailinfo:
            detail = Cvdetailtemp()
            detail.secretkey = self.mysecretkey
            detail.cv_num = drow.cv_num
            detail.cvmain = drow.cvmain_id
            detail.cvdetail = drow.pk
            detail.item_counter = drow.item_counter
            detail.cv_date = drow.cv_date
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

            breakinfo = Cvdetailbreakdown.objects.\
                filter(cvdetail_id=drow.id).order_by('pk', 'datatype')
            if breakinfo:
                for brow in breakinfo:
                    breakdown = Cvdetailbreakdowntemp()
                    breakdown.cv_num = drow.cv_num
                    breakdown.secretkey = self.mysecretkey
                    breakdown.cvmain = drow.cvmain_id
                    breakdown.cvdetail = drow.pk
                    breakdown.cvdetailtemp = detailtempid
                    breakdown.cvdetailbreakdown = brow.pk
                    breakdown.item_counter = brow.item_counter
                    breakdown.cv_date = brow.cv_date
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
        context['designatedapprover'] = Employee.objects.filter(isdeleted=0, cv_approver=1).order_by('firstname')#User.objects.filter(is_active=1).order_by('first_name')
        context['savedcvsubtype'] = Cvmain.objects.get(pk=self.object.id).cvsubtype.code
        # context['payee'] = Cvmain.objects.get(pk=self.object.id).payee.id if Cvmain.objects.get(
        #     pk=self.object.id).payee is not None else ''
        # context['payee_name'] = Cvmain.objects.get(pk=self.object.id).payee_name
        context['originalcvstatus'] = Cvmain.objects.get(pk=self.object.id).cvstatus
        context['actualapprover'] = None if Cvmain.objects.get(pk=self.object.id).actualapprover is None else Cvmain.objects.get(pk=self.object.id).actualapprover.id
        context['approverremarks'] = Cvmain.objects.get(pk=self.object.id).approverremarks
        context['responsedate'] = Cvmain.objects.get(pk=self.object.id).responsedate
        context['releaseby'] = Cvmain.objects.get(pk=self.object.id).releaseby
        context['releaseto'] = Cvmain.objects.get(pk=self.object.id).releaseto
        context['releasedate'] = Cvmain.objects.get(pk=self.object.id).releasedate
        context['reppcvmain'] = Reppcvmain.objects.filter(isdeleted=0, cvmain=self.object.id).order_by('enterdate')
        cv_main_aggregate = Reppcvmain.objects.filter(isdeleted=0, cvmain=self.object.id).aggregate(Sum('amount'))
        context['reppcv_total_amount'] = cv_main_aggregate['amount__sum']
        context['cvnum'] = self.object.cvnum
        context['confi'] = self.object.confi
        context['winvoice'] = self.object.winvoice
        context['wor'] = self.object.wor

        if self.request.POST.get('payee', False):
            context['payee'] = Supplier.objects.get(pk=self.request.POST['payee'], isdeleted=0)
        elif self.object.payee:
            context['payee'] = Supplier.objects.get(pk=self.object.payee.id, isdeleted=0)

        context['selectedcvsubtype'] = self.object.cvsubtype.code

        # data for lookup
        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        context['cvsubtype'] = Cvsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        # context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = self.object.pk
        # data for lookup

        # accounting entry starts here
        context['secretkey'] = self.mysecretkey
        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'cvdetailtemp',
            'tablebreakdowntemp': 'cvdetailbreakdowntemp',

            'datatemp': querystmtdetail('cvdetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('cvdetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        # accounting entry ends here
        # context['datainfo'] = self.object

        context['footers'] = [
            self.object.enterby.first_name + " " + self.object.enterby.last_name if self.object.enterby else '',
            self.object.enterdate,
            self.object.modifyby.first_name + " " + self.object.modifyby.last_name if self.object.modifyby else '',
            self.object.modifydate,
            self.object.postby.first_name + " " + self.object.postby.last_name if self.object.postby else '',
            self.object.postdate,
            self.object.closeby.first_name + " " + self.object.closeby.last_name if self.object.closeby else '',
            self.object.closedate,
        ]

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if self.request.POST['originalcvstatus'] != 'R':
            # if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
            self.object.payee = Supplier.objects.get(pk=self.request.POST['payee'])
            self.object.payee_code = self.object.payee.code
            self.object.payee_name = self.object.payee.name
            # else:
            #     self.object.payee = None
            #     self.object.payee_code = None
            #     self.object.payee_name = self.request.POST['payee']

            self.object.confi = self.request.POST.get('confi', 0)
            self.object.winvoice = self.request.POST.get('winvoice', 0)
            self.object.wor = self.request.POST.get('wor', 0)
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
            self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
            self.object.save(update_fields=['cvdate', 'cvtype', 'cvsubtype', 'amount', 'amountinwords', 'refnum',
                                            'particulars', 'vat', 'atc', 'bankaccount',
                                            'inputvattype', 'deferredvat', 'currency', 'fxrate', 'cvstatus', 'remarks',
                                            'branch', 'checknum', 'checkdate', 'ornum', 'vatrate', 'atcrate', 'payee',
                                            'payee_code', 'payee_name', 'modifyby', 'modifydate', 'confi', 'winvoice', 'wor'])

            if self.object.cvstatus == 'F':
                self.object.designatedapprover = User.objects.get(pk=self.request.POST['designatedapprover'])
                self.object.save(update_fields=['designatedapprover'])

            # revert status from APPROVED/DISAPPROVED to For Approval if no response date or approver response is saved
            # remove approval details if CVSTATUS is not APPROVED/DISAPPROVED
            if self.object.cvstatus == 'A' or self.object.cvstatus == 'D':
                if self.object.responsedate is None or self.object.approverresponse is None or \
                        self.object.actualapprover is None:
                    print self.object.responsedate
                    print self.object.approverresponse
                    print self.object.actualapprover
                    self.object.responsedate = None
                    self.object.approverremarks = None
                    self.object.approverresponse = None
                    self.object.actualapprover = None
                    self.object.cvstatus = 'F'
                    self.object.save(update_fields=['responsedate', 'approverremarks', 'approverresponse',
                                                    'actualapprover', 'cvstatus'])
            elif self.object.cvstatus == 'F':
                self.object.responsedate = None
                self.object.approverremarks = None
                self.object.approverresponse = None
                self.object.actualapprover = None
                self.object.save(update_fields=['responsedate', 'approverremarks', 'approverresponse',
                                                'actualapprover'])



            # revert status from RELEASED to Approved if no release date is saved
            # remove release details if CVSTATUS is not RELEASED
            if self.object.cvstatus == 'R' and self.object.releasedate is None:
                self.object.releaseby = None
                self.object.releaseto = None
                self.object.releasedate = None
                self.object.cvstatus = 'A'
                self.object.save(update_fields=['releaseby', 'releasedate', 'releaseto', 'cvstatus'])
            elif self.object.cvstatus != 'R':
                self.object.releaseby = None
                self.object.releaseto = None
                self.object.releasedate = None
                self.object.save(update_fields=['releaseby', 'releasedate', 'releaseto'])

            # accounting entry starts here..
            source = 'cvdetailtemp'
            mainid = self.object.id
            num = self.object.cvnum
            secretkey = self.request.POST['secretkey']
            cvmaindate = self.object.cvdate
            print cvmaindate

            updatedetail(source, mainid, num, secretkey, self.request.user, cvmaindate)
        else:
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['modifyby', 'modifydate', 'remarks'])

        # Save Activity Logs
        Activitylogs.objects.create(
            user_id=self.request.user.id,
            username=self.request.user,
            remarks='Update CV Transaction #' + self.object.cvnum
        )

        return HttpResponseRedirect('/checkvoucher/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Cvmain
    template_name = 'checkvoucher/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('checkvoucher.delete_cvmain') or self.object.status == 'O' \
                or self.object.cvstatus == 'A' or self.object.cvstatus == 'I' or self.object.cvstatus == 'R':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.cvstatus = 'D'
        self.object.save()

        # remove references in reppcvmain, reppcvdetail, ofmain
        reppcvmain = Reppcvmain.objects.filter(cvmain=self.object.id)
        for data in reppcvmain:
            data.cvmain = None
            data.save()

        reppcvdetail = Reppcvdetail.objects.filter(cvmain=self.object.id)
        for data in reppcvdetail:
            data.cvmain = None
            data.save()

        ofmain = Ofmain.objects.filter(cvmain=self.object.id)
        for data in ofmain:
            data.cvmain = None
            data.save()
        # remove references in reppcvmain, reppcvdetail, ofmain

        # remove references in APV tables
        apvcvtrans = Apvcvtransaction.objects.filter(cvmain=self.object)
        for data in apvcvtrans:
            apvmain = Apmain.objects.filter(pk=data.apmain.id).first()
            apvmain.cvamount -= data.cvamount
            apvmain.isfullycv = 0
            apvmain.save()
            data.delete()

        return HttpResponseRedirect('/checkvoucher')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Cvmain
    template_name = 'checkvoucher/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['cvmain'] = Cvmain.objects.get(pk=self.kwargs['pk'])
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['detail'] = Cvdetail.objects.filter(isdeleted=0). \
            filter(cvmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Cvdetail.objects.filter(isdeleted=0). \
            filter(cvmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Cvdetail.objects.filter(isdeleted=0). \
            filter(cvmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['reppcvmain'] = Reppcvmain.objects.filter(isdeleted=0, cvmain=self.kwargs['pk']).order_by('enterdate')
        cv_main_aggregate = Reppcvmain.objects.filter(isdeleted=0, cvmain=self.kwargs['pk']).aggregate(Sum('amount'))
        context['reppcv_total_amount'] = cv_main_aggregate['amount__sum']

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "https://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedcv = Cvmain.objects.get(pk=self.kwargs['pk'])
        printedcv.print_ctr += 1
        printedcv.save()
        return context


@method_decorator(login_required, name='dispatch')
class Voucher(PDFTemplateView):
    model = Cvmain
    template_name = 'checkvoucher/pdfvoucher.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['cvmain'] = Cvmain.objects.get(pk=self.kwargs['pk'])
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['detail'] = Cvdetail.objects.filter(isdeleted=0). \
            filter(cvmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Cvdetail.objects.filter(isdeleted=0). \
            filter(cvmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Cvdetail.objects.filter(isdeleted=0). \
            filter(cvmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['convertedamount'] = Cvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0).amount * Cvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0).fxrate

        context['reppcvmain'] = Reppcvmain.objects.filter(isdeleted=0, cvmain=self.kwargs['pk']).order_by(
            'enterdate')
        cv_main_aggregate = Reppcvmain.objects.filter(isdeleted=0, cvmain=self.kwargs['pk']).aggregate(
            Sum('amount'))
        context['reppcv_total_amount'] = cv_main_aggregate['amount__sum']

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedcv = Cvmain.objects.get(pk=self.kwargs['pk'])
        printedcv.print_ctr += 1
        printedcv.save()
        return context


@method_decorator(login_required, name='dispatch')
class PrePrintedVoucher(TemplateView):
    template_name = 'checkvoucher/preprintedvoucher.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        query = Cvdetail.objects.filter(isdeleted=0).filter(cvmain=self.kwargs['pk'])

        context['chart'] = query.order_by('-balancecode','chartofaccount')
        context['total'] = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        return context


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Cvmain
    template_name = 'checkvoucher/report/index.html'
    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('description')
        context['cvsubtype'] = Cvsubtype.objects.filter(isdeleted=0).order_by('description')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        # context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        # context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        # context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        # context['outputvat'] = Outputvat.objects.filter(isdeleted=0).order_by('code')
        #context['unit'] = Unit.objects.filter(isdeleted=0).order_by('code')
        #context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        #context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('code')
        #context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['user'] = User.objects.filter(is_active=1).order_by('first_name')
        creator = Cvmain.objects.filter(isdeleted=0).values_list('enterby_id', flat=True)
        context['creator'] = User.objects.filter(id__in=set(creator)).order_by('first_name', 'last_name')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultHtmlView(ListView):
    model = Ofmain
    template_name = 'checkvoucher/reportresulthtml.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['pcv'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "CHECK VOUCHER"
        context['rc_title'] = "CHECK VOUCHER"

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Cvmain
    template_name = 'checkvoucher/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['pcv'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "CHECK VOUCHER"
        context['rc_title'] = "CHECK VOUCHER"

        return context


# @csrf_exempt
# def approve(request):
#     if request.method == 'POST':
#         cv_for_approval = Cvmain.objects.get(cvnum=request.POST['cvnum'])
#         if request.user.has_perm('checkvoucher.approve_allcv') or \
#                 request.user.has_perm('checkvoucher.approve_assignedcv'):
#             if request.user.has_perm('checkvoucher.approve_allcv') or \
#                     (request.user.has_perm('checkvoucher.approve_assignedcv') and
#                         cv_for_approval.designatedapprover == request.user):
#                 if request.POST['originalcvstatus'] != 'R' or int(request.POST['backtoinprocess']) == 1:
#                     cv_for_approval.cvstatus = request.POST['approverresponse']
#                     cv_for_approval.isdeleted = 0
#                     if request.POST['approverresponse'] == 'D':
#                         cv_for_approval.status = 'C'
#                     else:
#                         cv_for_approval.status = 'A'
#                     cv_for_approval.approverresponse = request.POST['approverresponse']
#                     cv_for_approval.responsedate = request.POST['responsedate']
#                     cv_for_approval.actualapprover = User.objects.get(pk=request.user.id)
#                     cv_for_approval.approverremarks = request.POST['approverremarks']
#                     cv_for_approval.releaseby = None
#                     cv_for_approval.releaseto = None
#                     cv_for_approval.releasedate = None
#                     cv_for_approval.save()
#                     data = {
#                         'status': 'success',
#                         'cvnum': cv_for_approval.cvnum,
#                         'newcvstatus': cv_for_approval.cvstatus,
#                     }
#                 else:
#                     data = {
#                         'status': 'error',
#                     }
#             else:
#                 data = {
#                     'status': 'error',
#                 }
#         else:
#             data = {
#                 'status': 'error',
#             }
#     else:
#         data = {
#             'status': 'error',
#         }
#
#     return JsonResponse(data)

@csrf_exempt
def approve(request):

    if request.method == 'POST':

        approval = Cvmain.objects.get(pk=request.POST['id'])

        details = Cvdetail.objects.filter(cvmain_id=approval.id).order_by('item_counter')
        print details

        msg = ""
        msgchartname = ""
        msgchart = ""
        error = 0
        totalerror = 0
        for item in details:

            chartvalidate = Chartofaccount.objects.get(pk=item.chartofaccount_id)

            if chartvalidate.bankaccount_enable == 'Y':
                if item.bankaccount_id is None:
                    error += 1
                    msg += "Bank is Needed "

            if chartvalidate.department_enable == 'Y':
                if item.department_id is None:
                    error += 1
                    msg += "Department is Needed "
                ## check expense
                print chartvalidate.accountcode
                if chartvalidate.accountcode[0:1] == '5':
                    print "expense ako"
                    dept = Department.objects.get(pk=item.department_id)
                    deptchart = Chartofaccount.objects.filter(isdeleted=0, status='A',
                                                              pk=dept.expchartofaccount_id).first()

                    if chartvalidate.accountcode[0:2] != deptchart.accountcode[0:2]:
                        error += 1
                        msg += "Expense code did not match with the department code "

            if chartvalidate.supplier_enable == 'Y':

                print chartvalidate.setup_supplier
                if chartvalidate.setup_supplier is None:
                    if item.supplier_id is None:
                        error += 1
                        msg += "Supplier is Needed "

            if chartvalidate.customer_enable == 'Y':
                print chartvalidate.setup_customer
                if chartvalidate.setup_customer is None:
                    if item.customer_id is None:
                        error += 1
                        msg += "Customer is Needed "

            if chartvalidate.branch_enable == 'Y':
                if item.branch_id is None:
                    error += 1
                    msg += "Branch is Needed "

            if chartvalidate.unit_enable == 'Y':
                if item.unit_id is None:
                    error += 1
                    msg += "Unit is Needed "

            if chartvalidate.inputvat_enable == 'Y':
                if item.inputvat_id is None:
                    error += 1
                    msg += "Input VAT is Needed "

            if chartvalidate.outputvat_enable == 'Y':
                if item.outputvat_id is None:
                    error += 1
                    msg += "Output VAT is Needed "

            if chartvalidate.vat_enable == 'Y':
                if item.vat_id is None:
                    error += 1
                    msg += "VAT is Needed "

            if chartvalidate.wtax_enable == 'Y':
                if item.wtax_id is None:
                    error += 1
                    msg += "WTAX is Needed "

            if chartvalidate.ataxcode_enable == 'Y':
                if item.ataxcode_id is None:
                    error += 1
                    msg += "ATAX is Needed "

            totalerror += error
            if error > 0:
                msgchartname = " Chart of Account: " + str(chartvalidate) + " "
                ## Double Validation
                msgchart += str(msgchartname) + " " + str(msg)
                msg = ""
                msgchartname = ""
                error = 0
            # print error
            # print msg

        if totalerror > 0:
            data = {'status': 'error', 'msg': msgchart}
            return JsonResponse(data)
        else:
            if (approval.cvstatus != 'R' and approval.status != 'O'):
                approval.cvstatus = 'A'
                approval.responsedate = str(datetime.datetime.now())
                approval.approverremarks = str(approval.approverremarks) + ';' + 'Approved'
                approval.actualapprover = User.objects.get(pk=request.user.id)
                approval.save()
                data = {'status': 'success'}

                # Save Activity Logs
                Activitylogs.objects.create(
                    user_id=request.user.id,
                    username=request.user,
                    remarks='Aproved CV Transaction #' + str(approval.cvnum)
                )
            else:
                data = {'status': 'error'}

            return JsonResponse(data)

    else:
        data = { 'status': 'error' }

        return JsonResponse(data)


@csrf_exempt
def disapprove(request):
    if request.method == 'POST':
        approval = Cvmain.objects.get(pk=request.POST['id'])
        if (approval.cvstatus != 'R' and approval.status != 'O'):
            approval.cvstatus = 'D'
            approval.responsedate = str(datetime.datetime.now())
            approval.approverremarks = str(approval.approverremarks) +';'+ request.POST['reason']
            approval.actualapprover = User.objects.get(pk=request.user.id)
            approval.save()
            data = {'status': 'success'}

            # Save Activity Logs
            Activitylogs.objects.create(
                user_id=request.user.id,
                username=request.user,
                remarks='Disaproved CV Transaction #' + str(approval.cvnum)
            )
        else:
            data = {'status': 'error'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def posting(request):
    if request.method == 'POST':
        release = Cvmain.objects.filter(pk=request.POST['id']).update(cvstatus='R',releaseby=User.objects.get(pk=request.user.id),releasedate= str(datetime.datetime.now()))

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def gopost(request):

    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        release = Cvmain.objects.filter(pk__in=ids).update(cvstatus='R',releaseby=User.objects.get(pk=request.user.id),releasedate= str(datetime.datetime.now()))

        data = {'status': 'success'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def gounpost(request):
    if request.method == 'POST':
        approval = Cvmain.objects.get(pk=request.POST['id'])
        if (approval.cvstatus == 'R' and approval.status != 'O'):
            approval.cvstatus = 'A'
            approval.save()
            data = {'status': 'success'}

            # Save Activity Logs
            Activitylogs.objects.create(
                user_id=request.user.id,
                username=request.user,
                remarks='Unpost CV Transaction #' + str(approval.cvnum)
            )
        else:
            data = {'status': 'error'}
    else:
        data = { 'status': 'error' }

    return JsonResponse(data)

@csrf_exempt
def release(request):
    if request.method == 'POST':
        cv_for_release = Cvmain.objects.get(cvnum=request.POST['cvnum'])
        if cv_for_release.cvstatus != 'F' and cv_for_release.cvstatus != 'D':
            cv_for_release.releaseby = User.objects.get(pk=request.POST['releaseby'])
            cv_for_release.releaseto = request.POST['releaseto']
            cv_for_release.releasedate = request.POST['releasedate']
            cv_for_release.cvstatus = 'R'
            cv_for_release.save()
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


@csrf_exempt
def importreppcv(request):
    if request.method == 'POST':
        first_ofmain = Ofmain.objects.filter(reppcvmain=request.POST.getlist('checked_reppcvmain[]')[0], isdeleted=0,
                                             status='A').first()
        first_ofitem = Ofitem.objects.filter(ofmain=first_ofmain.id, isdeleted=0, status='A').first()

        ofdetail = Ofdetail.objects.filter(ofmain__reppcvmain__in=set(request.POST.getlist('checked_reppcvmain[]'))).\
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

        if 'cvnum' in request.POST:
            if request.POST['cvnum']:
                updateallquery(request.POST['table'], request.POST['cvnum'])
        # set isdeleted=2 for existing detailtemp data

        i = 1
        for detail in ofdetail:
            cvdetailtemp = Cvdetailtemp()
            cvdetailtemp.item_counter = i
            cvdetailtemp.secretkey = request.POST['secretkey']
            cvdetailtemp.cv_date = datetime.datetime.now()
            cvdetailtemp.chartofaccount = detail['chartofaccount__id']
            cvdetailtemp.bankaccount = detail['bankaccount__id']
            cvdetailtemp.department = detail['department__id']
            cvdetailtemp.employee = detail['employee__id']
            cvdetailtemp.supplier = detail['supplier__id']
            cvdetailtemp.customer = detail['customer__id']
            cvdetailtemp.unit = detail['unit__id']
            cvdetailtemp.branch = detail['branch__id']
            cvdetailtemp.product = detail['product__id']
            cvdetailtemp.inputvat = detail['inputvat__id']
            cvdetailtemp.outputvat = detail['outputvat__id']
            cvdetailtemp.vat = detail['vat__id']
            cvdetailtemp.wtax = detail['wtax__id']
            cvdetailtemp.ataxcode = detail['ataxcode__id']
            cvdetailtemp.debitamount = detail['debitamount__sum']
            cvdetailtemp.creditamount = detail['creditamount__sum']
            cvdetailtemp.balancecode = detail['balancecode']
            cvdetailtemp.enterby = request.user
            cvdetailtemp.modifyby = request.user
            cvdetailtemp.save()
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
            'branch': first_ofmain.branch_id,
            'vat': first_ofitem.vat_id,
            'atc': first_ofitem.atc_id,
            'inputvattype': first_ofitem.inputvattype_id,
            'deferredvat': first_ofitem.deferredvat
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def manualcvautoentry(request):
    # auto-entry for manually created CVs
    # credit side: CASH IN BANK (get from parameter file)
    #              Bank account: get from main; if none, get bank account of branch
    if request.method == 'POST':
        # set isdeleted=2 for existing detailtemp data
        data_table = validatetable(request.POST['table'])
        deleteallquery(request.POST['table'], request.POST['secretkey'])

        if 'cvnum' in request.POST:
            if request.POST['cvnum']:
                updateallquery(request.POST['table'], request.POST['cvnum'])
        # set isdeleted=2 for existing detailtemp data

        # insert Cash In Bank acctg entry in cvdetailtemp
        cvdetailtemp = Cvdetailtemp()
        cvdetailtemp.item_counter = 1
        cvdetailtemp.secretkey = request.POST['secretkey']
        cvdetailtemp.cv_date = datetime.datetime.now()
        cvdetailtemp.chartofaccount = Companyparameter.objects.get(code='PDI').coa_cashinbank.id
        if request.POST['bankaccount']:
            bank_account = int(request.POST['bankaccount'])
        elif request.POST['branch']:
            if Branch.objects.get(pk=int(request.POST['branch'])).bankaccount:
                bank_account = Branch.objects.get(pk=int(request.POST['branch'])).bankaccount.id
            else:
                bank_account = Companyparameter.objects.get(code='PDI').def_bankaccount.id
        else:
            bank_account = Companyparameter.objects.get(code='PDI').def_bankaccount.id
        cvdetailtemp.bankaccount = bank_account
        cvdetailtemp.creditamount = request.POST['amount'].replace(',', '')
        cvdetailtemp.balancecode = 'C'
        cvdetailtemp.enterby = request.user
        cvdetailtemp.modifyby = request.user
        cvdetailtemp.save()
        # insert Cash In Bank acctg entry in cvdetailtemp

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
def remanualcvautoentry(request):

    if request.method == 'POST':
        data_table = validatetable(request.POST['table'])
        #deleteallquery(request.POST['table'], request.POST['secretkey'])

        secretkey = request.POST['secretkey']
        bankaccount = request.POST['bankaccount']
        amount = request.POST['amount'].replace(',', '')
        #find cash in bank
        cashinbank = Companyparameter.objects.get(code='PDI').coa_cashinbank.id

        #find = Cvdetailtemp..objects.get(code='PDI')
        find = Cvdetailtemp.objects.filter(secretkey=secretkey,chartofaccount=30)

        for f in find:
            temp = Cvdetailtemp.objects.get(pk=f.id)
            temp.bankaccount = bankaccount
            if f.balancecode == 'D':
                temp.creditamount = amount
            else:
                temp.creditamount = amount

            temp.save()


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
def reportresultquery(request):
    query = ''
    report_type = ''
    report_xls = ''
    report_total = ''
    pcv = 'hide'

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's'\
       or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':

        if request.COOKIES.get('rep_f_cvsubtype_' + request.resolver_match.app_name):
            subtype = str(request.COOKIES.get('rep_f_cvsubtype_' + request.resolver_match.app_name))
        else:
            subtype = ''

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's'\
                or (request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd'
                    and (subtype == '' or subtype == '2')):
            if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
                report_type = "Check Voucher Detailed"
                report_xls = "CV Detailed"
            else:
                report_type = "Check Voucher Summary"
                report_xls = "CV Summary"

            query = Cvmain.objects.all().filter(isdeleted=0)

            if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
                query = query.filter(cvnum__gte=int(key_data))
            if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
                query = query.filter(cvnum__lte=int(key_data))

            if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
                query = query.filter(cvdate__gte=key_data)
            if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
                query = query.filter(cvdate__lte=key_data)

            if request.COOKIES.get('rep_f_cvtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_cvtype_' + request.resolver_match.app_name))
                query = query.filter(cvtype=int(key_data))
            if request.COOKIES.get('rep_f_cvsubtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_cvsubtype_' + request.resolver_match.app_name))
                query = query.filter(cvsubtype=int(key_data))
            if request.COOKIES.get('rep_f_cvstatus_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_cvstatus_' + request.resolver_match.app_name))
                query = query.filter(cvstatus=str(key_data))
            if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
                if key_data == 'P':
                    query = query.filter(postby__isnull=False)
                elif key_data == 'U':
                    query = query.filter(postby__isnull=True)
            if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
                query = query.filter(status=str(key_data))

            if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
                query = query.filter(branch=int(key_data))
            if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
                query = query.filter(Q(payee_code__icontains=key_data) | Q(payee_name__icontains=key_data))
            if request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name))
                query = query.filter(Q(checknum__icontains=key_data))
            if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
                query = query.filter(Q(refnum__icontains=key_data))
            if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
                query = query.filter(currency=int(key_data))

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
            if request.COOKIES.get('rep_f_bank_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_bank_' + request.resolver_match.app_name))
                query = query.filter(bankaccount=int(key_data))
            if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
                query = query.filter(disbursingbranch=int(key_data))
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
            report_type = "Check Voucher Detailed"
            report_xls = "CV Detailed"
            pcv = "show"

            query = Reppcvmain.objects.all().filter(isdeleted=0).exclude(cvmain__isnull=True)

            if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
                query = query.filter(cvmain__cvnum__gte=int(key_data))
            if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
                query = query.filter(cvmain__cvnum__lte=int(key_data))

            if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
                query = query.filter(cvmain__cvdate__gte=key_data)
            if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
                query = query.filter(cvmain__cvdate__lte=key_data)

            if request.COOKIES.get('rep_f_cvtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_cvtype_' + request.resolver_match.app_name))
                query = query.filter(cvmain__cvtype=int(key_data))
            if request.COOKIES.get('rep_f_cvsubtype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_cvsubtype_' + request.resolver_match.app_name))
                query = query.filter(cvmain__cvsubtype=int(key_data))
            if request.COOKIES.get('rep_f_cvstatus_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_cvstatus_' + request.resolver_match.app_name))
                query = query.filter(cvmain__cvstatus=str(key_data))
            if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
                if key_data == 'P':
                    query = query.filter(cvmain__postby__isnull=False)
                elif key_data == 'U':
                    query = query.filter(cvmain__postby__isnull=True)
            if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
                query = query.filter(cvmain__status=str(key_data))

            if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
                query = query.filter(cvmain__branch=int(key_data))
            if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
                query = query.filter(Q(cvmain__payee_code__icontains=key_data) | Q(cvmain__payee_name__icontains=key_data))
            if request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name))
                query = query.filter(Q(cvmain__checknum__icontains=key_data))
            if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
                query = query.filter(Q(cvmain__refnum__icontains=key_data))
            if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
                query = query.filter(cvmain__currency=int(key_data))

            if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
                query = query.filter(cvmain__vat=int(key_data))
            if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
                query = query.filter(cvmain__inputvattype=int(key_data))
            if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
                query = query.filter(cvmain__atc=int(key_data))
            if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
                query = query.filter(cvmain__deferredvat=str(key_data))
            if request.COOKIES.get('rep_f_bank_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_bank_' + request.resolver_match.app_name))
                query = query.filter(cvmain__bankaccount=int(key_data))
            if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
                query = query.filter(cvmain__disbursingbranch=int(key_data))

            if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
                query = query.filter(cvmain__amount__gte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
                query = query.filter(cvmain__amount__lte=float(key_data.replace(',', '')))
            if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
                key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    for n,data in enumerate(key_data):
                        key_data[n] = "cvmain__" + data
                    query = query.order_by(*key_data)
                else:
                    query = query.order_by('cvmain')

            report_total = query.values('cvmain').annotate(Sum('amount')).aggregate(Sum('cvmain__amount'))

        if request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name))
            if key_data == 'd':
                query = query.reverse()

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get(
                    'rep_f_report_' + request.resolver_match.app_name) == 'ae':
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub':
            report_type = "Check Voucher Unbalanced Entries"
            report_xls = "CV Unbalanced Entries"
        else:
            report_type = "Check Voucher All Entries"
            report_xls = "CV All Entries"

        query = Cvdetail.objects.filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvdate__lte=key_data)

        if request.COOKIES.get('rep_f_cvtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_cvtype_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvtype=int(key_data))
        if request.COOKIES.get('rep_f_cvsubtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_cvsubtype_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvsubtype=int(key_data))
        if request.COOKIES.get('rep_f_cvstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_cvstatus_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvstatus=str(key_data))
        if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
            if key_data == 'P':
                query = query.filter(cvmain__postby__isnull=False)
            elif key_data == 'U':
                query = query.filter(cvmain__postby__isnull=True)
        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            query = query.filter(cvmain__status=str(key_data))

        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(cvmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
            query = query.filter(cvmain__Q(payee_code__icontains=key_data) | Q(payee_name__icontains=key_data))
        if request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name))
            query = query.filter(cvmain__Q(checknum__icontains=key_data))
        if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
            query = query.filter(cvmain__Q(refnum__icontains=key_data))
        if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
            query = query.filter(cvmain__currency=int(key_data))

        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(cvmain__vat=int(key_data))
        if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
            query = query.filter(cvmain__inputvattype=int(key_data))
        if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
            query = query.filter(cvmain__atc=int(key_data))
        if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
            query = query.filter(cvmain__deferredvat=str(key_data))
        if request.COOKIES.get('rep_f_bank_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_bank_' + request.resolver_match.app_name))
            query = query.filter(cvmain__bankaccount=int(key_data))
        if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
            query = query.filter(cvmain__disbursingbranch=int(key_data))
        if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(cvmain__amount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
            query = query.filter(cvmain__amount__lte=float(key_data.replace(',', '')))
        query = query.values('cvmain__cvnum') \
            .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),
                      creditsum=Sum('creditamount')) \
            .values('cvmain__cvnum', 'margin', 'cvmain__cvdate', 'debitsum', 'creditsum', 'cvmain__pk').order_by(
            'cvmain__cvnum')

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
        query = Cvdetail.objects.all().filter(isdeleted=0)

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
            query = query.filter(cvmain__cvnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvdate__lte=key_data)

        if request.COOKIES.get('rep_f_cvtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_cvtype_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvtype=int(key_data))
        if request.COOKIES.get('rep_f_cvsubtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_cvsubtype_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvsubtype=int(key_data))
        if request.COOKIES.get('rep_f_cvstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_cvstatus_' + request.resolver_match.app_name))
            query = query.filter(cvmain__cvstatus=str(key_data))
        if request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_posted_' + request.resolver_match.app_name))
            if key_data == 'P':
                query = query.filter(cvmain__postby__isnull=False)
            elif key_data == 'U':
                query = query.filter(cvmain__postby__isnull=True)
        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            query = query.filter(cvmain__status=str(key_data))

        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(cvmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_payee_' + request.resolver_match.app_name))
            query = query.filter(Q(cvmain__payee_code__icontains=key_data) | Q(cvmain__payee_name__icontains=key_data))
        if request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_check_' + request.resolver_match.app_name))
            query = query.filter(Q(cvmain__checknum__icontains=key_data))
        if request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_ref_' + request.resolver_match.app_name))
            query = query.filter(Q(cvmain__refnum__icontains=key_data))
        if request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_currency_' + request.resolver_match.app_name))
            query = query.filter(cvmain__currency=int(key_data))

        if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
            query = query.filter(cvmain__vat=int(key_data))
        if request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inputvattype_' + request.resolver_match.app_name))
            query = query.filter(cvmain__inputvattype=int(key_data))
        if request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_atc_' + request.resolver_match.app_name))
            query = query.filter(cvmain__atc=int(key_data))
        if request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_deferred_' + request.resolver_match.app_name))
            query = query.filter(cvmain__deferredvat=str(key_data))
        if request.COOKIES.get('rep_f_bank_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_bank_' + request.resolver_match.app_name))
            query = query.filter(cvmain__bankaccount=int(key_data))
        if request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_disburse_' + request.resolver_match.app_name))
            query = query.filter(cvmain__disbursingbranch=int(key_data))

        if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(cvmain__amount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
            query = query.filter(cvmain__amount__lte=float(key_data.replace(',', '')))

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "Check Voucher Accounting Entry - Summary"
            report_xls = "CV Acctg Entry - Summary"

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
            report_type = "Check Voucher Accounting Entry - Detailed"
            report_xls = "CV Acctg Entry - Detailed"

            query = query.values('cv_num') \
                .annotate(Sum('debitamount'), Sum('creditamount')) \
                .values('cvmain__payee_name',
                        'cvmain__cvdate',
                        'cv_num',
                        'cvmain__payee__tin',
                        'cvmain__payee__address1',
                        'cvmain__payee__address2',
                        'cvmain__particulars',
                        'item_counter',
                        'chartofaccount__accountcode',
                        'chartofaccount__title',
                        'department__code',
                        'department__departmentname',
                        'debitamount__sum',
                        'creditamount__sum') \
                .order_by('cv_num',
                          'item_counter')\

    return query, report_type, report_total, pcv, report_xls

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
    queryset, report_type, report_total, pcv, report_xls = reportresultquery(request)
    report_type = report_type if report_type != '' else 'CV Report'
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
        amount_placement = 6
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        amount_placement = 13 if pcv == 'show' else 11
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        amount_placement = 2
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 4
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        amount_placement = 7

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'CV Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Type', bold)
        worksheet.write('D1', 'Subtype', bold)
        worksheet.write('E1', 'Payee', bold)
        worksheet.write('F1', 'Status', bold)
        worksheet.write('G1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        if pcv == 'show':
            worksheet.merge_range('A1:A2', 'CV Number', bold)
            worksheet.merge_range('B1:B2', 'Date', bold)
            worksheet.merge_range('C1:C2', 'Type', bold)
            worksheet.merge_range('D1:D2', 'Subtype', bold)
            worksheet.merge_range('E1:E2', 'Payee', bold)
            worksheet.merge_range('F1:F2', 'Check No.', bold)
            worksheet.merge_range('G1:G2', 'Check Date', bold)
            worksheet.merge_range('H1:H2', 'VAT', bold)
            worksheet.merge_range('I1:I2', 'ATC', bold)
            worksheet.merge_range('J1:J2', 'In/VAT', bold)
            worksheet.merge_range('K1:K2', 'Status', bold)
            worksheet.merge_range('L1:N1', 'Replenished PCV', bold_center)
            worksheet.merge_range('O1:O2', 'Amount', bold_right)
            worksheet.write('L2', 'Rep PCV Number', bold)
            worksheet.write('M2', 'Date', bold)
            worksheet.write('N2', 'Rep PCV Amount', bold_right)
            row += 1
        else:
            worksheet.write('A1', 'CV Number', bold)
            worksheet.write('B1', 'Date', bold)
            worksheet.write('C1', 'Type', bold)
            worksheet.write('D1', 'Subtype', bold)
            worksheet.write('E1', 'Payee', bold)
            worksheet.write('F1', 'Check No.', bold)
            worksheet.write('G1', 'Check Date', bold)
            worksheet.write('H1', 'VAT', bold)
            worksheet.write('I1', 'ATC', bold)
            worksheet.write('J1', 'In/VAT', bold)
            worksheet.write('K1', 'Status', bold)
            worksheet.write('L1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
        worksheet.write('A1', 'CV Number', bold)
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
        worksheet.merge_range('A1:C1', 'Check Voucher', bold_center)
        worksheet.merge_range('D1:D2', 'Account Number', bold_center)
        worksheet.merge_range('E1:E2', 'Account Title', bold_center)
        worksheet.merge_range('F1:F2', 'Dept. Code', bold_center)
        worksheet.merge_range('G1:G2', 'Dept. Name', bold_center)
        worksheet.merge_range('H1:H2', 'Debit', bold_right)
        worksheet.merge_range('I1:I2', 'Credit', bold_right)
        worksheet.write('A2', 'Date', bold)
        worksheet.write('B2', 'Number / Payee', bold)
        worksheet.write('C2', 'Particulars', bold)
        row += 1

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            data = [
                obj.cvnum,
                DateFormat(obj.cvdate).format('Y-m-d'),
                obj.cvtype.description if obj.cvtype else '',
                obj.cvsubtype.description if obj.cvsubtype else '',
                obj.payee_name,
                obj.get_cvstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            if pcv == 'show':
                data = [
                    obj.cvmain.cvnum,
                    DateFormat(obj.cvmain.cvdate).format('Y-m-d'),
                    obj.cvmain.cvtype.description if obj.cvmain.cvtype else '',
                    obj.cvmain.cvsubtype.description if obj.cvmain.cvsubtype else '',
                    obj.cvmain.payee_name,
                    obj.cvmain.checknum,
                    DateFormat(obj.cvmain.checkdate).format('Y-m-d'),
                    obj.cvmain.vat.code if obj.cvmain.vat else '',
                    obj.cvmain.atc.code if obj.cvmain.atc else '',
                    obj.cvmain.inputvattype.description if obj.cvmain.inputvattype else '',
                    obj.cvmain.get_cvstatus_display(),
                    'PCV-' + obj.reppcvnum,
                    DateFormat(obj.reppcvdate).format('Y-m-d'),
                    obj.amount,
                    obj.cvmain.amount,
                ]
            else:
                data = [
                    obj.cvnum,
                    DateFormat(obj.cvdate).format('Y-m-d'),
                    obj.cvtype.description if obj.cvtype else '',
                    obj.cvsubtype.description if obj.cvsubtype else '',
                    obj.payee_name,
                    obj.checknum,
                    DateFormat(obj.checkdate).format('Y-m-d'),
                    obj.vat.code if obj.vat else '',
                    obj.atc.code if obj.atc else '',
                    obj.inputvattype.description if obj.inputvattype else '',
                    obj.get_cvstatus_display(),
                    obj.amount,
                ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ub' or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'ae':
            data = [
                obj['cvmain__cvnum'],
                DateFormat(obj['cvmain__cvdate']).format('Y-m-d'),
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
            if obj['item_counter'] == 1:
                data = [
                    DateFormat(obj['cvmain__cvdate']).format('Y-m-d'),
                    obj['cv_num'] + ' ' + obj['cvmain__payee_name'],
                    obj['cvmain__particulars'],
                    obj['chartofaccount__accountcode'],
                    obj['chartofaccount__title'],
                    obj['department__code'],
                    obj['department__departmentname'],
                    obj['debitamount__sum'],
                    obj['creditamount__sum'],
                ]
            elif obj['item_counter'] == 2:
                data = [
                    ' ',
                    'TIN: ' + obj['cvmain__payee__tin'],
                    ' ',
                    obj['chartofaccount__accountcode'],
                    obj['chartofaccount__title'],
                    obj['department__code'],
                    obj['department__departmentname'],
                    obj['debitamount__sum'],
                    obj['creditamount__sum'],
                ]
            elif obj['item_counter'] == 3:
                data = [
                    ' ',
                    obj['cvmain__payee__address1'],
                    ' ',
                    obj['chartofaccount__accountcode'],
                    obj['chartofaccount__title'],
                    obj['department__code'],
                    obj['department__departmentname'],
                    obj['debitamount__sum'],
                    obj['creditamount__sum'],
                ]
            elif obj['item_counter'] == 4:
                data = [
                    ' ',
                    obj['cvmain__payee__address2'],
                    ' ',
                    obj['chartofaccount__accountcode'],
                    obj['chartofaccount__title'],
                    obj['department__code'],
                    obj['department__departmentname'],
                    obj['debitamount__sum'],
                    obj['creditamount__sum'],
                ]
            elif obj['item_counter'] > 4:
                data = [
                    ' ',
                    ' ',
                    ' ',
                    obj['chartofaccount__accountcode'],
                    obj['chartofaccount__title'],
                    obj['department__code'],
                    obj['department__departmentname'],
                    obj['debitamount__sum'],
                    obj['creditamount__sum'],
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
        if pcv == 'show':
            data = [
                "", "", "", "", "", "", "", "", "", "", "", "", "",
                "Total", report_total['cvmain__amount__sum'],
            ]
        else:
            data = [
                "", "", "", "", "", "", "", "", "", "",
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
            "", "", "", "", "", "",
            "Grand Total", report_total['debitamount__sum'], report_total['creditamount__sum'],
        ]

    row += 1
    for col_num in xrange(len(data)):
        worksheet.write(row, col_num, data[col_num], bold_money_format)

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+report_xls+".xlsx"
    return response

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        context = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        cvtype = request.GET['cvtype']
        cvsubtype = request.GET['cvsubtype']
        payee = request.GET['payee']
        branch = request.GET['branch']
        approver = request.GET['approver']
        cvstatus = request.GET['cvstatus']
        status = request.GET['status']
        atc = request.GET['atc']
        inputvattype = request.GET['inputvattype']
        vat = request.GET['vat']
        bankaccount = request.GET['bankaccount']
        creator = request.GET['creator']
        checknum = request.GET['checknum']
        checkdate = request.GET['checkdate']
        title = "Check Voucher List"
        subtype = ""
        list = Cvmain.objects.filter(isdeleted=0).order_by('cvnum')[:0]

        if report == '1':
            title = "Check Voucher Transaction List - Summary"
            q = Cvmain.objects.filter(isdeleted=0).order_by('cvnum', 'cvdate')
            if dfrom != '':
                q = q.filter(cvdate__gte=dfrom)
            if dto != '':
                q = q.filter(cvdate__lte=dto)
        elif report == '2':
            title = "Check Voucher Transaction List"
            q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0).order_by('cv_num', 'cv_date', 'item_counter')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
        elif report == '3':
            title = "Unposted Check Voucher Transaction List - Summary"
            q = Cvmain.objects.filter(isdeleted=0,status__in=['A','C']).order_by('cvnum', 'cvdate')
            if dfrom != '':
                q = q.filter(cvdate__gte=dfrom)
            if dto != '':
                q = q.filter(cvdate__lte=dto)
        elif report == '4':
            title = "Unposted Check Voucher Transaction List"
            q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0,status__in=['A','C']).order_by('cv_num', 'cv_date', 'item_counter')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
        elif report == '5':
            title = "Check Voucher Transaction Listing Subject To Input VAT"
            cvlist = getCVList(dfrom, dto)
            efo = getEFO()
            query = query_cvsubjecttovat(dfrom, dto, cvlist, efo)

            q = Cvmain.objects.filter(isdeleted=0).order_by('cvnum', 'cvdate')
        elif report == '6':
            title = "Check Voucher Transaction Listing Subject To Input VAT Summary"
            cvlist = getCVList(dfrom, dto)
            efo = getEFO()
            query = query_cvsubjecttovatsummary(dfrom, dto, cvlist, efo)

            q = Cvmain.objects.filter(isdeleted=0).order_by('cvnum', 'cvdate')

        if cvtype != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__cvtype__exact=cvtype)
            else:
                q = q.filter(cvtype=cvtype)
            subtype = Cvtype.objects.filter(pk=cvtype).first()
        if cvsubtype != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__cvsubtype__exact=cvsubtype)
            else:
                q = q.filter(cvsubtype=cvsubtype)

        if payee != 'null':
            if report == '2' or report == '4':
                q = q.filter(cvmain__payee_code__exact=payee)
            else:
                q = q.filter(payee_code=payee)
        if branch != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__branch__exact=branch)
            else:
                q = q.filter(branch=branch)
        if approver != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__designatedapprover__exact=approver)
            else:
                q = q.filter(designatedapprover=approver)
        if cvstatus != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__cvstatus__exact=cvstatus)
            else:
                q = q.filter(cvstatus=cvstatus)
        if status != '':
            q = q.filter(status=status)
        if atc != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__atc__exact=atc)
            else:
                q = q.filter(atc=atc)
        if inputvattype != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__inputvattype__exact=inputvattype)
            else:
                q = q.filter(inputvattype=inputvattype)
        if vat != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__vat__exact=vat)
            else:
                q = q.filter(vat=vat)
        if bankaccount != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__bankaccount__exact=bankaccount)
            else:
                q = q.filter(bankaccount=bankaccount)

        if creator != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(cvmain__enterby_id=creator)
            else:
                q = q.filter(enterby_id=creator)

        if checknum != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__checknum__exact=checknum)
            else:
                q = q.filter(checknum=checknum)

        if checkdate != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__checkdate=checkdate)
            else:
                q = q.filter(checkdate=checkdate)

        if report == '5' or report == '6':
            print 'pasok'
            list = query
            inputcredit = 0
            inputdebit = 0
            efocredit = 0
            efodebit = 0
            if list:
                df = pd.DataFrame(query)
                inputcredit = df['inputvatcreditamount'].sum()
                inputdebit = df['inputvatdebitamount'].sum()
                efocredit = df['efocreditamount'].sum()
                efodebit = df['efodebitamount'].sum()
        else:
            list = q

        if list:
            if report == '2' or report == '4':
                total = list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))
            elif report == '5' or report == '6':
                total = {'inputcredit': inputcredit, 'inputdebit': inputdebit, 'efocredit': efocredit, 'efodebit':efodebit}
            else:
                total = list.aggregate(total_amount=Sum('amount'))

        context = {
            "title": title,
            "subtype": subtype,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "datefrom": datetime.datetime.strptime(dfrom, '%Y-%m-%d'),
            "dateto": datetime.datetime.strptime(dto, '%Y-%m-%d'),
            "username": request.user,
        }
        if report == '1':
            return Render.render('checkvoucher/report/report_1.html', context)
        elif report == '2':
            return Render.render('checkvoucher/report/report_2.html', context)
        elif report == '3':
            return Render.render('checkvoucher/report/report_3.html', context)
        elif report == '4':
            return Render.render('checkvoucher/report/report_4.html', context)
        elif report == '5':
            return Render.render('checkvoucher/report/report_5.html', context)
        elif report == '6':
            return Render.render('checkvoucher/report/report_6.html', context)
        else:
            return Render.render('checkvoucher/report/report_1.html', context)

@method_decorator(login_required, name='dispatch')
class GenerateExcel(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        context = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        cvtype = request.GET['cvtype']
        cvsubtype = request.GET['cvsubtype']
        payee = request.GET['payee']
        branch = request.GET['branch']
        approver = request.GET['approver']
        cvstatus = request.GET['cvstatus']
        status = request.GET['status']
        atc = request.GET['atc']
        inputvattype = request.GET['inputvattype']
        vat = request.GET['vat']
        bankaccount = request.GET['bankaccount']
        creator = request.GET['creator']
        checknum = request.GET['checknum']
        checkdate = request.GET['checkdate']
        title = "Check Voucher List"
        list = Cvmain.objects.filter(isdeleted=0).order_by('cvnum')[:0]

        if report == '1':
            print 'hey pasok 1'
            title = "Check Voucher Transaction List - Summary"
            q = Cvmain.objects.filter(isdeleted=0).order_by('cvnum', 'cvdate')
            if dfrom != '':
                q = q.filter(cvdate__gte=dfrom)
            if dto != '':
                q = q.filter(cvdate__lte=dto)
        elif report == '2':
            title = "Check Voucher Transaction List"
            q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0).order_by('cv_num', 'cv_date',
                                                                                       'item_counter')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
        elif report == '3':
            title = "Unposted Check Voucher Transaction List - Summary"
            q = Cvmain.objects.filter(isdeleted=0, status__in=['A', 'C']).order_by('cvnum', 'cvdate')
            if dfrom != '':
                q = q.filter(cvdate__gte=dfrom)
            if dto != '':
                q = q.filter(cvdate__lte=dto)
        elif report == '4':
            title = "Unposted Check Voucher Transaction List"
            q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0, status__in=['A', 'C']).order_by('cv_num',
                                                                                                              'cv_date',
                                                                                                              'item_counter')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
        elif report == '5':
            title = "Check Voucher Transaction Listing Subject To Input VAT"
            cvlist = getCVList(dfrom, dto)
            efo = getEFO()
            query = query_cvsubjecttovat(dfrom, dto, cvlist, efo)

            q = Cvmain.objects.filter(isdeleted=0).order_by('cvnum', 'cvdate')
        elif report == '6':
            title = "Check Voucher Transaction Listing Subject To Input VAT Summary"
            cvlist = getCVList(dfrom, dto)
            efo = getEFO()
            query = query_cvsubjecttovatsummary(dfrom, dto, cvlist, efo)

            q = Cvmain.objects.filter(isdeleted=0).order_by('cvnum', 'cvdate')

        if cvtype != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__cvtype__exact=cvtype)
            else:
                q = q.filter(cvtype=cvtype)
        if cvsubtype != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__cvsubtype__exact=cvsubtype)
            else:
                q = q.filter(cvsubtype=cvsubtype)
        if payee != 'null':
            if report == '2' or report == '4':
                q = q.filter(cvmain__payee_code__exact=payee)
            else:
                q = q.filter(payee_code=payee)
        if branch != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__branch__exact=branch)
            else:
                q = q.filter(branch=branch)
        if approver != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__designatedapprover__exact=approver)
            else:
                q = q.filter(designatedapprover=approver)
        if cvstatus != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__cvstatus__exact=cvstatus)
            else:
                q = q.filter(cvstatus=cvstatus)
        if status != '':
            q = q.filter(status=status)
        if atc != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__atc__exact=atc)
            else:
                q = q.filter(atc=atc)
        if inputvattype != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__inputvattype__exact=inputvattype)
            else:
                q = q.filter(inputvattype=inputvattype)
        if vat != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__vat__exact=vat)
            else:
                q = q.filter(vat=vat)
        if bankaccount != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__bankaccount__exact=bankaccount)
            else:
                q = q.filter(bankaccount=bankaccount)

        if checknum != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__checknum__exact=checknum)
            else:
                q = q.filter(checknum=checknum)

        if checkdate != '':
            if report == '2' or report == '4':
                q = q.filter(cvmain__checkdate=checkdate)
            else:
                q = q.filter(checkdate=checkdate)

        if creator != '':
            if report == '2' or report == '4' or report == '8':
                q = q.filter(cvmain__enterby_id=creator)
            else:
                q = q.filter(enterby_id=creator)

        if report == '5' or report == '6':
            print 'pasok'
            list = query
            inputcredit = 0
            inputdebit = 0
            efocredit = 0
            efodebit = 0
            if list:
                df = pd.DataFrame(query)
                inputcredit = df['inputvatcreditamount'].sum()
                inputdebit = df['inputvatdebitamount'].sum()
                efocredit = df['efocreditamount'].sum()
                efodebit = df['efodebitamount'].sum()
        else:
            print 'nasa q'
            list = q

        if list:
            if report == '2' or report == '4':
                total = list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))
            elif report == '5' or report == '6':
                total = {'inputcredit': inputcredit, 'inputdebit': inputdebit, 'efocredit': efocredit,
                         'efodebit': efodebit}
            else:
                total = list.aggregate(total_amount=Sum('amount'))

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', str(title), bold)
        worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)

        filename = "cvreport.xlsx"

        print q
        if report == '1':

            # header
            worksheet.write('A4', 'CV Number', bold)
            worksheet.write('B4', 'CV Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Amount', bold)
            worksheet.write('F4', 'OR Number', bold)
            worksheet.write('G4', 'AP#', bold)
            worksheet.write('H4', 'With Invoice', bold)
            worksheet.write('I4', 'With OR', bold)

            row = 5
            col = 0
            totalamount = 0
            amount = 0
            for data in list:
                worksheet.write(row, col, data.cvnum)
                worksheet.write(row, col + 1, data.cvdate, formatdate)

                aptrans = Apvcvtransaction.objects.filter(cvmain_id=data.id).first()
                apnumx = ''
                if aptrans:
                    apnumx = str(aptrans.apmain.apnum)
                worksheet.write(row, col + 6, apnumx)

                if not request.user.is_superuser and data.confi == 1 and data.enterby_id != request.user.id:
                    worksheet.write(row, col + 2, 'Reserved Transaction')
                    worksheet.write(row, col + 4, float(format(data.amount, '.2f')))
                    row += 1

                else:

                    if data.status == 'C':
                        worksheet.write(row, col + 2, 'C A N C E L L E D')
                    else:
                        worksheet.write(row, col + 2, data.payee_name)
                    worksheet.write(row, col + 3, data.particulars)
                    if data.status == 'C':
                        worksheet.write(row, col + 4, float(format(0, '.2f')))
                        amount = 0
                    else:
                        worksheet.write(row, col + 4, float(format(data.amount, '.2f')))
                        amount = data.amount

                    winvoice = ''
                    wor = ''

                    if data.winvoice == 1:
                        winvoice = 'YES'
                    if data.wor == 1:
                        wor = 'YES'


                    worksheet.write(row, col + 5, data.ornum)
                    worksheet.write(row, col + 6, winvoice)
                    worksheet.write(row, col + 7, wor)
                    row += 1
                    totalamount += amount

            #print float(format(totalamount, '.2f'))
            #print total['total_amount']
            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totalamount, '.2f')))


            filename = "cvtransactionlistsummary.xlsx"

        elif report == '2':
            worksheet.write('A4', 'CV Number', bold)
            worksheet.write('B4', 'CV Date', bold)
            worksheet.write('C4', 'Particular', bold)
            worksheet.write('D4', 'Account Title', bold)
            worksheet.write('E4', 'Subs Ledger', bold)
            worksheet.write('F4', 'Debit', bold)
            worksheet.write('G4', 'Credit', bold)
            worksheet.write('H4', 'With Invoice', bold)
            worksheet.write('I4', 'With OR', bold)

            row = 4
            col = 0

            totaldebit = 0
            totalcredit = 0
            list = list.values('cvmain__cvnum', 'cvmain__cvdate', 'cvmain__particulars', 'cvmain__payee_name', 'cvmain__confi', 'cvmain__enterby_id',  'cvmain__winvoice', 'cvmain__wor',
                               'chartofaccount__accountcode', 'chartofaccount__description', 'status', 'debitamount',
                               'creditamount', 'branch__code', 'bankaccount__code', 'department__code')
            dataset = pd.DataFrame.from_records(list)

            for cvnum, detail in dataset.fillna('NaN').groupby(
                    ['cvmain__cvnum', 'cvmain__cvdate', 'cvmain__payee_name', 'cvmain__particulars', 'status', 'cvmain__confi', 'cvmain__enterby_id', 'cvmain__winvoice', 'cvmain__wor']):
                worksheet.write(row, col, cvnum[0])
                worksheet.write(row, col + 1, cvnum[1], formatdate)

                winvoice = ''
                wor = ''

                if cvnum[7] == 1:
                    winvoice = 'YES'
                if cvnum[8] == 1:
                    wor = 'YES'

                worksheet.write(row, col + 7, winvoice)
                worksheet.write(row, col + 8, wor)

                debit = 0
                credit = 0

                if not request.user.is_superuser and cvnum[5] == 1 and cvnum[6] != request.user.id:
                    worksheet.write(row, col + 2, 'Reserved Transaction')
                    row += 1
                    totaldebit += debit
                    totalcredit += credit
                else:

                    if cvnum[4] == 'C':
                        worksheet.write(row, col + 2, 'C A N C E L L E D')
                    else:
                        worksheet.write(row, col + 2, cvnum[2])
                    worksheet.write(row, col + 3, cvnum[3])
                    row += 1

                    branch = ''
                    bankaccount = ''
                    department = ''
                    for sub, data in detail.iterrows():
                        worksheet.write(row, col + 2, data['chartofaccount__accountcode'])
                        worksheet.write(row, col + 3, data['chartofaccount__description'])
                        if data['branch__code'] != 'NaN':
                            branch = data['branch__code']
                        if data['bankaccount__code'] != 'NaN':
                            bankaccount = data['bankaccount__code']
                        if data['department__code'] != 'NaN':
                            department = data['department__code']
                        worksheet.write(row, col + 4, branch + ' ' + bankaccount + ' ' + department)
                        if cvnum[4] == 'C':
                            worksheet.write(row, col + 5, float(format(0, '.2f')))
                            worksheet.write(row, col + 6, float(format(0, '.2f')))
                            debit = 0
                            credit = 0
                        else:
                            worksheet.write(row, col + 5, float(format(data['debitamount'], '.2f')))
                            worksheet.write(row, col + 6, float(format(data['creditamount'], '.2f')))
                            debit = data['debitamount']
                            credit = data['creditamount']

                        row += 1
                        totaldebit += debit
                        totalcredit += credit

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(totaldebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalcredit, '.2f')))

            filename = "cvtransactionlist.xlsx"

        elif report == '3':
            # header
            worksheet.write('A4', 'CV Number', bold)
            worksheet.write('B4', 'CV Date', bold)
            worksheet.write('C4', 'Payee', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Amount', bold)

            row = 5
            col = 0

            totalamount = 0
            amount = 0
            for data in list:
                worksheet.write(row, col, data.cvnum)
                worksheet.write(row, col + 1, data.cvdate, formatdate)
                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, data.payee_name)
                worksheet.write(row, col + 3, data.particulars)

                if data.status == 'C':
                    worksheet.write(row, col + 4, float(format(0, '.2f')))
                    amount = 0
                else:
                    worksheet.write(row, col + 4, float(format(data.amount, '.2f')))
                    amount = data.amount

                row += 1
                totalamount += amount

            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totalamount, '.2f')))

            filename = "unpostedcvtransactionlistsummary.xlsx"

        elif report == '4':
            # header
            worksheet.write('A4', 'CV Number', bold)
            worksheet.write('B4', 'CV Date', bold)
            worksheet.write('C4', 'Particular', bold)
            worksheet.write('D4', 'Account Title', bold)
            worksheet.write('E4', 'Subs Ledger', bold)
            worksheet.write('F4', 'Debit', bold)
            worksheet.write('G4', 'Credit', bold)

            row = 4
            col = 0

            totaldebit = 0
            totalcredit = 0
            list = list.values('cvmain__cvnum', 'cvmain__cvdate', 'cvmain__particulars', 'cvmain__payee_name',
                               'chartofaccount__accountcode', 'chartofaccount__description', 'status', 'debitamount',
                               'creditamount', 'branch__code', 'bankaccount__code', 'department__code')
            dataset = pd.DataFrame.from_records(list)

            for cvnum, detail in dataset.fillna('NaN').groupby(
                    ['cvmain__cvnum', 'cvmain__cvdate', 'cvmain__particulars', 'cvmain__payee_name', 'status']):
                worksheet.write(row, col, cvnum[0])
                worksheet.write(row, col + 1, cvnum[1], formatdate)
                if cvnum[4] == 'C':
                    worksheet.write(row, col + 2, 'C A N C E L L E D')
                else:
                    worksheet.write(row, col + 2, cvnum[2])
                worksheet.write(row, col + 3, cvnum[3])
                row += 1
                debit = 0
                credit = 0
                branch = ''
                bankaccount = ''
                department = ''
                for sub, data in detail.iterrows():
                    worksheet.write(row, col + 2, data['chartofaccount__accountcode'])
                    worksheet.write(row, col + 3, data['chartofaccount__description'])
                    if data['branch__code'] != 'NaN':
                        branch = data['branch__code']
                    if data['bankaccount__code'] != 'NaN':
                        bankaccount = data['bankaccount__code']
                    if data['department__code'] != 'NaN':
                        department = data['department__code']
                    worksheet.write(row, col + 4, branch + ' ' + bankaccount + ' ' + department)
                    if cvnum[4] == 'C':
                        worksheet.write(row, col + 5, float(format(0, '.2f')))
                        worksheet.write(row, col + 6, float(format(0, '.2f')))
                        debit = 0
                        credit = 0
                    else:
                        worksheet.write(row, col + 5, float(format(data['debitamount'], '.2f')))
                        worksheet.write(row, col + 6, float(format(data['creditamount'], '.2f')))
                        debit = data['debitamount']
                        credit = data['creditamount']

                    row += 1
                    totaldebit += debit
                    totalcredit += credit

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(totaldebit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalcredit, '.2f')))


            filename = "unpostedcvtransactionlist.xlsx"

        elif report == '5':
            # header
            worksheet.write('A4', 'CV Number', bold)
            worksheet.write('B4', 'CV Date', bold)
            worksheet.write('C4', 'Payee/Particular', bold)
            worksheet.write('D4', 'Type', bold)
            worksheet.write('E4', 'E F O Debit', bold)
            worksheet.write('F4', 'E F O Credit', bold)
            worksheet.write('G4', 'Input VAT Debit', bold)
            worksheet.write('H4', 'Input VAT Credit', bold)
            worksheet.write('I4', 'VAT Rate', bold)

            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0


            for data in list:
                worksheet.write(row, col, data.cvnum)
                worksheet.write(row, col + 1, data.cvdate, formatdate)
                worksheet.write(row, col + 2, data.payee_name)
                worksheet.write(row, col + 3, data.inputvat)
                worksheet.write(row, col + 4, float(format(data.efodebitamount, '.2f')))
                worksheet.write(row, col + 5, float(format(data.efocreditamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.inputvatdebitamount, '.2f')))
                worksheet.write(row, col + 7, float(format(data.inputvatcreditamount, '.2f')))
                worksheet.write(row, col + 8, data.inputvatrate)

                totalefodebit += data.efodebitamount
                totalefocredit += data.efocreditamount
                totalinputdebit += data.inputvatdebitamount
                totalinputcredit += data.inputvatcreditamount

                row += 1

            worksheet.write(row, col + 3, 'Total')
            worksheet.write(row, col + 4, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 5, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 6, float(format(totalinputdebit, '.2f')))
            worksheet.write(row, col + 7, float(format(totalinputcredit, '.2f')))


            filename = "cvtransactionsubjecttoinputvat.xlsx"
        elif report == '6':
            # header
            worksheet.write('A4', 'Payee/Particular', bold)
            worksheet.write('B4', 'Type', bold)
            worksheet.write('C4', 'E F O Debit', bold)
            worksheet.write('D4', 'E F O Credit', bold)
            worksheet.write('E4', 'Input VAT Debit', bold)
            worksheet.write('F4', 'Input VAT Credit', bold)
            worksheet.write('G4', 'VAT Rate', bold)
            worksheet.write('H4', 'Address', bold)
            worksheet.write('I4', 'TIN', bold)


            row = 4
            col = 0

            totalefodebit = 0
            totalefocredit = 0
            totalinputdebit = 0
            totalinputcredit = 0


            for data in list:
                worksheet.write(row, col, data.payee_name)
                worksheet.write(row, col + 1, data.inputvat)
                worksheet.write(row, col + 2, float(format(data.efodebitamount, '.2f')))
                worksheet.write(row, col + 3, float(format(data.efocreditamount, '.2f')))
                worksheet.write(row, col + 4, float(format(data.inputvatdebitamount, '.2f')))
                worksheet.write(row, col + 5, float(format(data.inputvatcreditamount, '.2f')))
                worksheet.write(row, col + 6, data.inputvatrate)
                worksheet.write(row, col + 7, data.address)
                worksheet.write(row, col + 8, data.tin)

                totalefodebit += data.efodebitamount
                totalefocredit += data.efocreditamount
                totalinputdebit += data.inputvatdebitamount
                totalinputcredit += data.inputvatcreditamount

                row += 1

            worksheet.write(row, col + 1, 'Total')
            worksheet.write(row, col + 2, float(format(totalefodebit, '.2f')))
            worksheet.write(row, col + 3, float(format(totalefocredit, '.2f')))
            worksheet.write(row, col + 4, float(format(totalinputdebit, '.2f')))
            worksheet.write(row, col + 5, float(format(totalinputcredit, '.2f')))


            filename = "cvtransactionsubjecttoinputvatsummary.xlsx"

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response
        
def query_cvsubjecttovat(dfrom, dto, cvlist, efo):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    aptrade = 274
    if not cvlist:
        cvlist = '0'

    query = "SELECT m.cvnum, m.cvdate, m.payee_name, m.particulars, inv.code AS inputvat, " \
            "IFNULL(efo.debitamount, 0) AS efodebitamount, IFNULL(efo.creditamount, 0) AS efocreditamount, " \
            "IFNULL(inputvat.debitamount, 0) AS inputvatdebitamount, IFNULL(inputvat.creditamount, 0) AS inputvatcreditamount, " \
            "ROUND((IFNULL(inputvat.debitamount, 0) - IFNULL(inputvat.creditamount, 0)) / (IFNULL(efo.debitamount, 0) - IFNULL(efo.creditamount, 0)) * 100) AS inputvatrate " \
            "FROM cvmain AS m " \
            "LEFT OUTER JOIN inputvattype AS invt ON invt.id = m.inputvattype_id " \
            "LEFT OUTER JOIN inputvat AS inv ON inv.inputvattype_id = invt.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.cvmain_id, d.cv_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM cvdetail AS d " \
            "WHERE d.cvmain_id IN ("+cvlist+") " \
            "AND d.chartofaccount_id IN ("+efo+") " \
            "GROUP BY d.cvmain_id " \
            "ORDER BY d.cv_num, d.cv_date " \
            ") AS efo ON efo.cvmain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.cvmain_id, d.cv_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM cvdetail AS d " \
            "WHERE d.cvmain_id IN ("+cvlist+") " \
            "AND d.chartofaccount_id = '"+str(aptrade)+"' " \
            "GROUP BY d.cvmain_id " \
            "ORDER BY d.cv_num, d.cv_date" \
            ") AS inputvat ON inputvat.cvmain_id = m.id " \
            "WHERE DATE(m.cvdate) >= '"+str(dfrom)+"' AND DATE(m.cvdate) <= '"+str(dto)+"' " \
            "AND m.cvstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+cvlist+") " \
            "ORDER BY m.cvnum"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_cvsubjecttovatsummary(dfrom, dto, cvlist, efo):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    aptrade = 274

    if not cvlist:
        cvlist = '0'

    query = "SELECT z.*, CONCAT(IFNULL(sup.address1, ''), ' ', IFNULL(sup.address2, '')) AS address, sup.tin " \
            "FROM ( " \
            "SELECT m.cvnum, m.cvdate, m.payee_code, m.payee_name, m.particulars, inv.code AS inputvat, " \
            "SUM(IFNULL(efo.debitamount, 0)) AS efodebitamount, SUM(IFNULL(efo.creditamount, 0)) AS efocreditamount, " \
            "SUM(IFNULL(inputvat.debitamount, 0)) AS inputvatdebitamount, SUM(IFNULL(inputvat.creditamount, 0)) AS inputvatcreditamount, " \
            "ROUND((SUM(IFNULL(inputvat.debitamount, 0)) - SUM(IFNULL(inputvat.creditamount, 0))) / (SUM(IFNULL(efo.debitamount, 0)) - SUM(IFNULL(efo.creditamount, 0))) * 100) AS inputvatrate " \
            "FROM cvmain AS m " \
            "LEFT OUTER JOIN inputvattype AS invt ON invt.id = m.inputvattype_id " \
            "LEFT OUTER JOIN inputvat AS inv ON inv.inputvattype_id = invt.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.cvmain_id, d.cv_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM cvdetail AS d " \
            "WHERE d.cvmain_id IN ("+cvlist+") " \
            "AND d.chartofaccount_id IN ("+efo+") " \
            "GROUP BY d.cvmain_id " \
            "ORDER BY d.cv_num, d.cv_date " \
            ") AS efo ON efo.cvmain_id = m.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT d.cvmain_id, d.cv_num, SUM(d.debitamount) AS debitamount, SUM(d.creditamount) AS creditamount, d.chartofaccount_id " \
            "FROM cvdetail AS d " \
            "WHERE d.cvmain_id IN ("+cvlist+") " \
            "AND d.chartofaccount_id = '"+str(aptrade)+"' " \
            "GROUP BY d.cvmain_id " \
            "ORDER BY d.cv_num, d.cv_date " \
            ") AS inputvat ON inputvat.cvmain_id = m.id " \
            "WHERE DATE(m.cvdate) >= '"+str(dfrom)+"' AND DATE(m.cvdate) <= '"+str(dto)+"' " \
            "AND m.cvstatus IN ('R') " \
            "AND m.status != 'C' " \
            "AND m.id IN ("+cvlist+") " \
            "GROUP BY m.payee_code, inv.code " \
            "ORDER BY m.payee_name) AS z " \
            "LEFT OUTER JOIN supplier AS sup ON sup.code = z.payee_code;"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

@csrf_exempt
def searchforposting(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']

        q = Cvmain.objects.filter(isdeleted=0,status='A',cvstatus='A').order_by('cvnum', 'cvdate')
        if dfrom != '':
            q = q.filter(cvdate__gte=dfrom)
        if dto != '':
            q = q.filter(cvdate__lte=dto)

        context = {
            'data': q
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('checkvoucher/postingresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


def getCVList(dfrom, dto):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    inputvat = 274 # 1940000000 INPUT VAT

    query = "SELECT m.cvnum, m.cvdate, m.payee_name, m.particulars, " \
            "d.balancecode, d.chartofaccount_id, d.cvmain_id " \
            "FROM cvmain AS m " \
            "LEFT OUTER JOIN cvdetail AS d ON d.cvmain_id = m.id " \
            "WHERE DATE(m.cvdate) >= '"+str(dfrom)+"' AND DATE(m.cvdate) <= '"+str(dto)+"' " \
            "AND m.cvstatus IN ('A', 'R') " \
            "AND m.status != 'C' " \
            "AND d.chartofaccount_id = "+str(inputvat)+" " \
            "ORDER BY m.cvnum;"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    list = ''
    for r in result:
        list += str(r.cvmain_id) + ','

    return list[:-1]


def getEFO():
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()


    query = "SELECT id, accountcode, description, main, clas, item, SUBSTR(sub, 1, 2) AS sub " \
            "FROM chartofaccount " \
            "WHERE (main = 5) OR (main = 1 AND clas = 5 AND SUBSTR(sub, 1, 2) = 10) " \
            "OR (main = 1 AND clas = 7 AND SUBSTR(sub, 1, 2) = 10) " \
            "OR (main = 1 AND clas = 1 AND item = 9) " \
            "OR (main = 1 AND clas = 1 AND item = 8) " \
            "OR (main = 1 AND clas = 6)"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    list = ''
    for r in result:
        list += str(r.id) + ','

    return list[:-1]
    #return result

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

@method_decorator(login_required, name='dispatch')
class DigibankerView(TemplateView):
    template_name = 'checkvoucher/digibanker.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        return context

@csrf_exempt
def fileupload(request):
    if request.method == 'POST':

        if request.FILES['or_file'] \
                and request.FILES['or_file'].name.endswith('.csv'):  # 3
            if request.FILES['or_file']._size < float(upload_size) * 1024 * 1024:
                csv_file = request.FILES["or_file"]

                file_data = csv_file.read().decode("utf-8")

                lines = file_data.split("\n")

                counter = 0
                batchkey = generatekey(1)
                for line in lines[:-1]:
                    fields = line.split(",")

                    apdata = fields[6].split("::")
                    apnum = ''.join(c for c in str(apdata[0][2:]) if c in digits)

                    print apnum

                    Temp_digibanker.objects.create(
                        item=str(fields[0]),
                        apnum=apnum,
                        mcno=str(fields[1]),
                        branch=str(fields[2]),
                        payeename=str(fields[3]),
                        amount=fields[4],
                        status=str(fields[5]),
                        remarks=str(fields[6]),
                        payeetype=str(fields[8]),
                        acctno=str(fields[9]),
                        refno=str(fields[10]),
                        mcdate=str(fields[11]),
                        batchkey=str(batchkey)
                    )
                    counter += 1

                data = {
                    'result': 1,
                    'batchkey': batchkey
                }
                return JsonResponse(data)
            else:
                data = {
                    'result': 4
                }
            return JsonResponse(data)

@csrf_exempt
def exportsave(request):
    if request.method == 'POST':
        # data-result definition:
        #   1: success
        #   2: failed - artype error

        print request.POST['batchkey']

        digibanker = getTempDigibanker(request.POST['batchkey']) #Temp_digibanker.objects.filter(batchkey=request.POST['batchkey'])

        aptrade = 285  # ACCOUNTS PAYABLE-TRADE
        cashinbank = 30  # CASH IN BANK
        pdate = datetime.datetime.now()

        for data in digibanker:
            print data.apnum
            apdata = Apdetail.objects.filter(ap_num=data.apnum, chartofaccount_id=aptrade).first()
            checkno = data.mcno
            checkdate = data.checkdate
            refno = 'APV'+data.apnum+' '+data.refno

            try:
                cvnumlast = Cvmain.objects.all().latest('cvnum')
                latestcvnum = str(cvnumlast)
                #print latestcvnum
                if latestcvnum[0:4] == str(datetime.datetime.now().year):
                    cvnum = str(datetime.datetime.now().year)
                    last = str(int(latestcvnum[4:]) + 1)
                    last = last.rjust(6, '0')
                    cvnum += last
                else:
                    cvnum = str(datetime.datetime.now().year) + '000001'
            except Cvmain.DoesNotExist:
                cvnum = str(datetime.datetime.now().year) + '000001'

            print 'cvnum'

            amountinwords = num2words(data.amount)

            bankacct = 22  # SB9
            confi = 0
            print apdata.ap_num
            if apdata.apmain.confi == 1:
                bankacct = 19 # SB7
                confi = 1

            # apdata.digicvmain_id:
            #print apdata.apmain.digicvmain_id

            if apdata.apmain.digicvmain_id is None or apdata.apmain.digicvmain_id == 0:

                main = Cvmain.objects.create(
                    cvnum=str(cvnum),
                    cvdate=str(checkdate),
                    cvtype_id=8,  # PAID-SB
                    cvsubtype_id=5,  # Digibanker
                    branch_id=5,  # Head Office
                    cvstatus = 'A',
                    checknum = str(checkno),
                    checkdate = str(checkdate),
                    payee_code = apdata.apmain.payeecode,
                    payee_name = apdata.apmain.payeename,
                    payee_id = apdata.apmain.payee_id,
                    currency_id= apdata.apmain.currency_id,
                    atc_id = apdata.apmain.atax_id,
                    fxrate= apdata.apmain.fxrate,
                    refnum=refno,
                    confi=confi,
                    deferredvat = apdata.apmain.deferred,
                    bankaccount_id = bankacct,
                    particulars=data.remarks,
                    amount=data.amount,
                    amountinwords=amountinwords,
                    designatedapprover_id=141,  # Pat Luzon
                    actualapprover_id = 141, # Pat Luzon
                    vat_id = apdata.apmain.vat_id,
                    inputvattype_id = apdata.apmain.inputvattype_id,
                    approverremarks = 'Auto approved from Digibanker Import File',
                    responsedate = datetime.datetime.now(),
                    enterby_id=request.user.id,
                    enterdate=datetime.datetime.now(),
                    modifyby_id=request.user.id,
                    modifydate=datetime.datetime.now()
                )

                ''' Update APMAIN '''
                apmain = Apmain.objects.filter(apnum=data.apnum).first()
                apmain.digicvmain_id = main.id
                apmain.cvamount = main.amount
                apmain.isfullycv = 1
                apmain.save()


                ''' Create CV AP Transaction Link'''
                Apvcvtransaction.objects.create(
                    cvamount=main.amount,
                    status='A',
                    apmain_id=apmain.id,
                    cvmain_id=main.id
                )


                ''' Accounts Payable Trade '''
                Cvdetail.objects.create(
                    item_counter=1,
                    cv_num=str(cvnum),
                    cv_date=str(checkdate),
                    cvmain_id=main.id,
                    debitamount=data.amount,
                    balancecode='D',
                    amount=data.amount,
                    chartofaccount_id=aptrade,
                    supplier_id=apdata.apmain.payee_id,
                    enterby_id=request.user.id,
                    enterdate=datetime.datetime.now(),
                    modifyby_id=request.user.id,
                    modifydate=datetime.datetime.now()
                )

                ''' Cash In Bank '''
                Cvdetail.objects.create(
                    item_counter=2,
                    cv_num=str(cvnum),
                    cv_date=str(checkdate),
                    cvmain_id=main.id,
                    creditamount=data.amount,
                    balancecode='C',
                    amount=data.amount,
                    chartofaccount_id=cashinbank,
                    bankaccount_id=bankacct, #SB
                    enterby_id=request.user.id,
                    enterdate=datetime.datetime.now(),
                    modifyby_id=request.user.id,
                    modifydate=datetime.datetime.now()
                )

                print 'done'
            else:
                print 'already imported'

            #Temp_digibanker.objects.filter(batchkey=request.POST['batchkey']).delete()

        data = {
            'result': 1
        }

        return JsonResponse(data)

def getTempDigibanker(batchkey):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()


    query = "SELECT *, STR_TO_DATE(mcdate, '%m/%d/%Y') AS checkdate FROM temp_digibanker WHERE batchkey = '"+str(batchkey)+"' ORDER BY item ASC"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


@csrf_exempt
def searchforacp(request):
    if request.method == 'POST':

        dfrom = request.POST['dfrom']
        dto = request.POST['dto']
        creator = request.POST['creator']

        cvtype = 10
        statuses = ['A', 'O']
        q = Cvmain.objects.filter(cvtype_id=cvtype,isdeleted=0,status__in=['A', 'O'],cvstatus='R').order_by('cvnum', 'cvdate')

        if dfrom != '':
            q = q.filter(cvdate__gte=dfrom)
        if dto != '':
            q = q.filter(cvdate__lte=dto)

        if creator != '':
            q = q.filter(enterby_id=creator)

        total = q.aggregate(Sum('amount'))

        print total

        context = {
            'data': q,
            'total': total,
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('checkvoucher/acpresult.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@method_decorator(login_required, name='dispatch')
class GenerateACPExcel(View):
    def get(self, request):

        #ids = request.GET['ids[]']
        ids = request.GET['ids']

        id_val = ids.split(',')

        list = Cvmain.objects.filter(id__in=id_val,isdeleted=0,status='A',cvstatus='R').order_by('cvnum', 'cvdate')

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', 'cv_num', bold)
        worksheet.write('B1', 'cv_date', bold)
        worksheet.write('C1', 'cv_type', bold)
        worksheet.write('D1', 'smf_code', bold)
        worksheet.write('E1', 'cv_payee', bold)
        worksheet.write('F1', 'cv_bnacc', bold)
        worksheet.write('G1', 'cv_ref', bold)
        worksheet.write('H1', 'cv_cknum', bold)
        worksheet.write('I1', 'cv_ckdate', bold)
        worksheet.write('J1', 'cv_amt_d', bold)
        worksheet.write('K1', 'cv_fx', bold)
        worksheet.write('L1', 'cv_amt_p', bold)
        worksheet.write('M1', 'cv_part1', bold)
        worksheet.write('N1', 'cv_part2', bold)
        worksheet.write('O1', 'cv_part3', bold)
        worksheet.write('P1', 'baf_at', bold)
        worksheet.write('Q1', 'baf_an', bold)
        worksheet.write('R1', 'remarks', bold)

        filename = "acpextract.xlsx"

        row = 1
        col = 0
        for data in list:
            worksheet.write(row, col, data.cvnum)
            worksheet.write(row, col + 1, data.cvdate, formatdate)
            worksheet.write(row, col + 2, 'A')
            worksheet.write(row, col + 3, data.payee_code)
            worksheet.write(row, col + 4, data.payee_name)
            worksheet.write(row, col + 5, data.bankaccount.code)
            worksheet.write(row, col + 6, data.refnum)
            worksheet.write(row, col + 7, data.checknum)
            worksheet.write(row, col + 8, data.checkdate, formatdate)
            worksheet.write(row, col + 9, '')
            worksheet.write(row, col + 10, '')
            worksheet.write(row, col + 11, data.amount)
            worksheet.write(row, col + 12, data.particulars)
            worksheet.write(row, col + 13, '')
            worksheet.write(row, col + 14, '')
            worksheet.write(row, col + 15, data.bankaccount.bankaccounttype.code)
            worksheet.write(row, col + 16, data.bankaccount.accountnumber)
            worksheet.write(row, col + 17, data.payee.account_number)

            row += 1

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        response = HttpResponse(output.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = "attachment; filename=" + filename

        output.close()

        return response

@csrf_exempt
def acpdigibanker(request):

    print 'ACP Digibanker'
    # AC 01 1218181 PHP 0111007943003 20181218 0000100361172 00193
    #
    # #text_file = open("accountspayable/txtfile/digibanker.txt", "w")
    text_file = open("static/digibanker/acpdigibanker.txt", "w")

    bnum = request.POST['batchnumber']
    pdate = request.POST['postingdate']
    funding = request.POST['funding']

    batchnum = bnum
    currency = 'PHP'
    fundacct = funding.replace('-', '')
    postingdate = pdate
    totalamount = 0
    totalno = 0
    #
    ids = request.POST.getlist('ids[]')

    cvtype = 10

    cashinbank = 30  # ACCOUNTS PAYABLE-TRADE

    detail = Cvdetail.objects.filter(cvmain_id__in=ids, chartofaccount_id=cashinbank).order_by('cv_num', 'cv_date')

    detaildata = ""
    for item in detail:
        print item.cvmain.payee.account_number
        transamount = str(item.creditamount).replace('.', '').rjust(13, '0')[:13]
        baccount = item.cvmain.payee.account_number.replace('-', '').ljust(16, ' ')[:16]
        particulars = 'CV'+str(item.cvmain.cvnum)+'::'+str(item.cvmain.payee_code)+'::'+str(item.cvmain.payee_name)+'::'+str(item.cvmain.checknum)+'::'+str(item.cvmain.particulars)
        particulars = ' '.join(particulars.splitlines())
        totalamount += item.creditamount
        totalno += 1
        detaildata += "AC10     "+str(currency)+str(baccount)+str(transamount)+str(particulars)+"\n"

    header = "AC01" + str(batchnum) + str(currency) + str(fundacct) + str(postingdate) + str(totalamount).replace('.', '').rjust(13, '0')[:13] + str(totalno).rjust(5, '0')[:5] + "\n"
    text_file.writelines(header)
    text_file.writelines(detaildata)

    text_file.close()

    print 'url'
    baseurl = request.build_absolute_uri('https://fin101bss.inquirer.com.ph/checkvoucher/acp/')
    print baseurl
    fileurl = baseurl.replace("checkvoucher/acp", "static/digibanker/")+'acpdigibanker.txt'
    print fileurl

    data = {'status': 'success', 'fileurl': fileurl}

    return JsonResponse(data)


def upload(request):
    folder = 'media/cvupload/'
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        id = request.POST['dataid']
        fs = FileSystemStorage(location=folder)  # defaults to   MEDIA_ROOT
        filename = fs.save(myfile.name, myfile)

        upl = Cvupload(cvmain_id=id, filename=filename, enterby=request.user, modifyby=request.user)
        upl.save()

        uploaded_file_url = fs.url(filename)
        return HttpResponseRedirect('/checkvoucher/' + str(id) )
    return HttpResponseRedirect('/checkvoucher/' + str(id) )

def tagging(request):
    if request.method == 'POST':
        id = request.POST['taggingid']
        winvoice = request.POST.get('winvoice', 0)
        wor = request.POST.get('wor', 0)

        Cvmain.objects.filter(id=id).update(winvoice=winvoice,wor=wor)

        return HttpResponseRedirect('/checkvoucher/' + str(id) )

    return HttpResponseRedirect('/checkvoucher/' + str(id) )

@csrf_exempt
def datafix(request):

    cvdata = Cvmain.objects.filter(cvsubtype_id=5).order_by('cvnum', 'cvdate')

    for item in cvdata:
        apvcv = Apvcvtransaction.objects.filter(cvmain_id=item.id).first()

        if apvcv is None:
            apnum = item.refnum[3:13]
            ap = Apmain.objects.filter(apnum=apnum).first()

            Apvcvtransaction.objects.create(
                cvamount=ap.cvamount,
                status='A',
                apmain_id=ap.id,
                cvmain_id=item.id
            )
        else:
            print item.id

@csrf_exempt
def filedelete(request):

    if request.method == 'POST':

        id = request.POST['id']
        fileid = request.POST['fileid']

        Cvupload.objects.filter(id=fileid).delete()

        return HttpResponseRedirect('/checkvoucher/' + str(id) )

    return HttpResponseRedirect('/checkvoucher/' + str(id) )





