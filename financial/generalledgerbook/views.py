from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from chartofaccount.models import Chartofaccount
from subledger.models import Subledger
from subledgersummary.models import Subledgersummary
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from companyparameter.models import Companyparameter
from django.http import JsonResponse
from django.db import connection
from collections import namedtuple
import datetime
from datetime import timedelta



@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'generalledgerbook/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        # context['coa_maingroup'] = ChartofAccountMainGroup.objects.filter(status='A', isdeleted=0).order_by('code')
        # context['coa_subgroup'] = ChartofAccountSubGroup.objects.filter(status='A', isdeleted=0).order_by('code')
        #
        # print context['coa_maingroup']
        # context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        # context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        # context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        # context['unit'] = Unit.objects.filter(isdeleted=0).order_by('code')
        # context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        # context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('code')
        # context['outputvat'] = Outputvat.objects.filter(isdeleted=0).order_by('code')
        # context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        # context['product'] = Product.objects.filter(isdeleted=0).order_by('code')
        # context['wtax'] = Wtax.objects.filter(isdeleted=0).order_by('code')

        months = ([0, '***** Year End *****'], [1, 'January'], [2, 'February'], [3, 'March'], [4, 'April'], [5, 'May'], [6 ,'June'], \
                  [7, 'July'], [8, 'August'], [9, 'September'], [10, 'October'], [11, 'November'], [12, 'December'])

        context['months'] = months
        today = datetime.datetime.now()
        context['this_month'] = 1#today.month
        context['this_year'] = today.year

        return context

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
        context['result'] = query_trial_balance(retained_earnings, current_earnings, year, month, prevyear, prevmonth)
        viewhtml = render_to_string('generalledgerbook/trial_balance.html', context)
    elif report == 'BS':
        print "balance sheet"
        context['month'] = datetime.date(int(year), int(month), 10).strftime("%B")
        context['prev_month'] = datetime.date(int(prevyear), int(prevmonth), 10).strftime("%B")
        context['result'] = query_balance_sheet(retained_earnings, current_earnings, year, month, prevyear, prevmonth)
        viewhtml = render_to_string('generalledgerbook/balance_sheet.html', context)
    elif report == 'IS':
        print "income statement"
        context['result'] = query_income_statement(retained_earnings, current_earnings, year, month, prevyear, prevmonth)
        viewhtml = render_to_string('generalledgerbook/income_statement.html', context)
    else:
        print "no report"

    data = {
        'status': 'success',
        'viewhtml': viewhtml,
    }
    return JsonResponse(data)


