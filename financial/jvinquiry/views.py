from django.views.generic import View, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from journalvoucher.models import Jvmain, Jvdetail, Jvdetailtemp, Jvdetailbreakdown, Jvdetailbreakdowntemp
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
    model = Jvmain
    template_name = 'jvinquiry/index.html'
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
        status = request.GET['status']
        chart = request.GET['chart']
        title = "Journal Voucher Inquiry List"

        list = Jvdetail.objects.filter(isdeleted=0).order_by('jv_date', 'jv_num','item_counter')[:0]

        if report == '1':
            q = Jvdetail.objects.select_related('jvmain').filter(isdeleted=0,chartofaccount__exact=chart).filter(~Q(status = 'C')).order_by('jv_date', 'jv_num','item_counter')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)

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
        if status != '':
            #pasok
            print status
            q = q.filter(jvmain__status__exact=status)

        list = q

        print list

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
            'viewhtml': render_to_string('jvinquiry/generate.html', context)
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
        status = request.GET['status']
        chart = request.GET['chart']
        title = "Journal Voucher Inquiry List"

        list = Jvdetail.objects.filter(isdeleted=0).order_by('jv_date', 'jv_num','item_counter')[:0]

        if report == '1':
            q = Jvdetail.objects.select_related('jvmain').filter(isdeleted=0,chartofaccount__exact=chart).filter(~Q(status = 'C')).order_by('jv_date', 'jv_num','item_counter')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)

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
        if status != '':
            q = q.filter(status__exact=status)

        list = q

        print list

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

        return Render.render('jvinquiry/report_1.html', context)


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
        status = request.GET['status']
        chart = request.GET['chart']
        title = "Journal Voucher Inquiry List"

        list = Jvdetail.objects.filter(isdeleted=0).order_by('jv_date', 'jv_num', 'item_counter')[:0]

        if report == '1':
            q = Jvdetail.objects.select_related('jvmain').filter(isdeleted=0, chartofaccount__exact=chart).filter(
                ~Q(status='C')).order_by('jv_date', 'jv_num', 'item_counter')
            if dfrom != '':
                q = q.filter(jv_date__gte=dfrom)
            if dto != '':
                q = q.filter(jv_date__lte=dto)

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
        if status != '':
            q = q.filter(status__exact=status)

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
        worksheet.write('A1', 'JOURNAL VOUCHER INQUIRY LIST', bold)
        worksheet.write('A2', 'AS OF '+str(dfrom)+' to '+str(dto), bold)
        worksheet.write('A3', 'Chart of Account', bold)
        worksheet.write('B3', chartofaccount.accountcode, bold)
        worksheet.write('C3', chartofaccount.description, bold)

        # header
        worksheet.write('A4', 'JV Number', bold)
        worksheet.write('B4', 'JV Date', bold)
        worksheet.write('C4', 'Particulars', bold)
        worksheet.write('D4', 'Debit Amount', bold)
        worksheet.write('E4', 'Credit Amount', bold)
        worksheet.write('F4', 'JV Type', bold)
        worksheet.write('G4', 'JV Subtype', bold)
        worksheet.write('H4', 'Reference', bold)
        worksheet.write('I4', 'Branch', bold)
        worksheet.write('J4', 'Department', bold)
        worksheet.write('K4', 'Currency', bold)
        worksheet.write('L4', 'FX Rate', bold)
        worksheet.write('M4', 'Due Date', bold)
        worksheet.merge_range('N4:Y4', 'Subsidiary Ledger', centertext)

        worksheet.write('N5', 'Supplier', bold)
        worksheet.write('O5', 'Customer', bold)
        worksheet.write('P5', 'Employee', bold)
        worksheet.write('Q5', 'Department', bold)
        worksheet.write('R5', 'Product', bold)
        worksheet.write('S5', 'Branch', bold)
        worksheet.write('T5', 'Bank Account', bold)
        worksheet.write('U5', 'VAT', bold)
        worksheet.write('V5', 'WTAX', bold)
        worksheet.write('W5', 'ATAX', bold)
        worksheet.write('X5', 'Input VAT', bold)
        worksheet.write('Y5', 'Output VAT', bold)

        row = 5
        col = 0

        for data in list:
            worksheet.write(row, col, data.jv_num)
            worksheet.write(row, col + 1, data.jv_date, formatdate)
            worksheet.write(row, col + 2, data.jvmain.particular)
            worksheet.write(row, col + 3, float(format(data.debitamount, '.2f')))
            worksheet.write(row, col + 4, float(format(data.creditamount, '.2f')))
            worksheet.write(row, col + 5, data.jvmain.jvtype.description)
            worksheet.write(row, col + 6, data.jvmain.jvsubtype.description)
            worksheet.write(row, col + 7, data.jvmain.refnum)
            if data.jvmain.branch:
                worksheet.write(row, col + 8, data.jvmain.branch.code)
            if data.jvmain.department:
                worksheet.write(row, col + 9, data.jvmain.department.code)
            if data.jvmain.currency:
                worksheet.write(row, col + 10, data.jvmain.currency.symbol)
            worksheet.write(row, col + 11, data.jvmain.fxrate)

            if data.supplier:
                worksheet.write(row, col + 12, data.supplier.name)
            if data.customer:
                worksheet.write(row, col + 13, data.customer.name)
            if data.employee:
                worksheet.write(row, col + 14, data.employee.firstname + ' ' + data.employee.lastname)
            if data.department:
                worksheet.write(row, col + 15, data.department.departmentname)
            if data.product:
                worksheet.write(row, col + 16, data.product.description)
            if data.branch:
                worksheet.write(row, col + 17, data.branch.description)
            if data.bankaccount:
                worksheet.write(row, col + 18, data.bankaccount.code)
            if data.vat:
                worksheet.write(row, col + 19, data.vat.description)
            if data.wtax:
                worksheet.write(row, col + 20, data.wtax.description)
            if data.ataxcode:
                worksheet.write(row, col + 21, data.ataxcode.description)
            if data.inputvat:
                worksheet.write(row, col + 22, data.inputvat.description)
            if data.outputvat:
                worksheet.write(row, col + 23, data.outputvat.description)

            row += 1


        worksheet.write(row, col + 2, 'TOTAL', bold)
        worksheet.write(row, col + 3, float(format(total['total_debit'], '.2f')), bold)
        worksheet.write(row, col + 4, float(format(total['total_credit'], '.2f')), bold)

        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = "jvinquiry.xlsx"
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response