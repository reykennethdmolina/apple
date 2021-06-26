from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from chartofaccount.models import Chartofaccount
from subledger.models import Subledger
from subledgersummary.models import Subledgersummary
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from companyparameter.models import Companyparameter
from chartofaccount.models import Chartofaccount
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.http import JsonResponse
from django.db import connection
from collections import namedtuple
import datetime
import pandas as pd
from datetime import timedelta
import reportlab
from reportlab.lib.pagesizes import legal, landscape
from reportlab.lib.units import inch
import io
from xlsxwriter.workbook import Workbook
from reportlab.pdfgen import canvas
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'generalledgerbook/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        months = ([12, '***** Year End *****'], [1, 'January'], [2, 'February'], [3, 'March'], [4, 'April'], [5, 'May'], [6 ,'June'], \
                  [7, 'July'], [8, 'August'], [9, 'September'], [10, 'October'], [11, 'November'], [12, 'December'])

        context['months'] = months
        today = datetime.datetime.now()
        context['this_month'] = today.month
        context['this_year'] = today.year

        return context

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        report = request.GET['report']
        type = request.GET['type']
        year = request.GET['year']
        month = request.GET['month']
        title = "Supplier Master List"

        prevdate = datetime.date(int(year), int(month), 10) - timedelta(days=15)
        prevyear = prevdate.year
        prevmonth = prevdate.month

        # RETAINED EARNINGS
        retained_earnings = Companyparameter.objects.first().coa_retainedearnings_id
        current_earnings = Companyparameter.objects.first().coa_currentearnings_id

        if report == 'TB':
            title = "Trial Balance"
            result = query_trial_balance(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth)
            print "trial balance"
        elif report == 'BS':
            title = "Balance Sheet"
            result = query_balance_sheet(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth)
            current_month = datetime.date(int(year), int(month), 10).strftime("%B")
            prev_month = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
            print "balance sheet"
        elif report == 'IS':
            title = "Income Statement"
            current_month = datetime.date(int(year), int(month), 10).strftime("%B")
            prev_month = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
            result = query_income_statement(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth)
            print "income statement"
        elif report == 'YETB':
            title = "Year End Trial Balance"
            #current_month = datetime.date(int(year), int(month), 10).strftime("%B")
            #prev_month = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
            result = Chartofaccount.objects.filter(accounttype='P').order_by('accountcode')
            print "year end trial balance"
        else:
            print "no pdf"

        month_text = datetime.date(int(year), int(month), 10).strftime("%B")
        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "month": month_text,
            "year": year,
            "username": request.user,
        }

        if report == 'TB':
            datalist = {}
            # Iterate over the data and write it out row by row.
            counter = 0
            total_beg_debit = 0
            total_beg_credit = 0
            total_mon_debit = 0
            total_mon_credit = 0
            total_end_debit = 0
            total_end_credit = 0
            subtotal_bal_debit = 0
            subtotal_bal_credit = 0
            subtotal_inc_debit = 0
            subtotal_inc_credit = 0
            total_inc_debit = 0
            total_inc_credit = 0
            total_bal_debit = 0
            total_bal_credit = 0
            current_inc_debit = 0
            current_inc_credit = 0
            current_bal_debit = 0
            current_bal_credit = 0

            for data in result:

                if data.chartmain <= 3:
                    if data.summary_end_code == 'D':
                        tbb_debit = float(format(data.summary_end_amount, '.2f'))
                        tbb_credit = float(format(0.00, '.2f'))
                        total_beg_debit += float(format(data.summary_end_amount, '.2f'))
                    else:
                        tbb_debit = float(format(0.00, '.2f'))
                        tbb_credit = float(format(data.summary_end_amount, '.2f'))
                        total_beg_credit += float(format(data.summary_end_amount, '.2f'))
                else:
                    if data.summary_end_code == 'D':
                        tbb_debit = float(format(data.summary_year_to_date_amount, '.2f'))
                        tbb_credit = float(format(0.00, '.2f'))
                        total_beg_debit += float(format(data.summary_year_to_date_amount, '.2f'))
                    else:
                        tbb_debit = float(format(0.00, '.2f'))
                        tbb_credit = float(format(data.summary_year_to_date_amount, '.2f'))
                        total_beg_credit += float(format(data.summary_year_to_date_amount, '.2f'))

                if data.trans_mon_code == 'D':
                    tm_debit = float(format(data.trans_mon_amount, '.2f'))
                    tm_credit = float(format(0.00, '.2f'))
                    total_mon_debit += float(format(data.trans_mon_amount, '.2f'))
                else:
                    tm_debit = float(format(0.00, '.2f'))
                    tm_credit = float(format(data.trans_mon_amount, '.2f'))
                    total_mon_credit += float(format(data.trans_mon_amount, '.2f'))

                if data.chartmain <= 3:
                    if data.end_code == 'D':
                        tbe_debit = float(format(data.end_amount, '.2f'))
                        tbe_credit = float(format(0.00, '.2f'))
                        in_debit = float(format(0.00, '.2f'))
                        in_credit = float(format(0.00, '.2f'))
                        is_debit = float(format(data.end_amount, '.2f'))
                        is_credit = float(format(0.00, '.2f'))
                        total_end_debit += float(format(data.end_amount, '.2f'))
                        subtotal_bal_debit += float(format(data.end_amount, '.2f'))
                    else:
                        tbe_debit = float(format(0.00, '.2f'))
                        tbe_credit = float(format(data.end_amount, '.2f'))
                        in_debit = float(format(0.00, '.2f'))
                        in_credit = float(format(0.00, '.2f'))
                        is_debit = float(format(0.00, '.2f'))
                        is_credit = float(format(data.end_amount, '.2f'))
                        total_end_credit += float(format(data.end_amount, '.2f'))
                        subtotal_bal_credit += float(format(data.end_amount, '.2f'))
                else:
                    if data.year_to_date_code == 'D':
                        tbe_debit = float(format(data.year_to_date_amount, '.2f'))
                        tbe_credit = float(format(0.00, '.2f'))
                        in_debit = float(format(data.year_to_date_amount, '.2f'))
                        in_credit = float(format(0.00, '.2f'))
                        is_debit = float(format(0.00, '.2f'))
                        is_credit = float(format(0.00, '.2f'))
                        total_end_debit += float(format(data.year_to_date_amount, '.2f'))
                        subtotal_inc_debit += float(format(data.year_to_date_amount, '.2f'))
                    else:
                        tbe_debit = float(format(0.00, '.2f'))
                        tbe_credit = float(format(data.year_to_date_amount, '.2f'))
                        in_debit = float(format(0.00, '.2f'))
                        in_credit = float(format(data.year_to_date_amount, '.2f'))
                        is_debit = float(format(0.00, '.2f'))
                        is_credit = float(format(0.00, '.2f'))
                        total_end_credit += float(format(data.year_to_date_amount, '.2f'))
                        subtotal_inc_credit += float(format(data.year_to_date_amount, '.2f'))

                datalist[counter] = dict(accountcode=data.accountcode, description=data.description, tbb_debit=tbb_debit, tbb_credit=tbb_credit,
                                         tm_debit=tm_debit, tm_credit=tm_credit, tbe_debit=tbe_debit, tbe_credit=tbe_credit,
                                         in_debit=in_debit, in_credit=in_credit, is_debit=is_debit, is_credit=is_credit)
                counter += 1

            context["subtotal"] = dict(subtotal_inc_debit=subtotal_inc_debit, subtotal_inc_credit=subtotal_inc_credit,
                                       subtotal_bal_debit=subtotal_bal_debit, subtotal_bal_credit=subtotal_bal_credit)

            if subtotal_inc_debit >= subtotal_inc_credit:
                current_inc_credit = float(format(subtotal_inc_debit, '.2f')) - float(format(subtotal_inc_credit, '.2f'))
                current_is_debit = float(format(0.00, '.2f'))
                current_is_credit = float(format(current_inc_credit, '.2f'))
            else:
                current_inc_debit = float(format(subtotal_inc_credit, '.2f')) - float(format(subtotal_inc_debit, '.2f'))
                current_is_debit = float(format(current_inc_debit, '.2f'))
                current_is_credit = float(format(0.00, '.2f'))

            if subtotal_bal_debit >= subtotal_bal_credit:
                current_bal_credit = float(format(subtotal_bal_debit, '.2f')) - float(format(subtotal_bal_credit, '.2f'))
                current_bs_debit = float(format(0.00, '.2f'))
                current_bs_credit = float(format(current_bal_credit, '.2f'))
            else:
                current_bal_debit = float(format(subtotal_bal_credit, '.2f')) - float(format(subtotal_bal_debit, '.2f'))
                current_bs_debit = float(format(current_bal_debit, '.2f'))
                current_bs_credit = float(format(0.00, '.2f'))

            total_inc_debit = float(format(subtotal_inc_debit, '.2f')) + float(format(current_inc_debit, '.2f'))
            total_inc_credit = float(format(subtotal_inc_credit, '.2f')) + float(format(current_inc_credit, '.2f'))
            total_bal_debit = float(format(subtotal_bal_debit, '.2f')) + float(format(current_bal_debit, '.2f'))
            total_bal_credit = float(format(subtotal_bal_credit, '.2f')) + float(format(current_bal_credit, '.2f'))

            context["curear"] = dict(current_is_debit=current_is_debit, current_is_credit=current_is_credit,
                                      current_bs_debit=current_bs_debit, current_bs_credit=current_bs_credit)

            context["total"] = dict(total_beg_debit=total_beg_debit,total_beg_credit=total_beg_credit,
                                    total_mon_debit=total_mon_debit, total_mon_credit=total_mon_credit,
                                    total_end_debit=total_end_debit, total_end_credit=total_end_credit,
                                    total_inc_debit=total_inc_debit, total_inc_credit=total_inc_credit,
                                    total_bal_debit=total_bal_debit, total_bal_credit=total_bal_credit)

            context["result"] = datalist
            return Render.render('generalledgerbook/tb_pdf.html', context)
        elif report == 'BS':
            datalist = {}
            counter = 0
            current_percentage = 0
            prev_percentage = 0
            variance_percentage = 0
            variance = 0
            gtotal_current = 0
            gtotal_previous = 0
            gtotal_variance = 0
            gtotal_previous_percentage = 0
            gtotal_var = 0
            prev_liab_equity_percentage = 0

            dataset = pd.DataFrame(result)
            curdata = dataset.groupby('this_code')['current_amount'].sum()
            prevdata = dataset.groupby('this_code')['prev_amount'].sum()
            cur_liab_equity = curdata['ASSETS']
            prev_liab_equity = prevdata['ASSETS']
            for this, thisgroup in dataset.fillna('NaN').sort_values(by=['this_code'], ascending=False,na_position='last').groupby(['this_code', 'this_desc']):
                if this[0] != 'NaN':
                    datalist[counter] = dict(title='yes',main='yesheader',col1=this[1].upper())
                gtotal_current = thisgroup['current_amount_abs'].sum()
                gtotal_previous = thisgroup['prev_amount_abs'].sum()
                counter += 1
                for group, maingroup in thisgroup.fillna('NaN').sort_values(by=['group_code'], ascending=True).groupby(['group_code', 'group_desc']):
                    if group[0] != 'NaN':
                        datalist[counter] = dict(title='yes',main='yes',col1=group[1])
                        counter += 1
                    total_current = 0
                    total_previous = 0
                    total_variance = 0
                    for main, subgroup in maingroup.fillna('NaN').sort_values(by=['subgroup_code'],ascending=True).groupby(['maingroup_code', 'maingroup_desc']):
                        datalist[counter] = dict(title='yes',main='no',col1=main[1].upper())
                        counter += 1
                        subtotal_current = 0
                        subtotal_previous = 0
                        subtotal_variance = 0
                        subtotal_cur = subgroup.groupby('maingroup_code')['current_amount_abs'].sum()
                        subtotal_prev = subgroup.groupby('maingroup_code')['prev_amount_abs'].sum()
                        current_percentage = 0
                        previous_percentage = 0
                        subtotal_current_percentage = 0
                        subtotal_previous_percentage = 0
                        for data, sub in subgroup.iterrows():
                            if float(subtotal_cur) > 0:
                                current_percentage = float(format(sub['current_amount_abs'], '.2f')) / float(
                                    subtotal_cur) * 100

                            if float(subtotal_prev) > 0:
                                previous_percentage = float(format(sub['prev_amount_abs'], '.2f')) / float(
                                    subtotal_prev) * 100

                            variance = float(format(sub['current_amount_abs'], '.2f')) - float(
                                format(sub['prev_amount_abs'], '.2f'))

                            if float(variance) != 0:
                                if sub['prev_amount_abs'] != 0:
                                    variance_percentage = float(variance) / float(
                                        format(sub['prev_amount_abs'], '.2f')) * 100
                                else:
                                    variance_percentage = 0
                            else:
                                variance_percentage = 0

                            datalist[counter] = dict(title='no', col1=sub['subgroup_code'],col2=sub['subgroup_desc'],
                                                     col4=float(format(sub['current_amount_abs'], '.2f')),
                                                     col5=float(format(sub['prev_amount_abs'], '.2f')),
                                                     col6=float(format(current_percentage, '.2f')),
                                                     col7=float(format(previous_percentage, '.2f')),
                                                     col8=float(format(variance, '.2f')),
                                                     col9=float(format(variance_percentage, '.2f')))

                            subtotal_current += float(format(sub['current_amount_abs'], '.2f'))
                            subtotal_previous += float(format(sub['prev_amount_abs'], '.2f'))
                            subtotal_variance += float(format(variance, '.2f'))
                            counter += 1

                        total_current += subtotal_current
                        total_previous += subtotal_previous
                        total_variance += subtotal_variance

                        if float(total_current) != 0:
                            subtotal_current_percentage = float(format(subtotal_current, '.2f')) / float(
                                format(total_current, '.2f')) * 100
                        else:
                            total_current = 0

                        if float(total_previous) != 0:
                            subtotal_previous_percentage = float(format(subtotal_previous, '.2f')) / float(
                                format(total_previous, '.2f')) * 100
                        else:
                            total_previous = 0

                        if float(subtotal_previous) != 0:
                            subtotal_var = float(format(subtotal_variance, '.2f')) / float(
                                format(subtotal_previous, '.2f')) * 100
                        else:
                            subtotal_var = 0

                        datalist[counter] = dict(title='yes',main='nosub',
                                                 col1='TOTAL ' + str(main[1].upper()),
                                                 col3='',
                                                 col4=float(format(subtotal_current, '.2f')),
                                                 col5=float(format(subtotal_previous, '.2f')),
                                                 col6=float(format(subtotal_current_percentage, '.2f')),
                                                 col7=float(format(subtotal_previous_percentage, '.2f')),
                                                 col8=float(format(subtotal_current, '.2f')) - float(format(subtotal_previous, '.2f')),
                                                 col9=float(format(subtotal_var, '.2f')))
                        counter += 1

                    if group[0] != 'NaN':

                        if float(gtotal_current) != 0:
                            total_current_percentage = float(format(total_current, '.2f')) / float(
                                format(gtotal_current, '.2f')) * 100
                        else:
                            total_current_percentage = 0

                        if float(gtotal_previous) != 0:
                            total_previous_percentage = float(format(total_previous, '.2f')) / float(
                                format(gtotal_previous, '.2f')) * 100
                        else:
                            total_previous_percentage = 0

                        if float(total_previous) != 0:
                            total_var = float(format(total_variance, '.2f')) / float(
                                format(total_previous, '.2f')) * 100
                        else:
                            total_var = 0

                        datalist[counter] = dict(title='yes',main='nototal',
                                                 col1='TOTAL ' + str(group[1]).upper(),
                                                 col2='',
                                                 col4=float(format(total_current, '.2f')),
                                                 col5=float(format(total_previous, '.2f')),
                                                 col6=float(format(total_current_percentage, '.2f')),
                                                 col7=float(format(total_previous_percentage, '.2f')),
                                                 col8=float(format(total_current, '.2f')) - float(format(total_previous, '.2f')),
                                                 col9=float(format(total_var, '.2f')))
                        counter += 1

                if this[0] != 'NaN':

                    if float(gtotal_current) != 0:
                        gtotal_current_percentage = float(format(gtotal_current, '.2f')) / float(format(gtotal_current, '.2f')) * 100
                    if float(gtotal_previous) != 0:
                        gtotal_previous_percentage = float(format(gtotal_previous, '.2f')) / float(format(gtotal_previous, '.2f')) * 100
                        gtotal_variance = float(format(gtotal_current, '.2f')) - float(format(gtotal_previous, '.2f'))
                    if float(gtotal_previous) != 0:
                        gtotal_var = float(format(gtotal_variance, '.2f')) / float(format(gtotal_previous, '.2f')) * 100

                    datalist[counter] = dict(title='yes',main='nogtotal',
                                             col1='TOTAL ' + 'TOTAL ' + str(this[1]).upper(),
                                             col2='',
                                             col4=float(format(gtotal_current, '.2f')),
                                             col5=float(format(gtotal_previous, '.2f')),
                                             col6=float(format(gtotal_current_percentage, '.2f')),
                                             col7=float(format(gtotal_previous_percentage, '.2f')),
                                             col8=float(format(gtotal_variance, '.2f')),
                                             col9=float(format(gtotal_var, '.2f')))
                    counter += 1


            if float(cur_liab_equity) != 0:
                cur_liab_equity_percentage = float(format(cur_liab_equity, '.2f')) / float(
                    format(cur_liab_equity, '.2f')) * 100
            else:
                cur_liab_equity_percentage = 0

            if float(prev_liab_equity) != 0:
                prev_liab_equity_percentage = float(format(prev_liab_equity, '.2f')) / float(
                    format(prev_liab_equity, '.2f')) * 100
            else:
                prev_liab_equity = 0

            liab_equity_variance = float(format(cur_liab_equity, '.2f')) - float(format(prev_liab_equity, '.2f'))

            if float(prev_liab_equity) != 0:
                liab_equity_var = float(format(liab_equity_variance, '.2f')) / float(
                    format(prev_liab_equity, '.2f')) * 100
            else:
                liab_equity_var = 0



            datalist[counter] = dict(title='yes',main='nogtotal',
                                     col1='TOTAL LIABILITIES & CAPITAL',
                                     col2='',
                                     col4=float(format(cur_liab_equity, '.2f')),
                                     col5=float(format(prev_liab_equity, '.2f')),
                                     col6=float(format(cur_liab_equity_percentage, '.2f')),
                                     col7=float(format(prev_liab_equity_percentage, '.2f')),
                                     col8=float(format(liab_equity_variance, '.2f')),
                                     col9=float(format(liab_equity_var, '.2f')))

            counter += 1

            print datalist
            context["result"] = datalist
            context['month'] = datetime.date(int(year), int(month), 10).strftime("%B")
            context['prev_month'] = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
            context['prev_year'] = prevdate.year
            return Render.render('generalledgerbook/bs_pdf.html', context)
        elif report == 'IS':
            datalist = {}
            counter = 0
            col = 0
            cur_netsales = 0
            prev_netsales = 0
            current_percentage = 0
            prev_percentage = 0
            variance_percentage = 0
            variance = 0
            noi_cur = 0
            noi_prev = 0
            noi_todate = 0
            incometax_cur = 0
            incometax_prev = 0
            incometax_todate = 0

            dataset = pd.DataFrame(result)
            dcur_netsales = dataset.groupby('group_code')['current_amount'].sum()
            dprev_netsales = dataset.groupby('group_code')['prev_amount'].sum()
            dtodate_netsales = dataset.groupby('group_code')['todate_amount'].sum()
            cur_netsales = dcur_netsales['GS']  # dataset['current_amount'][dataset['group_code'] == 'GS'].sum()
            prev_netsales = dprev_netsales['GS']  # dataset['prev_amount'][dataset['group_code'] == 'GS'].sum()
            todate_netsales = dtodate_netsales['GS']  # dataset['todate_amount'][dataset['group_code'] == 'GS'].sum()
            for group, maintitle in dataset.fillna('NaN').groupby(['group_code', 'group_desc', 'group_title']):
                if group[0] != 'NaN' and group[0] != 'PFIT' and group[0] != 'OTHER':
                    datalist[counter] = dict(title='yes', main='yesheader', col1=group[1].upper())
                    counter += 1
                total_current = 0
                total_previous = 0
                total_todate = 0
                total_variance = 0
                total_current_percentage = 0
                total_previous_percentage = 0
                for title, maingroup in maintitle.fillna('NaN').sort_values(by=['maingroup_code'],ascending=True).groupby(['group_code', 'group_desc', 'group_title', 'maingroup_title']):
                    net_total_current = 0
                    net_total_previous = 0
                    net_total_todate = 0
                    net_total_variance = 0
                    net_total_current_percentage = 0
                    net_total_previous_percentage = 0
                    for main, subgroup in maingroup.fillna('NaN').sort_values(by=['subgroup_code'],ascending=True).groupby(['maingroup_code', 'maingroup_desc']):
                        datalist[counter] = dict(title='yes', main='no', col1=main[1])
                        counter += 1
                        subtotal_current = 0
                        subtotal_previous = 0
                        subtotal_todate = 0
                        subtotal_variance = 0
                        subtotal_var = 0
                        subtotal_current_percentage = 0
                        subtotal_previous_percentage = 0
                        for data, sub in subgroup.iterrows():

                            if float(cur_netsales) > 0:
                                current_percentage = float(format(sub['current_amount'], '.2f')) / float(
                                    format(cur_netsales, '.2f')) * 100

                            if float(prev_netsales) > 0:
                                previous_percentage = float(format(sub['prev_amount'], '.2f')) / float(
                                    format(prev_netsales, '.2f')) * 100

                            variance = float(format(sub['current_amount'], '.2f')) - float(
                                format(sub['prev_amount'], '.2f'))

                            if float(variance) != 0:
                                if float(format(sub['prev_amount'], '.2f')) == 0:
                                    if float(variance) > 0:
                                        variance_percentage = 100
                                    else:
                                        variance_percentage = 100 * -1
                                else:
                                    variance_percentage = float(variance) / float(
                                        format(sub['prev_amount'], '.2f')) * 100
                            else:
                                variance_percentage = 0

                            datalist[counter] = dict(title='no', col1=sub['subgroup_code'], col2=sub['subgroup_desc'],
                                                     col4=float(format(sub['current_amount'], '.2f')),
                                                     col5=float(format(sub['prev_amount'], '.2f')),
                                                     col6=float(format(sub['todate_amount'], '.2f')),
                                                     col7=float(format(current_percentage, '.2f')),
                                                     col8=float(format(previous_percentage, '.2f')),
                                                     col9=float(format(variance, '.2f')),
                                                     col10= float(format(variance_percentage, '.2f')))

                            subtotal_current += float(format(sub['current_amount'], '.2f'))
                            subtotal_previous += float(format(sub['prev_amount'], '.2f'))
                            subtotal_todate += float(format(sub['todate_amount'], '.2f'))
                            subtotal_variance += float(format(variance, '.2f'))
                            counter += 1

                        if float(cur_netsales) > 0:
                            subtotal_current_percentage = float(format(subtotal_current, '.2f')) / float(
                                format(cur_netsales, '.2f')) * 100
                        if float(prev_netsales) > 0:
                            subtotal_previous_percentage = float(format(subtotal_previous, '.2f')) / float(
                                format(prev_netsales, '.2f')) * 100
                        if subtotal_previous > 0:
                            subtotal_var = float(format(subtotal_variance, '.2f')) / float(
                                format(subtotal_previous, '.2f')) * 100

                        datalist[counter] = dict(title='yes', main='nosub',
                                                 col1='TOTAL ' + str(main[1].upper()),
                                                 col3='',
                                                 col4=float(format(subtotal_current, '.2f')),
                                                 col5=float(format(subtotal_previous, '.2f')),
                                                 col6=float(format(subtotal_todate, '.2f')),
                                                 col7=float(format(subtotal_current_percentage, '.2f')),
                                                 col8=float(format(subtotal_previous_percentage, '.2f')),
                                                 col9=float(format(subtotal_current, '.2f')) - float(format(subtotal_previous, '.2f')),
                                                 col10=float(format(subtotal_var, '.2f')))


                        total_current += float(subtotal_current)
                        total_previous += float(subtotal_previous)
                        total_todate += float(subtotal_todate)
                        net_total_current += float(subtotal_current)
                        net_total_previous += float(subtotal_previous)
                        net_total_todate += float(subtotal_todate)
                        counter += 1

                    if title[3] != 'NaN':
                        if title[3] == 'GROSS INCOME FROM SALES':


                            gross_current = float(format(cur_netsales, '.2f')) - float(format(net_total_current, '.2f'))
                            gross_previous = float(format(prev_netsales, '.2f')) - float(format(net_total_previous, '.2f'))
                            gross_todate = float(format(todate_netsales, '.2f')) - float(format(net_total_todate, '.2f'))

                            gross_total_current_percentage = 0
                            gross_total_previous_percentage = 0
                            if float(cur_netsales) > 0:
                                gross_total_current_percentage = float(format(gross_current, '.2f')) / float(format(cur_netsales, '.2f')) * 100
                            if float(prev_netsales) > 0:
                                gross_total_previous_percentage = float(format(gross_previous, '.2f')) / float(format(prev_netsales, '.2f')) * 100
                            gross_total_variance = float(format(gross_current, '.2f')) - float(format(gross_previous, '.2f'))
                            gross_total_var = float(format(gross_total_variance, '.2f')) / float(format(gross_previous, '.2f')) * 100

                            datalist[counter] = dict(title='yes', main='nototal',
                                                     col1=str(title[3]).upper(),
                                                     col2='',
                                                     col4=float(format(gross_current, '.2f')),
                                                     col5=float(format(gross_previous, '.2f')),
                                                     col6=float(format(gross_todate, '.2f')),
                                                     col7=float(format(gross_total_current_percentage, '.2f')),
                                                     col8=float(format(gross_total_previous_percentage, '.2f')),
                                                     col9=float(format(gross_current, '.2f')) - float(format(gross_previous, '.2f')),
                                                     col10=float(format(gross_total_var, '.2f')))

                        elif title[3] == 'NET INCOME BEFORE TAX':
                            print 'x'


                            incometax_cur = float(format(noi_cur, '.2f')) + float(format(total_current, '.2f'));
                            incometax_prev = float(format(noi_prev, '.2f')) + float(format(total_previous, '.2f'));
                            incometax_todate = float(format(noi_todate, '.2f')) + float(format(total_todate, '.2f'));


                            incometax_total_current_percentage = 0
                            incometax_total_previous_percentage = 0
                            if float(cur_netsales) > 0:
                                incometax_total_current_percentage = float(format(incometax_cur, '.2f')) / float(format(cur_netsales, '.2f')) * 100
                            if float(prev_netsales) > 0:
                                incometax_total_previous_percentage = float(format(incometax_prev, '.2f')) / float(format(prev_netsales, '.2f')) * 100
                            incometax_total_variance = float(format(incometax_cur, '.2f')) - float(format(incometax_prev, '.2f'))
                            incometax_total_var = float(format(incometax_total_variance, '.2f')) / float(format(incometax_prev, '.2f')) * 100

                            datalist[counter] = dict(title='yes', main='nototal',
                                                     col1=str(title[3]).upper(),
                                                     col2='',
                                                     col4=float(format(incometax_cur, '.2f')),
                                                     col5=float(format(incometax_prev, '.2f')),
                                                     col6=float(format(incometax_todate, '.2f')),
                                                     col7=float(format(incometax_total_current_percentage, '.2f')),
                                                     col8=float(format(incometax_total_previous_percentage, '.2f')),
                                                     col9=float(format(incometax_cur, '.2f')) - float(format(incometax_prev, '.2f')),
                                                     col10=float(format(incometax_total_var, '.2f')))

                        elif title[3] == 'NET INCOME (LOSS) AFTER TAX':
                            print 'x'

                            incometaxafter_cur = float(format(incometax_cur, '.2f')) + float(format(total_current, '.2f'));
                            incometaxafter_prev = float(format(incometax_prev, '.2f')) + float(format(total_previous, '.2f'));
                            incometaxafter_todate = float(format(incometax_todate, '.2f')) + float(format(total_todate, '.2f'));

                            incometaxafter_total_current_percentage = 0
                            if float(cur_netsales) > 0:
                                incometaxafter_total_current_percentage = float(format(incometaxafter_cur, '.2f')) / float(format(cur_netsales, '.2f')) * 100
                            incometaxafter_total_previous_percentage = 0
                            if float(prev_netsales) > 0:
                                incometaxafter_total_previous_percentage = float(format(incometaxafter_prev, '.2f')) / float(format(prev_netsales, '.2f')) * 100
                            incometaxafter_total_variance = float(format(incometaxafter_cur, '.2f')) - float(format(incometaxafter_prev, '.2f'))
                            incometaxafter_total_var = float(format(incometaxafter_total_variance, '.2f')) / float(format(incometaxafter_prev, '.2f')) * 100

                            datalist[counter] = dict(title='yes', main='nototal',
                                                     col1=str(title[3]).upper(),
                                                     col2='',
                                                     col4=float(format(incometaxafter_cur, '.2f')),
                                                     col5=float(format(incometaxafter_prev, '.2f')),
                                                     col6=float(format(incometaxafter_todate, '.2f')),
                                                     col7=float(format(incometaxafter_total_current_percentage, '.2f')),
                                                     col8=float(format(incometaxafter_total_previous_percentage, '.2f')),
                                                     col9=float(format(incometaxafter_cur, '.2f')) - float(format(incometaxafter_prev, '.2f')),
                                                     col10=float(format(incometaxafter_total_var, '.2f')))


                        else:
                            print 'x'

                            if float(cur_netsales) > 0:
                                net_total_current_percentage = float(format(net_total_current, '.2f')) / float(
                                    format(cur_netsales, '.2f')) * 100
                            if float(prev_netsales) > 0:
                                net_total_previous_percentage = float(format(net_total_previous, '.2f')) / float(
                                    format(prev_netsales, '.2f')) * 100
                            net_total_variance = float(format(net_total_current, '.2f')) - float(
                                format(net_total_previous, '.2f'))
                            net_total_var = float(format(net_total_variance, '.2f')) / float(
                                format(net_total_previous, '.2f')) * 100

                            datalist[counter] = dict(title='yes', main='nototal',
                                                     col1=str(title[3]).upper(),
                                                     col2='',
                                                     col4=float(format(net_total_current, '.2f')),
                                                     col5=float(format(net_total_previous, '.2f')),
                                                     col6=float(format(net_total_todate, '.2f')),
                                                     col7=float(format(net_total_current_percentage, '.2f')),
                                                     col8=float(format(net_total_previous_percentage, '.2f')),
                                                     col9=float(format(net_total_current, '.2f')) - float(format(net_total_previous, '.2f')),
                                                     col10=float(format(net_total_var, '.2f')))

                        counter += 1

                if group[0] != 'NaN' and group[0] != 'PFIT' and group[0] != 'OTHER':
                    if group[2] == "NET OPERATING INCOME (LOSS)":

                        noi_cur = float(format(gross_current, '.2f')) - float(format(total_current, '.2f'));
                        noi_prev = float(format(gross_previous, '.2f')) - float(format(total_previous, '.2f'));
                        noi_todate = float(format(gross_todate, '.2f')) - float(format(total_todate, '.2f'));

                        noi_total_current_percentage = 0
                        noi_total_previous_percentage = 0
                        if float(cur_netsales) > 0:
                            noi_total_current_percentage = float(format(noi_cur, '.2f')) / float(
                                format(cur_netsales, '.2f')) * 100
                        if float(prev_netsales) > 0:
                            noi_total_previous_percentage = float(format(noi_prev, '.2f')) / float(
                                format(prev_netsales, '.2f')) * 100
                        noi_total_variance = float(format(noi_cur, '.2f')) - float(format(noi_prev, '.2f'))
                        noi_total_var = float(format(noi_total_variance, '.2f')) / float(
                            format(noi_prev, '.2f')) * 100

                        datalist[counter] = dict(title='yes', main='nototal',
                                                 col1=str(group[2]),
                                                 col2='',
                                                 col4=float(format(noi_cur, '.2f')),
                                                 col5=float(format(noi_prev, '.2f')),
                                                 col6=float(format(noi_todate, '.2f')),
                                                 col7=float(format(noi_total_current_percentage, '.2f')),
                                                 col8=float(format(noi_total_previous_percentage, '.2f')),
                                                 col9=float(format(noi_cur, '.2f')) - float(format(noi_prev, '.2f')),
                                                 col10=float(format(noi_total_var, '.2f')))
                        counter += 1
                    else:

                        if float(cur_netsales) > 0:
                            total_current_percentage = float(format(total_current, '.2f')) / float(
                                format(cur_netsales, '.2f')) * 100
                        if float(prev_netsales) > 0:
                            total_previous_percentage = float(format(total_previous, '.2f')) / float(
                                format(prev_netsales, '.2f')) * 100
                        total_variance = float(format(total_current, '.2f')) - float(format(total_previous, '.2f'))
                        total_var = float(format(total_variance, '.2f')) / float(
                            format(total_previous, '.2f')) * 100


                        datalist[counter] = dict(title='yes', main='nototal',
                                                 col1='TOTAL' + str(group[2]),
                                                 col2='',
                                                 col4=float(format(total_current, '.2f')),
                                                 col5=float(format(total_previous, '.2f')),
                                                 col6=float(format(total_todate, '.2f')),
                                                 col7=float(format(total_current_percentage, '.2f')),
                                                 col8=float(format(total_previous_percentage, '.2f')),
                                                 col9=float(format(total_current, '.2f')) - float(format(total_previous, '.2f')),
                                                 col10=float(format(total_var, '.2f')))
                        counter += 1

            counter += 1
            print datalist
            context["result"] = datalist
            context['month'] = datetime.date(int(year), int(month), 10).strftime("%B")
            context['prev_month'] = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
            context['prev_year'] = prevdate.year
            return Render.render('generalledgerbook/is_pdf.html', context)
        # elif report == 'YETB':
        #     return Render.render('generalledgerbook/report_3.html', context)
        else:
            return Render.render('generalledgerbook/report_1.html', context)

