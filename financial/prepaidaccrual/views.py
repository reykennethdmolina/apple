import datetime
from datetime import datetime as dt
from decimal import Decimal
import json
from dateutil.relativedelta import relativedelta
from django.db import connection
from django.views.generic import View, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, Http404, HttpResponse
from branch.models import Branch
from department.models import Department
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from companyparameter.models import Companyparameter
from accountspayable.models import Apmain
from checkvoucher.models import Cvmain
from journalvoucher.models import Jvdetail, Jvmain
from officialreceipt.models import Ormain
from subledger.models import Subledger
from chartofaccount.models import Chartofaccount
from collections import namedtuple
from django.db.models import Q
from django.template.loader import render_to_string
import io
import xlsxwriter
import datetime
from supplier.models import Supplier
from .models import PrepaidExpenseSchedule, PrepaidExpenseScheduleDetail


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'prepaidaccrual/index.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('prepaidaccrual.view_prepaidexpenseschedule'):
            raise Http404
        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['chart'] = Chartofaccount.objects.filter(Q(prepaid_enable='Y') | Q(accrual_enable='Y'), isdeleted=0, accounttype='P').order_by('accountcode')
        context['payee'] = Supplier.objects.filter
        return context


@login_required
def transgenerate(request):
    transactions = {
        '1': 'Prepaid Expenses',
        '2': 'Accrued Expenses'
    }
    report_types = {
        '1': 'Subsidiary Ledger',
        '2': 'Subsidiary Ledger per Payee',
        '3': 'Schedule',
        '4': 'YTD Schedule'
    }

    dto = request.GET["dto"]
    dfrom = request.GET["dfrom"]
    transaction = request.GET["transaction"]
    chartofaccount = request.GET["chartofaccount"]
    payeecode = request.GET["payeecode"]
    payeename = request.GET["payeename"]
    classification = request.GET["classification"]
    report = request.GET["report"]

    viewhtml = ''
    context = {}

    # 1- prepaid
    if transaction == '1':
        if report == '1':
            print "subledger 1"

            data = querySubledger(dto, dfrom, transaction, chartofaccount)
            
            tdebit = 0
            tcredit = 0
            for val in data:
                tdebit += val.debitamount
                tcredit += val.creditamount

            context['data'] = data
            context['tdebit'] = tdebit
            context['tcredit'] = tcredit
            context['transaction'] = transactions[transaction]
            context['report_type'] = report_types[report]
            context['dfrom'] = dfrom
            viewhtml = render_to_string('prepaidaccrual/transaction_result_subledger.html', context)

        elif report == '2':

            data = querySubledgerPerPayee(dto, dfrom, transaction, chartofaccount)
            
            tdebit = 0
            tcredit = 0
            current_payee_code = ''
            sub_credit_amount = 0
            sub_debit_amount = 0

            main_list = []
            sub_list = []
            for val in data:
                tdebit += val.debitamount
                tcredit += val.creditamount

                payee_code = val.payeecode

                if current_payee_code is '':
                    current_payee_code = payee_code

                if payee_code != current_payee_code:
                    sub_list.append({'document_type': 'subtotal', 'sub_debit_amount': sub_debit_amount, 'sub_credit_amount': sub_credit_amount})

                    current_payee_code = payee_code
                    sub_debit_amount = 0
                    sub_credit_amount = 0

                    main_list.append(sub_list)
                    sub_list = []

                sub_debit_amount += val.debitamount
                sub_credit_amount += val.creditamount
                sub_list.append(val) # append itemized row

            # Append the totals for the last payee
            if current_payee_code is not '':
                sub_list.append({'document_type': 'subtotal', 'sub_debit_amount': sub_debit_amount, 'sub_credit_amount': sub_credit_amount})
                main_list.append(sub_list)
            
            context['data'] = main_list
            context['tdebit'] = tdebit
            context['tcredit'] = tcredit
            context['transaction'] = transactions[transaction]
            context['report_type'] = report_types[report]
            context['dfrom'] = dfrom
            viewhtml = render_to_string('prepaidaccrual/transaction_result_subledger_per_payee.html', context)

        elif report == '3':
            print 'schedule 1'

            start_date = dt.strptime(dfrom, "%Y-%m-%d")
            end_date = dt.strptime(dto, "%Y-%m-%d")

            if start_date.month != end_date.month or start_date.year != end_date.year:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The date range is not within the same month.'
                })

            data = queryPrepaidScheduleDetail(dto, dfrom)
            import_count = countdataforimport(dto, dfrom)
            total = 0
            for val in data:
                total += val.amount

            context['data'] = data
            context['total'] = total
            context['transaction'] = transaction
            context['report_type'] = report
            context['dfrom'] = dfrom
            context['dto'] = dto
            context['import_count'] = import_count
            context['expense_accounts'] = Chartofaccount.objects.values('id', 'accountcode', 'description').filter(main=5, accounttype='P').order_by('-accountcode')
            context['departments'] = Department.objects.all().values('id', 'code', 'departmentname').order_by('code')
            context['branches'] = Branch.objects.values('id', 'code', 'description').filter(isdeleted=0)
            
            viewhtml = render_to_string('prepaidaccrual/transaction_result_schedule.html', context)
    # 2 - accrued
    elif transaction == '2':
        if report == '1':
            data = querySubledgerAccrued(dto, dfrom, transaction, payeecode, payeename, classification)

            tdebit = 0
            tcredit = 0
            for val in data:
                tdebit += val.debitamount
                tcredit += val.creditamount
                
            context['data'] = data
            context['tdebit'] = tdebit
            context['tcredit'] = tcredit
            context['transaction'] = transactions[transaction]
            context['report_type'] = report_types[report]
            context['dfrom'] = dfrom
            viewhtml = render_to_string('prepaidaccrual/accruedexpenses/transaction_result_subledger.html', context)

        elif report == '2':

            data = querySubledgerPerPayee(dto, dfrom, transaction, chartofaccount)
            
            tdebit = 0
            tcredit = 0
            current_payee_code = ''
            sub_credit_amount = 0
            sub_debit_amount = 0

            main_list = []
            sub_list = []
            for val in data:
                tdebit += val.debitamount
                tcredit += val.creditamount

                payee_code = val.payeecode

                if current_payee_code is '':
                    current_payee_code = payee_code

                if payee_code != current_payee_code:
                    sub_list.append({'document_type': 'subtotal', 'sub_debit_amount': sub_debit_amount, 'sub_credit_amount': sub_credit_amount})

                    current_payee_code = payee_code
                    sub_debit_amount = 0
                    sub_credit_amount = 0

                    main_list.append(sub_list)
                    sub_list = []

                sub_debit_amount += val.debitamount
                sub_credit_amount += val.creditamount
                sub_list.append(val) # append itemized row

            # Append the totals for the last payee
            if current_payee_code is not '':
                sub_list.append({'document_type': 'subtotal', 'sub_debit_amount': sub_debit_amount, 'sub_credit_amount': sub_credit_amount})
                main_list.append(sub_list)
            
            context['data'] = main_list
            context['tdebit'] = tdebit
            context['tcredit'] = tcredit
            context['transaction'] = transactions[transaction]
            context['report_type'] = report_types[report]
            context['dfrom'] = dfrom
            viewhtml = render_to_string('prepaidaccrual/transaction_result_subledger_per_payee.html', context)

        elif report == '3':

            start_date = dt.strptime(dfrom, "%Y-%m-%d")
            end_date = dt.strptime(dto, "%Y-%m-%d")

            if start_date.month != end_date.month or start_date.year != end_date.year:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The date range is not within the same month.'
                })

            data = queryAccruedSchedule(dto, dfrom)
            import_count = countdataforimport(dto, dfrom)
            total = 0
            for val in data:
                total += val.amount

            context['data'] = data
            context['total'] = total
            context['transaction'] = transaction
            context['report_type'] = report
            context['dfrom'] = dfrom
            context['dto'] = dto
            context['import_count'] = import_count
            context['expense_accounts'] = Chartofaccount.objects.values('id', 'accountcode', 'description').filter(main=5, accounttype='P').order_by('-accountcode')
            context['departments'] = Department.objects.all().values('id', 'code', 'departmentname').order_by('code')
            context['branches'] = Branch.objects.values('id', 'code', 'description').filter(isdeleted=0)
            
            viewhtml = render_to_string('prepaidaccrual/accruedexpenses/transaction_result_schedule.html', context)

    data = {
        'status': 'success',
        'viewhtml': viewhtml,
    }

    return JsonResponse(data)


