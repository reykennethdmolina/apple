import datetime
from django.db.models import Sum
from django.views.generic import DetailView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from jvtype.models import Jvtype
from jvsubtype.models import Jvsubtype
from currency.models import Currency
from branch.models import Branch
from department.models import Department
from operationalfund.models import Ofmain, Ofdetail, Ofitem
from . models import Jvmain, Jvdetail, Jvdetailtemp, Jvdetailbreakdown, Jvdetailbreakdowntemp
from acctentry.views import updateallquery, validatetable, deleteallquery, generatekey, querystmtdetail, \
    querytotaldetail, savedetail, updatedetail
from endless_pagination.views import AjaxListView
from django.db.models import Q
from django.contrib.auth.models import User


class IndexView(AjaxListView):
    model = Jvmain
    template_name = 'journalvoucher/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'journalvoucher/index_list.html'

    def get_queryset(self):
        query = Jvmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(jvnum__icontains=keysearch) |
                                 Q(jvdate__icontains=keysearch) |
                                 Q(jvtype__description__icontains=keysearch) |
                                 Q(department__departmentname__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        #lookup
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('description')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('description')
        context['pk'] = 0

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
    fields = ['jvdate', 'jvtype', 'jvsubtype', 'refnum', 'particular', 'branch', 'currency', 'department',
              'designatedapprover']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['department'] = Department.objects.filter(isdeleted=0).exclude(pk=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('pk')
        context['jvsubtype'] = Jvsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['ofcsvmain'] = Ofmain.objects.filter(isdeleted=0, oftype__code='CSV', jvmain=None).\
            exclude(releasedate=None).order_by('id')   # released CSVs that do not have JVs yet
        return context

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

        # accounting entry starts here..
        source = 'jvdetailtemp'
        mainid = self.object.id
        num = self.object.jvnum
        secretkey = self.request.POST['secretkey']
        savedetail(source, mainid, num, secretkey, self.request.user)

        # save jvmain in ofmain
        for i in range(len(self.request.POST.getlist('csv_checkbox'))):
            ofmain = Ofmain.objects.get(pk=int(self.request.POST.getlist('csv_checkbox')[i]))
            ofmain.jvmain = self.object
            ofmain.save()
        # save jvmain in ofmain

        totaldebitamount = Jvdetail.objects.filter(isdeleted=0).filter(jvmain_id=self.object.id).aggregate(
            Sum('debitamount'))
        totalcreditamount = Jvdetail.objects.filter(isdeleted=0).filter(jvmain_id=self.object.id).aggregate(
            Sum('creditamount'))

        if totaldebitamount['debitamount__sum'] == totalcreditamount['creditamount__sum']:
            self.object.amount = totaldebitamount['debitamount__sum']
            self.object.save(update_fields=['amount'])
        else:
            print "Debit and Credit amounts are not equal. JV Amount is not saved."

        return HttpResponseRedirect('/journalvoucher/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Jvmain
    template_name = 'journalvoucher/edit.html'
    fields = ['jvdate', 'jvtype', 'jvsubtype', 'refnum', 'particular', 'branch', 'currency', 'department',
              'designatedapprover', 'jvstatus']

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
        context['jvsubtype'] = Jvsubtype.objects.filter(isdeleted=0).order_by('pk')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['jvnum'] = self.object.jvnum
        context['originaljvstatus'] = Jvmain.objects.get(pk=self.object.id).jvstatus

        contextdatatable = {
            # to be used by accounting entry on load
            'tabledetailtemp': 'jvdetailtemp',
            'tablebreakdowntemp': 'jvdetailbreakdowntemp',

            'datatemp': querystmtdetail('jvdetailtemp', self.mysecretkey),
            'datatemptotal': querytotaldetail('jvdetailtemp', self.mysecretkey),
        }
        context['datatable'] = render_to_string('acctentry/datatable.html', contextdatatable)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['jvdate', 'jvtype', 'jvsubtype', 'refnum', 'particular', 'branch', 'currency',
                                        'department', 'designatedapprover', 'jvstatus'])

        # accounting entry starts here..
        source = 'jvdetailtemp'
        mainid = self.object.id
        num = self.object.jvnum
        secretkey = self.request.POST['secretkey']
        updatedetail(source, mainid, num, secretkey, self.request.user)

        return HttpResponseRedirect('/journalvoucher/'+str(self.object.pk)+'/update')


@csrf_exempt
def importrepcsv(request):
    if request.method == 'POST':
        first_ofmain = Ofmain.objects.filter(id=request.POST.getlist('checked_repcsvmain[]')[0],
                                             isdeleted=0,
                                             status='A').first()

        ofdetail = Ofdetail.objects.filter(
            ofmain__in=set(request.POST.getlist('checked_repcsvmain[]'))). \
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

        if 'jvnum' in request.POST:
            if request.POST['jvnum']:
                updateallquery(request.POST['table'], request.POST['jvnum'])
        # set isdeleted=2 for existing detailtemp data

        i = 1
        for detail in ofdetail:
            jvdetailtemp = Jvdetailtemp()
            jvdetailtemp.item_counter = i
            jvdetailtemp.secretkey = request.POST['secretkey']
            jvdetailtemp.jv_date = datetime.datetime.now()
            jvdetailtemp.chartofaccount = detail['chartofaccount__id']
            jvdetailtemp.bankaccount = detail['bankaccount__id']
            jvdetailtemp.department = detail['department__id']
            jvdetailtemp.employee = detail['employee__id']
            jvdetailtemp.supplier = detail['supplier__id']
            jvdetailtemp.customer = detail['customer__id']
            jvdetailtemp.unit = detail['unit__id']
            jvdetailtemp.branch = detail['branch__id']
            jvdetailtemp.product = detail['product__id']
            jvdetailtemp.inputvat = detail['inputvat__id']
            jvdetailtemp.outputvat = detail['outputvat__id']
            jvdetailtemp.vat = detail['vat__id']
            jvdetailtemp.wtax = detail['wtax__id']
            jvdetailtemp.ataxcode = detail['ataxcode__id']
            jvdetailtemp.debitamount = detail['debitamount__sum']
            jvdetailtemp.creditamount = detail['creditamount__sum']
            jvdetailtemp.balancecode = detail['balancecode']
            jvdetailtemp.enterby = request.user
            jvdetailtemp.modifyby = request.user
            jvdetailtemp.save()
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
            'branch': first_ofmain.branch_id
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)

