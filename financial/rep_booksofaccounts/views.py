from django.views.generic import View, TemplateView
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
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
import pandas as pd
from datetime import timedelta
from django.db import connection
from collections import namedtuple
import pandas as pd
import io
import xlsxwriter
import datetime
from django.template.loader import render_to_string

@method_decorator(login_required, name='dispatch')
class ReportView(TemplateView):
    model = Jvdetail
    template_name = 'rep_booksofaccounts/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        context['default_datefrom'] = first_day_of_month(datetime.date.today())
        context['default_dateto'] = last_day_of_month(datetime.date.today())

        return context

def first_day_of_month(date):
    today_date = date
    if today_date.day > 25:
        today_date += datetime.timedelta(7)
    return today_date.replace(day=1)


def last_day_of_month(date):
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month+1, day=1) - datetime.timedelta(days=1)

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = ''
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        title = "GENERAL JOURNAL BOOK - DETAILED ENTRIES"

        if report == '1' or report == '18':
            if report == '18':
                title = "GENERAL JOURNAL BOOK"
            else:
                title = "GENERAL JOURNAL BOOK - DETAILED ENTRIES"
            q = Jvdetail.objects.all().filter(isdeleted=0,jvmain__jvstatus='R').exclude(jvmain__status='C').order_by('jv_date', 'jv_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)
            total = q.exclude(jvmain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
            q = q[:100]
        elif report == '2':
            title = "GENERAL JOURNAL BOOK - SUMMARY ENTRIES"
            q = Jvdetail.objects.all().filter(isdeleted=0,jvmain__jvstatus='R').exclude(jvmain__status='C')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)
            q = q.values('chartofaccount__accountcode','chartofaccount__description') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('chartofaccount__accountcode')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        elif report == '3':
            title = "GENERAL JOURNAL BOOK - SUBSIDIARY ENTRIES"
            q = Jvdetail.objects.all().filter(isdeleted=0,jvmain__jvstatus='R').exclude(jvmain__status='C')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)
            q = q.values('chartofaccount__accountcode', 'chartofaccount__description', 'bankaccount__code', 'employee__firstname', 'employee__middlename', 'employee__lastname',
                         'supplier__name', 'customer__name', 'department__departmentname') \
                .annotate(Sum('debitamount'), Sum('creditamount')) \
                .order_by('chartofaccount__accountcode', 'bankaccount__code', 'employee__lastname', 'employee__firstname', 'employee__middlename',
                          'supplier__name', 'customer__name', 'department__departmentname')

            total = q.aggregate(Sum('debitamount__sum'), Sum('creditamount__sum'))
        elif report == '4':
            title = "CASH DISBURSEMENT BOOK - DETAILED ENTRIES"
            q = Cvdetail.objects.all().filter(isdeleted=0,cvmain__cvstatus='R').exclude(cvmain__status='C').order_by('cv_date', 'cv_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
            total = q.exclude(cvmain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
            q = q[:100]
        elif report == '5':
            title = "CASH DISBURSEMENT BOOK - SUMMARY ENTRIES"
            q = Cvdetail.objects.all().filter(isdeleted=0,cvmain__cvstatus='R').exclude(cvmain__status='C')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
            q = q.values('chartofaccount__accountcode', 'chartofaccount__description') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('chartofaccount__accountcode')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        elif report == '6':
            title = "CASH DISBURSEMENT BOOK - SUBSIDIARY ENTRIES"
            q = Cvdetail.objects.all().filter(isdeleted=0,cvmain__cvstatus='R').exclude(cvmain__status='C')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
            q = q.values('chartofaccount__accountcode', 'chartofaccount__description', 'bankaccount__code',
                         'employee__firstname', 'employee__middlename', 'employee__lastname',
                         'supplier__name', 'customer__name', 'department__departmentname') \
                .annotate(Sum('debitamount'), Sum('creditamount')) \
                .order_by('chartofaccount__accountcode', 'bankaccount__code', 'employee__lastname',
                          'employee__firstname', 'employee__middlename',
                          'supplier__name', 'customer__name', 'department__departmentname')

            total = q.aggregate(Sum('debitamount__sum'), Sum('creditamount__sum'))
        elif report == '7':
            title = "CASH RECEIPTS BOOK - DETAILED ENTRIES"
            q = Ordetail.objects.all().filter(isdeleted=0,ormain__orstatus='R').exclude(ormain__status='C').order_by('or_date', 'or_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
            total = q.exclude(ormain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
            q = q[:100]
        elif report == '8':
            title = "CASH RECEIPTS BOOK - SUMMARY ENTRIES"
            q = Ordetail.objects.all().filter(isdeleted=0,ormain__orstatus='R').exclude(ormain__status='C')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
            q = q.values('chartofaccount__accountcode', 'chartofaccount__description') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('chartofaccount__accountcode')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))

        elif report == '9':
            title = "CASH RECEIPTS BOOK - SUBSIDIARY ENTRIES"
            q = Ordetail.objects.all().filter(isdeleted=0,ormain__orstatus='R').exclude(ormain__status='C')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
            q = q.values('chartofaccount__accountcode', 'chartofaccount__description', 'bankaccount__code',
                         'employee__firstname', 'employee__middlename', 'employee__lastname',
                         'supplier__name', 'customer__name', 'department__departmentname') \
                .annotate(Sum('debitamount'), Sum('creditamount')) \
                .order_by('chartofaccount__accountcode', 'bankaccount__code', 'employee__lastname',
                          'employee__firstname', 'employee__middlename',
                          'supplier__name', 'customer__name', 'department__departmentname')

            total = q.aggregate(Sum('debitamount__sum'), Sum('creditamount__sum'))
        elif report == '10':
            title = "ACCOUNTS PAYABLE VOUCHER - DETAILED ENTRIES"
            q = Apdetail.objects.all().filter(isdeleted=0,apmain__apstatus='R').exclude(apmain__status='C').order_by('ap_date', 'ap_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
            total = q.exclude(apmain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
            q = q[:100]
        elif report == '11':
            title = "ACCOUNTS PAYABLE VOUCHER - SUMMARY ENTRIES"
            q = Apdetail.objects.all().filter(isdeleted=0,apmain__apstatus='R').exclude(apmain__status='C')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
            q = q.values('chartofaccount__accountcode', 'chartofaccount__description') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('chartofaccount__accountcode')

            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))

        elif report == '12':
            title = "ACCOUNTS PAYABLE VOUCHER - SUBSIDIARY ENTRIES"
            q = Apdetail.objects.all().filter(isdeleted=0,apmain__apstatus='R').exclude(apmain__status='C')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
            q = q.values('chartofaccount__accountcode', 'chartofaccount__description', 'bankaccount__code',
                         'employee__firstname', 'employee__middlename', 'employee__lastname',
                         'supplier__name', 'customer__name', 'department__departmentname') \
                .annotate(Sum('debitamount'), Sum('creditamount')) \
                .order_by('chartofaccount__accountcode', 'bankaccount__code', 'employee__lastname',
                          'employee__firstname', 'employee__middlename',
                          'supplier__name', 'customer__name', 'department__departmentname')

            total = q.aggregate(Sum('debitamount__sum'), Sum('creditamount__sum'))
        elif report == '13':
            totald = {}
            total_debit = {}
            totalc = {}
            total_credit = {}
            title = "ACCOUNTS PAYABLE VOUCHER (with Branch) - SUMMARY ENTRIES"
            totald['debitamount__sum__sum'] = 0
            total_debit['debitamount__sum__sum'] = 0
            totalc['creditamount__sum__sum'] = 0
            total_credit['creditamount__sum__sum'] = 0
            q = Apdetail.objects.all().filter(isdeleted=0,apmain__apstatus='R',department__isnull=False)\
                .exclude(apmain__status='C').exclude(chartofaccount=Companyparameter.objects.first().coa_cashinbank)\
                .exclude(chartofaccount=Companyparameter.objects.first().coa_aptrade)
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
            q = q.values('department__code', 'department__departmentname', 'branch__code') \
                .annotate(Sum('debitamount')) \
                .order_by('department__code')
            totald = q.aggregate(Sum('debitamount__sum'))

            q2 = Apdetail.objects.all().filter(isdeleted=0,apmain__apstatus='R', department__isnull=False).exclude(creditamount=0) \
                .exclude(apmain__status='C').exclude(chartofaccount=Companyparameter.objects.first().coa_cashinbank) \
                .exclude(chartofaccount=Companyparameter.objects.first().coa_aptrade)
            if dfrom != '':
                q2 = q2.filter(ap_date__gte=dfrom)
            if dto != '':
                q2 = q2.filter(ap_date__lte=dto)
            q2 = q2.values('department__code', 'department__departmentname', 'branch__code') \
                .annotate(Sum('creditamount')) \
                .order_by('department__code')
            totalc = q2.aggregate(Sum('creditamount__sum'))

            cdebit = Apdetail.objects.all().filter(isdeleted=0,apmain__apstatus='R') \
                .filter((Q(chartofaccount__accountcode__startswith='1') | Q(
                chartofaccount__accountcode__startswith='2'))).exclude(apmain__status='C') \
                .exclude(chartofaccount=Companyparameter.objects.first().coa_cashinbank) \
                .exclude(chartofaccount=Companyparameter.objects.first().coa_aptrade)
            if dfrom != '':
                cdebit = cdebit.filter(ap_date__gte=dfrom)
            if dto != '':
                cdebit = cdebit.filter(ap_date__lte=dto)
            cdebit = cdebit.values('chartofaccount__description').annotate(Sum('debitamount')). \
                filter(debitamount__sum__gt=0). \
                order_by('chartofaccount__accountcode')
            total_debit = cdebit.aggregate(Sum('debitamount__sum'))

            ccredit = Apdetail.objects.all().filter(isdeleted=0,apmain__apstatus='R')\
                .filter((Q(chartofaccount__accountcode__startswith='1')|Q(chartofaccount__accountcode__startswith='2'))).exclude(apmain__status='C')\
                .exclude(chartofaccount=Companyparameter.objects.first().coa_cashinbank) \
                .exclude(chartofaccount=Companyparameter.objects.first().coa_aptrade)
            if dfrom != '':
                ccredit = ccredit.filter(ap_date__gte=dfrom)
            if dto != '':
                ccredit = ccredit.filter(ap_date__lte=dto)
            ccredit = ccredit.values('chartofaccount__description').annotate(Sum('creditamount')). \
                filter(creditamount__sum__gt=0). \
                order_by('chartofaccount__accountcode')
            total_credit = ccredit.aggregate(Sum('creditamount__sum'))
        elif report == '14':
            title = "GENERAL LEDGER BOOK"
            q = query_bir(report, dfrom, dto)
            q = q[:100]
        elif report == '15':
            title = "CASH RECEIPT BOOK"
            q = query_bir(report, dfrom, dto)
            q = q[:100]
        elif report == '16':
            title = "PURCHASE BOOK"
            q = query_bir(report, dfrom, dto)
            q = q[:100]
        elif report == '17':
            title = "GENERAL LEDGER BOOK"
            q = query_bir(report, dfrom, dto)
            q = q[:100]
        elif report == '19':
            title = "PURCHASE BOOK"
            q = query_bir(report, dfrom, dto)
            q = q[:100]

        else:
            q = Jvdetail.objects.filter(isdeleted=0,jvmain__jvstatus='R').exclude(jvmain__status='C').order_by('jv_date', 'jv_num')[:0]

        list = q
        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "datefrom": dfrom,
            "dateto": dto,
            "username": request.user,
        }
        if report == '1':
            return Render.render('rep_booksofaccounts/report_1.html', context)
        elif report == '2':
            return Render.render('rep_booksofaccounts/report_2.html', context)
        elif report == '3':
            return Render.render('rep_booksofaccounts/report_3.html', context)
        elif report == '4':
            return Render.render('rep_booksofaccounts/report_4.html', context)
        elif report == '5':
            return Render.render('rep_booksofaccounts/report_5.html', context)
        elif report == '6':
            return Render.render('rep_booksofaccounts/report_6.html', context)
        elif report == '7':
            return Render.render('rep_booksofaccounts/report_7.html', context)
        elif report == '8':
            return Render.render('rep_booksofaccounts/report_8.html', context)
        elif report == '9':
            return Render.render('rep_booksofaccounts/report_9.html', context)
        elif report == '10':
            return Render.render('rep_booksofaccounts/report_10.html', context)
        elif report == '11':
            return Render.render('rep_booksofaccounts/report_11.html', context)
        elif report == '12':
            return Render.render('rep_booksofaccounts/report_12.html', context)
        elif report == '13':
            context['list2'] = q2
            context['chart_credit'] = ccredit
            context['chart_debit'] = cdebit

            totalcc = totalc['creditamount__sum__sum']
            if totalc['creditamount__sum__sum'] is None:
                totalcc = 0

            totaldd = totald['debitamount__sum__sum']
            if totald['debitamount__sum__sum'] is None:
                totaldd = 0

            total_ddebit = total_debit['debitamount__sum__sum']
            if total_debit['debitamount__sum__sum'] is None:
                total_ddebit = 0

            total_ccredit = total_credit['creditamount__sum__sum']
            if total_credit['creditamount__sum__sum'] is None:
                total_ccredit = 0

            context['totalamount'] = (totaldd + total_ddebit) - (totalcc + total_ccredit)
            return Render.render('rep_booksofaccounts/report_13.html', context)
        elif report == '14':
            return Render.render('rep_booksofaccounts/report_14.html', context)
        elif report == '15':
            return Render.render('rep_booksofaccounts/report_15.html', context)
        elif report == '16':
            return Render.render('rep_booksofaccounts/report_16.html', context)
        elif report == '17':
            return Render.render('rep_booksofaccounts/report_17.html', context)
        elif report == '18':
            return Render.render('rep_booksofaccounts/report_18.html', context)
        elif report == '19':
            return Render.render('rep_booksofaccounts/report_19.html', context)
        else:
            return Render.render('rep_booksofaccounts/report_1.html', context)

@method_decorator(login_required, name='dispatch')
class GeneratePDFCashInBank(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = ''
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        title = "GENERAL JOURNAL BOOK - SUMMARY ENTRIES"
        subtitle = ""

        cashinbank = Companyparameter.objects.first().coa_cashinbank_id
        if report == '2':
            title = "GENERAL JOURNAL BOOK - SUMMARY ENTRIES"
            subtitle = "Summary of Cash In Bank"
            q = Jvdetail.objects.all().filter(isdeleted=0,chartofaccount=cashinbank).exclude(jvmain__status='C')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)
            q = q.values('bankaccount__code',
                         'bankaccount__bank__code',
                         'bankaccount__bankaccounttype__code') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('bankaccount__code')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        elif report == '5':
            title = "CASH DISBURSEMENT BOOK - SUMMARY ENTRIES"
            subtitle = "Summary of Cash In Bank"
            q = Cvdetail.objects.all().filter(isdeleted=0,chartofaccount=cashinbank).exclude(cvmain__status='C')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
            q = q.values('bankaccount__code',
                         'bankaccount__bank__code',
                         'bankaccount__bankaccounttype__code') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('bankaccount__code')

            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        elif report == '8':
            title = "CASH RECEIPTS BOOK - SUMMARY ENTRIES"
            subtitle = "Summary of Cash In Bank"
            q = Ordetail.objects.all().filter(isdeleted=0,chartofaccount=cashinbank).exclude(ormain__status='C')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
            q = q.values('bankaccount__code',
                         'bankaccount__bank__code',
                         'bankaccount__bankaccounttype__code') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('bankaccount__code')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))

        elif report == '11':
            title = "ACCOUNTS PAYABLE VOUCHER - SUMMARY ENTRIES"
            subtitle = "Summary of Cash In Bank"
            q = Apdetail.objects.all().filter(isdeleted=0,chartofaccount=cashinbank).exclude(apmain__status='C')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
            q = q.values('bankaccount__code',
                         'bankaccount__bank__code',
                         'bankaccount__bankaccounttype__code') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('bankaccount__code')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        else:
            q = Jvdetail.objects.filter(isdeleted=0).order_by('jv_date', 'jv_num')[:0]

        list = q
        context = {
            "title": title,
            "subtitle": subtitle,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "datefrom": dfrom,
            "dateto": dto,
            "username": request.user,
        }
        if report == '2':
            return Render.render('rep_booksofaccounts/summary_cashinbank.html', context)
        else:
            return Render.render('rep_booksofaccounts/summary_cashinbank.html', context)

