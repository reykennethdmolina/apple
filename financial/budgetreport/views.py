from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from companyparameter.models import Companyparameter
from django.db import connection
from accountexpensebalance.models import Accountexpensebalance
from department.models import Department
from product.models import Product
from utils.mixins import ReportContentMixin
from easy_pdf.views import PDFTemplateView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Case, Value, When, F, Q
from financial.context_processors import namedtuplefetchall
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
class IndexView(TemplateView):
    model = Accountexpensebalance
    template_name = 'budgetreport/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        context['product'] = Product.objects.filter(isdeleted=0).order_by('description')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')

        return context

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = []
        total = []
        report = request.GET['report']
        filter = request.GET['filter']
        type = request.GET['type']
        dfrom = request.GET['from']
        dto = request.GET['to']
        title = "Budget Monitoring Report"
        subtitle = ""
        typetext = "Summary"
        filtertext = "Cost of Sales"

        list = Accountexpensebalance.objects.filter(isdeleted=0)[:0]

        if filter == '1':
            filtertext = "Cost of Sales"
        elif filter == '2':
            filtertext = "General & Administrative"
        elif filter == '3':
            filtertext = "Selling"
        else:
            filtertext = "All"

        if type == '1':
            typetext = "Summary"
        else:
            typetext = "Detailed"

        if report == '1':
            subtitle = "Budget Performance On Fixed Operating Expenses ( "+filtertext+" - "+typetext+" )"
        elif report == '2':
            subtitle = "Budget Status By Department/Section ( " + filtertext + " - " + typetext + " )"
            data = query_bugdet_status_by_department(filter, type)

            list = []
            df = pd.DataFrame(data)
            #print df
            for id, expenses in df.fillna('NaN').groupby(['expenses', 'charttitle']):
                #print expenses
                for exp, titledata in expenses.fillna('NaN').sort_values(by=['accountcode'], ascending=True).groupby(['charttitle']):
                    print exp
                    #print titledata

                #for main, subgroup in maingroup.fillna('NaN').sort_values(by=['subgroup_code'], ascending=True).groupby(['maingroup_code', 'maingroup_desc']):

        context = {
            "title": title,
            "subtitle": subtitle,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "username": request.user,
        }

        if report == '1':
            return Render.render('budgetreport/report_1.html', context)
        elif report == '2':
            return Render.render('budgetreport/report_2.html', context)
        else:
            return Render.render('budgetreport/report_1.html', context)

def query_bugdet_status_by_department(filter, type):
    print "raw query"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT chart.id , chart.main, chart.clas, chart.item, title.title AS charttitle, chart.description, chart.accountcode, " \
            "CASE " \
            "WHEN chart.clas =  1 THEN 'cost of sales' " \
            "WHEN chart.clas =  2 THEN 'general & administrative' " \
            "WHEN chart.clas =  3 THEN 'selling' " \
            "END AS expenses, " \
            "dept.code AS deptcode, dept.departmentname, deptbud.year, " \
            "deptbud.mjan, deptbud.mfeb, deptbud.mmar, deptbud.mapr,  deptbud.mmay,  deptbud.mjun, " \
            "deptbud.mjul, deptbud.maug, deptbud.msep, deptbud.moct, deptbud.mnov, deptbud.mdec, " \
            "curmon.year AS curmonyear, curmon.amount AS curmonamount, curmon.code AS curmoncode, " \
            "curyear.year AS curyear, curyear.amount AS curyearamount, curyear.code AS curyearcode, " \
            "prevyear.year AS prevyear, prevyear.amount AS prevyearmonthamount, prevyear.code AS prevyearmonthcode " \
            "FROM chartofaccount AS chart " \
            "LEFT OUTER JOIN chartofaccount AS title ON (title.main = chart.main AND title.clas = chart.clas AND title.item = chart.item AND title.cont = 0 AND title.sub = 000000 AND title.accounttype = 'T') " \
            "LEFT OUTER JOIN departmentbudget AS deptbud ON deptbud.chartofaccount_id = chart.id " \
            "LEFT OUTER JOIN department AS dept ON dept.id = deptbud.department_id " \
            "LEFT OUTER JOIN ( " \
            "SELECT a.year, a.month, a.amount, a.code, a.chartofaccount_id, a.department_id " \
            "FROM accountexpensebalance AS a " \
            "WHERE a.year = 2018 AND a.month = 3" \
            ") AS curmon ON (curmon.chartofaccount_id = deptbud.chartofaccount_id AND curmon.department_id = deptbud.department_id) " \
            "LEFT OUTER JOIN (" \
            "SELECT a.year, a.month, SUM(IF (a.code = 'C', (a.amount * -1), a.amount)) AS amount, a.code, a.chartofaccount_id, a.department_id " \
            "FROM accountexpensebalance AS a " \
            "WHERE a.year >= 2018 AND a.year <= 2018 " \
            "AND a.month >= 1 AND a.month <= 3 " \
            "GROUP BY a.chartofaccount_id, a.department_id" \
            ") AS curyear ON (curyear.chartofaccount_id = deptbud.chartofaccount_id AND curyear.department_id = deptbud.department_id) " \
            "LEFT OUTER JOIN ( " \
            "SELECT a.year, a.month, SUM(IF (a.code = 'C', (a.amount * -1), a.amount)) AS amount, a.code, a.chartofaccount_id, a.department_id " \
            "FROM accountexpensebalance AS a " \
            "WHERE a.year >= 2017 AND a.year <= 2017 " \
            "AND a.month >= 1 AND a.month <= 3 " \
            "GROUP BY a.chartofaccount_id, a.department_id" \
            ") AS prevyear ON (prevyear.chartofaccount_id = deptbud.chartofaccount_id AND prevyear.department_id = deptbud.department_id) " \
            "WHERE chart.main = 5 AND chart.accounttype = 'P' " \
            "AND dept.code IS NOT NULL " \
            "AND dept.id IN (22, 47) " \
            "ORDER BY chart.accountcode"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result