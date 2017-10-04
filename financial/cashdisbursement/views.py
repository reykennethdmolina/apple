from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from checkvoucher.models import Cvmain, Cvdetail
from django.utils.dateformat import DateFormat
from utils.mixins import ReportContentMixin
from easy_pdf.views import PDFTemplateView
from datetime import datetime
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'cashdisbursement/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    template_name = 'cashdisbursement/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)

        query, context['rc_title'], context['report_total'], context['rc_fontsize'] = reportresultquery(self.request)

        context['data_list'] = query

        if self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name):
            context['datefrom'] = self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name)
            context['datefrom'] = datetime.strptime(context['datefrom'], "%Y-%m-%d").date()
            context['datefrom'] = DateFormat(context['datefrom']).format('F d, Y')
        else:
            context['datefrom'] = DateFormat(datetime.now()).format('F d, Y')

        if self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name):
            context['dateto'] = self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name)
            context['dateto'] = datetime.strptime(context['dateto'], "%Y-%m-%d").date()
            context['dateto'] = DateFormat(context['dateto']).format('F d, Y')
        else:
            context['dateto'] = DateFormat(datetime.now()).format('F d, Y')

        context['datenow'] = DateFormat(datetime.now()).format('m/d/Y')

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "CASH DISBURSEMENT BOOK"
        context['rc_font'] = "Times New Roman"

        return context


