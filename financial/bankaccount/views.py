import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from collections import namedtuple
from django.db import connection
from bank.models import Bank
from bankaccount.models import Bankaccountsummary
from bankbranch.models import Bankbranch
from bankaccounttype.models import Bankaccounttype
from currency.models import Currency
from chartofaccount.models import Chartofaccount
from . models import Bankaccount
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter
from django.template.loader import render_to_string
from django.db.models.lookups import MonthTransform as Month, YearTransform as Year
from datetime import timedelta
import io
import xlsxwriter


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Bankaccount
    template_name = 'bankaccount/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Bankaccount.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Bankaccount
    template_name = 'bankaccount/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Bankaccount
    template_name = 'bankaccount/create.html'
    fields = ['code', 'bank', 'bankbranch', 'bankaccounttype',
              'currency', 'chartofaccount', 'accountnumber',
              'remarks', 'beg_amount', 'beg_code', 'beg_date',
              'run_amount', 'run_code', 'run_date']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankaccount.add_bankaccount'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/bankaccount')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['bank'] = Bank.objects.filter(isdeleted=0).order_by('description')
        context['bankaccounttype'] = Bankaccounttype.objects.\
            filter(isdeleted=0).order_by('id')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('id')
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Bankaccount
    template_name = 'bankaccount/edit.html'
    fields = ['code', 'bank', 'bankbranch', 'bankaccounttype', 'currency',
              'chartofaccount', 'accountnumber',
              'remarks', 'beg_amount', 'beg_code', 'beg_date', 'run_amount',
              'run_code', 'run_date']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankaccount.change_bankaccount'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['bank', 'bankbranch', 'bankaccounttype', 'currency',
                                        'chartofaccount', 'accountnumber', 'remarks',
                                        'beg_amount', 'beg_code', 'beg_date', 'run_amount',
                                        'run_code', 'run_date', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/bankaccount')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['bank'] = Bank.objects.filter(isdeleted=0).order_by('description')
        context['bankaccounttype'] = Bankaccounttype.objects.filter(isdeleted=0).order_by('id')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('id')
        context['bankbranch_id'] = self.object.bankbranch.id
        context['bankbranch_description'] = self.object.bankbranch.description
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        elif self.object.chartofaccount:
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.object.chartofaccount.id, isdeleted=0)
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Bankaccount
    template_name = 'bankaccount/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankaccount.delete_bankaccount'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/bankaccount')


