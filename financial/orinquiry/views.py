from django.views.generic import View, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from officialreceipt.models import Ormain, Ordetail, Ordetailtemp, Ordetailbreakdown, Ordetailbreakdowntemp
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

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Ormain
    template_name = 'orinquiry/index.html'
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
        title = "Official Receipt Inquiry List"

        list = Ordetail.objects.filter(isdeleted=0).order_by('or_date', 'or_num','item_counter')[:0]

        if report == '1':
            q = Ordetail.objects.select_related('ormain').filter(isdeleted=0,chartofaccount__exact=chart).filter(~Q(status = 'C')).order_by('or_date', 'or_num','item_counter')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)

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
            'viewhtml': render_to_string('orinquiry/generate.html', context)
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
        title = "Official Receipt Inquiry List"

        list = Ordetail.objects.filter(isdeleted=0).order_by('or_date', 'or_num','item_counter')[:0]

        if report == '1':
            q = Ordetail.objects.select_related('ormain').filter(isdeleted=0,chartofaccount__exact=chart).filter(~Q(status = 'C')).order_by('or_date', 'or_num','item_counter')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)

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

        return Render.render('orinquiry/report_1.html', context)


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
        title = "Official Receipt Inquiry List"

        list = Ordetail.objects.filter(isdeleted=0).order_by('or_date', 'or_num', 'item_counter')[:0]

        if report == '1':
            q = Ordetail.objects.select_related('ormain').filter(isdeleted=0, chartofaccount__exact=chart).filter(
                ~Q(status='C')).order_by('or_date', 'or_num', 'item_counter')
            if dfrom != '':
                q = q.filter(or_date__gte=dfrom)
            if dto != '':
                q = q.filter(or_date__lte=dto)

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
        worksheet.write('A1', 'OFFICIAL RECEIPT INQUIRY LIST', bold)
        worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)
        worksheet.write('A3', 'Chart of Account', bold)
        worksheet.write('B3', chartofaccount.accountcode, bold)
        worksheet.write('C3', chartofaccount.description, bold)

        # header
        worksheet.write('A4', 'OR Number', bold)
        worksheet.write('B4', 'OR Date', bold)
        worksheet.write('C4', 'Particulars', bold)
        worksheet.write('D4', 'Debit Amount', bold)
        worksheet.write('E4', 'Credit Amount', bold)
        worksheet.write('F4', 'Transaction Type', bold)
        worksheet.write('G4', 'OR Type', bold)
        worksheet.write('H4', 'AR Type', bold)
        worksheet.write('I4', 'PR Number', bold)
        worksheet.write('J4', 'PR Date', bold)
        worksheet.write('K4', 'Adtype', bold)
        worksheet.write('L4', 'Collector', bold)
        worksheet.write('M4', 'Branch', bold)
        worksheet.write('N4', 'Payee Code', bold)
        worksheet.write('O4', 'Payee Name', bold)
        worksheet.write('P4', 'Amount', bold)
        worksheet.write('Q4', 'VAT', bold)
        worksheet.write('R4', 'VAT Rate', bold)
        worksheet.write('S4', 'WTAX', bold)
        worksheet.write('T4', 'WTAX Rate', bold)
        worksheet.write('U4', 'Output VAT', bold)
        worksheet.write('V4', 'Deferred VAT', bold)
        worksheet.write('W4', 'Product', bold)
        worksheet.write('X4', 'Bank Account', bold)
        worksheet.write('Y4', 'Government', bold)
        worksheet.write('Z4', 'Remarks', bold)
        worksheet.merge_range('Z4:AL4', 'Subsidiary Ledger', centertext)

        worksheet.write('AA5', 'Supplier', bold)
        worksheet.write('AB5', 'Customer', bold)
        worksheet.write('AC5', 'Employee', bold)
        worksheet.write('AD5', 'Department', bold)
        worksheet.write('AE5', 'Product', bold)
        worksheet.write('AF5', 'Branch', bold)
        worksheet.write('AG5', 'Bank Account', bold)
        worksheet.write('AH5', 'VAT', bold)
        worksheet.write('AI5', 'WTAX', bold)
        worksheet.write('AJ5', 'ATAX', bold)
        worksheet.write('AK5', 'Input VAT', bold)
        worksheet.write('AL5', 'Output VAT', bold)

        row = 5
        col = 0

        for data in list:
            worksheet.write(row, col, data.or_num)
            worksheet.write(row, col + 1, data.or_date, formatdate)
            worksheet.write(row, col + 2, data.ormain.particulars)
            worksheet.write(row, col + 3, float(format(data.debitamount, '.2f')))
            worksheet.write(row, col + 5, float(format(data.creditamount, '.2f')))
            worksheet.write(row, col + 6, data.ormain.transaction_type)
            worksheet.write(row, col + 7, data.ormain.ortype.description)
            worksheet.write(row, col + 8, data.ormain.orsource)
            worksheet.write(row, col + 9, data.ormain.prnum)
            worksheet.write(row, col + 10, str(data.ormain.prdate))
            if data.ormain.adtype:
                worksheet.write(row, col + 11, data.ormain.adtype.code)
            if data.ormain.collector:
                worksheet.write(row, col + 12, data.ormain.collector.code)
            if data.ormain.branch:
                worksheet.write(row, col + 13, data.ormain.branch.code)
            worksheet.write(row, col + 14, data.ormain.payee_code)
            worksheet.write(row, col + 15, data.ormain.payee_name)
            worksheet.write(row, col + 16, data.ormain.amount)
            if data.ormain.vat:
                worksheet.write(row, col + 17, data.ormain.vat.code)
            worksheet.write(row, col + 18, data.ormain.vatrate)
            if data.ormain.wtax:
                worksheet.write(row, col + 19, data.ormain.wtax.code)
            worksheet.write(row, col + 20, data.ormain.wtaxrate)
            if data.ormain.outputvattype:
                worksheet.write(row, col + 21, data.ormain.outputvattype.code)
            worksheet.write(row, col + 22, data.ormain.deferredvat)
            if data.ormain.product:
                worksheet.write(row, col + 23, data.ormain.product.code)
            if data.ormain.bankaccount:
                worksheet.write(row, col + 24, data.ormain.bankaccount.code)
            worksheet.write(row, col + 25, data.ormain.government)
            worksheet.write(row, col + 26, data.ormain.remarks)


            if data.supplier:
                worksheet.write(row, col + 27, data.supplier.name)
            if data.customer:
                worksheet.write(row, col + 28, data.customer.name)
            if data.employee:
                worksheet.write(row, col + 29, data.employee.firstname + ' ' + data.employee.lastname)
            if data.department:
                worksheet.write(row, col + 30, data.department.departmentname)
            if data.product:
                worksheet.write(row, col + 31, data.product.description)
            if data.branch:
                worksheet.write(row, col + 32, data.branch.description)
            if data.bankaccount:
                worksheet.write(row, col + 33, data.bankaccount.code)
            if data.vat:
                worksheet.write(row, col + 34, data.vat.description)
            if data.wtax:
                worksheet.write(row, col + 35, data.wtax.description)
            if data.ataxcode:
                worksheet.write(row, col + 36, data.ataxcode.description)
            if data.inputvat:
                worksheet.write(row, col + 37, data.inputvat.description)
            if data.outputvat:
                worksheet.write(row, col + 38, data.outputvat.description)

            row += 1


        worksheet.write(row, col + 2, 'TOTAL', bold)
        worksheet.write(row, col + 3, float(format(total['total_debit'], '.2f')), bold)
        worksheet.write(row, col + 4, float(format(total['total_credit'], '.2f')), bold)

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = "orinquiry.xlsx"
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response