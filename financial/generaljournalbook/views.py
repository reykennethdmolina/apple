from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.apps import apps
from django.db.models import Sum, F, Count, Q
from collections import namedtuple
from django.db import connection
from companyparameter.models import Companyparameter
from chartofaccount.models import Chartofaccount
from inputvat.models import Inputvat
from outputvat.models import Outputvat
from product.models import Product
from branch.models import Branch
from bankaccount.models import Bankaccount
from department.models import Department
from ataxcode.models import Ataxcode
from subledger.models import Subledger
from subledgersummary.models import Subledgersummary
from vat.models import Vat
from wtax.models import Wtax
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
import pandas as pd
from datetime import timedelta
import io
import xlsxwriter
import datetime
from django.template.loader import render_to_string
from django.db.models.lookups import MonthTransform as Month, YearTransform as Year


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'generaljournalbook/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['chart'] = Chartofaccount.objects.filter(isdeleted=0, accounttype='P').order_by('accountcode')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('code')
        context['outputvat'] = Outputvat.objects.filter(isdeleted=0).order_by('code')
        context['product'] = Product.objects.filter(isdeleted=0).order_by('description')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['wtax'] = Wtax.objects.filter(isdeleted=0).order_by('code')

        return context

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        chartofaccount = []
        begbal = []
        beg_code = 'D'
        beg_amount = 0
        report = request.GET['report']
        transtype = request.GET['transtype']
        dfrom = request.GET['from']
        dto = request.GET['to']
        chart = request.GET['chart']
        chart2 = request.GET['chart2']
        supplier = request.GET['supplier']
        client = request.GET['client']
        agency = request.GET['agency']
        agent = request.GET['agent']
        employee = request.GET['employee']
        department = request.GET['department']
        product = request.GET['product']
        branch = request.GET['branch']
        bankaccount = request.GET['bankaccount']
        vat = request.GET['vat']
        atax = request.GET['atax']
        wtax = request.GET['wtax']
        inputvat = request.GET['inputvat']
        outputvat = request.GET['outputvat']
        chart = request.GET['chart']
        title = "General Ledger"
        subtitle = ""

        list = Subledger.objects.filter(isdeleted=0).order_by('chartofaccount__accountcode', 'document_type', 'document_date', 'document_num','item_counter')[:0]

        if report == '1':
            subtitle = "Detailed Entries"
            q = Subledger.objects.annotate(month=Month('document_date')).values('month').filter(isdeleted=0).order_by('chartofaccount__accountcode', 'document_type', 'document_date', 'document_num','item_counter')
            if dfrom != '':
                q = q.filter(document_date__gte=dfrom)
            if dto != '':
                q = q.filter(document_date__lte=dto)

            if chart != '' and chart2 != '':
                q = q.filter(chartofaccount__accountcode__gte=chart)
                q = q.filter(chartofaccount__accountcode__lte=chart2)
            elif chart != '' and chart2 == '':
                q = q.filter(chartofaccount__accountcode__exact=chart)
            elif chart2 != '' and chart == '':
                q = q.filter(chartofaccount__accountcode__exact=chart2)

            if transtype != 'null':
                values = ''.join(transtype.split(' ')).split(',')
                q = q.filter(document_type__in=values)

            if supplier != 'null':
                q = q.filter(document_supplier_id=supplier)
            if client != 'null':
                q = q.filter(document_customer_id=client)
            if agency != 'null':
                q = q.filter(document_customer_id=agency)
            if agent != 'null':
                q = q.filter(document_customer_id=agent)
            if employee != 'null':
                q = q.filter(employee_id=employee)
            if product != '':
                q = q.filter(product_id=product)
            if department != '':
                q = q.filter(department_id=department)
            if branch != '':
                q = q.filter(branch_id=branch)
            if bankaccount != '':
                q = q.filter(bankaccount_id=bankaccount)
            if vat != '':
                q = q.filter(vat_id=vat)
            if atax != '':
                q = q.filter(atccode=atax)
            if wtax != '':
                q = q.filter(wtax_id=wtax)
            if inputvat != '':
                q = q.filter(inputvat_id=inputvat)
            if outputvat != '':
                q = q.filter(outputvat_id=outputvat)

        if report == '2':
            subtitle = "Summary Entries (Year-End)"

        new_list = []

        if report == '1':

            q = q.values('chartofaccount_id', 'chartofaccount__accountcode', 'chartofaccount__description', 'document_type', 'document_num', 'document_date', 'balancecode', 'amount', 'particulars')
            list = q

            if list:
                df = pd.DataFrame.from_records(list)

                if dto != '':
                    newdto = datetime.datetime.strptime(dto, "%Y-%m-%d")
                    prevdate = datetime.date(int(newdto.year), int(newdto.month), 10) - timedelta(days=15)
                    prevyear = prevdate.year
                    prevmonth = prevdate.month

                counter = 0

                for id, accountcode in df.fillna('NaN').groupby(['chartofaccount_id', 'chartofaccount__accountcode']):
                    begbal = Subledgersummary.objects.filter(chartofaccount=id, year=prevyear, month=prevmonth).first()
                    beg_code = begbal.end_code
                    beg_amount = begbal.end_amount
                    begamount = beg_amount
                    for item, data in accountcode.iterrows():
                        if data.balancecode == beg_code:
                            begamount += data.amount
                        else:
                            begamount -= data.amount
                        new_list.append({'accountcode': data.chartofaccount__accountcode, 'description': data.chartofaccount__description, 'amount': data.amount,
                                         'dnum': data.document_num, 'ddate': data.document_date, 'balancecode': data.balancecode, 'particulars': data.particulars,
                                         'type': data.document_type, 'begcode': beg_code, 'begamount': beg_amount, 'dbegcode': beg_code, 'dbegamount': begamount})
                        counter += 1
                    new_list.append({'accountcode': data.chartofaccount__accountcode, 'description': data.chartofaccount__description,
                                     'amount': data.amount, 'dnum': data.document_num, 'ddate': data.document_date, 'balancecode': data.balancecode,
                                     'particulars': data.particulars,'type': 'ending', 'begcode': beg_code, 'begamount': beg_amount, 'dbegcode': beg_code,'dbegamount': begamount})
                    counter += 1

        elif report == '2':

            if dfrom != '':
                newdfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
                startdate = datetime.date(int(newdfrom.year), int(newdfrom.month), 10) - timedelta(days=15)
                startyear = startdate.year
                startmonth = startdate.month

            if dfrom != '' and dto != '':
                ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
                todate = datetime.date(int(ndto.year), int(ndto.month), 10)
                toyear = todate.year
                tomonth = todate.month
                nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
                fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
                fromyear = fromdate.year
                frommonth = fromdate.month

            result = query_summary(chart, chart2, toyear, tomonth, fromyear, frommonth)

            df = pd.DataFrame(result)

            counter = 0
            begamount = 0
            dbegamount = 0
            begcode = ''
            dbegcode = ''

            for id, account in df.groupby(['id']):
                begbal = Subledgersummary.objects.filter(chartofaccount_id=id, year=startyear, month=startmonth).first()
                if begbal:
                    beg_code = begbal.end_code
                    begcode = beg_code
                    beg_amount = begbal.end_amount
                    begamount = beg_amount
                    for item, data in account.iterrows():

                        if int(data.ap_credit) != 0 or int(data.ap_debit) != 0:
                            if int(data.ap_credit) != 0:
                                dbegamount =  data.ap_credit
                                dbegcode = 'C'
                            else:
                                dbegamount = data.ap_debit
                                dbegcode = 'D'

                            if dbegcode == beg_code:
                                begamount += dbegamount
                            else:
                                begamount -= dbegamount

                            if begamount > 0:
                                begcode = beg_code
                            else:
                                begcode = dbegcode

                            new_list.append({'accountcode': data.accountcode, 'description': data.description,
                                             'balancecode': data.balancecode,
                                             'year': data.year, 'month': datetime.date(int(data.year), int(data.month), 10), 'beg_code': beg_code,
                                             'beg_amount': beg_amount,
                                             'type': 'Account Payable Voucher', 'begamount': begamount, 'begcode': begcode,
                                             'dbegamount': dbegamount, 'dbegcode': dbegcode})

                        if int(data.jv_credit) != 0 or int(data.jv_debit) != 0:
                            if int(data.jv_credit) != 0:
                                dbegamount =  data.jv_credit
                                dbegcode = 'C'
                            else:
                                dbegamount = data.jv_debit
                                dbegcode = 'D'

                            if dbegcode == beg_code:
                                begamount += dbegamount
                            else:
                                begamount -= dbegamount

                            if begamount > 0:
                                begcode = beg_code
                            else:
                                begcode = dbegcode

                            new_list.append({'accountcode': data.accountcode, 'description': data.description,
                                             'balancecode': data.balancecode,
                                             'year': data.year, 'month': datetime.date(int(data.year), int(data.month), 10), 'beg_code': beg_code,
                                             'beg_amount': beg_amount,
                                             'type': 'Journal Voucher', 'begamount': begamount, 'begcode': begcode,
                                             'dbegamount': dbegamount, 'dbegcode': dbegcode})

                        if int(data.cv_credit) != 0 or int(data.cv_debit) != 0:
                            if int(data.cv_credit) != 0:
                                dbegamount =  data.cv_credit
                                dbegcode = 'C'
                            else:
                                dbegamount = data.cv_debit
                                dbegcode = 'D'

                            if dbegcode == beg_code:
                                begamount += dbegamount
                            else:
                                begamount -= dbegamount

                            if begamount > 0:
                                begcode = beg_code
                            else:
                                begcode = dbegcode

                            new_list.append({'accountcode': data.accountcode, 'description': data.description,
                                             'balancecode': data.balancecode,
                                             'year': data.year, 'month': datetime.date(int(data.year), int(data.month), 10), 'beg_code': beg_code,
                                             'beg_amount': beg_amount,
                                             'type': 'Check Voucher', 'begamount': begamount, 'begcode': begcode,
                                             'dbegamount': dbegamount, 'dbegcode': dbegcode})

                        if int(data.or_credit) != 0 or int(data.or_debit) != 0:
                            if int(data.or_credit) != 0:
                                dbegamount =  data.or_credit
                                dbegcode = 'C'
                            else:
                                dbegamount = data.or_debit
                                dbegcode = 'D'

                            if dbegcode == beg_code:
                                begamount += dbegamount
                            else:
                                begamount -= dbegamount

                            if begamount > 0:
                                begcode = beg_code
                            else:
                                begcode = dbegcode

                            new_list.append({'accountcode': data.accountcode, 'description': data.description,
                                             'balancecode': data.balancecode,
                                             'year': data.year, 'month': datetime.date(int(data.year), int(data.month), 10), 'beg_code': beg_code,
                                             'beg_amount': beg_amount,
                                             'type': 'Official Receipt', 'begamount': begamount, 'begcode': begcode,
                                             'dbegamount': dbegamount, 'dbegcode': dbegcode})
                        counter += 1

                    new_list.append({'accountcode': data.accountcode, 'description': data.description,
                                     'balancecode': data.balancecode,
                                     'year': data.year, 'month': datetime.date(int(data.year), int(data.month), 10), 'beg_code': beg_code,
                                     'beg_amount': beg_amount,
                                     'type': 'ending', 'begamount': begamount, 'begcode': begcode,
                                     'dbegamount': dbegamount, 'dbegcode': dbegcode})
                    counter += 1
                else:

                    new_list.append({'accountcode': account.accountcode.to_string(index=False), 'description': account.description.to_string(index=False),
                                     'balancecode': '',
                                     'year': '', 'month': '', 'beg_code': beg_code,
                                     'beg_amount': beg_amount,
                                     'type': '', 'begamount': beg_amount, 'begcode': '',
                                     'dbegamount': dbegamount, 'dbegcode': ''})

                    new_list.append({'accountcode': account.accountcode.to_string(index=False),
                                     'description': account.description.to_string(index=False),
                                     'balancecode': '',
                                     'year': '', 'month': '', 'beg_code': beg_code,
                                     'beg_amount': beg_amount,
                                     'type': 'ending', 'begamount': beg_amount, 'begcode': beg_code,
                                     'dbegamount': dbegamount, 'dbegcode': ''})

                    counter += 1

                counter += 1
        if dfrom == '':
            dfrom = '2018-01-01'
        if dto == '':
            dto = '2018-01-01'
        context = {
            "title": title,
            "subtitle": subtitle,
            "today": timezone.now(),
            "company": company,
            "listing": new_list,
            "total": total,
            "chartofaccount": chartofaccount,
            "begbal": begbal,
            "datefrom": datetime.datetime.strptime(dfrom, '%Y-%m-%d'),
            "dateto": datetime.datetime.strptime(dto, '%Y-%m-%d'),
            "username": request.user,
        }

        if report == '1':
            return Render.render('generaljournalbook/report_1.html', context)
        elif report == '2':
            return Render.render('generaljournalbook/report_2.html', context)
        else:
            return Render.render('generaljournalbook/report_1.html', context)

