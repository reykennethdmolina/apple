from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from companyparameter.models import Companyparameter
from django.db import connection
from accountexpensebalance.models import Accountexpensebalance
from department.models import Department
from departmentbudget.models import Departmentbudget
from chartofaccount.models import Chartofaccount
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
from django.http import HttpResponse, JsonResponse
import pandas as pd
from datetime import timedelta
import io
import xlsxwriter
import datetime
from django.template.loader import render_to_string
from operator import itemgetter

@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    model = Accountexpensebalance
    template_name = 'budgetreport/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        context['product'] = Product.objects.filter(isdeleted=0).order_by('description')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        context['expense'] = Chartofaccount.objects.filter(isdeleted=0, accounttype='T', pk__in=[527, 643, 745]).order_by('accountcode')

        return context

@method_decorator(login_required, name='dispatch')
class DeptBudgetInquiry(TemplateView):
    model = Accountexpensebalance
    template_name = 'budgetreport/inquiry/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['chart'] = Chartofaccount.objects.filter(isdeleted=0, accounttype='P', main=5).order_by('accountcode')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')

        return context

def transgenerate(request):
    dto = request.GET["dto"]
    dfrom = request.GET["dfrom"]
    chart = request.GET["chart"]
    department = request.GET["department"]

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

    budget = Departmentbudget.objects.filter(isdeleted=0,year=toyear)

    if chart != '':
        budget = budget.filter(chartofaccount_id=chart)
        print 'budget'

    if department != '':
        budget = budget.filter(department_id=department)
        print 'department'

    #budget = getBudget(tomonth, item)
    totalbudget = 0
    for item in budget:
        budgetdata = getBudget(tomonth, item)
        totalbudget += budgetdata[1]

    data = query_transaction(dto, dfrom, chart, department)

    debit = 0
    credit = 0
    total = 0
    totalvariance = 0
    for item in data:
        debit += item.debitamount
        credit += item.creditamount

    total = float(debit) - float(credit)
    totalvariance = float(totalbudget) - float(total)

    context['result'] = data
    context['dto'] = dto
    context['dfrom'] = dfrom
    context['debit'] = debit
    context['credit'] = credit
    context['total'] = total
    viewhtml = render_to_string('budgetreport/inquiry/transaction_result.html', context)


    data = {
        'status': 'success',
        'viewhtml': viewhtml,
        'totalbudget': totalbudget,
        'totalactual': total,
        'totalvariance': totalvariance,
    }
    return JsonResponse(data)

# @method_decorator(login_required, name='dispatch')
# class GeneratePDF(View):
#     def get(self, request):
#         company = Companyparameter.objects.all().first()
#         list = []
#         total = []
#         report = request.GET['report']
#         filter = request.GET['filter']
#         type = request.GET['type']
#         dfrom = request.GET['from']
#         dto = request.GET['to']
#         department = request.GET['department']
#         product = request.GET['product']
#         title = "Budget Monitoring Report"
#         subtitle = ""
#         typetext = "Summary"
#         filtertext = "Cost of Sales"
#
#         ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
#         todate = datetime.date(int(ndto.year), int(ndto.month), 10)
#         toyear = todate.year
#         tomonth = todate.month
#         nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
#         fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
#         fromyear = fromdate.year
#         frommonth = fromdate.month
#
#         accountcode = 0
#         curmon_var = 0
#         curmon_var_per = 0
#         yearcur_var = 0
#         yearcur_var_per = 0
#         yearprev_var = 0
#         yearprev_var_per = 0
#         subtotal_curmon_bud = 0
#         subtotal_curmon_act = 0
#         subtotal_curmon_var = 0
#         subtotal_curmon_var_per = 0
#         subtotal_curyear_bud = 0
#         subtotal_curyear_act = 0
#         subtotal_curyear_var = 0
#         subtotal_curyear_var_per = 0
#         subtotal_prevyear_act = 0
#         subtotal_prevyear_var = 0
#         subtotal_prevyear_var_per = 0
#         total_curmon_bud = 0
#         total_curmon_act = 0
#         total_curmon_var = 0
#         total_curmon_var_per = 0
#         total_curyear_bud = 0
#         total_curyear_act = 0
#         total_curyear_var = 0
#         total_curyear_var_per = 0
#         total_prevyear_act = 0
#         total_prevyear_var = 0
#         total_prevyear_var_per = 0
#
#         counter = 0
#
#         list = Accountexpensebalance.objects.filter(isdeleted=0)[:0]
#
#         if filter == '1':
#             filtertext = "Cost of Sales"
#         elif filter == '2':
#             filtertext = "General & Administrative"
#         elif filter == '3':
#             filtertext = "Selling"
#         else:
#             filtertext = "All"
#
#         if type == '1':
#             typetext = "Summary"
#         else:
#             typetext = "Detailed"
#
#         new_list = []
#
#         if report == '1':
#             subtitle = "Budget Status By Department/Section ( " + filtertext + " - " + typetext + " )"
#             data = query_bugdet_status_by_department(filter, type, fromyear, frommonth, toyear, tomonth, department, product)
#
#             df = pd.DataFrame(data)
#
#             if type == '2':
#                 if data:
#                     for dept, department in df.fillna('NaN').sort_values(by=['deptcode', 'chartgroupaccountcode', 'chartsubgroupaccountcode', 'accountcode'], ascending=True).groupby(['deptcode', 'departmentname']):
#                         total_curmon_bud = 0
#                         total_curmon_act = 0
#                         total_curmon_var = 0
#                         total_curyear_bud = 0
#                         total_curyear_act = 0
#                         total_curyear_var = 0
#                         total_prevyear_act = 0
#                         total_prevyear_var = 0
#                         total_prevyear_var_per = 0
#                         for group, chartgroup in department.fillna('NaN').sort_values(by=['deptcode', 'chartgroupaccountcode', 'chartsubgroupaccountcode', 'accountcode'], ascending=True).groupby(['chartgroup']):
#                             counter += 1
#                             accountcode = 0
#                             subtotal_curmon_bud = 0
#                             subtotal_curmon_act = 0
#                             subtotal_curmon_var = 0
#                             subtotal_curyear_bud = 0
#                             subtotal_curyear_act = 0
#                             subtotal_curyear_var = 0
#                             subtotal_prevyear_act = 0
#                             subtotal_prevyear_var = 0
#                             subtotal_prevyear_var_per = 0
#                             for subgroup, chartsubgroup in chartgroup.sort_values(by=['accountcode'], ascending=True).groupby(['chartsubgroup']):
#
#                                 for data, item in chartsubgroup.iterrows():
#
#                                     budget = getBudget(tomonth, item)
#                                     curmon_var = float(item.actualcurmonamount) - float(budget[0])
#                                     if float(budget[0]):
#                                         curmon_var_per = (float(curmon_var) / float(budget[0])) * 100
#                                     else:
#                                         curmon_var_per = 0
#
#                                     yearcur_var = float(item.actualcuryearamount) - float(budget[1])
#                                     if float(budget[1]):
#                                         yearcur_var_per = (float(yearcur_var) / float(budget[1]))* 100
#                                     else:
#                                         yearcur_var_per = 0
#
#                                     yearprev_var = float(item.actualcuryearamount) - float(item.actualprevyearamount)
#                                     if float(item.actualprevyearamount):
#                                         yearprev_var_per = (float(yearprev_var) / float(item.actualprevyearamount)) * 100
#                                     else:
#                                         yearprev_var_per = 0
#
#                                     new_list.append({'chartgroup': group, 'chartsubgroup': subgroup, 'accountcode': item.accountcode,
#                                                      'chartofaccount': item.description, 'deptcode': item.deptcode, 'department': item.departmentname,
#                                                      'curmon_bud': budget[0], 'curmon_act': item.actualcurmonamount, 'curmon_var': curmon_var, 'curmon_var_per': curmon_var_per,
#                                                      'yearcur_bud': budget[1], 'yearcur_act': item.actualcuryearamount, 'yearcur_var': yearcur_var, 'yearcur_var_per': yearcur_var_per,
#                                                      'yearprev_act': item.actualprevyearamount, 'yearprev_var': yearprev_var, 'yearprev_var_per': yearprev_var_per, 'counter': counter})
#
#                                     subtotal_curmon_bud += budget[0]
#                                     subtotal_curmon_act += item.actualcurmonamount
#                                     subtotal_curmon_var += curmon_var
#                                     subtotal_curyear_bud +=  budget[1]
#                                     subtotal_curyear_act += item.actualcuryearamount
#                                     subtotal_curyear_var += yearcur_var
#                                     subtotal_prevyear_act += item.actualprevyearamount
#                                     subtotal_prevyear_var += yearprev_var
#
#                                     total_curmon_bud += budget[0]
#                                     total_curmon_act += item.actualcurmonamount
#                                     total_curmon_var += curmon_var
#                                     total_curyear_bud += budget[1]
#                                     total_curyear_act += item.actualcuryearamount
#                                     total_curyear_var += yearcur_var
#                                     total_prevyear_act += item.actualprevyearamount
#                                     total_prevyear_var += yearprev_var
#
#                             if float(subtotal_curmon_bud):
#                                 subtotal_curmon_var_per = (float(subtotal_curmon_var) / float(subtotal_curmon_bud)) * 100
#                             if float(subtotal_curyear_bud):
#                                 subtotal_curyear_var_per = (float(subtotal_curyear_var) / float(subtotal_curyear_bud))* 100
#                             if float(subtotal_prevyear_act):
#                                 subtotal_prevyear_var_per = (float(subtotal_prevyear_var) / float(subtotal_prevyear_act)) * 100
#
#                             new_list.append({'chartgroup': group, 'chartsubgroup': 'subtotal', 'accountcode': accountcode,
#                                              'chartofaccount': 'subtotal', 'deptcode': dept[0], 'department': dept[1],
#                                              'curmon_bud': subtotal_curmon_bud, 'curmon_act': subtotal_curmon_act, 'curmon_var': subtotal_curmon_var, 'curmon_var_per': subtotal_curmon_var_per,
#                                              'yearcur_bud': subtotal_curyear_bud, 'yearcur_act': subtotal_curyear_act, 'yearcur_var': subtotal_curyear_var, 'yearcur_var_per': subtotal_curyear_var_per,
#                                              'yearprev_act': subtotal_prevyear_act, 'yearprev_var': subtotal_prevyear_var, 'yearprev_var_per': subtotal_prevyear_var_per,
#                                              'counter': counter + 1})
#
#                         if float(total_curmon_bud):
#                             total_curmon_var_per = (float(total_curmon_var) / float(total_curmon_bud)) * 100
#                         if float(total_curyear_bud):
#                             total_curyear_var_per = (float(total_curyear_var) / float(total_curyear_bud)) * 100
#                         if float(total_prevyear_act):
#                             total_prevyear_var_per = (float(total_prevyear_var) / float(total_prevyear_act)) * 100
#
#                         new_list.append({'chartgroup': 'total', 'chartsubgroup': 'total', 'accountcode': accountcode,
#                                          'chartofaccount': 'total', 'deptcode': dept[0], 'department': dept[1],
#                                          'curmon_bud': total_curmon_bud, 'curmon_act': total_curmon_act, 'curmon_var': total_curmon_var, 'curmon_var_per': total_curmon_var_per,
#                                          'yearcur_bud': total_curyear_bud, 'yearcur_act': total_curyear_act, 'yearcur_var': total_curyear_var, 'yearcur_var_per': total_curyear_var_per,
#                                          'yearprev_act': total_prevyear_act, 'yearprev_var': total_prevyear_var, 'yearprev_var_per': total_prevyear_var_per,
#                                          'counter': counter + 1})
#             else:
#                 if data:
#                     for dept, department in df.fillna('NaN').sort_values(by=['deptcode', 'chartgroupaccountcode', 'chartsubgroupaccountcode', 'accountcode'], ascending=True).groupby(['deptcode', 'departmentname']):
#                         total_curmon_bud = 0
#                         total_curmon_act = 0
#                         total_curmon_var = 0
#                         total_curyear_bud = 0
#                         total_curyear_act = 0
#                         total_curyear_var = 0
#                         total_prevyear_act = 0
#                         total_prevyear_var = 0
#                         total_prevyear_var_per = 0
#                         for group, chartgroup in department.fillna('NaN').sort_values(by=['accountcode'],ascending=True).groupby(['chartgroup']):
#                             counter += 1
#                             accountcode = 0
#                             subtotal_curmon_bud = 0
#                             subtotal_curmon_act = 0
#                             subtotal_curmon_var = 0
#                             subtotal_curyear_bud = 0
#                             subtotal_curyear_act = 0
#                             subtotal_curyear_var = 0
#                             subtotal_prevyear_act = 0
#                             subtotal_prevyear_var = 0
#                             subtotal_prevyear_var_per = 0
#                             for data, item in chartgroup.iterrows():
#                                 counter += 1
#                                 budget = getBudget(tomonth, item)
#
#                                 curmon_var = float(item.actualcurmonamount) - float(budget[0])
#                                 if float(budget[0]):
#                                     curmon_var_per = (float(curmon_var) / float(budget[0])) * 100
#                                 else:
#                                     curmon_var_per = 0
#
#                                 yearcur_var = float(item.actualcuryearamount) - float(budget[1])
#                                 if float(budget[1]):
#                                     yearcur_var_per = (float(yearcur_var) / float(budget[1])) * 100
#                                 else:
#                                     yearcur_var_per = 0
#
#                                 yearprev_var = float(item.actualcuryearamount) - float(item.actualprevyearamount)
#                                 if float(item.actualprevyearamount):
#                                     yearprev_var_per = (float(yearprev_var) / float(item.actualprevyearamount)) * 100
#                                 else:
#                                     yearprev_var_per = 0
#
#                                 new_list.append({'chartgroup': group, 'chartsubgroup': item.chartsubgroup, 'accountcode': item.accountcode,'chartofaccount': item.description,
#                                                  'deptcode': item.deptcode, 'department': item.departmentname,
#                                                  'curmon_bud': budget[0], 'curmon_act': item.actualcurmonamount, 'curmon_var': curmon_var, 'curmon_var_per': curmon_var_per,
#                                                  'yearcur_bud': budget[1], 'yearcur_act': item.actualcuryearamount, 'yearcur_var': yearcur_var, 'yearcur_var_per': yearcur_var_per,
#                                                  'yearprev_act': item.actualprevyearamount, 'yearprev_var': yearprev_var, 'yearprev_var_per': yearprev_var_per, 'counter': counter})
#
#                                 subtotal_curmon_bud += budget[0]
#                                 subtotal_curmon_act += item.actualcurmonamount
#                                 subtotal_curmon_var += curmon_var
#                                 subtotal_curyear_bud += budget[1]
#                                 subtotal_curyear_act += item.actualcuryearamount
#                                 subtotal_curyear_var += yearcur_var
#                                 subtotal_prevyear_act += item.actualprevyearamount
#                                 subtotal_prevyear_var += yearprev_var
#
#                                 total_curmon_bud += budget[0]
#                                 total_curmon_act += item.actualcurmonamount
#                                 total_curmon_var += curmon_var
#                                 total_curyear_bud += budget[1]
#                                 total_curyear_act += item.actualcuryearamount
#                                 total_curyear_var += yearcur_var
#                                 total_prevyear_act += item.actualprevyearamount
#                                 total_prevyear_var += yearprev_var
#
#                             if float(subtotal_curmon_bud):
#                                 subtotal_curmon_var_per = (float(subtotal_curmon_var) / float(
#                                     subtotal_curmon_bud)) * 100
#                             if float(subtotal_curyear_bud):
#                                 subtotal_curyear_var_per = (float(subtotal_curyear_var) / float(
#                                     subtotal_curyear_bud)) * 100
#                             if float(subtotal_prevyear_act):
#                                 subtotal_prevyear_var_per = (float(subtotal_prevyear_var) / float(
#                                     subtotal_prevyear_act)) * 100
#
#                             new_list.append({'chartgroup': group, 'chartsubgroup': 'subtotal', 'accountcode': accountcode,
#                                              'chartofaccount': 'subtotal', 'deptcode': dept[0], 'department': dept[1],
#                                              'curmon_bud': subtotal_curmon_bud, 'curmon_act': subtotal_curmon_act,
#                                              'curmon_var': subtotal_curmon_var, 'curmon_var_per': subtotal_curmon_var_per,
#                                              'yearcur_bud': subtotal_curyear_bud, 'yearcur_act': subtotal_curyear_act,
#                                              'yearcur_var': subtotal_curyear_var, 'yearcur_var_per': subtotal_curyear_var_per,
#                                              'yearprev_act': subtotal_prevyear_act, 'yearprev_var': subtotal_prevyear_var,
#                                              'yearprev_var_per': subtotal_prevyear_var_per,
#                                              'counter': counter + 1})
#
#                         if float(total_curmon_bud):
#                             total_curmon_var_per = (float(total_curmon_var) / float(total_curmon_bud)) * 100
#                         if float(total_curyear_bud):
#                             total_curyear_var_per = (float(total_curyear_var) / float(total_curyear_bud)) * 100
#                         if float(total_prevyear_act):
#                             total_prevyear_var_per = (float(total_prevyear_var) / float(total_prevyear_act)) * 100
#
#                         new_list.append({'chartgroup': 'total', 'chartsubgroup': 'total', 'accountcode': accountcode,
#                                          'chartofaccount': 'total', 'deptcode': dept[0], 'department': dept[1],
#                                          'curmon_bud': total_curmon_bud, 'curmon_act': total_curmon_act, 'curmon_var': total_curmon_var, 'curmon_var_per': total_curmon_var_per,
#                                          'yearcur_bud': total_curyear_bud, 'yearcur_act': total_curyear_act, 'yearcur_var': total_curyear_var, 'yearcur_var_per': total_curyear_var_per,
#                                          'yearprev_act': total_prevyear_act, 'yearprev_var': total_prevyear_var, 'yearprev_var_per': total_prevyear_var_per,
#                                          'counter': counter + 1})
#         print report
#         context = {
#             "title": title,
#             "subtitle": subtitle,
#             "today": timezone.now(),
#             "company": company,
#             "list": new_list,
#             "filtertext": filtertext,
#             "typetext": typetext,
#             "total": total,
#             "username": request.user,
#         }
#
#         if report == '1':
#             if type == '2':
#                 return Render.render('budgetreport/report_2_d.html', context)
#             else:
#                 print 'dito'
#                 return Render.render('budgetreport/department_summary.html', context)
#         else:
#             return Render.render('budgetreport/report_1.html', context)

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
    conbudgroup = ""
    conproduc = ""
    contype = ""
    confilter = ""

    if filter == '1':
        confilter = "AND chart.main = 5 AND chart.clas = 1"
    elif filter == '2':
        confilter = "AND chart.main = 5 AND chart.clas = 2"
    else:
        confilter = "AND chart.main = 5 AND chart.clas = 3"

    if department:
        #condepartment = "AND deptbud.department_id IN (48,22)"
        #condepartment2 = "AND acctbal.department_id IN (48,22)"
        condepartment = "AND deptbud.department_id = "+str(department)+" "
        condepartment2 = "AND acctbal.department_id = "+str(department)+" "
    if type == '2':
        print 'detailed'
        contype = "GROUP BY z.chartgroup, z.chartsubgroup, z.accountcode, z.deptcode"
        conbudgroup = "GROUP BY chartgroup.title, chartsubgroup.title, chart.accountcode, dept.code"
    elif type == '1':
        print 'summary'
        contype = "GROUP BY z.chartgroup, z.chartsubgroup, z.deptcode"
        conbudgroup = "GROUP BY chartgroup.title, chartsubgroup.title, dept.code"

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
            "SUM(deptbud.mjan) AS mjan, SUM(deptbud.mfeb) AS mfeb, SUM(deptbud.mmar) AS mmar, SUM(deptbud.mapr) AS mapr,  SUM(deptbud.mmay) AS mmay,  SUM(deptbud.mjun) AS mjun, " \
            "SUM(deptbud.mjul) AS mjul, SUM(deptbud.maug) AS maug, SUM(deptbud.msep) AS msep, SUM(deptbud.moct) AS moct, SUM(deptbud.mnov) AS mnov, SUM(deptbud.mdec) AS mdec, " \
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
            " "+str(confilter)+" " \
            " "+str(conbudgroup)+" " \
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
            "SELECT acctbal.id, acctbal.year, acctbal.month, (IF (acctbal.code = 'C', (acctbal.amount * -1), acctbal.amount)) AS amount, acctbal.code, acctbal.chartofaccount_id, acctbal.department_id " \
            "FROM accountexpensebalance AS acctbal " \
            "WHERE acctbal.year = "+str(fromyear)+" AND acctbal.month = "+str(frommonth)+" "+str(condepartment2)+" " \
            "AND acctbal.chartofaccount_id NOT IN(SELECT DISTINCT(chart.id) FROM chartofaccount AS chart " \
            "INNER JOIN departmentbudget AS deptbud ON deptbud.chartofaccount_id = chart.id WHERE acctbal.isdeleted = 0 "+str(condepartment)+") " \
            "GROUP BY acctbal.chartofaccount_id, acctbal.department_id) AS actualcurmon ON (actualcurmon.chartofaccount_id = acctbal.chartofaccount_id AND actualcurmon.department_id = acctbal.department_id)	 " \
            "WHERE acctbal.year >= "+str(fromyear)+" AND acctbal.year <= "+str(toyear)+" " \
            "AND acctbal.month >= "+str(frommonth)+" AND acctbal.month <= "+str(tomonth)+" " \
            " "+str(confilter)+" " \
            " "+str(condepartment2)+" " \
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
            " "+str(confilter)+" " \
            " "+str(condepartment2)+" " \
            "GROUP BY chartgroup.title, chartsubgroup.title, chart.accountcode, dept.code) AS z " \
            "WHERE z.chartgroup IS NOT NULL " \
            " "+str(contype)+" " \
            "ORDER BY z.deptcode, z.accountcode , z.chartgroup, z.chartsubgroup"

    #print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