def querySubledger(dto, dfrom, transaction, chartofaccount):
    ''' Create query '''
    # orderby = "ORDER BY document_date ASC, FIELD(a.document_type, 'AP','CV','JV','OR')"
    
    cursor = connection.cursor()
    query = """
    SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, a.document_refnum, a.document_refdate, a.amount, 
    a.balancecode, a.document_customer_id, a.document_supplier_id, ap.payeename, ap.payeecode, sup.code, sup.name, 
    IF (
        a.balancecode = 'C', a.amount, 0
    ) 
    AS creditamount, 
    IF (
        a.balancecode = 'D', a.amount, 0
    ) 
    AS debitamount, 
    IF(prep.sl_id IS NULL, 'no match', 'match') AS match_status 
    FROM subledger AS a 
    LEFT OUTER JOIN apmain AS ap ON 
        ap.apnum = a.document_num 
    LEFT OUTER JOIN prepaidexpenseschedule AS prep ON 
        prep.sl_id = a.id 
    LEFT OUTER JOIN supplier as sup ON
        a.document_supplier_id = sup.id 
    WHERE a.chartofaccount_id IN (
        SELECT id 
        FROM chartofaccount 
        WHERE main = %s 
            AND isdeleted=0 
            AND accounttype='P' 
            AND (
                (prepaid_enable = 'Y')
            )
            ORDER BY accountcode
    ) 
    AND a.status <> 'C' 
    AND (
        DATE(document_date) >= %s AND 
        DATE(document_date) <= %s
    )
    ORDER BY 
        document_date ASC, 
        FIELD(
            a.document_type, 'AP','CV','JV','OR'
        )
    """
    # print query
    cursor.execute(query, [transaction, str(dfrom), str(dto)])
    result = namedtuplefetchall(cursor)
    
    return result


def queryTaggedSubledgerAccrued(dto, dfrom):
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, a.document_refnum, a.document_refdate, a.document_refamount, a.amount, "\
            "a.balancecode, a.document_customer_id, a.document_supplier_id, a.status, a.tag_id, sup.code, sup.name, " \
            "IF (a.balancecode = 'C', a.amount, 0) AS creditamount, " \
            "IF (a.balancecode = 'D', a.amount, 0) AS debitamount " \
            "FROM subledger AS a " \
            "LEFT OUTER JOIN supplier AS sup ON a.document_supplier_id = sup.id " \
            "WHERE a.chartofaccount_id IN (SELECT id FROM chartofaccount WHERE main = '2' AND isdeleted=0 AND accounttype='P' AND accrual_enable = 'Y' ORDER BY accountcode) " \
            "AND a.document_refnum IS NOT NULL "\
            "AND a.status <> 'C' " \
            "AND DATE(document_date) >= '"+str(dfrom)+"' " \
            "AND DATE(document_date) <= '"+str(dto)+"' " \
            "ORDER BY sup.name ASC, a.tag_id, document_date ASC, a.amount DESC, FIELD(a.document_type, 'AP','CV','JV','OR')"
    
    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    
    cursor.close()
    
    return result


