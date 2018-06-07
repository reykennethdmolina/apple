from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
# from chartofaccountmaingroup.models import ChartofAccountMainGroup
# from chartofaccountsubgroup.models import ChartofAccountSubGroup
# from chartofaccountmainsubgroup.models import MainGroupSubgroup
from chartofaccount.models import Chartofaccount
from subledger.models import Subledger
from subledgersummary.models import Subledgersummary
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from companyparameter.models import Companyparameter
# from django.db.models import Count
# from branch.models import Branch
# from vat.models import Vat
# from department.models import Department
# from unit.models import Unit
# from bankaccount.models import Bankaccount
# from inputvat.models import Inputvat
# from outputvat.models import Outputvat
# from ataxcode.models import Ataxcode
# from product.models import Product
# from wtax.models import Wtax
# from employee.models import Employee
# from supplier.models import Supplier
# from customer.models import Customer
# from annoying.functions import get_object_or_None
# from django.db.models import Q, Sum
# from dateutil.relativedelta import relativedelta
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

    report =  request.GET["report"]
    type =  request.GET["type"]
    year =  request.GET["year"]
    month = request.GET["month"]

    prevdate = datetime.date(int(year), int(month), 10) - timedelta(days=15)
    prevyear = prevdate.year
    prevmonth = prevdate.month

    # RETAINED EARNINGS
    retained_earnings = Companyparameter.objects.first().coa_retainedearnings_id
    current_earnings = Companyparameter.objects.first().coa_currentearnings_id

    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  chart.id AS chartid, chart.main AS chartmain, " \
            "chart.accountcode, chart.description, chart.balancecode, " \
            "chart.beginning_amount, chart.beginning_code, IFNULL(chart.end_amount, 0) AS end_amount, " \
            "chart.end_code, IFNULL(chart.year_to_date_amount, 0) AS year_to_date_amount, chart.year_to_date_code, " \
            "IF (chart.id = "+str(retained_earnings)+" AND summary.month = "+str(prevmonth)+", IFNULL(chart.beginning_amount, 0) , IFNULL(summary.end_amount, 0)) AS summary_end_amount, " \
            "IF (chart.id = "+str(retained_earnings)+" AND summary.month = "+str(prevmonth)+", chart.beginning_code , summary.end_code) AS summary_end_code, " \
            "IF (chart.main >= 4 AND summary.month = "+str(prevmonth)+" , IFNULL(chart.beginning_amount, 0), IFNULL(summary.year_to_date_amount, 0)) " \
            "AS summary_year_to_date_amount, " \
            "IF (chart.main >= 4 AND summary.month = "+str(prevmonth)+", chart.beginning_code, summary.year_to_date_code) AS summary_year_to_date_code, " \
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
            "   WHERE summary.year = "+str(prevyear)+" AND summary.month = "+str(prevmonth)+"" \
            ") AS summary ON summary.chartofaccount_id = chart.id " \
            "LEFT OUTER JOIN ( " \
                "SELECT subled.chartofaccount_id, subled.balancecode, SUM(amount) AS amount " \
                "FROM subledger AS subled " \
                "WHERE YEAR(subled.document_date) = '"+str(year)+"' AND MONTH(subled.document_date) = '"+str(month)+"' " \
                "AND subled.balancecode = 'D' " \
                "GROUP BY subled.chartofaccount_id, subled.balancecode " \
            ") AS subled_d ON subled_d.chartofaccount_id = chart.id " \
            "LEFT OUTER JOIN ( " \
                "SELECT subled.chartofaccount_id, subled.balancecode, SUM(amount) AS amount " \
                "FROM subledger AS subled " \
                "WHERE YEAR(subled.document_date) = '"+str(year)+"' AND MONTH(subled.document_date) = '"+str(month)+"' " \
                "AND subled.balancecode = 'C' " \
                "GROUP BY subled.chartofaccount_id, subled.balancecode " \
            ") AS subled_c ON subled_c.chartofaccount_id = chart.id " \
            "WHERE chart.accounttype = 'P' AND chart.isdeleted = 0 AND chart.id != "+str(current_earnings)+" " \
            "ORDER BY chart.accountcode ASC"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    context = {}
    context['result'] = result

    if report == 'TB':
        print "trial balance"
        viewhtml = render_to_string('generalledgerbook/trial_balance.html', context)
    elif report == 'BS':
        print "balance sheet"
        viewhtml = render_to_string('generalledgerbook/trial_balance.html', context)
    elif report == 'IS':
        print "income statement"
        viewhtml = render_to_string('generalledgerbook/trial_balance.html', context)
    else:
        print "no report"

    data = {
        'status': 'success',
        'viewhtml': viewhtml,
    }
    return JsonResponse(data)


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