def tbpdf(request):
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename = "somefilename.pdf"'

    # Create the PDF object, using the response object as its "file."
    p = canvas.Canvas(response)
    p.setPageSize(landscape(legal))

    p.line(10, 100, 1 * inch, 0)

    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.drawString(1, 1, "Hello world.")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    return response

@csrf_exempt
def excel(request):
    # request variables
    report = request.GET["report"]
    type = request.GET["type"]
    year = request.GET["year"]
    month = request.GET["month"]

    prevdate = datetime.date(int(year), int(month), 10) - timedelta(days=15)
    prevyear = prevdate.year
    prevmonth = prevdate.month

    # RETAINED EARNINGS
    retained_earnings = Companyparameter.objects.first().coa_retainedearnings_id
    current_earnings = Companyparameter.objects.first().coa_currentearnings_id

    if report == 'TB':
        result = query_trial_balance(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth)
        return excel_trail_balance(request, result, report, type, year, month)
    elif report == 'BS':
        result = query_balance_sheet(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth)
        current_month = datetime.date(int(year), int(month), 10).strftime("%B")
        prev_month = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
        return excel_balance_sheet(request,result, report, type, year, month, current_month, prev_month, year, prevyear)
    elif report == 'IS':
        current_month = datetime.date(int(year), int(month), 10).strftime("%B")
        prev_month = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
        result = query_income_statement(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth)
        return excel_income_statement(request,result, report, type, year, month, current_month, prev_month, year, prevyear)
    elif report == 'YETB':
        result = Chartofaccount.objects.filter(accounttype='P', isdeleted=0).order_by('accountcode')
        return excel_year_end_trial_balance(result)

    else:
        print "no report"