def query_transaction(dto, dfrom, chart, department):
    print "Transaction Query Department Budget"
    ''' Create query '''
    cursor = connection.cursor()

    chart_condition = ''
    department_condition = ''

    if chart != '':
        chart_condition = "AND d.chartofaccount_id = '" + str(chart) + "'"
    if department != '':
        department_condition = "AND d.department_id = '" + str(department) + "'"

    query = "SELECT z.tran, z.item_counter, z.ap_num AS tnum, z.ap_date AS tdate, z.debitamount, z.creditamount, z.balancecode, z.apstatus AS transtatus, z.status AS status, " \
            "z.particulars, bank.code AS bank, chart.accountcode, chart.description AS chartofaccount, cust.code AS custcode, cust.name AS customer, dept.code AS deptcode, dept.departmentname AS department, " \
            "emp.code AS empcode, CONCAT(IFNULL(emp.firstname, ''), ' ', IFNULL(emp.lastname, '')) AS employee, inpvat.code AS inpvatcode, inpvat.description AS inputvat, " \
            "outvat.code AS outvatcode, outvat.description AS outputvat, prod.code AS prodcode, prod.description AS product, " \
            "supp.code AS suppcode, supp.name AS supplier, vat.code AS vatcode, vat.description AS vat, wtax.code AS wtaxcode, wtax.description AS wtax " \
            "FROM ( " \
            "SELECT 'AP' AS tran, d.item_counter, d.ap_num, d.ap_date, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, m.particulars, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.apstatus, m.status " \
            "FROM apdetail AS d " \
            "LEFT OUTER JOIN apmain AS m ON m.id = d.apmain_id " \
            "WHERE DATE(d.ap_date) >= '"+str(dfrom)+"' AND DATE(d.ap_date) <= '"+str(dto)+"' AND m.apstatus = 'R' AND m.status = 'O' " \
            +str(chart_condition)+" "+str(department_condition)+"" \
            "UNION " \
            "SELECT 'CV' AS tran, d.item_counter, d.cv_num, d.cv_date, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, m.particulars, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.cvstatus, m.status	" \
            "FROM cvdetail AS d " \
            "LEFT OUTER JOIN cvmain AS m ON m.id = d.cvmain_id " \
            "WHERE DATE(d.cv_date) >= '"+str(dfrom)+"' AND DATE(d.cv_date) <= '"+str(dto)+"' AND m.cvstatus = 'R' AND m.status = 'O' " \
            +str(chart_condition)+" "+str(department_condition)+"" \
            "UNION " \
            "SELECT 'JV' AS tran, d.item_counter, d.jv_num, d.jv_date, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, m.particular," \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.jvstatus, m.status " \
            "FROM jvdetail AS d " \
            "LEFT OUTER JOIN jvmain AS m ON m.id = d.jvmain_id " \
            "WHERE DATE(d.jv_date) >= '"+str(dfrom)+"' AND DATE(d.jv_date) <= '"+str(dto)+"' AND m.jvstatus = 'R' AND m.status = 'O' " \
            +str(chart_condition)+" "+str(department_condition)+"" \
            "UNION " \
            "SELECT 'OR' AS tran, d.item_counter, m.ornum, m.ordate, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, m.particulars, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.orstatus, m.status " \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ordetail AS d ON m.id = d.ormain_id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' AND m.orstatus = 'R' AND m.status = 'O' " \
            +str(chart_condition)+" "+str(department_condition)+") AS z " \
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
            "LEFT OUTER JOIN wtax AS wtax ON wtax.id = z.wtax_id WHERE chart.main = 5 " \
            "ORDER BY z.tran, z.ap_num, z.ap_date, z.item_counter"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result


