from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.apps import apps
from django.db.models import Sum, Case, Value, When, Count, F, Q
from collections import namedtuple
from django.db import connection
from companyparameter.models import Companyparameter
from chartofaccount.models import Chartofaccount
from cmsadjustment.models import Cmmain, Cmitem
from subledger.models import Subledger
from subledgersummary.models import Subledgersummary
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
from django.db import connection
from collections import namedtuple
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict as ddict


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'rep_contributionmargin/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

@csrf_exempt
def generate(request):
    company = Companyparameter.objects.all().first()
    list = []
    total = []
    report = request.GET['report']
    dfrom = request.GET['from']
    dto = request.GET['to']
    title = "Contribution Margin Report"
    subtitle = ""
    filtertext = "Cost of Sales"

    list = {}
    cmlist = {}
    revlist = {}
    revlistsum = {}
    viewhtml = ''

    ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
    todate = datetime.date(int(ndto.year), int(ndto.month), 10)
    toyear = todate.year
    tomonth = todate.month
    nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
    fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
    fromyear = fromdate.year
    frommonth = fromdate.month

    context = {
        "subtitle": subtitle,
        "company": company,
        "list": list,
        "nfrom": nfrom,
        "ndto": ndto,
        "total": total,
        "title": title,
        "username": request.user,
    }

    list_product = cm_product(dfrom, dto)

    prod = {}
    prodname = {}
    prod_id = []
    opex = []
    col_prod = ''
    counter = 1
    for c in list_product:
        if col_prod != c.code:
            prod.update({c.id: c.description})
            prodname.update({c.id: c.description})
            prod_id.append(c.id)
            counter += 1
            col_prod = c.code

    prod = sorted(prod.items(), key=lambda kv: (kv[0]))
    prodname = sorted(prodname.items(), key=lambda kv: (kv[0]))

    if report == '1':

        q = query_cm_product_row(report, prod, dfrom, dto, toyear, tomonth)
        revenue = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, 'detail')
        revenuesum = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, '')
        cmitem = query_cm_item(prod, dfrom, dto)

        ## Operating income (loss) hack
        c = 1
        cmadjustment = 0
        rev = 0
        exp = 0
        income_loss = 0

        if cmitem:
            for x in range(counter):
                rev = eval('revenuesum[0].col' + str(c))
                exp = eval('sum(row.col' + str(c) + ' for row in q)')

                cmadjustment = eval('cmitem[0].col' + str(c))
                income_loss = (rev - exp) + cmadjustment
                opex.append(income_loss)
            c += 1

        list = q
        cmlist = cmitem
        revlist = revenue
        revlistsum = revenuesum

        context['prod'] = prodname
        context['list'] = list
        context['cmlist'] = cmlist
        context['revlist'] = revlist
        context['counter'] = counter + 1
        context['counterminus'] = counter
        context['opex'] = opex
        context['title'] = "Contribution Margin - Type of Expense"
        viewhtml = render_to_string('rep_contributionmargin/report_cm1.html', context)
    elif report == '2':

        q = query_cm_product_row(report, prod, dfrom, dto, toyear, tomonth)
        revenue = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, 'detail')
        revenuesum = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, '')
        cmitem = query_cm_item(prod, dfrom, dto)

        ## Operating income (loss) hack
        c = 1
        cmadjustment = 0
        rev = 0
        exp = 0
        income_loss = 0
        if cmitem:
            for x in range(counter):
                rev = eval('revenuesum[0].col' + str(c))
                exp = eval('sum(row.col' + str(c) + ' for row in q)')

                cmadjustment = eval('cmitem[0].col' + str(c))
                income_loss = (rev - exp) + cmadjustment
                opex.append(income_loss)
                c += 1

        list = q
        cmlist = cmitem
        revlist = revenue
        revlistsum = revenuesum

        context['prod'] = prodname
        context['list'] = list
        context['cmlist'] = cmlist
        context['revlist'] = revlist
        context['counter'] = counter + 1
        context['counterminus'] = counter
        context['opex'] = opex
        context['title'] = "Contribution Margin - Kind of Expense"
        viewhtml = render_to_string('rep_contributionmargin/report_cm2.html', context)

    elif report == '3':

        q = query_cm_product_row(report, prod, dfrom, dto, toyear, tomonth)
        revenue = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, 'detail')
        revenuesum = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, '')
        cmitem = query_cm_item(prod, dfrom, dto)

        ## Operating income (loss) hack
        c = 1
        cmadjustment = 0
        rev = 0
        exp = 0
        income_loss = 0
        if cmitem:
            for x in range(counter):
                rev = eval('revenuesum[0].col' + str(c))
                exp = eval('sum(row.col' + str(c) + ' for row in q)')

                cmadjustment = eval('cmitem[0].col' + str(c))
                income_loss = (rev - exp) + cmadjustment
                opex.append(income_loss)
                c += 1

        list = q
        cmlist = cmitem
        revlist = revenue
        revlistsum = revenuesum

        context['prod'] = prodname
        context['list'] = list
        context['cmlist'] = cmlist
        context['revlist'] = revlist
        context['counter'] = counter + 1
        context['counterminus'] = counter
        context['opex'] = opex
        context['title'] = "Contribution Margin - Group"
        viewhtml = render_to_string('rep_contributionmargin/report_cm3.html', context)

    elif report == '4':

        q = query_cm_product_row(report, prod, dfrom, dto, toyear, tomonth)
        revenue = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, 'detail')
        revenuesum = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, '')
        cmitem = query_cm_item(prod, dfrom, dto)

        ## Operating income (loss) hack
        c = 1
        cmadjustment = 0
        rev = 0
        exp = 0
        income_loss = 0

        if cmitem:
            for x in range(counter):
                rev = eval('revenuesum[0].col' + str(c))
                exp = eval('sum(row.col' + str(c) + ' for row in q)')

                cmadjustment = eval('cmitem[0].col' + str(c))
                income_loss = (rev - exp) + cmadjustment
                opex.append(income_loss)
                c += 1

        list = q
        cmlist = cmitem
        revlist = revenue
        revlistsum = revenuesum

        context['prod'] = prodname
        context['list'] = list
        context['cmlist'] = cmlist
        context['revlist'] = revlist
        context['counter'] = counter + 1
        context['counterminus'] = counter
        context['opex'] = opex
        context['title'] = "Contribution Margin - Expense Summary"
        viewhtml = render_to_string('rep_contributionmargin/report_cm4.html', context)

    else:
        print 'nothing'
        viewhtml = []


    data = {
        'status': 'success',
        'viewhtml': viewhtml,
    }
    return JsonResponse(data)