def query_summary(chart, chart2, toyear, tomonth, fromyear, frommonth):
    print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    condition = ''
    if chart != '' and chart2 != '':
        condition = "AND chart.accountcode >= '"+str(chart)+"' AND chart.accountcode <= '"+str(chart2)+"'"
    elif chart != '' and chart2 == '':
        condition = "AND chart.accountcode = '" + str(chart)+ "'"
    elif chart2 != '' and chart == '':
        condition = "AND chart.accountcode = '" + str(chart2) + "'"

    query = "SELECT chart.id, chart.accountcode, chart.description, subs.year, subs.month, " \
            "IF (subs.accounts_payable_voucher_credit_total >= subs.accounts_payable_voucher_debit_total, (subs.accounts_payable_voucher_credit_total - subs.accounts_payable_voucher_debit_total), 0) AS ap_credit, " \
            "IF (subs.accounts_payable_voucher_debit_total > subs.accounts_payable_voucher_credit_total, (subs.accounts_payable_voucher_debit_total - subs.accounts_payable_voucher_credit_total), 0) AS ap_debit, " \
            "IF (subs.journal_voucher_credit_total >= subs.journal_voucher_debit_total, (subs.journal_voucher_credit_total - subs.journal_voucher_debit_total), 0) AS jv_credit, " \
            "IF (subs.journal_voucher_debit_total > subs.journal_voucher_credit_total, (subs.journal_voucher_debit_total - subs.journal_voucher_credit_total), 0) AS jv_debit, " \
            "IF (subs.check_voucher_credit_total >= subs.check_voucher_debit_total, (subs.check_voucher_credit_total - subs.check_voucher_debit_total), 0) AS cv_credit, " \
            "IF (subs.check_voucher_debit_total > subs.check_voucher_credit_total, (subs.check_voucher_debit_total - subs.check_voucher_credit_total), 0) AS cv_debit, " \
            "IF (subs.official_receipt_credit_total >= subs.official_receipt_debit_total, (subs.official_receipt_credit_total - subs.official_receipt_debit_total), 0) AS or_credit, " \
            "IF (subs.official_receipt_debit_total > subs.official_receipt_credit_total, (subs.official_receipt_debit_total - subs.official_receipt_credit_total), 0) AS or_debit, " \
            "(subs.accounts_payable_voucher_credit_total + subs.accounts_payable_voucher_debit_total + subs.journal_voucher_credit_total + subs.journal_voucher_debit_total + " \
            "subs.check_voucher_credit_total + subs.check_voucher_debit_total + subs.official_receipt_credit_total + subs.official_receipt_debit_total) AS total, subs.end_code AS balancecode " \
            "FROM chartofaccount AS chart " \
            "LEFT OUTER JOIN subledgersummary AS subs ON subs.chartofaccount_id = chart.id " \
            "WHERE chart.accounttype = 'P' AND chart.isdeleted = 0 " \
            "AND subs.year >= "+str(fromyear)+" AND subs.year <= "+str(toyear)+" " \
            "AND subs.month >= "+str(frommonth)+" AND subs.month <= "+str(tomonth)+" "+condition+" " \
            "ORDER BY chart.accountcode, subs.year, subs.month"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

