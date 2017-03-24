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
from journalvoucher.models import Jvdetailtemp
import datetime, random

import json

# Create your views here.
@csrf_exempt
def maccountingentry(request):
    if request.method == 'POST':

        #context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0).order_by('accountcode')
        context = {
            'chartofaccount':  Chartofaccount.objects.filter(isdeleted=0, status='A').order_by('accountcode'),
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
def checkchartvalidatetion(request):

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
        detailtemp.item_counter = 1
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

        data = {
            'status': 'success',
        }
    else :
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

def generatekey(request):
    SECREY_KEY = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
    return SECREY_KEY