@csrf_exempt
def generate(request):

    report = request.GET["report"]
    type = request.GET["type"]
    year = request.GET["year"]
    month = request.GET["month"]

    prevdate = datetime.date(int(year), int(month), 10) - timedelta(days=15)
    prevyear = prevdate.year
    prevmonth = prevdate.month

    # RETAINED EARNINGS
    retained_earnings = Companyparameter.objects.first().coa_retainedearnings_id
    current_earnings = Companyparameter.objects.first().coa_currentearnings_id

    context = {}

    if report == 'TB':
        print "trial balance"
        context['month'] = datetime.date(int(year), int(month), 10).strftime("%B")
        context['year'] = year
        context['result'] = query_trial_balance(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth)
        viewhtml = render_to_string('generalledgerbook/trial_balance.html', context)
    elif report == 'BS':
        print "balance sheet"
        context['month'] = datetime.date(int(year), int(month), 10).strftime("%B")
        context['prev_month'] = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
        context['current_year'] = year
        context['prev_year'] = prevyear
        result = query_balance_sheet(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth)
        dataset = pd.DataFrame(result)
        curdata = dataset.groupby('this_code')['current_amount'].sum()
        prevdata = dataset.groupby('this_code')['prev_amount'].sum()
        #cur_liab_equity = dataset['current_amount'][dataset['this_code'] != 'ASSETS'].sum()
        #print dataset['current_amount'][dataset['this_code'] != 'ASSETS'].sum()
        cur_liab_equity = curdata['ASSETS']
        prev_liab_equity = prevdata['ASSETS']
        context['cur_liab_equity'] = float(format(cur_liab_equity, '.2f'))
        context['prev_liab_equity'] = float(format(prev_liab_equity, '.2f'))
        context['result'] = result
        viewhtml = render_to_string('generalledgerbook/balance_sheet.html', context)
    elif report == 'IS':
        print "income statement"
        result = query_income_statement(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth)
        dataset = pd.DataFrame(result)
        cur_netsales = dataset.groupby('group_code')['current_amount'].sum()
        prev_netsales = dataset.groupby('group_code')['prev_amount'].sum()
        context['cur_netsales'] = float(format(cur_netsales['GS'], '.2f'))
        context['prev_netsales'] = float(format(prev_netsales['GS'], '.2f'))
        context['month'] = datetime.date(int(year), int(month), 10).strftime("%B")
        context['prev_month'] = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
        context['current_year'] = year
        context['prev_year'] = prevyear
        context['result'] = result
        #test = dataset.groupby(['group_code']).sum().sum(level=['group_code']).unstack('Groups').fillna(0).reset_index()
        #print test
        viewhtml = render_to_string('generalledgerbook/income_statement.html', context)
    elif report == 'YETB':
        title = "Year End Trial Balance"
        # current_month = datetime.date(int(year), int(month), 10).strftime("%B")
        # prev_month = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
        result = Chartofaccount.objects.filter(accounttype='P',isdeleted=0).exclude(main__in=[4,5,6,7,8,9]).order_by('accountcode')

        debit = 0
        credit = 0
        for l in result:
            print l.beginning_amount
            if l.beginning_code == 'D':
                debit += l.beginning_amount
            else:
                credit += l.beginning_amount

        context['debit'] = debit
        context['credit'] = credit
        context['result'] = result
        context['today'] = timezone.now(),

        viewhtml = render_to_string('generalledgerbook/year_end_trail_balance.html', context)
    else:
        print "no report"

    data = {
        'status': 'success',
        'viewhtml': viewhtml,
    }
    return JsonResponse(data)