@csrf_exempt
def get_branch(request):
    if request.method == 'POST':
        bank = request.POST['bank']
        bankbranch = Bankbranch.objects.filter(bank=bank).order_by('description')
        data = {
            'status': 'success',
            'bankbranch': serializers.serialize("json", bankbranch),
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Bank Account Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('bankaccount/list.html', context)

@method_decorator(login_required, name='dispatch')
class GeneratePDF2(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Bankaccount.objects.filter(isdeleted=0).order_by('code')

        debit = 0
        credit = 0
        grandtotal = 0
        for l in list:
            print l.run_amount
            if l.run_code == 'D':
                debit += l.run_amount
            else:
                credit += l.run_amount

        grandtotal = abs(debit - credit)

        total = {'debit': debit, 'credit': credit, 'grandtotal': grandtotal}

        context = {
            "title": "Cash In Bank Balances",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "username": request.user,
        }
        return Render.render('bankaccount/cashinbankbalances.html', context)

@method_decorator(login_required, name='dispatch')
class InquiryView(TemplateView):
    template_name = 'bankaccount/inquiry/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['bankaccount'] = Bankaccount.objects.all().filter(isdeleted=0).order_by('code')

        return context

def transgenerate(request):
    dto = request.GET["dto"]
    dfrom = request.GET["dfrom"]
    bankaccount = request.GET["bankaccount"]

    context = {}

    print "transaction listing"

    ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
    todate = datetime.date(int(ndto.year), int(ndto.month), 10)
    toyear = todate.year
    tomonth = todate.month
    nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
    fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
    adfromdate = datetime.datetime.strptime(dfrom, "%Y-%m-%d") - timedelta(days=1)
    fromyear = fromdate.year
    frommonth = fromdate.month

    prevdate = datetime.date(int(fromyear), int(frommonth), 10) - timedelta(days=15)
    prevyear = prevdate.year
    prevmonth = prevdate.month

    if prevmonth != 12:
        prevyear = prevdate.year - 1

    print prevyear

    begbalamount = 0
    endbalamount = 0
    endcode = 'D'

    cashinbank = 30
    defcode = 'D'

    print defcode

    data = query_transaction(dto, dfrom, cashinbank, bankaccount)

    totaldebit = 0
    totalcredit = 0
    netamount = 0
    netcode = 'C'
    for item in data:
        totaldebit += item.debitamount
        totalcredit += item.creditamount

    if totaldebit >= totalcredit:
        netcode = 'D'
    netamount = totaldebit - totalcredit

    begbal =Bankaccountsummary.objects.filter(year=prevyear, bankaccount_id=bankaccount).first()
    adtrans = query_sumtransaction(adfromdate, str(nfrom.year)+'-01-01', cashinbank, bankaccount)

    adtransnet = 0
    adtranscode = 'D'
    for adtrans in adtrans:
        adtransnet = float(adtrans.debitamount) - float(adtrans.creditamount)
        adtranscode = adtrans.balcode

    begcode = 'D'
    bbamount = 0
    if begbal:
        if begbal.beg_amount is None:
            bbamount = 0
        else:
            bbamount = begbal.beg_amount

        if begbal.beg_code != adtranscode:
            #print 'dito'
            #print begbal.beg_code
            #print adtranscode
            begbalamount = float(bbamount) - float(abs(adtransnet))
        else:
            print 'dito ba'
            begbalamount = float(bbamount) + float(abs(adtransnet))
            #begbalamount = float(begbal.beg_amount) + float(abs(adtransnet))
        if begbal.beg_amount >= abs(adtransnet):
            begcode = begbal.beg_code
        else:
            begcode = adtranscode
    else:
        begbalamount =float((adtransnet))
        begcode = adtranscode

    print begbalamount
    print begcode
    if begcode == 'D':
        begbalamount = abs(begbalamount)
    else:
        begbalamount = abs(begbalamount) * -1
    print netamount
    # print endbalamount

    # print begbalamount
    # print netamount
    print '****'
    endbalamount = float(begbalamount) + float(netamount)

    # if begcode == 'C':
    #     endbalamount = (float(begbalamount) * -1) + float(netamount)
    # else:
    #     endbalamount = float(abs(begbalamount)) + float(netamount)

    if float(endbalamount) < 0:
        endcode = 'C'

    print endbalamount
    print endcode

    context['result'] = query_transaction(dto, dfrom, cashinbank, bankaccount)
    context['dfrom'] = dfrom
    context['dto'] = dto
    context['totaldebit'] = totaldebit
    context['totalcredit'] = totalcredit
    context['netamount'] = abs(netamount)
    viewhtml = render_to_string('bankaccount/inquiry/transaction_result.html', context)

    data = {
        'status': 'success',
        'viewhtml': viewhtml,
        'begbal': float(abs(begbalamount)),
        'begcode': begcode,
        'endbal': float(abs(endbalamount)),
        'endcode': endcode,
    }
    return JsonResponse(data)

def query_sumtransaction(dto, dfrom, chart, bankaccount):
    dfrom  = str(dfrom)[0:11]
    #dfrom ='2020-01-01'
    dto  = str(dto)[0:11]
    print "Transaction Query"
    ''' Create query '''
    cursor = connection.cursor()

    print dfrom
    print '***'
    chart_condition = ''
    chart_bankaccount = ''

    if chart != '':
        chart_condition = "AND m.status = 'O' AND d.chartofaccount_id = '" + str(chart) + "'"
    if bankaccount != '':
        chart_bankaccount = "AND d.bankaccount_id = '" + str(bankaccount) + "'"

    query = "SELECT IFNULL(SUM(z.debitamount), 0) AS debitamount, IFNULL(SUM(z.creditamount), 0) AS creditamount  , IF (IFNULL(SUM(z.debitamount), 0) >= IFNULL(SUM(z.creditamount), 0), 'D', 'C') AS balcode " \
            "FROM ( " \
            "SELECT 'AP' AS tran, d.item_counter, d.ap_num, d.ap_date, d.debitamount, d.creditamount, d.balancecode, d.bankaccount_id " \
            "FROM apdetail AS d " \
            "LEFT OUTER JOIN apmain AS m ON m.id = d.apmain_id " \
            "WHERE DATE(d.ap_date) >= '"+str(dfrom)+"' AND DATE(d.ap_date) <= '"+str(dto)+"' " \
            +str(chart_condition)+" "+str(chart_bankaccount)+"" \
            " UNION " \
            "SELECT 'CV' AS tran, d.item_counter, d.cv_num, d.cv_date, d.debitamount, d.creditamount, d.balancecode, d.bankaccount_id " \
            "FROM cvdetail AS d " \
            "LEFT OUTER JOIN cvmain AS m ON m.id = d.cvmain_id " \
            "WHERE DATE(d.cv_date) >= '"+str(dfrom)+"' AND DATE(d.cv_date) <= '"+str(dto)+"' " \
            + str(chart_condition) + " " + str(chart_bankaccount) + "" \
            " UNION " \
            "SELECT 'JV' AS tran, d.item_counter, d.jv_num, d.jv_date, d.debitamount, d.creditamount, d.balancecode, d.bankaccount_id " \
            "FROM jvdetail AS d " \
            "LEFT OUTER JOIN jvmain AS m ON m.id = d.jvmain_id " \
            "WHERE DATE(d.jv_date) >= '"+str(dfrom)+"' AND DATE(d.jv_date) <= '"+str(dto)+"' " \
            + str(chart_condition) + " " + str(chart_bankaccount) + "" \
            " UNION " \
            "SELECT 'OR' AS tran, d.item_counter, m.ornum, m.ordate, d.debitamount, d.creditamount, d.balancecode, d.bankaccount_id " \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ordetail AS d ON m.id = d.ormain_id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            + str(chart_condition) + " " + str(chart_bankaccount)+") AS z "
    print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def query_transaction(dto, dfrom, chart, bankaccount):
    print "Transaction Query"
    ''' Create query '''
    cursor = connection.cursor()

    chart_condition = ''
    chart_bankaccount = ''

    if chart != '':
        chart_condition = "AND m.status = 'O' AND d.chartofaccount_id = '" + str(chart) + "'"
    if bankaccount != '':
        chart_bankaccount = "AND d.bankaccount_id = '" + str(bankaccount) + "'"

    query = "SELECT z.tran, z.item_counter, z.ap_num AS tnum, z.ap_date AS tdate, z.debitamount, z.creditamount, z.balancecode, z.apstatus AS transtatus, z.status AS status, bank.code AS bank, chart.accountcode, chart.description AS chartofaccount, cust.code AS custcode, cust.name AS customer, dept.code AS deptcode, dept.departmentname AS department, " \
            "emp.code AS empcode, CONCAT(IFNULL(emp.firstname, ''), ' ', IFNULL(emp.lastname, '')) AS employee, inpvat.code AS inpvatcode, inpvat.description AS inputvat, " \
            "outvat.code AS outvatcode, outvat.description AS outputvat, prod.code AS prodcode, prod.description AS product, " \
            "supp.code AS suppcode, supp.name AS supplier, vat.code AS vatcode, vat.description AS vat, wtax.code AS wtaxcode, wtax.description AS wtax, z.payeecode AS payee_code, z.payeename AS payee_name, z.particulars " \
            "FROM ( " \
            "SELECT 'AP' AS tran, d.item_counter, d.ap_num, d.ap_date, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.apstatus, m.status, m.payeecode, m.payeename, m.particulars	 " \
            "FROM apdetail AS d " \
            "LEFT OUTER JOIN apmain AS m ON m.id = d.apmain_id " \
            "WHERE DATE(d.ap_date) >= '"+str(dfrom)+"' AND DATE(d.ap_date) <= '"+str(dto)+"' " \
            +str(chart_condition)+" "+str(chart_bankaccount)+"" \
            "UNION " \
            "SELECT 'CV' AS tran, d.item_counter, d.cv_num, d.cv_date, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.cvstatus, m.status, m.payee_code, m.payee_name, m.particulars	 " \
            "FROM cvdetail AS d " \
            "LEFT OUTER JOIN cvmain AS m ON m.id = d.cvmain_id " \
            "WHERE DATE(d.cv_date) >= '"+str(dfrom)+"' AND DATE(d.cv_date) <= '"+str(dto)+"' " \
            + str(chart_condition) + " " + str(chart_bankaccount) + "" \
            "UNION " \
            "SELECT 'JV' AS tran, d.item_counter, d.jv_num, d.jv_date, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.jvstatus, m.status, '' AS payeecode, '' AS payeename, m.particular	 " \
            "FROM jvdetail AS d " \
            "LEFT OUTER JOIN jvmain AS m ON m.id = d.jvmain_id " \
            "WHERE DATE(d.jv_date) >= '"+str(dfrom)+"' AND DATE(d.jv_date) <= '"+str(dto)+"' " \
            + str(chart_condition) + " " + str(chart_bankaccount) + "" \
            "UNION " \
            "SELECT 'OR' AS tran, d.item_counter, m.ornum, m.ordate, d.debitamount, d.creditamount, d.balancecode, d.ataxcode_id, " \
            "d.bankaccount_id, d.branch_id, d.chartofaccount_id, d.customer_id, d.department_id, d.employee_id, d.inputvat_id, " \
            "d.outputvat_id, d.product_id, d.supplier_id, d.vat_id, d.wtax_id, m.orstatus, m.status, m.payee_code, m.payee_name, m.particulars	" \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ordetail AS d ON m.id = d.ormain_id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            + str(chart_condition) + " " + str(chart_bankaccount)+") AS z " \
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

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

@method_decorator(login_required, name='dispatch')
class GenerateTransExcel(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]
        bankaccount = request.GET["bankaccount"]

        context = {}

        print "transaction listing"

        ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
        todate = datetime.date(int(ndto.year), int(ndto.month), 10)
        toyear = todate.year
        tomonth = todate.month
        nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
        fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
        adfromdate = datetime.datetime.strptime(dfrom, "%Y-%m-%d") - timedelta(days=1)
        fromyear = fromdate.year
        frommonth = fromdate.month

        prevdate = datetime.date(int(fromyear), int(frommonth), 10) - timedelta(days=15)
        prevyear = prevdate.year
        prevmonth = prevdate.month

        if prevmonth != 12:
            prevyear = prevdate.year - 1

        begbalamount = 0
        endbalamount = 0
        endcode = 'D'

        cashinbank = 30

        data = query_transaction(dto, dfrom, cashinbank, bankaccount)

        totaldebit = 0
        totalcredit = 0
        netamount = 0
        netcode = 'C'
        for item in data:
            totaldebit += item.debitamount
            totalcredit += item.creditamount

        if totaldebit >= totalcredit:
            netcode = 'D'
        netamount = totaldebit - totalcredit
        print netamount

        begbal = Bankaccountsummary.objects.filter(year=prevyear, bankaccount_id=bankaccount).first()
        adtrans = query_sumtransaction(adfromdate, str(nfrom.year) + '-01-01', cashinbank, bankaccount)
        adtransnet = 0
        adtranscode = 'D'
        for adtrans in adtrans:
            adtransnet = float(adtrans.debitamount) - float(adtrans.creditamount)
            adtranscode = adtrans.balcode

        begcode = 'D'
        if begbal:
            if begbal.beg_code != adtranscode:
                begbalamount = float(begbal.beg_amount) - float(abs(adtransnet))
            else:
                print begbal.beg_amount
                print abs(adtransnet)
                if begbal.beg_amount:
                    begbalamount = float(begbal.beg_amount) + float(abs(adtransnet))
                else:
                    begbalamount = 0 + float(abs(adtransnet))
            if begbal.beg_amount >= abs(adtransnet):
                begcode = begbal.beg_code
            else:
                begcode = adtranscode
        else:
            begbalamount = float(abs(adtransnet))
            begcode = adtranscode

        # endbalamount = float(begbalamount) + float(netamount)
        # begbalamount = float(begbalamount)

        # if begcode == 'C':
        #     endbalamount = (float(begbalamount) * -1) + float(netamount)
        #     begbalamount = (float(begbalamount) * -1)
        # else:
        #     endbalamount = float(abs(begbalamount)) + float(netamount)
        #     begbalamount = float(abs(begbalamount))

        if begcode == 'C':
            endbalamount = (float(begbalamount) * -1) + float(netamount)
            begbalamount = float(begbalamount) * -1
        else:
            endbalamount = float(abs(begbalamount)) + float(netamount)
            begbalamount = float(begbalamount)

        if float(endbalamount) < 0:
            endcode = 'C'

        result = query_transaction(dto, dfrom, cashinbank, bankaccount)

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', 'BANK ACCOUNT INQUIRY', bold)
        worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)

        worksheet.write('A3', 'BEG BALANCE', bold)
        worksheet.write('B3', float(format(begbalamount, '.2f')), bold)
        worksheet.write('C3', 'END BALANCE', bold)
        worksheet.write('D3', float(format(endbalamount, '.2f')), bold)

        # header
        worksheet.write('A5', 'Type', bold)
        worksheet.write('B5', 'Number', bold)
        worksheet.write('C5', 'Date', bold)
        worksheet.write('D5', 'Particulars', bold)
        worksheet.write('E5', 'Account Code', bold)
        worksheet.write('F5', 'Description', bold)
        worksheet.write('G5', 'Debit Amount', bold)
        worksheet.write('H5', 'Credit Amount', bold)

        row = 5
        col = 0

        for data in result:

            worksheet.write(row, col, data.tran, formatdate)
            worksheet.write(row, col + 1, data.tnum, formatdate)
            worksheet.write(row, col + 2, data.tdate, formatdate)
            worksheet.write(row, col + 3, data.particulars)
            worksheet.write(row, col + 4, data.accountcode)
            worksheet.write(row, col + 5, data.chartofaccount)
            worksheet.write(row, col + 6, float(format(data.debitamount, '.2f')))
            worksheet.write(row, col + 7, float(format(data.creditamount, '.2f')))

            row += 1

        worksheet.write(row, col + 5, 'Total', bold)
        worksheet.write(row, col + 6, float(format(totaldebit, '.2f')), bold)
        worksheet.write(row, col + 7, float(format(totalcredit, '.2f')), bold)

        worksheet.write(row+1, col + 5, 'NET Amount', bold)
        if totaldebit > totalcredit:
            worksheet.write(row+1, col + 6, float(format(netamount, '.2f')), bold)
            worksheet.write(row+1, col + 7, float(format(0, '.2f')), bold)
        else:
            worksheet.write(row + 1, col + 6, float(format(0, '.2f')), bold)
            worksheet.write(row + 1, col + 7, float(format(netamount, '.2f')), bold)

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = "bankaccountinquiry.xlsx"
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response


@method_decorator(login_required, name='dispatch')
class GenerateSummaryTransPDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]

        print "transaction listing"

        ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
        todate = datetime.date(int(ndto.year), int(ndto.month), 10)
        toyear = todate.year
        tomonth = todate.month
        nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
        fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
        adfromdate = datetime.datetime.strptime(dfrom, "%Y-%m-%d") - timedelta(days=1)
        fromyear = fromdate.year
        frommonth = fromdate.month

        prevdate = datetime.date(int(fromyear), int(frommonth), 10) - timedelta(days=15)
        prevyear = prevdate.year
        prevmonth = prevdate.month

        if prevmonth != 12:
            prevyear = prevdate.year - 1

        cashinbank = 30
        data = query_cashinbanktransaction(prevyear, dto, str(nfrom.year) + '-01-01', cashinbank, '')

        debit = 0
        credit = 0
        grandtotal = 0
        for l in data:
            if l.endcode == 'D':
                debit += l.endamount
            else:
                credit += l.endamount

        grandtotal = abs(debit - credit)

        total = {'debit': debit, 'credit': credit, 'grandtotal': grandtotal}

        context = {
            "title": "Cash In Bank Balances",
            "today": datetime.datetime.strptime(dto, "%Y-%m-%d"),
            "company": company,
            "list": data,
            "total": total,
            "username": request.user,
        }
        return Render.render('bankaccount/inquiry/cashinbankbalances.html', context)