def querySubledgerAccrued(dto, dfrom, transaction, payeecode, payeename, classification):
    ''' Create query '''
    cursor = connection.cursor()

    conpayeecode = ""
    conpayeename = ""

    if payeecode:
        conpayeecode = " AND sup.code = '"+str(payeecode)+"'"

    if payeename:
        conpayeename = " AND sup.name LIKE '%"+str(payeename)+"%'"

    conclassification = ""
    if classification == '2':
        conclassification = " AND ((a.document_refnum IS NOT NULL OR a.document_refnum <> '') AND a.document_refamount = 0.00)"
    elif classification == '3':
        # open - first condition is for setup/credit and next condition is debit
        conclassification = " AND ((a.is_closed = 0 OR a.is_closed IS NULL) OR (a.document_refnum IS NULL OR a.document_refnum = ''))"
    elif classification == '4':
        conclassification = " AND ((a.document_refnum IS NOT NULL OR a.document_refnum <> '') AND a.document_refamount <> 0.00)"
    elif classification == '5':
        conclassification = " AND ((a.document_refnum IS NULL OR a.document_refnum = '') AND a.document_refamount = 0.00)"

    query = "SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, a.document_refnum, a.document_refdate, a.document_refamount, a.amount, "\
            "a.balancecode, a.document_customer_id, a.document_supplier_id, a.status, sup.code, sup.name, " \
            "IF (a.balancecode = 'C', a.amount, 0) AS creditamount, " \
            "IF (a.balancecode = 'D', a.amount, 0) AS debitamount " \
            "FROM subledger AS a " \
            "LEFT OUTER JOIN supplier AS sup ON a.document_supplier_id = sup.id " \
            "WHERE a.chartofaccount_id IN (SELECT id FROM chartofaccount WHERE main = '"+transaction+"' AND isdeleted=0 AND accounttype='P' AND accrual_enable = 'Y' ORDER BY accountcode) " \
            ""+str(conpayeecode)+" "+str(conpayeename)+" "+str(conclassification)+" "\
            "AND a.status <> 'C' " \
            "AND DATE(document_date) >= '"+str(dfrom)+"' " \
            "AND DATE(document_date) <= '"+str(dto)+"' " \
            "ORDER BY sup.name ASC, document_date ASC, a.amount DESC, FIELD(a.document_type, 'AP','CV','JV','OR')"
    
    cursor.execute(query)
    result = namedtuplefetchall(cursor)
    
    cursor.close()
    
    return result


def querySubledgerPerPayee(dto, dfrom, transaction, chartofaccount):
    ''' Create query '''

    cursor = connection.cursor()
    query = """
    SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, a.document_refnum, a.document_refdate, a.amount, 
    a.balancecode, IF (a.balancecode = 'C', a.amount, 0) AS creditamount, IF (a.balancecode = 'D', a.amount, 0) AS debitamount, a.document_customer_id, a.document_supplier_id, 
    ap.payeename, ap.payeecode FROM subledger AS a 
    LEFT OUTER JOIN apmain AS ap ON ap.apnum = a.document_num 
    WHERE a.chartofaccount_id IN (
        SELECT id FROM chartofaccount WHERE main = %s 
            AND isdeleted=0 
            AND accounttype='P' 
            AND (
                (%s = 1 AND prepaid_enable = 'Y')
                OR
                (%s = 2 AND accrual_enable = 'Y')
            )
            ORDER BY accountcode
        ) 
    AND DATE(document_date) >= %s 
    AND DATE(document_date) <= %s 
    ORDER BY 
        CASE
            WHEN payeecode IS NULL THEN 1  -- Place NULL values at the end
            ELSE 0  -- Place non-NULL values at the beginning
        END,
        payeecode, 
        document_date ASC, 
        FIELD(a.document_type, 'AP','CV','JV','OR')
    """
    
    cursor.execute(query, [transaction, transaction, transaction, str(dfrom), str(dto)])
    result = namedtuplefetchall(cursor)
    
    return result


def queryPrepaidSchedule(dto, dfrom):
    data = PrepaidExpenseSchedule.objects.filter(date__range=(dfrom, dto))
    return data


def queryPrepaidScheduleDetail(dto, dfrom):
    data = PrepaidExpenseScheduleDetail.objects.filter(date__range=(dfrom, dto), status='A').order_by('main__transaction_number')
    return data


def querySchedule(dto, dfrom):
    cursor = connection.cursor()
    query = """
    SELECT a.id, a.document_type, a.document_num, a.document_date, a.chartofaccount_id, a.balancecode, a.amount, a.particulars, 
    ap.apnum, ap.payeename, ap.payeecode, ap.payee_id, ap.branch_id,
    IF (a.balancecode = 'C', a.amount, 0) AS creditamount, 
    IF (a.balancecode = 'D', a.amount, 0) AS debitamount 
    FROM subledger AS a 
    LEFT OUTER JOIN apmain AS ap ON ap.apnum = a.document_num 
    WHERE a.chartofaccount_id IN (
        SELECT id 
        FROM chartofaccount 
        WHERE main = '1' 
            AND isdeleted=0 
            AND accounttype='P' 
            AND prepaid_enable = 'Y' 
            ORDER BY accountcode
    )  
    AND DATE(document_date) >= %s 
    AND DATE(document_date) <= %s
    ORDER BY ap.payeecode 
    """
    cursor.execute(query, [str(dfrom), str(dto)])
    result = namedtuplefetchall(cursor)
    
    return result


def queryScheduleById(transaction, id):
    cursor = connection.cursor()
    query = """
    SELECT a.id, a.document_type, a.document_date, a.chartofaccount_id, a.balancecode, a.amount, a.particulars, 
    ap.apnum, ap.payeename, ap.payeecode, ap.payee_id, ap.branch_id,
    IF (a.balancecode = 'C', a.amount, 0) AS creditamount, 
    IF (a.balancecode = 'D', a.amount, 0) AS debitamount 
    FROM subledger AS a 
    LEFT OUTER JOIN apmain AS ap ON ap.apnum = a.document_num 
    WHERE a.chartofaccount_id IN (
        SELECT id 
        FROM chartofaccount 
        WHERE main = %s  
            AND isdeleted=0 
            AND accounttype='P' 
            AND (
                (%s = 1 AND prepaid_enable = 'Y')
                OR
                (%s = 2 AND accrual_enable = 'Y')
            )
            ORDER BY accountcode
    ) 
    AND a.id = %s 
    LIMIT 1 
    """
    cursor.execute(query, [transaction, transaction, transaction, id])
    result = namedtuplefetchall(cursor)
    
    return result


