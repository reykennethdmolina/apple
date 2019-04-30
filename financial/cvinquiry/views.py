from django.views.generic import View, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from checkvoucher.models import Cvmain, Cvdetail, Cvdetailtemp, Cvdetailbreakdown, Cvdetailbreakdowntemp
from companyparameter.models import Companyparameter
from chartofaccount.models import Chartofaccount
from django.db.models import Q, Sum
from inputvat.models import Inputvat
from outputvat.models import Outputvat
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
import datetime
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

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

def transgenerate(request):
    dto = request.GET["dto"]
    dfrom = request.GET["dfrom"]
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

        print remarks

        data = Cvmain.objects.filter(id=id).update(cashier_remarks=remarks)

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
        bankaccount = request.GET["bankaccount"]
        payeename = request.GET["payeename"]
        stat = request.GET["stat"]
        cvnum = request.GET["cvnum"]
        checkno = request.GET["checkno"]

        context = {}

        print "transaction listing"

        cashinbank = Companyparameter.objects.first().coa_cashinbank_id
        q = Cvdetail.objects.select_related('cvmain').filter(isdeleted=0, chartofaccount=cashinbank).filter(~Q(status='C')).order_by('cv_date', 'cv_num', 'item_counter')

        if dfrom != '':
            q = q.filter(cv_date__gte=dfrom)
        if dto != '':
            q = q.filter(cv_date__lte=dto)
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

        title = "Check Voucher Inquiry List"

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
        worksheet.write('A3', 'AS OF '+str(dfrom)+' to '+str(dto), bold)

        # header
        worksheet.write('A4', 'Bank', bold)
        worksheet.write('B4', 'Check Number', bold)
        worksheet.write('C4', 'Check Date', bold)
        worksheet.write('D4', 'CV Number', bold)
        worksheet.write('E4', 'CV Date', bold)
        worksheet.write('F4', 'Payee', bold)
        worksheet.write('G4', 'Date Claimed', bold)
        worksheet.write('H4', 'Amount', bold)


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
            worksheet.write(row, col + 5, data.cvmain.payee_name)
            worksheet.write(row, col + 6, data.cvmain.claimed_date, formatdate)
            worksheet.write(row, col + 7, float(format(data.creditamount, '.2f')))
            total += data.creditamount

            row += 1

        worksheet.write(row, col + 6, 'TOTAL', bold)
        worksheet.write(row, col + 7, float(format(total, '.2f')), bold)

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
            q = q.filter(supplier__exact=supplier)
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
            q = q.filter(supplier__exact=supplier)
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
            q = q.filter(supplier__exact=supplier)
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
        worksheet.write('F4', 'Payee', bold)
        worksheet.write('G4', 'CV Type', bold)
        worksheet.write('H4', 'CV Subtype', bold)
        worksheet.write('I4', 'Reference', bold)
        worksheet.write('J4', 'Branch', bold)
        worksheet.write('K4', 'Check Number', bold)
        worksheet.write('L4', 'Check Date', bold)
        worksheet.write('M4', 'Amount', bold)
        worksheet.write('N4', 'VAT', bold)
        worksheet.write('O4', 'VAT Rate', bold)
        worksheet.write('P4', 'Input VAT', bold)
        worksheet.write('Q4', 'Deferred VAT', bold)
        worksheet.write('R4', 'ATAX', bold)
        worksheet.write('S4', 'ATAX Rate', bold)
        worksheet.write('T4', 'Status', bold)
        worksheet.write('U4', 'Currency', bold)
        worksheet.merge_range('V4:AG4', 'Subsidiary Ledger', centertext)

        worksheet.write('V5', 'Supplier', bold)
        worksheet.write('W5', 'Customer', bold)
        worksheet.write('X5', 'Employee', bold)
        worksheet.write('Y5', 'Department', bold)
        worksheet.write('Z5', 'Product', bold)
        worksheet.write('AA5', 'Branch', bold)
        worksheet.write('AB5', 'Bank Account', bold)
        worksheet.write('AC5', 'VAT', bold)
        worksheet.write('AD5', 'WTAX', bold)
        worksheet.write('AE5', 'ATAX', bold)
        worksheet.write('AF5', 'Input VAT', bold)
        worksheet.write('AG5', 'Output VAT', bold)

        row = 5
        col = 0

        for data in list:
            worksheet.write(row, col, data.cv_num)
            worksheet.write(row, col + 1, data.cv_date, formatdate)
            worksheet.write(row, col + 2, data.cvmain.particulars)
            worksheet.write(row, col + 3, float(format(data.debitamount, '.2f')))
            worksheet.write(row, col + 4, float(format(data.creditamount, '.2f')))
            worksheet.write(row, col + 5, data.cvmain.payee_name)
            worksheet.write(row, col + 6, data.cvmain.cvtype.description)
            worksheet.write(row, col + 7, data.cvmain.cvsubtype.description)
            worksheet.write(row, col + 8, data.cvmain.refnum)
            if data.cvmain.branch:
                worksheet.write(row, col + 9, data.cvmain.branch.code)
            worksheet.write(row, col + 10, data.cvmain.checknum)
            checkdate = str((data.cvmain.checkdate))
            worksheet.write(row, col + 11, checkdate, formatdate)
            worksheet.write(row, col + 12, float(format(data.cvmain.amount, '.2f')))
            worksheet.write(row, col + 13, data.cvmain.vat.code)
            worksheet.write(row, col + 14, data.cvmain.vatrate)
            if data.cvmain.inputvattype:
                worksheet.write(row, col + 15, data.cvmain.inputvattype.description)
            worksheet.write(row, col + 16, data.cvmain.deferredvat)
            worksheet.write(row, col + 17, data.cvmain.atc.code)
            worksheet.write(row, col + 18, data.cvmain.atcrate)
            worksheet.write(row, col + 19, data.cvmain.status)
            if data.cvmain.currency:
                worksheet.write(row, col + 20, data.cvmain.currency.symbol)

            if data.supplier:
                worksheet.write(row, col + 21, data.supplier.name)
            if data.customer:
                worksheet.write(row, col + 22, data.customer.name)
            if data.employee:
                worksheet.write(row, col + 23, data.employee.firstname + ' ' + data.employee.lastname)
            if data.department:
                worksheet.write(row, col + 24, data.department.departmentname)
            if data.product:
                worksheet.write(row, col + 25, data.product.description)
            if data.branch:
                worksheet.write(row, col + 26, data.branch.description)
            if data.bankaccount:
                worksheet.write(row, col + 27, data.bankaccount.code)
            if data.vat:
                worksheet.write(row, col + 28, data.vat.description)
            if data.wtax:
                worksheet.write(row, col + 29, data.wtax.description)
            if data.ataxcode:
                worksheet.write(row, col + 30, data.ataxcode.description)
            if data.inputvat:
                worksheet.write(row, col + 31, data.inputvat.description)
            if data.outputvat:
                worksheet.write(row, col + 32, data.outputvat.description)

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