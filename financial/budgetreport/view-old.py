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
        department = request.GET['department']
        product = request.GET['product']
        title = "Budget Monitoring Report"
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

        accountcode = 0
        curmon_var = 0
        curmon_var_per = 0
        yearcur_var = 0
        yearcur_var_per = 0
        yearprev_var = 0
        yearprev_var_per = 0
        subtotal_curmon_bud = 0
        subtotal_curmon_act = 0
        subtotal_curmon_var = 0
        subtotal_curmon_var_per = 0
        subtotal_curyear_bud = 0
        subtotal_curyear_act = 0
        subtotal_curyear_var = 0
        subtotal_curyear_var_per = 0
        subtotal_prevyear_act = 0
        subtotal_prevyear_var = 0
        subtotal_prevyear_var_per = 0
        total_curmon_bud = 0
        total_curmon_act = 0
        total_curmon_var = 0
        total_curmon_var_per = 0
        total_curyear_bud = 0
        total_curyear_act = 0
        total_curyear_var = 0
        total_curyear_var_per = 0
        total_prevyear_act = 0
        total_prevyear_var = 0
        total_prevyear_var_per = 0

        counter = 0

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

        new_list = []

        if report == '1':
            subtitle = "Budget Performance On Fixed Operating Expenses ( "+filtertext+" - "+typetext+" )"
        elif report == '2':
            subtitle = "Budget Status By Department/Section ( " + filtertext + " - " + typetext + " )"
            data = query_bugdet_status_by_department(filter, type, fromyear, frommonth, toyear, tomonth, department, product)

            df = pd.DataFrame(data)

            if type == '2':
                for dept, department in df.fillna('NaN').sort_values(by=['deptcode', 'chartgroupaccountcode', 'chartsubgroupaccountcode', 'accountcode'], ascending=True).groupby(['deptcode', 'departmentname']):
                    total_curmon_bud = 0
                    total_curmon_act = 0
                    total_curmon_var = 0
                    total_curyear_bud = 0
                    total_curyear_act = 0
                    total_curyear_var = 0
                    total_prevyear_act = 0
                    total_prevyear_var = 0
                    total_prevyear_var_per = 0
                    for group, chartgroup in department.fillna('NaN').sort_values(by=['deptcode', 'chartgroupaccountcode', 'chartsubgroupaccountcode', 'accountcode'], ascending=True).groupby(['chartgroup']):
                        counter += 1
                        accountcode = 0
                        subtotal_curmon_bud = 0
                        subtotal_curmon_act = 0
                        subtotal_curmon_var = 0
                        subtotal_curyear_bud = 0
                        subtotal_curyear_act = 0
                        subtotal_curyear_var = 0
                        subtotal_prevyear_act = 0
                        subtotal_prevyear_var = 0
                        subtotal_prevyear_var_per = 0
                        for subgroup, chartsubgroup in chartgroup.sort_values(by=['accountcode'], ascending=True).groupby(['chartsubgroup']):

                            for data, item in chartsubgroup.iterrows():

                                budget = getBudget(tomonth, item)
                                curmon_var = float(item.actualcurmonamount) - float(budget[0])
                                if float(budget[0]):
                                    curmon_var_per = (float(curmon_var) / float(budget[0])) * 100
                                else:
                                    curmon_var_per = 0

                                yearcur_var = float(item.actualcuryearamount) - float(budget[1])
                                if float(budget[1]):
                                    yearcur_var_per = (float(yearcur_var) / float(budget[1]))* 100
                                else:
                                    yearcur_var_per = 0

                                yearprev_var = float(item.actualcuryearamount) - float(item.actualprevyearamount)
                                if float(item.actualprevyearamount):
                                    yearprev_var_per = (float(yearprev_var) / float(item.actualprevyearamount)) * 100
                                else:
                                    yearprev_var_per = 0

                                new_list.append({'chartgroup': group, 'chartsubgroup': subgroup, 'accountcode': item.accountcode,
                                                 'chartofaccount': item.description, 'deptcode': item.deptcode, 'department': item.departmentname,
                                                 'curmon_bud': budget[0], 'curmon_act': item.actualcurmonamount, 'curmon_var': curmon_var, 'curmon_var_per': curmon_var_per,
                                                 'yearcur_bud': budget[1], 'yearcur_act': item.actualcuryearamount, 'yearcur_var': yearcur_var, 'yearcur_var_per': yearcur_var_per,
                                                 'yearprev_act': item.actualprevyearamount, 'yearprev_var': yearprev_var, 'yearprev_var_per': yearprev_var_per, 'counter': counter})

                                subtotal_curmon_bud += budget[0]
                                subtotal_curmon_act += item.actualcurmonamount
                                subtotal_curmon_var += curmon_var
                                subtotal_curyear_bud +=  budget[1]
                                subtotal_curyear_act += item.actualcuryearamount
                                subtotal_curyear_var += yearcur_var
                                subtotal_prevyear_act += item.actualprevyearamount
                                subtotal_prevyear_var += yearprev_var

                                total_curmon_bud += budget[0]
                                total_curmon_act += item.actualcurmonamount
                                total_curmon_var += curmon_var
                                total_curyear_bud += budget[1]
                                total_curyear_act += item.actualcuryearamount
                                total_curyear_var += yearcur_var
                                total_prevyear_act += item.actualprevyearamount
                                total_prevyear_var += yearprev_var

                        if float(subtotal_curmon_bud):
                            subtotal_curmon_var_per = (float(subtotal_curmon_var) / float(subtotal_curmon_bud)) * 100
                        if float(subtotal_curyear_bud):
                            subtotal_curyear_var_per = (float(subtotal_curyear_var) / float(subtotal_curyear_bud))* 100
                        if float(subtotal_prevyear_act):
                            subtotal_prevyear_var_per = (float(subtotal_prevyear_var) / float(subtotal_prevyear_act)) * 100

                        new_list.append({'chartgroup': group, 'chartsubgroup': 'subtotal', 'accountcode': accountcode,
                                         'chartofaccount': 'subtotal', 'deptcode': dept[0], 'department': dept[1],
                                         'curmon_bud': subtotal_curmon_bud, 'curmon_act': subtotal_curmon_act, 'curmon_var': subtotal_curmon_var, 'curmon_var_per': subtotal_curmon_var_per,
                                         'yearcur_bud': subtotal_curyear_bud, 'yearcur_act': subtotal_curyear_act, 'yearcur_var': subtotal_curyear_var, 'yearcur_var_per': subtotal_curyear_var_per,
                                         'yearprev_act': subtotal_prevyear_act, 'yearprev_var': subtotal_prevyear_var, 'yearprev_var_per': subtotal_prevyear_var_per,
                                         'counter': counter + 1})

                    if float(total_curmon_bud):
                        total_curmon_var_per = (float(total_curmon_var) / float(total_curmon_bud)) * 100
                    if float(total_curyear_bud):
                        total_curyear_var_per = (float(total_curyear_var) / float(total_curyear_bud)) * 100
                    if float(total_prevyear_act):
                        total_prevyear_var_per = (float(total_prevyear_var) / float(total_prevyear_act)) * 100

                    new_list.append({'chartgroup': 'total', 'chartsubgroup': 'total', 'accountcode': accountcode,
                                     'chartofaccount': 'total', 'deptcode': dept[0], 'department': dept[1],
                                     'curmon_bud': total_curmon_bud, 'curmon_act': total_curmon_act, 'curmon_var': total_curmon_var, 'curmon_var_per': total_curmon_var_per,
                                     'yearcur_bud': total_curyear_bud, 'yearcur_act': total_curyear_act, 'yearcur_var': total_curyear_var, 'yearcur_var_per': total_curyear_var_per,
                                     'yearprev_act': total_prevyear_act, 'yearprev_var': total_prevyear_var, 'yearprev_var_per': total_prevyear_var_per,
                                     'counter': counter + 1})
            else:
                for dept, department in df.fillna('NaN').sort_values(by=['deptcode', 'chartgroupaccountcode', 'chartsubgroupaccountcode', 'accountcode'], ascending=True).groupby(['deptcode', 'departmentname']):
                    total_curmon_bud = 0
                    total_curmon_act = 0
                    total_curmon_var = 0
                    total_curyear_bud = 0
                    total_curyear_act = 0
                    total_curyear_var = 0
                    total_prevyear_act = 0
                    total_prevyear_var = 0
                    total_prevyear_var_per = 0
                    for group, chartgroup in department.fillna('NaN').sort_values(by=['accountcode'],ascending=True).groupby(['chartgroup']):
                        counter += 1
                        accountcode = 0
                        subtotal_curmon_bud = 0
                        subtotal_curmon_act = 0
                        subtotal_curmon_var = 0
                        subtotal_curyear_bud = 0
                        subtotal_curyear_act = 0
                        subtotal_curyear_var = 0
                        subtotal_prevyear_act = 0
                        subtotal_prevyear_var = 0
                        subtotal_prevyear_var_per = 0
                        for data, item in chartgroup.iterrows():
                            counter += 1
                            budget = getBudget(tomonth, item)

                            curmon_var = float(item.actualcurmonamount) - float(budget[0])
                            if float(budget[0]):
                                curmon_var_per = (float(curmon_var) / float(budget[0])) * 100
                            else:
                                curmon_var_per = 0

                            yearcur_var = float(item.actualcuryearamount) - float(budget[1])
                            if float(budget[1]):
                                yearcur_var_per = (float(yearcur_var) / float(budget[1])) * 100
                            else:
                                yearcur_var_per = 0

                            yearprev_var = float(item.actualcuryearamount) - float(item.actualprevyearamount)
                            if float(item.actualprevyearamount):
                                yearprev_var_per = (float(yearprev_var) / float(item.actualprevyearamount)) * 100
                            else:
                                yearprev_var_per = 0

                            new_list.append({'chartgroup': group, 'chartsubgroup': item.chartsubgroup, 'accountcode': item.accountcode,'chartofaccount': item.description,
                                             'deptcode': item.deptcode, 'department': item.departmentname,
                                             'curmon_bud': budget[0], 'curmon_act': item.actualcurmonamount, 'curmon_var': curmon_var, 'curmon_var_per': curmon_var_per,
                                             'yearcur_bud': budget[1], 'yearcur_act': item.actualcuryearamount, 'yearcur_var': yearcur_var, 'yearcur_var_per': yearcur_var_per,
                                             'yearprev_act': item.actualprevyearamount, 'yearprev_var': yearprev_var, 'yearprev_var_per': yearprev_var_per, 'counter': counter})

                            subtotal_curmon_bud += budget[0]
                            subtotal_curmon_act += item.actualcurmonamount
                            subtotal_curmon_var += curmon_var
                            subtotal_curyear_bud += budget[1]
                            subtotal_curyear_act += item.actualcuryearamount
                            subtotal_curyear_var += yearcur_var
                            subtotal_prevyear_act += item.actualprevyearamount
                            subtotal_prevyear_var += yearprev_var

                            total_curmon_bud += budget[0]
                            total_curmon_act += item.actualcurmonamount
                            total_curmon_var += curmon_var
                            total_curyear_bud += budget[1]
                            total_curyear_act += item.actualcuryearamount
                            total_curyear_var += yearcur_var
                            total_prevyear_act += item.actualprevyearamount
                            total_prevyear_var += yearprev_var

                        if float(subtotal_curmon_bud):
                            subtotal_curmon_var_per = (float(subtotal_curmon_var) / float(
                                subtotal_curmon_bud)) * 100
                        if float(subtotal_curyear_bud):
                            subtotal_curyear_var_per = (float(subtotal_curyear_var) / float(
                                subtotal_curyear_bud)) * 100
                        if float(subtotal_prevyear_act):
                            subtotal_prevyear_var_per = (float(subtotal_prevyear_var) / float(
                                subtotal_prevyear_act)) * 100

                        new_list.append({'chartgroup': group, 'chartsubgroup': 'subtotal', 'accountcode': accountcode,
                                         'chartofaccount': 'subtotal', 'deptcode': dept[0], 'department': dept[1],
                                         'curmon_bud': subtotal_curmon_bud, 'curmon_act': subtotal_curmon_act,
                                         'curmon_var': subtotal_curmon_var, 'curmon_var_per': subtotal_curmon_var_per,
                                         'yearcur_bud': subtotal_curyear_bud, 'yearcur_act': subtotal_curyear_act,
                                         'yearcur_var': subtotal_curyear_var, 'yearcur_var_per': subtotal_curyear_var_per,
                                         'yearprev_act': subtotal_prevyear_act, 'yearprev_var': subtotal_prevyear_var,
                                         'yearprev_var_per': subtotal_prevyear_var_per,
                                         'counter': counter + 1})

                    if float(total_curmon_bud):
                        total_curmon_var_per = (float(total_curmon_var) / float(total_curmon_bud)) * 100
                    if float(total_curyear_bud):
                        total_curyear_var_per = (float(total_curyear_var) / float(total_curyear_bud)) * 100
                    if float(total_prevyear_act):
                        total_prevyear_var_per = (float(total_prevyear_var) / float(total_prevyear_act)) * 100

                    new_list.append({'chartgroup': 'total', 'chartsubgroup': 'total', 'accountcode': accountcode,
                                     'chartofaccount': 'total', 'deptcode': dept[0], 'department': dept[1],
                                     'curmon_bud': total_curmon_bud, 'curmon_act': total_curmon_act, 'curmon_var': total_curmon_var, 'curmon_var_per': total_curmon_var_per,
                                     'yearcur_bud': total_curyear_bud, 'yearcur_act': total_curyear_act, 'yearcur_var': total_curyear_var, 'yearcur_var_per': total_curyear_var_per,
                                     'yearprev_act': total_prevyear_act, 'yearprev_var': total_prevyear_var, 'yearprev_var_per': total_prevyear_var_per,
                                     'counter': counter + 1})

        context = {
            "title": title,
            "subtitle": subtitle,
            "today": timezone.now(),
            "company": company,
            "list": new_list,
            "filtertext": filtertext,
            "typetext": typetext,
            "total": total,
            "username": request.user,
        }

        if report == '1':
            return Render.render('budgetreport/report_1.html', context)
        elif report == '2':
            if type == '2':
                return Render.render('budgetreport/report_2_d.html', context)
            else:
                return Render.render('budgetreport/report_2.html', context)
        else:
            return Render.render('budgetreport/report_1.html', context)

