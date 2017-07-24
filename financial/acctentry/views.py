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
from journalvoucher.models import Jvdetailtemp, Jvdetailbreakdowntemp

# Create your views here.
@csrf_exempt
def maccountingentry(request):
    if request.method == 'POST':

        context = {
            'chartofaccount':  Chartofaccount.objects.filter(isdeleted=0, status='A', \
                accounttype='P').order_by('accountcode')[0:1000],
            'bankaccount':  Bankaccount.objects.filter(isdeleted=0).order_by('code'),
            'department':  Department.objects.filter(isdeleted=0).order_by('departmentname'),
            'employee':  Employee.objects.filter(isdeleted=0).order_by('firstname', 'lastname'),
            'supplier':  Supplier.objects.filter(isdeleted=0).order_by('name'),
            'customer':  Customer.objects.filter(isdeleted=0).order_by('name')[0:100],
            'branch':  Branch.objects.filter(isdeleted=0).order_by('description'),
            'product':  Product.objects.filter(isdeleted=0).order_by('description'),
            'inputvat':  Inputvat.objects.filter(isdeleted=0).order_by('description'),
            'outputvat':  Outputvat.objects.filter(isdeleted=0).order_by('description'),
            'vat':  Vat.objects.filter(isdeleted=0).order_by('description'),
            'wtax':  Wtax.objects.filter(isdeleted=0).order_by('description'),
            'ataxcode':  Ataxcode.objects.filter(isdeleted=0).order_by('description'),
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
def savemaccountingentry(request):

    if request.method == 'POST':
        # Save Data To JVDetail
        if request.POST['table'] == 'jvdetailtemp':
            detailtemp = Jvdetailtemp()
            detailtemp.item_counter = len(Jvdetailtemp.objects.all().\
                filter(secretkey=request.POST['secretkey'])) + 1

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

        if request.POST['creditamount'] <> "":
            balancecode = 'C'
        else:
            balancecode = 'D'

        if request.POST['creditamount']:
            detailtemp.creditamount = request.POST['creditamount'].replace(',', '')
        if request.POST['debitamount']:
            detailtemp.debitamount = request.POST['debitamount'].replace(',', '')

        detailtemp.balancecode = balancecode
        detailtemp.secretkey = request.POST['secretkey']
        detailtemp.jv_date = datetime.datetime.now()
        detailtemp.enterby = request.user
        detailtemp.enterdate = datetime.datetime.now()
        detailtemp.modifyby = request.user
        detailtemp.modifydate = datetime.datetime.now()
        detailtemp.save()

        table = request.POST['table']
        context = {
            'datatemp': querystmtdetail(table, request.POST['secretkey']),
            'datatemptotal': querytotaldetail(table, request.POST['secretkey']),
        }
        data = {
            'datatable': render_to_string('acctentry/datatable.html', context),
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
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
        contexttable = {
            'detailid': detailid,
            'datatype': request.POST['datatype'],
            'datatemp': querystmtbreakdown(table, request.POST['secretkey'], \
                detailid, request.POST['datatype']),
            'datatemptotal': querytotalbreakdown(table, request.POST['secretkey'], \
                detailid, request.POST['datatype']),
        }

        tablemain = request.POST['tablemain']
        datainfo = getdatainfo(tablemain, detailid)

        context = {
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
        # Save Data To JVDetail
        detailid = request.POST['detailid']
        if request.POST['table'] == 'jvdetailbreakdowntemp':
            detailtempbreakdown = Jvdetailbreakdowntemp()
            detailtempbreakdown.item_counter = len(Jvdetailbreakdowntemp.objects.all().\
                filter(secretkey=request.POST['secretkey'], jvdetailtemp=detailid)) + 1

        detailtempbreakdown.chartofaccount = request.POST['chartofaccount']
        detailtempbreakdown.jvdetailtemp = request.POST['detailid']
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

        if request.POST['creditamount'] <> "":
            balancecode = 'C'
        else:
            balancecode = 'D'

        if request.POST['creditamount']:
            detailtempbreakdown.creditamount = request.POST['creditamount'].replace(',', '')
        if request.POST['debitamount']:
            detailtempbreakdown.debitamount = request.POST['debitamount'].replace(',', '')

        detailtempbreakdown.balancecode = balancecode
        detailtempbreakdown.secretkey = request.POST['secretkey']
        detailtempbreakdown.jv_date = datetime.datetime.now()
        detailtempbreakdown.enterby = request.user
        detailtempbreakdown.enterdate = datetime.datetime.now()
        detailtempbreakdown.modifyby = request.user
        detailtempbreakdown.modifydate = datetime.datetime.now()
        detailtempbreakdown.save()

        """
        Get Data from tempbreakdown
        """

        table = request.POST['table']
        context = {
            'detailid': detailid,
            'datatype': request.POST['datatype'],
            'datatemp': querystmtbreakdown(table, request.POST['secretkey'], \
                detailid, request.POST['datatype']),
            'datatemptotal': querytotalbreakdown(table, request.POST['secretkey'], \
                detailid, request.POST['datatype']),
        }
        #print(context)
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
        table = request.POST['table']
        detailid = request.POST['detailid']
        datatype = request.POST['datatype']


        breakdowndata = getdatainfo(table, dataid)

        # Delete if not for updation
        if not breakdowndata[0].jvmain:
            deletequery(table, dataid)
        else:
            updatequery(table, dataid)

        context = {
            'detailid': detailid,
            'datatype': datatype,
            'datatemp': querystmtbreakdown(table, secretkey, \
                detailid, datatype),
            'datatemptotal': querytotalbreakdown(table, secretkey, \
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
        table = request.POST['table']

        detaildata = getdatainfo(table, dataid)

        # Delete if not for updation
        if not detaildata[0].jvmain:
            deletequery(table, dataid)
        else:
            updatequery(table, dataid)

        context = {
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

def deletequery(temptable, dataid):
    cursor = connection.cursor()

    stmt = "DELETE FROM " + temptable + " WHERE id='" + dataid + "'"

    return cursor.execute(stmt)


def getdatainfo(temptable, dataid):
    stmt = "SELECT temp.*, FORMAT(temp.creditamount, 2) AS creditamountformatted, \
    FORMAT(temp.debitamount, 2) AS debitamountformatted " \
           "FROM " + temptable + " AS temp WHERE id='" + dataid + "'"

    data = executestmt(stmt)
    return list(data)

def querystmtbreakdown(temptable, secretkey, detailid, datatype):
    stmt = "SELECT temp.id, temp.chartofaccount, temp.jvdetailtemp AS detailid, \
    temp.particular, temp.item_counter, temp.jvmain, temp.jv_num, DATE(temp.jv_date) AS jvdate, " \
                "c.accountcode, c.description AS chartofaccountdesc, " \
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
                "LEFT OUTER JOIN inputvat AS i ON i.id = temp.product " \
                "LEFT OUTER JOIN outputvat AS o ON o.id = temp.outputvat " \
                "LEFT OUTER JOIN vat AS v ON v.id = temp.vat " \
                "LEFT OUTER JOIN wtax AS w ON w.id = temp.wtax " \
                "LEFT OUTER JOIN ataxcode AS a ON a.id = temp.ataxcode " \
                "WHERE temp.jvdetailtemp ='" + detailid + "' \
                AND temp.secretkey = '" + secretkey + "' \
                AND temp.datatype='" + datatype + "' \
                AND temp.isdeleted NOT IN(1,2) ORDER BY temp.item_counter"
    data = executestmt(stmt)
    return data

def querytotalbreakdown(temptable, secretkey, detailid, datatype):
    querytotal = "SELECT FORMAT(SUM(IFNULL(temp.creditamount,0)), 2) AS totalcreditamount, " \
                 "FORMAT(SUM(IFNULL(temp.debitamount,0)), 2) AS totaldebitamount " \
                 "FROM "+temptable+" AS temp " \
                 "WHERE temp.jvdetailtemp ='" + detailid + "' \
                 AND temp.secretkey = '" + secretkey + "' \
                 AND temp.datatype='" + datatype + "' AND temp.isdeleted  NOT IN(1,2)"
    data = executestmt(querytotal)
    return data

def querystmtdetail(temptable, secretkey):
    stmt = "SELECT temp.id, temp.chartofaccount, temp.item_counter, \
    temp.jvmain, temp.jv_num, DATE(temp.jv_date) AS jvdate, " \
                "c.accountcode, c.description AS chartofaccountdesc, " \
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
                "a.code AS ataxcode, a.description AS ataxname," \
                "temp.customerbreakstatus, temp.supplierbreakstatus, temp.employeebreakstatus, " \
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
                "LEFT OUTER JOIN inputvat AS i ON i.id = temp.product " \
                "LEFT OUTER JOIN outputvat AS o ON o.id = temp.outputvat " \
                "LEFT OUTER JOIN vat AS v ON v.id = temp.vat " \
                "LEFT OUTER JOIN wtax AS w ON w.id = temp.wtax " \
                "LEFT OUTER JOIN ataxcode AS a ON a.id = temp.ataxcode " \
                "WHERE temp.secretkey = '" + secretkey + "' \
                AND temp.isdeleted  NOT IN(1,2) ORDER BY temp.item_counter"

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
            listdata.append({'id': row.id, 'item_counter': row.item_counter,
                             'jvmain': row.jvmain, 'jv_num': row.jv_num, 
                             'jv_date': str(row.jv_date),
                             'chartofaccount': row.chartofaccount, 'bankaccount': row.bankaccount,
                             'department': row.department, 'employee': row.employee,
                             'supplier': row.supplier,
                             'customer': row.customer, 'unit': row.unit, 'branch': row.branch,
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

        dataid = request.POST['id']
        table = request.POST['table']

        info = getdatainfo(table, dataid)

        listdata = []  # create list
        for row in info:  # populate list
            listdata.append({'id': row.id, 'item_counter': row.item_counter,
                             'jvmain': row.jvmain, 'jv_num': row.jv_num, 
                             'jv_date': str(row.jv_date),
                             'chartofaccount': row.chartofaccount, 'particular': row.particular,
                             'bankaccount': row.bankaccount,
                             'department': row.department, 'employee': row.employee,
                             'supplier': row.supplier,
                             'customer': row.customer, 'unit': row.unit, 'branch': row.branch,
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
            datastring += "bankaccount='0',"
        if request.POST['department']:
            datastring += "department='" + request.POST['department'] + "',"
        else:
            datastring += "department='0',"
        if request.POST['employee']:
            datastring += "employee='" + request.POST['employee'] + "',"
            if request.POST['employeetype'] == 'Y':
                datastring += "employeebreakstatus='1',"
        else:
            datastring += "employee='0',"
            datastring += "employeebreakstatus='0',"
        if request.POST['supplier']:
            datastring += "supplier='" + request.POST['supplier'] + "',"
            if request.POST['suppliertype'] == 'Y':
                datastring += "supplierbreakstatus='1',"
        else:
            datastring += "supplier='0',"
            datastring += "supplierbreakstatus='0',"
        if request.POST['customer']:
            datastring += "customer='" + request.POST['customer'] + "',"
            if request.POST['customertype'] == 'Y':
                datastring += "customerbreakstatus='1',"
        else:
            datastring += "customer='0',"
            datastring += "customerbreakstatus='0',"
        if request.POST['unit']:
            datastring += "unit='" + request.POST['unit'] + "',"
        else:
            datastring += "unit='0',"
        if request.POST['branch']:
            datastring += "branch='" + request.POST['branch'] + "',"
        else:
            datastring += "branch='0',"
        if request.POST['product']:
            datastring += "product='" + request.POST['product'] + "',"
        else:
            datastring += "product='0',"
        if request.POST['inputvat']:
            datastring += "inputvat='" + request.POST['inputvat'] + "',"
        else:
            datastring += "inputvat='0',"
        if request.POST['outputvat']:
            datastring += "outputvat='" + request.POST['outputvat'] + "',"
        else:
            datastring += "outputvat='0',"
        if request.POST['vat']:
            datastring += "vat='" + request.POST['vat'] + "',"
        else:
            datastring += "vat='0',"
        if request.POST['wtax']:
            datastring += "wtax='" + request.POST['wtax'] + "',"
        else:
            datastring += "wtax='0',"
        if request.POST['ataxcode']:
            datastring += "ataxcode='" + request.POST['ataxcode'] + "',"
        else:
            datastring += "ataxcode='0',"

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

        context = {
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
        table = request.POST['table']

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

        updatedetailtemp(table, dataid, datastring)

        context = {
            'detailid': detailid,
            'datatype': request.POST['datatype'],
            'datatemp': querystmtbreakdown(table, secretkey, \
                detailid, request.POST['datatype']),
            'datatemptotal': querytotalbreakdown(table, secretkey, \
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
            datastring = "customerbreakstatus ='" + stat + "'"
        if datatype == 'S':
            datastring = "supplierbreakstatus ='" + stat + "'"
        if datatype == 'E':
            datastring = "employeebreakstatus ='" + stat + "'"
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