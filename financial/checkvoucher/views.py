from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from ataxcode.models import Ataxcode
from bankaccount.models import Bankaccount
from bankbranchdisburse.models import Bankbranchdisburse
from branch.models import Branch
from companyparameter.models import Companyparameter
from currency.models import Currency
from inputvattype.models import Inputvattype
from cvtype.models import Cvtype
from operationalfund.models import Ofmain, Ofitem, Ofdetail
from replenish_pcv.models import Reppcvmain, Reppcvdetail
from supplier.models import Supplier
from vat.models import Vat
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from . models import Cvmain, Cvdetail, Cvdetailtemp, Cvdetailbreakdown, Cvdetailbreakdowntemp
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail
from django.template.loader import render_to_string
from easy_pdf.views import PDFTemplateView
import datetime
from pprint import pprint


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Cvmain
    template_name = 'checkvoucher/index.html'
    page_template = 'checkvoucher/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Cvmain.objects.all().filter(isdeleted=0)

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
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
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
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = self.object.pk
        # data for lookup

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Cvmain
    template_name = 'checkvoucher/create.html'
    fields = ['cvdate', 'cvtype', 'amount', 'refnum', 'particulars', 'vat', 'atc', 'checknum', 'checkdate',
              'inputvattype', 'deferredvat', 'currency', 'fxrate', 'branch', 'bankaccount', 'disbursingbranch',
              'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('checkvoucher.add_cvmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['reppcvmain'] = Reppcvmain.objects.filter(isdeleted=0, cvmain=None).order_by('enterdate')

        # data for lookup
        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['pk'] = 0
        # data for lookup

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
        print self.request.POST['hiddenpayee']
        print self.request.POST['hiddenpayeeid']
        if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
            self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
            self.object.payee_code = self.object.payee.code
            self.object.payee_name = self.object.payee.name
        else:
            self.object.payee_name = self.request.POST['payee']

        self.object.cvnum = cvnum
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.cvstatus = 'F'
        self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
        self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
        self.object.save()

        # accounting entry starts here..
        source = 'cvdetailtemp'
        mainid = self.object.id
        num = self.object.cvnum
        secretkey = self.request.POST['secretkey']
        savedetail(source, mainid, num, secretkey, self.request.user)

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
    fields = ['cvnum', 'cvdate', 'cvtype', 'amount', 'refnum', 'particulars', 'vat', 'atc', 'bankaccount',
              'disbursingbranch', 'inputvattype', 'deferredvat', 'currency', 'fxrate', 'cvstatus', 'remarks',
              'branch', 'checknum', 'checkdate', 'vatrate', 'atcrate', 'designatedapprover']

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
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['payee'] = Cvmain.objects.get(pk=self.object.id).payee.id if Cvmain.objects.get(
            pk=self.object.id).payee is not None else ''
        context['payee_name'] = Cvmain.objects.get(pk=self.object.id).payee_name
        context['originalcvstatus'] = Cvmain.objects.get(pk=self.object.id).cvstatus
        context['actualapprover'] = None if Cvmain.objects.get(pk=self.object.id).actualapprover is None else Cvmain.objects.get(pk=self.object.id).actualapprover.id
        context['approverremarks'] = Cvmain.objects.get(pk=self.object.id).approverremarks
        context['responsedate'] = Cvmain.objects.get(pk=self.object.id).responsedate
        context['releaseby'] = Cvmain.objects.get(pk=self.object.id).releaseby
        context['releasedate'] = Cvmain.objects.get(pk=self.object.id).releasedate
        context['reppcvmain'] = Reppcvmain.objects.filter(isdeleted=0, cvmain=self.object.id).order_by('enterdate')
        cv_main_aggregate = Reppcvmain.objects.filter(isdeleted=0, cvmain=self.object.id).aggregate(Sum('amount'))
        context['reppcv_total_amount'] = cv_main_aggregate['amount__sum']

        # data for lookup
        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
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

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if self.request.POST['originalcvstatus'] != 'R':
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
            self.object.save(update_fields=['cvdate', 'cvtype', 'amount', 'refnum', 'particulars', 'vat', 'atc',
                                            'bankaccount', 'disbursingbranch', 'inputvattype', 'deferredvat',
                                            'currency', 'fxrate', 'cvstatus', 'remarks', 'branch', 'checknum',
                                            'checkdate', 'vatrate', 'atcrate'])

            if self.object.cvstatus == 'F':
                print "heyy F"
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
                self.object.releasedate = None
                self.object.cvstatus = 'A'
                self.object.save(update_fields=['releaseby', 'releasedate', 'cvstatus'])
            elif self.object.cvstatus != 'R':
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.save(update_fields=['releaseby', 'releasedate'])

        else:
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['modifyby', 'modifydate', 'remarks'])

        # accounting entry starts here..
        source = 'cvdetailtemp'
        mainid = self.object.id
        num = self.object.cvnum
        secretkey = self.request.POST['secretkey']
        updatedetail(source, mainid, num, secretkey, self.request.user)

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

        return HttpResponseRedirect('/checkvoucher')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Cvmain
    template_name = 'checkvoucher/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['cvmain'] = Cvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['detail'] = Cvdetail.objects.filter(isdeleted=0). \
            filter(cvmain_id=self.kwargs['pk']).order_by('item_counter')
        context['totaldebitamount'] = Cvdetail.objects.filter(isdeleted=0). \
            filter(cvmain_id=self.kwargs['pk']).aggregate(Sum('debitamount'))
        context['totalcreditamount'] = Cvdetail.objects.filter(isdeleted=0). \
            filter(cvmain_id=self.kwargs['pk']).aggregate(Sum('creditamount'))

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedcv = Cvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedcv.print_ctr += 1
        printedcv.save()
        return context


@csrf_exempt
def approve(request):
    if request.method == 'POST':
        cv_for_approval = Cvmain.objects.get(cvnum=request.POST['cvnum'])
        if request.user.has_perm('checkvoucher.approve_allcv') or \
                request.user.has_perm('checkvoucher.approve_assignedcv'):
            if request.user.has_perm('checkvoucher.approve_allcv') or \
                    (request.user.has_perm('checkvoucher.approve_assignedcv') and
                        cv_for_approval.designatedapprover == request.user):
                if request.POST['originalcvstatus'] != 'R' or int(request.POST['backtoinprocess']) == 1:
                    cv_for_approval.cvstatus = request.POST['approverresponse']
                    cv_for_approval.isdeleted = 0
                    if request.POST['approverresponse'] == 'D':
                        cv_for_approval.status = 'C'
                    else:
                        cv_for_approval.status = 'A'
                    cv_for_approval.approverresponse = request.POST['approverresponse']
                    cv_for_approval.responsedate = request.POST['responsedate']
                    cv_for_approval.actualapprover = User.objects.get(pk=request.user.id)
                    cv_for_approval.approverremarks = request.POST['approverremarks']
                    cv_for_approval.releaseby = None
                    cv_for_approval.releasedate = None
                    cv_for_approval.save()
                    data = {
                        'status': 'success',
                        'cvnum': cv_for_approval.cvnum,
                        'newcvstatus': cv_for_approval.cvstatus,
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
def release(request):
    if request.method == 'POST':
        cv_for_release = Cvmain.objects.get(cvnum=request.POST['cvnum'])
        if cv_for_release.cvstatus != 'F' and cv_for_release.cvstatus != 'D':
            cv_for_release.releaseby = User.objects.get(pk=request.POST['releaseby'])
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