def getBudget(tomonth, item):
    if tomonth == 1:
        monbudget = float(item.mjan)
        yearbudget = float(item.mjan)
    elif tomonth == 2:
        monbudget = float(item.mfeb)
        yearbudget = float(item.mjan) + float(item.mfeb)
    elif tomonth == 3:
        monbudget = float(item.mmar)
        yearbudget = float(item.mjan) + float(item.mfeb) + float(item.mmar)
    elif tomonth == 4:
        monbudget = float(item.mapr)
        yearbudget = float(item.mjan) + float(item.mfeb) + float(item.mmar) + float(item.mapr)
    elif tomonth == 5:
        monbudget = float(item.mmay)
        yearbudget = float(item.mjan) + float(item.mfeb) + float(item.mmar) + float(item.mapr) + float(item.mmay)
    elif tomonth == 6:
        monbudget = float(item.mjun)
        yearbudget = float(item.mjan) + float(item.mfeb) + float(item.mmar) + float(item.mapr) + float(item.mmay) \
                     + float(item.mjun)
    elif tomonth == 7:
        monbudget = float(item.mjul)
        yearbudget = float(item.mjan) + float(item.mfeb) + float(item.mmar) + float(item.mapr) + float(item.mmay) \
                     + float(item.mjun) + float(item.mjul)
    elif tomonth == 8:
        monbudget = float(item.maug)
        yearbudget = float(item.mjan) + float(item.mfeb) + float(item.mmar) + float(item.mapr) + float(item.mmay) \
                     + float(item.mjun) + float(item.mjul) + float(item.maug)
    elif tomonth == 9:
        monbudget = float(item.msep)
        yearbudget = float(item.mjan) + float(item.mfeb) + float(item.mmar) + float(item.mapr) + float(item.mmay) \
                     + float(item.mjun) + float(item.mjul) + float(item.maug) + float(item.msep)
    elif tomonth == 10:
        monbudget = float(item.moct)
        yearbudget = float(item.mjan) + float(item.mfeb) + float(item.mmar) + float(item.mapr) + float(item.mmay) \
                     + float(item.mjun) + float(item.mjul) + float(item.maug) + float(item.msep) + float(item.moct)
    elif tomonth == 11:
        monbudget = float(item.mnov)
        yearbudget = float(item.mjan) + float(item.mfeb) + float(item.mmar) + float(item.mapr) + float(item.mmay) \
                     + float(item.mjun) + float(item.mjul) + float(item.maug) + float(item.msep) + float(item.moct) + float(item.mnov)
    elif tomonth == 12:
        monbudget = float(item.mdec)
        yearbudget = float(item.mjan) + float(item.mfeb) + float(item.mmar) + float(item.mapr) + float(item.mmay) \
                     + float(item.mjun) + float(item.mjul) + float(item.maug) + float(item.msep) + float(item.moct) + float(item.mnov) + float(item.mdec)
    else:
        monbudget = float(item.mjan)
        yearbudget = float(item.mjan)

    return [monbudget, yearbudget]

