import datetime
from django.views.generic import View, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from mrstype.models import Mrstype
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from companyparameter.models import Companyparameter
from accountspayable.models import Apmain, Apdetail
from checkvoucher.models import Cvmain
from journalvoucher.models import Jvmain
from officialreceipt.models import Ormain
from subledger.models import Subledger
from customer.models import Customer
from chartofaccount.models import Chartofaccount
from collections import namedtuple
from django.db import connection
from django.template.loader import render_to_string
import pandas as pd
import io
import xlsxwriter
import datetime
from datetime import timedelta


class IndexView(TemplateView):
    template_name = 'nontrade/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['chart'] = Chartofaccount.objects.filter(isdeleted=0, accounttype='P', nontrade='Y').order_by('accountcode')

        return context

@csrf_exempt
def tagging(request):

    # print request.GET["id"]
    # print request.GET["reftype"]
    # print request.GET["refnum"]
    # print request.GET["refdate"]

    msg = 'Successfully tag'
    status = 1
    tdate= ''

    if request.GET["reftype"] == '':
        msg = 'Reftype is empty'
        status = 0
    elif request.GET["refnum"] == '':
        msg = 'Refnum is empty'
        status = 0
    # elif request.GET["refdate"] == '':
    #     msg = 'Refdate is empty'
    #     status = 0
    else:
        sub = Subledger.objects.filter(isdeleted=0, id=request.GET["id"]).first()
        if request.GET["reftype"] == 'AP':
            print 'AP'
            main = Apmain.objects.filter(isdeleted=0, apnum=request.GET["refnum"]).first()
            if main:
                msg = 'Valid AP Transaction'
                tdate = main.apdate
                status = 1
            else:
                msg = 'Invalid AP Transaction'
                status = 0
        elif request.GET["reftype"] == 'CV':
            print 'CV'
            main = Cvmain.objects.filter(isdeleted=0, cvnum=request.GET["refnum"]).first()
            if main:
                msg = 'Valid CV Transaction'
                tdate = main.cvdate
                status = 1
            else:
                msg = 'Invalid CV Transaction'
                status = 0
        elif request.GET["reftype"] == 'JV':
            print 'JV'
            main = Jvmain.objects.filter(isdeleted=0, jvnum=request.GET["refnum"]).first()
            if main:
                msg = 'Valid JV Transaction'
                tdate = main.jvdate
                status = 1
            else:
                msg = 'Invalid JV Transaction'
                status = 0
        elif request.GET["reftype"] == 'OR':
            print 'OR'
            main = Ormain.objects.filter(isdeleted=0, ornum=request.GET["refnum"]).first()
            if main:
                msg = 'Valid OR Transaction'
                tdate = main.ordate
                status = 1
            else:
                msg = 'Invalid OR Transaction'
                status = 0


        if status == 1:
            print 'Valid Transaction'
            if sub.document_type != request.GET["reftype"]:
                msg = 'Invalid Transaction Tagging Subledger Type: '+ sub.document_type + ' vs Ref Type: '+ request.GET["reftype"]
                status = 0
            else:
                msg = 'Successfully tag'
                sub.document_reftype = request.GET["reftype"]
                sub.document_refnum = request.GET["refnum"]
                sub.document_refdate = tdate
                sub.save()
                status = 1

            print sub.document_type
            print status

    data = {
        'status': status,
        'msg': msg,
        'tdate': tdate
    }


    return JsonResponse(data)