@method_decorator(login_required, name='dispatch')
class GenerateExcel(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = []
        total = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        title = "Contribution Margin"
        subtitle = ""
        typetext = "Summary"
        filtertext = "Cost of Sales"

        ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
        todate = datetime.date(int(ndto.year), int(ndto.month), 10)
        toyear = todate.year
        tomonth = todate.month
        nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
        fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
        fromyear = fromdate.year
        frommonth = fromdate.month


        list = []
        cmlist = []
        revenuelist = []
        revenuesumlist = []
        filename = "contributionmargin.xlsx"

        list_product = cm_product(dfrom, dto)

        prod = {}
        prodname = {}
        col_prod = ''
        counter = 1
        for c in list_product:
            if col_prod != c.code:
                prod.update({c.id: c.description})
                prodname.update({c.id: c.description})
                counter += 1
                col_prod = c.code

        prod = sorted(prod.items(), key=lambda kv: (kv[0]))
        prodname = sorted(prodname.items(), key=lambda kv: (kv[0]))

        if report == '1':
            list = query_cm_product_row(report, prod, dfrom, dto, toyear, tomonth)
            cmitem = query_cm_item(prod, dfrom, dto)
            revenue = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, 'detail')
            revenuesum = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, '')
            title = "Contribution Margin - Type of Expense"
            filename = "contributionmargin-typeofexpense.xlsx"
        elif report == '2':
            list = query_cm_product_row(report, prod, dfrom, dto, toyear, tomonth)
            cmitem = query_cm_item(prod, dfrom, dto)
            revenue = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, 'detail')
            revenuesum = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, '')
            title = "Contribution Margin - Kind of Expense"
            filename = "contributionmargin-kindofexpense.xlsx"
        elif report == '3':
            list = query_cm_product_row(report, prod, dfrom, dto, toyear, tomonth)
            cmitem = query_cm_item(prod, dfrom, dto)
            revenue = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, 'detail')
            revenuesum = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, '')
            title = "Contribution Margin - Group"
            filename = "contributionmargin-group.xlsx"
        elif report == '4':
            list = query_cm_product_row(report, prod, dfrom, dto, toyear, tomonth)
            cmitem = query_cm_item(prod, dfrom, dto)
            revenue = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, 'detail')
            revenuesum = query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, '')
            title = "Contribution Margin - Expense Summary"
            filename = "contributionmargin-expensesummary.xlsx"

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', str(title), bold)
        worksheet.write('A2', 'for the period of '+str(dfrom)+' to'+str(dto), bold)

        # header
        worksheet.write('A5', '', bold)
        rowh = 4
        colh = 1
        subtotal = []
        grandtotal = []
        grandgrandtotal = 0
        cmtotal = 0
        for key, val in prod:
            worksheet.write(rowh, colh, val, bold)
            subtotal.append(0)
            grandtotal.append(0)
            colh += 1
        worksheet.write(rowh, colh, 'TOTAL', bold)

        df = pd.DataFrame(list)
        cmlist = pd.DataFrame(cmitem)
        revenuelist = pd.DataFrame(revenue)
        revenuesumlist = pd.DataFrame(revenuesum)
        if report == '1':

            row = 6
            col = 0
            if list:
                print revenuesumlist['col1'][0]
                for index, rowr in revenuelist.iterrows():
                    worksheet.write(row, col, str(rowr.typecode))
                    colrh = 0
                    colrv = 1
                    revtotal = 0
                    for key, val in prod:
                        xx = eval('rowr.col' + str(colrv))
                        revtotal += xx
                        worksheet.write(row, colrh + 1, float(format(xx, '.2f')))
                        colrh += 1
                        colrv += 1
                    worksheet.write(row, colrh + 1, float(format(revtotal, '.2f')))
                    row += 1

                for index, rowr in revenuesumlist.iterrows():
                    worksheet.write(row, col, ' Total Revenue', bold)
                    colrh = 0
                    colrv = 1
                    revtotal = 0
                    for key, val in prod:
                        xx = eval('rowr.col' + str(colrv))
                        revtotal += xx
                        worksheet.write(row, colrh + 1, float(format(xx, '.2f')), bold)
                        colrh += 1
                        colrv += 1
                    worksheet.write(row, colrh + 1, float(format(revtotal, '.2f')), bold)
                    row += 1
                row += 2

                for type, typecode in df.fillna('NaN').groupby(['typeid', 'typecode']):
                    worksheet.write(row, col, str(type[1]), bold)
                    row += 1
                    totaltotal = 0
                    for data, item in typecode.iterrows():
                        worksheet.write(row, col, '      ' + str(item.csubheaddescription))
                        colh = 1
                        total = 0
                        for key, val in prod:
                            x = eval('item.col' + str(colh))
                            subtotal[colh - 1] += x
                            grandtotal[colh - 1] += x
                            worksheet.write(row, colh, float(format(x, '.2f')))
                            colh += 1
                            total += x
                        worksheet.write(row, colh, float(format(total, '.2f')))
                        totaltotal += total
                        grandgrandtotal += total
                        row += 1

                    worksheet.write(row, col, '  Subtotal - ' + str(type[1]), bold)
                    colh = 0
                    for key, val in prod:
                        worksheet.write(row, colh + 1, float(format(subtotal[colh], '.2f')), bold)
                        subtotal[colh] = 0
                        colh += 1
                    worksheet.write(row, colh + 1, float(format(totaltotal, '.2f')), bold)
                    row += 1

                worksheet.write(row, col, 'Total Expenses', bold)
                colh = 0
                for key, val in prod:
                    worksheet.write(row, colh + 1, float(format(grandtotal[colh], '.2f')), bold)
                    colh += 1
                worksheet.write(row, colh + 1, float(format(grandgrandtotal, '.2f')), bold)
                row += 1

                worksheet.write(row, col, 'Contribution Margin', bold)
                colh = 0

                for key, val in prod:
                    xx = eval("revenuesumlist['col" + str(colh + 1) + "'][0]")
                    worksheet.write(row, colh + 1, float(format(xx - grandtotal[colh], '.2f')), bold)
                    colh += 1
                xxx = eval("revenuesumlist['col" + str(colh + 1) + "'][0]")
                worksheet.write(row, colh + 1, float(format(xxx - grandgrandtotal, '.2f')), bold)
                row += 1

                worksheet.write(row, col, 'Add: (Deduct) adjustment', bold)
                worksheet.write(row + 1, col, 'Operating Income (Loss)', bold)
                colh = 0

                for index, rowx in cmlist.iterrows():
                    colh = 0
                    colv = 1
                    incomeloss = 0
                    for key, val in prod:
                        xx = eval('rowx.col' + str(colv))
                        xxx = eval("revenuesumlist['col" + str(colv) + "'][0]")
                        incomeloss = (xxx - grandtotal[colh]) + xx
                        cmtotal += xx
                        worksheet.write(row, colh + 1, float(format(xx, '.2f')), bold)
                        worksheet.write(row + 1, colh + 1, incomeloss, bold)
                        colh += 1
                        colv += 1
                xxx = eval("revenuesumlist['col" + str(colh + 1) + "'][0]")
                worksheet.write(row, colh + 1, float(format(cmtotal, '.2f')), bold)
                worksheet.write(row + 1, colh + 1, float(format(xxx - grandgrandtotal + cmtotal, '.2f')), bold)
                row += 1

        elif report == '2':

            row = 6
            col = 0
            if list:
                #print revenuesumlist['col1'][0]
                for index, rowr in revenuelist.iterrows():
                    worksheet.write(row, col, str(rowr.typecode))
                    colrh = 0
                    colrv = 1
                    revtotal = 0
                    for key, val in prod:
                        xx = eval('rowr.col' + str(colrv))
                        revtotal += xx
                        worksheet.write(row, colrh + 1, float(format(xx, '.2f')))
                        colrh += 1
                        colrv += 1
                    worksheet.write(row, colrh + 1, float(format(revtotal, '.2f')))
                    row += 1

                for index, rowr in revenuesumlist.iterrows():
                    worksheet.write(row, col, ' Total Revenue', bold)
                    colrh = 0
                    colrv = 1
                    revtotal = 0
                    for key, val in prod:
                        xx = eval('rowr.col' + str(colrv))
                        revtotal += xx
                        worksheet.write(row, colrh + 1, float(format(xx, '.2f')), bold)
                        colrh += 1
                        colrv += 1
                    worksheet.write(row, colrh + 1, float(format(revtotal, '.2f')), bold)
                    row += 1
                row += 2

                ind = df.sort_values(['kindid', 'kindcode'], ascending=False).groupby(['kindid', 'kindcode']).head(100000)

                k = ''
                row += 1
                stotal = 0
                gtotal = 0
                totaltotal = 0
                for key, value in ind.iterrows():
                    if (k != value['kindcode'] and k == ''):
                        worksheet.write(row, col, str(value['kindcode']), bold)
                        row += 1

                    if k != value['kindcode'] and k != '':
                        worksheet.write(row, col, '  Subtotal - ' + str(k), bold)
                        colhh = 0

                        for key, val in prod:
                            worksheet.write(row, colhh + 1, float(format(subtotal[colhh], '.2f')), bold)
                            stotal += subtotal[colhh]
                            subtotal[colhh] = 0
                            colhh += 1
                        worksheet.write(row, colhh + 1, float(format(stotal, '.2f')), bold)
                        stotal = 0
                        row += 2

                        worksheet.write(row, col, str(value['kindcode']), bold)
                        row += 1

                    worksheet.write(row, col, '      ' + str(value['csubheaddescription']))
                    colh = 1
                    total = 0
                    for key, val in prod:
                        x = value['col' + str(colh)]
                        subtotal[colh - 1] += x
                        grandtotal[colh - 1] += x
                        worksheet.write(row, colh, float(format(x, '.2f')))
                        colh += 1
                        total += x
                    worksheet.write(row, colh, float(format(total, '.2f')))
                    row += 1

                    k = value['kindcode']

                worksheet.write(row, col, '  Subtotal - ' + str(value['kindcode']), bold)
                colhh = 0
                for key, val in prod:
                    worksheet.write(row, colhh + 1, float(format(subtotal[colhh], '.2f')), bold)
                    stotal += subtotal[colhh]
                    subtotal[colhh] = 0
                    colhh += 1
                worksheet.write(row, colhh + 1, float(format(stotal, '.2f')), bold)
                stotal = 0
                row += 1

                worksheet.write(row, col, 'Total Expenses', bold)
                colhhh = 0
                for key, val in prod:
                    worksheet.write(row, colhhh + 1, float(format(grandtotal[colhhh], '.2f')), bold)
                    gtotal += grandtotal[colhhh]
                    colhhh += 1
                worksheet.write(row, colhhh + 1, float(format(gtotal, '.2f')), bold)
                row += 1

                worksheet.write(row, col, 'Contribution Margin', bold)
                colhcm = 0

                for key, val in prod:
                    xx = eval("revenuesumlist['col" + str(colhcm + 1) + "'][0]")
                    worksheet.write(row, colhcm + 1, float(format(xx - grandtotal[colhcm], '.2f')), bold)
                    colhcm += 1
                xxx = eval("revenuesumlist['col" + str(colhcm + 1) + "'][0]")
                worksheet.write(row, colhcm + 1, float(format(xxx - gtotal, '.2f')), bold)
                row += 1

                worksheet.write(row, col, 'Add: (Deduct) adjustment', bold)
                worksheet.write(row + 1, col, 'Operating Income (Loss)', bold)
                colh = 0

                for index, rowx in cmlist.iterrows():
                    colh = 0
                    colv = 1
                    incomeloss = 0
                    for key, val in prod:
                        xx = eval('rowx.col' + str(colv))
                        xxx = eval("revenuesumlist['col" + str(colv) + "'][0]")
                        incomeloss = (xxx - grandtotal[colh]) + xx
                        cmtotal += xx
                        worksheet.write(row, colh + 1, float(format(xx, '.2f')), bold)
                        worksheet.write(row + 1, colh + 1, incomeloss, bold)
                        colh += 1
                        colv += 1
                xxx = eval("revenuesumlist['col" + str(colh + 1) + "'][0]")
                worksheet.write(row, colh + 1, float(format(cmtotal, '.2f')), bold)
                worksheet.write(row + 1, colh + 1, float(format(xxx - gtotal + cmtotal, '.2f')), bold)
                row += 1

        elif report == '3':
            row = 6
            col = 0
            if list:
                print revenuesumlist['col1'][0]
                for index, rowr in revenuelist.iterrows():
                    worksheet.write(row, col, str(rowr.typecode))
                    colrh = 0
                    colrv = 1
                    revtotal = 0
                    for key, val in prod:
                        xx = eval('rowr.col' + str(colrv))
                        revtotal += xx
                        worksheet.write(row, colrh + 1, float(format(xx, '.2f')))
                        colrh += 1
                        colrv += 1
                    worksheet.write(row, colrh + 1, float(format(revtotal, '.2f')))
                    row += 1

                for index, rowr in revenuesumlist.iterrows():
                    worksheet.write(row, col, ' Total Revenue', bold)
                    colrh = 0
                    colrv = 1
                    revtotal = 0
                    for key, val in prod:
                        xx = eval('rowr.col' + str(colrv))
                        revtotal += xx
                        worksheet.write(row, colrh + 1, float(format(xx, '.2f')), bold)
                        colrh += 1
                        colrv += 1
                    worksheet.write(row, colrh + 1, float(format(revtotal, '.2f')), bold)
                    row += 1
                row += 2

                for type, typecode in df.fillna('NaN').groupby(['csubgrouptitle', 'csubgrouptitle']):
                    worksheet.write(row, col, str(type[1]), bold)
                    row += 1
                    totaltotal = 0
                    for data, item in typecode.iterrows():
                        worksheet.write(row, col, '      ' + str(item.csubheaddescription))
                        colh = 1
                        total = 0
                        for key, val in prod:
                            x = eval('item.col' + str(colh))
                            subtotal[colh - 1] += x
                            grandtotal[colh - 1] += x
                            worksheet.write(row, colh, float(format(x, '.2f')))
                            colh += 1
                            total += x
                        worksheet.write(row, colh, float(format(total, '.2f')))
                        totaltotal += total
                        grandgrandtotal += total
                        row += 1

                    worksheet.write(row, col, '  Subtotal - ' + str(type[1]), bold)
                    colh = 0
                    for key, val in prod:
                        worksheet.write(row, colh + 1, float(format(subtotal[colh], '.2f')), bold)
                        subtotal[colh] = 0
                        colh += 1
                    worksheet.write(row, colh + 1, float(format(totaltotal, '.2f')), bold)
                    row += 1

                worksheet.write(row, col, 'Total Expenses', bold)
                colh = 0
                for key, val in prod:
                    worksheet.write(row, colh + 1, float(format(grandtotal[colh], '.2f')), bold)
                    colh += 1
                worksheet.write(row, colh + 1, float(format(grandgrandtotal, '.2f')), bold)
                row += 1

                worksheet.write(row, col, 'Contribution Margin', bold)
                colh = 0

                for key, val in prod:
                    xx = eval("revenuesumlist['col" + str(colh + 1) + "'][0]")
                    worksheet.write(row, colh + 1, float(format(xx - grandtotal[colh], '.2f')), bold)
                    colh += 1
                xxx = eval("revenuesumlist['col" + str(colh + 1) + "'][0]")
                worksheet.write(row, colh + 1, float(format(xxx - grandgrandtotal, '.2f')), bold)
                row += 1

                worksheet.write(row, col, 'Add: (Deduct) adjustment', bold)
                worksheet.write(row + 1, col, 'Operating Income (Loss)', bold)
                colh = 0

                for index, rowx in cmlist.iterrows():
                    colh = 0
                    colv = 1
                    incomeloss = 0
                    for key, val in prod:
                        xx = eval('rowx.col' + str(colv))
                        xxx = eval("revenuesumlist['col" + str(colv) + "'][0]")
                        incomeloss = (xxx - grandtotal[colh]) + xx
                        cmtotal += xx
                        worksheet.write(row, colh + 1, float(format(xx, '.2f')), bold)
                        worksheet.write(row + 1, colh + 1, incomeloss, bold)
                        colh += 1
                        colv += 1
                xxx = eval("revenuesumlist['col" + str(colh + 1) + "'][0]")
                worksheet.write(row, colh + 1, float(format(cmtotal, '.2f')), bold)
                worksheet.write(row + 1, colh + 1, float(format(xxx - grandgrandtotal + cmtotal, '.2f')), bold)
                row += 1

        elif report == '4':

            row = 6
            col = 0
            if list:
                print revenuesumlist['col1'][0]
                for index, rowr in revenuelist.iterrows():
                    worksheet.write(row, col, str(rowr.typecode))
                    colrh = 0
                    colrv = 1
                    revtotal = 0
                    for key, val in prod:
                        xx = eval('rowr.col' + str(colrv))
                        revtotal += xx
                        worksheet.write(row, colrh + 1, float(format(xx, '.2f')))
                        colrh += 1
                        colrv += 1
                    worksheet.write(row, colrh + 1, float(format(revtotal, '.2f')))
                    row += 1

                for index, rowr in revenuesumlist.iterrows():
                    worksheet.write(row, col, ' Total Revenue', bold)
                    colrh = 0
                    colrv = 1
                    revtotal = 0
                    for key, val in prod:
                        xx = eval('rowr.col' + str(colrv))
                        revtotal += xx
                        worksheet.write(row, colrh + 1, float(format(xx, '.2f')), bold)
                        colrh += 1
                        colrv += 1
                    worksheet.write(row, colrh + 1, float(format(revtotal, '.2f')), bold)
                    row += 1
                row += 2

                ind = df.sort_values(['kindid', 'kindcode'], ascending=False).groupby(['kindid', 'kindcode']).head(
                    100000)

                k = ''
                row += 1
                stotal = 0
                gtotal = 0
                totaltotal = 0
                for key, value in ind.iterrows():
                    if (k != value['kindcode'] and k == ''):
                        worksheet.write(row, col, str(value['kindcode']), bold)
                        row += 1

                    if k != value['kindcode'] and k != '':
                        worksheet.write(row, col, '  Subtotal - ' + str(k), bold)
                        colhh = 0

                        for key, val in prod:
                            worksheet.write(row, colhh + 1, float(format(subtotal[colhh], '.2f')), bold)
                            stotal += subtotal[colhh]
                            subtotal[colhh] = 0
                            colhh += 1
                        worksheet.write(row, colhh + 1, float(format(stotal, '.2f')), bold)
                        stotal = 0
                        row += 2

                        worksheet.write(row, col, str(value['kindcode']), bold)
                        row += 1

                    worksheet.write(row, col, '      ' + str(value['csubheaddescription']))
                    colh = 1
                    total = 0
                    for key, val in prod:
                        x = value['col' + str(colh)]
                        subtotal[colh - 1] += x
                        grandtotal[colh - 1] += x
                        worksheet.write(row, colh, float(format(x, '.2f')))
                        colh += 1
                        total += x
                    worksheet.write(row, colh, float(format(total, '.2f')))
                    row += 1

                    k = value['kindcode']

                worksheet.write(row, col, '  Subtotal - ' + str(value['kindcode']), bold)
                colhh = 0
                for key, val in prod:
                    worksheet.write(row, colhh + 1, float(format(subtotal[colhh], '.2f')), bold)
                    stotal += subtotal[colhh]
                    subtotal[colhh] = 0
                    colhh += 1
                worksheet.write(row, colhh + 1, float(format(stotal, '.2f')), bold)
                stotal = 0
                row += 1

                worksheet.write(row, col, 'Total Expenses', bold)
                colhhh = 0
                for key, val in prod:
                    worksheet.write(row, colhhh + 1, float(format(grandtotal[colhhh], '.2f')), bold)
                    gtotal += grandtotal[colhhh]
                    colhhh += 1
                worksheet.write(row, colhhh + 1, float(format(gtotal, '.2f')), bold)
                row += 1

                worksheet.write(row, col, 'Contribution Margin', bold)
                colhcm = 0

                for key, val in prod:
                    xx = eval("revenuesumlist['col" + str(colhcm + 1) + "'][0]")
                    worksheet.write(row, colhcm + 1, float(format(xx - grandtotal[colhcm], '.2f')), bold)
                    colhcm += 1
                xxx = eval("revenuesumlist['col" + str(colhcm + 1) + "'][0]")
                worksheet.write(row, colhcm + 1, float(format(xxx - gtotal, '.2f')), bold)
                row += 1

                worksheet.write(row, col, 'Add: (Deduct) adjustment', bold)
                worksheet.write(row + 1, col, 'Operating Income (Loss)', bold)
                colh = 0

                for index, rowx in cmlist.iterrows():
                    colh = 0
                    colv = 1
                    incomeloss = 0
                    for key, val in prod:
                        xx = eval('rowx.col' + str(colv))
                        xxx = eval("revenuesumlist['col" + str(colv) + "'][0]")
                        incomeloss = (xxx - grandtotal[colh]) + xx
                        cmtotal += xx
                        worksheet.write(row, colh + 1, float(format(xx, '.2f')), bold)
                        worksheet.write(row + 1, colh + 1, incomeloss, bold)
                        colh += 1
                        colv += 1
                xxx = eval("revenuesumlist['col" + str(colh + 1) + "'][0]")
                worksheet.write(row, colh + 1, float(format(cmtotal, '.2f')), bold)
                worksheet.write(row + 1, colh + 1, float(format(xxx - gtotal + cmtotal, '.2f')), bold)
                row += 1

        else:
            print 'do nothing'

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        #filename = "departmentbudget.xlsx"
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        new_list = []
        mtotal = 0
        list_total = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        title = "Contribution Margin Report"
        list = []

        if report == '1':
            title = "Contribution Margin - Year-To-Date"
            q = query_cmytd(dfrom, dto)

            # to display the output or data
            # print q

        elif report == '2':
            title = "Advertising Discounts / Circulation Returns"
            dmain = "4"
            dclas1 = "2"
            dclas2 = "3"
            q = query_cmdiscountreturn(dfrom, dto, dmain, dclas1, dclas2)

            # to display the output or data
            # print(q)

        elif report == '3':
            title = "Other Income - INS"
            daccount = "7136000000"
            q = query_cmotherincomeins(dfrom, dto, daccount)

            # to display the output or data
            # print q

        list = q

        if report == '3':

            df = pd.DataFrame(q)

            # print df

            grandmtotal = 0

            for code, chartofaccount in df.fillna('NaN').groupby(['accountcode', 'title']):

                for item, data in chartofaccount.iterrows():
                    new_list.append({'ccode': data.accountcode, 'chartofaccount': data.title,
                                     'docdate': data.document_date, 'doctype': data.document_type,
                                     'docnum': data.document_num, 'particulars': data.particulars,
                                     'amount': data.amount })

                    grandmtotal += data.amount

            new_list.append({'ccode': 'subtotal', 'chartofaccount': '',
                             'docdate': '', 'doctype': '',
                             'docnum': '', 'particulars': '',
                             'amount': grandmtotal })

            list = new_list

            # print list
            # list = q

        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "list_total": list_total,
            "username": request.user,
        }
        if report == '1':
            return Render.render('rep_contributionmargin/report_1.html', context)
        elif report == '2':
            return Render.render('rep_contributionmargin/report_2.html', context)
        elif report == '3':
            return Render.render('rep_contributionmargin/report_3.html', context)
        # elif report == '4':
        #     return Render.render('rep_contributionmargin/report_4.html', context)
        else:
            return Render.render('rep_contributionmargin/report_1.html', context)