@csrf_exempt
def reportresultquery(request):
    report_type = ''
    report_total = ''
    report_font = '15px'
    report = request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name)

    query = Cvdetail.objects.all().filter(status='A').filter(isdeleted=0)

    if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
        key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
    else:
        key_data = DateFormat(datetime.now()).format('Y-m-d')
    query = query.filter(cv_date__gte=key_data)

    if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
        key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
    else:
        key_data = DateFormat(datetime.now()).format('Y-m-d')
    query = query.filter(cv_date__lte=key_data)

    if request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name):
        key_data = request.COOKIES.get('rep_f_status_' + request.resolver_match.app_name)
        query = query.filter(cvmain__cvstatus=key_data)

    if report == 's':
        report_type = "Summary Entries"

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        query = query.values('chartofaccount__accountcode', 'chartofaccount__description')\
                .annotate(Sum('debitamount'), Sum('creditamount'))\
                .order_by('chartofaccount__accountcode')

    if report == 'd':
        report_type = "Detailed Entries"
        report_font = '10px'

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        query = query.order_by('cv_num', '-balancecode')

    elif report == 'b':
        report_type = "Summary of Cash in Bank"

        query = query.filter(chartofaccount__accountcode='1112000000').exclude(bankaccount__isnull=True)

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        query = query.values('bankaccount__code', 'bankaccount__bank__code', 'bankaccount__bankaccounttype__code')\
                     .annotate(Sum('debitamount'), Sum('creditamount'))\
                     .order_by('bankaccount__code')

    return query, report_type, report_total, report_font


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
    queryset, report_type, report_total, report_font = reportresultquery(request)
    report_category = "CASH DISBMT BOOK"
    report_type = report_type if report_type != '' else 'Report'
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
        amount_placement = 2
        report_type = report_category + "(Summary)"
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        amount_placement = 26
        report_type = report_category + "(Cash in Bank)"
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'b':
        amount_placement = 2
        report_type = report_category + "(Detailed)"

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'Account No.', bold)
        worksheet.write('B1', 'Account Title', bold)
        worksheet.write('C1', 'Debit', bold_right)
        worksheet.write('D1', 'Credit', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.merge_range('A1:A2', 'CV Date.', bold)
        worksheet.merge_range('B1:B2', 'CV No.', bold)
        worksheet.merge_range('C1:G1', 'Payee', bold_center)
        worksheet.write('C2', 'Name', bold)
        worksheet.write('D2', 'Tin', bold)
        worksheet.write('E2', 'Address1', bold)
        worksheet.write('F2', 'Address2', bold)
        worksheet.write('G2', 'Address3', bold)
        worksheet.merge_range('H1:H2', 'Particulars', bold)
        worksheet.merge_range('I1:I2', 'Bank', bold)
        worksheet.merge_range('J1:J2', 'Check No.', bold)
        worksheet.merge_range('K1:K2', 'Amount', bold_right)
        worksheet.merge_range('L1:Z1', 'Accounting Entry', bold_center)
        worksheet.write('L2', 'Acct. No.', bold)
        worksheet.write('M2', 'Acct. Title', bold)
        worksheet.write('N2', 'Bank Account', bold)
        worksheet.write('O2', 'Department', bold)
        worksheet.write('P2', 'Employee', bold)
        worksheet.write('Q2', 'Supplier', bold)
        worksheet.write('R2', 'Customer', bold)
        worksheet.write('S2', 'Unit', bold)
        worksheet.write('T2', 'Branch', bold)
        worksheet.write('U2', 'Product', bold)
        worksheet.write('V2', 'Input VAT', bold)
        worksheet.write('W2', 'Output VAT', bold)
        worksheet.write('X2', 'VAT', bold)
        worksheet.write('Y2', 'WTAX', bold)
        worksheet.write('Z2', 'ATAX Code', bold)
        worksheet.merge_range('AA1:AA2', 'Debit', bold_right)
        worksheet.merge_range('AB1:AB2', 'Credit', bold_right)
        row += 1
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'b':
        worksheet.write('A1', 'Bank Acct.', bold)
        worksheet.write('B1', 'Bank Description', bold)
        worksheet.write('C1', 'Debit', bold_right)
        worksheet.write('D1', 'Credit', bold_right)

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            data = [
                obj['chartofaccount__accountcode'],
                obj['chartofaccount__description'],
                obj['debitamount__sum'],
                obj['creditamount__sum'],
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            data = [
                DateFormat(obj.cv_date).format('Y-m-d'),
                obj.cv_num,
                obj.cvmain.payee_name if obj.cvmain.payee else '',
                obj.cvmain.payee.tin if obj.cvmain.payee else '',
                obj.cvmain.payee.address1 if obj.cvmain.payee else '',
                obj.cvmain.payee.address2 if obj.cvmain.payee else '',
                obj.cvmain.payee.address3 if obj.cvmain.payee else '',
                obj.cvmain.particulars,
                obj.cvmain.bankaccount.code,
                obj.cvmain.checknum,
                obj.cvmain.amount,
                obj.chartofaccount.accountcode,
                obj.chartofaccount.description,
                obj.bankaccount.code + " " + obj.bankaccount.bank.code + " " + obj.bankaccount.bankaccounttype.code + "A" if obj.bankaccount else '',
                obj.department.code if obj.department else '',
                obj.employee.code if obj.employee else '',
                obj.supplier.code if obj.supplier else '',
                obj.customer.code if obj.customer else '',
                obj.unit.code if obj.unit else '',
                obj.branch.code if obj.branch else '',
                obj.product.code if obj.product else '',
                obj.inputvat.code if obj.inputvat else '',
                obj.outputvat.code if obj.outputvat else '',
                obj.vat.code if obj.vat else '',
                obj.wtax.code if obj.wtax else '',
                obj.ataxcode.code if obj.ataxcode else '',
                obj.debitamount,
                obj.creditamount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'b':
            data = [
                obj['bankaccount__code'],
                obj['bankaccount__bank__code'] + " " + obj['bankaccount__bankaccounttype__code'] + "A",
                obj['debitamount__sum'],
                obj['creditamount__sum'],
            ]

        temp_amount_placement = amount_placement
        for col_num in xrange(len(data)):
            if col_num == temp_amount_placement:
                temp_amount_placement += 1
                worksheet.write_number(row, col_num, data[col_num], money_format)
            else:
                if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd' and col_num == 10:
                    worksheet.write_number(row, col_num, data[col_num], money_format)
                else:
                    worksheet.write(row, col_num, data[col_num])

    # config: totals
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        data = [
            "", "Total", report_total['debitamount__sum'], report_total['creditamount__sum']
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        data = [
            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
            "Total", report_total['debitamount__sum'], report_total['creditamount__sum']
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'b':
        data = [
            "", "Total", report_total['debitamount__sum'], report_total['creditamount__sum']
        ]

    row += 1
    for col_num in xrange(len(data)):
        worksheet.write(row, col_num, data[col_num], bold_money_format)

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+report_type+".xlsx"
    return response
