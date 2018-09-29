from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from companyparameter.models import Companyparameter
from journalvoucher.models import Jvdetail
from checkvoucher.models import Cvdetail
from officialreceipt.models import Ordetail
from accountspayable.models import Apdetail
from purchaseorder.models import Pomain
from utils.mixins import ReportContentMixin
from easy_pdf.views import PDFTemplateView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Case, Value, When, F, Q
import datetime


@method_decorator(login_required, name='dispatch')
class ReportView(TemplateView):
    model = Jvdetail
    template_name = 'rep_booksofaccounts/report.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        context['default_datefrom'] = first_day_of_month(datetime.date.today())
        context['default_dateto'] = last_day_of_month(datetime.date.today())

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultPdfView(ReportContentMixin, PDFTemplateView):
    model = Jvdetail
    template_name = 'rep_booksofaccounts/reportresultpdf.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultPdfView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_subtype'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_subtype'], context['report_total'], context['report_xls'], \
            context['orientation'], context['pagesize'], accounts_debits, departments_debits, accounts_credits, \
            departments_credits = reportresultquery(self.request)

        if self.request.COOKIES.get('date_from_' + self.request.resolver_match.app_name):
            context['datefrom'] = datetime.datetime.strptime(self.request.COOKIES.get('date_from_' + self.request.
                                                                                      resolver_match.app_name),
                                                             "%Y-%m-%d")
        else:
            context['datefrom'] = first_day_of_month(datetime.date.today())
        if self.request.COOKIES.get('date_to_' + self.request.resolver_match.app_name):
            context['dateto'] = datetime.datetime.strptime(self.request.COOKIES.get('date_to_' + self.request.
                                                                                    resolver_match.app_name),
                                                           "%Y-%m-%d")
        else:
            context['dateto'] = last_day_of_month(datetime.date.today())

        if context['report_subtype'] == '(Summary Entries)':
            if context['report_type'] == 'SCHEDULE OF ACCRUAL - ACCTS. PAYABLE-TRADE' or context['report_type'] == \
                    'SCHEDULE OF ACCRUAL - ACCTS. PAYABLE-TRADE (WITH BRANCH)':
                context['data_list1'] = accounts_debits
                context['data_list2'] = departments_debits
                context['data_list3'] = accounts_credits
                context['data_list4'] = departments_credits
            else:
                context['data_list'] = query
        else:
            context['data_list'] = query

        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_subtype = ''
    report_total = ''
    report_xls = ''
    orientation = ''
    pagesize = ''
    accounts_debits = ''
    departments_debits = ''
    accounts_credits = ''
    departments_credits = ''

    set_report_type = request.COOKIES.get('report_type_' + request.resolver_match.app_name) if request.COOKIES.get(
        'report_type_' + request.resolver_match.app_name) else 'GJB_S'
    date_from = str(request.COOKIES.get('date_from_' + request.resolver_match.app_name)) if request.COOKIES.get(
        'date_from_' + request.resolver_match.app_name) else str(first_day_of_month(datetime.date.today()))
    date_to = str(request.COOKIES.get('date_to_' + request.resolver_match.app_name)) if request.COOKIES.get(
        'date_to_' + request.resolver_match.app_name) else str(last_day_of_month(datetime.date.today()))

    # set common configurations for Summary and Detailed per Transaction Type
    if set_report_type == 'GJB_S' or set_report_type == 'GJB_D':
        report_type = 'GENERAL JOURNAL BOOK'
        query = Jvdetail.objects.all().filter(isdeleted=0).exclude(jvmain__status='C')
        query = query.filter(jvmain__jvdate__gte=date_from)
        query = query.filter(jvmain__jvdate__lte=date_to)
        report_xls = 'GJB Summary' if set_report_type == 'GJB_S' else 'GJB Detailed' if set_report_type == 'GJB_D' \
            else 'GJB Summary'
        report_subtype = '(Summary Entries)' if set_report_type == 'GJB_S' else '(Detailed Entries)' if \
            set_report_type == 'GJB_D' else 'GJB Summary'
    elif set_report_type == 'CDB_S' or set_report_type == 'CDB_D':
        report_type = 'CASH DISBURSEMENT BOOK'
        query = Cvdetail.objects.all().filter(isdeleted=0).exclude(cvmain__status='C')
        query = query.filter(cvmain__cvdate__gte=date_from)
        query = query.filter(cvmain__cvdate__lte=date_to)
        report_xls = 'CDB Summary' if set_report_type == 'CDB_S' else 'CDB Detailed' if set_report_type == 'CDB_D' \
            else 'CDB Summary'
        report_subtype = '(Summary Entries)' if set_report_type == 'CDB_S' else '(Detailed Entries)' if \
            set_report_type == 'CDB_D' else 'CDB Summary'
    elif set_report_type == 'CRB_S' or set_report_type == 'CRB_D':
        report_type = 'CASH RECEIPTS BOOK'
        query = Ordetail.objects.all().filter(isdeleted=0).exclude(ormain__status='C')
        query = query.filter(ormain__ordate__gte=date_from)
        query = query.filter(ormain__ordate__lte=date_to)
        report_xls = 'CRB Summary' if set_report_type == 'CRB_S' else 'CRB Detailed' if set_report_type == 'CRB_D' \
            else 'CRB Summary'
        report_subtype = '(Summary Entries)' if set_report_type == 'CRB_S' else '(Detailed Entries)' if \
            set_report_type == 'CRB_D' else 'CRB Summary'
    elif set_report_type == 'SAP_S' or set_report_type == 'SAP_WB_S' or set_report_type == 'SAP_D':
        report_type = 'SCHEDULE OF ACCRUAL - ACCTS. PAYABLE-TRADE'
        if set_report_type == 'SAP_WB_S':
            report_type += ' (WITH BRANCH)'
        query = Apdetail.objects.all().filter(isdeleted=0).exclude(apmain__status='C')
        query = query.filter(apmain__apdate__gte=date_from)
        query = query.filter(apmain__apdate__lte=date_to)
        report_xls = 'SAP Summary' if set_report_type == 'SAP_S' else 'SAP-WB Summary' \
            if set_report_type == 'SAP_WB_S' else 'SAP Detailed' if set_report_type == 'SAP_D' else 'SAP Summary'
        report_subtype = '(Summary Entries)' if set_report_type == 'SAP_S' or set_report_type == 'SAP_WB_S' \
            else '(Detailed Entries)' if set_report_type == 'SAP_D' else '(Summary Entries)'
    elif set_report_type == 'PURCHASE':
        report_type = 'PURCHASE BOOK'
        query = Pomain.objects.all().filter(isdeleted=0).exclude(status='C')
        query = query.filter(podate__gte=date_from)
        query = query.filter(podate__lte=date_to)
        report_xls = 'Purchase Book'
        report_subtype = ''

    # set common configurations for all Transaction Types with SUMMARY ENTRIES subtype
    if report_subtype == '(Summary Entries)':
        orientation = 'portrait'
        pagesize = 'letter'
        if set_report_type == 'SAP_S' or set_report_type == 'SAP_WB_S':
            # debit amounts for assets and liabilities excluding cash in bank and ap trade
            accounts_debits = query
            accounts_debits = Apdetail.objects.filter((Q(chartofaccount__accountcode__startswith='1') |
                                                       Q(chartofaccount__accountcode__startswith='2'))). \
                exclude(chartofaccount=Companyparameter.objects.first().coa_cashinbank). \
                exclude(chartofaccount=Companyparameter.objects.first().coa_aptrade)
            accounts_debits = accounts_debits.values('chartofaccount__description').annotate(Sum('debitamount')). \
                filter(debitamount__sum__gt=0). \
                order_by('chartofaccount__accountcode')
            accounts_debits_total = accounts_debits.aggregate(Sum('debitamount__sum'))

            # debit amounts per department
            departments_debits = query
            departments_debits = Apdetail.objects.exclude(department=None)
            if set_report_type == 'SAP_S':
                departments_debits = departments_debits.values('department__code', 'department__departmentname')\
                    .annotate(Sum('debitamount')).filter(debitamount__sum__gt=0).order_by('department__code')
            else:
                departments_debits = departments_debits.values('department__code', 'department__departmentname',
                                                               'branch__code') \
                    .annotate(Sum('debitamount')).filter(debitamount__sum__gt=0).order_by('department__code')
            departments_debits_total = departments_debits.aggregate(Sum('debitamount__sum'))

            # credit amounts for assets and liabilities excluding cash in bank and ap trade
            accounts_credits = query
            accounts_credits = Apdetail.objects.filter((Q(chartofaccount__accountcode__startswith='1') |
                                                        Q(chartofaccount__accountcode__startswith='2'))). \
                exclude(chartofaccount=Companyparameter.objects.first().coa_cashinbank). \
                exclude(chartofaccount=Companyparameter.objects.first().coa_aptrade)
            accounts_credits = accounts_credits.values('chartofaccount__description').annotate(Sum('creditamount')). \
                filter(creditamount__sum__gt=0). \
                order_by('chartofaccount__accountcode')
            accounts_credits_total = accounts_credits.aggregate(Sum('creditamount__sum'))

            # credit amounts per department
            departments_credits = query
            departments_credits = Apdetail.objects.exclude(department=None)
            if set_report_type == 'SAP_S':
                departments_credits = departments_credits.values('department__code', 'department__departmentname')\
                    .annotate(Sum('creditamount')).filter(creditamount__sum__gt=0).order_by('department__code')
            else:
                departments_credits = departments_credits.values('department__code', 'department__departmentname',
                                                                 'branch__code') \
                    .annotate(Sum('creditamount')).filter(creditamount__sum__gt=0).order_by('department__code')
            departments_credits_total = departments_credits.aggregate(Sum('creditamount__sum'))

            report_total = (accounts_debits_total['debitamount__sum__sum'] +
                            departments_debits_total['debitamount__sum__sum']) - \
                           (accounts_credits_total['creditamount__sum__sum'] +
                            departments_credits_total['creditamount__sum__sum'])
        else:
            query = query.values('chartofaccount__accountcode',
                                 'chartofaccount__description') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('chartofaccount__accountcode')
            report_total = query.aggregate(Sum('debitdifference'), Sum('creditdifference'))

    # set common configurations for each Transaction Type with DETAILED ENTRIES subtype
    elif report_subtype == '(Detailed Entries)':
        orientation = 'landscape'
        pagesize = 'legal'
        sort_numbers = []

        # General Journal Book (JOURNAL VOUCHER)
        if set_report_type == 'GJB_D':
            query = query.order_by('jv_num', 'item_counter')
            sort_numbers = preserve_sort(query, 'jv_num')

        # Cash Disbursement Book (CHECK VOUCHER)
        elif set_report_type == 'CDB_D':
            query = query.order_by('cv_num', '-balancecode', 'item_counter')
            sort_numbers = preserve_sort(query, 'cv_num')

        # Cash Receipts Book (OFFICIAL RECEIPT)
        elif set_report_type == 'CRB_D':
            query = query.order_by('or_num', '-balancecode', 'item_counter')
            sort_numbers = preserve_sort(query, 'or_num')

        # Schedule of Accruals - Accts. Payable-Trade (ACCOUNTS PAYABLE VOUCHER)
        elif set_report_type == 'SAP_D':
            query = query.order_by('ap_num', '-balancecode', 'item_counter')
            sort_numbers = preserve_sort(query, 'ap_num')

        report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))
        query = zip(query[160:260], sort_numbers[160:260])

    elif report_subtype == '' and set_report_type == 'PURCHASE':
        orientation = 'landscape'
        pagesize = 'legal'

        query = query.order_by('ponum')

    return query, report_type, report_subtype, report_total, report_xls, orientation, pagesize, accounts_debits, \
        departments_debits, accounts_credits, departments_credits