def query_trial_balance(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth):
    print "trial balance query"
    ''' Create query '''
    cursor = connection.cursor()
    if type == 'P' :
        query = "SELECT  chart.id AS chartid, chart.main AS chartmain, maingroup.code AS maingroup_code, maingroup.description AS maingroup_desc, " \
                 "subgroup.code AS subgroup_code, subgroup.description AS subgroup_desc," \
                 "chart.accountcode, chart.description, chart.balancecode, " \
                 "chart.beginning_amount, chart.beginning_code, IFNULL(chart.end_amount, 0) AS end_amount, " \
                 "chart.end_code, IFNULL(chart.year_to_date_amount, 0) AS year_to_date_amount, chart.year_to_date_code, " \
                 "IF (chart.id = " + str(retained_earnings) + " AND summary.month = 12, IFNULL(chart.beginning_amount, 0) , IFNULL(summary.end_amount, 0)) AS summary_end_amount, " \
                 "IF (chart.id = " + str(retained_earnings) + " AND summary.month = 12, chart.beginning_code , summary.end_code) AS summary_end_code, " \
                 "IF (chart.main >= 4 AND summary.month = 12, IFNULL(chart.beginning_amount, 0), IFNULL(summary.year_to_date_amount, 0)) " \
                 "AS summary_year_to_date_amount, " \
                 "IF (chart.main >= 4 AND summary.month = 12, chart.beginning_code, summary.year_to_date_code) AS summary_year_to_date_code, " \
                 "subled_d.balancecode AS debit_code, IFNULL(subled_d.amount, 0) AS debit_amount, " \
                 "subled_c.balancecode AS credit_code, IFNULL(subled_c.amount, 0) AS credit_amount, " \
                 "IF (IFNULL(subled_d.amount, 0) >= IFNULL(subled_c.amount, 0), 'D', 'C') AS trans_mon_code, " \
                 "ABS(IFNULL(subled_d.amount, 0) - IFNULL(subled_c.amount, 0)) AS trans_mon_amount " \
                 "FROM chartofaccount AS chart " \
                 "LEFT OUTER JOIN (" \
                 "   SELECT summary.chartofaccount_id, " \
                 "   summary.beginning_amount AS summary_beg_amount, summary.beginning_code AS summary_beg_code,	" \
                 "   summary.end_amount, summary.end_code, " \
                 "   summary.year_to_date_amount, summary.year_to_date_code, summary.month " \
                 "   FROM subledgersummary AS summary " \
                 "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' " \
                 ") AS summary ON summary.chartofaccount_id = chart.id " \
                 "LEFT OUTER JOIN ( " \
                 "  SELECT subled.chartofaccount_id, subled.balancecode, SUM(amount) AS amount " \
                 "  FROM subledger AS subled " \
                 "  WHERE YEAR(subled.document_date) = '" + str(year) + "' AND MONTH(subled.document_date) = '" + str(month) + "' " \
                 "  AND subled.balancecode = 'D' " \
                 "  GROUP BY subled.chartofaccount_id, subled.balancecode " \
                 ") AS subled_d ON subled_d.chartofaccount_id = chart.id " \
                 "LEFT OUTER JOIN ( " \
                 "  SELECT subled.chartofaccount_id, subled.balancecode, SUM(amount) AS amount " \
                 "  FROM subledger AS subled " \
                 "  WHERE YEAR(subled.document_date) = '" + str(year) + "' AND MONTH(subled.document_date) = '" + str(month) + "' " \
                 "  AND subled.balancecode = 'C' " \
                 "  GROUP BY subled.chartofaccount_id, subled.balancecode " \
                 ") AS subled_c ON subled_c.chartofaccount_id = chart.id " \
                 "LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                 "LEFT OUTER JOIN chartofaccountmainsubgroup AS mainsubgroup ON mainsubgroup.sub_id = subgroup.id " \
                 "LEFT OUTER JOIN chartofaccountmaingroup AS maingroup ON maingroup.id = mainsubgroup.main_id " \
                 "WHERE chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.id != " + str(current_earnings) + " " \
                 "ORDER BY chart.accountcode ASC"
    else:
        query = "SELECT  chart.id AS chartid, chart.main AS chartmain, maingroup.code AS maingroup_code, maingroup.description AS maingroup_desc, " \
                "subgroup.code AS subgroup_code, subgroup.description AS subgroup_desc," \
                "chart.accountcode, chart.description, chart.balancecode, " \
                "chart.beginning_amount, chart.beginning_code, IFNULL(summary.end_amount, 0) AS end_amount, " \
                "summary.end_code, IFNULL(summary.year_to_date_amount, 0) AS year_to_date_amount, summary.year_to_date_code, " \
                "IF (chart.id = " + str(retained_earnings) + " AND summaryprev.month = 12, IFNULL(chart.beginning_amount, 0) , IFNULL(summaryprev.end_amount, 0)) AS summary_end_amount, " \
                "IF (chart.id = " + str(retained_earnings) + " AND summaryprev.month = 12, chart.beginning_code , summaryprev.end_code) AS summary_end_code, " \
                "IF (chart.main >= 4 AND summaryprev.month = 12, IFNULL(chart.beginning_amount, 0), IFNULL(summaryprev.year_to_date_amount, 0)) " \
                "AS summary_year_to_date_amount, " \
                "IF (chart.main >= 4 AND summaryprev.month = 12, chart.beginning_code, summaryprev.year_to_date_code) AS summary_year_to_date_code, " \
                "subled_d.balancecode AS debit_code, IFNULL(subled_d.amount, 0) AS debit_amount, " \
                "subled_c.balancecode AS credit_code, IFNULL(subled_c.amount, 0) AS credit_amount, " \
                "IF (IFNULL(subled_d.amount, 0) >= IFNULL(subled_c.amount, 0), 'D', 'C') AS trans_mon_code, " \
                "ABS(IFNULL(subled_d.amount, 0) - IFNULL(subled_c.amount, 0)) AS trans_mon_amount " \
                "FROM chartofaccount AS chart " \
                "LEFT OUTER JOIN (" \
                "   SELECT summary.chartofaccount_id, " \
                "   summary.beginning_amount AS summary_beg_amount, summary.beginning_code AS summary_beg_code,	" \
                "   summary.end_amount, summary.end_code, " \
                "   summary.year_to_date_amount, summary.year_to_date_code, summary.month " \
                "   FROM subledgersummary AS summary " \
                "   WHERE summary.year = '" + str(year) + "' AND summary.month = '" + str(month) + "' " \
                ") AS summary ON summary.chartofaccount_id = chart.id " \
                "LEFT OUTER JOIN (" \
                "   SELECT summary.chartofaccount_id, " \
                "   summary.beginning_amount AS summary_beg_amount, summary.beginning_code AS summary_beg_code,	" \
                "   summary.end_amount, summary.end_code, " \
                "   summary.year_to_date_amount, summary.year_to_date_code, summary.month " \
                "   FROM subledgersummary AS summary " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' " \
                ") AS summaryprev ON summaryprev.chartofaccount_id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "SELECT subled.chartofaccount_id, ABS((subled.journal_voucher_debit_total + subled.check_voucher_debit_total + " \
                "   subled.accounts_payable_voucher_debit_total + subled.official_receipt_debit_total)" \
                "   - (subled.journal_voucher_credit_total + subled.check_voucher_credit_total + " \
                "   subled.accounts_payable_voucher_credit_total + subled.official_receipt_credit_total)) " \
                "   AS amount, IF ((subled.journal_voucher_debit_total + subled.check_voucher_debit_total + " \
                "   subled.accounts_payable_voucher_debit_total + subled.official_receipt_debit_total) >= " \
                "   (subled.journal_voucher_credit_total + subled.check_voucher_credit_total + " \
                "   subled.accounts_payable_voucher_credit_total + subled.official_receipt_credit_total)" \
                "   , 'D', 'C') AS balancecode " \
                "  FROM subledgersummary AS subled " \
                "  WHERE subled.year = '" + str(year) + "' AND subled.month = '" + str(month) + "' " \
                "AND (subled.journal_voucher_debit_total + subled.check_voucher_debit_total + subled.accounts_payable_voucher_debit_total + subled.official_receipt_debit_total) >= " \
                "(subled.journal_voucher_credit_total + subled.check_voucher_credit_total + subled.accounts_payable_voucher_credit_total + subled.official_receipt_credit_total)" \
                "  GROUP BY subled.chartofaccount_id " \
                ") AS subled_d ON subled_d.chartofaccount_id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "SELECT subled.chartofaccount_id, ABS((subled.journal_voucher_debit_total + subled.check_voucher_debit_total + " \
                "   subled.accounts_payable_voucher_debit_total + subled.official_receipt_debit_total)" \
                "   - (subled.journal_voucher_credit_total + subled.check_voucher_credit_total + " \
                "   subled.accounts_payable_voucher_credit_total + subled.official_receipt_credit_total)) " \
                "   AS amount, IF ((subled.journal_voucher_debit_total + subled.check_voucher_debit_total + " \
                "   subled.accounts_payable_voucher_debit_total + subled.official_receipt_debit_total) >= " \
                "   (subled.journal_voucher_credit_total + subled.check_voucher_credit_total + " \
                "   subled.accounts_payable_voucher_credit_total + subled.official_receipt_credit_total)" \
                "   , 'D', 'C') AS balancecode " \
                "  FROM subledgersummary AS subled " \
                "  WHERE subled.year = '" + str(year) + "' AND subled.month = '" + str(month) + "' " \
                "AND (subled.journal_voucher_debit_total + subled.check_voucher_debit_total + subled.accounts_payable_voucher_debit_total + subled.official_receipt_debit_total) < " \
                "(subled.journal_voucher_credit_total + subled.check_voucher_credit_total + subled.accounts_payable_voucher_credit_total + subled.official_receipt_credit_total)" \
                "  GROUP BY subled.chartofaccount_id " \
                ") AS subled_c ON subled_c.chartofaccount_id = chart.id " \
                "LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "LEFT OUTER JOIN chartofaccountmainsubgroup AS mainsubgroup ON mainsubgroup.sub_id = subgroup.id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS maingroup ON maingroup.id = mainsubgroup.main_id " \
                "WHERE chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.id != " + str(current_earnings) + " " \
                "GROUP BY chart.accountcode ORDER BY chart.accountcode ASC"
    # print retained_earnings
    # print prevyear
    # print prevmonth
    # print year
    # print month
    # print current_earnings
    #
    # print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_balance_sheet(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth):
    print "balance sheet query"
    ''' Create query '''
    cursor = connection.cursor()
    if type == 'P':
        query = "SELECT z.*, " \
                "IF(z.current_code <>  z.main_balancecode, current_amount, ABS(current_amount)) AS current_amount_abs, " \
                "IF(z.prev_code <>  z.main_balancecode, prev_amount, ABS(prev_amount)) AS prev_amount_abs " \
                "FROM ( SELECT thisgroup.code AS this_code, thisgroup.description AS this_desc, grouping.code AS group_code, grouping.description AS group_desc, " \
                "       maingroup.balancecode AS main_balancecode, " \
                "       maingroup.code AS maingroup_code, maingroup.description AS maingroup_desc, " \
                "       subgroup.code AS subgroup_code, subgroup.description AS subgroup_desc, " \
                "       IF (maingroup.balancecode = 'C', (IFNULL(credit.credit_end_amount, 0) - IFNULL(debit.debit_end_amount, 0)) , (IFNULL(debit.debit_end_amount, 0) - IFNULL(credit.credit_end_amount, 0))) AS current_amount, " \
                "       IF (maingroup.balancecode = 'C', (IFNULL(summary_credit.sc_end_amount, 0) - IFNULL(summary_debit.sd_end_amount, 0)) , (IFNULL(summary_debit.sd_end_amount, 0) - IFNULL(summary_credit.sc_end_amount, 0))) AS prev_amount, " \
                "       IFNULL(debit.debit_end_code, 'D') AS debit_end_code, IFNULL(debit.debit_end_amount, 0) AS debit_end_amount, " \
                "       IFNULL(credit.credit_end_code, 'C') AS credit_end_code, IFNULL(credit.credit_end_amount, 0) AS credit_end_amount, " \
                "       IFNULL(summary_debit.sd_end_code, 'D') AS sd_end_code, IFNULL(summary_debit.sd_end_amount, 'D') AS sd_end_amount, " \
                "       IFNULL(summary_credit.sc_end_code, 'C')AS sc_end_code, IFNULL(summary_credit.sc_end_amount, 'C') AS sc_end_amount," \
                "       IF (IFNULL(debit.debit_end_amount, 0) >= IFNULL(credit.credit_end_amount, 0), IFNULL(debit.debit_end_code, 'D'), IFNULL(credit.credit_end_code, 'C')) AS current_code, " \
                "       IF (IFNULL(summary_debit.sd_end_amount, 0) >= IFNULL(summary_credit.sc_end_amount, 0), IFNULL(summary_debit.sd_end_code, 'D'), IFNULL(summary_credit.sc_end_code, 'C')) AS prev_code " \
                "FROM chartofaccount AS chart " \
                "LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "LEFT OUTER JOIN chartofaccountmainsubgroup AS mainsubgroup ON mainsubgroup.sub_id = subgroup.id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS maingroup ON maingroup.id = mainsubgroup.main_id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS grouping ON grouping.id = maingroup.group_id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS thisgroup ON thisgroup.id = grouping.group_id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart_d.id AS debit_id, SUM(chart_d.end_amount) AS debit_end_amount, chart_d.end_code AS debit_end_code, " \
                "           subgroup_d.id AS debit_subgroup, subgroup_d.code AS debit_subgroupcode " \
                "   FROM chartofaccount AS chart_d " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup_d ON subgroup_d.id = chart_d.subgroup_id " \
                "   WHERE chart_d.end_code = 'D' AND chart_d.accounttype = 'P' AND chart_d.isdeleted = 0 AND chart_d.main <= 3 AND chart_d.id != '"+str(current_earnings)+"' " \
                "   GROUP BY subgroup_d.id, chart_d.end_code " \
                "   UNION " \
                "   SELECT chart_d.id AS debit_id, SUM(chart_d.year_to_date_amount) AS debit_end_amount, chart_d.year_to_date_code AS debit_end_code, " \
                "           subgroup_d.id AS debit_subgroup, subgroup_d.code AS debit_subgroupcode " \
                "   FROM chartofaccount AS chart_d " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup_d ON subgroup_d.id = '164' " \
                "   WHERE chart_d.year_to_date_code = 'D' AND chart_d.accounttype = 'P' AND chart_d.isdeleted = 0 AND chart_d.main > 3 " \
                ") AS debit ON debit.debit_subgroup = subgroup.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart_c.id AS credit_id, SUM(chart_c.end_amount) AS credit_end_amount, chart_c.end_code AS credit_end_code, " \
                "           subgroup_c.id AS credit_subgroup, subgroup_c.code AS credit_subgroupcode " \
                "   FROM chartofaccount AS chart_c " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup_c ON subgroup_c.id = chart_c.subgroup_id " \
                "   WHERE chart_c.end_code = 'C' AND chart_c.accounttype = 'P' AND chart_c.isdeleted = 0 AND chart_c.main <= 3 AND chart_c.id != '"+str(current_earnings)+"' " \
                "   GROUP BY subgroup_c.id, chart_c.end_code " \
                "   UNION " \
                "   SELECT chart_c.id AS credit_id, SUM(chart_c.year_to_date_amount) AS credit_end_amount, chart_c.year_to_date_code AS credit_end_code, " \
                "           subgroup_c.id AS credit_subgroup, subgroup_c.code AS credit_subgroupcode " \
                "   FROM chartofaccount AS chart_c " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup_c ON subgroup_c.id = '164' " \
                "   WHERE chart_c.year_to_date_code = 'C' AND chart_c.accounttype = 'P' AND chart_c.isdeleted = 0 AND chart_c.main > 3 " \
                ") AS credit ON credit.credit_subgroup = subgroup.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT subgroup.id AS s_debit_id, subgroup.code AS s_debit_code, " \
                "           SUM(summary.end_amount) AS sd_end_amount, summary.end_code AS sd_end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'D' " \
                "   AND chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main <= 3 AND chart.id != '"+str(current_earnings)+"' " \
                "   GROUP BY subgroup.id, summary.end_code " \
                "   UNION " \
                "   SELECT subgroup.id AS s_debit_id, subgroup.code AS s_debit_code, " \
                "           SUM(summary.year_to_date_amount) AS sd_end_amount, summary.year_to_date_code AS sd_end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'D' " \
                "   AND chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.id = '" + str(current_earnings) + "' " \
                "   GROUP BY subgroup.id, summary.end_code " \
                ") AS summary_debit ON summary_debit.s_debit_id = subgroup.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT subgroup.id AS s_credit_id, subgroup.code AS s_credit_code, " \
                "           SUM(summary.end_amount) AS sc_end_amount, summary.end_code AS sc_end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'C' " \
                "   AND chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main <= 3 AND chart.id != '"+str(current_earnings)+"' " \
                "   GROUP BY subgroup.id, summary.end_code " \
                "   UNION " \
                "   SELECT subgroup.id AS s_credit_id, subgroup.code AS s_credit_code, " \
                "           SUM(summary.year_to_date_amount) AS sc_end_amount, summary.year_to_date_code AS sc_end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'C' " \
                "   AND chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.id = '" + str(current_earnings) + "' " \
                "   GROUP BY subgroup.id, summary.end_code " \
                ") AS summary_credit ON summary_credit.s_credit_id = subgroup.id " \
                "LEFT OUTER JOIN chartofaccount AS chartmain ON (chartmain.main = chart.main " \
                "AND chartmain.sub = 0 AND chartmain.item = 0 " \
                "AND chartmain.cont = 0 AND chartmain.sub = 000000 " \
                "AND chartmain.accounttype = 'T')" \
                "WHERE chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main <= 3 " \
                "GROUP BY subgroup.id " \
                "ORDER BY maingroup.code, subgroup.code) AS z"
    else:
        query = "SELECT z.*, " \
                "IF(z.current_code <>  z.main_balancecode, current_amount, ABS(current_amount)) AS current_amount_abs, " \
                "IF(z.prev_code <>  z.main_balancecode, prev_amount, ABS(prev_amount)) AS prev_amount_abs " \
                "FROM ( SELECT thisgroup.code AS this_code, thisgroup.description AS this_desc, grouping.code AS group_code, grouping.description AS group_desc, " \
                "       maingroup.balancecode AS main_balancecode, " \
                "       maingroup.code AS maingroup_code, maingroup.description AS maingroup_desc, " \
                "       subgroup.code AS subgroup_code, subgroup.description AS subgroup_desc, " \
                "       IF (maingroup.balancecode = 'C', (IFNULL(credit.credit_end_amount, 0) - IFNULL(debit.debit_end_amount, 0)) , (IFNULL(debit.debit_end_amount, 0) - IFNULL(credit.credit_end_amount, 0))) AS current_amount, " \
                "       IF (maingroup.balancecode = 'C', (IFNULL(summary_credit.sc_end_amount, 0) - IFNULL(summary_debit.sd_end_amount, 0)) , (IFNULL(summary_debit.sd_end_amount, 0) - IFNULL(summary_credit.sc_end_amount, 0))) AS prev_amount, " \
                "       IFNULL(debit.debit_end_code, 'D') AS debit_end_code, IFNULL(debit.debit_end_amount, 0) AS debit_end_amount, " \
                "       IFNULL(credit.credit_end_code, 'C') AS credit_end_code, IFNULL(credit.credit_end_amount, 0) AS credit_end_amount, " \
                "       IFNULL(summary_debit.sd_end_code, 'D') AS sd_end_code, IFNULL(summary_debit.sd_end_amount, 'D') AS sd_end_amount, " \
                "       IFNULL(summary_credit.sc_end_code, 'C')AS sc_end_code, IFNULL(summary_credit.sc_end_amount, 'C') AS sc_end_amount," \
                "       IF (IFNULL(debit.debit_end_amount, 0) >= IFNULL(credit.credit_end_amount, 0), IFNULL(debit.debit_end_code, 'D'), IFNULL(credit.credit_end_code, 'C')) AS current_code, " \
                "       IF (IFNULL(summary_debit.sd_end_amount, 0) >= IFNULL(summary_credit.sc_end_amount, 0), IFNULL(summary_debit.sd_end_code, 'D'), IFNULL(summary_credit.sc_end_code, 'C')) AS prev_code " \
                "FROM chartofaccount AS chart " \
                "LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "LEFT OUTER JOIN chartofaccountmainsubgroup AS mainsubgroup ON mainsubgroup.sub_id = subgroup.id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS maingroup ON maingroup.id = mainsubgroup.main_id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS grouping ON grouping.id = maingroup.group_id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS thisgroup ON thisgroup.id = grouping.group_id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart_d.id AS debit_id, SUM(summary.end_amount) AS debit_end_amount, summary.end_code AS debit_end_code, " \
                "           subgroup_d.id AS debit_subgroup, subgroup_d.code AS debit_subgroupcode " \
                "   FROM chartofaccount AS chart_d " \
                "   LEFT OUTER JOIN subledgersummary AS summary ON summary.chartofaccount_id = chart_d.id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup_d ON subgroup_d.id = chart_d.subgroup_id " \
                "   WHERE summary.end_code = 'D' AND summary.year = '" + str(year) + "' AND summary.month = '" + str(month) + "' AND chart_d.accounttype = 'P' AND chart_d.isdeleted = 0 AND chart_d.main <= 3 AND chart_d.id != '" + str(current_earnings) + "' " \
                "   GROUP BY subgroup_d.id, summary.end_code " \
                "   UNION " \
                "   SELECT chart_d.id AS debit_id, SUM(summary.year_to_date_amount) AS debit_end_amount, summary.year_to_date_code AS debit_end_code, " \
                "           subgroup_d.id AS debit_subgroup, subgroup_d.code AS debit_subgroupcode " \
                "   FROM chartofaccount AS chart_d " \
                "   LEFT OUTER JOIN subledgersummary AS summary ON summary.chartofaccount_id = chart_d.id" \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup_d ON subgroup_d.id = '164' " \
                "   WHERE summary.year_to_date_code = 'D' AND summary.year = '" + str(year) + "' AND summary.month = '" + str(month) + "' AND chart_d.accounttype = 'P' AND chart_d.isdeleted = 0 AND chart_d.main > 3 " \
                ") AS debit ON debit.debit_subgroup = subgroup.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart_c.id AS credit_id, SUM(summary.end_amount) AS credit_end_amount, summary.end_code AS credit_end_code, " \
                "           subgroup_c.id AS credit_subgroup, subgroup_c.code AS credit_subgroupcode " \
                "   FROM chartofaccount AS chart_c " \
                "   LEFT OUTER JOIN subledgersummary AS summary ON summary.chartofaccount_id = chart_c.id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup_c ON subgroup_c.id = chart_c.subgroup_id " \
                "   WHERE summary.end_code = 'C' AND summary.year = '" + str(year) + "' AND summary.month = '" + str(month) + "' AND chart_c.accounttype = 'P' AND chart_c.isdeleted = 0 AND chart_c.main <= 3 AND chart_c.id != '" + str(current_earnings) + "' " \
                "   GROUP BY subgroup_c.id, summary.end_code " \
                "   UNION " \
                "   SELECT chart_c.id AS credit_id, SUM(summary.year_to_date_amount) AS credit_end_amount, summary.year_to_date_code AS credit_end_code, " \
                "           subgroup_c.id AS credit_subgroup, subgroup_c.code AS credit_subgroupcode " \
                "   FROM chartofaccount AS chart_c " \
                "   LEFT OUTER JOIN subledgersummary AS summary ON summary.chartofaccount_id = chart_c.id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup_c ON subgroup_c.id = '164' " \
                "   WHERE summary.year_to_date_code = 'C' AND summary.year = '" + str(year) + "' AND summary.month = '" + str(month) + "' AND chart_c.accounttype = 'P' AND chart_c.isdeleted = 0 AND chart_c.main > 3 " \
                ") AS credit ON credit.credit_subgroup = subgroup.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT subgroup.id AS s_debit_id, subgroup.code AS s_debit_code, " \
                "           SUM(summary.end_amount) AS sd_end_amount, summary.end_code AS sd_end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'D' " \
                "   AND chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main <= 3 AND chart.id != '" + str(current_earnings) + "' " \
                "   GROUP BY subgroup.id, summary.end_code " \
                "   UNION " \
                "   SELECT subgroup.id AS s_debit_id, subgroup.code AS s_debit_code, " \
                "           SUM(summary.year_to_date_amount) AS sd_end_amount, summary.year_to_date_code AS sd_end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'D' " \
                "   AND chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.id = '" + str(current_earnings) + "' " \
                "   GROUP BY subgroup.id, summary.end_code " \
                ") AS summary_debit ON summary_debit.s_debit_id = subgroup.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT subgroup.id AS s_credit_id, subgroup.code AS s_credit_code, " \
                "           SUM(summary.end_amount) AS sc_end_amount, summary.end_code AS sc_end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'C' " \
                "   AND chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main <= 3 AND chart.id != '" + str(current_earnings) + "' " \
                "   GROUP BY subgroup.id, summary.end_code " \
                "   UNION " \
                "   SELECT subgroup.id AS s_credit_id, subgroup.code AS s_credit_code, " \
                "           SUM(summary.year_to_date_amount) AS sc_end_amount, summary.year_to_date_code AS sc_end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'C' " \
                "   AND chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.id = '" + str(current_earnings) + "' " \
                "   GROUP BY subgroup.id, summary.end_code " \
                ") AS summary_credit ON summary_credit.s_credit_id = subgroup.id " \
                "LEFT OUTER JOIN chartofaccount AS chartmain ON (chartmain.main = chart.main " \
                "AND chartmain.sub = 0 AND chartmain.item = 0 " \
                "AND chartmain.cont = 0 AND chartmain.sub = 000000 " \
                "AND chartmain.accounttype = 'T')" \
                "WHERE chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main <= 3 " \
                "GROUP BY subgroup.id " \
                "ORDER BY maingroup.code, subgroup.code) AS z"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_income_statement(type, retained_earnings, current_earnings, year, month, prevyear, prevmonth):
    print "income statement query"
    ''' Create query '''
    cursor = connection.cursor()
    if type == 'P':
        query = "SELECT grouping.code AS group_code, grouping.description AS group_desc, grouping.title AS group_title, maingroup.code AS maingroup_code, maingroup.description AS maingroup_desc, " \
                "maingroup.title AS maingroup_title, subgroup.code AS subgroup_code, subgroup.description AS subgroup_desc, " \
                "SUM(z.current_amount) AS current_amount, SUM(z.prev_amount) AS prev_amount, SUM(z.todate_amount) AS todate_amount " \
                "FROM ( " \
                "   SELECT chartmain.main, chartmain.balancecode,chart.id, chart.subgroup_id, chart.accountcode, chart.description, " \
                "   IF (chartmain.balancecode = 'D', (IFNULL(current_debit.end_amount, 0) - IFNULL(current_credit.end_amount, 0)), (IFNULL(current_credit.end_amount, 0) - IFNULL(current_debit.end_amount, 0))) AS current_amount, " \
                "   IF (chartmain.balancecode = 'D', (IFNULL(prev_debit.end_amount, 0) - IFNULL(prev_credit.end_amount, 0)), (IFNULL(prev_credit.end_amount, 0) - IFNULL(prev_debit.end_amount, 0))) AS prev_amount, " \
                "   IF (chartmain.balancecode = 'D', (IFNULL(todate_debit.year_to_date_amount, 0) - IFNULL(todate_credit.year_to_date_amount, 0)), (IFNULL(todate_credit.year_to_date_amount, 0) - IFNULL(todate_debit.year_to_date_amount, 0))) AS todate_amount, " \
                "   IFNULL(current_debit.end_amount, 0) AS current_debit_amount, " \
                "   IFNULL(current_debit.end_code, 'D') AS current_debit_code, " \
                "   IFNULL(current_credit.end_amount, 0) AS current_credit_amount, IFNULL(current_credit.end_code, 'C') AS current_credit_code, " \
                "   IFNULL(prev_debit.end_amount, 0) AS prev_debit_amount, IFNULL(prev_debit.end_code, 'D') AS prev_debit_code, " \
                "   IFNULL(prev_credit.end_amount, 0) AS prev_credit_amount, IFNULL(prev_credit.end_code, 'C') AS prev_credit_code, " \
                "   IFNULL(todate_debit.year_to_date_amount, 0) AS todate_debit_amount, IFNULL(todate_debit.year_to_date_code, 'D') AS todate_debit_code, " \
                "   IFNULL(todate_credit.year_to_date_amount, 0) AS todate_credit_amount, IFNULL(todate_credit.year_to_date_code, 'C') AS todate_credit_code " \
                "FROM chartofaccount AS chart " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, chart.description, chart.end_amount, chart.end_code " \
                "   FROM chartofaccount AS chart " \
                "   WHERE chart.accounttype = 'P' AND chart.main > 3 " \
                "   AND chart.isdeleted = 0 AND chart.end_code = 'C' " \
                ") AS current_credit ON current_credit.id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, chart.description, chart.end_amount, chart.end_code " \
                "   FROM chartofaccount AS chart " \
                "   WHERE chart.accounttype = 'P' AND chart.main > 3 " \
                "   AND chart.isdeleted = 0 AND chart.end_code = 'D' " \
                ") AS current_debit ON current_debit.id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, summary.end_amount, summary.end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'C' " \
                "   AND chart.accounttype = 'P' AND chart.main > 3 AND chart.isdeleted = 0 " \
                ") AS prev_credit ON prev_credit.id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, summary.end_amount, summary.end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'D' " \
                "   AND chart.accounttype = 'P' AND chart.main > 3 AND chart.isdeleted = 0 " \
                ") AS prev_debit ON prev_debit.id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, chart.description, chart.year_to_date_amount, chart.year_to_date_code " \
                "   FROM chartofaccount AS chart " \
                "   WHERE chart.accounttype = 'P' AND chart.main > 3 " \
                "   AND chart.isdeleted = 0 AND chart.year_to_date_code = 'C' " \
                ") AS todate_credit ON todate_credit.id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, chart.description, chart.year_to_date_amount, chart.year_to_date_code " \
                "   FROM chartofaccount AS chart " \
                "   WHERE chart.accounttype = 'P' AND chart.main > 3 " \
                "   AND chart.isdeleted = 0 AND chart.year_to_date_code = 'D' " \
                ") AS todate_debit ON todate_debit.id = chart.id " \
                "LEFT OUTER JOIN chartofaccount AS chartmain ON (IF(chartmain.main = 7,  " \
                "(chartmain.main = chart.main AND chartmain.clas = 1 AND chartmain.sub = 0  " \
                "AND chartmain.item = 0 AND chartmain.cont = 0 AND chartmain.sub = 000000) ,  " \
                "(chartmain.main = chart.main AND chartmain.clas = 0 AND chartmain.sub = 0  " \
                "AND chartmain.item = 0 AND chartmain.cont = 0 AND chartmain.sub = 000000))) " \
                "WHERE chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main > 3 " \
                "ORDER BY chart.accountcode) AS z " \
                "LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = z.subgroup_id " \
                "LEFT OUTER JOIN chartofaccountmainsubgroup AS mainsubgroup ON mainsubgroup.sub_id = subgroup.id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS maingroup ON maingroup.id = mainsubgroup.main_id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS grouping ON grouping.id = maingroup.group_id " \
                "GROUP BY maingroup.code, subgroup.code " \
                "ORDER BY maingroup.code, subgroup.code"
    else:
        query = "SELECT grouping.code AS group_code, grouping.description AS group_desc, grouping.title AS group_title, maingroup.code AS maingroup_code, maingroup.description AS maingroup_desc, " \
                "maingroup.title AS maingroup_title, subgroup.code AS subgroup_code, subgroup.description AS subgroup_desc, " \
                "SUM(z.current_amount) AS current_amount, SUM(z.prev_amount) AS prev_amount, SUM(z.todate_amount) AS todate_amount " \
                "FROM ( " \
                "   SELECT chartmain.main, chartmain.balancecode,chart.id, chart.subgroup_id, chart.accountcode, chart.description, " \
                "   IF (chartmain.balancecode = 'D', (IFNULL(current_debit.end_amount, 0) - IFNULL(current_credit.end_amount, 0)), (IFNULL(current_credit.end_amount, 0) - IFNULL(current_debit.end_amount, 0))) AS current_amount, " \
                "   IF (chartmain.balancecode = 'D', (IFNULL(prev_debit.end_amount, 0) - IFNULL(prev_credit.end_amount, 0)), (IFNULL(prev_credit.end_amount, 0) - IFNULL(prev_debit.end_amount, 0))) AS prev_amount, " \
                "   IF (chartmain.balancecode = 'D', (IFNULL(todate_debit.year_to_date_amount, 0) - IFNULL(todate_credit.year_to_date_amount, 0)), (IFNULL(todate_credit.year_to_date_amount, 0) - IFNULL(todate_debit.year_to_date_amount, 0))) AS todate_amount, " \
                "   IFNULL(current_debit.end_amount, 0) AS current_debit_amount, " \
                "   IFNULL(current_debit.end_code, 'D') AS current_debit_code, " \
                "   IFNULL(current_credit.end_amount, 0) AS current_credit_amount, IFNULL(current_credit.end_code, 'C') AS current_credit_code, " \
                "   IFNULL(prev_debit.end_amount, 0) AS prev_debit_amount, IFNULL(prev_debit.end_code, 'D') AS prev_debit_code, " \
                "   IFNULL(prev_credit.end_amount, 0) AS prev_credit_amount, IFNULL(prev_credit.end_code, 'C') AS prev_credit_code, " \
                "   IFNULL(todate_debit.year_to_date_amount, 0) AS todate_debit_amount, IFNULL(todate_debit.year_to_date_code, 'D') AS todate_debit_code, " \
                "   IFNULL(todate_credit.year_to_date_amount, 0) AS todate_credit_amount, IFNULL(todate_credit.year_to_date_code, 'C') AS todate_credit_code " \
                "FROM chartofaccount AS chart " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, chart.description, summary.end_amount, summary.end_code " \
                "   FROM chartofaccount AS chart " \
                "   LEFT OUTER JOIN subledgersummary AS summary ON summary.chartofaccount_id = chart.id " \
                "   WHERE chart.accounttype = 'P' AND chart.main > 3 " \
                "   AND chart.isdeleted = 0 AND summary.end_code = 'C' AND summary.year = '" + str(year) + "' AND summary.month = '" + str(month) + "' " \
                ") AS current_credit ON current_credit.id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, chart.description, summary.end_amount, summary.end_code " \
                "   FROM chartofaccount AS chart " \
                "   LEFT OUTER JOIN subledgersummary AS summary ON summary.chartofaccount_id = chart.id " \
                "   WHERE chart.accounttype = 'P' AND chart.main > 3 " \
                "   AND chart.isdeleted = 0 AND summary.end_code = 'D' AND summary.year = '" + str(year) + "' AND summary.month = '" + str(month) + "' " \
                ") AS current_debit ON current_debit.id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, summary.end_amount, summary.end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'C' " \
                "   AND chart.accounttype = 'P' AND chart.main > 3 AND chart.isdeleted = 0 " \
                ") AS prev_credit ON prev_credit.id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, summary.end_amount, summary.end_code " \
                "   FROM subledgersummary AS summary " \
                "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
                "   WHERE summary.year = '" + str(prevyear) + "' AND summary.month = '" + str(prevmonth) + "' AND summary.end_code = 'D' " \
                "   AND chart.accounttype = 'P' AND chart.main > 3 AND chart.isdeleted = 0 " \
                ") AS prev_debit ON prev_debit.id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, chart.description, summary.year_to_date_amount, summary.year_to_date_code " \
                "   FROM chartofaccount AS chart " \
                "   LEFT OUTER JOIN subledgersummary AS summary ON summary.chartofaccount_id = chart.id " \
                "   WHERE chart.accounttype = 'P' AND chart.main > 3 " \
                "   AND chart.isdeleted = 0 AND summary.year_to_date_code = 'C' AND summary.year = '" + str(year) + "' AND summary.month = '" + str(month) + "' " \
                ") AS todate_credit ON todate_credit.id = chart.id " \
                "LEFT OUTER JOIN ( " \
                "   SELECT chart.id, chart.accountcode, chart.description, summary.year_to_date_amount, summary.year_to_date_code " \
                "   FROM chartofaccount AS chart " \
                "   LEFT OUTER JOIN subledgersummary AS summary ON summary.chartofaccount_id = chart.id " \
                "   WHERE chart.accounttype = 'P' AND chart.main > 3 " \
                "   AND chart.isdeleted = 0 AND summary.year_to_date_code = 'D' AND summary.year = '" + str(year) + "' AND summary.month = '" + str(month) + "' " \
                ") AS todate_debit ON todate_debit.id = chart.id " \
                "LEFT OUTER JOIN chartofaccount AS chartmain ON (IF(chartmain.main = 7,  " \
                "(chartmain.main = chart.main AND chartmain.clas = 1 AND chartmain.sub = 0  " \
                "AND chartmain.item = 0 AND chartmain.cont = 0 AND chartmain.sub = 000000) ,  " \
                "(chartmain.main = chart.main AND chartmain.clas = 0 AND chartmain.sub = 0  " \
                "AND chartmain.item = 0 AND chartmain.cont = 0 AND chartmain.sub = 000000))) " \
                "WHERE chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main > 3 " \
                "ORDER BY chart.accountcode) AS z " \
                "LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = z.subgroup_id " \
                "LEFT OUTER JOIN chartofaccountmainsubgroup AS mainsubgroup ON mainsubgroup.sub_id = subgroup.id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS maingroup ON maingroup.id = mainsubgroup.main_id " \
                "LEFT OUTER JOIN chartofaccountmaingroup AS grouping ON grouping.id = maingroup.group_id " \
                "GROUP BY maingroup.code, subgroup.code " \
                "ORDER BY maingroup.code, subgroup.code"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