def queryAccruedSchedule(dto, dfrom):
    cursor = connection.cursor()
    query = """
    SELECT a.id, a.document_type, a.document_num, a.document_date, a.chartofaccount_id, a.balancecode, a.amount, a.particulars, a.document_refamount, 
    sup.code, sup.name, coa.accountcode, coa.description AS coa_description, 
    IF (a.balancecode = 'C', a.amount, 0) AS creditamount, 
    IF (a.balancecode = 'D', a.amount, 0) AS debitamount 
    FROM subledger AS a 
    LEFT OUTER JOIN supplier AS sup ON
        a.document_supplier_id = sup.id 
    LEFT OUTER JOIN chartofaccount AS coa ON
        a.chartofaccount_id = coa.id 
    WHERE a.chartofaccount_id IN (
        SELECT id 
        FROM chartofaccount 
        WHERE main = '2' 
            AND isdeleted=0 
            AND accounttype='P' 
            AND accrual_enable = 'Y' 
            ORDER BY accountcode
    )  
    AND ((a.is_closed = 0 OR a.is_closed IS NULL) OR (a.document_refnum IS NULL OR a.document_refnum = '')) 
    AND DATE(document_date) >= %s 
    AND DATE(document_date) <= %s
    ORDER BY 
        sup.name ASC, 
        document_date ASC, 
        a.amount DESC, 
        FIELD(
            a.document_type, 'AP','CV','JV','OR'
        ) 
    """

    # leaving a note: script to not select ids existing in other table
    # AND a.id NOT IN (
    #     SELECT DISTINCT sl_id 
    #     FROM accruedexpense
    # )

    cursor.execute(query, [str(dfrom), str(dto)])
    result = namedtuplefetchall(cursor)
    return result


def queryAccruedScheduleReport(dto, dfrom):
    cursor = connection.cursor()
    query = """
    SELECT a.id, a.document_type, a.document_num, a.document_date, a.chartofaccount_id, a.balancecode, a.amount, a.particulars, a.document_refamount, 
    sup.code, sup.name, coa.accountcode, coa.description AS coa_description, 
    IF (a.balancecode = 'C', a.amount, 0) AS creditamount, 
    IF (a.balancecode = 'D', a.amount, 0) AS debitamount 
    FROM subledger AS a 
    LEFT OUTER JOIN supplier AS sup ON
        a.document_supplier_id = sup.id 
    LEFT OUTER JOIN chartofaccount AS coa ON
        a.chartofaccount_id = coa.id 
    WHERE a.chartofaccount_id IN (
        SELECT id 
        FROM chartofaccount 
        WHERE main = '2' 
            AND isdeleted=0 
            AND accounttype='P' 
            AND accrual_enable = 'Y' 
            ORDER BY accountcode
    )  
    AND ((a.is_closed = 0 OR a.is_closed IS NULL) OR (a.document_refnum IS NULL OR a.document_refnum = '')) 
    AND DATE(document_date) >= %s 
    AND DATE(document_date) <= %s
    ORDER BY 
        sup.name ASC, 
        document_date ASC, 
        a.amount DESC, 
        FIELD(
            a.document_type, 'AP','CV','JV','OR'
        ) 
    """

    cursor.execute(query, [str(dfrom), str(dto)])
    result = namedtuplefetchall(cursor)
    return result


@method_decorator(login_required, name='dispatch')
class ImportPrepaidScheduleView(ListView):
    model = PrepaidExpenseSchedule
    template_name = 'prepaidaccrual/import_prepaid_schedule.html'
    context_object_name = 'data_list'

    def dispatch(self, request, *args, **kwargs):
        return super(ListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ImportPrepaidScheduleView, self).get_context_data(**kwargs)
        dfrom = self.request.GET.get('from')
        dto = self.request.GET.get('to')

        datefrom = dt.strptime(dfrom, '%Y-%m-%d')
        month = datefrom.strftime("%B")
        year = datefrom.year
        
        data = querySchedule(dto, dfrom)

        tdebit = 0
        tcredit = 0
        importdata = []

        for val in data:
            if not PrepaidExpenseSchedule.objects.filter(sl_id=val.id).exists():
                importdata.append(val)
                tdebit += val.debitamount
                tcredit += val.creditamount

        context['data'] = importdata
        context['tdebit'] = tdebit
        context['tcredit'] = tcredit
        context['dfrom'] = dfrom
        context['dto'] = dto
        context['month'] = month
        context['year'] = year
       
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            dto = self.request.POST.get('dto')
            dfrom = self.request.POST.get('dfrom')
            data = querySchedule(dto, dfrom)
            
            existing = 0
            for i in data:
                schedule = PrepaidExpenseSchedule.objects.filter(sl_id=i.id)
                if not schedule.exists():
                    branch_enable = Chartofaccount.objects.filter(id=i.chartofaccount_id).values('branch_enable').first()
                    branch_id = i.branch_id if branch_enable['branch_enable'] == 'Y' else None

                    PrepaidExpenseSchedule.objects.create(
                        sl_id=i.id,
                        supplier_id=i.payee_id, 
                        coa_id=i.chartofaccount_id,
                        transaction_type=i.document_type, 
                        date=i.document_date,
                        transaction_number=i.apnum, 
                        code=i.balancecode, 
                        amount=i.amount,
                        branch_id=branch_id, 
                        particulars=i.particulars, 
                        status=1,
                        enterby_id=self.request.user.id, 
                        modifyby_id=self.request.user.id
                    )
                else:
                    existing += 1
                
            response = {
                'status': 'success',
                'existing': existing
            }

        except Exception as e:
            response = {
                'status': 'failed',
                'message': str(e)
            }

        return JsonResponse(response)


@csrf_exempt
def importprepaiddata(request):
    try:
        id = request.POST.get('id')
        transaction = 1
        data = queryScheduleById(transaction, id)

        schedule = PrepaidExpenseSchedule.objects.filter(sl_id=data[0].id)
        if not schedule.exists():
            branch_enable = Chartofaccount.objects.filter(id=data[0].chartofaccount_id).values('branch_enable').first()
            branch_id = data[0].branch_id if branch_enable['branch_enable'] == 'Y' else None

            PrepaidExpenseSchedule.objects.create(
                sl_id=data[0].id,
                supplier_id=data[0].payee_id, 
                coa_id=data[0].chartofaccount_id,
                transaction_type=data[0].document_type, 
                date=data[0].document_date,
                transaction_number=data[0].apnum, 
                code=data[0].balancecode, 
                amount=data[0].amount,
                branch_id=branch_id, 
                particulars=data[0].particulars, 
                status=1,
                enterby_id=request.user.id, 
                modifyby_id=request.user.id
            )

            response = {
                'status': 'success'
            }
        else:
            response = {
                'status': 'exists',
                'message': 'Data already exists'
            }

    except Exception as e:
        response = {
            'status': 'failed',
            'message': str(e)
        }

    return JsonResponse(response)