@method_decorator(login_required, name='dispatch')
class GenerateSummaryTransExcel(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]

        print "transaction listing"

        ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
        todate = datetime.date(int(ndto.year), int(ndto.month), 10)
        toyear = todate.year
        tomonth = todate.month
        nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
        fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
        adfromdate = datetime.datetime.strptime(dfrom, "%Y-%m-%d") - timedelta(days=1)
        fromyear = fromdate.year
        frommonth = fromdate.month

        prevdate = datetime.date(int(fromyear), int(frommonth), 10) - timedelta(days=15)
        prevyear = prevdate.year
        prevmonth = prevdate.month

        if prevmonth != 12:
            prevyear = prevdate.year - 1

        cashinbank = 30
        data = query_cashinbanktransaction(prevyear, dto, str(nfrom.year) + '-01-01', cashinbank, '')

        debit = 0
        credit = 0
        grandtotal = 0
        for l in data:
            if l.endcode == 'D':
                debit += l.endamount
            else:
                credit += l.endamount

        grandtotal = abs(debit - credit)

        print grandtotal

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', 'BANK ACCOUNT INQUIRY', bold)
        worksheet.write('A2', 'AS OF '+str(dto), bold)

        worksheet.write('A3', 'CASH IN BANK BALANCES', bold)

        # header
        worksheet.write('A5', 'Bank Account', bold)
        worksheet.write('B5', 'Bank Description', bold)
        worksheet.write('C5', 'Debit', bold)
        worksheet.write('D5', 'Credit', bold)

        row = 5
        col = 0

        debit = 0
        credit = 0
        grandtotal = 0
        row = 5
        col = 0
        for l in data:
            if l.endcode == 'D':
                worksheet.write(row, col + 2, float(format(l.endamount, '.2f')))
                worksheet.write(row, col + 3, float(format(0, '.2f')))
                debit += l.endamount
            else:
                worksheet.write(row, col + 2, float(format(0, '.2f')))
                worksheet.write(row, col + 3, float(format(l.endamount, '.2f')))
                credit += l.endamount

            worksheet.write(row, col, l.code)
            worksheet.write(row, col + 1, str(l.bankcode) + ' ' + str(l.bankaccounttype) + ' #' + str(l.accountnumber))
            row += 1

        worksheet.write(row, col + 1, 'Total')
        worksheet.write(row, col + 2, float(format(debit, '.2f')))
        worksheet.write(row, col + 3, float(format(credit, '.2f')))
        row += 1

        grandtotal = abs(debit - credit)

        worksheet.write(row, col + 1, 'Grand Total')
        worksheet.write(row, col + 2, float(format(grandtotal, '.2f')))

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = "summarybankaccountinquiry.xlsx"
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response

