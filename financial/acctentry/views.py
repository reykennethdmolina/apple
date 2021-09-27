''' Accounting Entry '''
import datetime
import random
import json
from collections import namedtuple
from django.http import JsonResponse
from django.db import connection
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from chartofaccount.models import Chartofaccount
from bankaccount.models import Bankaccount
from department.models import Department
from employee.models import Employee
from supplier.models import Supplier
from customer.models import Customer
from unit.models import Unit
from branch.models import Branch
from product.models import Product
from inputvat.models import Inputvat
from outputvat.models import Outputvat
from vat.models import Vat
from wtax.models import Wtax
from ataxcode.models import Ataxcode
from journalvoucher.models import Jvmain, Jvdetailtemp, Jvdetailbreakdowntemp, Jvdetail, Jvdetailbreakdown
from accountspayable.models import Apmain, Apdetailtemp, Apdetailbreakdowntemp, Apdetail, Apdetailbreakdown
from operationalfund.models import Ofmain, Ofdetailtemp, Ofdetailbreakdowntemp, Ofdetail, Ofdetailbreakdown, Ofitem
from checkvoucher.models import Cvmain, Cvdetailtemp, Cvdetailbreakdowntemp, Cvdetail, Cvdetailbreakdown
from officialreceipt.models import Ormain, Ordetailtemp, Ordetailbreakdowntemp, Ordetail, Ordetailbreakdown
from acknowledgementreceipt.models import Armain, Ardetailtemp, Ardetailbreakdowntemp, Ardetail, Ardetailbreakdown
from debitcreditmemo.models import Dcmain, Dcdetailtemp, Dcdetailbreakdowntemp, Dcdetail, Dcdetailbreakdown
from annoying.functions import get_object_or_None


def validatetable(table):
    if table == 'jvdetailtemp':
        data = {
            'sal': 'jv',
            'str_main': 'jvmain',
            'str_detailtemp': 'jvdetailtemp',
            'str_detail': 'jvdetail',
            'str_detailbreakdowntemp': 'jvdetailbreakdowntemp',
            'str_detailbreakdown': 'jvdetailbreakdown',
            'stmt_detailtemp': 'temp.jvmain, temp.jv_num, DATE(temp.jv_date) AS jvdate, ',
            'stmt_detailbreakdowntemp': 'temp.jvdetailtemp AS detailid, temp.particular, temp.item_counter, temp.jvmain, temp.jv_num, DATE(temp.jv_date) AS jvdate, ',
        }
    elif table == 'apdetailtemp':
        data = {
            'sal': 'ap',
            'str_main': 'apmain',
            'str_detailtemp': 'apdetailtemp',
            'str_detail': 'apdetail',
            'str_detailbreakdowntemp': 'apdetailbreakdowntemp',
            'str_detailbreakdown': 'apdetailbreakdown',
            'stmt_detailtemp': 'temp.apmain, temp.ap_num, DATE(temp.ap_date) AS apdate, ',
            'stmt_detailbreakdowntemp': 'temp.apdetailtemp AS detailid, temp.particular, temp.item_counter, temp.apmain, temp.ap_num, DATE(temp.ap_date) AS apdate, ',
        }
    elif table == 'ofdetailtemp':
        data = {
            'sal': 'of',
            'str_main': 'ofmain',
            'str_detailtemp': 'ofdetailtemp',
            'str_detail': 'ofdetail',
            'str_detailbreakdowntemp': 'ofdetailbreakdowntemp',
            'str_detailbreakdown': 'ofdetailbreakdown',
            'stmt_detailtemp': 'temp.ofmain, temp.of_num, DATE(temp.of_date) AS ofdate, ',
            'stmt_detailbreakdowntemp': 'temp.ofdetailtemp AS detailid, temp.particular, temp.item_counter, temp.ofmain, temp.of_num, DATE(temp.of_date) AS ofdate, ',
        }
    elif table == 'cvdetailtemp':
        data = {
            'sal': 'cv',
            'str_main': 'cvmain',
            'str_detailtemp': 'cvdetailtemp',
            'str_detail': 'cvdetail',
            'str_detailbreakdowntemp': 'cvdetailbreakdowntemp',
            'str_detailbreakdown': 'cvdetailbreakdown',
            'stmt_detailtemp': 'temp.cvmain, temp.cv_num, DATE(temp.cv_date) AS cvdate, ',
            'stmt_detailbreakdowntemp': 'temp.cvdetailtemp AS detailid, temp.particular, temp.item_counter, temp.cvmain, temp.cv_num, DATE(temp.cv_date) AS cvdate, ',
        }
    elif table == 'ordetailtemp':
        data = {
            'sal': 'or',
            'str_main': 'ormain',
            'str_detailtemp': 'ordetailtemp',
            'str_detail': 'ordetail',
            'str_detailbreakdowntemp': 'ordetailbreakdowntemp',
            'str_detailbreakdown': 'ordetailbreakdown',
            'stmt_detailtemp': 'temp.ormain, temp.or_num, DATE(temp.or_date) AS ordate, ',
            'stmt_detailbreakdowntemp': 'temp.ordetailtemp AS detailid, temp.particular, temp.item_counter, temp.ormain, temp.or_num, DATE(temp.or_date) AS ordate, ',
        }
    elif table == 'ardetailtemp':
        data = {
            'sal': 'ar',
            'str_main': 'armain',
            'str_detailtemp': 'ardetailtemp',
            'str_detail': 'ardetail',
            'str_detailbreakdowntemp': 'ardetailbreakdowntemp',
            'str_detailbreakdown': 'ardetailbreakdown',
            'stmt_detailtemp': 'temp.armain, temp.ar_num, DATE(temp.ar_date) AS ardate, ',
            'stmt_detailbreakdowntemp': 'temp.ardetailtemp AS detailid, temp.particular, temp.item_counter, temp.armain, temp.ar_num, DATE(temp.ar_date) AS ardate, ',
        }
    elif table == 'dcdetailtemp':
        data = {
            'sal': 'dc',
            'str_main': 'dcmain',
            'str_detailtemp': 'dcdetailtemp',
            'str_detail': 'dcdetail',
            'str_detailbreakdowntemp': 'dcdetailbreakdowntemp',
            'str_detailbreakdown': 'dcdetailbreakdown',
            'stmt_detailtemp': 'temp.dcmain, temp.dc_num, DATE(temp.dc_date) AS dcdate, ',
            'stmt_detailbreakdowntemp': 'temp.dcdetailtemp AS detailid, temp.particular, temp.item_counter, temp.dcmain, temp.dc_num, DATE(temp.dc_date) AS dcdate, ',
        }

    return data