def namedtuplefetchall(cursor):
    desc = cursor.description
    "Return all rows from a cursor as a namedtuple"
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def countdataforimport(dto, dfrom):
    try:
        data = querySchedule(dto, dfrom)
        
        existing = 0
        for i in data:
            if PrepaidExpenseSchedule.objects.filter(sl_id=i.id).exists():
                existing += 1

        count = len(data) - existing
    except:
        count = 0
        
    return count


def amount_with_commas(number, decimal_places=2):
    return "{:,.{}f}".format(number, decimal_places)


@method_decorator(login_required, name='dispatch')
class PrepaidEntryIndexView(TemplateView):
    template_name = 'prepaidaccrual/prepaidentry/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        return context
    
    
@csrf_exempt
def prepaidgenerate(request):
    dto = request.GET["dto"]
    dfrom = request.GET["dfrom"]

    viewhtml = ''
    context = {}
    try:
        start_date = dt.strptime(dfrom, "%Y-%m-%d")
        end_date = dt.strptime(dto, "%Y-%m-%d")

        if start_date.month != end_date.month or start_date.year != end_date.year:
            return JsonResponse({
                'status': 'failed',
                'message': 'The date range is not within the same month.'
            })

        data = queryPrepaidSchedule(dto, dfrom)
        import_count = countdataforimport(dto, dfrom)
        total = 0
        for val in data:
            total += val.amount

        context['data'] = data
        context['total'] = total
        context['dfrom'] = dfrom
        context['dto'] = dto
        context['import_count'] = import_count
        context['expense_accounts'] = Chartofaccount.objects.values('id', 'accountcode', 'description', 'department_enable', 'branch_enable').filter(main=5, accounttype='P').order_by('-accountcode')
        context['departments'] = Department.objects.all().values('id', 'code', 'departmentname').order_by('code')
        context['branches'] = Branch.objects.values('id', 'code', 'description').filter(isdeleted=0)
        
        viewhtml = render_to_string('prepaidaccrual/prepaidentry/prepaid_entry.html', context)

        data = {
            'status': 'success',
            'viewhtml': viewhtml,
        }
    except Exception as e:
        print 'err: ', e
        data = {
            'status': 'failed',
            'message': str(e),
        }

    return JsonResponse(data)


@csrf_exempt
def getprepaiddata(request):
    id = request.GET.get('id')
    
    obj = PrepaidExpenseSchedule.objects.filter(pk=id).first()
    if obj is not None:
        try:
            detail = PrepaidExpenseScheduleDetail.objects.filter(main_id=id).exclude(status__in=('I', 'C')).values('id', 'date', 'month', 'amount', 'jvmain_id', 'jvnum', 'postdate').order_by('item_counter')
            
            date = obj.date
            new_date = date + relativedelta(months=1)
            start_date = new_date.strftime("%Y-%m-%d")

            if obj.start_date is not None:
                start_date = obj.start_date
                
            response = {
                'suppliercode': getattr(obj.supplier, 'code', ''),
                'suppliername': getattr(obj.supplier, 'name', ''),
                'accountcode': obj.coa.accountcode,
                'accountname': obj.coa.description,
                'date': date,
                'transactiontype': obj.transaction_type,
                'transactionnumber': obj.transaction_number,
                'code': obj.get_code_display(),
                'amount': amount_with_commas(obj.amount),
                'numberofmonth': obj.no_of_month,
                'startdate': start_date,
                'enddate': getattr(obj, 'end_date', ''),
                'computedamortization': amount_with_commas(obj.computed_amortization),
                'actualamortization': amount_with_commas(obj.actual_amortization) or 0,
                'expenseaccountid': getattr(obj.expense_account, 'id', ''),
                'expenseaccountcode': getattr(obj.expense_account, 'accountcode', ''),
                'expenseaccountdescription': getattr(obj.expense_account, 'description', ''),
                'departmentid': getattr(obj.department, 'id', ''),
                'departmentcode': getattr(obj.department, 'code', ''),
                'departmentdepartmentname': getattr(obj.department, 'departmentname', ''),
                'branchid': getattr(obj.branch, 'id', ''),
                'branchcode': getattr(obj.branch, 'code', ''),
                'branchdescription': getattr(obj.branch, 'description', ''),
                'remarks': obj.remarks,
                'particulars': obj.particulars,
                'status': obj.get_status_display(),
                'detail': list(detail),
                'responseCode': 200
            }
        except Exception as e:
            response = {
                'responseCode': 500,
                'message': 'An error occurred. '+ str(e)
            }
    else:
        response = {
            'responseCode': 404,
            'message': 'Resource not found.'
        }
        
    return JsonResponse(response)