@method_decorator(login_required, name='dispatch')
class GeneratePDFDepartment(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = ''
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        title = "GENERAL JOURNAL BOOK - SUMMARY ENTRIES"
        subtitle = ""

        cashinbank = Companyparameter.objects.first().coa_cashinbank_id
        if report == '2':
            title = "GENERAL JOURNAL BOOK - SUMMARY ENTRIES"
            subtitle = "Summary of Department"
            q = Jvdetail.objects.all().filter(isdeleted=0,department__isnull=False).exclude(jvmain__status='C')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)
            q = q.values('department__code',
                         'department__departmentname',
                         'department__sectionname', 'department__branchstatus') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('department__code')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        elif report == '5':
            title = "CASH DISBURSEMENT BOOK - SUMMARY ENTRIES"
            subtitle = "Summary of Department"
            q = Cvdetail.objects.all().filter(isdeleted=0,department__isnull=False).exclude(cvmain__status='C')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
            q = q.values('department__code',
                         'department__departmentname',
                         'department__sectionname', 'department__branchstatus') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('department__code')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        elif report == '8':
            title = "CASH RECEIPTS BOOK - SUMMARY ENTRIES"
            subtitle = "Summary of Department"
            q = Ordetail.objects.all().filter(isdeleted=0,department__isnull=False).exclude(ormain__status='C')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
            q = q.values('department__code',
                         'department__departmentname',
                         'department__sectionname', 'department__branchstatus') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('department__code')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        elif report == '11':
            title = "ACCOUNTS PAYABLE VOUCHER - SUMMARY ENTRIES"
            subtitle = "Summary of Department"
            q = Apdetail.objects.all().filter(isdeleted=0, department__isnull=False) \
                .exclude(apmain__status='C').exclude(chartofaccount=Companyparameter.objects.first().coa_cashinbank) \
                .exclude(chartofaccount=Companyparameter.objects.first().coa_aptrade)
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
            q = q.values('department__code',
                         'department__departmentname',
                         'department__sectionname', 'department__branchstatus') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('department__code')
            total = q.aggregate(Sum('debitamount__sum'), Sum('creditamount__sum'))
            print total
        else:
            q = Jvdetail.objects.filter(isdeleted=0).order_by('jv_date', 'jv_num')[:0]

        list = q
        context = {
            "title": title,
            "subtitle": subtitle,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "report": report,
            "datefrom": dfrom,
            "dateto": dto,
            "username": request.user,
        }
        if report == '2':
            return Render.render('rep_booksofaccounts/summary_department.html', context)
        else:
            return Render.render('rep_booksofaccounts/summary_department.html', context)