# Create your views here.
@csrf_exempt
def maccountingentry(request):
    if request.method == 'POST':

        data_table = validatetable(request.POST['table'])

        context = {
            'bankaccount':  Bankaccount.objects.filter(isdeleted=0).order_by('code'),
            'branch':  Branch.objects.filter(isdeleted=0).order_by('description'),
            'product':  Product.objects.filter(isdeleted=0).order_by('description'),
            'inputvat':  Inputvat.objects.filter(isdeleted=0).order_by('description'),
            'outputvat':  Outputvat.objects.filter(isdeleted=0).order_by('description'),
            'vat':  Vat.objects.filter(isdeleted=0).order_by('description'),
            'wtax':  Wtax.objects.filter(isdeleted=0).order_by('description'),
            'ataxcode':  Ataxcode.objects.filter(isdeleted=0).order_by('description'),
            'table': data_table['str_detailtemp'],
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('acctentry/manualentry.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def checkchartvalidation(request):

    if request.method == 'POST':
        chartid = request.POST['chartid']
        chartdata = Chartofaccount.objects.filter(pk=chartid)

        mainunit = 0
        unit = []
        if chartdata[0].unit_enable == 'Y':
            mainunit = Chartofaccount.objects.values('mainunit').filter(pk=chartid)
            unit = Unit.objects.filter(mainunit=mainunit, isdeleted=0)

        #bank = Bank.objects.filter(isdeleted=0)
        #print unit
        data = {
            'status': 'success',
            'chart': serializers.serialize("json", chartdata),
            'unit': serializers.serialize("json", unit),
            #'bank': serializers.serialize("json", bank),
        }
    else:
        data = {
            'status': 'error',
            'chart': [],
        }
    return JsonResponse(data)

@csrf_exempt
def validateDepartment(request):
    if request.method == 'POST':
        print 'hello'
        data = {
            'status': 'success',
        }

    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def savemaccountingentry(request):

    if request.method == 'POST':

        ## Validate Chart of Account x Department

        if request.POST['department']:

            mchart = Chartofaccount.objects.filter(isdeleted=0, status='A', accounttype='P', pk=request.POST['chartofaccount']).first()
            dept = Department.objects.filter(isdeleted=0,pk=request.POST['department']).first()
            deptchart = Chartofaccount.objects.filter(isdeleted=0, status='A', pk=dept.expchartofaccount_id).first()

            print mchart.accountcode[0:2]
            print deptchart.accountcode[0:2]

            if mchart.accountcode[0:1] == '5':

                if mchart.accountcode[0:2] != deptchart.accountcode[0:2]:

                    data = {
                        'status': 'error',
                        'msg': 'Expense code did not match with the department code'
                    }

                    return JsonResponse(data)
            else:
                print 'ignore'

        print 'dito ako'

        # Save Data To JVDetail

        data_table = validatetable(request.POST['table'])

        # declare temp table
        detailtemp = ''
        exec ("detailtemp = " + data_table['str_detailtemp'].title() + "()")

        # save col_date
        exec ("detailtemp." + data_table['sal'] + "_date = datetime.datetime.now()")

        # save item_counter
        exec ("detailtemp.item_counter = len(" + data_table[
            'sal'].title() + "detailtemp.objects.all().filter(secretkey=request.POST['secretkey'])) + 1")

        tabledetailtemp = data_table['str_detailtemp']
        tablebreakdowntemp = data_table['str_detailbreakdowntemp']

        detailtemp.chartofaccount = request.POST['chartofaccount']

        if request.POST['bankaccount']:
            detailtemp.bankaccount = request.POST['bankaccount']
        if request.POST['department']:
            detailtemp.department = request.POST['department']
        if request.POST['employee']:
            detailtemp.employee = request.POST['employee']
            employee = Employee.objects.get(pk=request.POST['employee'])
            if employee.multiplestatus == 'Y':
                detailtemp.employeebreakstatus = 1
        if request.POST['supplier']:
            detailtemp.supplier = request.POST['supplier']
            supplier = Supplier.objects.get(pk=request.POST['supplier'])
            if supplier.multiplestatus == 'Y':
                detailtemp.supplierbreakstatus = 1
        if request.POST['customer']:
            detailtemp.customer = request.POST['customer']
            customer = Customer.objects.get(pk=request.POST['customer'])
            if customer.multiplestatus == 'Y':
                detailtemp.customerbreakstatus = 1
        if request.POST['unit']:
            detailtemp.unit = request.POST['unit']
        if request.POST['branch']:
            detailtemp.branch = request.POST['branch']
        if request.POST['product']:
            detailtemp.product = request.POST['product']
        if request.POST['inputvat']:
            detailtemp.inputvat = request.POST['inputvat']
        if request.POST['outputvat']:
            detailtemp.outputvat = request.POST['outputvat']
        if request.POST['vat']:
            detailtemp.vat = request.POST['vat']
        if request.POST['wtax']:
            detailtemp.wtax = request.POST['wtax']
        if request.POST['ataxcode']:
            detailtemp.ataxcode = request.POST['ataxcode']
        if request.POST['reftype']:
            detailtemp.reftype = request.POST['reftype']
        if request.POST['refnum']:
            detailtemp.refnum = request.POST['refnum']
        if request.POST['refdate']:
            detailtemp.refdate = request.POST['refdate']

        if request.POST['creditamount'] != "" and float(request.POST['creditamount'].replace(',', '')) != 0:
            balancecode = 'C'
        else:
            balancecode = 'D'

        if request.POST['creditamount']:
            detailtemp.creditamount = request.POST['creditamount'].replace(',', '')
        if request.POST['debitamount']:
            detailtemp.debitamount = request.POST['debitamount'].replace(',', '')

        detailtemp.balancecode = balancecode
        detailtemp.secretkey = request.POST['secretkey']
        detailtemp.enterby = request.user
        detailtemp.enterdate = datetime.datetime.now()
        detailtemp.modifyby = request.user
        detailtemp.modifydate = datetime.datetime.now()
        detailtemp.save()

        table = request.POST['table']
        context = {
            'tabledetailtemp': tabledetailtemp,
            'tablebreakdowntemp': tablebreakdowntemp,
            'datatemp': querystmtdetail(table, request.POST['secretkey']),
            'datatemptotal': querytotaldetail(table, request.POST['secretkey']),
        }
        data = {
            'datatable': render_to_string('acctentry/datatable.html', context),
            'status': 'success',
        }

        return JsonResponse(data)

    else:
        data = {
            'status': 'error',
            'msg': 'Something is wrong'
        }

        return JsonResponse(data)

@csrf_exempt
def breakdownentry(request):

    if request.method == 'POST':

        detailid = request.POST['detailid']
        chartid = request.POST['chartid']
        chartdata = Chartofaccount.objects.filter(isdeleted=0, status='A', \
            accounttype='P', pk=chartid)
        bankdata = []
        colspan = 1

        if chartdata[0].bankaccount_enable == 'Y':
            bankdata = Bankaccount.objects.filter(isdeleted=0).order_by('code')
            colspan += 1
        departmentdata = []
        if chartdata[0].department_enable == 'Y':
            departmentdata = Department.objects.filter(isdeleted=0).order_by('departmentname')
            colspan += 1
        employeedata = []
        if chartdata[0].employee_enable == 'Y':
            employeedata = Employee.objects.filter(isdeleted=0, \
                multiplestatus='N').order_by('firstname', 'lastname')
            colspan += 1
        supplierdata = []
        if chartdata[0].supplier_enable == 'Y':
            supplierdata = Supplier.objects.filter(isdeleted=0, \
                multiplestatus='N').order_by('name')
            colspan += 1
        customerdata = []
        if chartdata[0].customer_enable == 'Y':
            customerdata = Customer.objects.filter(isdeleted=0, \
                multiplestatus='N').order_by('name')[0:10]
            colspan += 1
        branchdata = []
        if chartdata[0].branch_enable == 'Y':
            branchdata = Branch.objects.filter(isdeleted=0).order_by('description')
            colspan += 1
        productdata = []
        if chartdata[0].product_enable == 'Y':
            productdata = Product.objects.filter(isdeleted=0).order_by('description')
            colspan += 1
        inputvatdata = []
        if chartdata[0].inputvat_enable == 'Y':
            inputvatdata = Inputvat.objects.filter(isdeleted=0).order_by('description')
            colspan += 1
        outputvatdata = []
        if chartdata[0].outputvat_enable == 'Y':
            outputvatdata = Outputvat.objects.filter(isdeleted=0).order_by('description')
            colspan += 1
        vatdata = []
        if chartdata[0].vat_enable == 'Y':
            vatdata = Vat.objects.filter(isdeleted=0).order_by('description')
            colspan += 1
        wtaxdata = []
        if chartdata[0].wtax_enable == 'Y':
            wtaxdata = Wtax.objects.filter(isdeleted=0).order_by('description')
            colspan += 1
        ataxcodedata = []
        if chartdata[0].ataxcode_enable == 'Y':
            ataxcodedata = Ataxcode.objects.filter(isdeleted=0).order_by('description')
            colspan += 1

        table = request.POST['table']
        tablemain = request.POST['tablemain']

        contexttable = {
            'tabledetailtemp': tablemain,
            'tablebreakdowntemp': table,
            'detailid': detailid,
            'datatype': request.POST['datatype'],
            'datatemp': querystmtbreakdown(tablemain, request.POST['secretkey'], \
                detailid, request.POST['datatype']),
            'datatemptotal': querytotalbreakdown(tablemain, request.POST['secretkey'], \
                detailid, request.POST['datatype']),
        }

        datainfo = getdatainfo(tablemain, detailid)

        context = {
            'tabledetailtemp': tablemain,
            'tablebreakdowntemp': table,
            'detailid': detailid,
            'datainfo': datainfo,
            'datatype': request.POST['datatype'],
            'colspan': colspan,
            'chartofaccount': list(chartdata),
            'bankaccount': list(bankdata),
            'department': list(departmentdata),
            'employee': list(employeedata),
            'supplier': list(supplierdata),
            'customer': list(customerdata),
            'branch': list(branchdata),
            'product': list(productdata),
            'inputvat': list(inputvatdata),
            'outputvat': list(outputvatdata),
            'vat': list(vatdata),
            'wtax': list(wtaxdata),
            'ataxcode': list(ataxcodedata),
            'datatablebreakdown': render_to_string('acctentry/datatablebreakdown.html', \
                contexttable),
        }

        data = {
            'breakdowndata': render_to_string('acctentry/breakdownentry.html', \
                context),
            'status': 'success',
        }

    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def savemaccountingentrybreakdown(request):
    if request.method == 'POST':
        detailid = request.POST['detailid']

        data_table = validatetable(request.POST['table'])

        # declare temp table
        detailtempbreakdown = ''
        exec("detailtempbreakdown = " + data_table['str_detailbreakdowntemp'].title() + "()")

        # save item_counter
        exec("detailtempbreakdown.item_counter = len(" + data_table['str_detailbreakdowntemp'].title() + ".objects.all().filter(secretkey=request.POST['secretkey'], " + data_table['str_detailtemp'] + "=detailid)) + 1")

        # save col_date
        exec("detailtempbreakdown." + data_table['sal'] + "_date = datetime.datetime.now()")

        # save col detailtemp
        exec("detailtempbreakdown." + data_table['sal'] + "detailtemp = request.POST['detailid']")

        detailtempbreakdown.chartofaccount = request.POST['chartofaccount']
        detailtempbreakdown.particular = request.POST['particular']
        detailtempbreakdown.datatype = request.POST['datatype']

        if request.POST['bankaccount']:
            detailtempbreakdown.bankaccount = request.POST['bankaccount']
        if request.POST['department']:
            detailtempbreakdown.department = request.POST['department']
        if request.POST['employee']:
            detailtempbreakdown.employee = request.POST['employee']
        if request.POST['supplier']:
            detailtempbreakdown.supplier = request.POST['supplier']
        if request.POST['customer']:
            detailtempbreakdown.customer = request.POST['customer']
        if request.POST['unit']:
            detailtempbreakdown.unit = request.POST['unit']
        if request.POST['branch']:
            detailtempbreakdown.branch = request.POST['branch']
        if request.POST['product']:
            detailtempbreakdown.product = request.POST['product']
        if request.POST['inputvat']:
            detailtempbreakdown.inputvat = request.POST['inputvat']
        if request.POST['outputvat']:
            detailtempbreakdown.outputvat = request.POST['outputvat']
        if request.POST['vat']:
            detailtempbreakdown.vat = request.POST['vat']
        if request.POST['wtax']:
            detailtempbreakdown.wtax = request.POST['wtax']
        if request.POST['ataxcode']:
            detailtempbreakdown.ataxcode = request.POST['ataxcode']

        if request.POST['creditamount'] != "" and float(request.POST['creditamount'].replace(',', '')) != 0:
            balancecode = 'C'
        else:
            balancecode = 'D'

        if request.POST['creditamount']:
            detailtempbreakdown.creditamount = request.POST['creditamount'].replace(',', '')
        if request.POST['debitamount']:
            detailtempbreakdown.debitamount = request.POST['debitamount'].replace(',', '')

        detailtempbreakdown.balancecode = balancecode
        detailtempbreakdown.secretkey = request.POST['secretkey']
        detailtempbreakdown.enterby = request.user
        detailtempbreakdown.enterdate = datetime.datetime.now()
        detailtempbreakdown.modifyby = request.user
        detailtempbreakdown.modifydate = datetime.datetime.now()
        detailtempbreakdown.save()

        """
        Get Data from tempbreakdown
        """

        tabledetailtemp = request.POST['table']
        tabledetailbreakdowntemp = data_table['str_detailbreakdowntemp']

        context = {
            'tabledetailtemp': tabledetailtemp,
            'tablebreakdowntemp': tabledetailbreakdowntemp,
            'detailid': detailid,
            'datatype': request.POST['datatype'],
            'datatemp': querystmtbreakdown(tabledetailtemp, request.POST['secretkey'], \
                detailid, request.POST['datatype']),
            'datatemptotal': querytotalbreakdown(tabledetailtemp, request.POST['secretkey'], \
                detailid, request.POST['datatype']),
        }
        data = {
            'datatablebreakdown': render_to_string('acctentry/datatablebreakdown.html', \
                context),
            'status': 'success',
        }
    else:
        data = {
            'status': 'error'
        }

    return JsonResponse(data)

@csrf_exempt
def deletedetailbreakdown(request):

    if request.method == 'POST':

        dataid = request.POST['id']
        secretkey = request.POST['secretkey']
        detailid = request.POST['detailid']
        datatype = request.POST['datatype']

        data_table = validatetable(request.POST['table'])

        breakdowndata = getdatainfo(data_table['str_detailbreakdowntemp'], dataid)

        # Delete if not for updation
        condition = "breakdowndata[0]." + data_table['sal'] + "main"
        if not eval(condition):
            deletequery(data_table['str_detailbreakdowntemp'], dataid)
        else:
            updatequery(data_table['str_detailbreakdowntemp'], dataid)

        tabledetailtemp = request.POST['table']
        tabledetailbreakdowntemp = data_table['str_detailbreakdowntemp']

        context = {
            'tabledetailtemp': tabledetailtemp,
            'tablebreakdowntemp': tabledetailbreakdowntemp,
            'detailid': detailid,
            'datatype': datatype,
            'datatemp': querystmtbreakdown(request.POST['table'], secretkey, \
                detailid, datatype),
            'datatemptotal': querytotalbreakdown(request.POST['table'], secretkey, \
                detailid, datatype),
        }

        data = {
            'datatablebreakdown': render_to_string('acctentry/datatablebreakdown.html', \
                context),
            'status': 'success'
        }
    else:

        data = {
            'status': 'error'
        }

    return JsonResponse(data)

@csrf_exempt
def deletedetail(request):

    if request.method == 'POST':

        dataid = request.POST['id']
        secretkey = request.POST['secretkey']

        data_table = validatetable(request.POST['table'])

        detaildata = getdatainfo(data_table['str_detailtemp'], dataid)

        detailtemp = ''

        # Delete if not for updation
        condition = "detaildata[0]." + data_table['sal'] + "main"
        if not eval(condition):
            deletequery(data_table['str_detailtemp'], dataid)
        else:
            updatequery(data_table['str_detailtemp'], dataid)

        context = {
            'tabledetailtemp': data_table['str_detailtemp'],
            'tablebreakdowntemp': data_table['str_detailbreakdowntemp'],
            'datatemp': querystmtdetail(data_table['str_detailtemp'], secretkey),
            'datatemptotal': querytotaldetail(data_table['str_detailtemp'], secretkey),
        }

        data = {
            'datatable': render_to_string('acctentry/datatable.html', context),
            'status': 'success'
        }
    else:

        data = {
            'status': 'error'
        }

    return JsonResponse(data)

def generatekey(request):
    secret_key = ''.join([random.SystemRandom().choice\
        ('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
    return secret_key

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

def executestmt(query):
    cursor = connection.cursor()

    cursor.execute(query)

    return namedtuplefetchall(cursor)

def updatequery(temptable, dataid):
    cursor = connection.cursor()

    stmt = "UPDATE " + temptable + " SET isdeleted=2 WHERE id='" + dataid + "'"

    return cursor.execute(stmt)


def updateallquery(temptable, datanum):
    data_table = validatetable(temptable)
    cursor = connection.cursor()

    stmt = "UPDATE " + temptable + " SET isdeleted=2 WHERE " + data_table['sal'] + "_num=" + "'" + datanum + "'"

    return cursor.execute(stmt)


def deletequery(temptable, dataid):
    cursor = connection.cursor()

    stmt = "DELETE FROM " + temptable + " WHERE id='" + dataid + "'"

    return cursor.execute(stmt)


def deleteallquery(temptable, secretkey):
    cursor = connection.cursor()

    data_table = validatetable(temptable)

    stmt = "DELETE FROM " + temptable + " WHERE secretkey='" + secretkey + "' AND " + data_table['sal'] + "main IS NULL"

    return cursor.execute(stmt)


def getdatainfo(temptable, dataid):
    stmt = "SELECT temp.*, FORMAT(temp.creditamount, 2) AS creditamountformatted, \
    FORMAT(temp.debitamount, 2) AS debitamountformatted, \
    chart.title AS chartofaccount_title, chart.accountcode AS chartofaccount_accountcode, \
    dept.departmentname AS department_departmentname, \
    emp.code AS employee_code, emp.lastname AS employee_lastname, \
    emp.firstname AS employee_firstname, emp.middlename AS employee_middlename, \
    sup.code AS supplier_code, sup.name AS supplier_name, \
    cust.name AS customer_name " \
           "FROM " + temptable + " AS temp \
           JOIN chartofaccount chart ON chart.id = temp.chartofaccount \
           LEFT JOIN department dept ON dept.id = temp.department \
           LEFT JOIN employee emp ON emp.id = temp.employee \
           LEFT JOIN supplier sup ON sup.id = temp.supplier \
           LEFT JOIN customer cust ON cust.id = temp.customer \
           WHERE temp.id='" + dataid + "'"

    data = executestmt(stmt)
    return list(data)

def querystmtbreakdown(temptable, secretkey, detailid, datatype):
    data_table = validatetable(temptable)

    stmt = "SELECT temp.id, temp.chartofaccount, "
    stmt += data_table['stmt_detailbreakdowntemp']

    stmt += "c.accountcode, c.description AS chartofaccountdesc, c.title AS chartofaccounttitle, " \
            "b.code AS bankaccountcode, b.accountnumber, " \
            "d.code AS departmentcode, d.departmentname, " \
            "e.code AS employeecode, CONCAT(e.firstname,' ',e.lastname) AS employeename, \
            e.multiplestatus AS employeestatus, " \
            "s.code AS suppliercode, s.name AS suppliername, \
            s.multiplestatus AS supplierstatus, " \
            "cu.code AS customercode, cu.name AS customername, \
            cu.multiplestatus AS customerstatus, " \
            "u.code AS unitcode, u.description AS unitname, " \
            "br.code AS branchcode, br.description AS branchname, " \
            "p.code AS productcode, p.description AS productname, " \
            "i.code AS inputvatcode, i.description AS inputvatname, " \
            "o.code AS outputvatcode, o.description AS outputvatname, " \
            "v.code AS vatcode, v.description AS vatname, " \
            "w.code AS wtaxcode, w.description AS wtaxname, " \
            "a.code AS ataxcode, a.description AS ataxname, " \
            "FORMAT(temp.creditamount, 2) AS creditamount, \
            FORMAT(temp.debitamount, 2) AS debitamount," \
            "temp.creditamount AS credit, temp.debitamount AS debit, temp.balancecode " \
            "FROM "+data_table['str_detailbreakdowntemp']+" AS temp " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = temp.chartofaccount " \
            "LEFT OUTER JOIN bankaccount AS b ON b.id = temp.bankaccount " \
            "LEFT OUTER JOIN department AS d ON d.id = temp.department " \
            "LEFT OUTER JOIN employee AS e ON e.id = temp.employee " \
            "LEFT OUTER JOIN supplier AS s ON s.id = temp.supplier " \
            "LEFT OUTER JOIN customer AS cu ON cu.id = temp.customer " \
            "LEFT OUTER JOIN unit AS u ON u.id = temp.unit " \
            "LEFT OUTER JOIN branch AS br ON br.id = temp.branch " \
            "LEFT OUTER JOIN product AS p ON p.id = temp.product " \
            "LEFT OUTER JOIN inputvat AS i ON i.id = temp.inputvat " \
            "LEFT OUTER JOIN outputvat AS o ON o.id = temp.outputvat " \
            "LEFT OUTER JOIN vat AS v ON v.id = temp.vat " \
            "LEFT OUTER JOIN wtax AS w ON w.id = temp.wtax " \
            "LEFT OUTER JOIN ataxcode AS a ON a.id = temp.ataxcode " \
            "WHERE temp." + data_table['sal'] + "detailtemp ='" + detailid + "' \
            AND temp.secretkey = '" + secretkey + "' \
            AND temp.datatype='" + datatype + "' \
            AND temp.isdeleted NOT IN(1,2) ORDER BY temp.item_counter"
    data = executestmt(stmt)
    return data

def querytotalbreakdown(temptable, secretkey, detailid, datatype):
    data_table = validatetable(temptable)

    querytotal = "SELECT FORMAT(SUM(IFNULL(temp.creditamount,0)), 2) AS totalcreditamount, " \
                 "FORMAT(SUM(IFNULL(temp.debitamount,0)), 2) AS totaldebitamount " \
                 "FROM "+data_table['str_detailbreakdowntemp']+" AS temp " \
                 "WHERE temp." +data_table['sal']+ "detailtemp ='" + detailid + "' \
                 AND temp.secretkey = '" + secretkey + "' \
                 AND temp.datatype='" + datatype + "' AND temp.isdeleted  NOT IN(1,2)"
    data = executestmt(querytotal)
    return data

def querystmtdetail(temptable, secretkey):
    stmt = "SELECT temp.id, temp.chartofaccount, temp.item_counter, "

    data_table = validatetable(temptable)
    stmt += data_table['stmt_detailtemp']

    stmt += "c.accountcode, c.description AS chartofaccountdesc, c.title AS chartofaccounttitle, " \
            "b.code AS bankaccountcode, b.accountnumber, " \
            "d.code AS departmentcode, d.departmentname, " \
            "e.code AS employeecode, CONCAT(e.firstname,' ',e.lastname) AS employeename, \
            e.multiplestatus AS employeestatus, " \
            "s.code AS suppliercode, s.name AS suppliername, \
            s.multiplestatus AS supplierstatus, " \
            "cu.code AS customercode, cu.name AS customername, \
            cu.multiplestatus AS customerstatus, " \
            "u.code AS unitcode, u.description AS unitname, " \
            "br.code AS branchcode, br.description AS branchname, " \
            "p.code AS productcode, p.description AS productname, " \
            "i.code AS inputvatcode, i.description AS inputvatname, " \
            "o.code AS outputvatcode, o.description AS outputvatname, " \
            "v.code AS vatcode, v.description AS vatname, " \
            "w.code AS wtaxcode, w.description AS wtaxname, " \
            "a.code AS ataxcode, a.description AS ataxname,"

    if temptable == 'dcdetailtemp':
        stmt += "temp.reftype AS reftype, temp.refnum AS refnum, temp.refdate AS refdate,"

    stmt += "temp.customerbreakstatus, temp.supplierbreakstatus, temp.employeebreakstatus, " \
            "FORMAT(temp.creditamount, 2) AS creditamount, \
            FORMAT(temp.debitamount, 2) AS debitamount, " \
            "temp.creditamount AS credit, temp.debitamount AS debit, temp.balancecode " \
            "FROM "+temptable+" AS temp " \
            "LEFT OUTER JOIN chartofaccount AS c ON c.id = temp.chartofaccount " \
            "LEFT OUTER JOIN bankaccount AS b ON b.id = temp.bankaccount " \
            "LEFT OUTER JOIN department AS d ON d.id = temp.department " \
            "LEFT OUTER JOIN employee AS e ON e.id = temp.employee " \
            "LEFT OUTER JOIN supplier AS s ON s.id = temp.supplier " \
            "LEFT OUTER JOIN customer AS cu ON cu.id = temp.customer " \
            "LEFT OUTER JOIN unit AS u ON u.id = temp.unit " \
            "LEFT OUTER JOIN branch AS br ON br.id = temp.branch " \
            "LEFT OUTER JOIN product AS p ON p.id = temp.product " \
            "LEFT OUTER JOIN inputvat AS i ON i.id = temp.inputvat " \
            "LEFT OUTER JOIN outputvat AS o ON o.id = temp.outputvat " \
            "LEFT OUTER JOIN vat AS v ON v.id = temp.vat " \
            "LEFT OUTER JOIN wtax AS w ON w.id = temp.wtax " \
            "LEFT OUTER JOIN ataxcode AS a ON a.id = temp.ataxcode " \
            "WHERE temp.secretkey = '" + secretkey + "' \
            AND temp.isdeleted  NOT IN(1,2) ORDER BY temp.balancecode desc, temp.item_counter"

    data = executestmt(stmt)
    return data

def querytotaldetail(temptable, secretkey):
    querytotal = "SELECT IFNULL(FORMAT(SUM(IFNULL(temp.creditamount,0)), 2), 0.00) \
    AS totalcreditamount, " \
                 "IFNULL(FORMAT(SUM(IFNULL(temp.debitamount,0)), 2), 0.00) \
                 AS totaldebitamount " \
                 "FROM "+temptable+" AS temp " \
                 "WHERE temp.secretkey = '" + secretkey + "' AND temp.isdeleted  NOT IN(1,2)"

    data = executestmt(querytotal)
    return data

@csrf_exempt
def updateentry(request):

    if request.method == 'POST':

        dataid = request.POST['id']
        table = request.POST['table']

        chartid = request.POST['chartid']
        chartdata = Chartofaccount.objects.filter(pk=chartid)

        mainunit = 0
        unit = []
        if chartdata[0].unit_enable == 'Y':
            mainunit = Chartofaccount.objects.values('mainunit').filter(pk=chartid)
            unit = Unit.objects.filter(mainunit=mainunit, isdeleted=0)
        info = getdatainfo(table, dataid)

        listdata = []  # create list
        for row in info:  # populate list

            data_table = validatetable(table)

            # assign main
            row_main = ''
            exec("row_main = row." + data_table['sal'] + "main")

            # assign num
            row_num = ''
            exec("row_num = row." + data_table['sal'] + "_num")

            # assign date
            row_date = ''
            exec("row_date = row." + data_table['sal'] + "_date")

            listdata.append({'id': row.id, 'item_counter': row.item_counter,
                             data_table['sal']+'main': row_main,
                             data_table['sal']+'_num': row_num,
                             data_table['sal']+'_date': str(row_date),
                             'chartofaccount': row.chartofaccount,
                             'chartofaccount_title': row.chartofaccount_title,
                             'chartofaccount_accountcode': row.chartofaccount_accountcode,
                             'department': row.department,
                             'department_departmentname': row.department_departmentname,
                             'employee': row.employee,
                             'employee_code': row.employee_code,
                             'employee_lastname': row.employee_lastname,
                             'employee_firstname': row.employee_firstname,
                             'employee_middlename': row.employee_middlename,
                             'supplier': row.supplier,
                             'supplier_code': row.supplier_code,
                             'supplier_name': row.supplier_name,
                             'customer': row.customer,
                             'customer_name': row.customer_name,
                             'unit': row.unit, 'branch': row.branch,
                             'bankaccount': row.bankaccount,
                             'product': row.product, 'inputvat': row.inputvat,
                             'outputvat': row.outputvat,
                             'vat': row.vat, 'wtax': row.wtax, 'ataxcode': row.ataxcode,
                             'customerbreakstatus': row.customerbreakstatus,
                             'supplierbreakstatus': row.supplierbreakstatus,
                             'employeebreakstatus': row.employeebreakstatus,
                             'debitamount': str(row.debitamount),
                             'creditamount': str(row.creditamount), 'amount': str(row.amount),
                             'creditamountformatted': str(row.creditamountformatted),
                             'debitamountformatted': str(row.debitamountformatted)})
        infodata = json.dumps(listdata)

        data = {
            'info': infodata,
            'status': 'success',
            'unit': serializers.serialize("json", unit),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def updatebreakentry(request):

    if request.method == 'POST':

        data_table = validatetable(request.POST['table'])

        dataid = request.POST['id']
        table = data_table['str_detailbreakdowntemp']

        info = getdatainfo(table, dataid)

        listdata = []  # create list
        for row in info:  # populate list
            # assign main
            row_main = ''
            exec("row_main = row." + data_table['sal'] + "main")

            # assign num
            row_num = ''
            exec("row_num = row." + data_table['sal'] + "_num")

            # assign date
            row_date = ''
            exec("row_date = row." + data_table['sal'] + "_date")

            listdata.append({'id': row.id, 'item_counter': row.item_counter,
                             data_table['sal']+'main': row_main,
                             data_table['sal']+'_num': row_num,
                             data_table['sal']+'_date': str(row_date),
                             'chartofaccount': row.chartofaccount, 'particular': row.particular,
                             'bankaccount': row.bankaccount,
                             'department': row.department,
                             'employee': row.employee,
                             'employee_code': row.employee_code,
                             'employee_lastname': row.employee_lastname,
                             'employee_firstname': row.employee_firstname,
                             'employee_middlename': row.employee_middlename,
                             'supplier': row.supplier,
                             'supplier_code': row.supplier_code,
                             'supplier_name': row.supplier_name,
                             'customer': row.customer,
                             'customer_name': row.customer_name,
                             'unit': row.unit, 'branch': row.branch,
                             'product': row.product, 'inputvat': row.inputvat,
                             'outputvat': row.outputvat,
                             'vat': row.vat, 'wtax': row.wtax, 'ataxcode': row.ataxcode,
                             'debitamount': str(row.debitamount), 'creditamount': str(row.creditamount),
                             'amount': str(row.amount),
                             'creditamountformatted': str(row.creditamountformatted),
                             'debitamountformatted': str(row.debitamountformatted)})
        infodata = json.dumps(listdata)
        data = {
            'info': infodata,
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def saveupdatemaccountingentry(request):
    if request.method == 'POST':

        dataid = request.POST['id']
        secretkey = request.POST['secretkey']
        table = request.POST['table']

        datastring = ""

        if request.POST['bankaccount']:
            datastring += "bankaccount='" + request.POST['bankaccount'] + "',"
        else:
            # datastring += "bankaccount='0',"
            datastring += "bankaccount=NULL,"
        if request.POST['department'] and request.POST['department'] != 'null':
            datastring += "department='" + request.POST['department'] + "',"
        else:
            # datastring += "department='0',"
            datastring += "department=NULL,"
        if request.POST['employee'] and request.POST['employee'] != 'null':
            datastring += "employee='" + request.POST['employee'] + "',"
            if request.POST.get('employeetype') == 'Y':
                datastring += "employeebreakstatus='1',"
        else:
            # datastring += "employee='0',"
            datastring += "employee=NULL,"
            datastring += "employeebreakstatus='0',"
        if request.POST['supplier'] and request.POST['supplier'] != 'null':
            datastring += "supplier='" + request.POST['supplier'] + "',"
            if request.POST.get('suppliertype') == 'Y':
                datastring += "supplierbreakstatus='1',"
        else:
            # datastring += "supplier='0',"
            datastring += "supplier=NULL,"
            datastring += "supplierbreakstatus='0',"
        if request.POST['customer'] and request.POST['customer'] != 'null':
            datastring += "customer='" + request.POST['customer'] + "',"
            if request.POST.get('customertype') == 'Y':
                datastring += "customerbreakstatus='1',"
        else:
            # datastring += "customer='0',"
            datastring += "customer=NULL,"
            datastring += "customerbreakstatus='0',"
        if request.POST['unit']:
            datastring += "unit='" + request.POST['unit'] + "',"
        else:
            # datastring += "unit='0',"
            datastring += "unit=NULL,"
        if request.POST['branch']:
            datastring += "branch='" + request.POST['branch'] + "',"
        else:
            # datastring += "branch='0',"
            datastring += "branch=NULL,"
        if request.POST['product']:
            datastring += "product='" + request.POST['product'] + "',"
        else:
            # datastring += "product='0',"
            datastring += "product=NULL,"
        if request.POST['inputvat']:
            datastring += "inputvat='" + request.POST['inputvat'] + "',"
        else:
            # datastring += "inputvat='0',"
            datastring += "inputvat=NULL,"
        if request.POST['outputvat']:
            datastring += "outputvat='" + request.POST['outputvat'] + "',"
        else:
            # datastring += "outputvat='0',"
            datastring += "outputvat=NULL,"
        if request.POST['vat']:
            datastring += "vat='" + request.POST['vat'] + "',"
        else:
            # datastring += "vat='0',"
            datastring += "vat=NULL,"
        if request.POST['wtax']:
            datastring += "wtax='" + request.POST['wtax'] + "',"
        else:
            # datastring += "wtax='0',"
            datastring += "wtax=NULL,"
        if request.POST['ataxcode']:
            datastring += "ataxcode='" + request.POST['ataxcode'] + "',"
        else:
            # datastring += "ataxcode='0',"
            datastring += "ataxcode=NULL,"

        if request.POST['reftype']:
            datastring += "reftype='" + request.POST['reftype'] + "',"
        if request.POST['refnum']:
            datastring += "refnum='" + request.POST['refnum'] + "',"
        if request.POST['refdate']:
            datastring += "refdate='" + request.POST['refdate'] + "',"

        if request.POST['creditamount'] <> "" and request.POST['creditamount'] <> '0.00':
            datastring += "balancecode='C',"
            datastring += "creditamount='" + request.POST['creditamount'].replace(',', '') + "',"
            datastring += "debitamount='0.00',"
        else:
            datastring += "balancecode='D',"
            datastring += "debitamount='" + request.POST['debitamount'].replace(',', '') + "',"
            datastring += "creditamount='0.00',"

        datastring += "isdeleted='0'"

        updatedetailtemp(table, dataid, datastring)

        data_table = validatetable(table)
        tabledetailtemp = data_table['str_detailtemp']
        tablebreakdowntemp = data_table['str_detailbreakdowntemp']

        context = {
            'tabledetailtemp': tabledetailtemp,
            'tablebreakdowntemp': tablebreakdowntemp,
            'datatemp': querystmtdetail(table, secretkey),
            'datatemptotal': querytotaldetail(table, secretkey),
        }

        data = {
            'datatable': render_to_string('acctentry/datatable.html', context),
            'status': 'success'
        }
    else:
        data = {
            'status': 'error'
        }

    return JsonResponse(data)

@csrf_exempt
def saveupdatedetailbreakdown(request):
    if request.method == 'POST':

        dataid = request.POST['id']
        detailid = request.POST['detailid']
        secretkey = request.POST['secretkey']

        data_table = validatetable(request.POST['table'])

        datastring = ""

        if request.POST['bankaccount']:
            datastring += "bankaccount='" + request.POST['bankaccount'] + "',"
        if request.POST['department']:
            datastring += "department='" + request.POST['department'] + "',"
        if request.POST['employee']:
            datastring += "employee='" + request.POST['employee'] + "',"
        if request.POST['supplier']:
            datastring += "supplier='" + request.POST['supplier'] + "',"
        if request.POST['customer']:
            datastring += "customer='" + request.POST['customer'] + "',"
        if request.POST['unit']:
            datastring += "unit='" + request.POST['unit'] + "',"
        if request.POST['branch']:
            datastring += "branch='" + request.POST['branch'] + "',"
        if request.POST['product']:
            datastring += "product='" + request.POST['product'] + "',"
        if request.POST['inputvat']:
            datastring += "inputvat='" + request.POST['inputvat'] + "',"
        if request.POST['outputvat']:
            datastring += "outputvat='" + request.POST['outputvat'] + "',"
        if request.POST['vat']:
            datastring += "vat='" + request.POST['vat'] + "',"
        if request.POST['wtax']:
            datastring += "wtax='" + request.POST['wtax'] + "',"
        if request.POST['ataxcode']:
            datastring += "ataxcode='" + request.POST['ataxcode'] + "',"

        if request.POST['creditamount'] <> "" and request.POST['creditamount'] <> '0.00':
            datastring += "balancecode='C',"
            datastring += "creditamount='" + request.POST['creditamount'].replace(',', '') + "',"
            datastring += "debitamount='0.00',"
        else:
            datastring += "balancecode='D',"
            datastring += "creditamount='0.00',"
            datastring += "debitamount='" + request.POST['debitamount'].replace(',', '') + "',"

        datastring += "particular='" + request.POST['particular'] + "'"

        updatedetailtemp(data_table['str_detailbreakdowntemp'], dataid, datastring)

        tabledetailtemp = data_table['str_detailtemp']
        tablebreakdowntemp = data_table['str_detailbreakdowntemp']

        context = {
            'tabledetailtemp': tabledetailtemp,
            'tablebreakdowntemp': tablebreakdowntemp,
            'detailid': detailid,
            'datatype': request.POST['datatype'],
            'datatemp': querystmtbreakdown(request.POST['table'], secretkey, \
                detailid, request.POST['datatype']),
            'datatemptotal': querytotalbreakdown(request.POST['table'], secretkey, \
                detailid, request.POST['datatype']),
        }

        data = {
            'datatablebreakdown': render_to_string('acctentry/datatablebreakdown.html', context),
            'status': 'success'
        }
    else:

        data = {
            'status': 'error'
        }

    return JsonResponse(data)

@csrf_exempt
def updatebreakdownstatus(request):

    if request.method == 'POST':
        table = request.POST['table']
        datatype = request.POST['datatype']
        dataid = request.POST['detailid']
        stat = request.POST['stat']
        datastring = ""
        if datatype == 'C':
            datastring = "customerbreakstatus =" + stat + ""
        if datatype == 'S':
            datastring = "supplierbreakstatus =" + stat + ""
        if datatype == 'E':
            datastring = "employeebreakstatus =" + stat + ""
        cursor = connection.cursor()

        stmt = "UPDATE " + table + " SET " + datastring + "  WHERE id='" + dataid + "'"

        cursor.execute(stmt)

        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error'
        }

    return JsonResponse(data)

def updatedetailtemp(table, dataid, datastring):
    cursor = connection.cursor()
    stmt = "UPDATE " + table + " SET "+datastring+"  WHERE id='" + dataid + "'"

    return cursor.execute(stmt)

def savedetail(source, mainid, num, secretkey, by_user, ormaindate):
    print ormaindate
    print 'sulod'

    data_table = validatetable(source)

    # detailinfo
    detailinfo = ''
    exec("detailinfo = " + data_table['str_detailtemp'].title() + ".objects.all()")
    detailinfo = detailinfo.filter(secretkey=secretkey).order_by('item_counter')

    counter = 1
    for row in detailinfo:
        detail = ''

        # table declaration
        exec("detail = " + data_table['sal'].title() + "detail()")
        # num
        exec("detail." + data_table['sal'] + "_num = num")
        # mainid
        exec("detail." + data_table['str_main'] + " = " + data_table['sal'].title() + "main.objects.get(pk=mainid)")
        # date
        exec("detail." + data_table['sal'] + "_date = row." + data_table['sal'] + "_date")

        detail.item_counter = counter
        detail.or_date = ormaindate
        detail.cv_date = ormaindate
        detail.jv_date = ormaindate
        detail.ap_date = ormaindate
        print 'upadte detail date'
        detail.chartofaccount = Chartofaccount.objects.get(pk=row.chartofaccount)
        # Return None if object is empty
        detail.bankaccount = get_object_or_None(Bankaccount, pk=row.bankaccount)
        detail.employee = get_object_or_None(Employee, pk=row.employee)
        detail.supplier = get_object_or_None(Supplier, pk=row.supplier)
        detail.customer = get_object_or_None(Customer, pk=row.customer)
        detail.department = get_object_or_None(Department, pk=row.department)
        detail.unit = get_object_or_None(Unit, pk=row.unit)
        detail.branch = get_object_or_None(Branch, pk=row.branch)
        detail.product = get_object_or_None(Product, pk=row.product)
        detail.inputvat = get_object_or_None(Inputvat, pk=row.inputvat)
        detail.outputvat = get_object_or_None(Outputvat, pk=row.outputvat)
        detail.vat = get_object_or_None(Vat, pk=row.vat)
        detail.wtax = get_object_or_None(Wtax, pk=row.wtax)
        detail.ataxcode = get_object_or_None(Ataxcode, pk=row.ataxcode)
        detail.debitamount = row.debitamount
        detail.creditamount = row.creditamount
        detail.balancecode = row.balancecode
        detail.customerbreakstatus = row.customerbreakstatus
        detail.supplierbreakstatus = row.supplierbreakstatus
        detail.employeebreakstatus = row.employeebreakstatus
        detail.modifyby = by_user
        detail.enterby = by_user
        detail.modifydate = datetime.datetime.now()

        if data_table['sal'] == 'ap':
            detail.isautogenerated = row.isautogenerated
        elif data_table['sal'] == 'dc':
            detail.reftype = row.reftype
            detail.refnum = row.refnum
            detail.refdate = row.refdate

        detail.save()
        counter += 1

        # Saving breakdown entry
        if row.customerbreakstatus <> 0:
            savebreakdownentry(by_user, num, mainid, detail.pk, row.pk, 'C', data_table)
        if row.employeebreakstatus <> 0:
            savebreakdownentry(by_user, num, mainid, detail.pk, row.pk, 'E', data_table)
        if row.supplierbreakstatus <> 0:
            savebreakdownentry(by_user, num, mainid, detail.pk, row.pk, 'S', data_table)

def savebreakdownentry(user, num, mainid, detailid, tempdetailid, dtype, data_table):

    breakdowninfo = ''
    exec("breakdowninfo = " + data_table['str_detailbreakdowntemp'].title() + ".objects.all().filter(" + data_table['str_detailtemp'] + "=tempdetailid, datatype=dtype)")
    breakdowninfo = breakdowninfo.order_by('item_counter')
    # breakdowninfo = Apdetailbreakdowntemp.objects.all().filter(apdetailtemp=tempdetailid, datatype=dtype).order_by('item_counter')

    counter = 1
    for row in breakdowninfo:

        breakdown = ''

        # breakdown = Apdetailbreakdown()
        exec("breakdown = " + data_table['str_detailbreakdown'].title() + "()")

        # breakdown.ap_num = apnum
        exec("breakdown." + data_table['sal'] + "_num = num")

        # breakdown.apmain = Apmain.objects.get(pk=mainid)
        exec("breakdown." + data_table['sal'] + "main = " + data_table['str_main'].title() + ".objects.get(pk=mainid)")

        # breakdown.apdetail = Apdetail.objects.get(pk=detailid)
        exec("breakdown." + data_table['str_detail'] + " = " + data_table['str_detail'].title() + ".objects.get(pk=detailid)")

        # breakdown.ap_date = row.ap_date
        exec("breakdown." + data_table['sal'] + "_date = row." + data_table['sal'] + "_date")

        breakdown.item_counter = counter
        breakdown.chartofaccount = Chartofaccount.objects.get(pk=row.chartofaccount)
        breakdown.particular = row.particular
        # Return None if object is empty
        breakdown.bankaccount = get_object_or_None(Bankaccount, pk=row.bankaccount)
        breakdown.employee = get_object_or_None(Employee, pk=row.employee)
        breakdown.supplier = get_object_or_None(Supplier, pk=row.supplier)
        breakdown.customer = get_object_or_None(Customer, pk=row.customer)
        breakdown.department = get_object_or_None(Department, pk=row.department)
        breakdown.unit = get_object_or_None(Unit, pk=row.unit)
        breakdown.branch = get_object_or_None(Branch, pk=row.branch)
        breakdown.product = get_object_or_None(Product, pk=row.product)
        breakdown.inputvat = get_object_or_None(Inputvat, pk=row.inputvat)
        breakdown.outputvat = get_object_or_None(Outputvat, pk=row.outputvat)
        breakdown.vat = get_object_or_None(Vat, pk=row.vat)
        breakdown.wtax = get_object_or_None(Wtax, pk=row.wtax)
        breakdown.ataxcode = get_object_or_None(Ataxcode, pk=row.ataxcode)
        breakdown.debitamount = row.debitamount
        breakdown.creditamount = row.creditamount
        breakdown.balancecode = row.balancecode
        breakdown.datatype = dtype
        breakdown.customerbreakstatus = row.customerbreakstatus
        breakdown.supplierbreakstatus = row.supplierbreakstatus
        breakdown.employeebreakstatus = row.employeebreakstatus
        breakdown.modifyby = user
        breakdown.enterby = user
        breakdown.modifydate = datetime.datetime.now()
        breakdown.save()
        counter += 1

    return True


def updatedetail(source, mainid, num, secretkey, by_user, ormaindate):

    print ormaindate
    print 'sulod'

    data_table = validatetable(source)

    detailinfo = ''
    exec("detailinfo = " + data_table['str_detailtemp'].title() + ".objects.all()")
    detailinfo = detailinfo.filter(secretkey=secretkey).order_by('item_counter')

    print detailinfo

    counter = 1
    for row in detailinfo:
        if eval("row." + data_table['str_main']):
            if row.isdeleted == 0:
                #update
                # detail = Jvdetail.objects.get(pk=row.jvdetail)
                exec("detail = " + data_table['str_detail'].title() + ".objects.get(pk=row." + data_table['str_detail'] + ")")

                detail.item_counter = counter
                # detail date
                detail.or_date = ormaindate
                detail.cv_date = ormaindate
                detail.jv_date = ormaindate
                detail.ap_date = ormaindate
                detail.chartofaccount = Chartofaccount.objects.get(pk=row.chartofaccount)
                # Return None if object is empty
                detail.bankaccount = get_object_or_None(Bankaccount, pk=row.bankaccount)
                detail.employee = get_object_or_None(Employee, pk=row.employee)
                detail.supplier = get_object_or_None(Supplier, pk=row.supplier)
                detail.customer = get_object_or_None(Customer, pk=row.customer)
                detail.department = get_object_or_None(Department, pk=row.department)
                detail.unit = get_object_or_None(Unit, pk=row.unit)
                detail.branch = get_object_or_None(Branch, pk=row.branch)
                detail.product = get_object_or_None(Product, pk=row.product)
                detail.inputvat = get_object_or_None(Inputvat, pk=row.inputvat)
                detail.outputvat = get_object_or_None(Outputvat, pk=row.outputvat)
                detail.vat = get_object_or_None(Vat, pk=row.vat)
                detail.wtax = get_object_or_None(Wtax, pk=row.wtax)
                detail.ataxcode = get_object_or_None(Ataxcode, pk=row.ataxcode)
                detail.debitamount = row.debitamount
                detail.creditamount = row.creditamount
                detail.balancecode = row.balancecode
                detail.customerbreakstatus = row.customerbreakstatus
                detail.supplierbreakstatus = row.supplierbreakstatus
                detail.employeebreakstatus = row.employeebreakstatus
                detail.modifyby = by_user
                detail.modifydate = datetime.datetime.now()

                if data_table['sal'] == 'ap':
                    detail.isautogenerated = row.isautogenerated
                elif data_table['sal'] == 'dc':
                    detail.reftype = row.reftype
                    detail.refnum = row.refnum
                    detail.refdate = row.refdate

                detail.save()

                datatype = 'X'
                if row.customerbreakstatus <> 0 and row.customerbreakstatus is not None:
                    datatype = 'C'
                if row.employeebreakstatus <> 0 and row.employeebreakstatus is not None:
                    datatype = 'E'
                if row.supplierbreakstatus <> 0 and row.supplierbreakstatus is not None:
                    datatype = 'S'

                breakdowninfo = ''
                exec("breakdowninfo = " + data_table['str_detailbreakdowntemp'].title() + ".objects.all()")
                exec("breakdowninfo = breakdowninfo.filter(" + data_table['str_detailtemp'] + "=row.pk, datatype=datatype)")
                breakdowninfo = breakdowninfo.order_by('item_counter')
                # breakdowninfo = Jvdetailbreakdowntemp.objects.all().filter(jvdetailtemp=row.pk, datatype=datatype).order_by('item_counter')

                counterb = 1
                for brow in breakdowninfo:
                    if eval("brow." + data_table['str_main']):
                        if brow.isdeleted == 0:
                            #update
                            # breakdown = Jvdetailbreakdown.objects.get(pk=brow.jvdetailbreakdown)
                            exec("breakdown = " + data_table['str_detailbreakdown'].title() + ".objects.get(pk=brow." + data_table['str_detailbreakdown'] + ")")

                            breakdown.item_counter = counterb
                            breakdown.chartofaccount = Chartofaccount.objects.\
                                get(pk=brow.chartofaccount)
                            breakdown.particular = brow.particular
                            # Return None if object is empty
                            breakdown.bankaccount = get_object_or_None(Bankaccount, \
                                pk=brow.bankaccount)
                            breakdown.employee = get_object_or_None(Employee, \
                                pk=brow.employee)
                            breakdown.supplier = get_object_or_None(Supplier, \
                                pk=brow.supplier)
                            breakdown.customer = get_object_or_None(Customer, \
                                pk=brow.customer)
                            breakdown.department = get_object_or_None(Department, \
                                pk=brow.department)
                            breakdown.unit = get_object_or_None(Unit, pk=brow.unit)
                            breakdown.branch = get_object_or_None(Branch, pk=brow.branch)
                            breakdown.product = get_object_or_None(Product, pk=brow.product)
                            breakdown.inputvat = get_object_or_None(Inputvat, \
                                pk=brow.inputvat)
                            breakdown.outputvat = get_object_or_None(Outputvat, \
                                pk=brow.outputvat)
                            breakdown.vat = get_object_or_None(Vat, pk=brow.vat)
                            breakdown.wtax = get_object_or_None(Wtax, pk=brow.wtax)
                            breakdown.ataxcode = get_object_or_None(Ataxcode, pk=brow.ataxcode)
                            breakdown.debitamount = brow.debitamount
                            breakdown.creditamount = brow.creditamount
                            breakdown.balancecode = brow.balancecode
                            breakdown.datatype = datatype
                            breakdown.customerbreakstatus = brow.customerbreakstatus
                            breakdown.supplierbreakstatus = brow.supplierbreakstatus
                            breakdown.employeebreakstatus = brow.employeebreakstatus
                            breakdown.modifyby = by_user
                            breakdown.modifydate = datetime.datetime.now()
                            breakdown.save()
                            counterb = 1
                        if brow.isdeleted == 2:
                            #delete
                            # instance = Jvdetailbreakdown.objects.get(pk=brow.jvdetailbreakdown)
                            exec("instance = " + data_table['str_detailbreakdown'].title() + ".objects.get(pk=brow." + data_table['str_detailbreakdown'] + ")")

                            instance.delete()
                    if not eval("brow." + data_table['str_main']):
                        #add
                        breakdown = ''

                        # breakdown = Jvdetailbreakdown()
                        exec("breakdown = " + data_table['str_detailbreakdown'].title() + "()")

                        # breakdown.jv_num = num
                        exec("breakdown." + data_table['sal'] + "_num = num")

                        # breakdown.jvmain = Jvmain.objects.get(pk=mainid)
                        exec("breakdown." + data_table['str_main'] + " = " + data_table['str_main'].title() + ".objects.get(pk=mainid)")

                        # breakdown.jvdetail = Jvdetail.objects.get(pk=detail.pk)
                        exec("breakdown." + data_table['str_detail'] + " = " + data_table['str_detail'].title() + ".objects.get(pk=detail.pk)")

                        # breakdown.jv_date = brow.jv_date
                        exec("breakdown." + data_table['sal'] + "_date = brow." + data_table['sal'] + "_date")

                        breakdown.item_counter = counterb
                        breakdown.chartofaccount = Chartofaccount.objects.get(\
                            pk=brow.chartofaccount)
                        breakdown.particular = brow.particular
                        # Return None if object is empty
                        breakdown.bankaccount = get_object_or_None(Bankaccount, \
                            pk=brow.bankaccount)
                        breakdown.employee = get_object_or_None(Employee, pk=brow.employee)
                        breakdown.supplier = get_object_or_None(Supplier, pk=brow.supplier)
                        breakdown.customer = get_object_or_None(Customer, pk=brow.customer)
                        breakdown.department = get_object_or_None(Department, \
                            pk=brow.department)
                        breakdown.unit = get_object_or_None(Unit, pk=brow.unit)
                        breakdown.branch = get_object_or_None(Branch, pk=brow.branch)
                        breakdown.product = get_object_or_None(Product, pk=brow.product)
                        breakdown.inputvat = get_object_or_None(Inputvat, pk=brow.inputvat)
                        breakdown.outputvat = get_object_or_None(Outputvat, pk=brow.outputvat)
                        breakdown.vat = get_object_or_None(Vat, pk=brow.vat)
                        breakdown.wtax = get_object_or_None(Wtax, pk=brow.wtax)
                        breakdown.ataxcode = get_object_or_None(Ataxcode, pk=brow.ataxcode)
                        breakdown.debitamount = brow.debitamount
                        breakdown.creditamount = brow.creditamount
                        breakdown.balancecode = brow.balancecode
                        breakdown.datatype = datatype
                        breakdown.customerbreakstatus = brow.customerbreakstatus
                        breakdown.supplierbreakstatus = brow.supplierbreakstatus
                        breakdown.employeebreakstatus = brow.employeebreakstatus
                        breakdown.modifyby = by_user
                        breakdown.enterby = by_user
                        breakdown.modifydate = datetime.datetime.now()
                        breakdown.save()
                        counterb = 1

                counter += 1
            if row.isdeleted == 2:
                #delete
                instance = ''
                instancebreakdown = ''

                # instance = Jvdetail.objects.get(pk=row.jvdetail)
                exec("instance = " + data_table['str_detail'].title() + ".objects.get(pk=row." + data_table['str_detail'] + ")")

                instance.delete()

                # instancebreakdown = Jvdetailbreakdown.objects.filter(jvdetail=row.jvdetail)
                exec("instancebreakdown = " + data_table['str_detailbreakdown'].title() + ".objects.filter(" + data_table['str_detail'] + "=row." + data_table['str_detail'] + ")")

                instancebreakdown.delete()
        if not eval("row." + data_table['str_main']):
            #add
            detail = ''

            # detail = Jvdetail()
            exec("detail = " + data_table['str_detail'].title() + "()")

            # detail.jv_num = num
            exec("detail." + data_table['sal'] + "_num = num")

            # detail.jvmain = Jvmain.objects.get(pk=mainid)
            exec("detail." + data_table['str_main'] + " = " + data_table['str_main'].title() + ".objects.get(pk=mainid)")

            # detail.jv_date = row.jv_date
            exec("detail." + data_table['sal'] + "_date = row." + data_table['sal'] + "_date")

            # for OF only (save ofitem)
            if data_table['sal'] == 'of':
                detail.ofitem = get_object_or_None(Ofitem, pk=row.ofitem)

            detail.item_counter = counter
            detail.or_date = ormaindate
            detail.cv_date = ormaindate
            detail.jv_date = ormaindate
            detail.ap_date = ormaindate
            detail.chartofaccount = Chartofaccount.objects.get(pk=row.chartofaccount)
            # Return None if object is empty
            detail.bankaccount = get_object_or_None(Bankaccount, pk=row.bankaccount)
            detail.employee = get_object_or_None(Employee, pk=row.employee)
            detail.supplier = get_object_or_None(Supplier, pk=row.supplier)
            detail.customer = get_object_or_None(Customer, pk=row.customer)
            detail.department = get_object_or_None(Department, pk=row.department)
            detail.unit = get_object_or_None(Unit, pk=row.unit)
            detail.branch = get_object_or_None(Branch, pk=row.branch)
            detail.product = get_object_or_None(Product, pk=row.product)
            detail.inputvat = get_object_or_None(Inputvat, pk=row.inputvat)
            detail.outputvat = get_object_or_None(Outputvat, pk=row.outputvat)
            detail.vat = get_object_or_None(Vat, pk=row.vat)
            detail.wtax = get_object_or_None(Wtax, pk=row.wtax)
            detail.ataxcode = get_object_or_None(Ataxcode, pk=row.ataxcode)
            detail.debitamount = row.debitamount
            detail.creditamount = row.creditamount
            detail.balancecode = row.balancecode
            detail.customerbreakstatus = row.customerbreakstatus
            detail.supplierbreakstatus = row.supplierbreakstatus
            detail.employeebreakstatus = row.employeebreakstatus
            detail.modifyby = by_user
            detail.enterby = by_user
            detail.modifydate = datetime.datetime.now()
            detail.save()

            # Saving breakdown entry
            if row.customerbreakstatus <> 0:
                savebreakdownentry(by_user, num, mainid, detail.pk, row.pk, 'C', data_table)
            if row.employeebreakstatus <> 0:
                savebreakdownentry(by_user, num, mainid, detail.pk, row.pk, 'E', data_table)
            if row.supplierbreakstatus <> 0:
                savebreakdownentry(by_user, num, mainid, detail.pk, row.pk, 'S', data_table)

            counter += 1