@csrf_exempt
def saveprepaiddata(request):
    try:
        id = request.POST.get('id')
        amount = request.POST.get('amount')
        startdate = request.POST.get('startdate')
        enddate = request.POST.get('enddate')
        numberofmonth = request.POST.get('numberofmonth')
        computedamortization = request.POST.get('computedamortization')
        actualamortization = request.POST.get('actualamortization')
        expenseaccount = request.POST.get('expenseaccount')
        department = request.POST.get('department')
        branch = request.POST.get('branch')
        remarks = request.POST.get('remarks')
        particulars = request.POST.get('particulars')
        isduplicate = request.POST.get('isduplicate')

        transaction = PrepaidExpenseSchedule.objects.filter(pk=id)

        kwargs = {
            'amount': amount,
            'start_date': startdate,
            'end_date': enddate,
            'no_of_month': numberofmonth,
            'computed_amortization': computedamortization,
            'actual_amortization': actualamortization,
            'expense_account_id': expenseaccount,
            'department_id': department,
            'branch_id': branch,
            'remarks': remarks,
            'particulars': particulars,
            'modifyby_id': request.user.id,
            'modifydate': datetime.datetime.now(),
        }

        schedule = request.POST.getlist('schedule')[0]
        amortizationschedule = json.loads(schedule)

        if isduplicate == '0':

            transaction.update(**kwargs)
            
            if not PrepaidExpenseScheduleDetail.objects.filter(main_id=id).exists():

                schedule_details = [
                    PrepaidExpenseScheduleDetail(
                        item_counter = item['item'],
                        main_id = id,
                        date = item['date'],
                        month = item['month'],
                        amount = item['amount'],
                        total_amortization = item['totalamortization'],
                        ending_balance = item['endingbalance'],
                        enterby_id = request.user.id,
                        modifyby_id = request.user.id,
                        enterdate = datetime.datetime.now(),
                        modifydate = datetime.datetime.now(),
                    )
                    for item in amortizationschedule
                ]

                PrepaidExpenseScheduleDetail.objects.bulk_create(schedule_details)

            else:
                for item in amortizationschedule:
                    schedule_datail = PrepaidExpenseScheduleDetail.objects.filter(main_id=id, item_counter=item['item'])
                    
                    detail_kwargs = {
                        'amount': item['amount'],
                        'total_amortization': item['totalamortization'],
                        'ending_balance': item['endingbalance'],
                        'modifyby_id': request.user.id,
                        'modifydate': datetime.datetime.now(),
                    }
                    schedule_datail.update(**detail_kwargs)
        
        elif isduplicate == '1':

            orig = transaction[0]

            kwargs.update(
                sl_id = orig.sl_id,
                supplier_id = orig.supplier_id,
                coa_id = orig.coa_id,
                transaction_type = orig.transaction_type,
                date = orig.date,
                transaction_number = orig.transaction_number,
                code = orig.code,
                status = orig.status,
                enterby_id = request.user.id,
                enterdate = datetime.datetime.now(),
            )
            PrepaidExpenseSchedule.objects.create(**kwargs)
            
            schedule_details = [
                PrepaidExpenseScheduleDetail(
                    item_counter = item['item'],
                    main_id = id,
                    date = item['date'],
                    month = item['month'],
                    amount = item['amount'],
                    total_amortization = item['totalamortization'],
                    ending_balance = item['endingbalance'],
                    enterby_id = request.user.id,
                    modifyby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifydate = datetime.datetime.now(),
                )
                for item in amortizationschedule
            ]

            PrepaidExpenseScheduleDetail.objects.bulk_create(schedule_details)
        response = {
            'status': 'success'
        }

    except Exception as e:
        response = {
            'status': 'failed',
            'message': str(e)
        }
    
    return JsonResponse(response)


@csrf_exempt
def editamount(request):
    try:
        id = request.POST.get('id')
        amount = request.POST.get('amount')

        detail = PrepaidExpenseScheduleDetail.objects.filter(id=id)

        kwargs = {
            'amount': amount,
            'modifyby_id': request.user.id,
            'modifydate': datetime.datetime.now(),
        }

        detail.update(**kwargs)
        response = {
            'status': 'success'
        }

    except Exception as e:
        response = {
            'status': 'failed',
            'message': 'An internal error occurred. '+ str(e)
        }

    return JsonResponse(response)


@csrf_exempt
def tagaccruedexpense(request):
    accrued_expenses = []
    try:
        accrued_expenses = json.loads(request.POST.get('accrued_expenses'))
        
        main = accrued_expenses[0]['main']
        main_id = main['sl_id']
        main_document_type = main['documentType']
        main_document_number = main['documentNum']
        main_balance_code = main['balanceCode']
        main_amount = main['amount']
        
        total = accrued_expenses[2]['total']
        computed_balance = Decimal(accrued_expenses[3]['computed_balance'])
        
        breakdown = accrued_expenses[1]['breakdown']
        msg = 'Invalid'
        status = 0
        if main_document_type == 'AP':

            main = Apmain.objects.filter(isdeleted=0, apnum=main_document_number).first()
            if main:
                print 'Valid AP Transaction'
                tdate = main.apdate
                status = 1
            else:
                msg = 'Invalid AP Transaction'
                status = 0
        elif main_document_type == 'CV':

            main = Cvmain.objects.filter(isdeleted=0, cvnum=main_document_number).first()
            if main:
                print 'Valid CV Transaction'
                tdate = main.cvdate
                status = 1
            else:
                msg = 'Invalid CV Transaction'
                status = 0
        elif main_document_type == 'JV':
            
            main = Jvmain.objects.filter(isdeleted=0, jvnum=main_document_number).first()
            if main:
                print 'Valid JV Transaction'
                tdate = main.jvdate
                status = 1
            else:
                msg = 'Invalid JV Transaction'
                status = 0
        elif main_document_type == 'OR':
            
            main = Ormain.objects.filter(isdeleted=0, ornum=main_document_number).first()
            if main:
                print 'Valid OR Transaction'
                tdate = main.ordate
                status = 1
            else:
                msg = 'Invalid OR Transaction'
                status = 0

        if status == 0:
            response = {
                'status': 'failed',
                'message': msg
            }
        else:
            if main_balance_code == 'Credit':

                main_exp = Subledger.objects.filter(isdeleted=0, id=main_id).first()
                main_exp.document_reftype = main_document_type
                main_exp.document_refnum = main_exp.document_num
                main_exp.document_refamount = computed_balance
                main_exp.document_refdate = tdate
                main_exp.tag_id = main_exp.pk
                main_exp.is_closed = 0 if computed_balance > 0 else 1
                    
                main_exp.save()
                
                for exp in breakdown:
                    sub = Subledger.objects.filter(isdeleted=0, id=exp['sl_id']).first()

                    sub.document_reftype = main_document_type
                    sub.document_refnum = main_document_number
                    sub.document_refdate = tdate
                    sub.tag_id = main_exp.pk
                    sub.is_closed = 1
                    sub.save()

                response = {
                    'status': 'success'
                }
            else:
                response = {
                    'status': 'failed',
                    'message': 'Setup must be credit!'
                }
        
    except Exception as e:
        response = {
            'status': 'failed',
            'message': str(e)
        }

    return JsonResponse(response)


