# Used for XLS & XLSX excel file types.

import xlrd
import hashlib
import datetime as dt
from decimal import Decimal
from dateutil.parser import parse
from bankrecon.models import Bankrecon
from django.http import JsonResponse
from dbfread import DBF
from utils.views import storeupload
from django.conf import settings
from datetime import datetime


bgblue = "bg-blue-400"
bgyellow = "bg-yellow-700"
bgorange = "bg-orange-400"
bggrey = "bg-grey-700"
errorunabletoimport = "Unable to import"
errorcommaorcolumnexceeded = "Comma detected or column count exceeded at "
catchheaderorfooter = "Header or footer"
catchheader = "Header"
dataexists = " Data exists"


def RobinsonSavingsBankDBF(request): 
    allowedemptyfield = 5
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    datacount = 0
    successdata = []
    faileddata = []

    upload_directory = 'bankrecon/'
    sequence = datetime.now().isoformat().replace(':', '-')
    if storeupload(request.FILES['data_file'], sequence, 'dbf', upload_directory + 'imported_bankstatement/'):
        creditamount = '0.00'
        debitamount = '0.00'
        for field in DBF(settings.MEDIA_ROOT + '/' + upload_directory + 'imported_bankstatement/' + str(sequence) + '.dbf', char_decode_errors='ignore'):
            datacount += 1

            postingdate = field.values()[0] if field.values()[0] != '' else ''
            valuedate = field.values()[1] if field.values()[1] != '' else ''
            indicator = field.values()[3] if field.values()[3] != '' else ''
            balance = field.values()[4] if field.values()[4] != '' else ''
            transactionnarration = field.values()[5] if field.values()[5] != '' else ''
            instrumentnumber = field.values()[6] if field.values()[6] != '' else ''
            # accountno = fields[7] if fields[7] != '' else ''
            # transactiondate = fields[8] if fields[8] != '' else ''
            # transactioncategory = fields[9] if fields[9] != '' else ''
            transactionid = field.values()[10] if field.values()[10] != '' else ''
            branchname = field.values()[11] if field.values()[11] != '' else ''
            remarks = field.values()[12] if field.values()[12] != '' else ''

            if field.values().count('') <= allowedemptyfield:

                if indicator == 'D':
                    debitamount = field.values()[2] if field.values()[2] != '' else '0.00'
                    creditamount = '0.00'
                elif indicator == 'C':
                    creditamount = field.values()[2] if field.values()[2] != '' else '0.00'
                    debitamount = '0.00'

                # Hash: transdate,particulars,debit,credit,balance
                generatedkey = generate_hash_key(postingdate, transactionnarration, debitamount, creditamount, balance)

                if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                    # Result: transdate,branch,particulars,debit,credit
                    faileddata.append([postingdate, branchname, transactionnarration, debitamount, creditamount, dataexists, bgblue])
                    failedcount += 1
                    existscount += 1
                else:
                    try:
                        postingdate = dt.datetime.strptime(str(postingdate), '%d/%m/%Y').strftime('%Y-%m-%d')
                        Bankrecon.objects.create(
                            bank_id=request.POST['bank_id'],
                            bankaccount_id=request.POST['bank_account'],
                            generatedkey=generatedkey,
                            transaction_date=postingdate,
                            posting_date=postingdate,
                            branch=str(branchname),
                            particulars=str(transactionnarration),
                            debit_amount=Decimal(debitamount),
                            credit_amount=Decimal(creditamount),
                            balance_amount=Decimal(balance),
                            checknumber=str(instrumentnumber),
                            transactioncode = str(transactionid),
                            remarks=str(remarks)
                        )
                        successdata.append([postingdate, branchname, transactionnarration, debitamount, creditamount])
                        successcount += 1
                    except:
                        if debitamount.replace(' ', '').isalpha() or creditamount.replace(' ', '').isalpha() or balance.replace(' ', '').isalpha():
                            faileddata.append([postingdate, branchname, transactionnarration, '', '', catchheader, bggrey])
                            headorfootcount += 1
                        elif not is_date(postingdate):
                            faileddata.append([postingdate, "", transactionnarration, '', '', catchheaderorfooter, bggrey])
                            headorfootcount += 1
                        else:
                            # can be special characters detected. - enye or date format conflict.
                            faileddata.append([postingdate, branchname, transactionnarration, debitamount, creditamount, errorunabletoimport, bgorange])
                            failedcount += 1
                            dberrorcount += 1
            else:
                faileddata.append([postingdate, branchname, transactionnarration, '', '', catchheaderorfooter, bggrey])
                headorfootcount += 1

    count = successcount + failedcount
    bodycount = datacount - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


