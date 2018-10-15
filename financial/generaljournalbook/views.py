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
        customer = request.GET['payee']
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

        list = Subledger.objects.filter(isdeleted=0).order_by('chartofaccount__accountcode', 'document_date', 'document_num','item_counter')[:0]

        if report == '1':
            subtitle = "Detailed Entries"
            q = Subledger.objects.filter(isdeleted=0).order_by('chartofaccount__accountcode', 'document_num','item_counter')
            if dfrom != '':
                q = q.filter(document_date__gte=dfrom)
            if dto != '':
                q = q.filter(document_date__lte=dto)

        #if chart != '':
            #q.filter(chartofaccount__accountcode=chart)
            # chartofaccount = Chartofaccount.objects.filter(isdeleted=0, id__exact=chart).first()
            # newdto = datetime.datetime.strptime(dto, "%Y-%m-%d")
            # prevdate = datetime.date(int(newdto.year), int(newdto.month), 10) - timedelta(days=15)
            # prevyear = prevdate.year
            # prevmonth = prevdate.month
            # begbal = Subledgersummary.objects.filter(chartofaccount=chart,year=prevyear,month=prevmonth).first()
            # beg_code = begbal.end_code
            # beg_amount = begbal.end_amount

        # if supplier != 'null':
        #     q = q.filter(supplier__exact=supplier)
        # if customer != 'null':
        #     q = q.filter(customer__exact=customer)
        # if employee != 'null':
        #     q = q.filter(employee__exact=employee)
        # if product != '':
        #     q = q.filter(product__exact=product)
        # if department != '':
        #     q = q.filter(department__exact=department)
        # if branch != '':
        #     q = q.filter(branch__exact=branch)
        # if bankaccount != '':
        #     q = q.filter(bankaccount__exact=bankaccount)
        # if vat != '':
        #     q = q.filter(vat__exact=vat)
        # if atax != '':
        #     q = q.filter(ataxcode__exact=atax)
        # if wtax != '':
        #     q = q.filter(wtax__exact=wtax)
        # if inputvat != '':
        #     q = q.filter(inputvat__exact=inputvat)
        # if outputvat != '':
        #     q = q.filter(outputvat__exact=outputvat)

        q = q.values('chartofaccount_id', 'chartofaccount__accountcode', 'chartofaccount__description', 'document_type', 'document_num', 'document_date', 'balancecode', 'amount')
        list = q[:250]

        new_list = {}

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
            for item, data in accountcode.iterrows():
                new_list[counter] = dict(accountcode=data.chartofaccount__accountcode, description=data.chartofaccount__description,
                                         amount=data.amount, dnum=data.document_num, ddate=data.document_date, balancecode=data.balancecode,
                                         type=data.document_type, begcode=beg_code, beg_amount=beg_amount)
            counter += 1

        #df = pd.DataFrame.from_records("DATA_GOES_HERE", columns=['amount'])
       # print df
        #df = pd.DataFrame.from_records(q)

        #dataset = pd.DataFrame.from_records(q)

        #print dataset

        # datalist[counter] = dict(accountcode=data.accountcode, description=data.description, tbb_debit=tbb_debit,
        #                          tbb_credit=tbb_credit,
        #                          tm_debit=tm_debit, tm_credit=tm_credit, tbe_debit=tbe_debit, tbe_credit=tbe_credit,
        #                          in_debit=in_debit, in_credit=in_credit, is_debit=is_debit, is_credit=is_credit)
        # counter = 0
        # for item in list:
        #     new_list[counter] = dict(hey='ASDA')
        #     counter += 1
        # print new_list

        # for item in list:
        #     new_list

        # for item in list:
        #     if item.balancecode == beg_code:
        #         beg_amount += item.amount
        #     else:
        #         beg_amount -= item.amount
        #     dict = {'date': item.document_date, 'type': item.document_type, 'number': item.document_num, 'particulars': item.particulars, 'trans_code': item.balancecode, 'trans_amount': item.amount, 'beg_code': beg_code, 'beg_amount': beg_amount}
        #     new_list.append(dict)
        # dict = {'date': '', 'type': 'ending', 'number': '', 'particulars': 'ending balance', 'trans_code': '', 'trans_amount': '', 'beg_code': beg_code, 'beg_amount': beg_amount}
        # new_list.append(dict)

        context = {
            "title": title,
            "subtitle": subtitle,
            "today": timezone.now(),
            "company": company,
            "listing": new_list,
            "total": total,
            "chartofaccount": chartofaccount,
            "begbal": begbal,
            "username": request.user,
        }

        return Render.render('generaljournalbook/report_1.html', context)