def query_bugdet_status_by_department(filter, type, fromyear, frommonth, toyear, tomonth, department, product):

    prevyear = int(toyear) - 1
    condepartment = ""
    condepartment2 = ""
    conproduc = ""
    contype = ""
    if department:
        condepartment = "AND deptbud.department_id IN (48,22)"
        condepartment2 = "AND acctbal.department_id IN (48,22)"
        #condepartment = "AND deptbud.department_id = "+str(department)+" "
        #condepartment2 = "AND acctbal.department_id = "+str(department)+" "
    if type == '2':
        print 'detailed'
        contype = "GROUP BY z.chartgroup, z.chartsubgroup, z.accountcode, z.deptcode"
    elif type == '1':
        print 'summary'
        contype = "GROUP BY z.chartgroup, z.chartsubgroup, z.deptcode"

    print "raw query"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT z.accountcode, z.chartgroup, z.chartgroupaccountcode, z.chartsubgroup, z.chartsubgroupaccountcode, " \
            "z.main, z.clas, z.item, z.cont, z.sub, z.description, " \
            "z.deptcode, z.departmentname, z.year, " \
            "z.mjan, z.mfeb, z.mmar, z.mapr,  z.mmay,  z.mjun, " \
            "z.mjul, z.maug, z.msep, z.moct, z.mnov, z.mdec, " \
            "SUM(IFNULL(z.actualcurmonamount, 0)) AS actualcurmonamount, SUM(IFNULL(z.actualcuryearamount, 0)) AS actualcuryearamount, SUM(IFNULL(z.actualprevyearamount, 0)) AS actualprevyearamount " \
            "FROM ( " \
            "SELECT chartgroup.title AS chartgroup, chartgroup.accountcode AS chartgroupaccountcode, chartsubgroup.title AS chartsubgroup, chartsubgroup.accountcode AS chartsubgroupaccountcode, " \
            "chart.main, chart.clas, chart.item, chart.cont, chart.sub, chart.accountcode, chart.description, " \
            "dept.code AS deptcode, dept.departmentname, deptbud.year, " \
            "deptbud.mjan, deptbud.mfeb, deptbud.mmar, deptbud.mapr,  deptbud.mmay,  deptbud.mjun, " \
            "deptbud.mjul, deptbud.maug, deptbud.msep, deptbud.moct, deptbud.mnov, deptbud.mdec, " \
            "actualcurmon.year AS actualcurmonyear, actualcurmon.month AS actualcurmonmonth, actualcurmon.amount AS actualcurmonamount, " \
            "'' AS actualcuryear, 0 AS actualcuryearamount, " \
            "'' AS actualprevyear, 0 AS actualprevyearamount " \
            "FROM chartofaccount AS chart " \
            "LEFT OUTER JOIN departmentbudget AS deptbud ON deptbud.chartofaccount_id = chart.id " \
            "LEFT OUTER JOIN department AS dept ON dept.id = deptbud.department_id " \
            "LEFT OUTER JOIN chartofaccount AS chartgroup ON (chartgroup.main = chart.main AND chartgroup.clas = chart.clas " \
            "AND chartgroup.item = chart.item AND chartgroup.cont = 0 " \
            "AND chartgroup.sub = 000000 AND chartgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS chartsubgroup ON (chartsubgroup.main = chart.main AND chartsubgroup.clas = chart.clas " \
            "AND chartsubgroup.item = chart.item AND chartsubgroup.cont = chart.cont " \
            "AND chartsubgroup.sub = RPAD(SUBSTR(chart.sub, 1, 1), 6, 0)) " \
            "LEFT OUTER JOIN ( " \
            "SELECT a.year, a.month, SUM(IF (a.code = 'C', (a.amount * -1), a.amount)) AS amount, a.code, a.chartofaccount_id, a.department_id " \
            "FROM accountexpensebalance AS a " \
            "WHERE a.year = "+str(toyear)+" AND a.month = "+str(tomonth)+" " \
            "GROUP BY a.chartofaccount_id, a.department_id " \
            ") AS actualcurmon ON (actualcurmon.chartofaccount_id = deptbud.chartofaccount_id AND actualcurmon.department_id = deptbud.department_id) " \
            "WHERE deptbud.isdeleted = 0 "+str(condepartment)+" " \
            "UNION " \
            "SELECT chartgroup.title AS chartgroup, chartgroup.accountcode AS chartgroupaccountcode, chartsubgroup.title AS chartsubgroup, chartsubgroup.accountcode AS chartsubgroupaccountcode, " \
            "chart.main, chart.clas, chart.item, chart.cont, chart.sub, chart.accountcode, chart.description, " \
            "dept.code AS deptcode, dept.departmentname, acctbal.year, " \
            "0 AS mjan, 0 AS mfeb, 0 AS mmar, 0 AS mapr, 0 AS mmay,  0 AS mjun, " \
            "0 AS mjul, 0 AS maug, 0 AS msep, 0 AS moct, 0 AS mnov, 0 AS mdec, " \
            "acctbal.year AS actualcurmonyear, "+str(tomonth)+" AS actualcurmonmonth, IFNULL(actualcurmon.amount, 0) AS actualcurmonamount, " \
            "acctbal.year AS actualcuryear, SUM(IF (acctbal.code = 'C', (acctbal.amount * -1), acctbal.amount)) AS actualcuryearamount, " \
            "'' AS actualprevyear, 0 AS actualprevyearamount " \
            "FROM chartofaccount AS chart " \
            "LEFT OUTER JOIN accountexpensebalance AS acctbal ON acctbal.chartofaccount_id = chart.id " \
            "LEFT OUTER JOIN department AS dept ON dept.id = acctbal.department_id " \
            "LEFT OUTER JOIN chartofaccount AS chartgroup ON (chartgroup.main = chart.main AND chartgroup.clas = chart.clas " \
            "AND chartgroup.item = chart.item AND chartgroup.cont = 0 " \
            "AND chartgroup.sub = 000000 AND chartgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS chartsubgroup ON (chartsubgroup.main = chart.main AND chartsubgroup.clas = chart.clas " \
            "AND chartsubgroup.item = chart.item AND chartsubgroup.cont = chart.cont " \
            "AND chartsubgroup.sub = RPAD(SUBSTR(chart.sub, 1, 1), 6, 0)) " \
            "LEFT OUTER JOIN (" \
            "SELECT a.id, a.year, a.month, (IF (a.code = 'C', (a.amount * -1), a.amount)) AS amount, a.code, a.chartofaccount_id, a.department_id " \
            "FROM accountexpensebalance AS a " \
            "WHERE a.year = 2018 AND a.month = 3 AND a.department_id = 48 " \
            "AND a.chartofaccount_id NOT IN(SELECT DISTINCT(chart.id) FROM chartofaccount AS chart " \
            "INNER JOIN departmentbudget AS deptbud ON deptbud.chartofaccount_id = chart.id WHERE a.isdeleted = 0 "+str(condepartment)+") " \
            "GROUP BY a.chartofaccount_id, a.department_id) AS actualcurmon ON (actualcurmon.chartofaccount_id = acctbal.chartofaccount_id AND actualcurmon.department_id = acctbal.department_id)	 " \
            "WHERE acctbal.year >= "+str(fromyear)+" AND acctbal.year <= "+str(toyear)+" " \
            "AND acctbal.month >= "+str(frommonth)+" AND acctbal.month <= "+str(tomonth)+" " \
            " "+str(condepartment2)+" " \
            "GROUP BY chartgroup.title, chartsubgroup.title, chart.accountcode, dept.code " \
            "UNION " \
            "SELECT chartgroup.title AS chartgroup, chartgroup.accountcode AS chartgroupaccountcode, chartsubgroup.title AS chartsubgroup, chartsubgroup.accountcode AS chartsubgroupaccountcode, " \
            "chart.main, chart.clas, chart.item, chart.cont, chart.sub, chart.accountcode, chart.description, " \
            "dept.code AS deptcode, dept.departmentname, acctbal.year, " \
            "0 AS mjan, 0 AS mfeb, 0 AS mmar, 0 AS mapr, 0 AS mmay,  0 AS mjun, " \
            "0 AS mjul, 0 AS maug, 0 AS msep, 0 AS moct, 0 AS mnov, 0 AS mdec, " \
            "'' AS actualcurmonyear, acctbal.month AS actualcurmonmonth, 0 AS actualcurmonamount, " \
            "'', 0 AS actualcuryearamount, " \
            "acctbal.year AS actualprevyear, SUM(IF (acctbal.code = 'C', (acctbal.amount * -1), acctbal.amount)) AS actualprevyearamount " \
            "FROM chartofaccount AS chart " \
            "LEFT OUTER JOIN accountexpensebalance AS acctbal ON acctbal.chartofaccount_id = chart.id " \
            "LEFT OUTER JOIN department AS dept ON dept.id = acctbal.department_id " \
            "LEFT OUTER JOIN chartofaccount AS chartgroup ON (chartgroup.main = chart.main AND chartgroup.clas = chart.clas " \
            "AND chartgroup.item = chart.item AND chartgroup.cont = 0 " \
            "AND chartgroup.sub = 000000 AND chartgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS chartsubgroup ON (chartsubgroup.main = chart.main AND chartsubgroup.clas = chart.clas " \
            "AND chartsubgroup.item = chart.item AND chartsubgroup.cont = chart.cont " \
            "AND chartsubgroup.sub = RPAD(SUBSTR(chart.sub, 1, 1), 6, 0)) " \
            "WHERE acctbal.year >= "+str(prevyear)+" AND acctbal.year <= "+str(prevyear)+" " \
            "AND acctbal.month >= "+str(frommonth)+" AND acctbal.month <= "+str(tomonth)+" " \
            " "+str(condepartment2)+" " \
            "GROUP BY chartgroup.title, chartsubgroup.title, chart.accountcode, dept.code) AS z " \
            "WHERE z.chartgroup IS NOT NULL " \
            " "+str(contype)+" " \
            "ORDER BY z.deptcode, z.accountcode , z.chartgroup, z.chartsubgroup"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result