def RobinsonSavingsBank(request): 
    workbook = xlrd.open_workbook(file_contents=request.FILES['data_file'].read(), encoding_override='utf8')
    # Open the worksheet
    worksheet = workbook.sheet_by_index(0)

    allowedemptyfield = 5
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    successdata = []
    faileddata = []
    
    # Iterate the rows
    for r in range(0, worksheet.nrows):
        fields = []
        creditamount = '0.00'
        debitamount = '0.00'
        # Iterate the cell fields
        for c in range(0, 13):
            fields.append(worksheet.cell_value(r, c))
        
        postingdate = fields[0] if fields[0] != '' else ''
        valuedate = fields[1] if fields[1] != '' else ''
        indicator = fields[3] if fields[3] != '' else ''
        balance = fields[4] if fields[4] != '' else ''
        transactionnarration = fields[5] if fields[5] != '' else ''
        instrumentnumber = fields[6] if fields[6] != '' else ''
        # accountno = fields[7] if fields[7] != '' else ''
        # transactiondate = fields[8] if fields[8] != '' else ''
        # transactioncategory = fields[9] if fields[9] != '' else ''
        transactionid = fields[10] if fields[10] != '' else ''
        branchname = fields[11] if fields[11] != '' else ''
        remarks = fields[12] if fields[12] != '' else ''

        if fields.count('') <= allowedemptyfield:

            if indicator == 'D':
                debitamount = fields[2] if fields[2] != '' else '0.00'
                creditamount = '0.00'
            elif indicator == 'C':
                creditamount = fields[2] if fields[2] != '' else '0.00'
                debitamount = '0.00'

            # Hash: transdate,particulars,debit,credit,balance
            generatedkey = generate_hash_key(postingdate, transactionnarration, debitamount, creditamount, balance)

            if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                # Result: transdate,branch,particulars,debit,credit
                faileddata.append([postingdate, branchname, transactionnarration, debitamount, creditamount, dataexists, bgblue])
                failedcount += 1
                existscount += 1
            else:
                try:
                    postingdate = datetime.datetime.strptime(str(postingdate), '%d/%m/%Y').strftime('%Y-%m-%d')

                    Bankrecon.objects.create(
                        bank_id=request.POST['bank_id'],
                        bankaccount_id=request.POST['bank_account'],
                        generatedkey=generatedkey,
                        transaction_date=postingdate,
                        posting_date=postingdate,
                        branch=str(branchname),
                        particulars=str(transactionnarration),
                        debit_amount=Decimal(debitamount),
                        credit_amount=Decimal(creditamount),
                        balance_amount=Decimal(balance),
                        checknumber=str(instrumentnumber),
                        transactioncode = str(transactionid),
                        remarks=str(remarks)
                    )
                    successdata.append([postingdate, branchname, transactionnarration, debitamount, creditamount])
                    successcount += 1
                except:
                    if debitamount.replace(' ', '').isalpha() or creditamount.replace(' ', '').isalpha() or balance.replace(' ', '').isalpha():
                        faileddata.append([postingdate, branchname, transactionnarration, '', '', catchheader, bggrey])
                        headorfootcount += 1
                    elif not is_date(postingdate):
                        faileddata.append([postingdate, "", transactionnarration, '', '', catchheaderorfooter, bggrey])
                        headorfootcount += 1
                    else:
                        # can be special characters detected. - enye or date format conflict.
                        faileddata.append([postingdate, branchname, transactionnarration, debitamount, creditamount, errorunabletoimport, bgorange])
                        failedcount += 1
                        dberrorcount += 1
        else:
            faileddata.append([postingdate, branchname, transactionnarration, '', '', catchheaderorfooter, bggrey])
            headorfootcount += 1

    count = successcount + failedcount
    bodycount = worksheet.nrows - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


