from django.views.generic import View, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from checkvoucher.models import Cvmain, Cvdetail, Cvdetailtemp, Cvdetailbreakdown, Cvdetailbreakdowntemp
from accountspayable.models import Apmain, Apdetail
from companyparameter.models import Companyparameter
from chartofaccount.models import Chartofaccount
from django.db.models import Q, Sum
from vat.models import Vat
from ataxcode.models import Ataxcode
from inputvat.models import Inputvat
from outputvat.models import Outputvat
from supplier.models import Supplier
from product.models import Product
from branch.models import Branch
from bankaccount.models import Bankaccount
from department.models import Department
from ataxcode.models import Ataxcode
from vat.models import Vat
from wtax.models import Wtax
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
import pandas as pd
from datetime import timedelta
import io
import xlsxwriter
import json
import datetime
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import connection
from collections import namedtuple

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Cvmain
    template_name = 'cvinquiry/index.html'
    context_object_name = 'data_list'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['chart'] = Chartofaccount.objects.filter(isdeleted=0,accounttype='P').order_by('accountcode')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('code')
        context['outputvat'] = Outputvat.objects.filter(isdeleted=0).order_by('code')
        context['product'] = Product.objects.filter(isdeleted=0).order_by('description')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        context['atax'] = Ataxcode.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('code')
        context['wtax'] = Wtax.objects.filter(isdeleted=0).order_by('code')

        return context

@method_decorator(login_required, name='dispatch')
class StatusView(ListView):
    model = Cvmain
    template_name = 'cvinquiry/status_index.html'
    context_object_name = 'data_list'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')

        return context

