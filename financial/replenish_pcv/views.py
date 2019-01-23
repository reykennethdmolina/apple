from django.views.generic import ListView, TemplateView
from utils.mixins import ReportContentMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from . models import Reppcvmain, Reppcvdetail
from companyparameter.models import Companyparameter
from oftype.models import Oftype
from operationalfund. models import Ofmain, Ofdetail, Ofdetailtemp, Ofdetailbreakdown, Ofdetailbreakdowntemp, Ofitem, Ofitemtemp
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime
from endless_pagination.views import AjaxListView
from easy_pdf.views import PDFTemplateView
from django.utils.dateformat import DateFormat


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Reppcvmain
    template_name = 'replenish_pcv/index.html'
    page_template = 'replenish_pcv/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Reppcvmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(reppcvnum__icontains=keysearch) |
                                 Q(reppcvdate__icontains=keysearch) |
                                 Q(cvmain__cvnum__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        context['initialapprover'] = Companyparameter.objects.get(code='PDI').pcv_initial_approver.id
        context['finalapprover'] = Companyparameter.objects.get(code='PDI').pcv_final_approver.id

        return context


@method_decorator(login_required, name='dispatch')
class ApprovalView(TemplateView):
    template_name = 'replenish_pcv/approval.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user != Companyparameter.objects.get(code='PDI').pcv_initial_approver \
                and self.request.user != Companyparameter.objects.get(code='PDI').pcv_final_approver:
            raise Http404
        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        context['pcv'] = Reppcvmain.objects.filter(status='A', isdeleted=0, cvmain=None)

        if self.request.user == Companyparameter.objects.get(code='PDI').pcv_initial_approver \
                and self.request.user == Companyparameter.objects.get(code='PDI').pcv_final_approver:
            context['pcv'] = context['pcv'].filter(Q(initialapproverresponse=None)
                               | (Q(initialapproverresponse='A') & Q(finalapproverresponse=None))
                               | Q(initialapproverresponse='D') | Q(finalapproverresponse__isnull=False))
        elif self.request.user == Companyparameter.objects.get(code='PDI').pcv_initial_approver:
            context['pcv'] = context['pcv'].filter(Q(initialapproverresponse=None)
                               | (Q(initialapproverresponse='A') & Q(finalapproverresponse=None))
                               | Q(initialapproverresponse='D'))
        elif self.request.user == Companyparameter.objects.get(code='PDI').pcv_final_approver:
            context['pcv'] = context['pcv'].filter((Q(initialapproverresponse='A') & Q(finalapproverresponse=None))
                               | Q(finalapproverresponse__isnull=False))

        context['initialapprover'] = Companyparameter.objects.get(code='PDI').pcv_initial_approver.id
        context['finalapprover'] = Companyparameter.objects.get(code='PDI').pcv_final_approver.id

        return context


def userpcvResponse(request):
    if request.method == 'POST':
        intro_remarks = '<font class="small text-primary">' + str(request.user.first_name) + ' </font><mark class="small text-warning">' + str(datetime.datetime.now().strftime("%m/%d/%y %H:%M")) + '</mark>&nbsp;&nbsp;&nbsp;'

        if request.POST['response_from'] == 'initial':
            if Companyparameter.objects.get(code='PDI').pcv_initial_approver.id == request.user.id \
                    and Reppcvmain.objects.get(pk=request.POST['response_id'], status='A', isdeleted=0, finalapproverresponse=None):
                if request.POST['response_type'] == 'a' or request.POST['response_type'] == 'd':
                    pcvitem = Reppcvmain.objects.filter(pk=request.POST['response_id'],
                                                        status='A',
                                                        isdeleted=0,
                                                        finalapproverresponse=None)
                    old_remarks = '' if pcvitem.first().initialapproverremarks is None else pcvitem.first().initialapproverremarks
                    pcvitem.update(initialapprover=request.user.id,
                                   initialapproverresponse=request.POST['response_type'].upper(),
                                   initialapproverresponsedate=datetime.datetime.now(),
                                   initialapproverremarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')
        elif request.POST['response_from'] == 'final':
            if Companyparameter.objects.get(code='PDI').pcv_final_approver.id == request.user.id \
                    and Reppcvmain.objects.get(pk=request.POST['response_id'], status='A', isdeleted=0, cvmain=None, initialapproverresponse='A'):
                if request.POST['response_type'] == 'a' or request.POST['response_type'] == 'd':
                    pcvitem = Reppcvmain.objects.filter(pk=request.POST['response_id'],
                                                        status='A',
                                                        isdeleted=0,
                                                        cvmain=None,
                                                        initialapproverresponse='A')
                    old_remarks = '' if pcvitem.first().finalapproverremarks is None else pcvitem.first().finalapproverremarks
                    pcvitem.update(finalapprover=request.user.id,
                                   finalapproverresponse=request.POST['response_type'].upper(),
                                   finalapproverresponsedate=datetime.datetime.now(),
                                   finalapproverremarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')

    return HttpResponseRedirect('/replenish_pcv/approval')


@method_decorator(login_required, name='dispatch')
class CreateView(ListView):
    model = Ofmain
    template_name = 'replenish_pcv/create.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Ofmain.objects.all().filter(isdeleted=0, ofstatus='R', oftype__code='PCV', reppcvmain=None).\
            order_by('ofnum')

        if self.request.GET:
            if self.request.GET['ofdatefrom']:
                query = query.filter(ofdate__gte=self.request.GET['ofdatefrom'])
            if self.request.GET['ofdateto']:
                query = query.filter(ofdate__lte=self.request.GET['ofdateto'])
            if self.request.GET['rofdatefrom']:
                query = query.filter(releasedate__gte=self.request.GET['rofdatefrom'])
            if self.request.GET['rofdateto']:
                query = query.filter(releasedate__lte=self.request.GET['rofdateto'])

        return query

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['oftype'] = Oftype.objects.filter(code='PCV', isdeleted=0)
        if self.request.GET:
            context['ofdatefrom'] = self.request.GET['ofdatefrom']
            context['ofdateto'] = self.request.GET['ofdateto']
            context['rofdatefrom'] = self.request.GET['rofdatefrom']
            context['rofdateto'] = self.request.GET['rofdateto']

        return context


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Reppcvmain
    template_name = 'replenish_pcv/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['reppcvmain'] = Reppcvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['reppcvdetail'] = Reppcvdetail.objects.filter(reppcvmain=self.kwargs['pk'], isdeleted=0).\
            order_by('ofmain_id')
        context['ofitem'] = Ofitem.objects.filter(isdeleted=0, status='A', ofmain__reppcvmain=self.kwargs['pk'],
                                                  ofitemstatus='A').order_by('ofnum')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedreppcv = Reppcvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedreppcv.print_ctr += 1
        printedreppcv.save()
        return context


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Ofmain
    template_name = 'replenish_pcv/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Ofmain
    template_name = 'replenish_pcv/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0
        query, context['report_type'], context['report_total'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query
            
        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "Petty Cash Replenishment"
        context['rc_title'] = "Petty Cash Replenishment"

        return context

            
@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_total = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        report_type = "P.Cash Replenishment Summary"
        query = Reppcvmain.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(reppcvnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(reppcvnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(reppcvdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(reppcvdate__lte=key_data)

        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            if key_data == 'req':
                query = query.filter(cvmain__isnull=True)
            elif key_data == 'rep':
                query = query.filter(cvmain__isnull=False)

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        report_type = "P.Cash Replenishment Detailed"
        defaultorder = ['ofmain__reppcvmain__reppcvnum', 'ofmain__reppcvmain__cvmain__cvnum',
                        'ofmain__ofnum', 'ofsubtype__description']

        query = Ofitem.objects.all().filter(isdeleted=0,
                                            ofitemstatus='A',
                                            ofmain__isnull=False,
                                            ofmain__reppcvdetail__isnull=False,
                                            ofmain__reppcvmain__isnull=False)

        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            if key_data == 'req':
                query = query.filter(ofmain__reppcvmain__cvmain__isnull=True)
            elif key_data == 'rep':
                query = query.filter(ofmain__reppcvmain__cvmain__isnull=False)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reppcvmain__reppcvnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reppcvmain__reppcvnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reppcvmain__reppcvdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reppcvmain__reppcvdate__lte=key_data)

        if request.COOKIES.get('rep_f_order2_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order2_' + request.resolver_match.app_name))
            if key_data != 'null':
                defaultorder = key_data.split(",")

        query = query.order_by(*defaultorder)

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        query = Ofdetail.objects.all().filter(isdeleted=0, ofmain__reppcvmain__isnull=False)

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
            query = query.filter(ofmain__reppcvmain__reppcvnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reppcvmain__reppcvnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reppcvmain__reppcvdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(ofmain__reppcvmain__reppcvdate__lte=key_data)

        if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name))
            if key_data == 'req':
                query = query.filter(ofmain__reppcvmain__cvmain__isnull=True)
            elif key_data == 'rep':
                query = query.filter(ofmain__reppcvmain__cvmain__isnull=False)

        if request.COOKIES.get('rep_f_balancecode_' + request.resolver_match.app_name) == 'd':
            query = query.filter(balancecode='D')
        elif request.COOKIES.get('rep_f_balancecode_' + request.resolver_match.app_name) == 'c':
            query = query.filter(balancecode='C')

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
            report_type = "PCR Acctg Entry - Summary"

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
            report_type = "PCR Acctg Entry - Detailed"

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
    report_type = report_type if report_type != '' else 'PCR Report'
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
        worksheet.write('A1', 'Rep PCV Num', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'CV Num', bold)
        worksheet.write('D1', 'Entered By', bold)
        worksheet.write('E1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.write('A1', 'R.PCV Num', bold)
        worksheet.write('B1', 'R.PCV Date', bold)
        worksheet.write('C1', 'CV Num', bold)
        worksheet.write('D1', 'CV Date', bold)
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
            str_cvnum = obj.cvmain.cvnum if obj.cvmain is not None else '-'
            data = [
                obj.reppcvnum,
                DateFormat(obj.reppcvdate).format('Y-m-d'),
                str_cvnum,
                obj.enterby.first_name + " " + obj.enterby.last_name,
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            str_cvnum = obj.ofmain.reppcvmain.cvmain.cvnum if obj.ofmain.reppcvmain.cvmain is not None else '-'
            str_cvdate = DateFormat(obj.ofmain.reppcvmain.cvmain.cvdate).format('Y-m-d') if obj.ofmain.reppcvmain.cvmain is not None else '-'
            if obj.supplier_name is not None:
                str_payee = obj.supplier_name
            elif obj.payee_name is not None:
                str_payee = obj.payee_name
            else:
                str_payee = ''

            data = [
                obj.ofmain.reppcvmain.reppcvnum,
                DateFormat(obj.ofmain.reppcvmain.reppcvdate).format('Y-m-d'),
                str_cvnum,
                str_cvdate,
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
        yearqs = Reppcvmain.objects.filter(reppcvnum__startswith=year)

        if yearqs:
            reppcvnumlast = yearqs.latest('reppcvnum')
            latestreppcvnum = str(reppcvnumlast)
            print "latest: " + latestreppcvnum

            reppcvnum = year
            last = str(int(latestreppcvnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                reppcvnum += '0'
            reppcvnum += last

        else:
            reppcvnum = year + '000001'

        print 'reppcvnum: ' + reppcvnum

        newreppcv = Reppcvmain()
        newreppcv.reppcvnum = reppcvnum
        newreppcv.reppcvdate = datetime.date.today()
        newreppcv.enterby = request.user
        newreppcv.modifyby = request.user
        newreppcv.save()

        total_amount = 0
        replenishedofs = Ofmain.objects.filter(id__in=request.POST.getlist('pcv_checkbox'))
        for data in replenishedofs:
            newreppcvdetail = Reppcvdetail()
            newreppcvdetail.amount = data.approvedamount
            newreppcvdetail.enterby = request.user
            newreppcvdetail.modifyby = request.user
            newreppcvdetail.ofmain = Ofmain.objects.get(pk=data.id)
            newreppcvdetail.reppcvmain = newreppcv
            total_amount += newreppcvdetail.amount
            newreppcvdetail.save()
            data.reppcvdetail = newreppcvdetail
            data.reppcvmain = newreppcv
            data.save()

        newreppcv.amount = total_amount
        newreppcv.save()
        print "PCV successfully replenished."
    else:
        print "Something went wrong in saving REPPCV."
    return redirect('/replenish_pcv/')


@csrf_exempt
def fetch_details(request):
    if request.method == 'POST':
        details = Reppcvdetail.objects.filter(isdeleted=0, reppcvmain__reppcvnum=request.POST['reppcvnum'])

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