def UnionBankDBF(request):
    allowedemptyfield = 32
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    datacount = 0
    successdata = []
    faileddata = []

    upload_directory = 'bankrecon/'
    sequence = datetime.now().isoformat().replace(':', '-')
    if storeupload(request.FILES['data_file'], sequence, 'dbf', upload_directory + 'imported_bankstatement/'):
        
        for field in DBF(settings.MEDIA_ROOT + '/' + upload_directory + 'imported_bankstatement/' + str(sequence) + '.dbf', char_decode_errors='ignore'):
            datacount += 1
            
            transactiondate = field.values()[0] if field.values()[0] != '' else ''
            posteddate = field.values()[1] if field.values()[1] != '' else ''
            transactionid = field.values()[2] if field.values()[2] != '' else ''
            transactiondescription = field.values()[3] if field.values()[3] != '' else ''
            checknumber = field.values()[4] if field.values()[4] != '' else ''
            debit = field.values()[5] if field.values()[5] != '' else '0.00'
            credit = field.values()[6] if field.values()[6] != '' else '0.00'
            endingbalance = field.values()[7] if field.values()[7] != '' else '0.00'
            referencenumber = field.values()[8] if field.values()[8] != '' else ''
            remarks = field.values()[9] if field.values()[9] != '' else ''
            # remarks1 = field.values()[10] if field.values()[10] != '' else ''
            # remarks2 = field.values()[11] if field.values()[11] != '' else ''
            branch = field.values()[12] if field.values()[12] != '' else ''

            if field.values().count('') <= allowedemptyfield:
                
                # Hash: transdate,particulars,debit,credit,balance
                generatedkey = generate_hash_key(posteddate, transactiondate, debit, credit, endingbalance)

                if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                    # Result: transdate,branch,particulars,debit,credit
                    faileddata.append([posteddate, branch, transactiondescription, debit, credit, dataexists, bgblue])
                    failedcount += 1
                    existscount += 1
                else:
                    try:
                        
                        transactiondate = transactiondate.split('T')[0]
                        transactiondate = dt.datetime.strptime(str(transactiondate), '%Y-%m-%d').strftime('%Y-%m-%d')

                        pdate = posteddate.split('T')[0]
                        pdate = dt.datetime.strptime(str(pdate), '%Y-%m-%d').strftime('%Y-%m-%d')

                        debitamount = debit.replace(',', '')
                        creditamount = credit.replace(',', '')
                        endingbalance = endingbalance.replace(',', '')

                        Bankrecon.objects.create(
                            bank_id=request.POST['bank_id'],
                            bankaccount_id=request.POST['bank_account'],
                            generatedkey=generatedkey,
                            transaction_date=transactiondate,
                            posting_date=pdate,
                            branch=str(branch),
                            particulars=str(transactiondescription),
                            debit_amount=Decimal(debitamount),
                            credit_amount=Decimal(creditamount),
                            balance_amount=Decimal(endingbalance),
                            checknumber=str(checknumber),
                            transactioncode = str(transactionid),
                            remarks=str(remarks)
                        )
                        successdata.append([transactiondate, branch, transactiondescription, debit, credit])
                        successcount += 1
                    except Exception as e:
                        # print e.message
                        if debit.replace(' ', '').isalpha() or credit.replace(' ', '').isalpha() or endingbalance.replace(' ', '').isalpha():
                            faileddata.append([posteddate, branch, transactiondescription, '', '', catchheader, bggrey])
                            headorfootcount += 1
                        elif not is_date(posteddate):
                            faileddata.append([posteddate, "", transactiondescription, '', '', catchheaderorfooter, bggrey])
                            headorfootcount += 1
                        else:
                            # can be special characters detected. - enye or date format conflict.
                            faileddata.append([posteddate, branch, transactiondescription, debit, credit, errorunabletoimport, bgorange])
                            failedcount += 1
                            dberrorcount += 1
            else:
                faileddata.append([posteddate, branch, transactiondescription, '', '', catchheaderorfooter, bggrey])
                headorfootcount += 1

    count = successcount + failedcount
    bodycount = datacount - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