@method_decorator(login_required, name='dispatch')
class GenerateExcel(View):
    def get(self, request):

        company = Companyparameter.objects.all().first()
        q = []
        total = []
        chartofaccount = []
        begbal = []
        beg_code = 'D'
        beg_amount = 0
        report = request.GET['report']
        transtype = request.GET['transtype']
        dfrom = request.GET['from']
        dto = request.GET['to']
        chart = request.GET['chart']
        chart2 = request.GET['chart2']
        supplier = request.GET['supplier']
        client = request.GET['client']
        agency = request.GET['agency']
        agent = request.GET['agent']
        employee = request.GET['employee']
        department = request.GET['department']
        product = request.GET['product']
        branch = request.GET['branch']
        bankaccount = request.GET['bankaccount']
        vat = request.GET['vat']
        atax = request.GET['atax']
        wtax = request.GET['wtax']
        inputvat = request.GET['inputvat']
        outputvat = request.GET['outputvat']
        chart = request.GET['chart']
        title = "General Ledger"
        subtitle = ""

        list = Subledger.objects.filter(isdeleted=0).order_by('chartofaccount__accountcode', 'document_type',
                                                              'document_date', 'document_num', 'item_counter')[:0]

        if report == '1':
            subtitle = "Detailed Entries"
            q = Subledger.objects.annotate(month=Month('document_date')).values('month').filter(isdeleted=0).order_by(
                'chartofaccount__accountcode', 'document_type', 'document_date', 'document_num', 'item_counter')
            if dfrom != '':
                q = q.filter(document_date__gte=dfrom)
            if dto != '':
                q = q.filter(document_date__lte=dto)

            if chart != '' and chart2 != '':
                q = q.filter(chartofaccount__accountcode__gte=chart)
                q = q.filter(chartofaccount__accountcode__lte=chart2)
            elif chart != '' and chart2 == '':
                q = q.filter(chartofaccount__accountcode__exact=chart)
            elif chart2 != '' and chart == '':
                q = q.filter(chartofaccount__accountcode__exact=chart2)

            if transtype != 'null':
                values = ''.join(transtype.split(' ')).split(',')
                q = q.filter(document_type__in=values)

            if supplier != 'null':
                q = q.filter(document_supplier_id=supplier)
            if client != 'null':
                q = q.filter(document_customer_id=client)
            if agency != 'null':
                q = q.filter(document_customer_id=agency)
            if agent != 'null':
                q = q.filter(document_customer_id=agent)
            if employee != 'null':
                q = q.filter(employee_id=employee)
            if product != '':
                q = q.filter(product_id=product)
            if department != '':
                q = q.filter(department_id=department)
            if branch != '':
                q = q.filter(branch_id=branch)
            if bankaccount != '':
                q = q.filter(bankaccount_id=bankaccount)
            if vat != '':
                q = q.filter(vat_id=vat)
            if atax != '':
                q = q.filter(atccode=atax)
            if wtax != '':
                q = q.filter(wtax_id=wtax)
            if inputvat != '':
                q = q.filter(inputvat_id=inputvat)
            if outputvat != '':
                q = q.filter(outputvat_id=outputvat)

        if report == '2':
            subtitle = "Summary Entries (Year-End)"

        new_list = []

        if report == '1':

            q = q.values('chartofaccount_id', 'chartofaccount__accountcode', 'chartofaccount__description',
                         'document_type', 'document_num', 'document_date', 'balancecode', 'amount', 'particulars')
            list = q

            if list:
                df = pd.DataFrame.from_records(list)

                if dto != '':
                    newdto = datetime.datetime.strptime(dto, "%Y-%m-%d")
                    prevdate = datetime.date(int(newdto.year), int(newdto.month), 10) - timedelta(days=15)
                    prevyear = prevdate.year
                    prevmonth = prevdate.month

                counter = 0

                for id, accountcode in df.fillna('NaN').groupby(['chartofaccount_id', 'chartofaccount__accountcode']):
                    begbal = Subledgersummary.objects.filter(chartofaccount=id, year=prevyear, month=prevmonth).first()
                    beg_code = begbal.end_code
                    beg_amount = begbal.end_amount
                    begamount = beg_amount
                    for item, data in accountcode.iterrows():
                        if data.balancecode == beg_code:
                            begamount += data.amount
                        else:
                            begamount -= data.amount
                        new_list.append({'accountcode': data.chartofaccount__accountcode,
                                         'description': data.chartofaccount__description, 'amount': data.amount,
                                         'dnum': data.document_num, 'ddate': data.document_date,
                                         'balancecode': data.balancecode, 'particulars': data.particulars,
                                         'type': data.document_type, 'begcode': beg_code, 'begamount': beg_amount,
                                         'dbegcode': beg_code, 'dbegamount': begamount})
                        counter += 1
                    new_list.append({'accountcode': data.chartofaccount__accountcode,
                                     'description': data.chartofaccount__description,
                                     'amount': data.amount, 'dnum': data.document_num, 'ddate': data.document_date,
                                     'balancecode': data.balancecode,
                                     'particulars': data.particulars, 'type': 'ending', 'begcode': beg_code,
                                     'begamount': beg_amount, 'dbegcode': beg_code, 'dbegamount': begamount})
                    counter += 1

        elif report == '2':

            if dfrom != '':
                newdfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
                startdate = datetime.date(int(newdfrom.year), int(newdfrom.month), 10) - timedelta(days=15)
                startyear = startdate.year
                startmonth = startdate.month

            if dfrom != '' and dto != '':
                ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
                todate = datetime.date(int(ndto.year), int(ndto.month), 10)
                toyear = todate.year
                tomonth = todate.month
                nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
                fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
                fromyear = fromdate.year
                frommonth = fromdate.month

            result = query_summary(chart, chart2, toyear, tomonth, fromyear, frommonth)

            df = pd.DataFrame(result)

            counter = 0
            begamount = 0
            dbegamount = 0
            begcode = ''
            dbegcode = ''

            for id, account in df.groupby(['id']):
                begbal = Subledgersummary.objects.filter(chartofaccount_id=id, year=startyear, month=startmonth).first()
                if begbal:
                    beg_code = begbal.end_code
                    begcode = beg_code
                    beg_amount = begbal.end_amount
                    begamount = beg_amount
                    for item, data in account.iterrows():

                        if int(data.ap_credit) != 0 or int(data.ap_debit) != 0:
                            if int(data.ap_credit) != 0:
                                dbegamount = data.ap_credit
                                dbegcode = 'C'
                            else:
                                dbegamount = data.ap_debit
                                dbegcode = 'D'

                            if dbegcode == beg_code:
                                begamount += dbegamount
                            else:
                                begamount -= dbegamount

                            if begamount > 0:
                                begcode = beg_code
                            else:
                                begcode = dbegcode

                            new_list.append({'accountcode': data.accountcode, 'description': data.description,
                                             'balancecode': data.balancecode,
                                             'year': data.year,
                                             'month': datetime.date(int(data.year), int(data.month), 10),
                                             'beg_code': beg_code,
                                             'beg_amount': beg_amount,
                                             'type': 'Account Payable Voucher', 'begamount': begamount,
                                             'begcode': begcode,
                                             'dbegamount': dbegamount, 'dbegcode': dbegcode})

                        if int(data.jv_credit) != 0 or int(data.jv_debit) != 0:
                            if int(data.jv_credit) != 0:
                                dbegamount = data.jv_credit
                                dbegcode = 'C'
                            else:
                                dbegamount = data.jv_debit
                                dbegcode = 'D'

                            if dbegcode == beg_code:
                                begamount += dbegamount
                            else:
                                begamount -= dbegamount

                            if begamount > 0:
                                begcode = beg_code
                            else:
                                begcode = dbegcode

                            new_list.append({'accountcode': data.accountcode, 'description': data.description,
                                             'balancecode': data.balancecode,
                                             'year': data.year,
                                             'month': datetime.date(int(data.year), int(data.month), 10),
                                             'beg_code': beg_code,
                                             'beg_amount': beg_amount,
                                             'type': 'Journal Voucher', 'begamount': begamount, 'begcode': begcode,
                                             'dbegamount': dbegamount, 'dbegcode': dbegcode})

                        if int(data.cv_credit) != 0 or int(data.cv_debit) != 0:
                            if int(data.cv_credit) != 0:
                                dbegamount = data.cv_credit
                                dbegcode = 'C'
                            else:
                                dbegamount = data.cv_debit
                                dbegcode = 'D'

                            if dbegcode == beg_code:
                                begamount += dbegamount
                            else:
                                begamount -= dbegamount

                            if begamount > 0:
                                begcode = beg_code
                            else:
                                begcode = dbegcode

                            new_list.append({'accountcode': data.accountcode, 'description': data.description,
                                             'balancecode': data.balancecode,
                                             'year': data.year,
                                             'month': datetime.date(int(data.year), int(data.month), 10),
                                             'beg_code': beg_code,
                                             'beg_amount': beg_amount,
                                             'type': 'Check Voucher', 'begamount': begamount, 'begcode': begcode,
                                             'dbegamount': dbegamount, 'dbegcode': dbegcode})

                        if int(data.or_credit) != 0 or int(data.or_debit) != 0:
                            if int(data.or_credit) != 0:
                                dbegamount = data.or_credit
                                dbegcode = 'C'
                            else:
                                dbegamount = data.or_debit
                                dbegcode = 'D'

                            if dbegcode == beg_code:
                                begamount += dbegamount
                            else:
                                begamount -= dbegamount

                            if begamount > 0:
                                begcode = beg_code
                            else:
                                begcode = dbegcode

                            new_list.append({'accountcode': data.accountcode, 'description': data.description,
                                             'balancecode': data.balancecode,
                                             'year': data.year,
                                             'month': datetime.date(int(data.year), int(data.month), 10),
                                             'beg_code': beg_code,
                                             'beg_amount': beg_amount,
                                             'type': 'Official Receipt', 'begamount': begamount, 'begcode': begcode,
                                             'dbegamount': dbegamount, 'dbegcode': dbegcode})
                        counter += 1

                    new_list.append({'accountcode': data.accountcode, 'description': data.description,
                                     'balancecode': data.balancecode,
                                     'year': data.year, 'month': datetime.date(int(data.year), int(data.month), 10),
                                     'beg_code': beg_code,
                                     'beg_amount': beg_amount,
                                     'type': 'ending', 'begamount': begamount, 'begcode': begcode,
                                     'dbegamount': dbegamount, 'dbegcode': dbegcode})
                    counter += 1
                else:

                    new_list.append({'accountcode': account.accountcode.to_string(index=False),
                                     'description': account.description.to_string(index=False),
                                     'balancecode': '',
                                     'year': '', 'month': '', 'beg_code': beg_code,
                                     'beg_amount': beg_amount,
                                     'type': '', 'begamount': beg_amount, 'begcode': '',
                                     'dbegamount': dbegamount, 'dbegcode': ''})

                    new_list.append({'accountcode': account.accountcode.to_string(index=False),
                                     'description': account.description.to_string(index=False),
                                     'balancecode': '',
                                     'year': '', 'month': '', 'beg_code': beg_code,
                                     'beg_amount': beg_amount,
                                     'type': 'ending', 'begamount': beg_amount, 'begcode': beg_code,
                                     'dbegamount': dbegamount, 'dbegcode': ''})

                    counter += 1

                counter += 1

        if report == '1':
            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})

            # title
            worksheet.write('A1', 'GENERAL LEDGER DETAILED ENTRIES', bold)
            worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)
            worksheet.merge_range('A3:C3', 'Account Code', bold)
            worksheet.write('D3', 'Account Title', bold)
            worksheet.merge_range('E3:F3', 'Transactions', bold)
            worksheet.merge_range('G3:H3', 'Balance', bold)

            # header
            worksheet.write('A4', 'Date', bold)
            worksheet.write('B4', 'Type', bold)
            worksheet.write('C4', 'Number', bold)
            worksheet.write('D4', 'Particulars', bold)
            worksheet.write('E4', 'Debit', bold)
            worksheet.write('F4', 'Credit', bold)
            worksheet.write('G4', 'Debit', bold)
            worksheet.write('H4', 'Credit', bold)

            row = 5
            col = 0
            dataset = pd.DataFrame(new_list)
            for id, accountcode in dataset.fillna('NaN').sort_values(by=['accountcode', 'type']).groupby(['accountcode', 'description', 'begcode', 'begamount']):
                worksheet.write(row, col, id[0])
                worksheet.write(row, col + 1, id[1])
                worksheet.write(row, col + 4, 'beginning balance')
                if id[2] == 'D':
                    worksheet.write(row, col + 6, float(format(id[3], '.2f')))
                    worksheet.write(row, col + 7, float(format(0, '.2f')))
                else:
                    worksheet.write(row, col + 6, float(format(0, '.2f')))
                    worksheet.write(row, col + 7, float(format(id[3], '.2f')))
                row += 1
                for sub, data in accountcode.iterrows():
                    if data['type'] == 'ending':
                        worksheet.write(row, col + 4, 'ending balance')
                        if data.dbegcode == 'D':
                            worksheet.write(row, col + 6, float(format(data['dbegamount'], '.2f')))
                            worksheet.write(row, col + 7, float(format(0, '.2f')))
                        else:
                            worksheet.write(row, col + 6, float(format(0, '.2f')))
                            worksheet.write(row, col + 7, float(format(data['dbegamount'], '.2f')))
                        row += 1
                    else:
                        worksheet.write(row, col, data['ddate'], formatdate)
                        worksheet.write(row, col + 1, data['type'])
                        worksheet.write(row, col + 2, data['dnum'])
                        worksheet.write(row, col + 3, data['particulars'])
                        if data.balancecode == 'D':
                            worksheet.write(row, col + 4, float(format(data['amount'], '.2f')))
                            worksheet.write(row, col + 5, float(format(0, '.2f')))
                        else:
                            worksheet.write(row, col + 4, float(format(0, '.2f')))
                            worksheet.write(row, col + 5, float(format(data['amount'], '.2f')))
                        if data.dbegcode == 'D':
                            worksheet.write(row, col + 6, float(format(data['dbegamount'], '.2f')))
                            worksheet.write(row, col + 7, float(format(0, '.2f')))
                        else:
                            worksheet.write(row, col + 6, float(format(0, '.2f')))
                            worksheet.write(row, col + 7, float(format(data['dbegamount'], '.2f')))
                        row += 1
            workbook.close()

            # Set up the Http response.
            filename = "generaljournalbook_detailed.xlsx"

        elif report == '2':
            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # variables
            bold = workbook.add_format({'bold': 1})
            formatdate = workbook.add_format({'num_format': 'MM/YYYY'})
            centertext = workbook.add_format({'bold': 1, 'align': 'center'})

            # title
            worksheet.write('A1', 'GENERAL LEDGER SUMMARY ENTRIES', bold)
            worksheet.write('A2', 'AS OF ' + str(dfrom) + ' to ' + str(dto), bold)
            worksheet.merge_range('A3:B3', 'Chart of Account', bold)
            worksheet.merge_range('C3:G3', 'Transactions', bold)
            worksheet.merge_range('H3:I3', 'Balance', bold)

            # header
            worksheet.write('A4', 'Code', bold)
            worksheet.write('B4', 'Title', bold)
            worksheet.write('C4', 'Date', bold)
            worksheet.write('D4', 'Type', bold)
            worksheet.write('E4', 'Number', bold)
            worksheet.write('F4', 'Debit', bold)
            worksheet.write('G4', 'Credit', bold)
            worksheet.write('H4', 'Debit', bold)
            worksheet.write('I4', 'Credit', bold)

            row = 5
            col = 0
            dataset = pd.DataFrame(new_list)
            for id, accountcode in dataset.fillna('NaN').sort_values(by=['accountcode', 'month']).groupby(['accountcode', 'description', 'beg_code', 'beg_amount']):
                worksheet.write(row, col, id[0])
                worksheet.write(row, col + 1, id[1])
                worksheet.write(row, col + 6, 'beginning balance')
                if id[2] == 'D':
                    worksheet.write(row, col + 7, float(format(id[3], '.2f')))
                    worksheet.write(row, col + 8, float(format(0, '.2f')))
                else:
                    worksheet.write(row, col + 7, float(format(0, '.2f')))
                    worksheet.write(row, col + 8, float(format(id[3], '.2f')))
                row += 1
                for sub, data in accountcode.iterrows():
                    if data['type'] == 'ending':
                        worksheet.write(row, col + 6, 'ending balance')
                        if data.dbegcode == 'D':
                            worksheet.write(row, col + 7, float(format(abs(data['begamount']), '.2f')))
                            worksheet.write(row, col + 8, float(format(0, '.2f')))
                        else:
                            worksheet.write(row, col + 7, float(format(0, '.2f')))
                            worksheet.write(row, col + 8, float(format(abs(data['begamount']), '.2f')))
                        row += 2
                    else:
                        worksheet.write(row, col + 2, data['month'], formatdate)
                        worksheet.write(row, col + 3, data['type'])
                        if data.dbegcode == 'D':
                            worksheet.write(row, col + 5, float(format(data['dbegamount'], '.2f')))
                            worksheet.write(row, col + 6, float(format(0, '.2f')))
                        else:
                            worksheet.write(row, col + 5, float(format(0, '.2f')))
                            worksheet.write(row, col + 6, float(format(data['dbegamount'], '.2f')))
                        if data.begcode == 'D':
                            worksheet.write(row, col + 7, float(format(abs(data['begamount']), '.2f')))
                            worksheet.write(row, col + 8, float(format(0, '.2f')))
                        else:
                            worksheet.write(row, col + 7, float(format(0, '.2f')))
                            worksheet.write(row, col + 8, float(format(abs(data['begamount']), '.2f')))
                        row += 1

            workbook.close()

            # Set up the Http response.
            filename = "generaljournalbook_summary.xlsx"


        # Rewind the buffer.
        output.seek(0)

        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response