def stalecheck(request):
    if request.method == 'POST':
        from django.db.models import CharField
        from django.db.models.functions import Length

        CharField.register_lookup(Length, 'length')

        ids = request.POST['ids']

        idlist = json.loads(ids)
        amount = 0
        counter = 0
        for id in idlist:
            cvmain = Cvmain.objects.filter(pk=id,staled=0,claimed=0).first()
            if cvmain:
                print cvmain.payee_id

                # Create AP
                # try:
                #     apnumlast = Apmain.objects.filter(apnum__length=10).latest('apnum')
                #     latestapnum = str(apnumlast)
                #     #print latestapnum
                #     if latestapnum[0:4] == str(datetime.datetime.now().year):
                #         apnum = str(datetime.datetime.now().year)
                #         last = str(int(latestapnum[4:]) + 1)
                #         zero_addon = 6 - len(last)
                #         for x in range(0, zero_addon):
                #             apnum += '0'
                #         apnum += last
                #     else:
                #         apnum = str(datetime.datetime.now().year) + '000001'
                # except Apmain.DoesNotExist:
                #     apnum = str(datetime.datetime.now().year) + '000001'

                apnumlast = lastNumber('true')

                ## SELECT RIGHT(MAX(LPAD(apnum, 10, 0)) , 6)  FROM apmain;
                latestapnum = str(apnumlast[0])
                apnum = str(datetime.datetime.now().year)
                # print str(int(latestapnum[4:]))
                last = str(int(latestapnum) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    apnum += '0'
                apnum += last


                #print 'AP' + str(apnum)

                #print datetime.datetime.now()

                # billingremarks = '';
                #
                # employee = Employee.objects.get(pk=of.requestor_id)
                vat = Vat.objects.filter(pk=cvmain.vat_id).first()
                atax = Ataxcode.objects.filter(pk=cvmain.atc_id).first()
                supplier = Supplier.objects.get(pk=cvmain.payee_id)


                main = Apmain.objects.create(
                    apnum = apnum,
                    apdate = datetime.datetime.now(),
                    aptype_id = 13, # SB
                    apsubtype_id = 15, # Stale Check
                    branch_id = 5, # Head Office
                    inputvattype_id = cvmain.inputvattype_id, # Service
                    creditterm_id = 2, # 90 Days 2
                    payee_id = cvmain.payee_id,
                    payeecode = cvmain.payee_code,
                    payeename = cvmain.payee_name,
                    vat_id = cvmain.vat_id,
                    vatcode = vat.code,
                    vatrate = cvmain.vatrate,
                    atax_id = cvmain.atc_id, # NO ATC 66
                    ataxcode = atax.code, # NO ATC 66
                    ataxrate = cvmain.atcrate,
                    duedate = datetime.datetime.now(),
                    refno = 'CV#'+str(cvmain.cvnum),
                    particulars = cvmain.particulars,
                    remarks = 'Stale Check CV#'+str(cvmain.cvnum),
                    bankaccount_id=cvmain.bankaccount_id,
                    currency_id = 1,
                    fxrate = 1,
                    designatedapprover_id = 225, # Arlene Astapan
                    actualapprover_id = 225, # Arlene Astapan
                    approverremarks = '',
                    apstatus = 'F',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )


                print 'dito 1'
                amount = float(cvmain.amount)
                Apdetail.objects.create(
                    apmain_id = main.id,
                    ap_num = main.apnum,
                    ap_date = main.apdate,
                    item_counter = 1,
                    debitamount = amount,
                    creditamount = 0,
                    balancecode = 'D',
                    bankaccount_id = cvmain.bankaccount_id,
                    chartofaccount_id = 30, # Cash in bank
                    status='A',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )
                print 'dito 2'
                Apdetail.objects.create(
                    apmain_id = main.id,
                    ap_num = main.apnum,
                    ap_date = main.apdate,
                    item_counter = 2,
                    debitamount = 0,
                    creditamount = amount,
                    balancecode = 'C',
                    chartofaccount_id = 310, # ACCOUNTS PAYABLE - STALE CHECKS
                    status='A',
                    enterby_id = request.user.id,
                    enterdate = datetime.datetime.now(),
                    modifyby_id = request.user.id,
                    modifydate = datetime.datetime.now()
                )

                print 'dito 3'


                main.amount = amount
                main.save()

                counter += 1

                cvmain.staled = 1
                cvmain.staled_date = datetime.datetime.now()
                cvmainstaled_by_id = request.user.id
                cvmain.save()

                #CVMAIN update staled = 1, staled_date = now(), staled_by_id = user


        data = {
            'status': 'success',
            'counter': counter,
        }
        return JsonResponse(data)

def transgenerate(request):
    dto = request.GET["dto"]
    dfrom = request.GET["dfrom"]
    dto2 = request.GET["dto2"]
    dfrom2 = request.GET["dfrom2"]
    dto3 = request.GET["dto3"]
    dfrom3 = request.GET["dfrom3"]
    bankaccount = request.GET["bankaccount"]
    payeename = request.GET["payeename"]
    stat = request.GET["stat"]
    cvnum = request.GET["cvnum"]
    checkno = request.GET["checkno"]

    context = {}

    print "transaction listing"

    cashinbank = Companyparameter.objects.first().coa_cashinbank_id
    q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0,chartofaccount=cashinbank).filter(~Q(status='C')).order_by('cv_date', 'cv_num', 'item_counter')

    if dfrom != '':
        q = q.filter(cv_date__gte=dfrom)
    if dto != '':
        q = q.filter(cv_date__lte=dto)
    if dfrom2 != '':
        q = q.filter(cvmain__received_date__date__gte=dfrom2)
    if dto2 != '':
        q = q.filter(cvmain__received_date__date__lte=dto2)
    if dfrom3 != '':
        q = q.filter(cvmain__claimed_date__date__gte=dfrom3)
    if dto3 != '':
        q = q.filter(cvmain__claimed_date__date__lte=dto3)
    if bankaccount != '':
        q = q.filter(bankaccount_id=bankaccount)
    if payeename != '':
        q = q.filter(cvmain__payee_name__icontains=payeename)
    if cvnum != '':
        q = q.filter(cv_num=cvnum)
    if checkno != '':
        q = q.filter(cvmain__checknum=checkno)

    if stat == '1':
        q = q.filter(cvmain__received=1)
    elif stat == '2':
        q = q.filter(cvmain__received=0)
    elif stat == '3':
        q = q.filter(cvmain__claimed=1)
    elif stat == '4':
        q = q.filter(cvmain__claimed=0)

    context['result'] = q #query_transaction(dto, dfrom, chart, transtatus, status, payeecode, payeename)
    context['dto'] = dto
    context['dfrom'] = dfrom
    context['stat'] = stat
    viewhtml = render_to_string('cvinquiry/transaction_result.html', context)


    data = {
        'status': 'success',
        'viewhtml': viewhtml,
    }
    return JsonResponse(data)