@method_decorator(login_required, name='dispatch')
class GenerateTransExcel(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        chartofaccount = []
        dept = []
        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]
        chart = request.GET["chart"]
        department = request.GET["department"]

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

        budget = Departmentbudget.objects.filter(isdeleted=0, year=toyear)

        if chart != '':
            budget = budget.filter(chartofaccount_id=chart)
            chartofaccount = Chartofaccount.objects.filter(isdeleted=0, id__exact=chart).first()
            print 'budget'

        if department != '':
            budget = budget.filter(department_id=department)
            dept = Department.objects.filter(isdeleted=0, id__exact=department).first()
            print 'department'

        # budget = getBudget(tomonth, item)
        totalbudget = 0
        for item in budget:
            budgetdata = getBudget(tomonth, item)
            totalbudget += budgetdata[1]

        title = "Department Budget"

        result = query_transaction(dto, dfrom, chart, department)


        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', 'DEPARTMENT BUDGET', bold)
        worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)

        if chartofaccount and  dept:
            worksheet.write('A3', 'Chart of Account', bold)
            worksheet.write('B3', chartofaccount.accountcode, bold)
            worksheet.write('C3', chartofaccount.description, bold)
            worksheet.write('A4', 'Department', bold)
            worksheet.write('B4', dept.code, bold)
            worksheet.write('C4', dept.departmentname, bold)
        elif chartofaccount:
            worksheet.write('A3', 'Chart of Account', bold)
            worksheet.write('B3', chartofaccount.accountcode, bold)
            worksheet.write('C3', chartofaccount.description, bold)
        elif dept:
            worksheet.write('A3', 'Department', bold)
            worksheet.write('B3', dept.code, bold)
            worksheet.write('C3', dept.departmentname, bold)
        else:
            worksheet.write('A3', 'ALL Transaction', bold)

        # header
        worksheet.write('A6', 'Date', bold)
        worksheet.write('B6', 'Type', bold)
        worksheet.write('C6', 'Number', bold)
        worksheet.write('D6', 'Dept', bold)
        worksheet.write('E6', 'Account Code', bold)
        worksheet.write('F6', 'Chart of Account', bold)
        worksheet.write('G6', 'Particulars', bold)
        worksheet.write('H6', 'Debit Amount', bold)
        worksheet.write('I6', 'Credit Amount', bold)

        row = 7
        col = 0
        debit = 0
        credit = 0
        total = 0
        totalvariance = 0

        for data in result:
            debit += data.debitamount
            credit += data.creditamount
            worksheet.write(row, col, data.tdate, formatdate)
            worksheet.write(row, col + 1, data.tran)
            worksheet.write(row, col + 2, data.tnum)
            worksheet.write(row, col + 3, data.deptcode)
            worksheet.write(row, col + 4, data.accountcode)
            worksheet.write(row, col + 5, data.chartofaccount)
            worksheet.write(row, col + 6, data.particulars)
            worksheet.write(row, col + 7, float(format(data.debitamount, '.2f')))
            worksheet.write(row, col + 8, float(format(data.creditamount, '.2f')))

            row += 1

        total = float(debit) - float(credit)
        totalvariance = float(totalbudget) - float(total)

        worksheet.write(row, col + 6, 'Total', bold)
        worksheet.write(row, col + 7, float(format(debit, '.2f')), bold)
        worksheet.write(row, col + 8, float(format(credit, '.2f')), bold)

        worksheet.write(row+1, col + 6, 'NET Amount', bold)
        if debit > credit:
            worksheet.write(row+1, col + 7, float(format(total, '.2f')), bold)
            worksheet.write(row+1, col + 8, float(format(0, '.2f')), bold)
        else:
            worksheet.write(row + 1, col + 7, float(format(0, '.2f')), bold)
            worksheet.write(row + 1, col + 8, float(format(total, '.2f')), bold)

        worksheet.write('A5', 'Budget Amount', bold)
        worksheet.write('B5', float(format(totalbudget, '.2f')), bold)
        worksheet.write('C5', 'Actual Amount', bold)
        worksheet.write('D5', float(format(total, '.2f')), bold)
        worksheet.write('E5', 'Variance Amount', bold)
        worksheet.write('F5', float(format(totalvariance, '.2f')), bold)

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = "departmentbudget.xlsx"
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response

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

        prevdate = datetime.date(int(fromyear), int(frommonth), 10) - timedelta(days=15)
        prevyear = prevdate.year
        prevmonth = prevdate.month

        if filter == '527':
            filtertext = "Cost of Sales"
        elif filter == '643':
            filtertext = "General & Administrative"
        elif filter == '745':
            filtertext = "Selling Expense"
        else:
            filtertext = "All"

        if type == '1':
            typetext = "Summary"
        else:
            typetext = "Detailed"

        list = []

        if report == '1':
            if type == '2':
                list = query_scheduled_expense_deptsection(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses - Department/Section - Detailed"
            else:
                list = query_scheduled_expense_deptsection(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses - Department/Section - Summary"
        elif report == '2':
            if type == '2':
                list = query_scheduled_expense_deptgroup(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses - Department Group - Detailed"
            else:
                list = query_scheduled_expense_deptgroup(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses - Department Group - Summary"
        elif report == '3':
            if type == '2':
                list = query_scheduled_expense_group(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses -  Group - Detailed"
            else:
                list = query_scheduled_expense_group(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses - Group - Summary"
        elif report == '9':
            if type == '2':
                list = query_scheduled_expense_yearend(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses -  Year-to-date - Detailed"
            else:
                list = query_scheduled_expense_yearend(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses - Year-to-date - Summary"

        # elif report == '4':
        #     if type == '2':
        #         list = query_sched_expense_row(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
        #         list = query_sched_expense_column(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
        #         title = "Schedule of Expenses - Detailed"
        #     else:
        #
        #         list_dept = query_sched_expense_dept(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
        #         dept = {}
        #         col_dept = ''
        #         for c in list_dept:
        #             if col_dept != c.dcode:
        #                 dept.update({c.id: c.departmentname, c.dcode: c.dcode})
        #             col_dept = c.dcode
        #         listx = query_sched_expense_row(dept, type, filter, department, product, fromyear, frommonth, toyear,tomonth, prevyear, prevmonth)
        #         title = "Schedule of Expenses - Summary"

        elif report == '5':
            if type == '2':
                list = query_budget_deptsection(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Department/Section - Detailed"
            else:
                list = query_budget_deptsection(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Department/Section - Summary"
        elif report == '6':
            if type == '2':
                list = query_budget_deptgroup(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Department Group - Detailed"
            else:
                list = query_budget_deptgroup(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Department Group - Summary"
        elif report == '7':
            if type == '2':
                list = query_budget_group(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Group - Detailed"
            else:
                list = query_budget_group(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Group - Summary"

        context = {
            "title": title,
            "subtitle": subtitle,
            "asof": ndto,
            "prevdate": prevdate,
            "curdate": nfrom,
            "company": company,
            "list": list,
            "filtertext": filtertext,
            "typetext": typetext,
            "total": total,
            "username": request.user,
        }

        if report == '1':
            if type == '2':
                print 'detail'
                return Render.render('budgetreport/schedule_expenses_department_section_detail.html', context)
            else:
                print 'summary'
                return Render.render('budgetreport/schedule_expenses_department_section_summary.html', context)
        elif report == '2':
            if type == '2':
                print 'detail'
                return Render.render('budgetreport/schedule_expenses_department_group_detail.html', context)
            else:
                print 'summary'
                return Render.render('budgetreport/schedule_expenses_department_group_summary.html', context)
        elif report == '3':
            if type == '2':
                print 'detail'
                return Render.render('budgetreport/schedule_expenses_group_detail.html', context)
            else:
                print 'summary'
                return Render.render('budgetreport/schedule_expenses_group_summary.html', context)

        elif report == '5':
            if type == '2':
                print 'detail'
                return Render.render('budgetreport/budget_department_section_detail.html', context)
            else:
                print 'summary'
                return Render.render('budgetreport/budget_department_section_summary.html', context)
        elif report == '6':
            if type == '2':
                print 'detail'
                return Render.render('budgetreport/budget_department_group_detail.html', context)
            else:
                print 'summary'
                return Render.render('budgetreport/budget_department_group_summary.html', context)
        elif report == '7':
            if type == '2':
                print 'detail'
                return Render.render('budgetreport/budget_group_detail.html', context)
            else:
                print 'summary'
                return Render.render('budgetreport/budget_group_summary.html', context)
        elif report == '9':
            if type == '2':
                print 'detail'
                return Render.render('budgetreport/schedule_expenses_yearend_detail.html', context)
            else:
                print 'summary'
                return Render.render('budgetreport/schedule_expenses_yearend_summary.html', context)
        else:
            return Render.render('budgetreport/department_summary.html', context)

@csrf_exempt
def generate(request):
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

    prevdate = datetime.date(int(fromyear), int(frommonth), 10) - timedelta(days=15)
    prevyear = prevdate.year
    prevmonth = prevdate.month

    if filter == '527':
        filtertext = "Cost of Sales"
    elif filter == '643':
        filtertext = "General & Administrative"
    elif filter == '745':
        filtertext = "Selling Expense"
    else:
        filtertext = "All"

    if type == '1':
        typetext = "Summary"
    else:
        typetext = "Detailed"

    list = []
    viewhtml = ''

    context = {
        "subtitle": subtitle,
        "asof": ndto,
        "prevdate": prevdate,
        "curdate": nfrom,
        "company": company,
        "list": list,
        "filtertext": filtertext,
        "typetext": typetext,
        "total": total,
        "username": request.user,
    }


    if report == '4':
        if type == '2':
            list_dept = query_sched_expense_dept(type, filter, department, product, fromyear, frommonth, toyear,
                                                 tomonth, prevyear, prevmonth)
            dept = {}
            deptname = {}
            col_dept = ''
            counter = 1
            for c in list_dept:
                if col_dept != c.dcode:
                    dept.update({c.id: c.departmentname})
                    deptname.update({c.id: c.departmentname})
                    counter += 1
                col_dept = c.dcode

            dept = sorted(dept.items(), key=lambda kv: (kv[0]))
            deptname = sorted(deptname.items(), key=lambda kv: (kv[0]))

            list = query_sched_expense_row(dept, type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
            title = "Schedule of Expenses - Detailed"
            context['title'] = title
            context['list'] = list
            context['dept'] = deptname
            context['counter'] = counter + 1
            context['counterminus'] = counter
            viewhtml = render_to_string('budgetreport/schedule_expenses_detail.html', context)
        else:

            list_dept = query_sched_expense_dept(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
            dept = {}
            deptname = {}
            col_dept = ''
            counter = 1
            for c in list_dept:
                if col_dept != c.dcode:
                    dept.update({c.id: c.departmentname})
                    deptname.update({c.id: c.departmentname})
                    counter += 1
                col_dept = c.dcode

            dept = sorted(dept.items(), key=lambda kv: (kv[0]))
            deptname = sorted(deptname.items(), key=lambda kv: (kv[0]))

            list = query_sched_expense_row(dept, type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
            title = "Schedule of Expenses - Summary"
            context['title'] = title
            context['list'] = list
            context['dept'] = deptname
            context['counter'] = counter + 1
            context['counterminus'] = counter
            viewhtml = render_to_string('budgetreport/schedule_expenses_summary.html', context)

    elif report == '8':
        if type == '2':
            list_dept = query_sched_expense_dept(type, filter, department, product, fromyear, frommonth, toyear,
                                                 tomonth, prevyear, prevmonth)
            dept = {}
            deptname = {}
            col_dept = ''
            counter = 1
            for c in list_dept:
                if col_dept != c.dcode:
                    dept.update({c.id: c.departmentname})
                    deptname.update({c.id: c.departmentname})
                    counter += 1
                col_dept = c.dcode

            dept = sorted(dept.items(), key=lambda kv: (kv[0]))
            deptname = sorted(deptname.items(), key=lambda kv: (kv[0]))

            list = query_sched_expense_row(dept, type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
            title = "Schedule of Budget - Detailed"
            context['title'] = title
            context['list'] = list
            context['dept'] = deptname
            context['counter'] = counter + 1
            context['counterminus'] = counter
            viewhtml = render_to_string('budgetreport/schedule_expenses_detail.html', context)
        else:

            list_dept = query_sched_expense_dept(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
            dept = {}
            deptname = {}
            col_dept = ''
            counter = 1
            for c in list_dept:
                if col_dept != c.dcode:
                    dept.update({c.id: c.departmentname})
                    deptname.update({c.id: c.departmentname})
                    counter += 1
                col_dept = c.dcode

            dept = sorted(dept.items(), key=lambda kv: (kv[0]))
            deptname = sorted(deptname.items(), key=lambda kv: (kv[0]))

            list = query_sched_expense_row(dept, type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
            title = "Schedule of Budget - Summary"
            context['title'] = title
            context['list'] = list
            context['dept'] = deptname
            context['counter'] = counter + 1
            context['counterminus'] = counter
            viewhtml = render_to_string('budgetreport/schedule_expenses_summary.html', context)

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
        nfrommonth = nfrom.strftime("%B")
        fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
        fromyear = fromdate.year
        frommonth = fromdate.month

        prevdate = datetime.date(int(fromyear), int(frommonth), 10) - timedelta(days=15)
        prevyear = prevdate.year
        prevmonth = prevdate.month
        prevmon = prevdate.strftime("%B")

        if filter == '527':
            filtertext = "Cost of Sales"
        elif filter == '643':
            filtertext = "General & Administrative"
        elif filter == '745':
            filtertext = "Selling Expense"
        else:
            filtertext = "All"

        if type == '1':
            typetext = "Summary"
        else:
            typetext = "Detailed"

        list = []
        filename = "schedexpensesdepartmentbudget.xlsx"

        if report == '1':
            if type == '2':
                list = query_scheduled_expense_deptsection(type, filter, department, product, fromyear, frommonth, toyear, tomonth,
                                               prevyear, prevmonth)
                title = "Schedule of Expenses - Department/Section - Detailed"
                filename = "schedexpenses-budgetreport-department-section-detailed.xlsx"
            else:
                list = query_scheduled_expense_deptsection(type, filter, department, product, fromyear, frommonth, toyear, tomonth,
                                               prevyear, prevmonth)
                title = "Schedule of Expenses - Department/Section - Summary"
                filename = "schedexpenses-budgetreport-department-section-summary.xlsx"
        elif report == '2':
            if type == '2':
                list = query_scheduled_expense_deptgroup(type, filter, department, product, fromyear, frommonth, toyear, tomonth,
                                               prevyear, prevmonth)
                title = "Schedule of Expenses - Department Group - Detailed"
                filename = "schedexpenses-budgetreport-department-group-detailed.xlsx"
            else:
                list = query_scheduled_expense_deptgroup(type, filter, department, product, fromyear, frommonth, toyear, tomonth,
                                               prevyear, prevmonth)
                title = "Schedule of Expenses - Department Group - Summary"
                filename = "schedexpenses-budgetreport-department-group-summary.xlsx"
        elif report == '3':
            if type == '2':
                list = query_scheduled_expense_group(type, filter, department, product, fromyear, frommonth, toyear, tomonth,
                                               prevyear, prevmonth)
                title = "Schedule of Expenses - Group - Detailed"
                filename = "schedexpenses-budgetreport-group-detailed.xlsx"
            else:
                list = query_scheduled_expense_group(type, filter, department, product, fromyear, frommonth, toyear, tomonth,
                                               prevyear, prevmonth)
                title = "Schedule of Expenses - Group - Summary"
                filename = "schedexpenses-budgetreport-group-summary.xlsx"

        elif report == '9':
            if type == '2':
                list = query_scheduled_expense_yearend(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses -  Year-to-date - Detailed"
                filename = "schedexpenses-year-to-date-detailed.xlsx"
            else:
                list = query_scheduled_expense_yearend(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses - Year-to-date - Summary"
                filename = "schedexpenses-year-to-date-summary.xlsx"

        elif report == '4':
            list_dept = query_sched_expense_dept(type, filter, department, product, fromyear, frommonth, toyear,
                                                 tomonth, prevyear, prevmonth)
            dept = {}
            deptname = {}
            col_dept = ''
            counter = 1
            for c in list_dept:
                if col_dept != c.dcode:
                    dept.update({c.id: c.departmentname})
                    deptname.update({c.id: c.departmentname})
                    counter += 1
                col_dept = c.dcode

            dept = sorted(dept.items(), key=lambda kv: (kv[0]))
            deptname = sorted(deptname.items(), key=lambda kv: (kv[0]))

            if type == '2':
                list = query_sched_expense_row(dept, type, filter, department, product, fromyear, frommonth, toyear,
                                               tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses - Detailed"
                filename = "schedexpenses-detailed.xlsx"
            else:
                list = query_sched_expense_row(dept, type, filter, department, product, fromyear, frommonth, toyear,
                                               tomonth, prevyear, prevmonth)
                title = "Schedule of Expenses - Summary"
                filename = "schedexpenses-summary.xlsx"

        elif report == '5':
            if type == '2':
                list = query_budget_deptsection(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Department/Section - Detailed"
                filename = "budgetstatus-department-section-detailed.xlsx"
            else:
                list = query_budget_deptsection(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Department/Section - Summary"
                filename = "budgetstatus-department-section-summary.xlsx"
        elif report == '6':
            if type == '2':
                list = query_budget_deptgroup(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Department Group - Detailed"
                filename = "budgetstatus-department-group-detailed.xlsx"
            else:
                list = query_budget_deptgroup(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Department Group - Summary"
                filename = "budgetstatus-department-group-summary.xlsx"
        elif report == '7':
            if type == '2':
                list = query_budget_group(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Group - Detailed"
                filename = "budgetstatus-group-detailed.xlsx"
            else:
                list = query_budget_group(type, filter, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth)
                title = "Budget Status - Group - Summary"
                filename = "budgetstatus-group-summary.xlsx"

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
        worksheet.write('A2', str(filtertext), bold)
        worksheet.write('A3', 'for the period of '+str(dfrom)+' to'+str(dto), bold)

        df = pd.DataFrame(list)
        if report == '1':

            # header
            worksheet.merge_range('B5:D5', '-------------------- actual --------------------', bold)

            worksheet.write('A6', '', bold)
            worksheet.write('B6', str(nfrommonth), bold)
            worksheet.write('C6', str(prevmon), bold)
            worksheet.write('D6', 'year-to-date', bold)
            worksheet.write('E6', 'variance over/(under)', bold)
            worksheet.write('F6', 'variance(%) over/(under)', bold)

            row = 6
            col = 0
            if list:
                if type == '1':
                    print 'summary'
                    for dept, department in df.fillna('NaN').groupby(['dcode', 'departmentname']):

                        worksheet.write(row, col, str(dept[0])+'-'+str(dept[1]), bold)
                        row += 1

                        for group, subgroup in department.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                            worksheet.write(row, col, str(group[0]), bold)
                            row += 1
                            totalcuramount = 0
                            totalprevamount = 0
                            totalytdamount = 0
                            totalvaramount = 0
                            totalvarpercent = 0
                            for head, headgroup in subgroup.fillna('NaN').groupby(['csubgrouptitle', 'csubgroupdescription']):
                                worksheet.write(row, col, '  '+str(head[0]), bold)
                                row += 1
                                subcuramount = 0
                                subprevamount = 0
                                subytdamount = 0
                                subvaramount = 0
                                subvarpercent = 0
                                for data, item in headgroup.iterrows():
                                    worksheet.write(row, col, '   '+str(item.csubheaddescription))
                                    worksheet.write(row, col + 1, float(format(item.curamount, '.2f')))
                                    worksheet.write(row, col + 2, float(format(item.prevamount, '.2f')))
                                    worksheet.write(row, col + 3, float(format(item.ytdamount, '.2f')))
                                    worksheet.write(row, col + 4, float(format(item.varamount, '.2f')))
                                    worksheet.write(row, col + 5, float(format(item.varpercent, '.2f')))
                                    subcuramount += item.curamount
                                    subprevamount += item.prevamount
                                    subytdamount += item.ytdamount
                                    subvaramount += item.varamount
                                    row += 1

                                if subprevamount > 0:
                                    subvarpercent = (subvaramount/subprevamount) * 100

                                worksheet.write(row, col, '  Subtotal - '+str(head[0]))
                                worksheet.write(row, col + 1, float(format(subcuramount, '.2f')))
                                worksheet.write(row, col + 2, float(format(subprevamount, '.2f')))
                                worksheet.write(row, col + 3, float(format(subytdamount, '.2f')))
                                worksheet.write(row, col + 4, float(format(subvaramount, '.2f')))
                                worksheet.write(row, col + 5, float(format(subvarpercent, '.2f')))

                                totalcuramount += subcuramount
                                totalprevamount += subprevamount
                                totalytdamount += subytdamount
                                totalvaramount += subvaramount

                                row += 1

                            if totalprevamount > 0:
                                totalvarpercent = (totalvaramount / totalprevamount) * 100

                            worksheet.write(row, col, 'Total - ' + str(group[0]))
                            worksheet.write(row, col + 1, float(format(totalcuramount, '.2f')))
                            worksheet.write(row, col + 2, float(format(totalprevamount, '.2f')))
                            worksheet.write(row, col + 3, float(format(totalytdamount, '.2f')))
                            worksheet.write(row, col + 4, float(format(totalvaramount, '.2f')))
                            worksheet.write(row, col + 5, float(format(totalvarpercent, '.2f')))
                            row += 1
                        row += 1
                else:
                    print 'detailed'
                    for dept, department in df.fillna('NaN').groupby(['dcode', 'departmentname']):

                        worksheet.write(row, col, str(dept[0])+'-'+str(dept[1]), bold)
                        row += 1

                        for group, subgroup in department.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                            worksheet.write(row, col, str(group[0]), bold)
                            row += 1

                            totalcuramount = 0
                            totalprevamount = 0
                            totalytdamount = 0
                            totalvaramount = 0
                            totalvarpercent = 0
                            for head, headgroup in subgroup.fillna('NaN').groupby(['csubgrouptitle', 'csubgroupdescription']):
                                worksheet.write(row, col, '  '+str(head[0]), bold)
                                row += 1

                                subcuramount = 0
                                subprevamount = 0
                                subytdamount = 0
                                subvaramount = 0
                                subvarpercent = 0
                                for subhead, subheadgroup in headgroup.fillna('NaN').groupby(['csubheadtitle', 'csubheaddescription']):
                                    worksheet.write(row, col, '    ' + str(subhead[0]), bold)
                                    row += 1
                                    for data, item in subheadgroup.iterrows():
                                        worksheet.write(row, col, '    ' + str(item.description))
                                        worksheet.write(row, col + 1, float(format(item.curamount, '.2f')))
                                        worksheet.write(row, col + 2, float(format(item.prevamount, '.2f')))
                                        worksheet.write(row, col + 3, float(format(item.ytdamount, '.2f')))
                                        worksheet.write(row, col + 4, float(format(item.varamount, '.2f')))
                                        worksheet.write(row, col + 5, float(format(item.varpercent, '.2f')))
                                        subcuramount += item.curamount
                                        subprevamount += item.prevamount
                                        subytdamount += item.ytdamount
                                        subvaramount += item.varamount
                                        row += 1

                                if subprevamount > 0:
                                    subvarpercent = (subvaramount/subprevamount) * 100

                                worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                                worksheet.write(row, col + 1, float(format(subcuramount, '.2f')))
                                worksheet.write(row, col + 2, float(format(subprevamount, '.2f')))
                                worksheet.write(row, col + 3, float(format(subytdamount, '.2f')))
                                worksheet.write(row, col + 4, float(format(subvaramount, '.2f')))
                                worksheet.write(row, col + 5, float(format(subvarpercent, '.2f')))

                                totalcuramount += subcuramount
                                totalprevamount += subprevamount
                                totalytdamount += subytdamount
                                totalvaramount += subvaramount
                                row += 1

                            if totalprevamount > 0:
                                totalvarpercent = (totalvaramount / totalprevamount) * 100

                            worksheet.write(row, col, '  Total - ' + str(group[0]))
                            worksheet.write(row, col + 1, float(format(totalcuramount, '.2f')))
                            worksheet.write(row, col + 2, float(format(totalprevamount, '.2f')))
                            worksheet.write(row, col + 3, float(format(totalytdamount, '.2f')))
                            worksheet.write(row, col + 4, float(format(totalvaramount, '.2f')))
                            worksheet.write(row, col + 5, float(format(totalvarpercent, '.2f')))
                            row += 1
                            row += 1

        elif report == '2':

            # header
            worksheet.merge_range('B5:D5', '-------------------- actual --------------------', bold)

            worksheet.write('A6', '', bold)
            worksheet.write('B6', str(nfrommonth), bold)
            worksheet.write('C6', str(prevmon), bold)
            worksheet.write('D6', 'year-to-date', bold)
            worksheet.write('E6', 'variance over/(under)', bold)
            worksheet.write('F6', 'variance(%) over/(under)', bold)

            row = 6
            col = 0
            if list:
                if type == '1':
                    print 'summary'
                    for dept, department in df.fillna('NaN').groupby(['groupname']):
                        worksheet.write(row, col, str(dept), bold)
                        row += 1

                        for group, subgroup in department.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                            worksheet.write(row, col, str(group[0]), bold)
                            row += 1

                            totalcuramount = 0
                            totalprevamount = 0
                            totalytdamount = 0
                            totalvaramount = 0
                            totalvarpercent = 0
                            for head, headgroup in subgroup.fillna('NaN').groupby(
                                    ['csubgrouptitle', 'csubgroupdescription']):
                                worksheet.write(row, col, '  ' + str(head[0]), bold)
                                row += 1
                                subcuramount = 0
                                subprevamount = 0
                                subytdamount = 0
                                subvaramount = 0
                                subvarpercent = 0
                                for data, item in headgroup.iterrows():
                                    worksheet.write(row, col, '   ' + str(item.csubheaddescription))
                                    worksheet.write(row, col + 1, float(format(item.curamount, '.2f')))
                                    worksheet.write(row, col + 2, float(format(item.prevamount, '.2f')))
                                    worksheet.write(row, col + 3, float(format(item.ytdamount, '.2f')))
                                    worksheet.write(row, col + 4, float(format(item.varamount, '.2f')))
                                    worksheet.write(row, col + 5, float(format(item.varpercent, '.2f')))
                                    subcuramount += item.curamount
                                    subprevamount += item.prevamount
                                    subytdamount += item.ytdamount
                                    subvaramount += item.varamount
                                    row += 1

                                if subprevamount > 0:
                                    subvarpercent = (subvaramount / subprevamount) * 100

                                worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                                worksheet.write(row, col + 1, float(format(subcuramount, '.2f')))
                                worksheet.write(row, col + 2, float(format(subprevamount, '.2f')))
                                worksheet.write(row, col + 3, float(format(subytdamount, '.2f')))
                                worksheet.write(row, col + 4, float(format(subvaramount, '.2f')))
                                worksheet.write(row, col + 5, float(format(subvarpercent, '.2f')))

                                totalcuramount += subcuramount
                                totalprevamount += subprevamount
                                totalytdamount += subytdamount
                                totalvaramount += subvaramount

                                row += 1

                        if totalprevamount > 0:
                            totalvarpercent = (totalvaramount / totalprevamount) * 100

                        worksheet.write(row, col, 'Total - ' + str(group[0]))
                        worksheet.write(row, col + 1, float(format(totalcuramount, '.2f')))
                        worksheet.write(row, col + 2, float(format(totalprevamount, '.2f')))
                        worksheet.write(row, col + 3, float(format(totalytdamount, '.2f')))
                        worksheet.write(row, col + 4, float(format(totalvaramount, '.2f')))
                        worksheet.write(row, col + 5, float(format(totalvarpercent, '.2f')))
                        row += 1
                        row += 1
                else:
                    print 'detailed'
                    for dept, department in df.fillna('NaN').groupby(['groupname']):

                        worksheet.write(row, col, str(dept), bold)
                        row += 1

                        for group, subgroup in department.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                            worksheet.write(row, col, str(group[0]), bold)
                            row += 1

                            totalcuramount = 0
                            totalprevamount = 0
                            totalytdamount = 0
                            totalvaramount = 0
                            totalvarpercent = 0
                            for head, headgroup in subgroup.fillna('NaN').groupby(
                                    ['csubgrouptitle', 'csubgroupdescription']):
                                worksheet.write(row, col, '  ' + str(head[0]), bold)
                                row += 1

                                subcuramount = 0
                                subprevamount = 0
                                subytdamount = 0
                                subvaramount = 0
                                subvarpercent = 0
                                for subhead, subheadgroup in headgroup.fillna('NaN').groupby(
                                        ['csubheadtitle', 'csubheaddescription']):
                                    worksheet.write(row, col, '    ' + str(subhead[0]), bold)
                                    row += 1
                                    for data, item in subheadgroup.iterrows():
                                        worksheet.write(row, col, '    ' + str(item.description))
                                        worksheet.write(row, col + 1, float(format(item.curamount, '.2f')))
                                        worksheet.write(row, col + 2, float(format(item.prevamount, '.2f')))
                                        worksheet.write(row, col + 3, float(format(item.ytdamount, '.2f')))
                                        worksheet.write(row, col + 4, float(format(item.varamount, '.2f')))
                                        worksheet.write(row, col + 5, float(format(item.varpercent, '.2f')))
                                        subcuramount += item.curamount
                                        subprevamount += item.prevamount
                                        subytdamount += item.ytdamount
                                        subvaramount += item.varamount
                                        row += 1

                                if subprevamount > 0:
                                    subvarpercent = (subvaramount / subprevamount) * 100

                                worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                                worksheet.write(row, col + 1, float(format(subcuramount, '.2f')))
                                worksheet.write(row, col + 2, float(format(subprevamount, '.2f')))
                                worksheet.write(row, col + 3, float(format(subytdamount, '.2f')))
                                worksheet.write(row, col + 4, float(format(subvaramount, '.2f')))
                                worksheet.write(row, col + 5, float(format(subvarpercent, '.2f')))

                                totalcuramount += subcuramount
                                totalprevamount += subprevamount
                                totalytdamount += subytdamount
                                totalvaramount += subvaramount
                                row += 1

                            if totalprevamount > 0:
                                totalvarpercent = (totalvaramount / totalprevamount) * 100

                            worksheet.write(row, col, '  Total - ' + str(group[0]))
                            worksheet.write(row, col + 1, float(format(totalcuramount, '.2f')))
                            worksheet.write(row, col + 2, float(format(totalprevamount, '.2f')))
                            worksheet.write(row, col + 3, float(format(totalytdamount, '.2f')))
                            worksheet.write(row, col + 4, float(format(totalvaramount, '.2f')))
                            worksheet.write(row, col + 5, float(format(totalvarpercent, '.2f')))
                            row += 1
                            row += 1

        elif report == '3':

            # header
            worksheet.merge_range('B5:D5', '-------------------- actual --------------------', bold)

            worksheet.write('A6', '', bold)
            worksheet.write('B6', str(nfrommonth), bold)
            worksheet.write('C6', str(prevmon), bold)
            worksheet.write('D6', 'year-to-date', bold)
            worksheet.write('E6', 'variance over/(under)', bold)
            worksheet.write('F6', 'variance(%) over/(under)', bold)

            row = 6
            col = 0
            if list:
                if type == '1':
                    print 'summary'
                    for group, subgroup in df.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                        worksheet.write(row, col, str(group[0]), bold)
                        row += 1

                        totalcuramount = 0
                        totalprevamount = 0
                        totalytdamount = 0
                        totalvaramount = 0
                        totalvarpercent = 0
                        for head, headgroup in subgroup.fillna('NaN').groupby(['csubgrouptitle', 'csubgroupdescription']):
                            worksheet.write(row, col, '  ' + str(head[0]), bold)
                            row += 1

                            subcuramount = 0
                            subprevamount = 0
                            subytdamount = 0
                            subvaramount = 0
                            subvarpercent = 0
                            for data, item in headgroup.iterrows():
                                worksheet.write(row, col, '   ' + str(item.csubheaddescription))
                                worksheet.write(row, col + 1, float(format(item.curamount, '.2f')))
                                worksheet.write(row, col + 2, float(format(item.prevamount, '.2f')))
                                worksheet.write(row, col + 3, float(format(item.ytdamount, '.2f')))
                                worksheet.write(row, col + 4, float(format(item.varamount, '.2f')))
                                worksheet.write(row, col + 5, float(format(item.varpercent, '.2f')))
                                subcuramount += item.curamount
                                subprevamount += item.prevamount
                                subytdamount += item.ytdamount
                                subvaramount += item.varamount
                                row += 1

                            if subprevamount > 0:
                                subvarpercent = (subvaramount / subprevamount) * 100

                            worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                            worksheet.write(row, col + 1, float(format(subcuramount, '.2f')))
                            worksheet.write(row, col + 2, float(format(subprevamount, '.2f')))
                            worksheet.write(row, col + 3, float(format(subytdamount, '.2f')))
                            worksheet.write(row, col + 4, float(format(subvaramount, '.2f')))
                            worksheet.write(row, col + 5, float(format(subvarpercent, '.2f')))

                            totalcuramount += subcuramount
                            totalprevamount += subprevamount
                            totalytdamount += subytdamount
                            totalvaramount += subvaramount

                            row += 1

                        if totalprevamount > 0:
                            totalvarpercent = (totalvaramount / totalprevamount) * 100

                        worksheet.write(row, col, 'Total - ' + str(group[0]))
                        worksheet.write(row, col + 1, float(format(totalcuramount, '.2f')))
                        worksheet.write(row, col + 2, float(format(totalprevamount, '.2f')))
                        worksheet.write(row, col + 3, float(format(totalytdamount, '.2f')))
                        worksheet.write(row, col + 4, float(format(totalvaramount, '.2f')))
                        worksheet.write(row, col + 5, float(format(totalvarpercent, '.2f')))
                        row += 1
                        row += 1

                else:
                    print 'detailed'
                    for group, subgroup in df.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                        worksheet.write(row, col, str(group[0]), bold)
                        row += 1

                        totalcuramount = 0
                        totalprevamount = 0
                        totalytdamount = 0
                        totalvaramount = 0
                        totalvarpercent = 0
                        for head, headgroup in subgroup.fillna('NaN').groupby(
                                ['csubgrouptitle', 'csubgroupdescription']):
                            worksheet.write(row, col, '  ' + str(head[0]), bold)
                            row += 1

                            subcuramount = 0
                            subprevamount = 0
                            subytdamount = 0
                            subvaramount = 0
                            subvarpercent = 0
                            for subhead, subheadgroup in headgroup.fillna('NaN').groupby(
                                    ['csubheadtitle', 'csubheaddescription']):
                                worksheet.write(row, col, '    ' + str(subhead[0]), bold)
                                row += 1
                                for data, item in subheadgroup.iterrows():
                                    worksheet.write(row, col, '    ' + str(item.description))
                                    worksheet.write(row, col + 1, float(format(item.curamount, '.2f')))
                                    worksheet.write(row, col + 2, float(format(item.prevamount, '.2f')))
                                    worksheet.write(row, col + 3, float(format(item.ytdamount, '.2f')))
                                    worksheet.write(row, col + 4, float(format(item.varamount, '.2f')))
                                    worksheet.write(row, col + 5, float(format(item.varpercent, '.2f')))
                                    subcuramount += item.curamount
                                    subprevamount += item.prevamount
                                    subytdamount += item.ytdamount
                                    subvaramount += item.varamount
                                    row += 1

                            if subprevamount > 0:
                                subvarpercent = (subvaramount / subprevamount) * 100

                            worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                            worksheet.write(row, col + 1, float(format(subcuramount, '.2f')))
                            worksheet.write(row, col + 2, float(format(subprevamount, '.2f')))
                            worksheet.write(row, col + 3, float(format(subytdamount, '.2f')))
                            worksheet.write(row, col + 4, float(format(subvaramount, '.2f')))
                            worksheet.write(row, col + 5, float(format(subvarpercent, '.2f')))

                            totalcuramount += subcuramount
                            totalprevamount += subprevamount
                            totalytdamount += subytdamount
                            totalvaramount += subvaramount
                            row += 1

                        if totalprevamount > 0:
                            totalvarpercent = (totalvaramount / totalprevamount) * 100

                        worksheet.write(row, col, '  Total - ' + str(group[0]))
                        worksheet.write(row, col + 1, float(format(totalcuramount, '.2f')))
                        worksheet.write(row, col + 2, float(format(totalprevamount, '.2f')))
                        worksheet.write(row, col + 3, float(format(totalytdamount, '.2f')))
                        worksheet.write(row, col + 4, float(format(totalvaramount, '.2f')))
                        worksheet.write(row, col + 5, float(format(totalvarpercent, '.2f')))
                        row += 1
                        row += 1

        elif report == '9':
            # header

            worksheet.write('A5', '', bold)
            worksheet.write('B5', 'January', bold)
            worksheet.write('C5', 'February', bold)
            worksheet.write('D5', 'March', bold)
            worksheet.write('E5', 'April', bold)
            worksheet.write('F5', 'May', bold)
            worksheet.write('G5', 'June', bold)
            worksheet.write('H5', 'July', bold)
            worksheet.write('I5', 'August', bold)
            worksheet.write('J5', 'September', bold)
            worksheet.write('K5', 'October', bold)
            worksheet.write('L5', 'November', bold)
            worksheet.write('M5', 'December', bold)
            worksheet.write('N5', 'Amount', bold)

            row = 6
            col = 0

            if list:
                if type == '1':
                    print 'summary'
                    for group, subgroup in df.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                        worksheet.write(row, col, str(group[0]), bold)
                        row += 1

                        totjan = 0
                        totfeb = 0
                        totmar = 0
                        totapr = 0
                        totmay = 0
                        totjun = 0
                        totjul = 0
                        totaug = 0
                        totsep = 0
                        totoct = 0
                        totnov = 0
                        totdec = 0
                        totamt = 0
                        for head, headgroup in subgroup.fillna('NaN').groupby(['csubgrouptitle', 'csubgroupdescription']):
                            worksheet.write(row, col, '  ' + str(head[0]), bold)
                            row += 1

                            subjan = 0
                            subfeb = 0
                            submar = 0
                            subapr = 0
                            submay = 0
                            subjun = 0
                            subjul = 0
                            subaug = 0
                            subsep = 0
                            suboct = 0
                            subnov = 0
                            subdec = 0
                            subamt = 0
                            for data, item in headgroup.iterrows():
                                worksheet.write(row, col, '   ' + str(item.csubheaddescription))
                                worksheet.write(row, col + 1, float(format(item.mjan, '.2f')))
                                worksheet.write(row, col + 2, float(format(item.mfeb, '.2f')))
                                worksheet.write(row, col + 3, float(format(item.mmar, '.2f')))
                                worksheet.write(row, col + 4, float(format(item.mapr, '.2f')))
                                worksheet.write(row, col + 5, float(format(item.mmay, '.2f')))
                                worksheet.write(row, col + 6, float(format(item.mjun, '.2f')))
                                worksheet.write(row, col + 7, float(format(item.mjul, '.2f')))
                                worksheet.write(row, col + 8, float(format(item.maug, '.2f')))
                                worksheet.write(row, col + 9, float(format(item.msep, '.2f')))
                                worksheet.write(row, col + 10, float(format(item.moct, '.2f')))
                                worksheet.write(row, col + 11, float(format(item.mnov, '.2f')))
                                worksheet.write(row, col + 12, float(format(item.mdec, '.2f')))
                                worksheet.write(row, col + 13, float(format(item.amount, '.2f')))
                                subjan += item.mjan
                                subfeb += item.mfeb
                                submar += item.mmar
                                subapr += item.mapr
                                submay += item.mmay
                                subjun += item.mjun
                                subjul += item.mjul
                                subaug += item.maug
                                subsep += item.msep
                                suboct += item.moct
                                subnov += item.mnov
                                subdec += item.mdec
                                subamt += item.amount
                                totjan += item.mjan
                                totfeb += item.mfeb
                                totmar += item.mmar
                                totapr += item.mapr
                                totmay += item.mmay
                                totjun += item.mjun
                                totjul += item.mjul
                                totaug += item.maug
                                totsep += item.msep
                                totoct += item.moct
                                totnov += item.mnov
                                totdec += item.mdec
                                totamt += item.amount
                                row += 1


                            worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                            worksheet.write(row, col + 1, float(format(subjan, '.2f')))
                            worksheet.write(row, col + 2, float(format(subfeb, '.2f')))
                            worksheet.write(row, col + 3, float(format(submar, '.2f')))
                            worksheet.write(row, col + 4, float(format(subapr, '.2f')))
                            worksheet.write(row, col + 5, float(format(submay, '.2f')))
                            worksheet.write(row, col + 6, float(format(subjun, '.2f')))
                            worksheet.write(row, col + 7, float(format(subjul, '.2f')))
                            worksheet.write(row, col + 8, float(format(subaug, '.2f')))
                            worksheet.write(row, col + 9, float(format(subsep, '.2f')))
                            worksheet.write(row, col + 10, float(format(suboct, '.2f')))
                            worksheet.write(row, col + 11, float(format(subnov, '.2f')))
                            worksheet.write(row, col + 12, float(format(subdec, '.2f')))
                            worksheet.write(row, col + 13, float(format(subamt, '.2f')))

                            row += 1

                        worksheet.write(row, col, 'Total - ' + str(group[0]))
                        worksheet.write(row, col + 1, float(format(totjan, '.2f')))
                        worksheet.write(row, col + 2, float(format(totfeb, '.2f')))
                        worksheet.write(row, col + 3, float(format(totmar, '.2f')))
                        worksheet.write(row, col + 4, float(format(totapr, '.2f')))
                        worksheet.write(row, col + 5, float(format(totmay, '.2f')))
                        worksheet.write(row, col + 6, float(format(totjun, '.2f')))
                        worksheet.write(row, col + 7, float(format(totjul, '.2f')))
                        worksheet.write(row, col + 8, float(format(totaug, '.2f')))
                        worksheet.write(row, col + 9, float(format(totsep, '.2f')))
                        worksheet.write(row, col + 10, float(format(totoct, '.2f')))
                        worksheet.write(row, col + 11, float(format(totnov, '.2f')))
                        worksheet.write(row, col + 12, float(format(totdec, '.2f')))
                        worksheet.write(row, col + 13, float(format(totamt, '.2f')))
                        row += 1

                        row += 1
                else:
                    print 'detailed'
                    for group, subgroup in df.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                        worksheet.write(row, col, str(group[0]), bold)
                        row += 1

                        totjan = 0
                        totfeb = 0
                        totmar = 0
                        totapr = 0
                        totmay = 0
                        totjun = 0
                        totjul = 0
                        totaug = 0
                        totsep = 0
                        totoct = 0
                        totnov = 0
                        totdec = 0
                        totamt = 0
                        for head, headgroup in subgroup.fillna('NaN').groupby(
                                ['csubgrouptitle', 'csubgroupdescription']):
                            worksheet.write(row, col, '  ' + str(head[0]), bold)
                            row += 1

                            subjan = 0
                            subfeb = 0
                            submar = 0
                            subapr = 0
                            submay = 0
                            subjun = 0
                            subjul = 0
                            subaug = 0
                            subsep = 0
                            suboct = 0
                            subnov = 0
                            subdec = 0
                            subamt = 0
                            for subhead, subheadgroup in headgroup.fillna('NaN').groupby(
                                    ['csubheadtitle', 'csubheaddescription']):
                                worksheet.write(row, col, '    ' + str(subhead[0]), bold)
                                row += 1
                                for data, item in subheadgroup.iterrows():
                                    worksheet.write(row, col, '    ' + str(item.description))
                                    worksheet.write(row, col + 1, float(format(item.mjan, '.2f')))
                                    worksheet.write(row, col + 2, float(format(item.mfeb, '.2f')))
                                    worksheet.write(row, col + 3, float(format(item.mmar, '.2f')))
                                    worksheet.write(row, col + 4, float(format(item.mapr, '.2f')))
                                    worksheet.write(row, col + 5, float(format(item.mmay, '.2f')))
                                    worksheet.write(row, col + 6, float(format(item.mjun, '.2f')))
                                    worksheet.write(row, col + 7, float(format(item.mjul, '.2f')))
                                    worksheet.write(row, col + 8, float(format(item.maug, '.2f')))
                                    worksheet.write(row, col + 9, float(format(item.msep, '.2f')))
                                    worksheet.write(row, col + 10, float(format(item.moct, '.2f')))
                                    worksheet.write(row, col + 11, float(format(item.mnov, '.2f')))
                                    worksheet.write(row, col + 12, float(format(item.mdec, '.2f')))
                                    worksheet.write(row, col + 13, float(format(item.amount, '.2f')))
                                    subjan += item.mjan
                                    subfeb += item.mfeb
                                    submar += item.mmar
                                    subapr += item.mapr
                                    submay += item.mmay
                                    subjun += item.mjun
                                    subjul += item.mjul
                                    subaug += item.maug
                                    subsep += item.msep
                                    suboct += item.moct
                                    subnov += item.mnov
                                    subdec += item.mdec
                                    subamt += item.amount
                                    totjan += item.mjan
                                    totfeb += item.mfeb
                                    totmar += item.mmar
                                    totapr += item.mapr
                                    totmay += item.mmay
                                    totjun += item.mjun
                                    totjul += item.mjul
                                    totaug += item.maug
                                    totsep += item.msep
                                    totoct += item.moct
                                    totnov += item.mnov
                                    totdec += item.mdec
                                    totamt += item.amount
                                    row += 1


                            worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                            worksheet.write(row, col + 1, float(format(subjan, '.2f')))
                            worksheet.write(row, col + 2, float(format(subfeb, '.2f')))
                            worksheet.write(row, col + 3, float(format(submar, '.2f')))
                            worksheet.write(row, col + 4, float(format(subapr, '.2f')))
                            worksheet.write(row, col + 5, float(format(submay, '.2f')))
                            worksheet.write(row, col + 6, float(format(subjun, '.2f')))
                            worksheet.write(row, col + 7, float(format(subjul, '.2f')))
                            worksheet.write(row, col + 8, float(format(subaug, '.2f')))
                            worksheet.write(row, col + 9, float(format(subsep, '.2f')))
                            worksheet.write(row, col + 10, float(format(suboct, '.2f')))
                            worksheet.write(row, col + 11, float(format(subnov, '.2f')))
                            worksheet.write(row, col + 12, float(format(subdec, '.2f')))
                            worksheet.write(row, col + 13, float(format(subamt, '.2f')))

                            row += 1

                        worksheet.write(row, col, '  Total - ' + str(group[0]))
                        worksheet.write(row, col + 1, float(format(totjan, '.2f')))
                        worksheet.write(row, col + 2, float(format(totfeb, '.2f')))
                        worksheet.write(row, col + 3, float(format(totmar, '.2f')))
                        worksheet.write(row, col + 4, float(format(totapr, '.2f')))
                        worksheet.write(row, col + 5, float(format(totmay, '.2f')))
                        worksheet.write(row, col + 6, float(format(totjun, '.2f')))
                        worksheet.write(row, col + 7, float(format(totjul, '.2f')))
                        worksheet.write(row, col + 8, float(format(totaug, '.2f')))
                        worksheet.write(row, col + 9, float(format(totsep, '.2f')))
                        worksheet.write(row, col + 10, float(format(totoct, '.2f')))
                        worksheet.write(row, col + 11, float(format(totnov, '.2f')))
                        worksheet.write(row, col + 12, float(format(totdec, '.2f')))
                        worksheet.write(row, col + 13, float(format(totamt, '.2f')))
                        row += 1
                        row += 1

        elif report == '4':

            # header
            worksheet.write('A5', '', bold)
            rowh = 5
            colh = 1
            subtotal = []
            grandtotal = []
            grandgrandtotal = 0
            for key, val in dept:
                worksheet.write(rowh,colh, val, bold)
                subtotal.append(0)
                grandtotal.append(0)
                colh += 1
            worksheet.write(rowh, colh, 'TOTAL', bold)

            row = 6
            col = 0
            if list:
                if type == '1':
                    print 'summary'
                    for deptx, department in df.fillna('NaN').groupby(['dcode', 'departmentname']):

                        for group, subgroup in department.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                            worksheet.write(row, col, str(group[0]), bold)
                            row += 1

                            for head, headgroup in subgroup.fillna('NaN').groupby(['csubgrouptitle', 'csubgroupdescription']):
                                worksheet.write(row, col, '  '+str(head[0]), bold)
                                row += 1

                                totaltotal = 0
                                for data, item in headgroup.iterrows():
                                    worksheet.write(row, col, '      '+str(item.csubheaddescription))
                                    colh = 1
                                    total = 0
                                    for key, val in dept:
                                        x = eval('item.col'+str(colh))
                                        subtotal[colh - 1] += x
                                        grandtotal[colh - 1] += x
                                        worksheet.write(row, colh, float(format(x, '.2f')))
                                        colh += 1
                                        total +=x
                                    worksheet.write(row, colh, float(format(total, '.2f')))
                                    totaltotal += total
                                    grandgrandtotal += total
                                    row += 1

                                worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                                colh = 0
                                for key, val in dept:
                                    worksheet.write(row, colh + 1, float(format(subtotal[colh], '.2f')))
                                    subtotal[colh] = 0
                                    colh += 1
                                worksheet.write(row, colh + 1, float(format(totaltotal, '.2f')))
                                row += 1

                            worksheet.write(row, col, 'Total - ' + str(group[0]))
                            colh = 0
                            for key, val in dept:
                                worksheet.write(row, colh + 1, float(format(grandtotal[colh], '.2f')))
                                colh += 1
                            worksheet.write(row, colh + 1, float(format(grandgrandtotal, '.2f')))
                            row += 1
                else:
                    print 'detailed'
                    for deptx, department in df.fillna('NaN').groupby(['dcode', 'departmentname']):

                        for group, subgroup in department.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                            worksheet.write(row, col, str(group[0]), bold)
                            row += 1

                            for head, headgroup in subgroup.fillna('NaN').groupby(['csubgrouptitle', 'csubgroupdescription']):
                                worksheet.write(row, col, '  ' + str(head[0]), bold)
                                row += 1

                                for subhead, subheadgroup in headgroup.fillna('NaN').groupby(['csubheadtitle', 'csubheaddescription']):
                                    worksheet.write(row, col, '    ' + str(subhead[0]), bold)
                                    row += 1

                                    totaltotal = 0
                                    for data, item in subheadgroup.iterrows():
                                        worksheet.write(row, col, '      ' + str(item.csubheaddescription))
                                        colh = 1
                                        total = 0
                                        for key, val in dept:
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

                                worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                                colh = 0
                                for key, val in dept:
                                    worksheet.write(row, colh + 1, float(format(subtotal[colh], '.2f')))
                                    subtotal[colh] = 0
                                    colh += 1
                                worksheet.write(row, colh + 1, float(format(totaltotal, '.2f')))
                                row += 1

                            worksheet.write(row, col, 'Total - ' + str(group[0]))
                            colh = 0
                            for key, val in dept:
                                worksheet.write(row, colh + 1, float(format(grandtotal[colh], '.2f')))
                                colh += 1
                            worksheet.write(row, colh + 1, float(format(grandgrandtotal, '.2f')))
                            row += 1

        elif report == '5':

            # header
            worksheet.write('A5', '', bold)
            worksheet.write('B5', '', bold)
            worksheet.merge_range('C5:E5', '---------- current month ----------', bold)
            worksheet.merge_range('F5:I5', '---------- current year -- year to date ----------', bold)
            worksheet.merge_range('J5:L5', '------- last year -- year to date -------', bold)


            worksheet.write('A6', '', bold)
            worksheet.write('B6', 'budget', bold)
            worksheet.write('C6', 'actual', bold)
            worksheet.write('D6', 'variance over/(under)', bold)
            worksheet.write('E6', 'variance(%) over/(under)', bold)
            worksheet.write('F6', 'budget', bold)
            worksheet.write('G6', 'actual', bold)
            worksheet.write('H6', 'variance over/(under)', bold)
            worksheet.write('I6', 'variance(%) over/(under)', bold)
            worksheet.write('J6', 'actual', bold)
            worksheet.write('K6', 'variance over/(under)', bold)
            worksheet.write('L6', 'variance(%) over/(under)', bold)

            row = 7
            col = 0
            if list:
                if type == '1':
                    print 'summary'
                    for dept, department in df.fillna('NaN').groupby(['dcode', 'departmentname']):

                        worksheet.write(row, col, str(dept[0])+'-'+str(dept[1]), bold)
                        row += 1

                        for group, subgroup in department.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                            worksheet.write(row, col, str(group[0]), bold)
                            row += 1
                            totalbudget = 0
                            totalactual = 0
                            totalvaramount = 0
                            totalvarpercent = 0
                            totalcur_budytd = 0
                            totalcur_actualytd = 0
                            totalcur_varamount = 0
                            totalcur_varpercent = 0
                            totallast_actualytd = 0
                            totallast_varamount = 0
                            totallast_varpercent = 0
                            for head, headgroup in subgroup.fillna('NaN').groupby(['csubgrouptitle', 'csubgroupdescription']):
                                worksheet.write(row, col, '  '+str(head[0]), bold)
                                row += 1
                                subbudget = 0
                                subactual = 0
                                subvaramount = 0
                                subvarpercent = 0
                                subcur_budytd = 0
                                subcur_actualytd = 0
                                subcur_varamount = 0
                                subcur_varpercent = 0
                                sublast_actualytd = 0
                                sublast_varamount = 0
                                sublast_varpercent = 0
                                for data, item in headgroup.iterrows():
                                    worksheet.write(row, col, '   '+str(item.csubheaddescription))
                                    worksheet.write(row, col + 1, float(format(item.budget, '.2f')))
                                    worksheet.write(row, col + 2, float(format(item.actual, '.2f')))
                                    worksheet.write(row, col + 3, float(format(item.varamount, '.2f')))
                                    worksheet.write(row, col + 4, float(format(item.varpercent, '.2f')))
                                    worksheet.write(row, col + 5, float(format(item.cur_budytd, '.2f')))
                                    worksheet.write(row, col + 6, float(format(item.cur_actualytd, '.2f')))
                                    worksheet.write(row, col + 7, float(format(item.cur_varamount, '.2f')))
                                    worksheet.write(row, col + 8, float(format(item.cur_varpercent, '.2f')))
                                    worksheet.write(row, col + 9, float(format(item.last_actualytd, '.2f')))
                                    worksheet.write(row, col + 10, float(format(item.last_varamount, '.2f')))
                                    worksheet.write(row, col + 11, float(format(item.last_varpercent, '.2f')))
                                    subbudget += item.budget
                                    subactual += item.actual
                                    subvaramount += item.varamount
                                    subcur_budytd += item.cur_budytd
                                    subcur_actualytd += item.cur_actualytd
                                    subcur_varamount += item.cur_varamount
                                    sublast_actualytd += item.last_actualytd
                                    sublast_varamount += item.last_varamount
                                    row += 1

                                if subbudget > 0:
                                    subvarpercent = (subvaramount/subbudget) * 100
                                if subcur_actualytd > 0:
                                    subcur_varpercent = (subcur_varamount/subcur_actualytd) * 100
                                if sublast_actualytd > 0:
                                    sublast_varpercent = (sublast_varamount/sublast_actualytd) * 100

                                worksheet.write(row, col, '  Subtotal - '+str(head[0]))
                                worksheet.write(row, col + 1, float(format(subbudget, '.2f')))
                                worksheet.write(row, col + 2, float(format(subactual, '.2f')))
                                worksheet.write(row, col + 3, float(format(subvaramount, '.2f')))
                                worksheet.write(row, col + 4, float(format(subvarpercent, '.2f')))
                                worksheet.write(row, col + 5, float(format(subcur_budytd, '.2f')))
                                worksheet.write(row, col + 6, float(format(subcur_actualytd, '.2f')))
                                worksheet.write(row, col + 7, float(format(subcur_varamount, '.2f')))
                                worksheet.write(row, col + 8, float(format(subcur_varpercent, '.2f')))
                                worksheet.write(row, col + 9, float(format(sublast_actualytd, '.2f')))
                                worksheet.write(row, col + 10, float(format(sublast_actualytd, '.2f')))
                                worksheet.write(row, col + 11, float(format(sublast_varpercent, '.2f')))

                                totalbudget += subbudget
                                totalactual += subactual
                                totalvaramount += subvaramount
                                totalvarpercent += subvarpercent
                                totalcur_budytd += subcur_budytd
                                totalcur_actualytd += subcur_actualytd
                                totalcur_varamount += subcur_varamount
                                totalcur_varpercent += subcur_varpercent
                                totallast_actualytd += sublast_actualytd
                                totallast_varamount += sublast_varamount
                                totallast_varpercent += sublast_varpercent

                                row += 1

                            if totalbudget > 0:
                                totalvarpercent = (totalvaramount / totalbudget) * 100
                            if totalcur_actualytd > 0:
                                totalcur_varpercent = (totalcur_varamount / totalcur_actualytd) * 100
                            if totallast_actualytd > 0:
                                totallast_varpercent = (totallast_varamount / totallast_actualytd) * 100

                            worksheet.write(row, col, 'Total - ' + str(group[0]))
                            worksheet.write(row, col + 1, float(format(totalbudget, '.2f')))
                            worksheet.write(row, col + 2, float(format(totalactual, '.2f')))
                            worksheet.write(row, col + 3, float(format(totalvaramount, '.2f')))
                            worksheet.write(row, col + 4, float(format(totalvarpercent, '.2f')))
                            worksheet.write(row, col + 5, float(format(totalcur_budytd, '.2f')))
                            worksheet.write(row, col + 6, float(format(totalcur_actualytd, '.2f')))
                            worksheet.write(row, col + 7, float(format(totalcur_varamount, '.2f')))
                            worksheet.write(row, col + 8, float(format(totalcur_varpercent, '.2f')))
                            worksheet.write(row, col + 9, float(format(totallast_actualytd, '.2f')))
                            worksheet.write(row, col + 10, float(format(totallast_varamount, '.2f')))
                            worksheet.write(row, col + 11, float(format(totallast_varpercent, '.2f')))
                            row += 1
                        row += 1
                else:
                    print 'detailed'
                    for dept, department in df.fillna('NaN').groupby(['dcode', 'departmentname']):

                        worksheet.write(row, col, str(dept[0])+'-'+str(dept[1]), bold)
                        row += 1

                        for group, subgroup in department.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                            worksheet.write(row, col, str(group[0]), bold)
                            row += 1

                            totalbudget = 0
                            totalactual = 0
                            totalvaramount = 0
                            totalvarpercent = 0
                            totalcur_budytd = 0
                            totalcur_actualytd = 0
                            totalcur_varamount = 0
                            totalcur_varpercent = 0
                            totallast_actualytd = 0
                            totallast_varamount = 0
                            totallast_varpercent = 0
                            for head, headgroup in subgroup.fillna('NaN').groupby(['csubgrouptitle', 'csubgroupdescription']):
                                worksheet.write(row, col, '  '+str(head[0]), bold)
                                row += 1

                                subbudget = 0
                                subactual = 0
                                subvaramount = 0
                                subvarpercent = 0
                                subcur_budytd = 0
                                subcur_actualytd = 0
                                subcur_varamount = 0
                                subcur_varpercent = 0
                                sublast_actualytd = 0
                                sublast_varamount = 0
                                sublast_varpercent = 0
                                for subhead, subheadgroup in headgroup.fillna('NaN').groupby(['csubheadtitle', 'csubheaddescription']):
                                    worksheet.write(row, col, '    ' + str(subhead[0]), bold)
                                    row += 1
                                    for data, item in subheadgroup.iterrows():
                                        worksheet.write(row, col, '   ' + str(item.description))
                                        worksheet.write(row, col + 1, float(format(item.budget, '.2f')))
                                        worksheet.write(row, col + 2, float(format(item.actual, '.2f')))
                                        worksheet.write(row, col + 3, float(format(item.varamount, '.2f')))
                                        worksheet.write(row, col + 4, float(format(item.varpercent, '.2f')))
                                        worksheet.write(row, col + 5, float(format(item.cur_budytd, '.2f')))
                                        worksheet.write(row, col + 6, float(format(item.cur_actualytd, '.2f')))
                                        worksheet.write(row, col + 7, float(format(item.cur_varamount, '.2f')))
                                        worksheet.write(row, col + 8, float(format(item.cur_varpercent, '.2f')))
                                        worksheet.write(row, col + 9, float(format(item.last_actualytd, '.2f')))
                                        worksheet.write(row, col + 10, float(format(item.last_varamount, '.2f')))
                                        worksheet.write(row, col + 11, float(format(item.last_varpercent, '.2f')))
                                        subbudget += item.budget
                                        subactual += item.actual
                                        subvaramount += item.varamount
                                        subcur_budytd += item.cur_budytd
                                        subcur_actualytd += item.cur_actualytd
                                        subcur_varamount += item.cur_varamount
                                        sublast_actualytd += item.last_actualytd
                                        sublast_varamount += item.last_varamount
                                        row += 1

                                if subbudget > 0:
                                    subvarpercent = (subvaramount/subbudget) * 100
                                if subcur_actualytd > 0:
                                    subcur_varpercent = (subcur_varamount/subcur_actualytd) * 100
                                if sublast_actualytd > 0:
                                    sublast_varpercent = (sublast_varamount/sublast_actualytd) * 100

                                worksheet.write(row, col, '  Subtotal - '+str(head[0]))
                                worksheet.write(row, col + 1, float(format(subbudget, '.2f')))
                                worksheet.write(row, col + 2, float(format(subactual, '.2f')))
                                worksheet.write(row, col + 3, float(format(subvaramount, '.2f')))
                                worksheet.write(row, col + 4, float(format(subvarpercent, '.2f')))
                                worksheet.write(row, col + 5, float(format(subcur_budytd, '.2f')))
                                worksheet.write(row, col + 6, float(format(subcur_actualytd, '.2f')))
                                worksheet.write(row, col + 7, float(format(subcur_varamount, '.2f')))
                                worksheet.write(row, col + 8, float(format(subcur_varpercent, '.2f')))
                                worksheet.write(row, col + 9, float(format(sublast_actualytd, '.2f')))
                                worksheet.write(row, col + 10, float(format(sublast_actualytd, '.2f')))
                                worksheet.write(row, col + 11, float(format(sublast_varpercent, '.2f')))

                                totalbudget += subbudget
                                totalactual += subactual
                                totalvaramount += subvaramount
                                totalvarpercent += subvarpercent
                                totalcur_budytd += subcur_budytd
                                totalcur_actualytd += subcur_actualytd
                                totalcur_varamount += subcur_varamount
                                totalcur_varpercent += subcur_varpercent
                                totallast_actualytd += sublast_actualytd
                                totallast_varamount += sublast_varamount
                                totallast_varpercent += sublast_varpercent

                                row += 1

                            if totalbudget > 0:
                                totalvarpercent = (totalvaramount / totalbudget) * 100
                            if totalcur_actualytd > 0:
                                totalcur_varpercent = (totalcur_varamount / totalcur_actualytd) * 100
                            if totallast_actualytd > 0:
                                totallast_varpercent = (totallast_varamount / totallast_actualytd) * 100

                            worksheet.write(row, col, 'Total - ' + str(group[0]))
                            worksheet.write(row, col + 1, float(format(totalbudget, '.2f')))
                            worksheet.write(row, col + 2, float(format(totalactual, '.2f')))
                            worksheet.write(row, col + 3, float(format(totalvaramount, '.2f')))
                            worksheet.write(row, col + 4, float(format(totalvarpercent, '.2f')))
                            worksheet.write(row, col + 5, float(format(totalcur_budytd, '.2f')))
                            worksheet.write(row, col + 6, float(format(totalcur_actualytd, '.2f')))
                            worksheet.write(row, col + 7, float(format(totalcur_varamount, '.2f')))
                            worksheet.write(row, col + 8, float(format(totalcur_varpercent, '.2f')))
                            worksheet.write(row, col + 9, float(format(totallast_actualytd, '.2f')))
                            worksheet.write(row, col + 10, float(format(totallast_varamount, '.2f')))
                            worksheet.write(row, col + 11, float(format(totallast_varpercent, '.2f')))
                            row += 1
                        row += 1

        elif report == '6':

            # header
            worksheet.write('A5', '', bold)
            worksheet.write('B5', '', bold)
            worksheet.merge_range('C5:E5', '---------- current month ----------', bold)
            worksheet.merge_range('F5:I5', '---------- current year -- year to date ----------', bold)
            worksheet.merge_range('J5:L5', '------- last year -- year to date -------', bold)

            worksheet.write('A6', '', bold)
            worksheet.write('B6', 'budget', bold)
            worksheet.write('C6', 'actual', bold)
            worksheet.write('D6', 'variance over/(under)', bold)
            worksheet.write('E6', 'variance(%) over/(under)', bold)
            worksheet.write('F6', 'budget', bold)
            worksheet.write('G6', 'actual', bold)
            worksheet.write('H6', 'variance over/(under)', bold)
            worksheet.write('I6', 'variance(%) over/(under)', bold)
            worksheet.write('J6', 'actual', bold)
            worksheet.write('K6', 'variance over/(under)', bold)
            worksheet.write('L6', 'variance(%) over/(under)', bold)

            row = 7
            col = 0
            if list:
                if type == '1':
                    print 'summary'
                    for dept, department in df.fillna('NaN').groupby(['groupname']):
                        worksheet.write(row, col, str(dept), bold)
                        row += 1

                        for group, subgroup in department.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                            worksheet.write(row, col, str(group[0]), bold)
                            row += 1

                            totalbudget = 0
                            totalactual = 0
                            totalvaramount = 0
                            totalvarpercent = 0
                            totalcur_budytd = 0
                            totalcur_actualytd = 0
                            totalcur_varamount = 0
                            totalcur_varpercent = 0
                            totallast_actualytd = 0
                            totallast_varamount = 0
                            totallast_varpercent = 0
                            for head, headgroup in subgroup.fillna('NaN').groupby(
                                    ['csubgrouptitle', 'csubgroupdescription']):
                                worksheet.write(row, col, '  ' + str(head[0]), bold)
                                row += 1
                                subbudget = 0
                                subactual = 0
                                subvaramount = 0
                                subvarpercent = 0
                                subcur_budytd = 0
                                subcur_actualytd = 0
                                subcur_varamount = 0
                                subcur_varpercent = 0
                                sublast_actualytd = 0
                                sublast_varamount = 0
                                sublast_varpercent = 0
                                for data, item in headgroup.iterrows():
                                    worksheet.write(row, col, '   ' + str(item.csubheaddescription))
                                    worksheet.write(row, col + 1, float(format(item.budget, '.2f')))
                                    worksheet.write(row, col + 2, float(format(item.actual, '.2f')))
                                    worksheet.write(row, col + 3, float(format(item.varamount, '.2f')))
                                    worksheet.write(row, col + 4, float(format(item.varpercent, '.2f')))
                                    worksheet.write(row, col + 5, float(format(item.cur_budytd, '.2f')))
                                    worksheet.write(row, col + 6, float(format(item.cur_actualytd, '.2f')))
                                    worksheet.write(row, col + 7, float(format(item.cur_varamount, '.2f')))
                                    worksheet.write(row, col + 8, float(format(item.cur_varpercent, '.2f')))
                                    worksheet.write(row, col + 9, float(format(item.last_actualytd, '.2f')))
                                    worksheet.write(row, col + 10, float(format(item.last_varamount, '.2f')))
                                    worksheet.write(row, col + 11, float(format(item.last_varpercent, '.2f')))
                                    subbudget += item.budget
                                    subactual += item.actual
                                    subvaramount += item.varamount
                                    subcur_budytd += item.cur_budytd
                                    subcur_actualytd += item.cur_actualytd
                                    subcur_varamount += item.cur_varamount
                                    sublast_actualytd += item.last_actualytd
                                    sublast_varamount += item.last_varamount
                                    row += 1

                                if subvaramount > 0:
                                    subvarpercent = (subvaramount/subbudget) * 100
                                if subcur_varamount > 0:
                                    subcur_varpercent = (subcur_varamount/subcur_actualytd) * 100
                                if sublast_varamount > 0:
                                    sublast_varpercent = (sublast_varamount/sublast_actualytd) * 100

                                worksheet.write(row, col, '  Subtotal - '+str(head[0]))
                                worksheet.write(row, col + 1, float(format(subbudget, '.2f')))
                                worksheet.write(row, col + 2, float(format(subactual, '.2f')))
                                worksheet.write(row, col + 3, float(format(subvaramount, '.2f')))
                                worksheet.write(row, col + 4, float(format(subvarpercent, '.2f')))
                                worksheet.write(row, col + 5, float(format(subcur_budytd, '.2f')))
                                worksheet.write(row, col + 6, float(format(subcur_actualytd, '.2f')))
                                worksheet.write(row, col + 7, float(format(subcur_varamount, '.2f')))
                                worksheet.write(row, col + 8, float(format(subcur_varpercent, '.2f')))
                                worksheet.write(row, col + 9, float(format(sublast_actualytd, '.2f')))
                                worksheet.write(row, col + 10, float(format(sublast_actualytd, '.2f')))
                                worksheet.write(row, col + 11, float(format(sublast_varpercent, '.2f')))

                                totalbudget += subbudget
                                totalactual += subactual
                                totalvaramount += subvaramount
                                totalvarpercent += subvarpercent
                                totalcur_budytd += subcur_budytd
                                totalcur_actualytd += subcur_actualytd
                                totalcur_varamount += subcur_varamount
                                totalcur_varpercent += subcur_varpercent
                                totallast_actualytd += sublast_actualytd
                                totallast_varamount += sublast_varamount
                                totallast_varpercent += sublast_varpercent

                                row += 1

                            if totalvarpercent > 0:
                                totalvarpercent = (totalvaramount / totalbudget) * 100
                            if totalcur_varpercent > 0:
                                totalcur_varpercent = (totalcur_varamount / totalcur_actualytd) * 100
                            if totallast_varpercent > 0:
                                totallast_varpercent = (totallast_varamount / totallast_actualytd) * 100

                            worksheet.write(row, col, 'Total - ' + str(group[0]))
                            worksheet.write(row, col + 1, float(format(totalbudget, '.2f')))
                            worksheet.write(row, col + 2, float(format(totalactual, '.2f')))
                            worksheet.write(row, col + 3, float(format(totalvaramount, '.2f')))
                            worksheet.write(row, col + 4, float(format(totalvarpercent, '.2f')))
                            worksheet.write(row, col + 5, float(format(totalcur_budytd, '.2f')))
                            worksheet.write(row, col + 6, float(format(totalcur_actualytd, '.2f')))
                            worksheet.write(row, col + 7, float(format(totalcur_varamount, '.2f')))
                            worksheet.write(row, col + 8, float(format(totalcur_varpercent, '.2f')))
                            worksheet.write(row, col + 9, float(format(totallast_actualytd, '.2f')))
                            worksheet.write(row, col + 10, float(format(totallast_varamount, '.2f')))
                            worksheet.write(row, col + 11, float(format(totallast_varpercent, '.2f')))
                            row += 1
                        row += 1
                else:
                    print 'detailed'
                    for dept, department in df.fillna('NaN').groupby(['groupname']):

                        worksheet.write(row, col, str(dept), bold)
                        row += 1

                        for group, subgroup in department.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                            worksheet.write(row, col, str(group[0]), bold)
                            row += 1

                            totalbudget = 0
                            totalactual = 0
                            totalvaramount = 0
                            totalvarpercent = 0
                            totalcur_budytd = 0
                            totalcur_actualytd = 0
                            totalcur_varamount = 0
                            totalcur_varpercent = 0
                            totallast_actualytd = 0
                            totallast_varamount = 0
                            totallast_varpercent = 0
                            for head, headgroup in subgroup.fillna('NaN').groupby(
                                    ['csubgrouptitle', 'csubgroupdescription']):
                                worksheet.write(row, col, '  ' + str(head[0]), bold)
                                row += 1

                                subbudget = 0
                                subactual = 0
                                subvaramount = 0
                                subvarpercent = 0
                                subcur_budytd = 0
                                subcur_actualytd = 0
                                subcur_varamount = 0
                                subcur_varpercent = 0
                                sublast_actualytd = 0
                                sublast_varamount = 0
                                sublast_varpercent = 0
                                for subhead, subheadgroup in headgroup.fillna('NaN').groupby(
                                        ['csubheadtitle', 'csubheaddescription']):
                                    worksheet.write(row, col, '    ' + str(subhead[0]), bold)
                                    row += 1
                                    for data, item in subheadgroup.iterrows():
                                        worksheet.write(row, col, '    ' + str(item.description))
                                        worksheet.write(row, col + 1, float(format(item.budget, '.2f')))
                                        worksheet.write(row, col + 2, float(format(item.actual, '.2f')))
                                        worksheet.write(row, col + 3, float(format(item.varamount, '.2f')))
                                        worksheet.write(row, col + 4, float(format(item.varpercent, '.2f')))
                                        worksheet.write(row, col + 5, float(format(item.cur_budytd, '.2f')))
                                        worksheet.write(row, col + 6, float(format(item.cur_actualytd, '.2f')))
                                        worksheet.write(row, col + 7, float(format(item.cur_varamount, '.2f')))
                                        worksheet.write(row, col + 8, float(format(item.cur_varpercent, '.2f')))
                                        worksheet.write(row, col + 9, float(format(item.last_actualytd, '.2f')))
                                        worksheet.write(row, col + 10, float(format(item.last_varamount, '.2f')))
                                        worksheet.write(row, col + 11, float(format(item.last_varpercent, '.2f')))
                                        subbudget += item.budget
                                        subactual += item.actual
                                        subvaramount += item.varamount
                                        subcur_budytd += item.cur_budytd
                                        subcur_actualytd += item.cur_actualytd
                                        subcur_varamount += item.cur_varamount
                                        sublast_actualytd += item.last_actualytd
                                        sublast_varamount += item.last_varamount
                                        row += 1

                                if subvaramount > 0:
                                    subvarpercent = (subvaramount/subbudget) * 100
                                if subcur_varamount > 0:
                                    subcur_varpercent = (subcur_varamount/subcur_actualytd) * 100
                                if sublast_varamount > 0:
                                    sublast_varpercent = (sublast_varamount/sublast_actualytd) * 100

                                worksheet.write(row, col, '  Subtotal - '+str(head[0]))
                                worksheet.write(row, col + 1, float(format(subbudget, '.2f')))
                                worksheet.write(row, col + 2, float(format(subactual, '.2f')))
                                worksheet.write(row, col + 3, float(format(subvaramount, '.2f')))
                                worksheet.write(row, col + 4, float(format(subvarpercent, '.2f')))
                                worksheet.write(row, col + 5, float(format(subcur_budytd, '.2f')))
                                worksheet.write(row, col + 6, float(format(subcur_actualytd, '.2f')))
                                worksheet.write(row, col + 7, float(format(subcur_varamount, '.2f')))
                                worksheet.write(row, col + 8, float(format(subcur_varpercent, '.2f')))
                                worksheet.write(row, col + 9, float(format(sublast_actualytd, '.2f')))
                                worksheet.write(row, col + 10, float(format(sublast_actualytd, '.2f')))
                                worksheet.write(row, col + 11, float(format(sublast_varpercent, '.2f')))

                                totalbudget += subbudget
                                totalactual += subactual
                                totalvaramount += subvaramount
                                totalvarpercent += subvarpercent
                                totalcur_budytd += subcur_budytd
                                totalcur_actualytd += subcur_actualytd
                                totalcur_varamount += subcur_varamount
                                totalcur_varpercent += subcur_varpercent
                                totallast_actualytd += sublast_actualytd
                                totallast_varamount += sublast_varamount
                                totallast_varpercent += sublast_varpercent

                                row += 1

                            if totalvarpercent > 0:
                                totalvarpercent = (totalvaramount / totalbudget) * 100
                            if totalcur_varpercent > 0:
                                totalcur_varpercent = (totalcur_varamount / totalcur_actualytd) * 100
                            if totallast_varpercent > 0:
                                totallast_varpercent = (totallast_varamount / totallast_actualytd) * 100

                            worksheet.write(row, col, 'Total - ' + str(group[0]))
                            worksheet.write(row, col + 1, float(format(totalbudget, '.2f')))
                            worksheet.write(row, col + 2, float(format(totalactual, '.2f')))
                            worksheet.write(row, col + 3, float(format(totalvaramount, '.2f')))
                            worksheet.write(row, col + 4, float(format(totalvarpercent, '.2f')))
                            worksheet.write(row, col + 5, float(format(totalcur_budytd, '.2f')))
                            worksheet.write(row, col + 6, float(format(totalcur_actualytd, '.2f')))
                            worksheet.write(row, col + 7, float(format(totalcur_varamount, '.2f')))
                            worksheet.write(row, col + 8, float(format(totalcur_varpercent, '.2f')))
                            worksheet.write(row, col + 9, float(format(totallast_actualytd, '.2f')))
                            worksheet.write(row, col + 10, float(format(totallast_varamount, '.2f')))
                            worksheet.write(row, col + 11, float(format(totallast_varpercent, '.2f')))
                            row += 1
                        row += 1

        elif report == '7':

            # header
            worksheet.write('A5', '', bold)
            worksheet.write('B5', '', bold)
            worksheet.merge_range('C5:E5', '---------- current month ----------', bold)
            worksheet.merge_range('F5:I5', '---------- current year -- year to date ----------', bold)
            worksheet.merge_range('J5:L5', '------- last year -- year to date -------', bold)

            worksheet.write('A6', '', bold)
            worksheet.write('B6', 'budget', bold)
            worksheet.write('C6', 'actual', bold)
            worksheet.write('D6', 'variance over/(under)', bold)
            worksheet.write('E6', 'variance(%) over/(under)', bold)
            worksheet.write('F6', 'budget', bold)
            worksheet.write('G6', 'actual', bold)
            worksheet.write('H6', 'variance over/(under)', bold)
            worksheet.write('I6', 'variance(%) over/(under)', bold)
            worksheet.write('J6', 'actual', bold)
            worksheet.write('K6', 'variance over/(under)', bold)
            worksheet.write('L6', 'variance(%) over/(under)', bold)

            row = 7
            col = 0
            if list:
                if type == '1':
                    print 'summary'
                    for group, subgroup in df.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                        worksheet.write(row, col, str(group[0]), bold)
                        row += 1

                        totalbudget = 0
                        totalactual = 0
                        totalvaramount = 0
                        totalvarpercent = 0
                        totalcur_budytd = 0
                        totalcur_actualytd = 0
                        totalcur_varamount = 0
                        totalcur_varpercent = 0
                        totallast_actualytd = 0
                        totallast_varamount = 0
                        totallast_varpercent = 0
                        for head, headgroup in subgroup.fillna('NaN').groupby(['csubgrouptitle', 'csubgroupdescription']):
                            worksheet.write(row, col, '  ' + str(head[0]), bold)
                            row += 1

                            subbudget = 0
                            subactual = 0
                            subvaramount = 0
                            subvarpercent = 0
                            subcur_budytd = 0
                            subcur_actualytd = 0
                            subcur_varamount = 0
                            subcur_varpercent = 0
                            sublast_actualytd = 0
                            sublast_varamount = 0
                            sublast_varpercent = 0
                            for data, item in headgroup.iterrows():
                                worksheet.write(row, col, '   ' + str(item.csubheaddescription))
                                worksheet.write(row, col + 1, float(format(item.budget, '.2f')))
                                worksheet.write(row, col + 2, float(format(item.actual, '.2f')))
                                worksheet.write(row, col + 3, float(format(item.varamount, '.2f')))
                                worksheet.write(row, col + 4, float(format(item.varpercent, '.2f')))
                                worksheet.write(row, col + 5, float(format(item.cur_budytd, '.2f')))
                                worksheet.write(row, col + 6, float(format(item.cur_actualytd, '.2f')))
                                worksheet.write(row, col + 7, float(format(item.cur_varamount, '.2f')))
                                worksheet.write(row, col + 8, float(format(item.cur_varpercent, '.2f')))
                                worksheet.write(row, col + 9, float(format(item.last_actualytd, '.2f')))
                                worksheet.write(row, col + 10, float(format(item.last_varamount, '.2f')))
                                worksheet.write(row, col + 11, float(format(item.last_varpercent, '.2f')))
                                subbudget += item.budget
                                subactual += item.actual
                                subvaramount += item.varamount
                                subcur_budytd += item.cur_budytd
                                subcur_actualytd += item.cur_actualytd
                                subcur_varamount += item.cur_varamount
                                sublast_actualytd += item.last_actualytd
                                sublast_varamount += item.last_varamount
                                row += 1

                            if subvaramount > 0:
                                subvarpercent = (subvaramount / subbudget) * 100
                            if subcur_varamount > 0:
                                subcur_varpercent = (subcur_varamount / subcur_actualytd) * 100
                            if sublast_varamount > 0:
                                sublast_varpercent = (sublast_varamount / sublast_actualytd) * 100

                            worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                            worksheet.write(row, col + 1, float(format(subbudget, '.2f')))
                            worksheet.write(row, col + 2, float(format(subactual, '.2f')))
                            worksheet.write(row, col + 3, float(format(subvaramount, '.2f')))
                            worksheet.write(row, col + 4, float(format(subvarpercent, '.2f')))
                            worksheet.write(row, col + 5, float(format(subcur_budytd, '.2f')))
                            worksheet.write(row, col + 6, float(format(subcur_actualytd, '.2f')))
                            worksheet.write(row, col + 7, float(format(subcur_varamount, '.2f')))
                            worksheet.write(row, col + 8, float(format(subcur_varpercent, '.2f')))
                            worksheet.write(row, col + 9, float(format(sublast_actualytd, '.2f')))
                            worksheet.write(row, col + 10, float(format(sublast_actualytd, '.2f')))
                            worksheet.write(row, col + 11, float(format(sublast_varpercent, '.2f')))

                            totalbudget += subbudget
                            totalactual += subactual
                            totalvaramount += subvaramount
                            totalvarpercent += subvarpercent
                            totalcur_budytd += subcur_budytd
                            totalcur_actualytd += subcur_actualytd
                            totalcur_varamount += subcur_varamount
                            totalcur_varpercent += subcur_varpercent
                            totallast_actualytd += sublast_actualytd
                            totallast_varamount += sublast_varamount
                            totallast_varpercent += sublast_varpercent

                            row += 1

                            if totalvarpercent > 0:
                                totalvarpercent = (totalvaramount / totalbudget) * 100
                            if totalcur_varpercent > 0:
                                totalcur_varpercent = (totalcur_varamount / totalcur_actualytd) * 100
                            if totallast_varpercent > 0:
                                totallast_varpercent = (totallast_varamount / totallast_actualytd) * 100

                            worksheet.write(row, col, 'Total - ' + str(group[0]))
                            worksheet.write(row, col + 1, float(format(totalbudget, '.2f')))
                            worksheet.write(row, col + 2, float(format(totalactual, '.2f')))
                            worksheet.write(row, col + 3, float(format(totalvaramount, '.2f')))
                            worksheet.write(row, col + 4, float(format(totalvarpercent, '.2f')))
                            worksheet.write(row, col + 5, float(format(totalcur_budytd, '.2f')))
                            worksheet.write(row, col + 6, float(format(totalcur_actualytd, '.2f')))
                            worksheet.write(row, col + 7, float(format(totalcur_varamount, '.2f')))
                            worksheet.write(row, col + 8, float(format(totalcur_varpercent, '.2f')))
                            worksheet.write(row, col + 9, float(format(totallast_actualytd, '.2f')))
                            worksheet.write(row, col + 10, float(format(totallast_varamount, '.2f')))
                            worksheet.write(row, col + 11, float(format(totallast_varpercent, '.2f')))
                            row += 1
                        row += 1

                else:
                    print 'detailed'
                    for group, subgroup in df.fillna('NaN').groupby(['cgrouptitle', 'cgroupdescription']):
                        worksheet.write(row, col, str(group[0]), bold)
                        row += 1

                        totalbudget = 0
                        totalactual = 0
                        totalvaramount = 0
                        totalvarpercent = 0
                        totalcur_budytd = 0
                        totalcur_actualytd = 0
                        totalcur_varamount = 0
                        totalcur_varpercent = 0
                        totallast_actualytd = 0
                        totallast_varamount = 0
                        totallast_varpercent = 0
                        for head, headgroup in subgroup.fillna('NaN').groupby(
                                ['csubgrouptitle', 'csubgroupdescription']):
                            worksheet.write(row, col, '  ' + str(head[0]), bold)
                            row += 1

                            subbudget = 0
                            subactual = 0
                            subvaramount = 0
                            subvarpercent = 0
                            subcur_budytd = 0
                            subcur_actualytd = 0
                            subcur_varamount = 0
                            subcur_varpercent = 0
                            sublast_actualytd = 0
                            sublast_varamount = 0
                            sublast_varpercent = 0
                            for subhead, subheadgroup in headgroup.fillna('NaN').groupby(
                                    ['csubheadtitle', 'csubheaddescription']):
                                worksheet.write(row, col, '    ' + str(subhead[0]), bold)
                                row += 1
                                for data, item in subheadgroup.iterrows():
                                    worksheet.write(row, col, '    ' + str(item.description))
                                    worksheet.write(row, col + 1, float(format(item.budget, '.2f')))
                                    worksheet.write(row, col + 2, float(format(item.actual, '.2f')))
                                    worksheet.write(row, col + 3, float(format(item.varamount, '.2f')))
                                    worksheet.write(row, col + 4, float(format(item.varpercent, '.2f')))
                                    worksheet.write(row, col + 5, float(format(item.cur_budytd, '.2f')))
                                    worksheet.write(row, col + 6, float(format(item.cur_actualytd, '.2f')))
                                    worksheet.write(row, col + 7, float(format(item.cur_varamount, '.2f')))
                                    worksheet.write(row, col + 8, float(format(item.cur_varpercent, '.2f')))
                                    worksheet.write(row, col + 9, float(format(item.last_actualytd, '.2f')))
                                    worksheet.write(row, col + 10, float(format(item.last_varamount, '.2f')))
                                    worksheet.write(row, col + 11, float(format(item.last_varpercent, '.2f')))
                                    subbudget += item.budget
                                    subactual += item.actual
                                    subvaramount += item.varamount
                                    subcur_budytd += item.cur_budytd
                                    subcur_actualytd += item.cur_actualytd
                                    subcur_varamount += item.cur_varamount
                                    sublast_actualytd += item.last_actualytd
                                    sublast_varamount += item.last_varamount
                                    row += 1

                            if subvaramount > 0:
                                subvarpercent = (subvaramount / subbudget) * 100
                            if subcur_varamount > 0:
                                subcur_varpercent = (subcur_varamount / subcur_actualytd) * 100
                            if sublast_varamount > 0:
                                sublast_varpercent = (sublast_varamount / sublast_actualytd) * 100

                            worksheet.write(row, col, '  Subtotal - ' + str(head[0]))
                            worksheet.write(row, col + 1, float(format(subbudget, '.2f')))
                            worksheet.write(row, col + 2, float(format(subactual, '.2f')))
                            worksheet.write(row, col + 3, float(format(subvaramount, '.2f')))
                            worksheet.write(row, col + 4, float(format(subvarpercent, '.2f')))
                            worksheet.write(row, col + 5, float(format(subcur_budytd, '.2f')))
                            worksheet.write(row, col + 6, float(format(subcur_actualytd, '.2f')))
                            worksheet.write(row, col + 7, float(format(subcur_varamount, '.2f')))
                            worksheet.write(row, col + 8, float(format(subcur_varpercent, '.2f')))
                            worksheet.write(row, col + 9, float(format(sublast_actualytd, '.2f')))
                            worksheet.write(row, col + 10, float(format(sublast_actualytd, '.2f')))
                            worksheet.write(row, col + 11, float(format(sublast_varpercent, '.2f')))

                            totalbudget += subbudget
                            totalactual += subactual
                            totalvaramount += subvaramount
                            totalvarpercent += subvarpercent
                            totalcur_budytd += subcur_budytd
                            totalcur_actualytd += subcur_actualytd
                            totalcur_varamount += subcur_varamount
                            totalcur_varpercent += subcur_varpercent
                            totallast_actualytd += sublast_actualytd
                            totallast_varamount += sublast_varamount
                            totallast_varpercent += sublast_varpercent

                            row += 1

                        if totalvarpercent > 0:
                            totalvarpercent = (totalvaramount / totalbudget) * 100
                        if totalcur_varpercent > 0:
                            totalcur_varpercent = (totalcur_varamount / totalcur_actualytd) * 100
                        if totallast_varpercent > 0:
                            totallast_varpercent = (totallast_varamount / totallast_actualytd) * 100

                        worksheet.write(row, col, 'Total - ' + str(group[0]))
                        worksheet.write(row, col + 1, float(format(totalbudget, '.2f')))
                        worksheet.write(row, col + 2, float(format(totalactual, '.2f')))
                        worksheet.write(row, col + 3, float(format(totalvaramount, '.2f')))
                        worksheet.write(row, col + 4, float(format(totalvarpercent, '.2f')))
                        worksheet.write(row, col + 5, float(format(totalcur_budytd, '.2f')))
                        worksheet.write(row, col + 6, float(format(totalcur_actualytd, '.2f')))
                        worksheet.write(row, col + 7, float(format(totalcur_varamount, '.2f')))
                        worksheet.write(row, col + 8, float(format(totalcur_varpercent, '.2f')))
                        worksheet.write(row, col + 9, float(format(totallast_actualytd, '.2f')))
                        worksheet.write(row, col + 10, float(format(totallast_varamount, '.2f')))
                        worksheet.write(row, col + 11, float(format(totallast_varpercent, '.2f')))
                        row += 1
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

def query_scheduled_expense_deptsection(type, expense, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth):
    print "Transaction Query Scheduled Expense"
    ''' Create query '''
    cursor = connection.cursor()

    type_condition = ''
    department_condition = ''
    expense_condition = ''
    product_condition = ''

    if type == '2':
        type_condition = "GROUP BY d.code, z.cgroupdescription, z.description"
    else:
        type_condition = "GROUP BY d.code, z.cgroupdescription, z.csubheadtitle"

    if expense != '':
        expense_condition = "AND d.expchartofaccount_id = '" + str(expense) + "'"

    if product != '':
        product_condition = "AND d.product_id = '" + str(product) + "'"

    if department != '':
        department_condition = "AND a.department_id = '" + str(department) + "'"

    print 'start'
    query = "SELECT d.code AS dcode, d.departmentname, d.product_id, d.expchartofaccount_id, SUM(IF(z.code = 'C', z.amount * -1, z.amount)) AS curamount, SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount)) AS prevamount, SUM(z.ytdamount) AS ytdamount, " \
            "(SUM(IF(z.code = 'C', z.amount * -1, z.amount)) - SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount))) AS varamount, " \
            "IFNULL(ROUND(((SUM(IF(z.code = 'C', z.amount * -1, z.amount)) - SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount))) / SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount))) * 100, 2), 0) AS varpercent, " \
            "z.accountcode, z.title, z.description, " \
            "z.cgrouptitle, z.cgroupdescription, z.csubgrouptitle, z.csubgroupdescription, z.csubheadtitle, z.csubheaddescription " \
            "FROM ( " \
            "SELECT a.year, a.month, a.amount, 0 AS prevamount, 0 AS ytdamount, a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(fromyear)+" AND a.month = "+str(frommonth)+" "+str(department_condition)+" " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS curamount, a.amount, 0 AS ytdamount, a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(prevyear)+" AND a.month = "+str(prevmonth)+" "+str(department_condition)+" " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS curamount, 0 AS amount, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS ytdamount,a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(fromyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" "+str(department_condition)+" " \
            "GROUP BY a.department_id, c.accountcode " \
            ") AS z " \
            "LEFT OUTER JOIN department AS d ON d.id = z.department_id " \
            "WHERE d.isdeleted = 0 AND z.main = '5' "+str(expense_condition)+" "+str(product_condition)+" "+" "+str(type_condition)+" " \
            "ORDER BY d.code, z.accountcode, z.year ASC, z.month DESC"
    print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    print 'end'
    return result

def query_scheduled_expense_deptgroup(type, expense, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth):
    print "Transaction Query Scheduled Expense"
    ''' Create query '''
    cursor = connection.cursor()

    type_condition = ''
    department_condition = ''
    expense_condition = ''
    product_condition = ''

    if type == '2':
        type_condition = "GROUP BY d.groupname, z.cgroupdescription, z.description"
    else:
        type_condition = "GROUP BY d.groupname, z.cgroupdescription, z.csubheadtitle"

    if expense != '':
        expense_condition = "AND d.expchartofaccount_id = '" + str(expense) + "'"

    if product != '':
        product_condition = "AND d.product_id = '" + str(product) + "'"

    if department != '':
        department_condition = "AND a.department_id = '" + str(department) + "'"

    print 'start'
    query = "SELECT d.code AS dcode, d.departmentname, d.groupname, d.product_id, d.expchartofaccount_id, SUM(IF(z.code = 'C', z.amount * -1, z.amount)) AS curamount, SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount)) AS prevamount, SUM(z.ytdamount) AS ytdamount, " \
            "(SUM(IF(z.code = 'C', z.amount * -1, z.amount)) - SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount))) AS varamount, " \
            "IFNULL(ROUND(((SUM(IF(z.code = 'C', z.amount * -1, z.amount)) - SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount))) / SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount))) * 100, 2), 0) AS varpercent, " \
            "z.accountcode, z.title, z.description, " \
            "z.cgrouptitle, z.cgroupdescription, z.csubgrouptitle, z.csubgroupdescription, z.csubheadtitle, z.csubheaddescription " \
            "FROM ( " \
            "SELECT a.year, a.month, a.amount, 0 AS prevamount, 0 AS ytdamount, a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(fromyear)+" AND a.month = "+str(frommonth)+" "+str(department_condition)+" " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS curamount, a.amount, 0 AS ytdamount, a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(prevyear)+" AND a.month = "+str(prevmonth)+" "+str(department_condition)+" " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS curamount, 0 AS amount, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS ytdamount,a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(fromyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" "+str(department_condition)+" " \
            "GROUP BY a.department_id, c.accountcode " \
            ") AS z " \
            "LEFT OUTER JOIN department AS d ON d.id = z.department_id " \
            "WHERE d.isdeleted = 0 AND z.main = '5' "+str(expense_condition)+" "+str(product_condition)+" "+" "+str(type_condition)+" " \
            "ORDER BY d.code, z.accountcode, z.year ASC, z.month DESC"
    
    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    print 'end'
    return result

def query_scheduled_expense_group(type, expense, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth):
    print "Transaction Query Scheduled Expense"
    ''' Create query '''
    cursor = connection.cursor()

    type_condition = ''
    department_condition = ''
    expense_condition = ''
    product_condition = ''

    if type == '2':
        type_condition = "GROUP BY z.cgroupdescription, z.description"
    else:
        type_condition = "GROUP BY z.cgroupdescription, z.csubheadtitle"

    if expense != '':
        expense_condition = "AND d.expchartofaccount_id = '" + str(expense) + "'"

    if product != '':
        product_condition = "AND d.product_id = '" + str(product) + "'"

    if department != '':
        department_condition = "AND a.department_id = '" + str(department) + "'"

    print 'start'
    query = "SELECT d.code AS dcode, d.departmentname, d.groupname, d.product_id, d.expchartofaccount_id, SUM(IF(z.code = 'C', z.amount * -1, z.amount)) AS curamount, SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount)) AS prevamount, SUM(z.ytdamount) AS ytdamount, " \
            "(SUM(IF(z.code = 'C', z.amount * -1, z.amount)) - SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount))) AS varamount, " \
            "IFNULL(ROUND(((SUM(IF(z.code = 'C', z.amount * -1, z.amount)) - SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount))) / SUM(IF(z.code = 'C', z.prevamount * -1, z.prevamount))) * 100, 2), 0) AS varpercent, " \
            "z.accountcode, z.title, z.description, " \
            "z.cgrouptitle, z.cgroupdescription, z.csubgrouptitle, z.csubgroupdescription, z.csubheadtitle, z.csubheaddescription " \
            "FROM ( " \
            "SELECT a.year, a.month, a.amount, 0 AS prevamount, 0 AS ytdamount, a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(fromyear)+" AND a.month = "+str(frommonth)+" "+str(department_condition)+" " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS curamount, a.amount, 0 AS ytdamount, a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(prevyear)+" AND a.month = "+str(prevmonth)+" "+str(department_condition)+" " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS curamount, 0 AS amount, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS ytdamount,a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(fromyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" "+str(department_condition)+" " \
            "GROUP BY c.accountcode " \
            ") AS z " \
            "LEFT OUTER JOIN department AS d ON d.id = z.department_id " \
            "WHERE d.isdeleted = 0 AND z.main = '5' "+str(expense_condition)+" "+str(product_condition)+" "+" "+str(type_condition)+" " \
            "ORDER BY z.accountcode, z.year ASC, z.month DESC"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    print 'end'
    return result

def query_budget_deptsection(type, expense, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth):
    print "Transaction Query Budget Report"
    ''' Create query '''
    cursor = connection.cursor()

    lastyear = prevyear - 1

    type_condition = ''
    department_condition = ''
    expense_condition = ''
    product_condition = ''

    if type == '2':
        type_condition = "GROUP BY d.code, z.cgroupdescription, z.description"
    else:
        type_condition = "GROUP BY d.code, z.cgroupdescription, z.csubheadtitle"

    if expense != '':
        expense_condition = "AND d.expchartofaccount_id = '" + str(expense) + "'"

    if product != '':
        product_condition = "AND d.product_id = '" + str(product) + "'"

    if department != '':
        department_condition = "AND a.department_id = '" + str(department) + "'"

    print 'start'
    query = "SELECT d.code AS dcode, d.departmentname, d.groupname, d.product_id, d.expchartofaccount_id, " \
            "SUM(IF(z.code = 'C', z.budget * -1, z.budget)) AS budget, SUM(IF(z.code = 'C', z.actual * -1, z.actual)) AS actual, " \
            "(SUM(IF(z.code = 'C', z.actual * -1, z.actual)) - SUM(IF(z.code = 'C', z.budget * -1, z.budget))) AS varamount, " \
            "IFNULL(ROUND((((SUM(IF(z.code = 'C', z.actual * -1, z.actual)) - SUM(IF(z.code = 'C', z.budget * -1, z.budget))) / SUM(IF(z.code = 'C', z.budget * -1, z.budget)))) * 100, 2), 0) AS varpercent, " \
            "SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd)) AS cur_budytd, SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd)) AS cur_actualytd, " \
            "(SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd)) - SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd))) AS cur_varamount, " \
            "IFNULL(ROUND((((SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd)) - SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd))) / SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd)))) * 100, 2), 0) AS cur_varpercent, " \
            "SUM(IF(z.code = 'C', z.last_budytd * -1, z.last_budytd)) AS last_budytd, " \
            "SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)) AS last_actualytd, " \
            "(SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)) - SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd))) AS last_varamount, " \
            "IFNULL(ROUND((((SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)) - SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd))) / SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)))) * 100, 2), 0) AS last_varpercent, " \
            "z.accountcode, z.title, z.description, " \
            "z.cgrouptitle, z.cgroupdescription, z.csubgrouptitle, z.csubgroupdescription, z.csubheadtitle, z.csubheaddescription " \
            "FROM ( " \
            "SELECT a.year, a.month, " \
            "CASE " \
            "WHEN a.month = 1 THEN IFNULL(deptbud.mjan, 0) " \
            "WHEN a.month = 2 THEN IFNULL(deptbud.mfeb, 0) " \
            "WHEN a.month = 3 THEN IFNULL(deptbud.mmar, 0) " \
            "WHEN a.month = 4 THEN IFNULL(deptbud.mapr, 0) " \
            "WHEN a.month = 5 THEN IFNULL(deptbud.mmay, 0) " \
            "WHEN a.month = 6 THEN IFNULL(deptbud.mjun, 0) " \
            "WHEN a.month = 7 THEN IFNULL(deptbud.mjul, 0) " \
            "WHEN a.month = 8 THEN IFNULL(deptbud.maug, 0) " \
            "WHEN a.month = 9 THEN IFNULL(deptbud.msep, 0) " \
            "WHEN a.month = 10 THEN IFNULL(deptbud.moct, 0) " \
            "WHEN a.month = 11 THEN IFNULL(deptbud.mnov, 0) " \
            "WHEN a.month = 12 THEN IFNULL(deptbud.mdec, 0) " \
            "ELSE 0 " \
            "END budget, " \
            "a.amount AS actual, 0 AS cur_budytd, 0 AS cur_actualytd, 0 AS last_budytd, 0 AS last_actualytd, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN departmentbudget AS deptbud ON (deptbud.chartofaccount_id = a.chartofaccount_id AND deptbud.year = "+str(toyear)+" AND deptbud.department_id = a.department_id) " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(toyear)+" AND a.month = "+str(tomonth)+" "+str(department_condition)+" " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS budget, 0 AS amount, " \
            "CASE " \
            "WHEN a.month = 1 THEN SUM(IFNULL(deptbud.mjan, 0)) " \
            "WHEN a.month = 2 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0))) " \
            "WHEN a.month = 3 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0))) " \
            "WHEN a.month = 4 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0))) " \
            "WHEN a.month = 5 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0))) " \
            "WHEN a.month = 6 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0))) " \
            "WHEN a.month = 7 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0))) " \
            "WHEN a.month = 8 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0))) " \
            "WHEN a.month = 9 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))) " \
            "WHEN a.month = 10 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))  + SUM(IFNULL(deptbud.moct, 0))) " \
            "WHEN a.month = 11 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))  + SUM(IFNULL(deptbud.moct, 0))  + SUM(IFNULL(deptbud.mnov, 0))) " \
            "WHEN a.month = 12 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0))+ SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))  + SUM(IFNULL(deptbud.moct, 0))  + SUM(IFNULL(deptbud.mnov, 0))  + SUM(IFNULL(deptbud.mdec, 0))) " \
            "ELSE 0 " \
            "END cur_budytd, " \
            "SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS cur_actualytd, " \
            "0 AS last_budytd, 0 AS last_actualytd, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN departmentbudget AS deptbud ON (deptbud.chartofaccount_id = a.chartofaccount_id AND deptbud.year = "+str(toyear)+" AND deptbud.department_id = a.department_id) " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(toyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" "+str(department_condition)+" " \
            "GROUP BY a.department_id, c.accountcode " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS budget, 0 AS amount, " \
            "0 cur_budytd, 0 AS cur_actualytd, 0 AS last_budytd, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS last_actualytd, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(lastyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" "+str(department_condition)+" " \
            "GROUP BY a.department_id, c.accountcode ) AS z " \
            "LEFT OUTER JOIN department AS d ON d.id = z.department_id " \
            "WHERE z.main = '5' "+str(expense_condition)+" "+str(product_condition)+" "+" "+str(type_condition)+" " \
            "ORDER BY d.code, z.accountcode, z.year ASC, z.month DESC"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    print 'end'
    return result