@method_decorator(login_required, name='dispatch')
class TransactionView(TemplateView):
    template_name = 'generaljournalbook/transaction.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['chart'] = Chartofaccount.objects.filter(isdeleted=0, accounttype='P').order_by('accountcode')

        return context

#@csrf_exempt
def transgenerate(request):
    dto = request.GET["dto"]
    dfrom = request.GET["dfrom"]
    chart = request.GET["chart"]
    transtatus = request.GET["transtatus"]
    status = request.GET["status"]
    payeecode = request.GET["payeecode"]
    payeename = request.GET["payeename"]

    context = {}

    print "transaction listing"

    ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
    todate = datetime.date(int(ndto.year), int(ndto.month), 10)
    toyear = todate.year
    tomonth = todate.month
    nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
    fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
    fromyear = fromdate.year
    frommonth = fromdate.month

    prevdate = datetime.date(int(fromyear), int(frommonth), 10) - timedelta(days=15)
    prevyear = prevdate.year
    prevmonth = prevdate.month

    begbalamount = 0
    endbalamount = 0
    endcode = ''

    if chart != '':
        begbal =Subledgersummary.objects.filter(chartofaccount_id=chart, year=prevyear, month=prevmonth).first();
        if begbal:
            begbalamount = begbal.end_amount

        endbal =Subledgersummary.objects.filter(chartofaccount_id=chart, year=toyear, month=tomonth).first();
        if endbal:
            endbalamount = endbal.end_amount
            endcode = endbal.end_code

    context['result'] = query_transaction(dto, dfrom, chart, transtatus, status, payeecode, payeename)
    context['dto'] = dto
    context['dfrom'] = dfrom
    viewhtml = render_to_string('generaljournalbook/transaction_result.html', context)

    data = {
        'status': 'success',
        'viewhtml': viewhtml,
        'begbal': float(begbalamount),
        'endbal': float(endbalamount),
        'endcode': endcode
    }
    return JsonResponse(data)