@method_decorator(login_required, name='dispatch')
class GenerateExcel(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = ''
        report = request.GET['report']
        dfrom = request.GET['dfrom']
        dto = request.GET['dto']
        title = "GENERAL JOURNAL BOOK - DETAILED ENTRIES"
        filename = "data"

        if report == '1':
            title = "GENERAL JOURNAL BOOK - DETAILED ENTRIES"
            q = Jvdetail.objects.all().filter(isdeleted=0, jvmain__jvstatus='R').exclude(jvmain__status='C').order_by(
                'jv_date', 'jv_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)

            total = q.exclude(jvmain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
        elif report == '4':
            title = "CASH DISBURSEMENT BOOK - DETAILED ENTRIES"
            q = Cvdetail.objects.all().filter(isdeleted=0, cvmain__cvstatus='R').exclude(cvmain__status='C').order_by(
                'cv_date', 'cv_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
            total = q.exclude(cvmain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
        elif report == '7':
            title = "CASH RECEIPTS BOOK - DETAILED ENTRIES"
            q = Ordetail.objects.all().filter(isdeleted=0, ormain__orstatus='R').exclude(ormain__status='C').order_by(
                'or_date', 'or_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
            total = q.exclude(ormain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
        elif report == '10':
            title = "ACCOUNTS PAYABLE VOUCHER - DETAILED ENTRIES"
            q = Apdetail.objects.all().filter(isdeleted=0, apmain__apstatus='R').exclude(apmain__status='C').order_by(
                'ap_date', 'ap_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
            total = q.exclude(apmain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
        elif report == '14' or report == '17':
            title = "GENERAL LEDGER BOOK - BIR FORMAT"
        elif report == '15':
            title = "CASH RECEIPTS BOOK - BIR FORMAT"
        elif report == '18':
            title = "GENERAL JOURNAL BOOK - BIR FORMAT"
            q = Jvdetail.objects.all().filter(isdeleted=0, jvmain__jvstatus='R').exclude(jvmain__status='C').order_by(
                'jv_date', 'jv_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)
            total = q.exclude(jvmain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
        elif report == '16' or report == '19':
            title = "PURCHASE BOOK - BIR FORMAT"
        else:
            q = Jvdetail.objects.filter(isdeleted=0).order_by('jv_date', 'jv_num')[:0]

        list = q
        print list
        if report == '1':

            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})
            cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

            # title

            worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
            worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
            worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
            worksheet.write('A4', 'GENERAL JOURNAL BOOK - DETAILED ENTRIES', bold)
            worksheet.write('A5', 'for the period ' + str(dfrom) + ' to ' + str(dto), bold)

            worksheet.write('C1', 'Software:')
            worksheet.write('C2', 'User:')
            worksheet.write('C3', 'Datetime:')

            worksheet.write('D1', 'iES Financial System v. 1.0')
            worksheet.write('D2', str(request.user.username))
            worksheet.write('D3', datetime.datetime.now(), cell_format)


            # header
            worksheet.write('A7', 'Date', bold)
            worksheet.write('B7', 'Number', bold)
            worksheet.write('C7', 'Particulars', bold)
            worksheet.write('D7', 'Account Number', bold)
            worksheet.write('E7', 'Account Title', bold)
            worksheet.write('F7', 'Code', bold)
            worksheet.write('G7', 'Particulars', bold)
            worksheet.write('H7', 'Debit Amount', bold)
            worksheet.write('I7', 'Credit Amount', bold)

            row = 7
            col = 0
            jvnum = ''
            bankaccount = ''
            department = ''
            departmentname = ''
            for data in list:

                worksheet.write(row, col, data.jv_date, formatdate)
                worksheet.write(row, col + 1, data.jv_num)
                worksheet.write(row, col + 2, data.jvmain.particular)
                worksheet.write(row, col + 3, data.chartofaccount.accountcode)
                worksheet.write(row, col + 4, data.chartofaccount.description)

                if data.bankaccount:
                    bankaccount = data.bankaccount.code
                if data.department:
                    department = data.department.code
                    departmentname = data.department.departmentname

                worksheet.write(row, col + 5, bankaccount+' '+department)
                worksheet.write(row, col + 6, bankaccount+' '+department+' '+departmentname)
                worksheet.write(row, col + 7, float(format(data.debitamount, '.2f')))
                worksheet.write(row, col + 8, float(format(data.creditamount, '.2f')))

                bankaccount = ""
                department = ""
                departmentname = ""
                row += 1

            workbook.close()

            # Rewind the buffer.
            output.seek(0)

            # Set up the Http response.
            filename = "generaljournalbook_detailed.xlsx"
        elif report == '4':

            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})
            cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

            # title

            worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
            worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
            worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
            worksheet.write('A4', 'CASH DISBURSEMENT BOOK - DETAILED ENTRIES', bold)
            worksheet.write('A5', 'for the period ' + str(dfrom) + ' to ' + str(dto), bold)

            worksheet.write('C1', 'Software:')
            worksheet.write('C2', 'User:')
            worksheet.write('C3', 'Datetime:')

            worksheet.write('D1', 'iES Financial System v. 1.0')
            worksheet.write('D2', str(request.user.username))
            worksheet.write('D3', datetime.datetime.now(), cell_format)



            # header
            worksheet.write('A7', 'Date', bold)
            worksheet.write('B7', 'Number', bold)
            worksheet.write('C7', 'Payee', bold)
            worksheet.write('D7', 'Particulars', bold)
            worksheet.write('E7', 'Bank', bold)
            worksheet.write('F7', 'Check', bold)
            worksheet.write('G7', 'Amount', bold)
            worksheet.write('H7', 'Account Number', bold)
            worksheet.write('I7', 'Account Title', bold)
            worksheet.write('J7', 'Subledger', bold)
            worksheet.write('K7', 'Debit Amount', bold)
            worksheet.write('L7', 'Credit Amount', bold)

            row = 7
            col = 0
            jvnum = ''
            payee = ''
            particulars = ''
            bankaccount = ''
            department = ''
            departmentname = ''
            for data in list:

                worksheet.write(row, col, data.cv_date, formatdate)
                worksheet.write(row, col + 1, data.cv_num)

                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C  A  N  C  E  L  L  E  D')
                    worksheet.write(row, col + 3, '')
                else:
                    worksheet.write(row, col + 2, data.cvmain.payee_name)
                    if data.bankaccount:
                        bankaccount = data.cvmain.bankaccount.code
                    worksheet.write(row, col + 3, data.cvmain.particulars)
                    worksheet.write(row, col + 4, bankaccount)
                    worksheet.write(row, col + 5, data.cvmain.checknum)
                    worksheet.write(row, col + 6, data.cvmain.amount)

                worksheet.write(row, col + 7, data.chartofaccount.accountcode)
                worksheet.write(row, col + 8, data.chartofaccount.description)

                if data.bankaccount:
                    bankaccount = data.bankaccount.code
                if data.department:
                    department = data.department.code
                    departmentname = data.department.departmentname

                worksheet.write(row, col + 9, bankaccount+' '+department+' '+departmentname)

                worksheet.write(row, col + 10, float(format(data.debitamount, '.2f')))
                worksheet.write(row, col + 11, float(format(data.creditamount, '.2f')))

                bankaccount = ""
                departmentname = ""
                department = ""

                row += 1

            workbook.close()

            # Rewind the buffer.
            output.seek(0)

            # Set up the Http response.
            filename = "cashdisbursementbook_detailed.xlsx"
        elif report == '7':

            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})
            cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

            # title

            worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
            worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
            worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
            worksheet.write('A4', 'CASH RECEIPTS BOOK - DETAILED ENTRIES', bold)
            worksheet.write('A5', 'for the period ' + str(dfrom) + ' to ' + str(dto), bold)

            worksheet.write('C1', 'Software:')
            worksheet.write('C2', 'User:')
            worksheet.write('C3', 'Datetime:')

            worksheet.write('D1', 'iES Financial System v. 1.0')
            worksheet.write('D2', str(request.user.username))
            worksheet.write('D3', datetime.datetime.now(), cell_format)


            # header
            worksheet.write('A7', 'Date', bold)
            worksheet.write('B7', 'Number', bold)
            worksheet.write('C7', 'Payee', bold)
            worksheet.write('D7', 'Particulars', bold)
            worksheet.write('E7', 'Amount', bold)
            worksheet.write('F7', 'Bank', bold)
            worksheet.write('G7', 'Account Number', bold)
            worksheet.write('H7', 'Account Title', bold)
            worksheet.write('I7', 'Subledger', bold)
            worksheet.write('J7', 'Debit Amount', bold)
            worksheet.write('K7', 'Credit Amount', bold)

            row = 7
            col = 0
            jvnum = ''
            payee = ''
            particulars = ''
            bankaccount = ''
            banktype = ''
            department = ''
            departmentname = ''
            for data in list:

                worksheet.write(row, col, data.or_date, formatdate)
                worksheet.write(row, col + 1, data.or_num)

                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C  A  N  C  E  L  L  E  D')
                    worksheet.write(row, col + 3, '')
                else:
                    worksheet.write(row, col + 2, data.ormain.payee_name)
                    if data.bankaccount:
                        bankaccount = data.ormain.bankaccount.code
                    worksheet.write(row, col + 3, data.ormain.particulars)

                worksheet.write(row, col + 4, float(format(data.ormain.amount, '.2f')))
                worksheet.write(row, col + 5, data.ormain.bankaccount.code)

                worksheet.write(row, col + 6, data.chartofaccount.accountcode)
                worksheet.write(row, col + 7, data.chartofaccount.description)

                print data.ormain.amount
                if data.bankaccount:
                    bankaccount = data.bankaccount.code
                    banktype = data.bankaccount.bankaccounttype.code
                if data.department:
                    department = data.department.code
                    departmentname = data.department.departmentname

                worksheet.write(row, col + 8, bankaccount+' '+banktype+' '+department+' '+departmentname)

                worksheet.write(row, col + 9, float(format(data.debitamount, '.2f')))
                worksheet.write(row, col + 10, float(format(data.creditamount, '.2f')))

                bankaccount = ""
                banktype = ""
                departmentname = ""
                department = ""

                row += 1

            workbook.close()

            # Rewind the buffer.
            output.seek(0)

            # Set up the Http response.
            filename = "cashreceiptsbook_detailed.xlsx"
        elif report == '10':

            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})
            cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

            # title

            worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
            worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
            worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
            worksheet.write('A4', 'ACCOUNTS PAYABLE VOUCHER - DETAILED ENTRIES', bold)
            worksheet.write('A5', 'for the period ' + str(dfrom) + ' to ' + str(dto), bold)

            worksheet.write('C1', 'Software:')
            worksheet.write('C2', 'User:')
            worksheet.write('C3', 'Datetime:')

            worksheet.write('D1', 'iES Financial System v. 1.0')
            worksheet.write('D2', str(request.user.username))
            worksheet.write('D3', datetime.datetime.now(), cell_format)

            # header
            worksheet.write('A7', 'Date', bold)
            worksheet.write('B7', 'Number', bold)
            worksheet.write('C7', 'Payee', bold)
            worksheet.write('D7', 'TIN', bold)
            worksheet.write('E7', 'Address', bold)
            worksheet.write('F7', 'Particulars', bold)
            worksheet.write('G7', 'Account Number', bold)
            worksheet.write('H7', 'Account Title', bold)
            worksheet.write('I7', 'Subledger', bold)
            worksheet.write('J7', 'Debit Amount', bold)
            worksheet.write('K7', 'Credit Amount', bold)


            row = 7
            col = 0
            jvnum = ''
            payee = ''
            particulars = ''
            bankaccount = ''
            department = ''
            departmentname = ''
            emp = ''
            empname = ''
            for data in list:

                worksheet.write(row, col, data.ap_date, formatdate)
                worksheet.write(row, col + 1, data.ap_num)

                if data.status == 'C':
                    worksheet.write(row, col + 2, 'C  A  N  C  E  L  L  E  D')
                    worksheet.write(row, col + 3, '')
                else:
                    worksheet.write(row, col + 2, data.apmain.payeename)
                    worksheet.write(row, col + 5, data.apmain.particulars)

                worksheet.write(row, col + 3, data.apmain.payee.tin)
                worksheet.write(row, col + 4, data.apmain.payee.address1 + ' ' + data.apmain.payee.address2 + ' ' + data.apmain.payee.address3)

                worksheet.write(row, col + 6, data.chartofaccount.accountcode)
                worksheet.write(row, col + 7, data.chartofaccount.description)

                if data.department:
                    department = data.department.code
                    departmentname = data.department.departmentname
                if data.employee:
                    emp = data.employee.code
                    empname = data.employee.firstname+' '+data.employee.lastname

                worksheet.write(row, col + 8,department+' '+departmentname+' '+empname)

                worksheet.write(row, col + 9, float(format(data.debitamount, '.2f')))
                worksheet.write(row, col + 10, float(format(data.creditamount, '.2f')))

                department = ""
                departmentname = ""
                emp = ""
                empname = ""
                row += 1

            workbook.close()

            # Rewind the buffer.
            output.seek(0)

            # Set up the Http response. Accounts Payable Voucher Book
            filename = "accountspayablevoucher_detailed.xlsx"
        elif report == '14':
            print 'gen ledger'

            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})
            cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

            # title

            worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
            worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
            worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
            worksheet.write('A4', 'GENERAL LEDGER BOOK', bold)
            worksheet.write('A5', 'for the period ' + str(dfrom) + ' to ' + str(dto), bold)

            worksheet.write('C1', 'Software:')
            worksheet.write('C2', 'User:')
            worksheet.write('C3', 'Datetime:')

            worksheet.write('D1', 'iES Financial System v. 1.0')
            worksheet.write('D2', str(request.user.username))
            worksheet.write('D3', datetime.datetime.now(), cell_format)

            # header
            worksheet.write('A7', 'DATE', bold)
            worksheet.write('B7', 'TRANSACTION', bold)
            worksheet.write('C7', 'REFERENCE', bold)
            worksheet.write('D7', 'PARTICULARS', bold)
            worksheet.write('E7', 'ACCOUNT NUMBER', bold)
            worksheet.write('F7', 'ACCOUNT TITLE', bold)
            worksheet.write('G7', 'DEBIT', bold)
            worksheet.write('H7', 'CREDIT', bold)

            row = 7
            col = 0
            q = query_bir(report, dfrom, dto)
            new_list = []
            if q:
                df = pd.DataFrame(q)
                for index, data in df.iterrows():
                    worksheet.write(row, col, data['transdate'], formatdate)
                    worksheet.write(row, col + 1, data['transtype'])
                    worksheet.write(row, col + 2, data['reference'])
                    worksheet.write(row, col + 3, data['particulars'],)
                    worksheet.write(row, col + 4, data['accountcode'])
                    worksheet.write(row, col + 5, data['description'])
                    worksheet.write(row, col + 6, float(format(data['debit'], '.2f')))
                    worksheet.write(row, col + 7, float(format(data['credit'], '.2f')))
                    row += 1

            workbook.close()

            # Rewind the buffer.
            output.seek(0)

            # Set up the Http response.
            filename = "generalledgerbook_bir.xlsx"

        elif report == '15':
            print 'cash receipt books'
            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})
            cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

            # title

            worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
            worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
            worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
            worksheet.write('A4', 'CASH RECEIPT BOOK', bold)
            worksheet.write('A5', 'for the period ' + str(dfrom) + ' to ' + str(dto), bold)

            worksheet.write('C1', 'Software:')
            worksheet.write('C2', 'User:')
            worksheet.write('C3', 'Datetime:')

            worksheet.write('D1', 'iES Financial System v. 1.0')
            worksheet.write('D2', str(request.user.username))
            worksheet.write('D3', datetime.datetime.now(), cell_format)

            # header
            worksheet.write('A7', 'DATE', bold)
            worksheet.write('B7', 'REFERENCE', bold)
            worksheet.write('C7', 'PAYOR', bold)
            worksheet.write('D7', 'PARTICULARS', bold)
            worksheet.write('E7', 'ACCOUNT NUMBER', bold)
            worksheet.write('F7', 'ACCOUNT TITLE', bold)
            worksheet.write('G7', 'DEBIT', bold)
            worksheet.write('H7', 'CREDIT', bold)
            worksheet.write('I7', 'BANK ACCOUNT', bold)

            row = 7
            col = 0
            q = query_bir(report, dfrom, dto)
            new_list = []
            if q:
                df = pd.DataFrame(q)
                for index, data in df.iterrows():
                    worksheet.write(row, col, data['ordate'], formatdate)
                    worksheet.write(row, col + 1, data['ornum'])
                    worksheet.write(row, col + 2, data['payee_name'])
                    worksheet.write(row, col + 3, data['particulars'], )
                    worksheet.write(row, col + 4, data['accountcode'])
                    worksheet.write(row, col + 5, data['description'])
                    worksheet.write(row, col + 6, float(format(data['debitamount'], '.2f')))
                    worksheet.write(row, col + 7, float(format(data['creditamount'], '.2f')))
                    worksheet.write(row, col + 8, data['bankacount'])
                    row += 1

            workbook.close()

            # Rewind the buffer.
            output.seek(0)

            # Set up the Http response.
            filename = "cashreceiptbooks_bir.xlsx"

        elif report == '16':

            print 'purchase books'

            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            formatdatetime = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})
            cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

            # title
            worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
            worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
            worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
            worksheet.write('A4', 'PURCHASE BOOK', bold)
            worksheet.write('A5', 'for the period ' + str(dfrom) + ' to ' + str(dto), bold)

            worksheet.write('C1', 'Software:')
            worksheet.write('C2', 'User:')
            worksheet.write('C3', 'Datetime:')

            worksheet.write('D1', 'iES Financial System v. 1.0')
            worksheet.write('D2', str(request.user.username))
            worksheet.write('D3', datetime.datetime.now(), cell_format)


            # header
            # PO Number, PO Date, Reference, Brief Description, Supplier, TIN, Address, Total Quantity, Gross Amount,
            # Discount Amount, Vatable, VAT Exempt (blank header in excel), VAT Zero-Rated, VAT Amount (change VAT Exempt header to VAT Amount),
            # Net Amount, Total Amount (still included since not sure if duplicate), VAT Rate, APV Amount (still included), ATC Amount.

            worksheet.write('A7', 'PO Number', bold)
            worksheet.write('B7', 'PO Date', bold)
            worksheet.write('C7', 'Reference', bold)
            worksheet.write('D7', 'Brief Description', bold)
            worksheet.write('E7', 'Supplier', bold)
            worksheet.write('F7', 'TIN', bold)
            worksheet.write('G7', 'Address', bold)
            worksheet.write('H7', 'Total Quantity', bold)
            worksheet.write('I7', 'Gross Amount', bold)
            worksheet.write('J7', 'Discount Amount', bold)
            worksheet.write('K7', 'Vatable', bold)
            worksheet.write('L7', 'VAT Exempt', bold)
            worksheet.write('M7', 'VAT Zero-Rated', bold)
            worksheet.write('N7', 'VAT Amount', bold)
            worksheet.write('O7', 'Net Amount', bold)
            worksheet.write('P7', 'Total Amount', bold)
            worksheet.write('Q7', 'VAT Rate', bold)
            worksheet.write('R7', 'APV Amount', bold)
            worksheet.write('S7', 'ATC Amount', bold)

            # PO Number, PO Date, Reference, Brief Description, Supplier, TIN, Address, Total Quantity, Gross Amount,
            # Discount Amount, Vatable, VAT Exempt (blank header in excel), VAT Zero-Rated, VAT Amount (change VAT Exempt header to VAT Amount),
            # Net Amount, Total Amount (still included since not sure if duplicate), VAT Rate, APV Amount (still included), ATC Amount.
            row = 7
            col = 0
            q = query_bir(report, dfrom, dto)
            print q
            new_list = []
            if q:
                df = pd.DataFrame(q)
                for index, data in df.iterrows():
                    print data['ponum']
                    worksheet.write(row, col, data['ponum'])
                    #print '1'
                    worksheet.write(row, col + 1, data['podate'], formatdate)
                    #print '2'
                    worksheet.write(row, col + 2, data['refnum'], )
                    #print '3'
                    worksheet.write(row, col + 3, data['particulars'])
                    #print '4'
                    worksheet.write(row, col + 4, data['supplier_name'])
                    #print '5'
                    worksheet.write(row, col + 5, data['tin'])
                    #print '6'
                    worksheet.write(row, col + 6,   data['address'])
                    #print '7'
                    worksheet.write(row, col + 7, float(format(data['totalquantity'], '.2f')))
                    worksheet.write(row, col + 8, float(format(data['grossamount'], '.2f')))
                    worksheet.write(row, col + 9, float(format(data['discountamount'], '.2f')))
                    worksheet.write(row, col + 10, float(format(data['vatable'], '.2f')))
                    worksheet.write(row, col + 11, float(format(data['vatexempt'], '.2f')))
                    worksheet.write(row, col + 12, float(format(data['vatzerorated'], '.2f')))
                    worksheet.write(row, col + 13, float(format(data['vatamount'], '.2f')))
                    worksheet.write(row, col + 14, float(format(data['netamount'], '.2f')))
                    worksheet.write(row, col + 15, float(format(data['totalamount'], '.2f')))
                    worksheet.write(row, col + 16, float(format(data['vatrate'], '.2f')))
                    worksheet.write(row, col + 17, float(format(data['apvamount'], '.2f')))
                    worksheet.write(row, col + 18, float(format(data['atcamount'], '.2f')))

                    row += 1

            workbook.close()

            # Rewind the buffer.
            output.seek(0)

            # Set up the Http response.
            filename = "purchasebooks_bir.xlsx"

        elif report == '17':
            print 'gen ledger v2'

            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})
            cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

            # title

            worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
            worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
            worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
            worksheet.write('A4', 'GENERAL LEDGER BOOK', bold)
            worksheet.write('A5', 'for the period ' + str(dfrom) + ' to ' + str(dto), bold)

            worksheet.write('C1', 'Software:')
            worksheet.write('C2', 'User:')
            worksheet.write('C3', 'Datetime:')

            worksheet.write('D1', 'iES Financial System v. 1.0')
            worksheet.write('D2', str(request.user.username))
            worksheet.write('D3', datetime.datetime.now(), cell_format)

            # header
            worksheet.write('A7', 'DATE', bold)
            worksheet.write('B7', 'REFERENCE', bold)
            worksheet.write('C7', 'PARTICULARS', bold)
            worksheet.write('D7', 'ACCOUNT TITLE', bold)
            worksheet.write('E7', 'DEBIT', bold)
            worksheet.write('F7', 'CREDIT', bold)

            row = 7
            col = 0
            q = query_bir(report, dfrom, dto)
            new_list = []
            if q:
                df = pd.DataFrame(q)
                for index, data in df.iterrows():
                    worksheet.write(row, col, data['transdate'], formatdate)
                    worksheet.write(row, col + 1, data['transtype']+''+data['reference'])
                    worksheet.write(row, col + 2, data['particulars'],)
                    worksheet.write(row, col + 3, data['description'])
                    worksheet.write(row, col + 4, float(format(data['debit'], '.2f')))
                    worksheet.write(row, col + 5, float(format(data['credit'], '.2f')))
                    row += 1

            workbook.close()

            # Rewind the buffer.
            output.seek(0)

            # Set up the Http response.
            filename = "generalledgerbook_birv2.xlsx"

        if report == '18':

            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})
            cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

            # title

            worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
            worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
            worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
            worksheet.write('A4', 'GENERAL JOURNAL BOOK', bold)
            worksheet.write('A5', 'for the period ' + str(dfrom) + ' to ' + str(dto), bold)

            worksheet.write('C1', 'Software:')
            worksheet.write('C2', 'User:')
            worksheet.write('C3', 'Datetime:')

            worksheet.write('D1', 'iES Financial System v. 1.0')
            worksheet.write('D2', str(request.user.username))
            worksheet.write('D3', datetime.datetime.now(), cell_format)


            # header
            worksheet.write('A7', 'Date', bold)
            worksheet.write('B7', 'Reference', bold)
            worksheet.write('C7', 'Brief Description/Explanation', bold)
            worksheet.write('D7', 'Account Title', bold)
            worksheet.write('E7', 'Debit', bold)
            worksheet.write('F7', 'Credit', bold)

            row = 7
            col = 0
            jvnum = ''
            bankaccount = ''
            department = ''
            departmentname = ''
            for data in list:

                worksheet.write(row, col, data.jv_date, formatdate)
                worksheet.write(row, col + 1, 'JV'+data.jv_num)
                worksheet.write(row, col + 2, data.jvmain.particular)
                worksheet.write(row, col + 3, data.chartofaccount.description)
                worksheet.write(row, col + 4, float(format(data.debitamount, '.2f')))
                worksheet.write(row, col + 5, float(format(data.creditamount, '.2f')))

                bankaccount = ""
                department = ""
                departmentname = ""
                row += 1

            workbook.close()

            # Rewind the buffer.
            output.seek(0)

            # Set up the Http response.
            filename = "generaljournalbook_birv2.xlsx"

        elif report == '19':

            print 'purchase books v2'

            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            formatdatetime = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})
            cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

            # title
            worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
            worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
            worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
            worksheet.write('A4', 'PURCHASE BOOK', bold)
            worksheet.write('A5', 'for the period ' + str(dfrom) + ' to ' + str(dto), bold)

            worksheet.write('C1', 'Software:')
            worksheet.write('C2', 'User:')
            worksheet.write('C3', 'Datetime:')

            worksheet.write('D1', 'iES Financial System v. 1.0')
            worksheet.write('D2', str(request.user.username))
            worksheet.write('D3', datetime.datetime.now(), cell_format)


            # header
            # PO Number, PO Date, Reference, Brief Description, Supplier, TIN, Address, Total Quantity, Gross Amount,
            # Discount Amount, Vatable, VAT Exempt (blank header in excel), VAT Zero-Rated, VAT Amount (change VAT Exempt header to VAT Amount),
            # Net Amount, Total Amount (still included since not sure if duplicate), VAT Rate, APV Amount (still included), ATC Amount.

            worksheet.write('A7', 'Date', bold)
            worksheet.write('B7', 'Supplier TIN', bold)
            worksheet.write('C7', 'Supplier Name', bold)
            worksheet.write('D7', 'Address', bold)
            worksheet.write('E7', 'Description', bold)
            worksheet.write('F7', 'Reference', bold)
            worksheet.write('G7', 'Amount', bold)
            worksheet.write('H7', 'Discount', bold)
            worksheet.write('I7', 'VAT Amount (Input Tax)', bold)
            worksheet.write('J7', 'Net Purchase', bold)

            # PO Number, PO Date, Reference, Brief Description, Supplier, TIN, Address, Total Quantity, Gross Amount,
            # Discount Amount, Vatable, VAT Exempt (blank header in excel), VAT Zero-Rated, VAT Amount (change VAT Exempt header to VAT Amount),
            # Net Amount, Total Amount (still included since not sure if duplicate), VAT Rate, APV Amount (still included), ATC Amount.
            row = 7
            col = 0
            q = query_bir(report, dfrom, dto)
            print q
            new_list = []
            if q:
                df = pd.DataFrame(q)
                for index, data in df.iterrows():
                    print data['ponum']
                    worksheet.write(row, col, data['podate'], formatdate)
                    worksheet.write(row, col + 1, data['tin'])
                    worksheet.write(row, col + 2, data['supplier_name'])
                    worksheet.write(row, col + 3, data['address'])
                    worksheet.write(row, col + 4, data['particulars'])
                    worksheet.write(row, col + 5, 'PO'+data['ponum'])
                    worksheet.write(row, col + 6, float(format(data['grossamount'], '.2f')))
                    worksheet.write(row, col + 7, float(format(data['discountamount'], '.2f')))
                    worksheet.write(row, col + 8, float(format(data['vatamount'], '.2f')))
                    worksheet.write(row, col + 9, float(format(data['totalamount'], '.2f')))

                    row += 1

            workbook.close()

            # Rewind the buffer.
            output.seek(0)

            # Set up the Http response.
            filename = "purchasebooks_birv2.xlsx"

        # Set up the Http response.
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response