def excel_trail_balance(request, result, report, type, year, month):
    company = Companyparameter.objects.all().first()
    mon = datetime.date(int(year), int(month), 10).strftime("%B")
    if type == 'P':
        type = 'preliminary'
    else:
        type = 'final'

    file_name = "trial_balance_"+type+"_"+year+"_"+mon+".xlsx"

    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # variables
    # variables
    bold = workbook.add_format({'bold': 1})
    formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
    centertext = workbook.add_format({'bold': 1, 'align': 'center'})
    cell_format = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

    # title

    worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
    worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
    worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
    worksheet.write('A4', 'TRIAL BALANCE', bold)
    worksheet.write('A5', 'period covered ' + str(mon) + ' , ' + str(year), bold)

    worksheet.write('C1', 'Software:')
    worksheet.write('C2', 'User:')
    worksheet.write('C3', 'Datetime:')

    worksheet.write('D1', 'iES Financial System v. 1.0')
    worksheet.write('D2', str(request.user.username))
    worksheet.write('D3', datetime.datetime.now(), cell_format)

    # header
    worksheet.write('A7', 'Account Code', bold)
    worksheet.write('B7', 'Chart of Account', bold)
    worksheet.write('C7', 'Beg Debit', bold)
    worksheet.write('D7', 'Beg Credit', bold)
    worksheet.write('E7', 'Mon Debit', bold)
    worksheet.write('F7', 'Mon Credit', bold)
    worksheet.write('G7', 'End Debit', bold)
    worksheet.write('H7', 'End Credit', bold)
    worksheet.write('I7', 'Inc Debit', bold)
    worksheet.write('J7', 'Inc Credit', bold)
    worksheet.write('K7', 'Bal Debit', bold)
    worksheet.write('L7', 'Bal Credit', bold)
    worksheet.write('M7', 'Main Group Code', bold)
    worksheet.write('N7', 'Main Group Description', bold)
    worksheet.write('O7', 'Sub Group Code', bold)
    worksheet.write('P7', 'Sub Group Description', bold)

    # Start from the first cell. Rows and columns are zero indexed.
    row = 7
    col = 0
    total_beg_debit = 0
    total_beg_credit = 0
    total_mon_debit = 0
    total_mon_credit = 0
    total_end_debit = 0
    total_end_credit = 0
    subtotal_inc_debit = 0
    subtotal_inc_credit = 0
    subtotal_bal_debit = 0
    subtotal_bal_credit = 0
    current_inc_debit = 0
    current_inc_credit = 0
    current_bal_debit = 0
    current_bal_credit = 0
    total_inc_debit = 0
    total_inc_credit = 0
    total_bal_debit = 0
    total_bal_credit = 0

    # Iterate over the data and write it out row by row.
    for data in result:
        worksheet.write(row, col, data.accountcode)
        worksheet.write(row, col + 1, data.description)

        if data.chartmain <= 3:
            if data.summary_end_code == 'D':
                worksheet.write(row, col + 2, float(format(data.summary_end_amount, '.2f')))
                worksheet.write(row, col + 3, float(format(0.00, '.2f')))
                total_beg_debit += float(format(data.summary_end_amount, '.2f'))
            else:
                worksheet.write(row, col + 2, float(format(0.00, '.2f')))
                worksheet.write(row, col + 3, float(format(data.summary_end_amount, '.2f')))
                total_beg_credit += float(format(data.summary_end_amount, '.2f'))
        else:
            if data.accountcode == '5327600000':
                print data.accountcode
                print 'hoy'
                print data.summary_year_to_date_code

            if data.summary_year_to_date_code == 'D':
                worksheet.write(row, col + 2, float(format(data.summary_year_to_date_amount, '.2f')))
                worksheet.write(row, col + 3, float(format(0.00, '.2f')))
                total_beg_debit += float(format(data.summary_year_to_date_amount, '.2f'))
            else:
                worksheet.write(row, col + 2, float(format(0.00, '.2f')))
                worksheet.write(row, col + 3, float(format(data.summary_year_to_date_amount, '.2f')))
                total_beg_credit += float(format(data.summary_year_to_date_amount, '.2f'))

        if data.trans_mon_code == 'D':
            worksheet.write(row, col + 4, float(format(data.trans_mon_amount, '.2f')))
            worksheet.write(row, col + 5, float(format(0.00, '.2f')))
            total_mon_debit += float(format(data.trans_mon_amount, '.2f'))
        else:
            worksheet.write(row, col + 4, float(format(0.00, '.2f')))
            worksheet.write(row, col + 5, float(format(data.trans_mon_amount, '.2f')))
            total_mon_credit += float(format(data.trans_mon_amount, '.2f'))

        #if data.accountcode == '4311000000':
        #    print data.chartmain
        #    print data.description
        #    print data.end_code

        if data.chartmain <= 3:
            if data.end_code == 'D':
                worksheet.write(row, col + 6, float(format(data.end_amount, '.2f')))
                worksheet.write(row, col + 7, float(format(0.00, '.2f')))
                worksheet.write(row, col + 8, float(format(0.00, '.2f')))
                worksheet.write(row, col + 9, float(format(0.00, '.2f')))
                worksheet.write(row, col + 10, float(format(data.end_amount, '.2f')))
                worksheet.write(row, col + 11, float(format(0.00, '.2f')))
                total_end_debit += float(format(data.end_amount, '.2f'))
                subtotal_bal_debit += float(format(data.end_amount, '.2f'))
            else:
                worksheet.write(row, col + 6, float(format(0.00, '.2f')))
                worksheet.write(row, col + 7, float(format(data.end_amount, '.2f')))
                worksheet.write(row, col + 8, float(format(0.00, '.2f')))
                worksheet.write(row, col + 9, float(format(0.00, '.2f')))
                worksheet.write(row, col + 10, float(format(0.00, '.2f')))
                worksheet.write(row, col + 11, float(format(data.end_amount, '.2f')))
                total_end_credit += float(format(data.end_amount, '.2f'))
                subtotal_bal_credit += float(format(data.end_amount, '.2f'))
        else:
            if data.year_to_date_code == 'D':
                worksheet.write(row, col + 6, float(format(data.year_to_date_amount, '.2f')))
                worksheet.write(row, col + 7, float(format(0.00, '.2f')))
                worksheet.write(row, col + 8, float(format(data.year_to_date_amount, '.2f')))
                worksheet.write(row, col + 9, float(format(0.00, '.2f')))
                worksheet.write(row, col + 10, float(format(0.00, '.2f')))
                worksheet.write(row, col + 11, float(format(0.00, '.2f')))
                total_end_debit += float(format(data.year_to_date_amount, '.2f'))
                subtotal_inc_debit += float(format(data.year_to_date_amount, '.2f'))
            else:
                worksheet.write(row, col + 6, float(format(0.00, '.2f')))
                worksheet.write(row, col + 7, float(format(data.year_to_date_amount, '.2f')))
                worksheet.write(row, col + 8, float(format(0.00, '.2f')))
                worksheet.write(row, col + 9, float(format(data.year_to_date_amount, '.2f')))
                worksheet.write(row, col + 10, float(format(0.00, '.2f')))
                worksheet.write(row, col + 11, float(format(0.00, '.2f')))
                total_end_credit += float(format(data.year_to_date_amount, '.2f'))
                subtotal_inc_credit += float(format(data.year_to_date_amount, '.2f'))

        worksheet.write(row, col + 12, data.maingroup_code)
        worksheet.write(row, col + 13, data.maingroup_desc)
        worksheet.write(row, col + 14, data.subgroup_code)
        worksheet.write(row, col + 15, data.subgroup_desc)
        row += 1

    # Write a total using a formula. subtotal
    worksheet.write(row, 0, 'Subtotal')
    worksheet.write(row, col + 8, float(format(subtotal_inc_debit, '.2f')))
    worksheet.write(row, col + 9, float(format(subtotal_inc_credit, '.2f')))
    worksheet.write(row, col + 10, float(format(subtotal_bal_debit, '.2f')))
    worksheet.write(row, col + 11, float(format(subtotal_bal_credit, '.2f')))

    worksheet.write(row + 1, 0, 'Current Earnings/(loss)')
    if subtotal_inc_debit >= subtotal_inc_credit:
        current_inc_credit = float(format(subtotal_inc_debit, '.2f')) - float(format(subtotal_inc_credit, '.2f'))
        worksheet.write(row + 1, col + 8, float(format(0.00, '.2f')))
        worksheet.write(row + 1, col + 9, float(format(current_inc_credit, '.2f')))
    else:
        current_inc_debit = float(format(subtotal_inc_credit, '.2f')) - float(format(subtotal_inc_debit, '.2f'))
        worksheet.write(row + 1, col + 8, float(format(current_inc_debit, '.2f')))
        worksheet.write(row + 1, col + 9, float(format(0.00, '.2f')))

    if subtotal_bal_debit >= subtotal_bal_credit:
        current_bal_credit = float(format(subtotal_bal_debit, '.2f')) - float(format(subtotal_bal_credit, '.2f'))
        worksheet.write(row + 1, col + 10, float(format(0.00, '.2f')))
        worksheet.write(row + 1, col + 11, float(format(current_bal_credit, '.2f')))
    else:
        current_bal_debit = float(format(subtotal_bal_credit, '.2f')) - float(format(subtotal_bal_debit, '.2f'))
        worksheet.write(row + 1, col + 10, float(format(current_bal_debit, '.2f')))
        worksheet.write(row + 1, col + 11, float(format(0.00, '.2f')))

    total_inc_debit = float(format(subtotal_inc_debit, '.2f')) + float(format(current_inc_debit, '.2f'))
    total_inc_credit = float(format(subtotal_inc_credit, '.2f')) + float(format(current_inc_credit, '.2f'))
    total_bal_debit = float(format(subtotal_bal_debit, '.2f')) + float(format(current_bal_debit, '.2f'))
    total_bal_credit = float(format(subtotal_bal_credit, '.2f')) + float(format(current_bal_credit, '.2f'))

    worksheet.write(row + 2, 0, 'Total')
    worksheet.write(row + 2, col + 2, float(format(total_beg_debit, '.2f')))
    worksheet.write(row + 2, col + 3, float(format(total_beg_credit, '.2f')))
    worksheet.write(row + 2, col + 4, float(format(total_mon_debit, '.2f')))
    worksheet.write(row + 2, col + 5, float(format(total_mon_credit, '.2f')))
    worksheet.write(row + 2, col + 6, float(format(total_end_debit, '.2f')))
    worksheet.write(row + 2, col + 7, float(format(total_end_credit, '.2f')))
    worksheet.write(row + 2, col + 8, float(format(total_inc_debit, '.2f')))
    worksheet.write(row + 2, col + 9, float(format(total_inc_credit, '.2f')))
    worksheet.write(row + 2, col + 10, float(format(total_bal_debit, '.2f')))
    worksheet.write(row + 2, col + 11, float(format(total_bal_credit, '.2f')))
    # worksheet.write(row, 1, '=SUM(B1:B4)')
    workbook.close()

    output.seek(0)

    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+file_name

    output.close()

    return response