def cm_product(dfrom, dto):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT DISTINCT p.id, p.code, p.description " \
            "FROM subledger AS s " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = s.chartofaccount_id " \
            "LEFT OUTER JOIN department AS d ON d.id = s.department_id " \
            "LEFT OUTER JOIN product AS p ON p.id = d.product_id " \
            "WHERE s.document_date >= '"+str(dfrom)+ "' AND s.document_date <= '"+str(dto)+"' " \
            "AND c.main = 5 " \
            "ORDER BY p.description"


    # "AND c.main = 5 AND p.id IN (3,8,1) " \

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_cm_item(prod, dfrom, dto):
    print "Transaction Query Budget Report"
    ''' Create query '''
    cursor = connection.cursor()

    str_col = ''
    str_colmain = ''
    str_total = ''
    str_totalmain = ''
    str_left = ''
    #str_con = ''
    #type_report = ''

    counter = 1
    for id, d in prod:
        str_colmain += "SUM(col" + str(counter) + ") AS col" + str(counter) + ", "
        str_col += "IFNULL(col" + str(counter) + ".amount, 0) AS col" + str(counter) + ", "
        str_totalmain += "SUM(col" + str(counter) + ") + "
        str_total += "SUM(IFNULL(col" + str(counter) + ".amount, 0)) + "
        str_left += "LEFT OUTER JOIN " \
                    "(SELECT item.product_code, item.product_name, item.product_id, SUM(IFNULL(item.debitamount, 0)) AS debit, SUM(IFNULL(item.creditamount, 0)) AS credit, (SUM(IFNULL(item.debitamount, 0)) -  SUM(IFNULL(item.creditamount, 0))) AS amount " \
                    "FROM cmitem AS item " \
                    "WHERE DATE(item.cmdate) >= '" + str(dfrom) + "' AND DATE(item.cmdate) <= '" + str(dto) + "' AND item.product_id = " + str(id) + " " \
                    "GROUP BY item.product_id) AS col" + str(counter) + " ON col" + str(counter) + ".product_id = i.product_id "
        #str_con += "IFNULL(col" + str(counter) + ".amount, 0) + "
        counter += 1

    str_total = "(" + str(str_total) + " 0 ) AS col" + str(counter) + ", "
    str_totalmain = "(" + str(str_totalmain) + " 0 ) AS col" + str(counter) + ", "

    print 'start'
    query = "SELECT  "+str(str_colmain)+" "+str(str_totalmain)+" '' AS product_code " \
            "FROM ( SELECT "+str(str_col)+" "+str(str_total)+" i.product_code  FROM cmitem AS i " + str(str_left) + " " \
            "WHERE DATE(i.cmdate) >= '" + str(dfrom) + "' AND DATE(i.cmdate) <= '" + str(dto) + "' GROUP BY i.product_id) AS z"
    #print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_revenue_product_row(report, prod, dfrom, dto, toyear, tomonth, type):
    print "Transaction Query Budget Report"
    ''' Create query '''
    cursor = connection.cursor()

    str_col = ''
    str_total = ''
    str_left = ''
    str_con = ''
    type_report = ''
    #type_condition = 'GROUP BY cgroup.description, csubhead.description'
    type_condition = ''
    if type == 'detail':
        type_condition = 'GROUP BY typeid'


    if report == '1':
        type_report = "ORDER BY ty.id, ch.main, ch.item, ch.cont, ch.sub"
    elif report == '2':
        type_report = "ORDER BY kd.id DESC, ch.main, ch.item, ch.cont, ch.sub"
    elif report == '3':
        type_report = "ORDER BY csubgroup.title DESC, ch.main, ch.item, ch.cont, ch.sub"
    elif report == '4':
        type_report = "ORDER BY typeid ASC, c.accountcode"
    else:
        print 'do nothing'

    counter = 1
    #for id, d in dept.items():
    for id, d in prod:
        str_col += "SUM(IFNULL(col"+str(counter)+".amount, 0)) AS col"+str(counter)+", "
        str_total += "SUM(IFNULL(col"+str(counter)+".amount, 0)) + "
        str_left += "LEFT OUTER JOIN " \
                    "(SELECT YEAR(a.document_date) AS `year`, MONTH(a.document_date) AS `month`, IF (SUBSTR(c.accountcode, 1, 2) = '41', IF (SUBSTR(c.accountcode, 1, 3) = '411', 1, 2), IF(SUBSTR(c.accountcode, 1,2) = '43', '1', 2)) AS itemx," \
                    " SUM(IF(a.balancecode = 'C', a.amount, a.amount * -1)) AS amount, a.balancecode, a.chartofaccount_id, c.product_id  " \
                    "FROM subledger AS a " \
                    "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
                    "WHERE DATE(a.document_date) >= '"+str(dfrom)+"' AND DATE(a.document_date) <= '"+str(dto)+"' AND c.main = 4  AND c.product_id  = "+str(id)+" " \
                    "GROUP BY itemx, c.product_id) AS col"+str(counter)+" ON col"+str(counter)+".chartofaccount_id = c.id "
        str_con += "IFNULL(col" + str(counter) + ".amount, 0) + "
        counter += 1

    str_total = "("+str(str_total)+" 0 ) AS col"+str(counter)+", "
    print 'start'
    query = "SELECT IF (SUBSTR(c.accountcode, 1, 6) = '411960', 3, IF (SUBSTR(c.accountcode, 1, 6) = '412650', 4, IF (SUBSTR(c.accountcode, 1, 2) = '41', IF (SUBSTR(c.accountcode, 1, 3) = '411', 1, 2), IF(SUBSTR(c.accountcode, 1,2) = '43', 1, 2)))) AS typeid, " \
            "IF (SUBSTR(c.accountcode, 1, 6) = '411960', 'NET EVENTS', IF (SUBSTR(c.accountcode, 1, 6) = '412650', 'NET DIGITAL', IF (SUBSTR(c.accountcode, 1, 2) = '41', IF (SUBSTR(c.accountcode, 1, 3) = '411', 'NET ADVERTISING', 'NET CIRCULATION REVENUE'), IF(SUBSTR(c.accountcode, 1,2) = '43', 'NET ADVERTISING', 'NET CIRCULATION REVENUE')))) AS typecode, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription, c.accountcode, c.description, "+str(str_col)+" "+str(str_total)+" c.id " \
            "FROM chartofaccount AS c "+str(str_left)+" " \
            "LEFT OUTER JOIN chartofaccount AS ch ON ch.id = c.id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = ch.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = ch.main AND csubgroup.clas = ch.clas AND csubgroup.item = ch.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = ch.main AND csubhead.clas = ch.clas AND csubhead.item = ch.item AND csubhead.cont = ch.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "LEFT OUTER JOIN typeofexpense AS ty ON ty.id = ch.typeofexpense_id " \
            "LEFT OUTER JOIN kindofexpense AS kd ON kd.id = ch.kindofexpense_id " \
            "WHERE c.main = 4 AND ch.accounttype != 'T' "+" "+str(type_condition)+" "+str(type_report)+" "
    #print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_cm_product_row(report, prod, dfrom, dto, toyear, tomonth):
    print "Transaction Query Budget Report"
    ''' Create query '''
    cursor = connection.cursor()

    str_col = ''
    str_total = ''
    str_left = ''
    str_con = ''
    type_report = ''
    #type_condition = 'GROUP BY cgroup.description, csubhead.description'
    type_condition = 'GROUP BY csubhead.description'


    if report == '1':
        type_report = "ORDER BY ty.id, ch.main, ch.item, ch.cont, ch.sub"
    elif report == '2':
        type_report = "ORDER BY kd.id DESC, ch.main, ch.item, ch.cont, ch.sub"
    elif report == '3':
        type_report = "ORDER BY csubgroup.title DESC, ch.main, ch.item, ch.cont, ch.sub"
    elif report == '4':
        type_report = "ORDER BY kd.id DESC, ch.main, ch.item, ch.cont, ch.sub"
    else:
        print 'do nothing'

    counter = 1
    #for id, d in dept.items():
    for id, d in prod:
        str_col += "SUM(IFNULL(col"+str(counter)+".amount, 0)) AS col"+str(counter)+", "
        str_total += "SUM(IFNULL(col"+str(counter)+".amount, 0)) + "
        str_left += "LEFT OUTER JOIN " \
                    "(SELECT a.year, a.month, SUM(IF(a.code ='C', a.amount * -1, a.amount)) AS amount, a.code, a.chartofaccount_id, a.department_id, d.product_id " \
                    "FROM accountexpensebalance AS a " \
                    "LEFT OUTER JOIN department AS d ON d.id = a.department_id " \
                    "WHERE a.year = "+str(toyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" AND d.product_id = "+str(id)+" " \
                    "GROUP BY a.chartofaccount_id) AS col"+str(counter)+" ON col"+str(counter)+".chartofaccount_id = c.id "
        str_con += "IFNULL(col" + str(counter) + ".amount, 0) + "
        counter += 1

    str_total = "("+str(str_total)+" 0 ) AS col"+str(counter)+", "
    print 'start'
    query = "SELECT ty.id AS typeid, ty.description AS typecode, kd.id AS kindid, kd.description AS kindcode, ch.main, ch.clas, ch.item, ch.cont, ch.sub, ch.title AS chtitle, ch.description AS chdescription, ch.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription, c.accountcode, c.description, "+str(str_col)+" "+str(str_total)+" c.id " \
            "FROM chartofaccount AS c "+str(str_left)+" " \
            "LEFT OUTER JOIN chartofaccount AS ch ON ch.id = c.id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = ch.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = ch.main AND csubgroup.clas = ch.clas AND csubgroup.item = ch.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = ch.main AND csubhead.clas = ch.clas AND csubhead.item = ch.item AND csubhead.cont = ch.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "LEFT OUTER JOIN typeofexpense AS ty ON ty.id = ch.typeofexpense_id " \
            "LEFT OUTER JOIN kindofexpense AS kd ON kd.id = ch.kindofexpense_id " \
            "WHERE c.main = 5 AND ch.accounttype != 'T' AND ("+str(str_con)+" 0) != 0 "+" "+str(type_condition)+" "+str(type_report)+" "
    #print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_cmytd(dfrom, dto):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT cmi.product_code, cmi.product_name, " \
            "SUM(IF(MONTH(cmi.cmdate)=1,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=1,cmi.creditamount,0)) AS mjan, " \
            "SUM(IF(MONTH(cmi.cmdate)=2,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=2,cmi.creditamount,0)) AS mfeb, " \
            "SUM(IF(MONTH(cmi.cmdate)=3,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=3,cmi.creditamount,0)) AS mmar, " \
            "SUM(IF(MONTH(cmi.cmdate)=4,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=4,cmi.creditamount,0)) AS mapr, " \
            "SUM(IF(MONTH(cmi.cmdate)=5,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=5,cmi.creditamount,0)) AS mmay, " \
            "SUM(IF(MONTH(cmi.cmdate)=6,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=6,cmi.creditamount,0)) AS mjun, " \
            "SUM(IF(MONTH(cmi.cmdate)=7,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=7,cmi.creditamount,0)) AS mjul, " \
            "SUM(IF(MONTH(cmi.cmdate)=8,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=8,cmi.creditamount,0)) AS maug, " \
            "SUM(IF(MONTH(cmi.cmdate)=9,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=9,cmi.creditamount,0)) AS msep, " \
            "SUM(IF(MONTH(cmi.cmdate)=10,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=10,cmi.creditamount,0)) AS moct, " \
            "SUM(IF(MONTH(cmi.cmdate)=11,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=11,cmi.creditamount,0)) AS mnov, " \
            "SUM(IF(MONTH(cmi.cmdate)=12,cmi.debitamount,0)) - SUM(IF(MONTH(cmi.cmdate)=12,cmi.creditamount,0)) AS mdec, " \
            "(SUM(cmi.debitamount) - SUM(cmi.creditamount)) AS mtotal " \
            "FROM cmitem AS cmi " \
            "LEFT OUTER JOIN cmmain AS cmm ON cmm.cmnum = cmi.cmnum " \
            "WHERE cmm.isdeleted = 0 AND cmm.status <> 'C' AND (cmi.cmdate >= '"+str(dfrom)+ "' AND cmi.cmdate <= '"+str(dto)+"') " \
            "GROUP BY cmi.product_code, cmi.product_name " \
            "ORDER BY cmi.product_code, cmi.product_name, MONTH(cmi.cmdate) "

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def query_cmdiscountreturn(dfrom, dto, dmain, dclas1, dclas2):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT IF(CONCAT(coa.main,coa.clas)="+str(dmain)+''+str(dclas1)+",'CIRCULATION RETURNS'," \
            "IF(CONCAT(coa.main,coa.clas)="+str(dmain)+''+str(dclas2)+",'ADVERTISING DISCOUNTS','')) AS mainclassdescription, coa.title, p.description AS pdescription, " \
            "SUM(IF(sl.balancecode='D',sl.amount,-1*sl.amount)) AS amount_subtotal " \
            "FROM subledger AS sl " \
            "LEFT OUTER JOIN chartofaccount AS coa ON coa.id = sl.chartofaccount_id " \
            "LEFT OUTER JOIN product AS p ON p.id = coa.product_id " \
            "WHERE (sl.document_date >= '"+str(dfrom)+"' AND sl.document_date <= '"+str(dto)+"') " \
            "AND (coa.main = "+str(dmain)+" AND (coa.clas="+str(dclas1)+" OR coa.clas="+str(dclas2)+")) " \
            "GROUP BY mainclassdescription, coa.main, coa.clas, coa.item, coa.cont " \
            "ORDER BY mainclassdescription ASC, coa.main DESC, coa.clas DESC, coa.item ASC, coa.cont ASC;"

    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def query_cmotherincomeins(dfrom, dto, daccount):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT coa.accountcode, coa.title, sl.document_date, sl.document_type, sl.document_num, sl.particulars, " \
            "IF(sl.balancecode='D',sl.amount,-1*sl.amount) AS amount " \
            "FROM subledger AS sl " \
            "LEFT OUTER JOIN chartofaccount AS coa ON coa.id = sl.chartofaccount_id " \
            "WHERE coa.accountcode = "+str(daccount)+" AND (sl.document_date >= '"+str(dfrom)+"' AND sl.document_date <= '"+str(dto)+"') " \
            "ORDER BY coa.accountcode, sl.document_date, sl.document_type, sl.document_num"


    # to determine the query statement, copy in dos prompt (using mark and copy) and execute in sqlyog
    # print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