@method_decorator(login_required, name='dispatch')
class ManageAccruedExpenseView(ListView):
    model = Subledger
    template_name = 'prepaidaccrual/accruedexpenses/index.html'
    context_object_name = 'data_list'

    def dispatch(self, request, *args, **kwargs):
        return super(ListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ManageAccruedExpenseView, self).get_context_data(**kwargs)
        
        return context


@csrf_exempt
def manageaccruedexpense(request):
    viewhtml = ''
    context = {}
    try:
        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]
        data = queryTaggedSubledgerAccrued(dto, dfrom)

        tdebit = 0
        tcredit = 0
        for val in data:
            tdebit += val.debitamount
            tcredit += val.creditamount
            
        context['data'] = data
        context['tdebit'] = tdebit
        context['tcredit'] = tcredit
        viewhtml = render_to_string('prepaidaccrual/accruedexpenses/transaction_result_accrued.html', context)
        
        data = {
            'status': 'success',
            'viewhtml': viewhtml
        }

        return JsonResponse(data)
    except:
        return JsonResponse({
            'status': 'failed',
            'message': 'An error occured'
        })


@csrf_exempt
def untagaccruedexpense(request):
    try:
        id = request.POST.get('id')
        untag_data = Subledger.objects.filter(pk=id).first()

        amount = untag_data.amount

        tag_id = untag_data.tag_id
        main = Subledger.objects.filter(pk=tag_id).first()
        main_refamount = main.document_refamount
        main_amount = main.amount

        if Decimal(main_refamount) == 0.00:
            breakdown_count = Subledger.objects.filter(tag_id=tag_id).count()

            if breakdown_count > 2:
                main.document_refamount = amount
                main.save()
            else:

                main.document_reftype = None
                main.document_refnum = None
                main.document_refdate = None
                main.tag_id = None
                main.is_closed = 0
                main.save()

        else:
            new_refamount = Decimal(main_refamount) + Decimal(amount)

            if new_refamount == Decimal(main_amount):
                main.document_reftype = None
                main.document_refnum = None
                main.document_refdate = None
                main.document_refamount = 0.00
                main.tag_id = None
                main.is_closed = 0
            else:
                main.document_refamount = new_refamount

            main.save()
        
        untag_data.document_reftype = None
        untag_data.document_refnum = None
        untag_data.document_refdate = None
        untag_data.tag_id = None
        untag_data.is_closed = 0

        untag_data.save()

        response = {
            'status': 'success'
        }

    except Exception as e:
        response = {
            'status': 'failed',
            'message': "An unexpected error has occured: " + str(e)
        }
   
    return JsonResponse(response)


@method_decorator(login_required, name='dispatch')
class TransExcel(View):
    def get(self, request):

        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]
        transaction = request.GET["transaction"]
        chartofaccount = request.GET["chartofaccount"]
        report = request.GET["report"]

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'MM/DD/YYYY'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})
        filename = ''

        if transaction == '1':
            filename = "Prepaid Expenses Schedule.xlsx"

            # transaction = PrepaidExpenseSchedule.objects.filter(date__range=(dfrom, dto), no_of_month__isnull=False)
            schedule = PrepaidExpenseScheduleDetail.objects.filter(date__range=(dfrom, dto))
            if schedule:
                # title
                worksheet.write('A1', 'PREPAID EXPENSE SCHEDULE FOR '+ str(schedule[0].month), bold)
                # worksheet.write('A2', 'AS OF ' + str(dfrom) + ' to ' + str(dto), bold)

                # header
                worksheet.write('A4', 'Doc. Type', bold)
                worksheet.write('B4', 'Doc. Number', bold)
                worksheet.write('C4', 'Doc. Date', bold)
                worksheet.write('D4', 'Supplier Code', bold)
                worksheet.write('E4', 'Supplier Name', bold)
                worksheet.write('F4', 'Account Code', bold)
                worksheet.write('G4', 'Account Title', bold)
                worksheet.write('H4', 'Department', bold)
                worksheet.write('I4', 'Branch', bold)
                worksheet.write('J4', 'Particulars', bold)
                worksheet.write('K4', 'Debit', bold)
                worksheet.write('L4', 'Credit', bold)

                row = 5
                col = 0
                tbal = 0

                for item in schedule:
                    
                    worksheet.write(row, col, item.main.transaction_type)
                    worksheet.write(row, col+1, str(item.main.transaction_number))
                    worksheet.write(row, col+2, str(item.date))

                    if item.main.supplier.code:
                        worksheet.write(row, col+3, getattr(item.main.supplier, 'code', ''))
                        worksheet.write(row, col+4, getattr(item.main.supplier, 'name', ''))
                    else:
                        worksheet.write(row, col+3, '')
                        worksheet.write(row, col+4, ' NO CUSTOMER/SUPPLIER - N/A')

                    worksheet.write(row, col+5, getattr(item.main.expense_account, 'accountcode', ''))
                    worksheet.write(row, col+6, getattr(item.main.expense_account, 'description', ''))
                    worksheet.write(row, col+7, getattr(item.main.department, 'code', ''))
                    worksheet.write(row, col+8, getattr(item.main.branch, 'code', ''))
                    worksheet.write(row, col+9, getattr(item.main, 'particulars', ''))

                    if item.main.code == 'D':
                        worksheet.write(row, col+10, getattr(item, 'amount', ''))
                        worksheet.write(row, col+11, '')
                    elif item.main.code == 'C':
                        worksheet.write(row, col+10, '')
                        worksheet.write(row, col+11, getattr(item, 'amount', ''))
                    else:
                        worksheet.write(row, col+10, '')
                        worksheet.write(row, col+11, '')
                    

                    row += 1
                    tbal += item.amount

                worksheet.write(row, col, 'Total')
                worksheet.write(row+1, col+10, float(format(tbal, '.2f')))

            workbook.close()
             # Rewind the buffer.
            output.seek(0)
        
        elif transaction == '2':
            # accrued schedule
            filename = "Accrued Expenses Schedule.xlsx"

            # transaction = PrepaidExpenseSchedule.objects.filter(date__range=(dfrom, dto), no_of_month__isnull=False)
            schedule = queryAccruedScheduleReport(dto, dfrom)
            if schedule:
                # title
                worksheet.write('A1', 'ACCRUED EXPENSE SCHEDULE', bold)
                # worksheet.write('A2', 'AS OF ' + str(dfrom) + ' to ' + str(dto), bold)

                # header
                worksheet.write('A4', 'Doc. Type', bold)
                worksheet.write('B4', 'Doc. Number', bold)
                worksheet.write('C4', 'Doc. Date', bold)
                worksheet.write('D4', 'Payee', bold)
                worksheet.write('E4', 'Particulars', bold)
                worksheet.write('F4', 'Debit', bold)
                worksheet.write('G4', 'Credit', bold)
                worksheet.write('H4', 'Remaining Balance', bold)

                row = 5
                col = 0
                tdebit = 0
                tcredit = 0
                tremainingbal = 0
                for item in schedule:
                    worksheet.write(row, col, getattr(item, 'document_type', ''))
                    worksheet.write(row, col+1, str(getattr(item, 'document_num', '')))
                    worksheet.write(row, col+2, str(getattr(item, 'document_date', '')))

                    if item.code:
                        worksheet.write(row, col+3, getattr(item, 'name', '') + " - " + getattr(item, 'code', ''))
                    else:
                        worksheet.write(row, col+3, '')

                    worksheet.write(row, col+4, getattr(item, 'particulars', ''))

                    if item.balancecode == 'D':
                        worksheet.write(row, col+5, getattr(item, 'amount', ''))
                        worksheet.write(row, col+6, '')
                        tdebit += item.amount
                    elif item.balancecode == 'C':
                        worksheet.write(row, col+5, '')
                        worksheet.write(row, col+6, getattr(item, 'amount', ''))
                        tcredit += item.amount
                    else:
                        worksheet.write(row, col+5, '')
                        worksheet.write(row, col+6, '')

                    worksheet.write(row, col+7, getattr(item, 'document_refamount', ''))
                    tremainingbal += item.document_refamount

                    row += 1

                worksheet.write(row, col, 'Total')
                worksheet.write(row+1, col+5, float(format(tdebit, '.2f')))
                worksheet.write(row+1, col+6, float(format(tcredit, '.2f')))
                worksheet.write(row+1, col+7, float(format(tremainingbal, '.2f')))

            workbook.close()
            # Rewind the buffer.
            output.seek(0)
        else:
            return HttpResponse("Invalid request. Please try again.")

        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response
    

def lastJVNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  SUBSTRING(jvnum, 5) AS num FROM jvmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    cursor.close()
    
    return result[0]


def get_jvnum(pdate):
    jvnumlast = lastJVNumber('true')
    latestjvnum = str(jvnumlast[0])
    jvnum = pdate[:4]
    last = str(int(latestjvnum) + 1)
    zero_addon = 6 - len(last)
    for num in range(0, zero_addon):
        jvnum += '0'
    jvnum += last

    return jvnum


@csrf_exempt
def gopostprepaid(request):
    try:
        if request.method == 'POST':

            ids = request.POST.getlist('ids[]')
            pdate = request.POST['postdate']
            issue_date = request.POST['issue_date']
            
            data = PrepaidExpenseScheduleDetail.objects.filter(pk__in=ids, status='A')
            if data:

                jvnum = get_jvnum(pdate)
                
                date = dt.strptime(issue_date, "%Y-%m-%d")
                amortization_month = date.strftime('%b %Y')

                jvmain = Jvmain.objects.create(
                    jvnum = jvnum,
                    jvdate = pdate,
                    jvtype_id = 1, # No JV Type
                    jvsubtype_id = 2, # MJV
                    branch_id = 5, # Head Office
                    department_id = 45, # CN - Controllership,
                    refnum = '',
                    particular = 'To take up amortization of prepaid expenses for the month of '+ str(amortization_month),
                    currency_id = 1,
                    fxrate = 1,
                    designatedapprover_id = 225, # Arlene Astapan
                    actualapprover_id = 225, # Arlene Astapan
                    approverremarks = '',
                    responsedate = datetime.datetime.now(),
                    jvstatus = 'F',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )

                billingremarks = ''
                counter = 1
                prepaid_amount = 0
                for item in data:
                    
                    prepaid_amount += item.amount

                    if item.main.code == 'D':
                        debitamount = item.amount
                        creditamount = 0.00
                    elif item.main.code == 'C':
                        debitamount = 0.00
                        creditamount = item.amount
                    else:
                        debitamount = 0.00
                        creditamount = 0.00

                    Jvdetail.objects.create(
                        jvmain_id = jvmain.id,
                        jv_num = jvmain.jvnum,
                        jv_date = jvmain.jvdate,
                        item_counter = counter,
                        debitamount = debitamount,
                        creditamount = creditamount,
                        balancecode = item.main.code,
                        branch_id = item.main.branch_id,
                        chartofaccount_id = item.main.expense_account_id,
                        department_id = item.main.department_id,
                        status='A',
                        enterby_id = request.user.id,
                        enterdate = datetime.datetime.now(),
                        modifyby_id = request.user.id,
                        modifydate = datetime.datetime.now()
                    )

                    item.jvmain_id = jvmain.pk
                    item.jvnum = jvmain.jvnum
                    item.postdate = datetime.datetime.now()
                    item.postby_id = request.user.id
                    item.status = 'O'

                    item.save()
                    counter += 1

                prepaidexp_id = Companyparameter.objects.filter(isdeleted=0, status='A').first().coa_prepaidexp_id

                Jvdetail.objects.create(
                    jvmain_id = jvmain.id,
                    jv_num = jvmain.jvnum,
                    jv_date = jvmain.jvdate,
                    item_counter = counter,
                    debitamount = 0.00,
                    creditamount = prepaid_amount,
                    balancecode = 'C',
                    chartofaccount_id = prepaidexp_id,
                    status='A',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                    )

                jvmain.amount = prepaid_amount
                jvmain.save()

                response = {'result': 'success'}
            else:
                response = {
                    'result': 'failed',
                    'message': 'No data found available for posting.'
                }
        else:
            response = {
                'result': 'failed',
                'message': 'Invalid request'
            }
    except Exception as e:
        response = {
                'result': 'failed',
                'message': 'An error occured. '+ str(e)
            }

    return JsonResponse(response)