def query_cashinbanktransaction(prevyear, dto, dfrom, chart, bankaccount):
    dfrom  = str(dfrom)[0:11]
    print "Transaction Query"
    ''' Create query '''
    cursor = connection.cursor()

    chart_condition = ''
    chart_bankaccount = ''

    if chart != '':
        chart_condition = "AND m.status = 'O' AND d.chartofaccount_id = '" + str(chart) + "'"
    if bankaccount != '':
        chart_bankaccount = "AND d.bankaccount_id = '" + str(bankaccount) + "'"

    query = "SELECT b.id, bank.code AS bankcode, bankaccounttype.description AS bankaccounttype, b.code, b.bankaccounttype_id, b.accountnumber, IFNULL(bs.beg_amount, 0) AS beg_amount, bs.beg_code, bs.year, " \
            "IFNULL(adtran.debitamount, 0) AS debitamount, IFNULL(adtran.creditamount, 0) AS creditamount, IFNULL(adtran.balcode, 'D') AS balcode, " \
            "IF (bs.beg_code = 'D' && IFNULL(adtran.balcode, 'D') = 'D' || bs.beg_code = 'C' && IFNULL(adtran.balcode, 'D') = 'C', (ABS(IFNULL(adtran.netamount, 0)) + IFNULL(bs.beg_amount, 0)), ABS((ABS(IFNULL(adtran.netamount, 0))) - IFNULL(bs.beg_amount, 0))) AS endamount, "\
            "IF (bs.beg_code = adtran.balcode, bs.beg_code, IF (ABS(IFNULL(adtran.netamount, 0)) > IFNULL(bs.beg_amount, 0), IFNULL(adtran.balcode, 'D'), IFNULL(bs.beg_code, 'D'))) AS endcode " \
            "FROM bankaccount AS b " \
            "LEFT OUTER JOIN bankaccountsummary AS bs ON (bs.bankaccount_id = b.id AND bs.year = "+str(prevyear)+") " \
            "LEFT OUTER JOIN ( " \
            "SELECT IFNULL(SUM(z.debitamount), 0) AS debitamount, IFNULL(SUM(z.creditamount), 0) AS creditamount, " \
            "(IFNULL(SUM(z.debitamount), 0) -  IFNULL(SUM(z.creditamount), 0)) AS netamount, " \
            "IF (IFNULL(SUM(z.debitamount), 0) >= IFNULL(SUM(z.creditamount), 0), 'D', 'C') AS balcode, z.bankaccount_id " \
            "FROM ( " \
            "SELECT 'AP' AS tran, d.item_counter, d.ap_num, d.ap_date, d.debitamount, d.creditamount, d.balancecode, d.bankaccount_id " \
            "FROM apdetail AS d " \
            "LEFT OUTER JOIN apmain AS m ON m.id = d.apmain_id " \
            "WHERE DATE(d.ap_date) >= '"+str(dfrom)+"' AND DATE(d.ap_date) <= '"+str(dto)+"' " \
            +str(chart_condition)+" "+str(chart_bankaccount)+"" \
            "UNION " \
            "SELECT 'CV' AS tran, d.item_counter, d.cv_num, d.cv_date, d.debitamount, d.creditamount, d.balancecode, d.bankaccount_id " \
            "FROM cvdetail AS d " \
            "LEFT OUTER JOIN cvmain AS m ON m.id = d.cvmain_id " \
            "WHERE DATE(d.cv_date) >= '"+str(dfrom)+"' AND DATE(d.cv_date) <= '"+str(dto)+"' " \
            + str(chart_condition) + " " + str(chart_bankaccount) + "" \
            "UNION " \
            "SELECT 'JV' AS tran, d.item_counter, d.jv_num, d.jv_date, d.debitamount, d.creditamount, d.balancecode, d.bankaccount_id " \
            "FROM jvdetail AS d " \
            "LEFT OUTER JOIN jvmain AS m ON m.id = d.jvmain_id " \
            "WHERE DATE(d.jv_date) >= '"+str(dfrom)+"' AND DATE(d.jv_date) <= '"+str(dto)+"' " \
            + str(chart_condition) + " " + str(chart_bankaccount) + "" \
            "UNION " \
            "SELECT 'OR' AS tran, d.item_counter, m.ornum, m.ordate, d.debitamount, d.creditamount, d.balancecode, d.bankaccount_id " \
            "FROM ormain AS m " \
            "LEFT OUTER JOIN ordetail AS d ON m.id = d.ormain_id " \
            "WHERE DATE(m.ordate) >= '"+str(dfrom)+"' AND DATE(m.ordate) <= '"+str(dto)+"' " \
            + str(chart_condition) + " " + str(chart_bankaccount) + "" \
            ") AS z " \
            "GROUP BY z.bankaccount_id ) AS adtran ON adtran.bankaccount_id = b.id " \
            "LEFT OUTER JOIN bankaccounttype AS bankaccounttype ON bankaccounttype.id = b.bankaccounttype_id " \
            "LEFT OUTER JOIN bank AS bank ON bank.id = b.bank_id " \
            "WHERE b.isdeleted = 0 ORDER BY b.code"

    print query
    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result