@method_decorator(login_required, name='dispatch')
class CashInBankPdfView(ReportContentMixin, PDFTemplateView):
    model = Jvdetail
    template_name = 'rep_booksofaccounts/cashinbankpdf.html'

    def get_context_data(self, **kwargs):
        context = super(CashInBankPdfView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_subtype'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_subtype'], context['report_total'], context['report_xls'], \
            context['orientation'], context['pagesize'] = cashinbankquery(self.request)

        if self.request.COOKIES.get('date_from_' + self.request.resolver_match.app_name):
            context['datefrom'] = datetime.datetime.strptime(self.request.COOKIES.get('date_from_' + self.request.
                                                                                      resolver_match.app_name),
                                                             "%Y-%m-%d")
        else:
            context['datefrom'] = first_day_of_month(datetime.date.today())
        if self.request.COOKIES.get('date_to_' + self.request.resolver_match.app_name):
            context['dateto'] = datetime.datetime.strptime(self.request.COOKIES.get('date_to_' + self.request.
                                                                                    resolver_match.app_name),
                                                           "%Y-%m-%d")
        else:
            context['dateto'] = last_day_of_month(datetime.date.today())
        context['data_list'] = query

        return context


@csrf_exempt
def cashinbankquery(request):
    query = ''
    report_type = ''
    report_xls = ''

    orientation = 'portrait'
    pagesize = 'letter'
    report_subtype = 'Summary of Cash in Bank'

    set_report_type = request.COOKIES.get('report_type_' + request.resolver_match.app_name) if request.COOKIES.get(
        'report_type_' + request.resolver_match.app_name) else 'GJB_S'
    date_from = str(request.COOKIES.get('date_from_' + request.resolver_match.app_name)) if request.COOKIES.get(
        'date_from_' + request.resolver_match.app_name) else str(first_day_of_month(datetime.date.today()))
    date_to = str(request.COOKIES.get('date_to_' + request.resolver_match.app_name)) if request.COOKIES.get(
        'date_to_' + request.resolver_match.app_name) else str(last_day_of_month(datetime.date.today()))

    if set_report_type == 'GJB_S':
        report_type = 'GENERAL JOURNAL BOOK'
        report_xls = 'GJB Summary CB'

        query = Jvdetail.objects.all().filter(isdeleted=0, chartofaccount=Companyparameter.objects.first().
                                              coa_cashinbank_id).exclude(jvmain__status='C')
        query = query.filter(jvmain__jvdate__gte=date_from)
        query = query.filter(jvmain__jvdate__lte=date_to)

    elif set_report_type == 'CDB_S':
        report_type = 'CASH DISBURSEMENT BOOK'
        report_xls = 'CDB Summary CB'

        query = Cvdetail.objects.all().filter(isdeleted=0, chartofaccount=Companyparameter.objects.first().
                                              coa_cashinbank_id).exclude(cvmain__status='C')
        query = query.filter(cvmain__cvdate__gte=date_from)
        query = query.filter(cvmain__cvdate__lte=date_to)

    elif set_report_type == 'CRB_S':
        report_type = 'CASH RECEIPTS BOOK'
        report_xls = 'CRB Summary CB'

        query = Ordetail.objects.all().filter(isdeleted=0).exclude(ormain__status='C')
        query = query.filter(ormain__ordate__gte=date_from)
        query = query.filter(ormain__ordate__lte=date_to)

    query = query.values('bankaccount__code',
                         'bankaccount__bank__code',
                         'bankaccount__bankaccounttype__code') \
        .annotate(Sum('debitamount'), Sum('creditamount'),
                  debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                       default=Sum('debitamount') - Sum('creditamount')),
                  creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                        default=Sum('creditamount') - Sum('debitamount'))) \
        .order_by('bankaccount__code')

    report_total = query.aggregate(Sum('debitdifference'), Sum('creditdifference'))

    return query, report_type, report_subtype, report_total, report_xls, orientation, pagesize