def UnionBank(request):
    workbook = xlrd.open_workbook(file_contents=request.FILES['data_file'].read(), encoding_override='utf8')
    # Open the worksheet
    worksheet = workbook.sheet_by_index(0)

    allowedemptyfield = 5
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    successdata = []
    faileddata = []
    
    
    # Iterate the rows
    for r in range(0, worksheet.nrows):
        fields = []
        # Iterate the cells in row
        for c in range(0, 13):
            fields.append(worksheet.cell_value(r, c))

        transactiondate = fields[0] if fields[0] != '' else ''
        posteddate = fields[1] if fields[1] != '' else ''
        transactionid = fields[2] if fields[2] != '' else ''
        transactiondescription = fields[3] if fields[3] != '' else ''
        checknumber = fields[4] if fields[4] != '' else ''
        debit = fields[5] if isinstance(fields[5], float) else '0.00'
        credit = fields[6] if isinstance(fields[6], float) else '0.00'
        endingbalance = fields[7] if fields[7] != '' else '0.00'
        referencenumber = fields[8] if fields[8] != '' else ''
        remarks = fields[9] if fields[9] != '' else ''
        # remarks1 = fields[10] if fields[10] != '' else ''
        # remarks2 = fields[11] if fields[11] != '' else ''
        branch = fields[12] if fields[12] != '' else ''

        if fields.count('') <= allowedemptyfield:
            
            # Hash: transdate,particulars,debit,credit,balance
            generatedkey = generate_hash_key(posteddate, transactiondescription, debit, credit, endingbalance)
            
            if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                # Result: transdate,branch,particulars,debit,credit
                faileddata.append([posteddate, branch, transactiondescription, debit, credit, dataexists, bgblue])
                failedcount += 1
                existscount += 1
            else:
                try:
                    transactiondate = transactiondate.split('T')[0]
                    transactiondate = datetime.datetime.strptime(str(transactiondate), '%Y-%m-%d').strftime('%Y-%m-%d')

                    pdate = posteddate.split('T')[0]
                    pdate = datetime.datetime.strptime(str(pdate), '%Y-%m-%d').strftime('%Y-%m-%d')
                   
                    Bankrecon.objects.create(
                        bank_id=request.POST['bank_id'],
                        bankaccount_id=request.POST['bank_account'],
                        generatedkey=generatedkey,
                        transaction_date=transactiondate,
                        posting_date=pdate,
                        branch=str(branch),
                        particulars=str(transactiondescription),
                        debit_amount=Decimal(debit),
                        credit_amount=Decimal(credit),
                        balance_amount=Decimal(endingbalance),
                        checknumber=str(checknumber),
                        transactioncode = str(transactionid),
                        refno=str(referencenumber),
                        remarks=str(remarks)
                    )
                    successdata.append([posteddate, branch, transactiondescription, debit, credit])
                    successcount += 1
                except Exception as e:
                    # print e.message
                    if debit.replace(' ', '').isalpha() or credit.replace(' ', '').isalpha() or endingbalance.replace(' ', '').isalpha():
                        faileddata.append([posteddate, branch, transactiondescription, '', '', catchheader, bggrey])
                        headorfootcount += 1
                    elif not is_date(posteddate):
                        faileddata.append([posteddate, "", transactiondescription, '', '', catchheaderorfooter, bggrey])
                        headorfootcount += 1
                    else:
                        # can be special characters detected. - enye or date format conflict.
                        faileddata.append([posteddate, branch, transactiondescription, debit, credit, errorunabletoimport, bgorange])
                        failedcount += 1
                        dberrorcount += 1
        else:
            faileddata.append([posteddate, branch, transactiondescription, '', '', catchheaderorfooter, bggrey])
            headorfootcount += 1

    count = successcount + failedcount
    bodycount = worksheet.nrows - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


def generate_hash_key(transdate,particulars,debit,credit,balance):
    hash = hashlib.md5(str(transdate) + str(particulars) + str(debit) + str(credit) + str(balance))
    return hash.hexdigest()


def is_date(string, fuzzy=False):
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount):
    if successcount > 0:
        result = 1
    elif existscount == bodycount:
        result = 2
    elif dberrorcount > 0:
        result = 3
    elif commadetectedcount > 0:
        result = 5
    else:
        result = 8
    return result


def json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result):
    return JsonResponse({
        'successcount': successcount,
        'failedcount': failedcount,
        'faileddata': faileddata,
        'successdata': successdata,
        'datacount': count,
        'existscount': existscount,
        'dberrorcount': dberrorcount,
        'commadetectedcount': commadetectedcount,
        'headorfootcount': headorfootcount,
        'result': result,
    })