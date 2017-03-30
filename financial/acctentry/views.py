from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
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
import datetime, random
from collections import namedtuple, defaultdict, OrderedDict
from django.db import connection

import json

# Create your views here.
@csrf_exempt
def maccountingentry(request):
    if request.method == 'POST':

        #context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0).order_by('accountcode')
        context = {
            'chartofaccount':  Chartofaccount.objects.filter(isdeleted=0, status='A', accounttype='P').order_by('accountcode'),
            'bankaccount':  Bankaccount.objects.filter(isdeleted=0).order_by('code'),
            'department':  Department.objects.filter(isdeleted=0).order_by('departmentname'),
            'employee':  Employee.objects.filter(isdeleted=0).order_by('firstname', 'lastname'),
            'supplier':  Supplier.objects.filter(isdeleted=0).order_by('name'),
            'customer':  Customer.objects.filter(isdeleted=0).order_by('name'),
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
            unit = Unit.objects.filter(mainunit=mainunit,isdeleted=0)

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
    #return HttpResponse(data, content_type='application/json')
    #return HttpResponse(data, content_type="application/json")

@csrf_exempt
def savemaccountingentry(request):

    if request.method == 'POST':
        # Save Data To JVDetail
        detailtemp = Jvdetailtemp()
        detailtemp.item_counter = len(Jvdetailtemp.objects.all().filter(secretkey=request.POST['secretkey'])) + 1
        detailtemp.chartofaccount = request.POST['chartofaccount']

        if request.POST['bankaccount']:
            detailtemp.bankaccount = request.POST['bankaccount']
        if request.POST['department']:
            detailtemp.department = request.POST['department']
        if request.POST['employee']:
            detailtemp.employee = request.POST['employee']
        if request.POST['supplier']:
            detailtemp.supplier = request.POST['supplier']
        if request.POST['customer']:
            detailtemp.customer = request.POST['customer']
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

        detailtemp.balancecode = 'D'
        if request.POST['creditamount']:
            detailtemp.balancecode = 'C'

        if request.POST['creditamount']:
            detailtemp.creditamount = request.POST['creditamount'].replace(',','')
        if request.POST['debitamount']:
            detailtemp.debitamount = request.POST['debitamount'].replace(',','')

        detailtemp.secretkey = request.POST['secretkey']
        detailtemp.jv_date = datetime.datetime.now()
        detailtemp.enterby = request.user
        detailtemp.enterdate = datetime.datetime.now()
        detailtemp.modifyby = request.user
        detailtemp.modifydate = datetime.datetime.now()
        detailtemp.save()

        querystmt = "SELECT temp.id, temp.chartofaccount, temp.item_counter, temp.jvmain, temp.jv_num, DATE(temp.jv_date) AS jvdate, " \
                "c.accountcode, c.description AS chartofaccountdesc, " \
                "b.code AS bankaccountcode, b.accountnumber, " \
                "d.code AS departmentcode, d.departmentname, " \
                "e.code AS employeecode, CONCAT(e.firstname,' ',e.lastname) AS employeename, e.multiplestatus AS employeestatus, " \
                "s.code AS suppliercode, s.name AS suppliername, s.multiplestatus AS supplierstatus, " \
                "cu.code AS customercode, cu.name AS customername, cu.multiplestatus AS customerstatus, " \
                "u.code AS unitcode, u.description AS unitname, " \
                "br.code AS branchcode, br.description AS branchname, " \
                "p.code AS productcode, p.description AS productname, " \
                "i.code AS inputvatcode, i.description AS inputvatname, " \
                "o.code AS outputvatcode, o.description AS outputvatname, " \
                "v.code AS vatcode, v.description AS vatname, " \
                "w.code AS wtaxcode, w.description AS wtaxname, " \
                "a.code AS ataxcode, a.description AS ataxname, " \
                "FORMAT(temp.creditamount, 2) AS creditamount, FORMAT(temp.debitamount, 2) AS debitamount " \
                "FROM jvdetailtemp AS temp " \
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
                "WHERE temp.secretkey = '"+request.POST['secretkey']+ "' AND temp.isdeleted != 1"

        querytotal = "SELECT FORMAT(SUM(IFNULL(temp.creditamount,0)), 2) AS totalcreditamount, " \
                     "FORMAT(SUM(IFNULL(temp.debitamount,0)), 2) AS totaldebitamount " \
                     "FROM jvdetailtemp AS temp " \
                     "WHERE temp.secretkey = '"+request.POST['secretkey']+ "' AND temp.isdeleted != 1"

        context = {
            #'datatemp': serializers.serialize("json", test),#Jvdetailtemp.objects.all().exclude(isdeleted=2).filter(secretkey=request.POST['secretkey']),
            #Jvdetailtemp.objects.all().exclude(isdeleted=2).filter(secretkey=request.POST['secretkey']),
            'datatemp': executestmt(querystmt),
            #'datatemptotal': serializers.serialize("python", executestmt(querytotal)),
            'datatemptotal': executestmt(querytotal),
        }
        print(context)
        data = {
            'datatable': render_to_string('acctentry/datatable.html', context),
            'status': 'success',
        }
    else :
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def breakdownentry(request):

    if request.method == 'POST':

        detailid = request.POST['detailid']
        chartid = request.POST['chartid']
        chartdata = Chartofaccount.objects.filter(isdeleted=0, status='A', accounttype='P', pk=chartid)
        bankdata = []
        if chartdata[0].bankaccount_enable == 'Y':
            bankdata = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        departmentdata = []
        if chartdata[0].department_enable == 'Y':
            departmentdata = Department.objects.filter(isdeleted=0).order_by('departmentname')
        employeedata = []
        if chartdata[0].employee_enable == 'Y':
            employeedata = Employee.objects.filter(isdeleted=0, multiplestatus='N').order_by('firstname', 'lastname')
        supplierdata = []
        if chartdata[0].supplier_enable == 'Y':
            supplierdata = Supplier.objects.filter(isdeleted=0, multiplestatus='N').order_by('name')
        customerdata = []
        if chartdata[0].customer_enable == 'Y':
            customerdata = Customer.objects.filter(isdeleted=0, multiplestatus='N').order_by('name')
        branchdata = []
        if chartdata[0].branch_enable == 'Y':
            branchdata = Branch.objects.filter(isdeleted=0).order_by('description')
        productdata = []
        if chartdata[0].product_enable == 'Y':
            productdata = Product.objects.filter(isdeleted=0).order_by('description')
        inputvatdata = []
        if chartdata[0].inputvat_enable == 'Y':
            inputvatdata = Inputvat.objects.filter(isdeleted=0).order_by('description')
        outputvatdata = []
        if chartdata[0].outputvat_enable == 'Y':
            outputvatdata = Outputvat.objects.filter(isdeleted=0).order_by('description')
        vatdata = []
        if chartdata[0].vat_enable == 'Y':
            vatdata = Vat.objects.filter(isdeleted=0).order_by('description')
        wtaxdata = []
        if chartdata[0].wtax_enable == 'Y':
            wtaxdata = Wtax.objects.filter(isdeleted=0).order_by('description')
        ataxcodedata = []
        if chartdata[0].ataxcode_enable == 'Y':
            ataxcodedata = Ataxcode.objects.filter(isdeleted=0).order_by('description'),

        context = {
            'detailid': detailid,
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
        }

        #print(context)
        data = {
            'breakdowndata': render_to_string('acctentry/breakdownentry.html', context),
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
        detailtempbreakdown = Jvdetailbreakdowntemp()
        detailtempbreakdown.item_counter = len(Jvdetailtemp.objects.all().filter(secretkey=request.POST['secretkey'])) + 1
        detailtempbreakdown.chartofaccount = request.POST['chartofaccount']
        detailtempbreakdown.jvdetailtemp = request.POST['detailid']
        detailtempbreakdown.particular = request.POST['particular']

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

        detailtempbreakdown.balancecode = 'D'
        if request.POST['creditamount']:
            detailtempbreakdown.balancecode = 'C'

        if request.POST['creditamount']:
            detailtempbreakdown.creditamount = request.POST['creditamount'].replace(',', '')
        if request.POST['debitamount']:
            detailtempbreakdown.debitamount = request.POST['debitamount'].replace(',', '')

        detailtempbreakdown.secretkey = request.POST['secretkey']
        detailtempbreakdown.jv_date = datetime.datetime.now()
        detailtempbreakdown.enterby = request.user
        detailtempbreakdown.enterdate = datetime.datetime.now()
        detailtempbreakdown.modifyby = request.user
        detailtempbreakdown.modifydate = datetime.datetime.now()
        detailtempbreakdown.save()

        data = {
            'status': 'success'
        }
    else:
        data = {
            'status': 'error'
        }

    return JsonResponse(data)

def generatekey(request):
    SECREY_KEY = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
    return SECREY_KEY


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

def executestmt(query):
    cursor = connection.cursor()

    cursor.execute(query)

    return namedtuplefetchall(cursor)