#@csrf_exempt
def transgenerate(request):
    dto = request.GET["dto"]
    dfrom = request.GET["dfrom"]
    transaction = request.GET["transaction"]
    chartofaccount = request.GET["chartofaccount"]
    payeecode = request.GET["payeecode"]
    payeename = request.GET["payeename"]
    report = request.GET["report"]

    viewhtml = ''
    context = {}

    if report == '1':
        print "subsidiary ledger"

        data = queryLedger(dto, dfrom, transaction, chartofaccount, payeecode, payeename)

        tdebit = 0
        tcredit = 0
        for val in data:
            tdebit += val.debitamount
            tcredit += val.creditamount

        context['data'] = data
        context['tdebit'] = tdebit
        context['tcredit'] = tcredit
        viewhtml = render_to_string('nontrade/transaction_result_ledger.html', context)
    elif report == '2':
        print "schedule"

        data = queryScheduled(dto, dfrom, transaction, chartofaccount, payeecode, payeename)

        tbalx = 0
        tbal = 0
        tbalbeg = 0
        tbaltran = 0
        for val in data:
            tbal += val.balamount
            tbalx += val.balamountx
            tbalbeg += val.begamt
            tbaltran += val.extrabal

        context['data'] = data
        context['tbalx'] = tbalx
        context['tbal'] = tbal
        context['tbalbeg'] = tbalbeg
        context['tbaltran'] = tbaltran
        context['dfrom'] = dfrom
        viewhtml = render_to_string('nontrade/transaction_result_scheduled.html', context)

    elif report == '3':
        print "statement of account"

        data = querySOA(dto, dfrom, transaction, chartofaccount, payeecode, payeename)
        transdata = querySOATran(dfrom, '2019-01-01', transaction, chartofaccount, payeecode, payeename)

        chart = Chartofaccount.objects.filter(isdeleted=0, accounttype='P', nontrade='Y', id=chartofaccount).first()

        print chart.balancecode

        beg_code = 'D'
        beg = 0
        end = 0

        # Begging Balance
        if transaction == '1':
            cust = Customer.objects.filter(isdeleted=0, code=payeecode).first()
            if cust:
                begdata = begBalance(cust.id)

                if begdata:
                    for i in begdata:
                        #print(i.id)
                        beg = i.beg_amt
                        beg_code = i.beg_code
            # print type(begdata)
            # print str(begdata['beg_amt'])
            # print begdata.beg_code
            # print begdata.beg_date

        if beg_code != chart.balancecode:
            beg = beg * -1

        datalist = {}
        counter = 0
        amount = 0
        balance = beg
        transdebit = 0
        transcredit = 0
        dft = pd.DataFrame(transdata)
        for index, row in dft.iterrows():
            if row['balancecode'] == 'D':
                amount = (row['debitamount'])
                transdebit += (row['debitamount'])
            else:
                amount = (row['creditamount'])
                transcredit += (row['creditamount'])

            if row['balancecode'] != chart.balancecode:
                amount = amount * -1

            balance = balance + amount
            end = balance


        transbeg = transdebit - transcredit
        df = pd.DataFrame(data)
        for index, row in df.iterrows():

            if row['balancecode'] == 'D':
                amount = (row['debitamount'])
            else:
                amount = (row['creditamount'])

            if row['balancecode'] != chart.balancecode:
                amount = amount * -1

            balance = balance + amount
            datalist[counter] = dict(document_date=row['document_date'], document_type=row['document_type'], document_num=row['document_num'],
                                     particulars=row['particulars'],
                                     debitamount=float(format(row['debitamount'], '.2f')),
                                     creditamount=float(format(row['creditamount'], '.2f')),
                                     balance=float(format(balance, '.2f')))
            end = balance
            counter += 1
        #print datalist
        context['datalist'] = datalist
        context['beg'] = beg
        context['dfrom'] = dfrom
        context['transbeg'] = transbeg
        context['end'] = end
        viewhtml = render_to_string('nontrade/transaction_result_soa.html', context)

    data = {
        'status': 'success',
        'viewhtml': viewhtml,

    }
    return JsonResponse(data)

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]
        transaction = request.GET["transaction"]
        chartofaccount = request.GET["chartofaccount"]
        payeecode = request.GET["payeecode"]
        payeename = request.GET["payeename"]
        report = request.GET["report"]
        tbal = 0
        begbal = 0
        chart = Chartofaccount.objects.filter(isdeleted=0, accounttype='P', nontrade='Y', id=chartofaccount).first()

        if report == '2':
            title = 'SCHEDULE OF ACCOUNTS PAYABLE (NON-TRADE)'

            data = queryScheduled(dto, dfrom, transaction, chartofaccount, payeecode, payeename)

            for val in data:
                tbal += val.balamount

            context = {
                "title": title,
                "today": timezone.now(),
                "company": company,
                "listing": data,
                "tbal": tbal,
                "chartofaccount": chart,
                "begbal": begbal,
                "datefrom": datetime.datetime.strptime(dfrom, '%Y-%m-%d'),
                "dateto": datetime.datetime.strptime(dto, '%Y-%m-%d'),
                "username": request.user,
            }

            return Render.render('nontrade/pdf_scheduled.html', context)
        elif report == '3':
            print "statement of account"

            title = 'STATEMENT OF ACCOUNT'

            data = querySOA(dto, dfrom, transaction, chartofaccount, payeecode, payeename)
            transdata = querySOATran(dfrom, '2019-01-01', transaction, chartofaccount, payeecode, payeename)


            chart = Chartofaccount.objects.filter(isdeleted=0, accounttype='P', nontrade='Y', id=chartofaccount).first()

            print chart.balancecode

            beg_code = 'D'
            beg = 1000
            end = 0

            # Begging Balance
            if transaction == '1':
                cust = Customer.objects.filter(isdeleted=0, code=payeecode).first()
                if cust:
                    begdata = begBalance(cust.id)

                    if begdata:
                        for i in begdata:
                            # print(i.id)
                            beg = i.beg_amt
                            beg_code = i.beg_code



            if beg_code != chart.balancecode:
                beg = beg * -1

            datalist = {}
            counter = 0
            amount = 0
            balance = beg
            transdebit = 0
            transcredit = 0
            cusup = ""
            dft = pd.DataFrame(transdata)
            for index, row in dft.iterrows():
                if row['balancecode'] == 'D':
                    amount = (row['debitamount'])
                    transdebit += (row['debitamount'])
                else:
                    amount = (row['creditamount'])
                    transcredit += (row['creditamount'])

                if row['balancecode'] != chart.balancecode:
                    amount = amount * -1

                balance = balance + amount
                end = balance

            transbeg = transdebit - transcredit
            df = pd.DataFrame(data)

            for index, row in df.iterrows():

                if row['balancecode'] == 'D':
                    amount = (row['debitamount'])
                else:
                    amount = (row['creditamount'])

                if row['balancecode'] != chart.balancecode:
                    amount = amount * -1

                balance = balance + amount
                cusup = row['pcode']+' - '+row['pname']
                datalist[counter] = dict(document_date=row['document_date'], document_type=row['document_type'],
                                         document_num=row['document_num'],
                                         particulars=row['particulars'],
                                         debitamount=float(format(row['debitamount'], '.2f')),
                                         creditamount=float(format(row['creditamount'], '.2f')),
                                         balance=float(format(balance, '.2f')))
                end = balance
                counter += 1
            context = {
                "title": title,
                "today": timezone.now(),
                "company": company,
                "listing": datalist,
                "balance": balance,
                "chartofaccount": chart,
                "beg": beg,
                "end": end,
                "cusup": cusup,
                "transbeg": transbeg,
                "datefrom": datetime.datetime.strptime(dfrom, '%Y-%m-%d'),
                "dateto": datetime.datetime.strptime(dto, '%Y-%m-%d'),
                "username": request.user,
            }
            return Render.render('nontrade/pdf_soa.html', context)