def excel_balance_sheet(request, result, report, type, year, month, current_month, prev_month, current_year, prev_year):
    company = Companyparameter.objects.all().first()
    mon = datetime.date(int(year), int(month), 10).strftime("%B")
    if type == 'P':
        type = 'preliminary'
    else:
        type = 'final'

    file_name = "balance_sheet_" + type + "_" + year + "_" + mon + ".xlsx"

    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # variables
    bold = workbook.add_format({'bold': 1})
    bold15 = workbook.add_format({'bold': 1})
    bold15.set_font_size(15)
    cell_format = workbook.add_format()
    cell_format.set_align('right')
    cell_format_size = workbook.add_format()
    cell_format_size.set_font_size(18)
    cell_format_size.set_bold()
    cell_format2 = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

    # header
    worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
    worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
    worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
    worksheet.write('A4', 'BALANCE SHEET', bold)
    worksheet.write('A5', 'period covered ' + str(mon) + ' , ' + str(year), bold)

    worksheet.write('C1', 'Software:')
    worksheet.write('C2', 'User:')
    worksheet.write('C3', 'Datetime:')

    worksheet.write('D1', 'iES Financial System v. 1.0')
    worksheet.write('D2', str(request.user.username))
    worksheet.write('D3', datetime.datetime.now(), cell_format2)

    worksheet.write('D7', current_month, bold)
    worksheet.write('E7', prev_month, bold)
    worksheet.write('F7', current_month +' %', bold)
    worksheet.write('G7', prev_month +' %', bold)
    worksheet.write('H7', 'Variance', bold)
    worksheet.write('I7', '%', bold)

    row = 7
    col = 0
    current_percentage = 0
    prev_percentage = 0
    variance_percentage = 0
    variance = 0
    gtotal_current = 0
    gtotal_previous = 0
    gtotal_variance = 0
    gtotal_previous_percentage = 0
    gtotal_var = 0
    prev_liab_equity_percentage = 0

    dataset = pd.DataFrame(result)
    curdata = dataset.groupby('this_code')['current_amount'].sum()
    prevdata = dataset.groupby('this_code')['prev_amount'].sum()
    cur_liab_equity = curdata['ASSETS']
    prev_liab_equity = prevdata['ASSETS']
    for this, thisgroup in dataset.fillna('NaN').sort_values(by=['this_code'], ascending=False, na_position='last').groupby(['this_code', 'this_desc']):
        if this[0] != 'NaN':
            worksheet.write(row, col, str(this[1]), cell_format_size)
            row += 1
        gtotal_current = thisgroup['current_amount_abs'].sum()
        gtotal_previous = thisgroup['prev_amount_abs'].sum()
        for group, maingroup in thisgroup.fillna('NaN').sort_values(by=['group_code'], ascending=True).groupby(['group_code', 'group_desc']):
            if group[0] != 'NaN':
                worksheet.write(row, col, str(group[1]), bold15)
                row += 1
            total_current = 0
            total_previous = 0
            total_variance = 0
            for main, subgroup in maingroup.fillna('NaN').sort_values(by=['subgroup_code'], ascending=True).groupby(['maingroup_code', 'maingroup_desc']):
                worksheet.write(row, col, str(main[1]), bold)
                row += 1
                subtotal_current = 0
                subtotal_previous = 0
                subtotal_variance = 0
                subtotal_cur = subgroup.groupby('maingroup_code')['current_amount_abs'].sum()
                subtotal_prev = subgroup.groupby('maingroup_code')['prev_amount_abs'].sum()
                current_percentage = 0
                previous_percentage = 0
                subtotal_current_percentage = 0
                subtotal_previous_percentage = 0
                for data, sub in subgroup.iterrows():
                    worksheet.write(row, col, str(sub['subgroup_code']))
                    worksheet.write(row, col + 1, str(sub['subgroup_desc']))
                    worksheet.write(row, col + 3, float(format(sub['current_amount_abs'], '.2f')))
                    worksheet.write(row, col + 4, float(format(sub['prev_amount_abs'], '.2f')))

                    if float(subtotal_cur) > 0:
                        current_percentage = float(format(sub['current_amount_abs'], '.2f')) / float(subtotal_cur) * 100

                    if float(subtotal_prev) > 0:
                        previous_percentage = float(format(sub['prev_amount_abs'], '.2f')) / float(subtotal_prev) * 100

                    variance = float(format(sub['current_amount_abs'], '.2f')) - float(format(sub['prev_amount_abs'], '.2f'))

                    if float(variance) != 0:
                        if sub['prev_amount_abs'] != 0:
                            variance_percentage = float(variance) / float(format(sub['prev_amount_abs'], '.2f')) * 100
                        else:
                            variance_percentage = 0
                    else:
                        variance_percentage = 0

                    worksheet.write(row, col + 5, float(format(current_percentage, '.2f')))
                    worksheet.write(row, col + 6, float(format(previous_percentage, '.2f')))
                    worksheet.write(row, col + 7, float(format(variance, '.2f')))
                    worksheet.write(row, col + 8, float(format(variance_percentage, '.2f')))

                    subtotal_current += float(format(sub['current_amount_abs'], '.2f'))
                    subtotal_previous += float(format(sub['prev_amount_abs'], '.2f'))
                    subtotal_variance += float(format(variance, '.2f'))
                    row += 1

                total_current += subtotal_current
                total_previous += subtotal_previous
                total_variance += subtotal_variance

                worksheet.write(row, col + 1, 'TOTAL ' + str(main[1]), cell_format)
                worksheet.write(row, col + 3, float(format(subtotal_current, '.2f')))
                worksheet.write(row, col + 4, float(format(subtotal_previous, '.2f')))

                if float(total_current) != 0:
                    subtotal_current_percentage = float(format(subtotal_current, '.2f')) / float(format(total_current, '.2f')) * 100
                else:
                    total_current = 0

                if float(total_previous) != 0:
                    subtotal_previous_percentage = float(format(subtotal_previous, '.2f')) / float(format(total_previous, '.2f')) * 100
                else:
                    total_previous = 0

                if float(subtotal_previous) != 0:
                    subtotal_var = float(format(subtotal_variance, '.2f')) / float(format(subtotal_previous, '.2f')) * 100
                else:
                    subtotal_var = 0

                worksheet.write(row, col + 5, float(format(subtotal_current_percentage, '.2f')))
                worksheet.write(row, col + 6, float(format(subtotal_previous_percentage, '.2f')))
                worksheet.write(row, col + 7, float(format(subtotal_current, '.2f')) - float(format(subtotal_previous, '.2f')))
                worksheet.write(row, col + 8, float(format(subtotal_var, '.2f')))
                row += 1

            if group[0] != 'NaN':
                worksheet.write(row, col + 1, 'TOTAL ' + str(group[1]).upper(), bold15)
                worksheet.write(row, col + 3, float(format(total_current, '.2f')))
                worksheet.write(row, col + 4, float(format(total_previous, '.2f')))

                if float(gtotal_current) != 0:
                    total_current_percentage = float(format(total_current, '.2f')) / float(format(gtotal_current, '.2f')) * 100
                else:
                    total_current_percentage = 0

                if float(gtotal_previous) != 0:
                    total_previous_percentage = float(format(total_previous, '.2f')) / float(format(gtotal_previous, '.2f')) * 100
                else:
                    total_previous_percentage = 0

                if float(total_previous) != 0:
                    total_var = float(format(total_variance, '.2f')) / float(format(total_previous, '.2f')) * 100
                else:
                    total_var = 0

                worksheet.write(row, col + 5, float(format(total_current_percentage, '.2f')))
                worksheet.write(row, col + 6, float(format(total_previous_percentage, '.2f')))
                worksheet.write(row, col + 7, float(format(total_current, '.2f')) - float(format(total_previous, '.2f')))
                worksheet.write(row, col + 8, float(format(total_var, '.2f')))
                row += 1

        if this[0] != 'NaN':
            worksheet.write(row, col + 1, 'TOTAL ' + str(this[1]).upper(), cell_format_size)
            worksheet.write(row, col + 3, float(format(gtotal_current, '.2f')))
            worksheet.write(row, col + 4, float(format(gtotal_previous, '.2f')))

            if float(gtotal_current) != 0:
                gtotal_current_percentage = float(format(gtotal_current, '.2f')) / float(format(gtotal_current, '.2f')) * 100
            if float(gtotal_previous) != 0:
                gtotal_previous_percentage = float(format(gtotal_previous, '.2f')) / float(format(gtotal_previous, '.2f')) * 100
                gtotal_variance = float(format(gtotal_current, '.2f')) - float(format(gtotal_previous, '.2f'))
            if float(gtotal_previous) != 0:
                gtotal_var = float(format(gtotal_variance, '.2f')) / float(format(gtotal_previous, '.2f')) * 100

            worksheet.write(row, col + 5, float(format(gtotal_current_percentage, '.2f')))
            worksheet.write(row, col + 6, float(format(gtotal_previous_percentage, '.2f')))
            worksheet.write(row, col + 7, float(format(gtotal_variance, '.2f')))
            worksheet.write(row, col + 8, float(format(gtotal_var, '.2f')))
            row += 1

    worksheet.write(row, col + 1, 'TOTAL LIABILITIES & CAPITAL', cell_format_size)
    worksheet.write(row, col + 3, float(format(cur_liab_equity, '.2f')))
    worksheet.write(row, col + 4, float(format(prev_liab_equity, '.2f')))

    if float(cur_liab_equity) != 0:
        cur_liab_equity_percentage = float(format(cur_liab_equity, '.2f')) / float(format(cur_liab_equity, '.2f')) * 100
    else:
        cur_liab_equity_percentage = 0

    if float(prev_liab_equity) != 0:
        prev_liab_equity_percentage = float(format(prev_liab_equity, '.2f')) / float(format(prev_liab_equity, '.2f')) * 100
    else:
        prev_liab_equity = 0

    liab_equity_variance = float(format(cur_liab_equity, '.2f')) - float(format(prev_liab_equity, '.2f'))

    if float(prev_liab_equity) != 0:
        liab_equity_var = float(format(liab_equity_variance, '.2f')) / float(format(prev_liab_equity, '.2f')) * 100
    else:
        liab_equity_var = 0

    worksheet.write(row, col + 5, float(format(cur_liab_equity_percentage, '.2f')))
    worksheet.write(row, col + 6, float(format(prev_liab_equity_percentage, '.2f')))
    worksheet.write(row, col + 7, float(format(liab_equity_variance, '.2f')))
    worksheet.write(row, col + 8, float(format(liab_equity_var, '.2f')))
    row += 1

    workbook.close()

    output.seek(0)

    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=" + file_name

    output.close()

    return response