def query_budget_deptgroup(type, expense, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth):
    print "Transaction Query Budget Report"
    ''' Create query '''
    cursor = connection.cursor()

    lastyear = prevyear - 1

    type_condition = ''
    department_condition = ''
    expense_condition = ''
    product_condition = ''

    if type == '2':
        type_condition = "GROUP BY d.groupname, z.cgroupdescription, z.description"
    else:
        type_condition = "GROUP BY d.groupname, z.cgroupdescription, z.csubheadtitle"

    if expense != '':
        expense_condition = "AND d.expchartofaccount_id = '" + str(expense) + "'"

    if product != '':
        product_condition = "AND d.product_id = '" + str(product) + "'"

    if department != '':
        department_condition = "AND a.department_id = '" + str(department) + "'"

    print 'start'
    query = "SELECT d.code AS dcode, d.departmentname, d.groupname, d.product_id, d.expchartofaccount_id, " \
            "SUM(IF(z.code = 'C', z.budget * -1, z.budget)) AS budget, SUM(IF(z.code = 'C', z.actual * -1, z.actual)) AS actual, " \
            "(SUM(IF(z.code = 'C', z.actual * -1, z.actual)) - SUM(IF(z.code = 'C', z.budget * -1, z.budget))) AS varamount, " \
            "IFNULL(ROUND((((SUM(IF(z.code = 'C', z.actual * -1, z.actual)) - SUM(IF(z.code = 'C', z.budget * -1, z.budget))) / SUM(IF(z.code = 'C', z.budget * -1, z.budget)))) * 100, 2), 0) AS varpercent, " \
            "SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd)) AS cur_budytd, SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd)) AS cur_actualytd, " \
            "(SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd)) - SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd))) AS cur_varamount, " \
            "IFNULL(ROUND((((SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd)) - SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd))) / SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd)))) * 100, 2), 0) AS cur_varpercent, " \
            "SUM(IF(z.code = 'C', z.last_budytd * -1, z.last_budytd)) AS last_budytd, " \
            "SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)) AS last_actualytd, " \
            "(SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)) - SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd))) AS last_varamount, " \
            "IFNULL(ROUND((((SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)) - SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd))) / SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)))) * 100, 2), 0) AS last_varpercent, " \
            "z.accountcode, z.title, z.description, " \
            "z.cgrouptitle, z.cgroupdescription, z.csubgrouptitle, z.csubgroupdescription, z.csubheadtitle, z.csubheaddescription " \
            "FROM ( " \
            "SELECT a.year, a.month, " \
            "CASE " \
            "WHEN a.month = 1 THEN IFNULL(deptbud.mjan, 0) " \
            "WHEN a.month = 2 THEN IFNULL(deptbud.mfeb, 0) " \
            "WHEN a.month = 3 THEN IFNULL(deptbud.mmar, 0) " \
            "WHEN a.month = 4 THEN IFNULL(deptbud.mapr, 0) " \
            "WHEN a.month = 5 THEN IFNULL(deptbud.mmay, 0) " \
            "WHEN a.month = 6 THEN IFNULL(deptbud.mjun, 0) " \
            "WHEN a.month = 7 THEN IFNULL(deptbud.mjul, 0) " \
            "WHEN a.month = 8 THEN IFNULL(deptbud.maug, 0) " \
            "WHEN a.month = 9 THEN IFNULL(deptbud.msep, 0) " \
            "WHEN a.month = 10 THEN IFNULL(deptbud.moct, 0) " \
            "WHEN a.month = 11 THEN IFNULL(deptbud.mnov, 0) " \
            "WHEN a.month = 12 THEN IFNULL(deptbud.mdec, 0) " \
            "ELSE 0 " \
            "END budget, " \
            "a.amount AS actual, 0 AS cur_budytd, 0 AS cur_actualytd, 0 AS last_budytd, 0 AS last_actualytd, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN departmentbudget AS deptbud ON (deptbud.chartofaccount_id = a.chartofaccount_id AND deptbud.year = "+str(toyear)+" AND deptbud.department_id = a.department_id) " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(toyear)+" AND a.month = "+str(tomonth)+" "+str(department_condition)+" " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS budget, 0 AS amount, " \
            "CASE " \
            "WHEN a.month = 1 THEN SUM(IFNULL(deptbud.mjan, 0)) " \
            "WHEN a.month = 2 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0))) " \
            "WHEN a.month = 3 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0))) " \
            "WHEN a.month = 4 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0))) " \
            "WHEN a.month = 5 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0))) " \
            "WHEN a.month = 6 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0))) " \
            "WHEN a.month = 7 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0))) " \
            "WHEN a.month = 8 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0))) " \
            "WHEN a.month = 9 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))) " \
            "WHEN a.month = 10 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))  + SUM(IFNULL(deptbud.moct, 0))) " \
            "WHEN a.month = 11 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))  + SUM(IFNULL(deptbud.moct, 0))  + SUM(IFNULL(deptbud.mnov, 0))) " \
            "WHEN a.month = 12 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0))+ SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))  + SUM(IFNULL(deptbud.moct, 0))  + SUM(IFNULL(deptbud.mnov, 0))  + SUM(IFNULL(deptbud.mdec, 0))) " \
            "ELSE 0 " \
            "END cur_budytd, " \
            "SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS cur_actualytd, " \
            "0 AS last_budytd, 0 AS last_actualytd, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN departmentbudget AS deptbud ON (deptbud.chartofaccount_id = a.chartofaccount_id AND deptbud.year = "+str(toyear)+" AND deptbud.department_id = a.department_id) " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(toyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" "+str(department_condition)+" " \
            "GROUP BY a.department_id, c.accountcode " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS budget, 0 AS amount, " \
            "0 cur_budytd, 0 AS cur_actualytd, 0 AS last_budytd, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS last_actualytd, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(lastyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" "+str(department_condition)+" " \
            "GROUP BY a.department_id, c.accountcode ) AS z " \
            "LEFT OUTER JOIN department AS d ON d.id = z.department_id " \
            "WHERE z.main = '5' "+str(expense_condition)+" "+str(product_condition)+" "+" "+str(type_condition)+" " \
            "ORDER BY d.code, z.accountcode, z.year ASC, z.month DESC"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    print 'end'
    return result