@method_decorator(login_required, name='dispatch')
class ReportResultHtmlView(TemplateView):
    template_name = 'generalledgerbook/reportresulthtml.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['report_xls'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "GENERAL LEDGER BOOK"
        context['rc_title'] = "GENERAL LEDGER BOOK"

        return context


@csrf_exempt
def reportresultquery(request):
    report_type = ''
    report_xls = ''
    report_total = ''

    query = Subledger.objects.all().filter(isdeleted=0)

    # minor filters
    if request.COOKIES.get('rep_f_transactiontype_' + request.resolver_match.app_name):
        key_data = str(request.COOKIES.get('rep_f_transactiontype_' + request.resolver_match.app_name))
        query = query.filter(document_type__in=key_data.split(","))
    if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
        key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
        query = query.filter(document_date__gte=key_data)
    if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
        key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
        query = query.filter(document_date__lte=key_data)

    if request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name) and request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name) != 'null':
        gl_request = request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name)

        query = query.filter(chartofaccount=int(gl_request))

        enable_check = Chartofaccount.objects.get(pk=gl_request)
        if enable_check.bankaccount_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_bankaccount_' + request.resolver_match.app_name)
            query = query.filter(bankaccount=get_object_or_None(Bankaccount, pk=int(gl_item)))
        if enable_check.department_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_department_' + request.resolver_match.app_name)
            query = query.filter(department=get_object_or_None(Department, pk=int(gl_item)))
        if enable_check.unit_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_unit_' + request.resolver_match.app_name)
            query = query.filter(unit=get_object_or_None(Unit, pk=int(gl_item)))
        if enable_check.branch_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_branch_' + request.resolver_match.app_name)
            query = query.filter(branch=get_object_or_None(Branch, pk=int(gl_item)))
        if enable_check.product_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_product_' + request.resolver_match.app_name)
            query = query.filter(product=get_object_or_None(Product, pk=int(gl_item)))
        if enable_check.inputvat_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_inputvat_' + request.resolver_match.app_name)
            query = query.filter(inputvat=get_object_or_None(Inputvat, pk=int(gl_item)))
        if enable_check.outputvat_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_outputvat_' + request.resolver_match.app_name)
            query = query.filter(outputvat=get_object_or_None(Outputvat, pk=int(gl_item)))
        if enable_check.vat_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_vat_' + request.resolver_match.app_name)
            query = query.filter(vat=get_object_or_None(Vat, pk=int(gl_item)))
        if enable_check.wtax_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_wtax_' + request.resolver_match.app_name)
            query = query.filter(wtax=get_object_or_None(Wtax, pk=int(gl_item)))
        if enable_check.ataxcode_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_ataxcode_' + request.resolver_match.app_name)
            query = query.filter(ataxcode=get_object_or_None(Ataxcode, pk=int(gl_item)))
        if enable_check.employee_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_employee_' + request.resolver_match.app_name)
            query = query.filter(employee=get_object_or_None(Employee, pk=int(gl_item)))
        if enable_check.supplier_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_supplier_' + request.resolver_match.app_name)
            query = query.filter(supplier=get_object_or_None(Supplier, pk=int(gl_item)))
        if enable_check.customer_enable == 'Y' \
                and request.COOKIES.get('rep_f_gl_customer_' + request.resolver_match.app_name) \
                and request.COOKIES.get('rep_f_gl_customer_' + request.resolver_match.app_name) != 'null':
            gl_item = request.COOKIES.get('rep_f_gl_customer_' + request.resolver_match.app_name)
            query = query.filter(customer=get_object_or_None(Customer, pk=int(gl_item)))

    elif request.COOKIES.get('rep_f_subgroup_' + request.resolver_match.app_name) and request.COOKIES.get('rep_f_subgroup_' + request.resolver_match.app_name) != 'null':
        key_data = str(request.COOKIES.get('rep_f_subgroup_' + request.resolver_match.app_name))
        query = query.filter(chartofaccount__subgroup__in=key_data.split(","))
    elif request.COOKIES.get('rep_f_maingroup_' + request.resolver_match.app_name):
        key_data = str(request.COOKIES.get('rep_f_maingroup_' + request.resolver_match.app_name))
        key_data = MainGroupSubgroup.objects.filter(main=int(key_data), isdeleted=0, status='A').values_list('sub__pk', flat=True)
        query = query.filter(chartofaccount__subgroup__in=key_data)

    # report type filter
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'bs':
        report_type = "Balance Sheet"
        report_xls = "Balance Sheet"

        query = query.filter(Q(chartofaccount__subgroup__code__startswith='A') | Q(chartofaccount__subgroup__code__startswith='L'))\
            .values('chartofaccount__subgroup__code', 'chartofaccount__subgroup__description', 'chartofaccount__subgroup__mapped_subgroup__main__description') \
            .annotate(count=Count('pk')) \
            .order_by('chartofaccount__subgroup__code')
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'sie':
        report_type = "Statement of Income and Expenses"
        report_xls = "Statement of Income and Expenses"

        query = query.filter(Q(chartofaccount__subgroup__code__startswith='R') | Q(chartofaccount__subgroup__code__startswith='E')) \
            .values('chartofaccount__subgroup__code', 'chartofaccount__subgroup__description', 'chartofaccount__subgroup__mapped_subgroup__main__description') \
            .annotate(count=Count('pk')) \
            .order_by('-chartofaccount__subgroup__code')
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'tb':
        report_type = "Trial Balance"
        report_xls = "Trial Balance"

        dt = datetime.datetime.strptime('2018-02-01', "%Y-%m-%d").date()
        # prev = dt + relativedelta(months=-1)
        # prev = dt + relativedelta(months=-1)
        # prev = dt + relativedelta(months=-1)
        prev = dt + relativedelta(months=0)

        query = Subledgersummary.objects.filter(month=prev.month, year=prev.year, status='A', isdeleted=0).order_by('chartofaccount__accountcode')

        tb_current_query = Subledger.objects.filter(document_date__month=dt.month, document_date__year=dt.year)

        tb_balances = []

        for data in query:
            tb_result = tb_current_query.filter(chartofaccount=data.chartofaccount)
            if tb_result.count() > 0:
                tb_result_d = tb_result.filter(balancecode='D').aggregate(Sum('amount'))['amount__sum']
                tb_result_c = tb_result.filter(balancecode='C').aggregate(Sum('amount'))['amount__sum']

                tb_result_amt = abs(float(tb_result_d if tb_result_d is not None else 0) - float(tb_result_c if tb_result_c is not None else 0))

                if tb_result_d > tb_result_c:
                    tb_result_bal = 'D'
                elif tb_result_d < tb_result_c:
                    tb_result_bal = 'C'
                else:
                    if data.chartofaccount.main < 4:
                        tb_result_bal = data.chartofaccount.end_code
                    else:
                        tb_result_bal = data.chartofaccount.year_to_date_code

                if data.chartofaccount.main < 4:
                    tb_chart_amt = data.end_amount
                    tb_chart_bal = data.end_code
                else:
                    tb_chart_amt = data.year_to_date_amount
                    tb_chart_bal = data.year_to_date_code

                if tb_chart_bal != tb_result_bal:
                    tb_next_amt = abs(tb_result_amt - float(tb_chart_amt))

                    if tb_chart_amt > tb_result_amt:
                        tb_next_bal = tb_chart_bal
                    else:
                        tb_next_bal = tb_result_bal
                else:
                    tb_next_amt = tb_result_amt + float(tb_chart_amt)
                    tb_next_bal = tb_chart_bal

                # tb_prev - tb_result - tb_next

                tb_balances.append([
                    tb_result_amt,
                    tb_result_bal,
                    tb_next_amt,
                    tb_next_bal,
                ])
            else:
                tb_balances.append([
                    '',
                    '',
                    '',
                    '',
                ])
        query = zip(query, tb_balances)

    return query, report_type, report_total, report_xls