def excel_income_statement(request, result, report, type, year, month, current_month, prev_month, current_year, prev_year):
    company = Companyparameter.objects.all().first()
    mon = datetime.date(int(year), int(month), 10).strftime("%B")
    if type == 'P':
        type = 'preliminary'
    else:
        type = 'final'

    file_name = "income_statement_" + type + "_" + year + "_" + mon + ".xlsx"

    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # variables
    bold = workbook.add_format({'bold': 1})
    cell_format = workbook.add_format()
    cell_format.set_align('right')
    # right = workbook.add_format({'right': 1}).set_align('right')

    cell_format2 = workbook.add_format({'num_format': 'yyyy/mm/dd H:M:S', 'align': 'left'})

    # header
    worksheet.write('A1', 'THE PHILIPPINE DAILY INQUIRER, INC.', bold)
    worksheet.write('A2', str(company.address1) + ' ' + str(company.address2), bold)
    worksheet.write('A3', 'VAT REG TIN: ' + str(company.tinnum), bold)
    worksheet.write('A4', 'INCOME STATEMENT', bold)
    worksheet.write('A5', 'period covered ' + str(mon) + ' , ' + str(year), bold)

    worksheet.write('C1', 'Software:')
    worksheet.write('C2', 'User:')
    worksheet.write('C3', 'Datetime:')

    worksheet.write('D1', 'iES Financial System v. 1.0')
    worksheet.write('D2', str(request.user.username))
    worksheet.write('D3', datetime.datetime.now(), cell_format2)

    # header
    worksheet.write('D7', current_month, bold)
    worksheet.write('E7', prev_month, bold)
    worksheet.write('F7', 'To Date', bold)
    worksheet.write('G7', 'Net '+ current_month + ' %', bold)
    worksheet.write('H7', 'Net '+ prev_month + ' %', bold)
    worksheet.write('I7', 'Increase (Decrease)', bold)
    worksheet.write('J7', '%', bold)

    row = 7
    col = 0
    cur_netsales = 0
    prev_netsales = 0
    current_percentage = 0
    prev_percentage = 0
    variance_percentage = 0
    variance = 0
    noi_cur = 0
    noi_prev = 0
    noi_todate = 0
    incometax_cur = 0
    incometax_prev = 0
    incometax_todate = 0

    dataset = pd.DataFrame(result)
    dcur_netsales = dataset.groupby('group_code')['current_amount'].sum()
    dprev_netsales = dataset.groupby('group_code')['prev_amount'].sum()
    dtodate_netsales = dataset.groupby('group_code')['todate_amount'].sum()
    cur_netsales = dcur_netsales['GS'] #dataset['current_amount'][dataset['group_code'] == 'GS'].sum()
    prev_netsales = dprev_netsales['GS'] #dataset['prev_amount'][dataset['group_code'] == 'GS'].sum()
    todate_netsales = dtodate_netsales['GS'] #dataset['todate_amount'][dataset['group_code'] == 'GS'].sum()
    for group, maintitle in dataset.fillna('NaN').groupby(['group_code', 'group_desc', 'group_title']):
        if group[0] != 'NaN' and group[0] != 'PFIT' and group[0] != 'OTHER':
            worksheet.write(row, col, str(group[1]), bold)
            row += 1
        total_current = 0
        total_previous = 0
        total_todate = 0
        total_variance = 0
        total_current_percentage = 0
        total_previous_percentage = 0
        for title, maingroup in maintitle.fillna('NaN').sort_values(by=['maingroup_code'], ascending=True).groupby(['group_code', 'group_desc', 'group_title', 'maingroup_title']):
            net_total_current = 0
            net_total_previous = 0
            net_total_todate = 0
            net_total_variance = 0
            net_total_current_percentage = 0
            net_total_previous_percentage = 0
            for main, subgroup in maingroup.fillna('NaN').sort_values(by=['subgroup_code'], ascending=True).groupby(['maingroup_code', 'maingroup_desc']):
                worksheet.write(row, col, str(main[1]), bold)
                row += 1
                subtotal_current = 0
                subtotal_previous = 0
                subtotal_todate = 0
                subtotal_variance = 0
                subtotal_var = 0
                subtotal_current_percentage = 0
                subtotal_previous_percentage = 0
                for data, sub in subgroup.iterrows():
                    worksheet.write(row, col, str(sub['subgroup_code']))
                    worksheet.write(row, col + 1, str(sub['subgroup_desc']))
                    worksheet.write(row, col + 3, float(format(sub['current_amount'], '.2f')))
                    worksheet.write(row, col + 4, float(format(sub['prev_amount'], '.2f')))
                    worksheet.write(row, col + 5, float(format(sub['todate_amount'], '.2f')))

                    if float(cur_netsales) > 0:
                        current_percentage = float(format(sub['current_amount'], '.2f')) / float(format(cur_netsales, '.2f')) * 100

                    if float(prev_netsales) > 0:
                        previous_percentage = float(format(sub['prev_amount'], '.2f')) / float(format(prev_netsales, '.2f')) * 100

                    variance = float(format(sub['current_amount'], '.2f')) - float(format(sub['prev_amount'], '.2f'))

                    if float(variance) != 0:
                        if float(format(sub['prev_amount'], '.2f')) == 0:
                            if float(variance) > 0:
                                variance_percentage = 100
                            else:
                                variance_percentage = 100 * -1
                        else:
                            variance_percentage = float(variance) / float(format(sub['prev_amount'], '.2f')) * 100
                    else:
                        variance_percentage = 0

                    worksheet.write(row, col + 6, float(format(current_percentage, '.2f')))
                    worksheet.write(row, col + 7, float(format(previous_percentage, '.2f')))
                    worksheet.write(row, col + 8, float(format(variance, '.2f')))
                    worksheet.write(row, col + 9, float(format(variance_percentage, '.2f')))

                    subtotal_current += float(format(sub['current_amount'], '.2f'))
                    subtotal_previous += float(format(sub['prev_amount'], '.2f'))
                    subtotal_todate += float(format(sub['todate_amount'], '.2f'))
                    subtotal_variance += float(format(variance, '.2f'))
                    row += 1

                worksheet.write(row, col + 1, 'TOTAL ' + str(main[1]), cell_format)
                worksheet.write(row, col + 3, float(format(subtotal_current, '.2f')))
                worksheet.write(row, col + 4, float(format(subtotal_previous, '.2f')))
                worksheet.write(row, col + 5, float(format(subtotal_todate, '.2f')))

                if float(cur_netsales) > 0:
                    subtotal_current_percentage = float(format(subtotal_current, '.2f')) / float(format(cur_netsales, '.2f')) * 100
                if float(prev_netsales) > 0:
                    subtotal_previous_percentage = float(format(subtotal_previous, '.2f')) / float(format(prev_netsales, '.2f')) * 100
                if subtotal_previous > 0:
                    subtotal_var = float(format(subtotal_variance, '.2f')) / float(format(subtotal_previous, '.2f')) * 100

                worksheet.write(row, col + 6, float(format(subtotal_current_percentage, '.2f')))
                worksheet.write(row, col + 7, float(format(subtotal_previous_percentage, '.2f')))
                worksheet.write(row, col + 8,
                                float(format(subtotal_current, '.2f')) - float(format(subtotal_previous, '.2f')))
                worksheet.write(row, col + 9, float(format(subtotal_var, '.2f')))
                total_current += float(subtotal_current)
                total_previous += float(subtotal_previous)
                total_todate += float(subtotal_todate)
                net_total_current += float(subtotal_current)
                net_total_previous += float(subtotal_previous)
                net_total_todate += float(subtotal_todate)
                row += 1


            if title[3] != 'NaN':
                if title[3] == 'GROSS INCOME FROM SALES':
                    worksheet.write(row, col + 1, str(title[3]), cell_format)

                    gross_current = float(format(cur_netsales, '.2f')) - float(format(net_total_current, '.2f'))
                    gross_previous = float(format(prev_netsales, '.2f')) - float(format(net_total_previous, '.2f'))
                    gross_todate = float(format(todate_netsales, '.2f')) - float(format(net_total_todate, '.2f'))
                    worksheet.write(row, col + 3, float(format(gross_current, '.2f')))
                    worksheet.write(row, col + 4, float(format(gross_previous, '.2f')))
                    worksheet.write(row, col + 5, float(format(gross_todate, '.2f')))

                    gross_total_current_percentage = 0
                    gross_total_previous_percentage = 0
                    if float(cur_netsales) > 0:
                        gross_total_current_percentage = float(format(gross_current, '.2f')) / float(format(cur_netsales, '.2f')) * 100
                    if float(prev_netsales) > 0:
                        gross_total_previous_percentage = float(format(gross_previous, '.2f')) / float(format(prev_netsales, '.2f')) * 100
                    gross_total_variance = float(format(gross_current, '.2f')) - float(format(gross_previous, '.2f'))
                    gross_total_var = float(format(gross_total_variance, '.2f')) / float(format(gross_previous, '.2f')) * 100

                    worksheet.write(row, col + 6, float(format(gross_total_current_percentage, '.2f')))
                    worksheet.write(row, col + 7, float(format(gross_total_previous_percentage, '.2f')))
                    worksheet.write(row, col + 8,float(format(gross_current, '.2f')) - float(format(gross_previous, '.2f')))
                    worksheet.write(row, col + 9, float(format(gross_total_var, '.2f')))
                elif title[3] == 'NET INCOME BEFORE TAX':
                    worksheet.write(row, col + 1, str(title[3]), cell_format)

                    incometax_cur = float(format(noi_cur, '.2f')) + float(format(total_current, '.2f'));
                    incometax_prev = float(format(noi_prev, '.2f')) + float(format(total_previous, '.2f'));
                    incometax_todate = float(format(noi_todate, '.2f')) + float(format(total_todate, '.2f'));
                    worksheet.write(row, col + 3, float(format(incometax_cur, '.2f')))
                    worksheet.write(row, col + 4, float(format(incometax_prev, '.2f')))
                    worksheet.write(row, col + 5, float(format(incometax_todate, '.2f')))

                    incometax_total_current_percentage = 0
                    incometax_total_previous_percentage = 0
                    if float(cur_netsales) > 0:
                        incometax_total_current_percentage = float(format(incometax_cur, '.2f')) / float(format(cur_netsales, '.2f')) * 100
                    if float(prev_netsales) > 0:
                        incometax_total_previous_percentage = float(format(incometax_prev, '.2f')) / float(format(prev_netsales, '.2f')) * 100
                    incometax_total_variance = float(format(incometax_cur, '.2f')) - float(format(incometax_prev, '.2f'))
                    incometax_total_var = float(format(incometax_total_variance, '.2f')) / float(format(incometax_prev, '.2f')) * 100

                    worksheet.write(row, col + 6, float(format(incometax_total_current_percentage, '.2f')))
                    worksheet.write(row, col + 7, float(format(incometax_total_previous_percentage, '.2f')))
                    worksheet.write(row, col + 8, float(format(incometax_cur, '.2f')) - float(format(incometax_prev, '.2f')))
                    worksheet.write(row, col + 9, float(format(incometax_total_var, '.2f')))
                elif title[3] == 'NET INCOME (LOSS) AFTER TAX':
                    worksheet.write(row, col + 1, str(title[3]), cell_format)

                    incometaxafter_cur = float(format(incometax_cur, '.2f')) + float(format(total_current, '.2f'));
                    incometaxafter_prev = float(format(incometax_prev, '.2f')) + float(format(total_previous, '.2f'));
                    incometaxafter_todate = float(format(incometax_todate, '.2f')) + float(format(total_todate, '.2f'));
                    worksheet.write(row, col + 3, float(format(incometaxafter_cur, '.2f')))
                    worksheet.write(row, col + 4, float(format(incometaxafter_prev, '.2f')))
                    worksheet.write(row, col + 5, float(format(incometaxafter_todate, '.2f')))

                    incometaxafter_total_current_percentage = 0
                    if float(cur_netsales) > 0:
                        incometaxafter_total_current_percentage = float(format(incometaxafter_cur, '.2f')) / float(format(cur_netsales, '.2f')) * 100
                    incometaxafter_total_previous_percentage = 0
                    if float(prev_netsales) > 0:
                        incometaxafter_total_previous_percentage = float(format(incometaxafter_prev, '.2f')) / float(format(prev_netsales, '.2f')) * 100
                    incometaxafter_total_variance = float(format(incometaxafter_cur, '.2f')) - float(format(incometaxafter_prev, '.2f'))
                    incometaxafter_total_var = float(format(incometaxafter_total_variance, '.2f')) / float(format(incometaxafter_prev, '.2f')) * 100

                    worksheet.write(row, col + 6, float(format(incometaxafter_total_current_percentage, '.2f')))
                    worksheet.write(row, col + 7, float(format(incometaxafter_total_previous_percentage, '.2f')))
                    worksheet.write(row, col + 8, float(format(incometaxafter_cur, '.2f')) - float(format(incometaxafter_prev, '.2f')))
                    worksheet.write(row, col + 9, float(format(incometaxafter_total_var, '.2f')))
                else:
                    worksheet.write(row, col + 1, str(title[3]), cell_format)
                    worksheet.write(row, col + 3, float(format(net_total_current, '.2f')))
                    worksheet.write(row, col + 4, float(format(net_total_previous, '.2f')))
                    worksheet.write(row, col + 5, float(format(net_total_todate, '.2f')))

                    if float(cur_netsales) > 0:
                        net_total_current_percentage = float(format(net_total_current, '.2f')) / float(format(cur_netsales, '.2f')) * 100
                    if float(prev_netsales) > 0:
                        net_total_previous_percentage = float(format(net_total_previous, '.2f')) / float(format(prev_netsales, '.2f')) * 100
                    net_total_variance = float(format(net_total_current, '.2f')) - float(format(net_total_previous, '.2f'))
                    net_total_var = float(format(net_total_variance, '.2f')) / float(format(net_total_previous, '.2f')) * 100

                    worksheet.write(row, col + 6, float(format(net_total_current_percentage, '.2f')))
                    worksheet.write(row, col + 7, float(format(net_total_previous_percentage, '.2f')))
                    worksheet.write(row, col + 8, float(format(net_total_current, '.2f')) - float(format(net_total_previous, '.2f')))
                    worksheet.write(row, col + 9, float(format(net_total_var, '.2f')))
                row += 1

        if group[0] != 'NaN' and group[0] != 'PFIT' and group[0] != 'OTHER':
            if group[2] == "NET OPERATING INCOME (LOSS)":
                worksheet.write(row, col + 1, str(group[2]), cell_format)

                noi_cur = float(format(gross_current, '.2f')) - float(format(total_current, '.2f'));
                noi_prev = float(format(gross_previous, '.2f')) - float(format(total_previous, '.2f'));
                noi_todate = float(format(gross_todate, '.2f')) - float(format(total_todate, '.2f'));

                worksheet.write(row, col + 3, float(format(noi_cur, '.2f')))
                worksheet.write(row, col + 4, float(format(noi_prev, '.2f')))
                worksheet.write(row, col + 5, float(format(noi_todate, '.2f')))

                noi_total_current_percentage = 0
                noi_total_previous_percentage = 0
                if float(cur_netsales) > 0:
                    noi_total_current_percentage = float(format(noi_cur, '.2f')) / float(format(cur_netsales, '.2f')) * 100
                if float(prev_netsales) > 0:
                    noi_total_previous_percentage = float(format(noi_prev, '.2f')) / float(format(prev_netsales, '.2f')) * 100
                noi_total_variance = float(format(noi_cur, '.2f')) - float(format(noi_prev, '.2f'))
                noi_total_var = float(format(noi_total_variance, '.2f')) / float(format(noi_prev, '.2f')) * 100

                worksheet.write(row, col + 6, float(format(noi_total_current_percentage, '.2f')))
                worksheet.write(row, col + 7, float(format(noi_total_previous_percentage, '.2f')))
                worksheet.write(row, col + 8, float(format(noi_cur, '.2f')) - float(format(noi_prev, '.2f')))
                worksheet.write(row, col + 9, float(format(noi_total_var, '.2f')))
                row += 1
            else:
                worksheet.write(row, col + 1, 'TOTAL' + str(group[2]), cell_format)
                worksheet.write(row, col + 3, float(format(total_current, '.2f')))
                worksheet.write(row, col + 4, float(format(total_previous, '.2f')))
                worksheet.write(row, col + 5, float(format(total_todate, '.2f')))

                if float(cur_netsales) > 0:
                    total_current_percentage = float(format(total_current, '.2f')) / float(format(cur_netsales, '.2f')) * 100
                if float(prev_netsales) > 0:
                    total_previous_percentage = float(format(total_previous, '.2f')) / float(format(prev_netsales, '.2f')) * 100
                total_variance = float(format(total_current, '.2f')) - float(format(total_previous, '.2f'))
                total_var = float(format(total_variance, '.2f')) / float(format(total_previous, '.2f')) * 100

                worksheet.write(row, col + 6, float(format(total_current_percentage, '.2f')))
                worksheet.write(row, col + 7, float(format(total_previous_percentage, '.2f')))
                worksheet.write(row, col + 8, float(format(total_current, '.2f')) - float(format(total_previous, '.2f')))
                worksheet.write(row, col + 9, float(format(total_var, '.2f')))
                row += 1

    workbook.close()

    output.seek(0)

    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=" + file_name

    output.close()

    return response