@method_decorator(login_required, name='dispatch')
class TransExcel(View):
    def get(self, request):

        dto = request.GET["dto"]
        dfrom = request.GET["dfrom"]
        transaction = request.GET["transaction"]
        chartofaccount = request.GET["chartofaccount"]
        payeecode = request.GET["payeecode"]
        payeename = request.GET["payeename"]
        report = request.GET["report"]


        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # variables
        bold = workbook.add_format({'bold': 1})
        formatdate = workbook.add_format({'num_format': 'MM/DD/YYYY'})
        centertext = workbook.add_format({'bold': 1, 'align': 'center'})

        if report == '1':
            print "subsidiary ledger"
            filename = "subsidiary_ledger.xlsx"

            result = queryLedger(dto, dfrom, transaction, chartofaccount, payeecode, payeename)

            tdebit = 0
            tcredit = 0

            # title
            worksheet.write('A1', 'NON-TRADE SUBSIDIARY LEDGER', bold)
            worksheet.write('A2', 'AS OF ' + str(dfrom) + ' to ' + str(dto), bold)

            # header
            worksheet.write('A4', 'Date', bold)
            worksheet.write('B4', 'Type', bold)
            worksheet.write('C4', 'Number', bold)
            worksheet.write('D4', 'Customer / Supplier', bold)
            worksheet.write('E4', 'Remarks', bold)
            worksheet.write('F4', 'Debit Amount', bold)
            worksheet.write('G4', 'Credit Amount', bold)
            worksheet.write('H4', 'Ref Type', bold)
            worksheet.write('I4', 'Ref No', bold)
            worksheet.write('J4', 'Ref Date', bold)

            row = 5
            col = 0

            # print result

            for data in result:
                worksheet.write(row, col, data.document_date, formatdate)
                worksheet.write(row, col + 1, data.document_type)
                worksheet.write(row, col + 2, data.document_num)
                if data.pcode:
                    worksheet.write(row, col + 3, data.pcode+'-'+data.pname)
                else:
                    worksheet.write(row, col + 3, 'N/A - NO CUSTOMER/SUPPLIER')
                worksheet.write(row, col + 4, data.particulars)
                worksheet.write(row, col + 5, float(format(data.debitamount, '.2f')))
                worksheet.write(row, col + 6, float(format(data.creditamount, '.2f')))
                worksheet.write(row, col + 7, data.document_reftype)
                worksheet.write(row, col + 8, data.document_refnum)
                worksheet.write(row, col + 9, data.document_refdate, formatdate)

                tdebit += data.debitamount
                tcredit += data.creditamount

                row += 1

            worksheet.write(row, col + 4, 'Total')
            worksheet.write(row, col + 5, float(format(tdebit, '.2f')))
            worksheet.write(row, col + 6, float(format(tcredit, '.2f')))

        elif report == '2':
            filename = "schedule.xlsx"

            result = queryScheduled(dto, dfrom, transaction, chartofaccount, payeecode, payeename)

            # title
            worksheet.write('A1', 'NON-TRADE SCHEDULE', bold)
            worksheet.write('A2', 'AS OF ' + str(dfrom) + ' to ' + str(dto), bold)

            # header
            worksheet.write('A4', 'Particulars', bold)
            worksheet.write('B4', 'Amount', bold)

            row = 5
            col = 0
            tbal = 0

            for data in result:
                if data.pcode:
                    worksheet.write(row, col, data.pname+' - '+data.pcode)
                else:
                    worksheet.write(row, col, ' NO CUSTOMER/SUPPLIER - N/A')
                worksheet.write(row, col + 1, float(format(data.balamount, '.2f')))
                row += 1
                tbal += data.balamount

            worksheet.write(row, col, 'Total')
            worksheet.write(row, col + 1, float(format(tbal, '.2f')))


        workbook.close()

        # Rewind the buffer.

        output.seek(0)

        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response