def query_trial_balance(retained_earnings, current_earnings, year, month, prevyear, prevmonth):
    print "trial balance query"
    ''' Create query '''
    cursor = connection.cursor()
    query = "SELECT  chart.id AS chartid, chart.main AS chartmain, " \
             "chart.accountcode, chart.description, chart.balancecode, " \
             "chart.beginning_amount, chart.beginning_code, IFNULL(chart.end_amount, 0) AS end_amount, " \
             "chart.end_code, IFNULL(chart.year_to_date_amount, 0) AS year_to_date_amount, chart.year_to_date_code, " \
             "IF (chart.id = " + str(retained_earnings) + " AND summary.month = " + str(prevmonth) + ", IFNULL(chart.beginning_amount, 0) , IFNULL(summary.end_amount, 0)) AS summary_end_amount, " \
             "IF (chart.id = " + str(retained_earnings) + " AND summary.month = " + str(prevmonth) + ", chart.beginning_code , summary.end_code) AS summary_end_code, " \
             "IF (chart.main >= 4 AND summary.month = " + str(prevmonth) + " , IFNULL(chart.beginning_amount, 0), IFNULL(summary.year_to_date_amount, 0)) " \
             "AS summary_year_to_date_amount, " \
             "IF (chart.main >= 4 AND summary.month = " + str(prevmonth) + ", chart.beginning_code, summary.year_to_date_code) AS summary_year_to_date_code, " \
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
             "   WHERE summary.year = " + str(prevyear) + " AND summary.month = " + str(prevmonth) + "" \
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
             "WHERE chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.id != " + str(current_earnings) + " " \
             "ORDER BY chart.accountcode ASC"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_balance_sheet(retained_earnings, current_earnings, year, month, prevyear, prevmonth):
    print "balance sheet query"
    ''' Create query '''
    cursor = connection.cursor()
    query = "SELECT chartmain.accountcode AS main_accountcode, " \
            "       chartmain.balancecode AS main_balancecode, " \
            "       maingroup.code AS maingroup_code, maingroup.description AS maingroup_desc, " \
            "       subgroup.code AS subgroup_code, subgroup.description AS subgroup_desc, " \
            "       (IFNULL(debit.debit_end_amount, 0) - IFNULL(credit.credit_end_amount, 0)) AS current_amount, " \
            "       (IFNULL(summary_debit.sd_end_amount, 0) - IFNULL(summary_credit.sc_end_amount, 0)) AS prev_amount, " \
            "       IFNULL(debit.debit_end_code, 'D') AS debit_end_code, IFNULL(debit.debit_end_amount, 0) AS debit_end_amount, " \
            "       IFNULL(credit.credit_end_code, 'C') AS credit_end_code, IFNULL(credit.credit_end_amount, 0) AS credit_end_amount, " \
            "       IFNULL(summary_debit.sd_end_code, 'D') AS sd_end_code, IFNULL(summary_debit.sd_end_amount, 0) AS sd_end_amount, " \
            "       IFNULL(summary_credit.sc_end_code, 'C')AS sc_end_code, IFNULL(summary_credit.sc_end_amount, 0) AS sc_end_amount " \
            "FROM chartofaccount AS chart " \
            "LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
            "LEFT OUTER JOIN chartofaccountmainsubgroup AS mainsubgroup ON mainsubgroup.sub_id = subgroup.id " \
            "LEFT OUTER JOIN chartofaccountmaingroup AS maingroup ON maingroup.id = mainsubgroup.main_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT chart_d.id AS debit_id, SUM(chart_d.end_amount) AS debit_end_amount, chart_d.end_code AS debit_end_code, " \
            "           subgroup_d.id AS debit_subgroup, subgroup_d.code AS debit_subgroupcode " \
            "   FROM chartofaccount AS chart_d " \
            "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup_d ON subgroup_d.id = chart_d.subgroup_id " \
            "   WHERE chart_d.end_code = 'D' AND chart_d.accounttype = 'P' AND chart_d.isdeleted = 0 AND chart_d.main <= 3 " \
            "   GROUP BY subgroup_d.id, chart_d.end_code " \
            ") AS debit ON debit.debit_subgroup = subgroup.id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT chart_c.id AS credit_id, SUM(chart_c.end_amount) AS credit_end_amount, chart_c.end_code AS credit_end_code, " \
            "           subgroup_c.id AS credit_subgroup, subgroup_c.code AS credit_subgroupcode " \
            "   FROM chartofaccount AS chart_c " \
            "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup_c ON subgroup_c.id = chart_c.subgroup_id " \
            "   WHERE chart_c.end_code = 'C' AND chart_c.accounttype = 'P' AND chart_c.isdeleted = 0 AND chart_c.main <= 3 " \
            "   GROUP BY subgroup_c.id, chart_c.end_code " \
            ") AS credit ON credit.credit_subgroup = subgroup.id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT subgroup.id AS s_debit_id, subgroup.code AS s_debit_code, " \
            "           SUM(summary.end_amount) AS sd_end_amount, summary.end_code AS sd_end_code " \
            "   FROM subledgersummary AS summary " \
            "LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
            "WHERE summary.year = 2017 AND summary.month = 12 AND summary.end_code = 'D' " \
            "AND chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main <= 3 " \
            "GROUP BY subgroup.id, summary.end_code " \
            ") AS summary_debit ON summary_debit.s_debit_id = subgroup.id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT subgroup.id AS s_credit_id, subgroup.code AS s_credit_code, " \
            "           SUM(summary.end_amount) AS sc_end_amount, summary.end_code AS sc_end_code " \
            "   FROM subledgersummary AS summary " \
            "   LEFT OUTER JOIN chartofaccount AS chart ON chart.id = summary.chartofaccount_id " \
            "   LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
            "   WHERE summary.year = 2017 AND summary.month = 12 AND summary.end_code = 'C' " \
            "   AND chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main <= 3 " \
            "   GROUP BY subgroup.id, summary.end_code " \
            ") AS summary_credit ON summary_credit.s_credit_id = subgroup.id " \
            "LEFT OUTER JOIN chartofaccount AS chartmain ON (chartmain.main = chart.main " \
            "AND chartmain.sub = 0 AND chartmain.item = 0 AND chartmain.cont = 0 AND chartmain.sub = 000000 AND chartmain.accounttype = 'T') " \
            "WHERE chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.main <= 3 " \
            "GROUP BY subgroup.id " \
            "ORDER BY chart.main, maingroup.code, subgroup.code"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_income_statement(retained_earnings, current_earnings, year, month, prevyear, prevmonth):
    print "income statement query"
    ''' Create query '''
    cursor = connection.cursor()
    query = "SELECT  chart.id AS chartid, chart.main AS chartmain, chart.accountcode, chart.description, chart.balancecode, chart.beginning_amount, chart.beginning_code, " \
            "IFNULL(chart.end_amount, 0) AS end_amount, chart.end_code, IFNULL(chart.year_to_date_amount, 0) AS year_to_date_amount, chart.year_to_date_code, " \
            "IF (chart.id = 373 AND summary.month = 12, IFNULL(chart.beginning_amount, 0) , IFNULL(summary.end_amount, 0)) AS summary_end_amount, " \
            "IF (chart.id = 373 AND summary.month = 12, chart.beginning_code , summary.end_code) AS summary_end_code, " \
            "IF (chart.main >= 4 AND summary.month = 12 , IFNULL(chart.beginning_amount, 0), IFNULL(summary.year_to_date_amount, 0)) AS summary_year_to_date_amount, " \
            "IF (chart.main >= 4 AND summary.month = 12, chart.beginning_code, summary.year_to_date_code) AS summary_year_to_date_code, " \
            "subled_d.balancecode AS debit_code, " \
            "IFNULL(subled_d.amount, 0) AS debit_amount, subled_c.balancecode AS credit_code, IFNULL(subled_c.amount, 0) AS credit_amount, " \
            "IF (IFNULL(subled_d.amount, 0) >= IFNULL(subled_c.amount, 0), 'D', 'C') AS trans_mon_code,  " \
            "ABS(IFNULL(subled_d.amount, 0) - IFNULL(subled_c.amount, 0)) AS trans_mon_amount, " \
            "chart.subgroup_id, subgroup.code AS subgroupcode, subgroup.description AS subgroup, " \
            "maingroup.code AS maingroupcode, maingroup.description AS maingroup " \
            "FROM chartofaccount AS chart " \
            "LEFT OUTER JOIN ( " \
            "SELECT summary.chartofaccount_id, summary.beginning_amount AS summary_beg_amount, summary.beginning_code AS summary_beg_code, " \
            "summary.end_amount, summary.end_code, " \
            "summary.year_to_date_amount, summary.year_to_date_code, summary.month " \
            "FROM subledgersummary AS summary " \
            "WHERE summary.year = 2017 AND summary.month = 12 " \
            ") AS summary ON summary.chartofaccount_id = chart.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT subled.chartofaccount_id, subled.balancecode, " \
            "SUM(amount) AS amount " \
            "FROM subledger AS subled " \
            "WHERE YEAR(subled.document_date) = '2018' AND MONTH(subled.document_date) = '1' " \
            "AND subled.balancecode = 'D' " \
            "GROUP BY subled.chartofaccount_id, subled.balancecode " \
            ") AS subled_d ON subled_d.chartofaccount_id = chart.id " \
            "LEFT OUTER JOIN ( " \
            "SELECT subled.chartofaccount_id, subled.balancecode, " \
            "SUM(amount) AS amount " \
            "FROM subledger AS subled WHERE YEAR(subled.document_date) = '2018' AND MONTH(subled.document_date) = '1' " \
            "AND subled.balancecode = 'C' " \
            "GROUP BY subled.chartofaccount_id, subled.balancecode ) " \
            "AS subled_c ON subled_c.chartofaccount_id = chart.id " \
            "LEFT OUTER JOIN chartofaccountsubgroup AS subgroup ON subgroup.id = chart.subgroup_id " \
            "LEFT OUTER JOIN chartofaccountmainsubgroup AS mainsubgroup ON mainsubgroup.sub_id = subgroup.id " \
            "LEFT OUTER JOIN chartofaccountmaingroup AS maingroup ON maingroup.id = mainsubgroup.main_id " \
            "WHERE chart.accounttype = 'P' " \
            "AND chart.isdeleted = 0 " \
            "AND chart.main > 3 " \
            "GROUP BY maingroup.code, subgroup.code " \
            "ORDER BY maingroup.code ASC, subgroup.code ASC, chart.accountcode ASC"
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