def excel_year_end_trial_balance(result):
    #mon = datetime.date(int(year), int(month), 10).strftime("%B")

    file_name = "year_endtrial_balance.xlsx"

    output = io.BytesIO()

    workbook = Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # variables
    bold = workbook.add_format({'bold': 1})

    # header
    worksheet.write('A1', 'Account Code', bold)
    worksheet.write('B1', 'Chart of Account', bold)
    worksheet.write('C1', 'Debit Amount', bold)
    worksheet.write('D1', 'Credit Amount', bold)

    # Start from the first cell. Rows and columns are zero indexed.
    row = 1
    col = 0
    debit = 0
    credit = 0
    # for l in result:
    #     print l.beginning_amount
    #     if l.beginning_code == 'D':
    #         debit += l.beginning_amount
    #     else:
    #         credit += l.beginning_amount

    # Iterate over the data and write it out row by row.
    for data in result:
        worksheet.write(row, col, data.accountcode)
        worksheet.write(row, col + 1, data.description)
        if data.beginning_code == 'D':
            worksheet.write(row, col + 2, float(format(data.beginning_amount, '.2f')))
            worksheet.write(row, col + 3, float(format(0, '.2f')))
            debit += data.beginning_amount
        else:
            worksheet.write(row, col + 2, float(format(0, '.2f')))
            worksheet.write(row, col + 3, float(format(data.beginning_amount, '.2f')))
            credit += data.beginning_amount

        row += 1

    # Write a total using a formula. subtotal
    worksheet.write(row, col+1, 'Total')
    worksheet.write(row, col + 2, float(format(debit, '.2f')))
    worksheet.write(row, col + 3, float(format(credit, '.2f')))


    # worksheet.write(row, 1, '=SUM(B1:B4)')
    workbook.close()

    output.seek(0)

    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+file_name

    output.close()

    return response