@csrf_exempt
def tagreceived(request):
    if request.method == 'POST':
        id = request.POST['id']
        stat = request.POST['stat']

        if (stat == '1'):
            data = Cvmain.objects.filter(id=id).update(received=1,received_by=User.objects.get(pk=request.user.id),received_date= str(datetime.datetime.now()))
        else:
            print 'none'
            data = Cvmain.objects.filter(id=id).update(received=0, received_by=None,received_date=None)

        data = Cvmain.objects.filter(id=id).first()


        data = {'status': 'success', 'received_by': str(data.received_by), 'received_date': data.received_date}
    else:
        data = { 'status': 'error', 'data': null }

    return JsonResponse(data)

@csrf_exempt
def tagclaimed(request):
    if request.method == 'POST':
        id = request.POST['id']
        stat = request.POST['stat']

        if (stat == '1'):
            data = Cvmain.objects.filter(id=id).update(claimed=1,claimed_by=User.objects.get(pk=request.user.id),claimed_date= str(datetime.datetime.now()))
        else:
            print 'none'
            data = Cvmain.objects.filter(id=id).update(claimed=0, claimed_by=None,claimed_date=None)

        data = Cvmain.objects.filter(id=id).first()


        data = {'status': 'success', 'claimed_by': str(data.claimed_by), 'claimed_date': data.claimed_date}
    else:
        data = { 'status': 'error', 'data': null }

    return JsonResponse(data)\

@csrf_exempt
def savecashierremarks(request):
    if request.method == 'POST':
        id = request.POST['id']
        remarks = request.POST['remarks']
        ornum = request.POST['ornum']

        print remarks

        data = Cvmain.objects.filter(id=id).update(cashier_remarks=remarks, ornum=ornum)

        data = {'status': 'success'}
    else:
        data = { 'status': 'error'}

    return JsonResponse(data)