def query_budget_group(type, expense, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth):
    print "Transaction Query Budget Report"
    ''' Create query '''
    cursor = connection.cursor()

    lastyear = prevyear - 1

    type_condition = ''
    department_condition = ''
    expense_condition = ''
    product_condition = ''

    if type == '2':
        type_condition = "GROUP BY z.cgroupdescription, z.description"
    else:
        type_condition = "GROUP BY z.cgroupdescription, z.csubheadtitle"

    if expense != '':
        expense_condition = "AND d.expchartofaccount_id = '" + str(expense) + "'"

    if product != '':
        product_condition = "AND d.product_id = '" + str(product) + "'"

    if department != '':
        department_condition = "AND a.department_id = '" + str(department) + "'"

    print 'start'
    query = "SELECT d.code AS dcode, d.departmentname, d.groupname, d.product_id, d.expchartofaccount_id, " \
            "SUM(IF(z.code = 'C', z.budget * -1, z.budget)) AS budget, SUM(IF(z.code = 'C', z.actual * -1, z.actual)) AS actual, " \
            "(SUM(IF(z.code = 'C', z.actual * -1, z.actual)) - SUM(IF(z.code = 'C', z.budget * -1, z.budget))) AS varamount, " \
            "IFNULL(ROUND((((SUM(IF(z.code = 'C', z.actual * -1, z.actual)) - SUM(IF(z.code = 'C', z.budget * -1, z.budget))) / SUM(IF(z.code = 'C', z.budget * -1, z.budget)))) * 100, 2), 0) AS varpercent, " \
            "SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd)) AS cur_budytd, SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd)) AS cur_actualytd, " \
            "(SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd)) - SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd))) AS cur_varamount, " \
            "IFNULL(ROUND((((SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd)) - SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd))) / SUM(IF(z.code = 'C', z.cur_budytd * -1, z.cur_budytd)))) * 100, 2), 0) AS cur_varpercent, " \
            "SUM(IF(z.code = 'C', z.last_budytd * -1, z.last_budytd)) AS last_budytd, " \
            "SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)) AS last_actualytd, " \
            "(SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)) - SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd))) AS last_varamount, " \
            "IFNULL(ROUND((((SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)) - SUM(IF(z.code = 'C', z.cur_actualytd * -1, z.cur_actualytd))) / SUM(IF(z.code = 'C', z.last_actualytd * -1, z.last_actualytd)))) * 100, 2), 0) AS last_varpercent, " \
            "z.accountcode, z.title, z.description, " \
            "z.cgrouptitle, z.cgroupdescription, z.csubgrouptitle, z.csubgroupdescription, z.csubheadtitle, z.csubheaddescription " \
            "FROM ( " \
            "SELECT a.year, a.month, " \
            "CASE " \
            "WHEN a.month = 1 THEN IFNULL(deptbud.mjan, 0) " \
            "WHEN a.month = 2 THEN IFNULL(deptbud.mfeb, 0) " \
            "WHEN a.month = 3 THEN IFNULL(deptbud.mmar, 0) " \
            "WHEN a.month = 4 THEN IFNULL(deptbud.mapr, 0) " \
            "WHEN a.month = 5 THEN IFNULL(deptbud.mmay, 0) " \
            "WHEN a.month = 6 THEN IFNULL(deptbud.mjun, 0) " \
            "WHEN a.month = 7 THEN IFNULL(deptbud.mjul, 0) " \
            "WHEN a.month = 8 THEN IFNULL(deptbud.maug, 0) " \
            "WHEN a.month = 9 THEN IFNULL(deptbud.msep, 0) " \
            "WHEN a.month = 10 THEN IFNULL(deptbud.moct, 0) " \
            "WHEN a.month = 11 THEN IFNULL(deptbud.mnov, 0) " \
            "WHEN a.month = 12 THEN IFNULL(deptbud.mdec, 0) " \
            "ELSE 0 " \
            "END budget, " \
            "a.amount AS actual, 0 AS cur_budytd, 0 AS cur_actualytd, 0 AS last_budytd, 0 AS last_actualytd, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN departmentbudget AS deptbud ON (deptbud.chartofaccount_id = a.chartofaccount_id AND deptbud.year = "+str(toyear)+" AND deptbud.department_id = a.department_id) " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(toyear)+" AND a.month = "+str(tomonth)+" "+str(department_condition)+" " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS budget, 0 AS amount, " \
            "CASE " \
            "WHEN a.month = 1 THEN SUM(IFNULL(deptbud.mjan, 0)) " \
            "WHEN a.month = 2 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0))) " \
            "WHEN a.month = 3 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0))) " \
            "WHEN a.month = 4 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0))) " \
            "WHEN a.month = 5 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0))) " \
            "WHEN a.month = 6 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0))) " \
            "WHEN a.month = 7 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0))) " \
            "WHEN a.month = 8 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0))) " \
            "WHEN a.month = 9 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))) " \
            "WHEN a.month = 10 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))  + SUM(IFNULL(deptbud.moct, 0))) " \
            "WHEN a.month = 11 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0)) + SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))  + SUM(IFNULL(deptbud.moct, 0))  + SUM(IFNULL(deptbud.mnov, 0))) " \
            "WHEN a.month = 12 THEN (SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mfeb, 0)) + SUM(IFNULL(deptbud.mmar, 0)) + SUM(IFNULL(deptbud.mapr, 0)) + SUM(IFNULL(deptbud.mmay, 0)) + SUM(IFNULL(deptbud.mjun, 0)) + SUM(IFNULL(deptbud.mjul, 0))+ SUM(IFNULL(deptbud.maug, 0)) + SUM(IFNULL(deptbud.msep, 0))  + SUM(IFNULL(deptbud.moct, 0))  + SUM(IFNULL(deptbud.mnov, 0))  + SUM(IFNULL(deptbud.mdec, 0))) " \
            "ELSE 0 " \
            "END cur_budytd, " \
            "SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS cur_actualytd, " \
            "0 AS last_budytd, 0 AS last_actualytd, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN departmentbudget AS deptbud ON (deptbud.chartofaccount_id = a.chartofaccount_id AND deptbud.year = "+str(toyear)+" AND deptbud.department_id = a.department_id) " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(toyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" "+str(department_condition)+" " \
            "GROUP BY a.department_id, c.accountcode " \
            "UNION " \
            "SELECT a.year, a.month, 0 AS budget, 0 AS amount, " \
            "0 cur_budytd, 0 AS cur_actualytd, 0 AS last_budytd, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS last_actualytd, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(lastyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" "+str(department_condition)+" " \
            "GROUP BY a.department_id, c.accountcode ) AS z " \
            "LEFT OUTER JOIN department AS d ON d.id = z.department_id " \
            "WHERE z.main = '5' "+str(expense_condition)+" "+str(product_condition)+" "+" "+str(type_condition)+" " \
            "ORDER BY z.accountcode, z.year ASC, z.month DESC"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    print 'end'
    return result

def query_sched_expense_row(dept, type, expense, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth):
    print "Transaction Query Budget Report"
    ''' Create query '''
    cursor = connection.cursor()

    str_col = ''
    str_total = ''
    str_left = ''
    str_con = ''
    type_condition = ''

    if type == '2':
        type_condition = "GROUP BY cgroup.description, ch.description"
    else:
        type_condition = "GROUP BY cgroup.description, csubhead.title"

    counter = 1
    #for id, d in dept.items():
    for id, d in dept:
        str_col += "SUM(IFNULL(col"+str(counter)+".amount, 0)) AS col"+str(counter)+", "
        str_total += "SUM(IFNULL(col"+str(counter)+".amount, 0)) + "
        str_left += "LEFT OUTER JOIN " \
                    "(SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, a.code, a.chartofaccount_id, a.department_id " \
                    "FROM accountexpensebalance AS a " \
                    "WHERE a.year = "+str(toyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" AND a.department_id = "+str(id)+" " \
                    "GROUP BY a.chartofaccount_id) AS col"+str(counter)+" ON col"+str(counter)+".chartofaccount_id = c.id "
        str_con += "IFNULL(col"+str(counter)+".amount, 0) + "
        counter += 1

    str_total = "("+str(str_total)+" 0 ) AS col"+str(counter)+", "
    print 'start'
    query = "SELECT '' AS dcode, '' AS departmentname, ch.main, ch.clas, ch.item, ch.cont, ch.sub, ch.title AS chtitle, ch.description AS chdescription, ch.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription, c.accountcode, c.description, "+str(str_col)+" "+str(str_total)+" c.id " \
            "FROM chartofaccount AS c "+str(str_left)+" " \
            "LEFT OUTER JOIN chartofaccount AS ch ON ch.id = c.id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = ch.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = ch.main AND csubgroup.clas = ch.clas AND csubgroup.item = ch.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = ch.main AND csubhead.clas = ch.clas AND csubhead.item = ch.item AND csubhead.cont = ch.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE c.main = 5 AND ("+str(str_con)+" 0) != 0 "+" "+str(type_condition)+" " \
            "ORDER BY c.accountcode"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    #print query

    print 'end'
    return result

def query_sched_expense_dept(type, expense, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth):
    print "Transaction Query Budget Report"
    ''' Create query '''
    cursor = connection.cursor()

    type_condition = "GROUP BY d.code, z.cgroupdescription, z.description"
    department_condition = ''
    expense_condition = ''
    product_condition = ''

    # if type == '2':
    #     type_condition = "GROUP BY z.cgroupdescription, z.description"
    # else:
    #     type_condition = "GROUP BY z.cgroupdescription, z.csubheadtitle"

    if expense != '':
        expense_condition = "AND d.expchartofaccount_id = '" + str(expense) + "'"

    if product != '':
        product_condition = "AND d.product_id = '" + str(product) + "'"

    if department != '':
        department_condition = "AND a.department_id = '" + str(department) + "'"

    print 'start'
    query = "SELECT d.code AS dcode, d.departmentname, d.id, d.groupname, d.classification, d.product_id, d.expchartofaccount_id, SUM(IF(z.code = 'C', z.amount * -1, z.amount)) AS amount, " \
            "z.accountcode, z.title, z.description, z.cgrouptitle, z.cgroupdescription, z.csubgrouptitle, z.csubgroupdescription, z.csubheadtitle, z.csubheaddescription " \
            "FROM ( " \
            "SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "WHERE a.year = "+str(toyear)+" AND a.month >= 1 AND a.month <= "+str(tomonth)+" "+str(department_condition)+" " \
            "GROUP BY a.department_id, c.accountcode " \
            ") AS z " \
            "LEFT OUTER JOIN department AS d ON d.id = z.department_id " \
            "WHERE z.main = '5' "+str(expense_condition)+" "+str(product_condition)+" "+" "+str(type_condition)+" " \
            "ORDER BY d.departmentname DESC, z.accountcode, z.year ASC, z.month DESC"
    #print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    print 'end'
    return result

def query_scheduled_expense_yearend(type, expense, department, product, fromyear, frommonth, toyear, tomonth, prevyear, prevmonth):
    print "Transaction Query Scheduled Expense"
    ''' Create query '''
    cursor = connection.cursor()

    type_condition = ''
    department_condition = ''
    expense_condition = ''
    product_condition = ''

    print type

    print tomonth

    if type == '2':
        type_condition = "GROUP BY d.groupname, cgroup.description, c.description"
    else:
        type_condition = "GROUP BY d.groupname, cgroup.description, csubhead.title"

    if expense != '':
        expense_condition = "AND d.expchartofaccount_id = '" + str(expense) + "'"

    if product != '':
        product_condition = "AND d.product_id = '" + str(product) + "'"

    if department != '':
        department_condition = "AND a.department_id = '" + str(department) + "'"

    print 'start'
    query = "SELECT d.code AS dcode, d.departmentname, (IFNULL(mjan.amount, 0) + IFNULL(mfeb.amount, 0) + IFNULL(mmar.amount, 0) + IFNULL(mapr.amount, 0) + IFNULL(mmay.amount, 0) + IFNULL(mjun.amount, 0) + IFNULL(mjul.amount, 0) + IFNULL(maug.amount, 0) + IFNULL(msep.amount, 0) + IFNULL(moct.amount, 0) + IFNULL(mnov.amount, 0) + IFNULL(mdec.amount, 0)) AS amount, " \
            "IFNULL(mjan.amount, 0) AS mjan, IFNULL(mfeb.amount, 0) AS mfeb, IFNULL(mmar.amount, 0) AS mmar, " \
            "IFNULL(mapr.amount, 0) AS mapr, IFNULL(mmay.amount, 0) AS mmay, IFNULL(mjun.amount, 0) AS mjun, " \
            "IFNULL(mjul.amount, 0) AS mjul, IFNULL(maug.amount, 0) AS maug, IFNULL(msep.amount, 0) AS msep, " \
            "IFNULL(moct.amount, 0) AS moct, IFNULL(mnov.amount, 0) AS mnov, IFNULL(mdec.amount, 0) AS mdec, " \
            "a.code, a.chartofaccount_id, a.department_id, " \
            "c.main, c.clas, c.item, c.cont, c.sub, " \
            "c.accountcode, c.title, c.description, c.accounttype, " \
            "cgroup.title AS cgrouptitle, cgroup.description AS cgroupdescription, " \
            "csubgroup.title AS csubgrouptitle, csubgroup.description AS csubgroupdescription, " \
            "csubhead.title AS csubheadtitle, csubhead.description AS csubheaddescription " \
            "FROM accountexpensebalance AS a " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 1 AND a.month <= "+str(tomonth)+" AND c.main = 5 " \
            "   GROUP BY a.year, a.chartofaccount_id" \
            ") AS mjan ON mjan.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a  " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 2 AND a.month <= "+str(tomonth)+" AND c.main = 5 " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS mfeb ON mfeb.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 3 AND a.month <= "+str(tomonth)+" AND c.main = 5 " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS mmar ON mmar.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 4 AND a.month <= "+str(tomonth)+" AND c.main = 5  " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS mapr ON mapr.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 5 AND a.month <= "+str(tomonth)+" AND c.main = 5 " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS mmay ON mmay.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 6 AND a.month <= "+str(tomonth)+" AND c.main = 5 " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS mjun ON mjun.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 7 AND a.month <= "+str(tomonth)+" AND c.main = 5  " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS mjul ON mjul.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a  " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 8 AND a.month <= "+str(tomonth)+" AND c.main = 5 " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS maug ON maug.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 9 AND a.month <= "+str(tomonth)+" AND c.main = 5  " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS msep ON msep.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 10 AND a.month <= "+str(tomonth)+" AND c.main = 5 " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS moct ON moct.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 11 AND a.month <= "+str(tomonth)+" AND c.main = 5 " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS mnov ON mnov.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN ( " \
            "   SELECT a.year, a.month, SUM(IF(a.code = 'C', a.amount * -1, a.amount)) AS amount, " \
            "   a.code, a.chartofaccount_id, a.department_id " \
            "   FROM accountexpensebalance AS a " \
            "   LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "   WHERE a.year = "+str(toyear)+" AND a.month = 12 AND a.month <= "+str(tomonth)+" AND c.main = 5 " \
            "   GROUP BY a.year, a.chartofaccount_id " \
            ") AS mdec ON mdec.chartofaccount_id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN chartofaccount AS cgroup ON (cgroup.main = c.main AND cgroup.clas = c.clas AND cgroup.item = 0 AND cgroup.cont = 0 AND cgroup.sub = 000000 AND cgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubgroup ON (csubgroup.main = c.main AND csubgroup.clas = c.clas AND csubgroup.item = c.item AND csubgroup.cont = 0 AND csubgroup.sub = 000000 AND csubgroup.accounttype = 'T') " \
            "LEFT OUTER JOIN chartofaccount AS csubhead ON (csubhead.main = c.main AND csubhead.clas = c.clas AND csubhead.item = c.item AND csubhead.cont = c.cont AND csubhead.sub = CONCAT(SUBSTR(c.sub, 1, 1),'','00000')) " \
            "LEFT OUTER JOIN department AS d ON d.id = a.department_id " \
            "WHERE a.year = "+str(toyear)+" AND a.month >= "+str(frommonth)+" AND a.month <= "+str(tomonth)+" AND c.main = 5 "+str(product_condition)+" "+" "+str(type_condition)+" "+str(expense_condition)+" "+str(department_condition)+" " \

    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    print 'end'
    return result