def query_transaction(dto, dfrom, chart, transtatus, status, payeecode, payeename):
    print "Transaction Query"
    ''' Create query '''
    cursor = connection.cursor()

    chart_condition = ''
    chart_transtatus_ap = ''
    chart_transtatus_cv = ''
    chart_transtatus_jv = ''
    chart_transtatus_or = ''
    chart_status = ''
    chart_payeecode1 = ''
    chart_payeecode2 = ''
    chart_payeecode3 = ''
    chart_payeename1 = ''
    chart_payeename2 = ''
    chart_payeename3 = ''

    if chart != '':
        chart_condition = "AND d.chartofaccount_id = '" + str(chart) + "'"
    if transtatus != '':
        chart_transtatus_ap = "AND m.apstatus = '" + str(transtatus) + "'"
        chart_transtatus_cv = "AND m.cvstatus = '" + str(transtatus) + "'"
        chart_transtatus_jv = "AND m.jvstatus = '" + str(transtatus) + "'"
        chart_transtatus_or = "AND m.orstatus = '" + str(transtatus) + "'"
    if status != '':
        chart_status = "AND m.status = '" + str(status) + "'"
    if payeecode != '':
        chart_payeecode1 = "AND m.payeecode LIKE '%" + str(payeecode) + "%'"
        chart_payeecode2 = "AND m.payee_code LIKE '%" + str(payeecode) + "%'"
    if payeename != '':
        chart_payeename1 = "AND m.payeename LIKE '%" + str(payeename) + "%'"
        chart_payeename2 = "AND m.payee_name LIKE '%" + str(payeename) + "%'"

    query = "SELECT z.enter, z.enterdate, z.modify, z.modifydate, z.tran, z.item_counter, z.ap_num AS tnum, z.ap_date AS tdate, IFNULL(z.debitamount, 0) AS debitamount, IFNULL(z.creditamount, 0) AS creditamount, z.balancecode, z.apstatus AS transtatus, z.status AS status, bank.code AS bank, chart.accountcode, chart.description AS chartofaccount, cust.code AS custcode, cust.name AS customer, dept.code AS deptcode, dept.departmentname AS department, " \
            "emp.code AS empcode, CONCAT(IFNULL(emp.firstname, ''), ' ', IFNULL(emp.lastname, '')) AS employee, inpvat.code AS inpvatcode, inpvat.description AS inputvat, " \
            "outvat.code AS outvatcode, outvat.description AS outputvat, prod.code AS prodcode, prod.description AS product, " \
            "supp.code AS suppcode, supp.name AS supplier, vat.code AS vatcode, vat.description AS vat, wtax.code AS wtaxcode, wtax.description AS wtax, z.payeecode AS payee_code, z.payeename AS payee_name, z.particulars " \
            "FROM ( " \
            "SELECT u1.username AS enter, d.enterdate, u2.username AS modify, d.modifydate, 'AP' AS tran, d.item_counter, d.ap_num, d.ap_date, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.apstatus, m.status, m.payeecode, m.payeename, m.particulars	 " \
            "FROM apdetail AS d " \
            "LEFT OUTER JOIN apmain AS m ON m.id = d.apmain_id " \
            "LEFT OUTER JOIN auth_user AS u1 ON u1.id = d.enterby_id " \
            "LEFT OUTER JOIN auth_user AS u2 ON u2.id = d.modifyby_id " \
            "WHERE DATE(d.ap_date) >= '"+str(dfrom)+"' AND DATE(d.ap_date) <= '"+str(dto)+"' " \
            +str(chart_condition)+" "+str(chart_transtatus_ap)+" "+str(chart_status)+" "+str(chart_payeecode1)+" "+str(chart_payeename1)+"" \
            "UNION " \
            "SELECT u1.username AS enter, d.enterdate, u2.username AS modify, d.modifydate, 'CV' AS tran, d.item_counter, d.cv_num, d.cv_date, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.cvstatus, m.status, m.payee_code, m.payee_name, m.particulars	 " \
            "FROM cvdetail AS d " \
            "LEFT OUTER JOIN cvmain AS m ON m.id = d.cvmain_id " \
            "LEFT OUTER JOIN auth_user AS u1 ON u1.id = d.enterby_id " \
            "LEFT OUTER JOIN auth_user AS u2 ON u2.id = d.modifyby_id " \
            "WHERE DATE(d.cv_date) >= '"+str(dfrom)+"' AND DATE(d.cv_date) <= '"+str(dto)+"' " \
            +str(chart_condition)+" "+str(chart_transtatus_cv)+" "+str(chart_status)+" "+str(chart_payeecode2)+" "+str(chart_payeename2)+"" \
            "UNION " \
            "SELECT u1.username AS enter, d.enterdate, u2.username AS modify, d.modifydate, 'JV' AS tran, d.item_counter, d.jv_num, d.jv_date, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.jvstatus, m.status, '' AS payeecode, '' AS payeename, m.particular	 " \
            "FROM jvdetail AS d " \
            "LEFT OUTER JOIN jvmain AS m ON m.id = d.jvmain_id " \
            "LEFT OUTER JOIN auth_user AS u1 ON u1.id = d.enterby_id " \
            "LEFT OUTER JOIN auth_user AS u2 ON u2.id = d.modifyby_id " \
            "WHERE DATE(d.jv_date) >= '"+str(dfrom)+"' AND DATE(d.jv_date) <= '"+str(dto)+"' " \
            +str(chart_condition)+" "+str(chart_transtatus_jv)+" "+str(chart_status)+" "+str(chart_payeecode3)+" "+str(chart_payeename3)+"" \
            "UNION " \
            "SELECT u1.username AS enter, d.enterdate, u2.username AS modify, d.modifydate, 'OR' AS tran, d.item_counter, m.ornum, m.ordate, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.orstatus, m.status, m.payee_code, m.payee_name, m.particulars	" \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ordetail AS d ON m.id = d.ormain_id " \
            "LEFT OUTER JOIN auth_user AS u1 ON u1.id = d.enterby_id " \
            "LEFT OUTER JOIN auth_user AS u2 ON u2.id = d.modifyby_id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            +str(chart_condition)+" "+str(chart_transtatus_or)+" "+str(chart_status)+" "+str(chart_payeecode2)+" "+str(chart_payeename2)+") AS z " \
            "LEFT OUTER JOIN bankaccount AS bank ON bank.id = z.bankaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS chart ON chart.id = z.chartofaccount_id " \
            "LEFT OUTER JOIN customer AS cust ON cust.id = z.customer_id " \
            "LEFT OUTER JOIN department AS dept ON dept.id = z.department_id " \
            "LEFT OUTER JOIN employee AS emp ON emp.id = z.employee_id " \
            "LEFT OUTER JOIN inputvat AS inpvat ON inpvat.id = z.inputvat_id " \
            "LEFT OUTER JOIN outputvat AS outvat ON outvat.id = z.outputvat_id " \
            "LEFT OUTER JOIN product AS prod ON prod.id = z.product_id " \
            "LEFT OUTER JOIN supplier AS supp ON supp.id = z.supplier_id " \
            "LEFT OUTER JOIN vat AS vat ON vat.id = z.vat_id " \
            "LEFT OUTER JOIN wtax AS wtax ON wtax.id = z.wtax_id " \
            "ORDER BY z.ap_date, z.ap_num, z.tran, z.item_counter"
    #print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