@method_decorator(login_required, name='dispatch')
class GenerateExcelStatus(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]
        dto2 = request.GET["dto2"]
        dfrom2 = request.GET["dfrom2"]
        dto3 = request.GET["dto3"]
        dfrom3 = request.GET["dfrom3"]
        bankaccount = request.GET["bankaccount"]
        payeename = request.GET["payeename"]
        stat = request.GET["stat"]
        cvnum = request.GET["cvnum"]
        checkno = request.GET["checkno"]

        context = {}
        title = "List of Check Status - All"

        print "transaction listing"

        cashinbank = Companyparameter.objects.first().coa_cashinbank_id
        q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0, chartofaccount=cashinbank).filter(~Q(status='C')).order_by('cv_date', 'cv_num', 'item_counter')

        if dfrom != '':
            q = q.filter(cv_date__gte=dfrom)
        if dto != '':
            q = q.filter(cv_date__lte=dto)
        if dfrom2 != '':
            q = q.filter(cvmain__received_date__date__gte=dfrom2)
        if dto2 != '':
            q = q.filter(cvmain__received_date__date__lte=dto2)
        if dfrom3 != '':
            q = q.filter(cvmain__claimed_date__date__gte=dfrom3)
        if dto3 != '':
            q = q.filter(cvmain__claimed_date__date__lte=dto3)
        if bankaccount != '':
            q = q.filter(bankaccount_id=bankaccount)
        if payeename != '':
            q = q.filter(cvmain__payee_name__icontains=payeename)
        if cvnum != '':
            q = q.filter(cv_num=cvnum)
        if checkno != '':
            q = q.filter(cvmain__checknum=checkno)

        if stat == '1':
            q = q.filter(cvmain__received=1)
            title = "List of Check Status - Recieved"
        elif stat == '2':
            q = q.filter(cvmain__received=0)
            title = "List of Check Status - Unrecieved"
        elif stat == '3':
            q = q.filter(cvmain__claimed=1)
            title = "List of Check Status - Claimed"
        elif stat == '4':
            q = q.filter(cvmain__claimed=0)
            title = "List of Check Status - Unclaimed"

        list = q

        if list:
            total = []
            total = list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', 'PHILIPPINE DAILY INQUIRER, INC.', bold)
        worksheet.write('A2', 'CHECK VOUCHER STATUS INQUIRY LIST', bold)
        worksheet.write('A3', str(title), bold)
        worksheet.write('A4', 'AS OF '+str(dfrom)+' to '+str(dto), bold)

        # header
        worksheet.write('A4', 'Bank', bold)
        worksheet.write('B4', 'Check Number', bold)
        worksheet.write('C4', 'Check Date', bold)
        worksheet.write('D4', 'CV Number', bold)
        worksheet.write('E4', 'CV Date', bold)
        worksheet.write('F4', 'Payee Code', bold)
        worksheet.write('G4', 'Payee', bold)
        worksheet.write('H4', 'Date Received', bold)
        worksheet.write('I4', 'Date Claimed', bold)
        worksheet.write('J4', 'Amount', bold)
        worksheet.write('J4', 'Cashier Remarks', bold)


        row = 5
        col = 0
        total = 0

        for data in list:
            if data.bankaccount:
                worksheet.write(row, col, data.bankaccount.code)
            worksheet.write(row, col + 1, data.cvmain.checknum)
            worksheet.write(row, col + 2, data.cvmain.checkdate, formatdate)
            worksheet.write(row, col + 3, data.cv_num)
            worksheet.write(row, col + 4, data.cv_date, formatdate)
            worksheet.write(row, col + 5, data.cvmain.payee_code)
            worksheet.write(row, col + 5, data.cvmain.payee_name)
            worksheet.write(row, col + 6, data.cvmain.received_date, formatdate)
            worksheet.write(row, col + 7, data.cvmain.claimed_date, formatdate)
            worksheet.write(row, col + 8, float(format(data.creditamount, '.2f')))
            worksheet.write(row, col + 9, data.cvmain.cashier_remarks)
            total += data.creditamount

            row += 1

        worksheet.write(row, col + 7, 'TOTAL', bold)
        worksheet.write(row, col + 8, float(format(total, '.2f')), bold)

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = "cvstatusinquiry.xlsx"
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response

