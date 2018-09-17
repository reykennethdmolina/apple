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
from django.http import HttpResponse
import pandas as pd
from datetime import timedelta
from django.http import StreamingHttpResponse
import io
import xlsxwriter
import datetime

# from collections import namedtuple
# import datetime
# import pandas as pd
# from datetime import timedelta
# import io
# from xlsxwriter.workbook import Workbook

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

        list = q[:50]

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

        list = q[:50]

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
        worksheet.write('D4', 'Supplier', bold)
        worksheet.write('E4', 'Customer', bold)
        worksheet.write('F4', 'Employee', bold)
        worksheet.write('G4', 'Department', bold)
        worksheet.write('H4', 'Product', bold)
        worksheet.write('I4', 'Branch', bold)
        worksheet.write('J4', 'Bank Account', bold)
        worksheet.write('K4', 'VAT', bold)
        worksheet.write('L4', 'WTAX', bold)
        worksheet.write('M4', 'ATAX', bold)
        worksheet.write('N4', 'Input VAT', bold)
        worksheet.write('O4', 'Output VAT', bold)
        worksheet.write('P4', 'Debit Amount', bold)
        worksheet.write('Q4', 'Credit Amount', bold)

        row = 4
        col = 0

        for data in list:
            worksheet.write(row, col, data.jv_num)
            worksheet.write(row, col + 1, data.jv_date, formatdate)
            worksheet.write(row, col + 2, data.jvmain.particular)
            if data.supplier:
                worksheet.write(row, col + 3, data.supplier.name)
            if data.customer:
                worksheet.write(row, col + 4, data.customer.name)
            if data.employee:
                worksheet.write(row, col + 5, data.employee.firstname+' '+data.employee.lastname)
            if data.department:
                worksheet.write(row, col + 6, data.department.departmentname)
            if data.product:
                worksheet.write(row, col + 7, data.product.description)
            if data.branch:
                worksheet.write(row, col + 8, data.branch.description)
            if data.bankaccount:
                worksheet.write(row, col + 9, data.bankaccount.code)
            if data.vat:
                worksheet.write(row, col + 10, data.vat.description)
            if data.wtax:
                worksheet.write(row, col + 11, data.wtax.description)
            if data.ataxcode:
                worksheet.write(row, col + 12, data.ataxcode.description)
            if data.inputvat:
                worksheet.write(row, col + 13, data.inputvat.description)
            if data.outputvat:
                worksheet.write(row, col + 14, data.outputvat.description)
            worksheet.write(row, col + 15, float(format(data.debitamount, '.2f')))
            worksheet.write(row, col + 16, float(format(data.creditamount, '.2f')))
            row += 1


        worksheet.write(row, col + 14, 'TOTAL', bold)
        worksheet.write(row, col + 15, float(format(total['total_debit'], '.2f')), bold)
        worksheet.write(row, col + 16, float(format(total['total_credit'], '.2f')), bold)

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