@method_decorator(login_required, name='dispatch')
class TransExcel(View):
    def get(self, request):

        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]
        chart = request.GET["chart"]
        transtatus = request.GET["transtatus"]
        status = request.GET["status"]
        payeecode = request.GET["payeecode"]
        payeename = request.GET["payeename"]

        print "transaction listing"

        ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
        todate = datetime.date(int(ndto.year), int(ndto.month), 10)
        toyear = todate.year
        tomonth = todate.month
        nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
        fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
        fromyear = fromdate.year
        frommonth = fromdate.month

        prevdate = datetime.date(int(fromyear), int(frommonth), 10) - timedelta(days=15)
        prevyear = prevdate.year
        prevmonth = prevdate.month

        begbalamount = 0
        endbalamount = 0
        endcode = ''

        if chart != '':
            begbal = Subledgersummary.objects.filter(chartofaccount_id=chart, year=prevyear, month=prevmonth).first();
            if begbal:
                begbalamount = begbal.end_amount

            endbal = Subledgersummary.objects.filter(chartofaccount_id=chart, year=toyear, month=tomonth).first();
            if endbal:
                endbalamount = endbal.end_amount
                endcode = endbal.end_code

        result = query_transaction(dto, dfrom, chart, transtatus, status, payeecode, payeename)

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'MM/DD/YYYY'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', 'GENERAL LEDGER TRANSACTION LISTING', bold)
        worksheet.write('A2', 'AS OF ' + str(dfrom) + ' to ' + str(dto), bold)

        worksheet.write('A3', 'Beg Bal', bold)
        worksheet.write('B3', float(format(begbalamount, '.2f')))
        worksheet.write('C3', 'End Bal', bold)
        worksheet.write('A4', float(format(endbalamount, '.2f')))
        worksheet.write('B4', 'Balance Code', bold)
        worksheet.write('C4', endcode, bold)

        # header
        worksheet.write('A4', 'Type', bold)
        worksheet.write('B4', 'Number', bold)
        worksheet.write('C4', 'Date', bold)
        worksheet.write('D4', 'Particulars', bold)
        worksheet.write('E4', 'Account Code', bold)
        worksheet.write('F4', 'Chart of Account', bold)
        worksheet.write('G4', 'Payee', bold)
        worksheet.write('H4', 'Debit', bold)
        worksheet.write('I4', 'Credit', bold)
        worksheet.write('J4', 'Transaction Status', bold)
        worksheet.write('K4', 'Status', bold)
        worksheet.write('L4', 'Bank Account', bold)
        worksheet.write('M4', 'Customer Code', bold)
        worksheet.write('N4', 'Customer', bold)
        worksheet.write('O4', 'Supplier Code', bold)
        worksheet.write('P4', 'Supplier', bold)
        worksheet.write('Q4', 'Department Code', bold)
        worksheet.write('R4', 'Department', bold)
        worksheet.write('S4', 'Employee Code', bold)
        worksheet.write('T4', 'Employee', bold)
        worksheet.write('U4', 'Product Code', bold)
        worksheet.write('V4', 'Product', bold)
        worksheet.write('W4', 'VAT Code', bold)
        worksheet.write('X4', 'VAT', bold)
        worksheet.write('Y4', 'WTAX Code', bold)
        worksheet.write('Z4', 'WTAX', bold)
        worksheet.write('AA4', 'Input VAT Code', bold)
        worksheet.write('AB4', 'Input VAT', bold)
        worksheet.write('AC4', 'Output VAT Code', bold)
        worksheet.write('AD4', 'Output VAT', bold)
        worksheet.write('AE4', 'Created By', bold)
        worksheet.write('AF4', 'Created Date', bold)
        worksheet.write('AG4', 'Modified By', bold)
        worksheet.write('AH4', 'Modified Date', bold)


        row = 5
        col = 0

        #print result

        for data in result:
            worksheet.write(row, col, data.tran)
            worksheet.write(row, col + 1, data.tnum)
            worksheet.write(row, col + 2, data.tdate, formatdate)
            worksheet.write(row, col + 3, data.particulars)
            worksheet.write(row, col + 4, data.accountcode)
            worksheet.write(row, col + 5, data.chartofaccount)
            worksheet.write(row, col + 6, data.payee_name)
            worksheet.write(row, col + 7, float(format(data.debitamount, '.2f')))
            worksheet.write(row, col + 8, float(format(data.creditamount, '.2f')))
            worksheet.write(row, col + 9, data.transtatus)
            worksheet.write(row, col + 10, data.status)
            worksheet.write(row, col + 11, data.bank)
            worksheet.write(row, col + 12, data.custcode)
            worksheet.write(row, col + 13, data.customer)
            worksheet.write(row, col + 14, data.suppcode)
            worksheet.write(row, col + 15, data.supplier)
            worksheet.write(row, col + 16, data.deptcode)
            worksheet.write(row, col + 17, data.department)
            worksheet.write(row, col + 18, data.empcode)
            worksheet.write(row, col + 19, data.employee)
            worksheet.write(row, col + 20, data.prodcode)
            worksheet.write(row, col + 21, data.product)
            worksheet.write(row, col + 22, data.vatcode)
            worksheet.write(row, col + 23, data.vat)
            worksheet.write(row, col + 24, data.wtaxcode)
            worksheet.write(row, col + 25, data.wtax)
            worksheet.write(row, col + 26, data.inpvatcode)
            worksheet.write(row, col + 27, data.inputvat)
            worksheet.write(row, col + 28, data.outvatcode)
            worksheet.write(row, col + 29, data.outputvat)
            worksheet.write(row, col + 30, data.enter)
            worksheet.write(row, col + 31, data.enterdate, formatdate)
            worksheet.write(row, col + 32, data.modify)
            worksheet.write(row, col + 33, data.modifydate, formatdate)
            row += 1
            #z.enter, z.enterdate, z.modify, z.modifydate

        workbook.close()

        # Set up the Http response.
        filename = "transaction_listing.xlsx"

        # Rewind the buffer.

        output.seek(0)

        response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response