@method_decorator(login_required, name='dispatch')
class Generate(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        chartofaccount = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        chart = request.GET['chart']
        supplier = request.GET['supplier']
        customer = request.GET['payee']
        employee = request.GET['employee']
        department = request.GET['department']
        product = request.GET['product']
        branch = request.GET['branch']
        bankaccount = request.GET['bankaccount']
        vat = request.GET['vat']
        atax = request.GET['atax']
        wtax = request.GET['wtax']
        inputvat = request.GET['inputvat']
        outputvat = request.GET['outputvat']
        chart = request.GET['chart']
        title = "Check Voucher Inquiry List"

        list = Cvdetail.objects.filter(isdeleted=0).order_by('cv_date', 'cv_num','item_counter')[:0]

        if report == '1':
            q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0,chartofaccount__exact=chart).filter(~Q(status = 'C')).order_by('cv_date', 'cv_num','item_counter')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)

        if chart != '':
            chartofaccount = Chartofaccount.objects.filter(isdeleted=0, id__exact=chart).first()

        if supplier != 'null':
            #q = q.filter(supplier__exact=supplier)
            q = q.filter(cvmain__payee_id=supplier)
            print 'hoy'
        if customer != 'null':
            q = q.filter(customer__exact=customer)
        if employee != 'null':
            q = q.filter(employee__exact=employee)
        if product != '':
            q = q.filter(product__exact=product)
        if department != '':
            q = q.filter(department__exact=department)
        if branch != '':
            q = q.filter(branch__exact=branch)
        if bankaccount != '':
            q = q.filter(bankaccount__exact=bankaccount)
        if vat != '':
            q = q.filter(vat__exact=vat)
        if atax != '':
            q = q.filter(ataxcode__exact=atax)
        if wtax != '':
            q = q.filter(wtax__exact=wtax)
        if inputvat != '':
            q = q.filter(inputvat__exact=inputvat)
        if outputvat != '':
            q = q.filter(outputvat__exact=outputvat)

        list = q

        if report == '1':
            total = {}
            total = list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))

        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "chartofaccount": chartofaccount,
            "username": request.user,
        }

        data = {
            'status': 'success',
            'viewhtml': render_to_string('cvinquiry/generate.html', context)
        }

        return JsonResponse(data)


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        chartofaccount = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        chart = request.GET['chart']
        supplier = request.GET['supplier']
        customer = request.GET['payee']
        employee = request.GET['employee']
        department = request.GET['department']
        product = request.GET['product']
        branch = request.GET['branch']
        bankaccount = request.GET['bankaccount']
        vat = request.GET['vat']
        atax = request.GET['atax']
        wtax = request.GET['wtax']
        inputvat = request.GET['inputvat']
        outputvat = request.GET['outputvat']
        chart = request.GET['chart']
        title = "Check Voucher Inquiry List"

        list = Cvdetail.objects.filter(isdeleted=0).order_by('cv_date', 'cv_num','item_counter')[:0]

        if report == '1':
            q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0,chartofaccount__exact=chart).filter(~Q(status = 'C')).order_by('cv_date', 'cv_num','item_counter')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)

        if chart != '':
            chartofaccount = Chartofaccount.objects.filter(isdeleted=0, id__exact=chart).first()

        if supplier != 'null':
            #q = q.filter(supplier__exact=supplier)
            q = q.filter(cvmain__payee_id=supplier)
            print 'hoy'
        if customer != 'null':
            q = q.filter(customer__exact=customer)
        if employee != 'null':
            q = q.filter(employee__exact=employee)
        if product != '':
            q = q.filter(product__exact=product)
        if department != '':
            q = q.filter(department__exact=department)
        if branch != '':
            q = q.filter(branch__exact=branch)
        if bankaccount != '':
            q = q.filter(bankaccount__exact=bankaccount)
        if vat != '':
            q = q.filter(vat__exact=vat)
        if atax != '':
            q = q.filter(ataxcode__exact=atax)
        if wtax != '':
            q = q.filter(wtax__exact=wtax)
        if inputvat != '':
            q = q.filter(inputvat__exact=inputvat)
        if outputvat != '':
            q = q.filter(outputvat__exact=outputvat)

        list = q

        if report == '1':
            total = {}
            total = list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))

        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "chartofaccount": chartofaccount,
            "username": request.user,
        }

        return Render.render('cvinquiry/report_1.html', context)


@method_decorator(login_required, name='dispatch')
class GeneratePDF2(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]
        dto2 = request.GET["dto2"]
        dfrom2 = request.GET["dfrom2"]
        dto3 = request.GET["dto3"]
        dfrom3 = request.GET["dfrom3"]
        bankaccount = request.GET["bankaccount"]
        payeename = request.GET["payeename"]
        stat = request.GET["stat"]
        cvnum = request.GET["cvnum"]
        checkno = request.GET["checkno"]

        context = {}
        title = "List of Check Status - All"

        print "transaction listing"

        cashinbank = Companyparameter.objects.first().coa_cashinbank_id
        q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0, chartofaccount=cashinbank).filter(~Q(status='C')).order_by('cv_date', 'cv_num', 'item_counter')

        if dfrom != '':
            q = q.filter(cv_date__gte=dfrom)
        if dto != '':
            q = q.filter(cv_date__lte=dto)
        if dfrom2 != '':
            q = q.filter(cvmain__received_date__date__gte=dfrom2)
        if dto2 != '':
            q = q.filter(cvmain__received_date__date__lte=dto2)
        if dfrom3 != '':
            q = q.filter(cvmain__claimed_date__date__gte=dfrom3)
        if dto3 != '':
            q = q.filter(cvmain__claimed_date__date__lte=dto3)
        if bankaccount != '':
            q = q.filter(bankaccount_id=bankaccount)
        if payeename != '':
            q = q.filter(cvmain__payee_name__icontains=payeename)
        if cvnum != '':
            q = q.filter(cv_num=cvnum)
        if checkno != '':
            q = q.filter(cvmain__checknum=checkno)

        if stat == '1':
            q = q.filter(cvmain__received=1)
            title = "List of Check Status - Recieved"
        elif stat == '2':
            q = q.filter(cvmain__received=0)
            title = "List of Check Status - Unrecieved"
        elif stat == '3':
            q = q.filter(cvmain__claimed=1)
            title = "List of Check Status - Claimed"
        elif stat == '4':
            q = q.filter(cvmain__claimed=0)
            title = "List of Check Status - Unclaimed"

        list = q

        if list:
            total = []
            total = list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))

        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "total": total,
            "username": request.user,
        }

        return Render.render('cvinquiry/transaction_pdf.html', context)