def queryLedger(dto, dfrom, transaction, chartofaccount, payeecode, payeename):

    conchart = ""
    orderby = "ORDER BY document_date ASC, FIELD(a.document_type, 'AP','CV','JV','OR')"
    conpayeecode = ""
    conpayeename = ""

    if chartofaccount:
        conchart = "SELECT id FROM chartofaccount WHERE id = '"+str(chartofaccount)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"
    else:
        conchart  = "SELECT id FROM chartofaccount WHERE main = '"+str(transaction)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"

    if payeecode:
        conpayeecode = "AND IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) = '"+str(payeecode)+"'"

    if payeename:
        conpayeename = "AND IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) LIKE '%"+str(payeename)+"%'"

    print conchart
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, a.document_refnum, a.document_refdate, " \
            "a.balancecode, IF (a.balancecode = 'C', a.amount, 0) AS creditamount, IF (a.balancecode = 'D', a.amount, 0) AS debitamount, " \
            "a.document_customer_id, a.document_supplier_id,  " \
            "b.accountcode, b.description, b.customer_enable, b.supplier_enable, b.nontrade, b.setup_customer, b.setup_supplier, " \
            "IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) AS pcode,  " \
            "IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) AS pname, " \
            "IF (b.customer_enable = 'Y', dcust.tin, IF (b.supplier_enable = 'Y', dsup.tin, IF (b.setup_customer != '', scust.tin, ssup.tin))) AS ptin " \
            "FROM subledger AS a " \
            "LEFT OUTER JOIN chartofaccount AS b ON b.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN customer AS dcust ON dcust.id = a.document_customer_id " \
            "LEFT OUTER JOIN customer AS scust ON scust.id =  b.setup_customer " \
            "LEFT OUTER JOIN supplier AS dsup ON dsup.id = a.document_supplier_id " \
            "LEFT OUTER JOIN supplier AS ssup ON ssup.id = b.setup_supplier " \
            "WHERE a.chartofaccount_id IN ("+str(conchart)+") " \
            ""+str(conpayeecode)+" "+str(conpayeename)+" AND DATE(document_date) >= '"+str(dfrom)+"' AND DATE(document_date) <= '"+str(dto)+"' "+str(orderby)

    print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def queryScheduled(dto, dfrom, transaction, chartofaccount, payeecode, payeename):
    chart = Chartofaccount.objects.filter(isdeleted=0, accounttype='P', nontrade='Y', id=chartofaccount).first()

    conchart = ""
    orderby = "ORDER BY document_date ASC, FIELD(a.document_type, 'AP','CV','JV','OR')"
    #orderby = "ORDER BY IFNULL(z.pcode, ' N/A') ASC, ' NO CUSTOMER/SUPPLIER') ASC"
    conpayeecode = ""
    conpayeename = ""
    conbeg = ""
    contran = ""

    if transaction == '1':
        #conbeg = "LEFT OUTER JOIN beginningbalance AS beg ON (beg.code_id = z.pid AND beg.trans_code = 'NT' AND trans_type = 'AR' AND beg.accountcode = '"+str(chart.accountcode)+"' )"
        print 'hy'
        conbeg = "WHERE b.accountcode = '" + str(chart.accountcode) + "' AND b.trans_code = 'NT' AND b.trans_type = 'AR'"

    else:
        #conbeg = "LEFT OUTER JOIN beginningbalance AS beg ON (beg.code_id = z.pid AND beg.trans_code = 'NT' AND trans_type = 'AP' AND beg.accountcode = '"+str(chart.accountcode)+"' )"
        conbeg = "WHERE b.accountcode = '"+str(chart.accountcode)+"' AND b.trans_code = 'NT' AND b.trans_type = 'AP'"
        print 'hy'

    contran = "LEFT OUTER JOIN ( " \
              " SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, " \
              " a.document_refnum, a.document_refdate, a.balancecode, " \
              " SUM(IF (a.balancecode = 'C', a.amount, 0)) AS creditamount, " \
              " SUM(IF (a.balancecode = 'D', a.amount, 0)) AS debitamount, " \
              " (SUM(IF (a.balancecode = 'D', a.amount, 0)) - SUM(IF (a.balancecode = 'C', a.amount, 0))) AS bal,  " \
              " a.document_customer_id, a.document_supplier_id,  b.accountcode, b.description, b.customer_enable, b.supplier_enable, b.nontrade, b.setup_customer, b.setup_supplier, " \
              " IF (b.customer_enable = 'Y', dcust.id, IF (b.supplier_enable = 'Y', dsup.id, IF (b.setup_customer != '', scust.id, ssup.id))) AS pid, " \
              " IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, " \
              " IF (b.setup_customer != '', scust.code, ssup.code))) AS pcode,  " \
              " IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) AS pname, " \
              " IF (b.customer_enable = 'Y', dcust.tin, IF (b.supplier_enable = 'Y', dsup.tin, IF (b.setup_customer != '', scust.tin, ssup.tin))) AS ptin " \
              " FROM subledger AS a " \
              " LEFT OUTER JOIN chartofaccount AS b ON b.id = a.chartofaccount_id " \
              " LEFT OUTER JOIN customer AS dcust ON dcust.id = a.document_customer_id " \
              " LEFT OUTER JOIN customer AS scust ON scust.id = b.setup_customer " \
              " LEFT OUTER JOIN supplier AS dsup ON dsup.id = a.document_supplier_id " \
              " LEFT OUTER JOIN supplier AS ssup ON ssup.id = b.setup_supplier " \
              " WHERE a.chartofaccount_id IN ( " \
              "     SELECT id FROM chartofaccount WHERE id = '" + str(chartofaccount) + "' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode) " \
                          "     AND DATE(a.document_date) > '2019-01-01' AND DATE(a.document_date) < '" + str(dfrom) + "' " \
                 "     GROUP BY IF (b.customer_enable = 'Y', dcust.id, IF (b.supplier_enable = 'Y', dsup.id, IF (b.setup_customer != '', scust.id, ssup.id))) " \
                 ") AS extrans ON extrans.pid = z.pid"

    if chartofaccount:
        conchart = "SELECT id FROM chartofaccount WHERE id = '"+str(chartofaccount)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"
    else:
        conchart  = "SELECT id FROM chartofaccount WHERE main = '"+str(transaction)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"

    if payeecode:
        conpayeecode = "AND IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) = '"+str(payeecode)+"'"

    if payeename:
        conpayeename = "AND IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) LIKE '%"+str(payeename)+"%'"

    print conchart
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT zz.pcode, zz.pname, pid, SUM(zz.creditamount) AS creditamount, SUM(zz.debitamount) AS debitamount, IFNULL(zz.beg_code, 'D') AS beg_code, " \
            "SUM(IFNULL(zz.begamt, 0)) AS begamt, SUM(zz.balamountx) AS balamountx, SUM(zz.extrabal) AS extrabal, SUM(zz.balamount) AS balamount " \
            "FROM (SELECT IFNULL(z.pcode, 'N/A') AS pcode, IFNULL(z.pname, ' NO CUSTOMER/SUPPLIER') AS pname,z.pid, " \
            "SUM(z.creditamount) AS creditamount, SUM(z.debitamount) AS debitamount, " \
            "IFNULL(z.balancecode, 'D') AS beg_code, 0 AS begamt,  " \
            "IF (z.cbcode = '"+str(chart.balancecode)+"', SUM(z.debitamount) - SUM(z.creditamount), SUM(z.creditamount) - SUM(z.debitamount)) AS balamountx,  IFNULL(extrans.bal, 0) AS extrabal, " \
            "IF (z.cbcode = '"+str(chart.balancecode)+"', (SUM(z.debitamount) - SUM(z.creditamount) + IFNULL(extrans.bal, 0)), (SUM(z.creditamount) - SUM(z.debitamount) + IFNULL(extrans.bal, 0))) AS balamount " \
            "FROM ( SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, a.document_refnum, a.document_refdate, " \
            "a.balancecode, IF (a.balancecode = 'C', a.amount, 0) AS creditamount, IF (a.balancecode = 'D', a.amount, 0) AS debitamount, " \
            "a.document_customer_id, a.document_supplier_id, '"+str(chart.balancecode)+"' AS cbcode, " \
            "b.accountcode, b.description, b.customer_enable, b.supplier_enable, b.nontrade, b.setup_customer, b.setup_supplier, " \
            "IF (b.customer_enable = 'Y', dcust.id, IF (b.supplier_enable = 'Y', dsup.id, IF (b.setup_customer != '', scust.id, ssup.id))) AS pid,  " \
            "IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) AS pcode,  " \
            "IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) AS pname, " \
            "IF (b.customer_enable = 'Y', dcust.tin, IF (b.supplier_enable = 'Y', dsup.tin, IF (b.setup_customer != '', scust.tin, ssup.tin))) AS ptin " \
            "FROM subledger AS a " \
            "LEFT OUTER JOIN chartofaccount AS b ON b.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN customer AS dcust ON dcust.id = a.document_customer_id " \
            "LEFT OUTER JOIN customer AS scust ON scust.id =  b.setup_customer " \
            "LEFT OUTER JOIN supplier AS dsup ON dsup.id = a.document_supplier_id " \
            "LEFT OUTER JOIN supplier AS ssup ON ssup.id = b.setup_supplier " \
            "WHERE a.chartofaccount_id IN ("+str(conchart)+") " \
            ""+str(conpayeecode)+" "+str(conpayeename)+" AND DATE(document_date) >= '"+str(dfrom)+"' AND DATE(document_date) <= '"+str(dto)+"' "+str(orderby) +") AS z  "+str(contran) +" GROUP BY pcode " \
            "UNION " \
            "SELECT IFNULL(s.code, 'N/A') AS pcode, IFNULL(s.name, ' NO CUSTOMER/SUPPLIER') AS pname, s.id AS pid, " \
            "0 AS creditamount, 0 AS debitamount, " \
            "IFNULL(b.beg_code, 'D') AS beg_code, IF (b.beg_code = 'D', IFNULL(b.beg_amt, 0), IFNULL(b.beg_amt, 0) * -1) AS begamt,  " \
            "0 AS balamountx, 0 AS extrabal, IF (b.beg_code = 'D', IFNULL(b.beg_amt, 0), IFNULL(b.beg_amt, 0) * -1) AS balamount  " \
            "FROM beginningbalance  AS b " \
            "LEFT OUTER JOIN supplier AS s ON s.id = b.code_id " \
            " "+str(conbeg)+") zz " \
            "GROUP BY zz.pid ORDER BY zz.pname"

    print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def querySOA(dto, dfrom, transaction, chartofaccount, payeecode, payeename):

    conchart = ""
    orderby = "ORDER BY document_date ASC, FIELD(a.document_type, 'AP','CV','JV','OR')"
    conpayeecode = ""
    conpayeename = ""

    if chartofaccount:
        conchart = "SELECT id FROM chartofaccount WHERE id = '"+str(chartofaccount)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"
    else:
        conchart  = "SELECT id FROM chartofaccount WHERE main = '"+str(transaction)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"

    if payeecode:
        conpayeecode = "AND IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) = '"+str(payeecode)+"'"

    if payeename:
        conpayeename = "AND IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) = '"+str(payeename)+"'"

    print conchart
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, a.document_refnum, a.document_refdate, " \
            "a.balancecode, IF (a.balancecode = 'C', a.amount, 0) AS creditamount, IF (a.balancecode = 'D', a.amount, 0) AS debitamount, " \
            "a.document_customer_id, a.document_supplier_id,  " \
            "b.accountcode, b.description, b.customer_enable, b.supplier_enable, b.nontrade, b.setup_customer, b.setup_supplier, " \
            "IF (b.customer_enable = 'Y', dcust.id, IF (b.supplier_enable = 'Y', dsup.id, IF (b.setup_customer != '', scust.id, ssup.id))) AS pid,  " \
            "IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) AS pcode,  " \
            "IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) AS pname, " \
            "IF (b.customer_enable = 'Y', dcust.tin, IF (b.supplier_enable = 'Y', dsup.tin, IF (b.setup_customer != '', scust.tin, ssup.tin))) AS ptin " \
            "FROM subledger AS a " \
            "LEFT OUTER JOIN chartofaccount AS b ON b.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN customer AS dcust ON dcust.id = a.document_customer_id " \
            "LEFT OUTER JOIN customer AS scust ON scust.id =  b.setup_customer " \
            "LEFT OUTER JOIN supplier AS dsup ON dsup.id = a.document_supplier_id " \
            "LEFT OUTER JOIN supplier AS ssup ON ssup.id = b.setup_supplier " \
            "WHERE a.chartofaccount_id IN ("+str(conchart)+") " \
            ""+str(conpayeecode)+" "+str(conpayeename)+" AND DATE(document_date) >= '"+str(dfrom)+"' AND DATE(document_date) <= '"+str(dto)+"' "+str(orderby)

    #print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def querySOATran(dto, dfrom, transaction, chartofaccount, payeecode, payeename):

    conchart = ""
    orderby = "ORDER BY document_date ASC, FIELD(a.document_type, 'AP','CV','JV','OR')"
    conpayeecode = ""
    conpayeename = ""

    if chartofaccount:
        conchart = "SELECT id FROM chartofaccount WHERE id = '"+str(chartofaccount)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"
    else:
        conchart  = "SELECT id FROM chartofaccount WHERE main = '"+str(transaction)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"

    if payeecode:
        conpayeecode = "AND IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) = '"+str(payeecode)+"'"

    if payeename:
        conpayeename = "AND IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) = '"+str(payeename)+"'"

    print conchart
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, a.document_refnum, a.document_refdate, " \
            "a.balancecode, IF (a.balancecode = 'C', a.amount, 0) AS creditamount, IF (a.balancecode = 'D', a.amount, 0) AS debitamount, " \
            "a.document_customer_id, a.document_supplier_id,  " \
            "b.accountcode, b.description, b.customer_enable, b.supplier_enable, b.nontrade, b.setup_customer, b.setup_supplier, " \
            "IF (b.customer_enable = 'Y', dcust.id, IF (b.supplier_enable = 'Y', dsup.id, IF (b.setup_customer != '', scust.id, ssup.id))) AS pid,  " \
            "IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) AS pcode,  " \
            "IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) AS pname, " \
            "IF (b.customer_enable = 'Y', dcust.tin, IF (b.supplier_enable = 'Y', dsup.tin, IF (b.setup_customer != '', scust.tin, ssup.tin))) AS ptin " \
            "FROM subledger AS a " \
            "LEFT OUTER JOIN chartofaccount AS b ON b.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN customer AS dcust ON dcust.id = a.document_customer_id " \
            "LEFT OUTER JOIN customer AS scust ON scust.id =  b.setup_customer " \
            "LEFT OUTER JOIN supplier AS dsup ON dsup.id = a.document_supplier_id " \
            "LEFT OUTER JOIN supplier AS ssup ON ssup.id = b.setup_supplier " \
            "WHERE a.chartofaccount_id IN ("+str(conchart)+") " \
            ""+str(conpayeecode)+" "+str(conpayeename)+" AND DATE(document_date) > '"+str(dfrom)+"' AND DATE(document_date) < '"+str(dto)+"' "+str(orderby)

    print 'querySOATran'
    print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def begBalance(id):

    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT * FROM beginningbalance WHERE trans_code = 'NT' AND code_id = '"+str(id)+"'"

    print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

@csrf_exempt
def datafix(request):
    print 'AP datafix'

    chart = Chartofaccount.objects.filter(isdeleted=0).filter(customer_enable='Y').values_list('id', flat=True)
    print chart
    detail = Apdetail.objects.filter(isdeleted=0).filter(chartofaccount_id__in=chart)

    #print detail.count()
    counter = 1
    for d in detail:

        s = Subledger.objects.filter(document_type='AP').filter(document_id=d.id).first()

        if s:
            if s.document_customer_id != d.customer_id:
                print str(d.id)+'|'+str(d.customer_id)+'|'+str(d.ap_num)+'|'+str(s.document_customer_id)+'|'+str(s.document_num)
                print counter
                counter += 1

    print counter

    return 'hey'
