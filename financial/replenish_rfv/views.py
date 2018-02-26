from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from utils.mixins import ReportContentMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from . models import Reprfvmain, Reprfvdetail
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
from operationalfund. models import Ofmain, Ofdetail, Ofdetailtemp, Ofdetailbreakdown, Ofdetailbreakdowntemp, Ofitem, Ofitemtemp
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
from dateutil.relativedelta import relativedelta
from django.utils.dateformat import DateFormat
from django.http import HttpResponse


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Reprfvmain
    template_name = 'replenish_rfv/index.html'
    page_template = 'replenish_rfv/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Reprfvmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(reprfvnum__icontains=keysearch) |
                                 Q(reprfvdate__icontains=keysearch) |
                                 Q(apmain__apnum__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        context['initialapprover'] = Companyparameter.objects.get(code='PDI').rfv_initial_approver.id
        context['finalapprover'] = Companyparameter.objects.get(code='PDI').rfv_final_approver.id

        return context


@method_decorator(login_required, name='dispatch')
class ApprovalView(TemplateView):
    template_name = 'replenish_rfv/approval.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user != Companyparameter.objects.get(code='PDI').rfv_initial_approver \
                and self.request.user != Companyparameter.objects.get(code='PDI').rfv_final_approver:
            raise Http404
        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        context['rfv'] = Reprfvmain.objects.filter(status='A', isdeleted=0, apmain=None)

        if self.request.user == Companyparameter.objects.get(code='PDI').rfv_initial_approver \
                and self.request.user == Companyparameter.objects.get(code='PDI').rfv_final_approver:
            context['rfv'] = context['rfv'].filter(Q(initialapproverresponse=None)
                               | (Q(initialapproverresponse='A') & Q(finalapproverresponse=None))
                               | Q(initialapproverresponse='D') | Q(finalapproverresponse__isnull=False))
        elif self.request.user == Companyparameter.objects.get(code='PDI').rfv_initial_approver:
            context['rfv'] = context['rfv'].filter(Q(initialapproverresponse=None)
                               | (Q(initialapproverresponse='A') & Q(finalapproverresponse=None))
                               | Q(initialapproverresponse='D'))
        elif self.request.user == Companyparameter.objects.get(code='PDI').rfv_final_approver:
            context['rfv'] = context['rfv'].filter((Q(initialapproverresponse='A') & Q(finalapproverresponse=None))
                               | Q(finalapproverresponse__isnull=False))

        context['initialapprover'] = Companyparameter.objects.get(code='PDI').rfv_initial_approver.id
        context['finalapprover'] = Companyparameter.objects.get(code='PDI').rfv_final_approver.id

        return context


def userrfvResponse(request):
    if request.method == 'POST':
        intro_remarks = '<font class="small text-primary">' + str(request.user.first_name) + ' </font><mark class="small text-warning">' + str(datetime.datetime.now().strftime("%m/%d/%y %H:%M")) + '</mark>&nbsp;&nbsp;&nbsp;'

        if request.POST['response_from'] == 'initial':
            if Companyparameter.objects.get(code='PDI').rfv_initial_approver.id == request.user.id \
                    and Reprfvmain.objects.get(pk=request.POST['response_id'], status='A', isdeleted=0, finalapproverresponse=None):
                if request.POST['response_type'] == 'a' or request.POST['response_type'] == 'd':
                    rfvitem = Reprfvmain.objects.filter(pk=request.POST['response_id'],
                                                        status='A',
                                                        isdeleted=0,
                                                        finalapproverresponse=None)
                    old_remarks = '' if rfvitem.first().initialapproverremarks is None else rfvitem.first().initialapproverremarks
                    rfvitem.update(initialapprover=request.user.id,
                                   initialapproverresponse=request.POST['response_type'].upper(),
                                   initialapproverresponsedate=datetime.datetime.now(),
                                   initialapproverremarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')
        elif request.POST['response_from'] == 'final':
            if Companyparameter.objects.get(code='PDI').rfv_final_approver.id == request.user.id \
                    and Reprfvmain.objects.get(pk=request.POST['response_id'], status='A', isdeleted=0, apmain=None, initialapproverresponse='A'):
                if request.POST['response_type'] == 'a' or request.POST['response_type'] == 'd':
                    rfvitem = Reprfvmain.objects.filter(pk=request.POST['response_id'],
                                                        status='A',
                                                        isdeleted=0,
                                                        apmain=None,
                                                        initialapproverresponse='A')
                    old_remarks = '' if rfvitem.first().finalapproverremarks is None else rfvitem.first().finalapproverremarks
                    rfvitem.update(finalapprover=request.user.id,
                                   finalapproverresponse=request.POST['response_type'].upper(),
                                   finalapproverresponsedate=datetime.datetime.now(),
                                   finalapproverremarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')

    return HttpResponseRedirect('/replenish_rfv/approval')


@method_decorator(login_required, name='dispatch')
class CreateView(ListView):
    model = Ofmain
    template_name = 'replenish_rfv/create.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Ofmain.objects.all().filter(isdeleted=0, ofstatus='R', oftype__code='RFV', reprfvmain=None).\
            order_by('ofnum')

        if self.request.GET:
            if self.request.GET['ofdatefrom']:
                query = query.filter(ofdate__gte=self.request.GET['ofdatefrom'])
            if self.request.GET['ofdateto']:
                query = query.filter(ofdate__lte=self.request.GET['ofdateto'])

        return query

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['oftype'] = Oftype.objects.filter(code='RFV', isdeleted=0)
        if self.request.GET:
            context['ofdatefrom'] = self.request.GET['ofdatefrom']
            context['ofdateto'] = self.request.GET['ofdateto']

        return context


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Ofmain
    template_name = 'replenish_rfv/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Ofmain
    template_name = 'replenish_rfv/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0
        query, context['report_type'], context['report_total'] = reportresultquery(self.request)

        print query

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "Revolving Fund Replenishment"
        context['rc_title'] = "Revolving Fund Replenishment"

        return context


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Reprfvmain
    template_name = 'replenish_rfv/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['reprfvmain'] = Reprfvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['reprfvdetail'] = Reprfvdetail.objects.filter(reprfvmain=self.kwargs['pk'], isdeleted=0).\
            order_by('ofmain_id')
        context['ofitem'] = Ofitem.objects.filter(isdeleted=0, status='A', ofmain__reprfvmain=self.kwargs['pk'],
                                                  ofitemstatus='A')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedreprfv = Reprfvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedreprfv.print_ctr += 1
        printedreprfv.save()
        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_total = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        report_type = "R.Fund Replenishment Summary"
        query = Reprfvmain.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(reprfvnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(reprfvnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(reprfvdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(reprfvdate__lte=key_data)

        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            if key_data == 'req':
                query = query.filter(apmain__isnull=True)
            elif key_data == 'rep':
                query = query.filter(apmain__isnull=False)

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        report_type = "R.Fund Replenishment Detailed"
        defaultorder = ['ofmain__reprfvmain__reprfvnum', 'ofmain__reprfvmain__apmain__apnum',
                        'ofmain__ofnum', 'ofsubtype__description']

        query = Ofitem.objects.all().filter(isdeleted=0,
                                            ofitemstatus='A',
                                            ofmain__isnull=False,
                                            ofmain__reprfvdetail__isnull=False,
                                            ofmain__reprfvmain__isnull=False)

        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            if key_data == 'req':
                query = query.filter(ofmain__reprfvmain__apmain__isnull=True)
            elif key_data == 'rep':
                query = query.filter(ofmain__reprfvmain__apmain__isnull=False)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reprfvmain__reprfvnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reprfvmain__reprfvnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reprfvmain__reprfvdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reprfvmain__reprfvdate__lte=key_data)

        if request.COOKIES.get('rep_f_order2_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order2_' + request.resolver_match.app_name))
            if key_data != 'null':
                defaultorder = key_data.split(",")

        query = query.order_by(*defaultorder)

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        query = Ofdetail.objects.all().filter(isdeleted=0, ofmain__reprfvmain__isnull=False)

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

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reprfvmain__reprfvnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reprfvmain__reprfvnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reprfvmain__reprfvdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reprfvmain__reprfvdate__lte=key_data)

        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            if key_data == 'req':
                query = query.filter(ofmain__reprfvmain__apmain__isnull=True)
            elif key_data == 'rep':
                query = query.filter(ofmain__reprfvmain__apmain__isnull=False)

        if request.COOKIES.get('rep_f_balancecode_' + request.resolver_match.app_name) == 'd':
            query = query.filter(balancecode='D')
        elif request.COOKIES.get('rep_f_balancecode_' + request.resolver_match.app_name) == 'c':
            query = query.filter(balancecode='C')

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "RFR Acctg Entry - Summary"

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
            report_type = "RFR Acctg Entry - Detailed"

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

        report_total = query.aggregate(Sum('amount'))

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
    report_type = report_type if report_type != '' else 'RFR Report'
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
        amount_placement = 8
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        amount_placement = 14
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        amount_placement = 15

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'Rep RFV Num', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'AP Num', bold)
        worksheet.write('D1', 'Entered By', bold)
        worksheet.write('E1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.write('A1', 'R.RFV Num', bold)
        worksheet.write('B1', 'R.RFV Date', bold)
        worksheet.write('C1', 'AP Num', bold)
        worksheet.write('D1', 'AP Date', bold)
        worksheet.write('E1', 'OF Num', bold)
        worksheet.write('F1', 'OF Date', bold)
        worksheet.write('G1', 'OF Subtype', bold)
        worksheet.write('H1', 'Payee', bold)
        worksheet.write('I1', 'Amount', bold)
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
            str_apnum = obj.apmain.apnum if obj.apmain is not None else '-'
            data = [
                obj.reprfvnum,
                DateFormat(obj.reprfvdate).format('Y-m-d'),
                str_apnum,
                obj.enterby.first_name + " " + obj.enterby.last_name,
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            str_apnum = obj.ofmain.reprfvmain.apmain.apnum if obj.ofmain.reprfvmain.apmain is not None else '-'
            str_apdate = DateFormat(obj.ofmain.reprfvmain.apmain.apdate).format('Y-m-d') if obj.ofmain.reprfvmain.apmain is not None else '-'
            if obj.supplier_name is not None:
                str_payee = obj.supplier_name
            elif obj.payee_name is not None:
                str_payee = obj.payee_name
            else:
                str_payee = ''

            data = [
                obj.ofmain.reprfvmain.reprfvnum,
                DateFormat(obj.ofmain.reprfvmain.reprfvdate).format('Y-m-d'),
                str_apnum,
                str_apdate,
                "OF-"+obj.ofmain.oftype.code + "-" + obj.ofmain.ofnum,
                DateFormat(obj.ofmain.ofdate).format('Y-m-d'),
                obj.ofsubtype.description,
                str_payee,
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
            "", "", "", "", "", "", "",
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


@csrf_exempt
def replenish(request):
    if request.method == 'POST':
        year = str(datetime.date.today().year)
        yearqs = Reprfvmain.objects.filter(reprfvnum__startswith=year)

        if yearqs:
            reprfvnumlast = yearqs.latest('reprfvnum')
            latestreprfvnum = str(reprfvnumlast)
            print "latest: " + latestreprfvnum

            reprfvnum = year
            last = str(int(latestreprfvnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                reprfvnum += '0'
            reprfvnum += last

        else:
            reprfvnum = year + '000001'

        print 'reprfvnum: ' + reprfvnum

        newreprfv = Reprfvmain()
        newreprfv.reprfvnum = reprfvnum
        newreprfv.reprfvdate = datetime.date.today()
        newreprfv.enterby = request.user
        newreprfv.modifyby = request.user
        newreprfv.save()

        total_amount = 0
        replenishedofs = Ofmain.objects.filter(id__in=request.POST.getlist('rfv_checkbox'))
        for data in replenishedofs:
            newreprfvdetail = Reprfvdetail()
            newreprfvdetail.amount = data.approvedamount
            newreprfvdetail.enterby = request.user
            newreprfvdetail.modifyby = request.user
            newreprfvdetail.ofmain = Ofmain.objects.get(pk=data.id)
            newreprfvdetail.reprfvmain = newreprfv
            total_amount += newreprfvdetail.amount
            newreprfvdetail.save()
            data.reprfvdetail = newreprfvdetail
            data.reprfvmain = newreprfv
            data.save()

        newreprfv.amount = total_amount
        newreprfv.save()
        print "RFV successfully replenished."
    else:
        print "Something went wrong in saving REPRFV."
    return redirect('/replenish_rfv/')


@csrf_exempt
def fetch_details(request):
    if request.method == 'POST':
        details = Reprfvdetail.objects.filter(isdeleted=0, reprfvmain__reprfvnum=request.POST['reprfvnum'])

        details_list = []

        for data in details:
            details_list.append([data.id,
                                 'OF-' + data.ofmain.oftype.code + '-' + data.ofmain.ofnum,
                                 data.ofmain.ofdate,
                                 data.ofmain.particulars,
                                 data.amount,
                                 ])

        data = {
            'status': 'success',
            'detail': details_list
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)
