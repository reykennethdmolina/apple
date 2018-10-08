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
import io
import xlsxwriter
import datetime
from django.template.loader import render_to_string

@method_decorator(login_required, name='dispatch')
class ReportView(TemplateView):
    model = Jvdetail
    template_name = 'rep_booksofaccounts/report.html'

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

        if report == '1':
            title = "GENERAL JOURNAL BOOK - DETAILED ENTRIES"
            q = Jvdetail.objects.all().filter(isdeleted=0).order_by('jv_date', 'jv_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)
            total = q.exclude(jvmain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
        elif report == '2':
            title = "GENERAL JOURNAL BOOK - SUMMARY ENTRIES"
            q = Jvdetail.objects.all().filter(isdeleted=0).exclude(jvmain__status='C')
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
            q = Jvdetail.objects.all().filter(isdeleted=0).exclude(jvmain__status='C')
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
            q = Cvdetail.objects.all().filter(isdeleted=0).order_by('cv_date', 'cv_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)
            total = q.exclude(cvmain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
        elif report == '5':
            title = "CASH DISBURSEMENT BOOK - SUMMARY ENTRIES"
            q = Cvdetail.objects.all().filter(isdeleted=0).exclude(cvmain__status='C')
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
            q = Cvdetail.objects.all().filter(isdeleted=0).exclude(cvmain__status='C')
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
            q = Ordetail.objects.all().filter(isdeleted=0).order_by('or_date', 'or_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)
            total = q.exclude(ormain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
        elif report == '8':
            title = "CASH RECEIPTS BOOK - SUMMARY ENTRIES"
            q = Ordetail.objects.all().filter(isdeleted=0).exclude(ormain__status='C')
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
            q = Ordetail.objects.all().filter(isdeleted=0).exclude(ormain__status='C')
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
            title = "SCHEDULE OF ACCURAL - AP TRADE - DETAILED ENTRIES"
            q = Apdetail.objects.all().filter(isdeleted=0).order_by('ap_date', 'ap_num', '-balancecode', 'item_counter')
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
            total = q.exclude(apmain__status='C').aggregate(Sum('debitamount'), Sum('creditamount'))
        elif report == '11':
            title = "SCHEDULE OF ACCURAL - AP TRADE - SUMMARY ENTRIES"
            q = Apdetail.objects.all().filter(isdeleted=0).exclude(apmain__status='C')
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
            title = "SCHEDULE OF ACCURAL - AP TRADE - SUBSIDIARY ENTRIES"
            q = Apdetail.objects.all().filter(isdeleted=0).exclude(apmain__status='C')
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
            title = "SCHEDULE OF ACCURAL - AP TRADE (with Branch) - SUMMARY ENTRIES"
            q = Apdetail.objects.all().filter(isdeleted=0,department__isnull=False)\
                .exclude(apmain__status='C').exclude(chartofaccount=Companyparameter.objects.first().coa_cashinbank)\
                .exclude(chartofaccount=Companyparameter.objects.first().coa_aptrade)
            if dfrom != '':
                q = q.filter(ap_date__gte=dfrom)
            if dto != '':
                q = q.filter(ap_date__lte=dto)
            q = q.values('department__code', 'department__departmentname', 'branch__code') \
                .annotate(Sum('debitamount'), Sum('creditamount'),
                          debitdifference=Case(When(debitamount__sum__lt=F('creditamount__sum'), then=Value(0)),
                                               default=Sum('debitamount') - Sum('creditamount')),
                          creditdifference=Case(When(creditamount__sum__lt=F('debitamount__sum'), then=Value(0)),
                                                default=Sum('creditamount') - Sum('debitamount'))) \
                .order_by('department__code')
            total = q.aggregate(Sum('debitdifference'), Sum('creditdifference'))
        else:
            q = Jvdetail.objects.filter(isdeleted=0).order_by('jv_date', 'jv_num')[:0]

        list = q[:50]
        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
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
            return Render.render('rep_booksofaccounts/report_13.html', context)
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
            title = "SCHEDULE OF ACCURAL - AP TRADE - SUMMARY ENTRIES"
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
            title = "SCHEDULE OF ACCURAL - AP TRADE - SUMMARY ENTRIES"
            subtitle = "Summary of Department"
            q = Apdetail.objects.all().filter(isdeleted=0,department__isnull=False).exclude(apmain__status='C')
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
        dfrom = request.GET['from']
        dto = request.GET['to']
        title = "GENERAL JOURNAL BOOK - DETAILED ENTRIES"

        if report == '3':
            title = "GENERAL JOURNAL BOOK - SUBSIDIARY ENTRIES"
            q = Jvdetail.objects.all().filter(isdeleted=0).exclude(jvmain__status='C')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)
            q = q.values('chartofaccount__accountcode', 'chartofaccount__description', 'bankaccount__code',
                         'employee__firstname', 'employee__middlename', 'employee__lastname',
                         'supplier__name', 'customer__name', 'department__departmentname') \
                .annotate(Sum('debitamount'), Sum('creditamount'))
                # .order_by('chartofaccount__accountcode', 'bankaccount__code', 'employee__lastname',
                #           'employee__firstname', 'employee__middlename',
                #           'supplier__name', 'customer__name', 'department__departmentname')
            q = q.order_by('chartofaccount__accountcode', 'debitamount__sum', 'creditamount__sum')
            total = q.aggregate(Sum('debitamount'), Sum('creditamount'))
        else:
            q = Jvdetail.objects.filter(isdeleted=0).order_by('jv_date', 'jv_num')[:0]

        list = q

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', 'JOURNAL VOUCHER INQUIRY LIST', bold)
        worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)
        worksheet.write('A3', 'Chart of Account', bold)

        # header
        worksheet.write('A4', 'JV Number', bold)
        worksheet.write('B4', 'JV Date', bold)
        worksheet.write('C4', 'Particulars', bold)
        worksheet.write('D4', 'Debit Amount', bold)
        worksheet.write('D4', 'Credit Amount', bold)

        row = 5
        col = 0
        for data in list:
            worksheet.write(row, col, data['chartofaccount__accountcode'])
            worksheet.write(row, col + 1, data['chartofaccount__description'])
            worksheet.write(row, col + 2, float(format(data['debitamount__sum'], '.2f')))
            worksheet.write(row, col + 3, float(format(data['creditamount__sum'], '.2f')))
            row += 1

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = "jvinquiry.xlsx"
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response