def first_day_of_month(date):
    today_date = date
    if today_date.day > 25:
        today_date += datetime.timedelta(7)
    return today_date.replace(day=1)


def last_day_of_month(date):
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month+1, day=1) - datetime.timedelta(days=1)


def preserve_sort(query, field):
    sort_numbers = []
    last_item = None
    sort_number = 0
    for data in query:
        if last_item is not None:
            if field == 'jv_num':
                if last_item.jv_num == data.jv_num:
                    sort_numbers.append({'sort_number': sort_number})
                    sort_number += 1
                else:
                    sort_number = 1
                    sort_numbers.append({'sort_number': sort_number})
                    sort_number += 1
            elif field == 'cv_num':
                if last_item.cv_num == data.cv_num:
                    sort_numbers.append({'sort_number': sort_number})
                    sort_number += 1
                else:
                    sort_number = 1
                    sort_numbers.append({'sort_number': sort_number})
                    sort_number += 1
            elif field == 'or_num':
                if last_item.or_num == data.or_num:
                    sort_numbers.append({'sort_number': sort_number})
                    sort_number += 1
                else:
                    sort_number = 1
                    sort_numbers.append({'sort_number': sort_number})
                    sort_number += 1
            elif field == 'ap_num':
                if last_item.ap_num == data.ap_num:
                    sort_numbers.append({'sort_number': sort_number})
                    sort_number += 1
                else:
                    sort_number = 1
                    sort_numbers.append({'sort_number': sort_number})
                    sort_number += 1
            else:
                if last_item[field] == data[field]:
                    sort_numbers.append({'sort_number': sort_number})
                    sort_number += 1
                else:
                    sort_number = 1
                    sort_numbers.append({'sort_number': sort_number})
                    sort_number += 1
        else:
            sort_number = 1
            sort_numbers.append({'sort_number': sort_number})
            sort_number += 1
        last_item = data

    return sort_numbers