def query_bir(report, dfrom, dto):
    print "Hello BIR"
    ''' Create query '''
    cursor = connection.cursor()

    if report == '14' or report == '17':
        print 'gen ledger'
        query = "SELECT s.document_date AS transdate, s.document_type AS transtype, s.document_num AS reference, " \
                "REPLACE(CONVERT(TRIM(REPLACE(REPLACE(s.particulars, '\\n', ''), '\\r', '')) USING ASCII), '?', '') AS particulars, " \
                "c.accountcode, c.description, IF (s.balancecode = 'D', s.amount, 0) AS debit, IF (s.balancecode = 'C', s.amount, 0) AS credit " \
                "FROM subledger AS s " \
                "LEFT OUTER JOIN chartofaccount AS c ON c.id = s.chartofaccount_id " \
                "WHERE s.document_date >= '" + str(dfrom) + "' AND s.document_date <= '" + str(dto) + "' " \
                "ORDER BY s.document_date, s.document_num, FIELD(s.document_type, 'AP','CV','JV','OR'), s.item_counter"

    elif report == '15' or report == '18':
        print 'cash receipt'
        query = "SELECT o.ordate, o.ornum, o.payee_name, " \
                 "REPLACE(CONVERT(TRIM(REPLACE(REPLACE(o.particulars, '\\n', ''), '\\r', '')) USING ASCII), '?', '') AS particulars, " \
                'd.balancecode, c.accountcode, REPLACE(REPLACE(c.description, "\'", ""), "//", "") AS description, d.debitamount, d.creditamount, IFNULL(b.code, "") AS bankacount ' \
                "FROM ormain AS o " \
                "LEFT OUTER JOIN ordetail AS d ON d.ormain_id = o.id " \
                "LEFT OUTER JOIN chartofaccount AS c ON c.id = d.chartofaccount_id " \
                "LEFT OUTER JOIN bankaccount AS b ON b.id = d.bankaccount_id " \
                "WHERE o.ordate >= '" + str(dfrom) + "' AND o.ordate <= '" + str(dto) + "' " \
                "AND o.orstatus = 'R' AND o.status = 'O' " \
                "ORDER BY o.ordate, o.ornum, d.balancecode DESC"
    elif report == '16' or report == '19':
        print 'purchase order'
        query = "SELECT po.ponum, po.podate, po.refnum, TRIM(REPLACE(REPLACE(particulars, '\\n', ''), '\\r', '')) AS particulars, po.supplier_name, po.discountamount, po.grossamount, po.netamount, " \
                "po.vatable, po.vatamount, po.vatexempt, po.vatrate, po.vatzerorated, po.totalamount, po.totalquantity, po.apvamount, po.atcamount,s.tin, CONCAT(s.address1,' ', s.address2, ' ', s.address3) AS address " \
                "FROM pomain AS po LEFT OUTER JOIN supplier AS s ON s.id = po.supplier_id " \
                "WHERE po.podate >= '" + str(dfrom) + "' AND po.podate <= '" + str(dto) + "' " \
                "AND postatus = 'A' AND po.status = 'A'  AND po.isfullyapv = 1 " \
                "ORDER BY po.podate, po.ponum"

    print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
