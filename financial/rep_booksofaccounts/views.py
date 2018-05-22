from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from journalvoucher.models import Jvdetail
from utils.mixins import ReportContentMixin
from easy_pdf.views import PDFTemplateView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Case, Value, When, F
import datetime


@method_decorator(login_required, name='dispatch')
class ReportView(TemplateView):
    model = Jvdetail
    template_name = 'rep_booksofaccounts/report.html'


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
            context['orientation'], context['pagesize'] = reportresultquery(self.request)

        context['datefrom'] = datetime.datetime.strptime(self.request.COOKIES.get('date_from_' + self.request.
                                                                                  resolver_match.app_name), "%Y-%m-%d")
        context['dateto'] = datetime.datetime.strptime(self.request.COOKIES.get('date_to_' + self.request.
                                                                                resolver_match.app_name), "%Y-%m-%d")
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

    if request.COOKIES.get('report_type_' + request.resolver_match.app_name) == 'GJB_S' or request.COOKIES.\
            get('report_type_' + request.resolver_match.app_name) == 'GJB_D':
        report_type = 'GENERAL JOURNAL BOOK'

        # get all records in Jvdetail
        query = Jvdetail.objects.all().filter(isdeleted=0)

        # filter items based on date_from and date_to from cookies
        if request.COOKIES.get('date_from_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('date_from_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvdate__gte=key_data)
        if request.COOKIES.get('date_to_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('date_to_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvdate__lte=key_data)

        # customize query and pdf settings for Summary
        if request.COOKIES.get('report_type_' + request.resolver_match.app_name) == 'GJB_S':
            report_subtype = '(Summary Entries)'
            report_xls = 'GJB Summary'
            orientation = 'portrait'
            pagesize = 'letter'

            query = query.values('chartofaccount__accountcode',
                                 'chartofaccount__description') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('chartofaccount__accountcode')

            report_total = query.aggregate(Sum('debitdifference'), Sum('creditdifference'))

        # customize query and pdf settings for Detailed
        elif request.COOKIES.get('report_type_' + request.resolver_match.app_name) == 'GJB_D':
            report_subtype = '(Detailed Entries)'
            report_xls = 'GJB Detailed'
            orientation = 'landscape'
            pagesize = 'legal'

            query = query.values('jv_num')\
                .annotate(Sum('debitamount'), Sum('creditamount'))\
                .values('jvmain__jvdate',
                        'jv_num',
                        'jvmain__particular',
                        'chartofaccount__accountcode',
                        'chartofaccount__description',
                        'bankaccount__code',
                        'bankaccount__bank__code',
                        'bankaccount__bankaccounttype__code',
                        'department__code',
                        'department__departmentname',
                        'item_counter',
                        'debitamount__sum',
                        'creditamount__sum')\
                .order_by('jv_num', 'item_counter')
            print query

            report_total = query.aggregate(Sum('debitamount__sum'), Sum('creditamount__sum'))

    return query, report_type, report_subtype, report_total, report_xls, orientation, pagesize


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

        context['datefrom'] = datetime.datetime.strptime(self.request.COOKIES.get('date_from_' + self.request.
                                                                                  resolver_match.app_name), "%Y-%m-%d")
        context['dateto'] = datetime.datetime.strptime(self.request.COOKIES.get('date_to_' + self.request.
                                                                                resolver_match.app_name), "%Y-%m-%d")
        context['data_list'] = query

        return context


@csrf_exempt
def cashinbankquery(request):
    query = ''
    report_type = ''
    report_subtype = ''
    report_total = ''
    report_xls = ''
    orientation = ''
    pagesize = ''

    if request.COOKIES.get('report_type_' + request.resolver_match.app_name) == 'GJB_S':
        report_type = 'GENERAL JOURNAL BOOK'
        report_subtype = 'Summary of Cash in Bank'
        report_xls = 'GJB Summary CB'
        orientation = 'portrait'
        pagesize = 'letter'

        query = Jvdetail.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('date_from_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('date_from_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvdate__gte=key_data)
        if request.COOKIES.get('date_to_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('date_to_' + request.resolver_match.app_name))
            query = query.filter(jvmain__jvdate__lte=key_data)

        query = query.exclude(bankaccount=None)
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
        print query
        print report_total

    return query, report_type, report_subtype, report_total, report_xls, orientation, pagesize