@method_decorator(login_required, name='dispatch')
class GenerateExcel(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        total = []
        chartofaccount = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        chart = request.GET['chart']
        supplier = request.GET['supplier']
        customer = request.GET['payee']
        employee = request.GET['employee']
        department = request.GET['department']
        product = request.GET['product']
        branch = request.GET['branch']
        bankaccount = request.GET['bankaccount']
        vat = request.GET['vat']
        atax = request.GET['atax']
        wtax = request.GET['wtax']
        inputvat = request.GET['inputvat']
        outputvat = request.GET['outputvat']
        chart = request.GET['chart']
        title = "Check Voucher Inquiry List"

        list = Cvdetail.objects.filter(isdeleted=0).order_by('cv_date', 'cv_num', 'item_counter')[:0]

        if report == '1':
            q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0, chartofaccount__exact=chart).filter(
                ~Q(status='C')).order_by('cv_date', 'cv_num', 'item_counter')
            if dfrom != '':
                q = q.filter(cv_date__gte=dfrom)
            if dto != '':
                q = q.filter(cv_date__lte=dto)

        if chart != '':
            chartofaccount = Chartofaccount.objects.filter(isdeleted=0, id__exact=chart).first()

        if supplier != 'null':
            #q = q.filter(supplier__exact=supplier)
            q = q.filter(cvmain__payee_id=supplier)
            print 'hoy'
        if customer != 'null':
            q = q.filter(customer__exact=customer)
        if employee != 'null':
            q = q.filter(employee__exact=employee)
        if product != '':
            q = q.filter(product__exact=product)
        if department != '':
            q = q.filter(department__exact=department)
        if branch != '':
            q = q.filter(branch__exact=branch)
        if bankaccount != '':
            q = q.filter(bankaccount__exact=bankaccount)
        if vat != '':
            q = q.filter(vat__exact=vat)
        if atax != '':
            q = q.filter(ataxcode__exact=atax)
        if wtax != '':
            q = q.filter(wtax__exact=wtax)
        if inputvat != '':
            q = q.filter(inputvat__exact=inputvat)
        if outputvat != '':
            q = q.filter(outputvat__exact=outputvat)

        list = q

        if list:
            total = []
            total = list.aggregate(total_debit=Sum('debitamount'), total_credit=Sum('creditamount'))

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        # title
        worksheet.write('A1', 'CHECK VOUCHER INQUIRY LIST', bold)
        worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)
        worksheet.write('A3', 'Chart of Account', bold)
        worksheet.write('B3', chartofaccount.accountcode, bold)
        worksheet.write('C3', chartofaccount.description, bold)

        # header
        worksheet.write('A4', 'CV Number', bold)
        worksheet.write('B4', 'CV Date', bold)
        worksheet.write('C4', 'Particulars', bold)
        worksheet.write('D4', 'Debit Amount', bold)
        worksheet.write('E4', 'Credit Amount', bold)
        worksheet.write('F4', 'Payee Code', bold)
        worksheet.write('G4', 'Payee Name', bold)
        worksheet.write('H4', 'CV Type', bold)
        worksheet.write('I4', 'CV Subtype', bold)
        worksheet.write('J4', 'Reference', bold)
        worksheet.write('K4', 'Branch', bold)
        worksheet.write('L4', 'Check Number', bold)
        worksheet.write('M4', 'Check Date', bold)
        worksheet.write('N4', 'Amount', bold)
        worksheet.write('O4', 'VAT', bold)
        worksheet.write('P4', 'VAT Rate', bold)
        worksheet.write('Q4', 'Input VAT', bold)
        worksheet.write('R4', 'Deferred VAT', bold)
        worksheet.write('S4', 'ATAX', bold)
        worksheet.write('T4', 'ATAX Rate', bold)
        worksheet.write('U4', 'Status', bold)
        worksheet.write('V4', 'Currency', bold)
        worksheet.merge_range('W4:AG4', 'Subsidiary Ledger', centertext)

        worksheet.write('W5', 'Supplier', bold)
        worksheet.write('X5', 'Customer', bold)
        worksheet.write('Y5', 'Employee', bold)
        worksheet.write('Z5', 'Department', bold)
        worksheet.write('AA5', 'Product', bold)
        worksheet.write('AB5', 'Branch', bold)
        worksheet.write('AC5', 'Bank Account', bold)
        worksheet.write('AD5', 'VAT', bold)
        worksheet.write('AE5', 'WTAX', bold)
        worksheet.write('AF5', 'ATAX', bold)
        worksheet.write('AG5', 'Input VAT', bold)
        worksheet.write('AH5', 'Output VAT', bold)

        row = 5
        col = 0

        for data in list:
            worksheet.write(row, col, data.cv_num)
            worksheet.write(row, col + 1, data.cv_date, formatdate)
            worksheet.write(row, col + 2, data.cvmain.particulars)
            worksheet.write(row, col + 3, float(format(data.debitamount, '.2f')))
            worksheet.write(row, col + 4, float(format(data.creditamount, '.2f')))
            worksheet.write(row, col + 5, data.cvmain.payee_code)
            worksheet.write(row, col + 6, data.cvmain.payee_name)
            worksheet.write(row, col + 7, data.cvmain.cvtype.description)
            worksheet.write(row, col + 8, data.cvmain.cvsubtype.description)
            worksheet.write(row, col + 9, data.cvmain.refnum)
            if data.cvmain.branch:
                worksheet.write(row, col + 10, data.cvmain.branch.code)
            worksheet.write(row, col + 11, data.cvmain.checknum)
            checkdate = str((data.cvmain.checkdate))
            worksheet.write(row, col + 12, checkdate, formatdate)
            worksheet.write(row, col + 13, float(format(data.cvmain.amount, '.2f')))
            worksheet.write(row, col + 14, data.cvmain.vat.code)
            worksheet.write(row, col + 15, data.cvmain.vatrate)
            if data.cvmain.inputvattype:
                worksheet.write(row, col + 16, data.cvmain.inputvattype.description)
            worksheet.write(row, col + 17, data.cvmain.deferredvat)
            worksheet.write(row, col + 18, data.cvmain.atc.code)
            worksheet.write(row, col + 19, data.cvmain.atcrate)
            worksheet.write(row, col + 20, data.cvmain.status)
            if data.cvmain.currency:
                worksheet.write(row, col + 21, data.cvmain.currency.symbol)

            if data.supplier:
                worksheet.write(row, col + 22, data.supplier.name)
            if data.customer:
                worksheet.write(row, col + 23, data.customer.name)
            if data.employee:
                worksheet.write(row, col + 24, data.employee.firstname + ' ' + data.employee.lastname)
            if data.department:
                worksheet.write(row, col + 25, data.department.departmentname)
            if data.product:
                worksheet.write(row, col + 26, data.product.description)
            if data.branch:
                worksheet.write(row, col + 27, data.branch.description)
            if data.bankaccount:
                worksheet.write(row, col + 28, data.bankaccount.code)
            if data.vat:
                worksheet.write(row, col + 29, data.vat.description)
            if data.wtax:
                worksheet.write(row, col + 30, data.wtax.description)
            if data.ataxcode:
                worksheet.write(row, col + 31, data.ataxcode.description)
            if data.inputvat:
                worksheet.write(row, col + 32, data.inputvat.description)
            if data.outputvat:
                worksheet.write(row, col + 33, data.outputvat.description)

            row += 1


        worksheet.write(row, col + 2, 'TOTAL', bold)
        worksheet.write(row, col + 3, float(format(total['total_debit'], '.2f')), bold)
        worksheet.write(row, col + 4, float(format(total['total_credit'], '.2f')), bold)

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = "cvinquiry.xlsx"
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response

def lastNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  SUBSTRING(apnum, 5) AS num FROM apmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
