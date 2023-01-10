''' Bankrecon Utility '''
import datetime
import hashlib
import re
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render
from bank.models import Bank
from bankrecon.models import Bankrecon
from bankrecon.importexcel import RobinsonSavingsBank, UnionBank
from bankaccount.models import Bankaccount
from bankbranch.models import Bankbranch
from bankaccounttype.models import Bankaccounttype
from subledger.models import Subledger
from currency.models import Currency
from endless_pagination.views import AjaxListView
from django.db.models import Q
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from django.template.loader import render_to_string
from companyparameter.models import Companyparameter
from acctentry.views import generatekey
from dateutil.parser import parse
from string import digits
from decimal import Decimal
import json
import xlwt


upload_size = 3
bgblue = "bg-blue-400"
bgyellow = "bg-yellow-700"
bgorange = "bg-orange-400"
bggrey = "bg-grey-700"
errorunabletoimport = "Unable to import"
errorcommaorcolumnexceeded = "Comma detected or column count exceeded at "
catchheaderorfooter = "Header or footer"
catchheader = "Header"
dataexists = " Data exists"


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Bankrecon
    template_name = 'bankrecon/index.html'
    context_object_name = 'data_list'

    page_template = 'bankrecon/index_list.html'

    def get_context_data(self, **kwargs):
       context = super(IndexView, self).get_context_data(**kwargs)
       context['bankaccount'] = Bankaccount.objects.all().filter(isdeleted=0).order_by('code')
       
       return context


@csrf_exempt
def upload(request):
    if request.method == 'POST':
        
        if request.FILES['data_file'] \
                and request.FILES['data_file'].name.endswith('.csv'):
            if request.FILES['data_file']._size < float(upload_size) * 1024 * 1024:
                    # 2-bd2, 4-bd4, 5-bd5, 6-bdo
                if request.POST['bank_account'] in ['2', '4', '5', '6']:
                    return BDO(request, columnlength=7)
                    # 7-bp2
                elif request.POST['bank_account'] in ['7']:
                    return BPI(request, columnlength=9)
                    # 9-lbp
                elif request.POST['bank_account'] in ['9']:
                    return LandBank(request, columnlength=7)
                    # 10-mb2
                elif request.POST['bank_account'] in ['10']:
                    return MetroBank(request, columnlength=11)
                    # 19-sb7, 22-sb9
                elif request.POST['bank_account'] in ['19', '22']:
                    return SecurityBank(request, columnlength=6)
                    # 32-ew1
                elif request.POST['bank_account'] in ['32']:
                    return EastWestBank(request, columnlength=9)
                    # 31-pn2
                elif request.POST['bank_account'] in ['31']:
                    return PNB(request, columnlength=9)
                else:
                    return JsonResponse({
                        'result': 7
                    })
            else:
                return JsonResponse({
                    'result': 4
                })
        elif request.FILES['data_file'] \
                and (request.FILES['data_file'].name.endswith('.xls') or request.FILES['data_file'].name.endswith('.xlsx')):
                if request.FILES['data_file']._size < float(upload_size) * 1024 * 1024:

                    if request.POST['bank_account'] in ['15']:
                        return RobinsonSavingsBank(request)
                    elif request.POST['bank_account'] in ['23']:
                        return UnionBank(request)

                else:
                    return JsonResponse({
                        'result': 4
                    })
        else:
            return JsonResponse({
                'result': 5
            })
    else:
        context = {
            "today": timezone.now(),
            "banks": Bank.objects.all().order_by('description'),
            "bankaccount": Bankaccount.objects.all().filter(isdeleted=0).order_by('code'),
            "username": request.user,
        }
        return render(request, 'bankrecon/upload.html', context)
    

def generate_hash_key(transdate,particulars,debit,credit,balance):
    hash = hashlib.md5(str(transdate) + str(particulars) + str(debit) + str(credit) + str(balance))
    return hash.hexdigest()


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


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


# Posting Date - Branch - Description - Debit - Credit - Running Balance - Check Number
def BDO(request, columnlength):
    
    csv_file = request.FILES["data_file"]
    file_data = csv_file.read().decode("utf-8")
    rows = file_data.split("\n")

    allowedemptyfield = 2
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    successdata = []
    faileddata = []
    fields = []
    increment = 0

    for row in rows:
        
        fields = row.split(",")
        increment += 1
        # validation
        postingdate = fields[0] if fields[0] != '' else ''
        branch = fields[1] if fields[1] != '' else ''
        description = fields[2] if fields[2] != '' else ''
        debit = fields[3] if fields[3] != '' else '0.00'
        credit = fields[4] if fields[4] != '' else '0.00'
        runningbalance = fields[5] if fields[5] != '' else '0.00'
        checknumber = fields[6] if fields[6] != '' else ''

        if fields.count('') <= allowedemptyfield:

            if len(fields) == columnlength:
                # Hash: transdate,particulars,debit,credit,balance
                unique_description = str(description) + '-seprtr-' + str(increment)
                generatedkey = generate_hash_key(postingdate, unique_description, debit, credit, runningbalance)

                if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                    # Result: transdate,branch,particulars,debit,credit
                    faileddata.append([postingdate, branch, description, debit, credit, dataexists, bgblue])
                    failedcount += 1
                    existscount += 1
                else:

                    try:
                        postingdate = datetime.datetime.strptime(str(postingdate), '%m/%d/%Y').strftime('%Y-%m-%d')

                        Bankrecon.objects.create(
                            bank_id=request.POST['bank_id'],
                            bankaccount_id=request.POST['bank_account'],
                            generatedkey=generatedkey,
                            transaction_date=postingdate,
                            posting_date=postingdate,
                            branch=str(branch),
                            particulars=str(description),
                            debit_amount=Decimal(debit),
                            credit_amount=Decimal(credit),
                            balance_amount=Decimal(runningbalance),
                            checknumber=str(checknumber),
                        )
                        successdata.append([postingdate, branch, description, debit, credit])
                        successcount += 1
                    except:
                        if debit.replace(' ', '').isalpha() or credit.replace(' ', '').isalpha() or runningbalance.replace(' ', '').isalpha():
                            faileddata.append([postingdate, branch, description, '', '', catchheader, bggrey])
                            headorfootcount += 1
                        elif not is_date(postingdate):
                            faileddata.append([postingdate, "", description, '', '', catchheaderorfooter, bggrey])
                            headorfootcount += 1
                        else:
                            # can be special characters detected. - enye or date format conflict.
                            faileddata.append([postingdate, branch, description, debit, credit, errorunabletoimport, bgorange])
                            failedcount += 1
                            dberrorcount += 1
            else:
                faileddata.append([postingdate, branch, description, debit, credit, errorcommaorcolumnexceeded + str(columnlength), bgyellow])
                failedcount += 1
                commadetectedcount += 1
        else:
            faileddata.append([postingdate, branch, description, '', '', catchheaderorfooter, bggrey])
            headorfootcount += 1

    count = successcount + failedcount
    bodycount = len(rows) - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


# Date - Check Number - SBA Reference No. - Branch - Transaction Code - Transaction Description - Debit - Credit - Running Balance
def BPI(request, columnlength):
    
    csv_file = request.FILES["data_file"]
    file_data = csv_file.read().decode("utf-8")
    rows = file_data.split("\n")

    allowedemptyfield = 3
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    successdata = []
    faileddata = []
    fields = []
    increment = 0

    for row in rows:

        fields = row.split(",")
        increment += 1
        # validation
        date = fields[0] if fields[0] != '' else ''
        checknumber = fields[1] if fields[1] != '' else ''
        sbareferenceno = fields[2] if fields[2] != '' else ''
        branch = fields[3] if fields[3] != '' else ''
        transactioncode = fields[4] if fields[4] != '' else ''
        transactiondescription = fields[5] if fields[5] != '' else ''
        debit = fields[6] if fields[6] != '' else '0.00'
        credit = fields[7] if fields[7] != '' else '0.00'
        runningbalance = fields[8] if fields[8] != '' else '0.00'

        if fields.count('') <= allowedemptyfield:

            if len(fields) == columnlength:
                # Hash: transdate,particulars,debit,credit,balance
                unique_description = str(transactiondescription) + '-seprtr-' + str(increment)
                generatedkey = generate_hash_key(date, unique_description, debit, credit, runningbalance)

                if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                    # Result: transdate,branch,particulars,debit,credit
                    faileddata.append([date, branch, transactiondescription, debit, credit, dataexists, bgblue])
                    failedcount += 1
                    existscount += 1
                else:
                    try:
                        date = datetime.datetime.strptime(str(date), '%m/%d/%Y').strftime('%Y-%m-%d')

                        Bankrecon.objects.create(
                            bank_id=request.POST['bank_id'],
                            bankaccount_id=request.POST['bank_account'],
                            generatedkey=generatedkey,
                            transaction_date=date,
                            branch=str(branch),
                            particulars=str(transactiondescription),
                            debit_amount=Decimal(debit),
                            credit_amount=Decimal(credit),
                            balance_amount=Decimal(runningbalance),
                            transactioncode=str(transactioncode),
                            refno=str(sbareferenceno),
                            checknumber=str(checknumber),
                        )
                        successdata.append([date, branch, transactiondescription, debit, credit])
                        successcount += 1
                    except:
                        if debit.replace(' ', '').isalpha() or credit.replace(' ', '').isalpha() or runningbalance.replace(' ', '').isalpha():
                            faileddata.append([date, branch, transactiondescription, '', '', catchheader, bggrey])
                            headorfootcount += 1
                        elif not is_date(date):
                            faileddata.append([date, "", transactiondescription, '', '', catchheaderorfooter, bggrey])
                            headorfootcount += 1
                        else:
                            # can be special characters detected. - enye or date format conflict or non-decimal amount.
                            faileddata.append([date, branch, transactiondescription, debit, credit, errorunabletoimport, bgorange])
                            failedcount += 1
                            dberrorcount += 1
            else: 
                faileddata.append([date, branch, transactiondescription, debit, credit, errorcommaorcolumnexceeded + str(columnlength), bgyellow])
                failedcount += 1
                commadetectedcount += 1
        else:
            faileddata.append([date, branch, transactiondescription, '', '', catchheaderorfooter, bggrey])
            headorfootcount += 1

    count = successcount + failedcount
    bodycount = len(rows) - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


# Transaction Date - Posting Date - Time - Check Number - Transaction Description - Debit Amount - Credit Amount - Balance - Branch/Channel - Subscriber Number/TIN Number - Sequence Number
def MetroBank(request, columnlength):
    
    csv_file = request.FILES["data_file"]
    file_data = csv_file.read().decode("utf-8")
    rows = file_data.split("\n")
    
    allowedemptyfield = 3
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    successdata = []
    faileddata = []
    fields = []
    increment = 0
    
    for row in rows:
        
        fields = row.split(",")
        increment += 1
        #validation
        transactiondate = fields[0] if fields[0] != '' else ''
        postingdate = fields[1] if fields[1] != '' else ''
        time = fields[2] if fields[2] != '' else ''
        checknumber = fields[3] if fields[3] != '' else ''
        transactiondescription = fields[4] if fields[4] != '' else ''
        debitamount = fields[5] if fields[5] != '' else '0.00'
        creditamount = fields[6] if fields[6] != '' else '0.00'
        balance = fields[7] if fields[7] != '' else '0.00'
        branchorchannel = fields[8] if fields[8] != '' else ''
        subscriberortinnumber = fields[9] if fields[9] != '' else ''
        sequencenumber = fields[10] if fields[10] != '' else ''
        
        if fields.count('') <= allowedemptyfield:
            
            if len(fields) == columnlength:
                # Hash: transdate,particulars,debit,credit,balance
                unique_description = str(transactiondescription) + '-seprtr-' + str(increment)
                generatedkey = generate_hash_key(transactiondate,unique_description,debitamount,creditamount,balance)

                if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                    faileddata.append([postingdate, branchorchannel, transactiondescription, debitamount, creditamount, dataexists, bgblue])
                    failedcount += 1
                    existscount += 1
                else:
                    try:
                        transactiondate = datetime.datetime.strptime(str(transactiondate), '%m/%d/%Y').strftime('%Y-%m-%d')
                        postingdate = datetime.datetime.strptime(str(postingdate), '%m/%d/%Y').strftime('%Y-%m-%d')
                        Bankrecon.objects.create(
                            bank_id=request.POST['bank_id'],
                            bankaccount_id=request.POST['bank_account'],
                            generatedkey=generatedkey,
                            transaction_date=transactiondate,
                            posting_date=postingdate,
                            transaction_time=str(time),
                            checknumber=str(checknumber),
                            particulars=str(transactiondescription),
                            debit_amount=debitamount,
                            credit_amount=creditamount,
                            balance_amount=balance,
                            branch=str(branchorchannel),
                            tinnumber=str(subscriberortinnumber),
                            transactioncode=str(sequencenumber)     # Sequence number
                        )
                        successdata.append([postingdate, branchorchannel, transactiondescription, debitamount, creditamount])
                        successcount += 1
                    except:
                        if debitamount.replace(' ', '').isalpha() or creditamount.replace(' ', '').isalpha() or balance.replace(' ', '').isalpha():
                            faileddata.append([postingdate, branchorchannel, transactiondescription, '', '', catchheader, bggrey])
                            headorfootcount += 1
                        elif not is_date(postingdate):
                            faileddata.append([postingdate, "", transactiondescription, '', '', catchheaderorfooter, bggrey])
                            headorfootcount += 1
                        else:
                            # can be special characters detected. - enye
                            faileddata.append([postingdate, branchorchannel, transactiondescription, debitamount, creditamount, errorunabletoimport, bgorange])
                            failedcount += 1
                            dberrorcount += 1
            else: 
                faileddata.append([postingdate, branchorchannel, transactiondescription, debitamount, creditamount, errorcommaorcolumnexceeded + str(columnlength), bgyellow])
                failedcount += 1
                commadetectedcount += 1
        else:
            faileddata.append([postingdate, branchorchannel, transactiondescription, '', '', catchheaderorfooter, bggrey])
            headorfootcount += 1
    
    count = successcount + failedcount
    bodycount = len(rows) - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


# Posting Date, Transaction Description, Credit Amount, Debit Amount, Running Balance, Narrative
def SecurityBank(request, columnlength):
    csv_file = request.FILES["data_file"]
    file_data = csv_file.read().decode("utf-8")
    rows = file_data.split("\n")
    
    allowedemptyfield = 2
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    successdata = []
    faileddata = []
    fields = []
    increment = 0
    
    for row in rows:
        
        fields = row.split(",")
        increment += 1
        # validation
        postingdate = fields[0] if fields[0] != '' else ''
        transactiondescription = fields[1] if fields[1] != '' else ''
        creditamount = fields[2] if fields[2] != '' else '0.00'
        debitamount = fields[3] if fields[3] != '' else '0.00'
        runningbalance = fields[4] if fields[4] != '' else '0.00'
        narrative = fields[5] if fields[5] != '' else ''
        
        if fields.count('') <= allowedemptyfield:
            
            if len(fields) == columnlength:
                # Hash: transdate,particulars,debit,credit,balance
                unique_description = str(transactiondescription) + '-seprtr-' + str(increment)
                generatedkey = generate_hash_key(postingdate,unique_description,debitamount,creditamount,runningbalance)

                if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                    faileddata.append([postingdate, "", transactiondescription, debitamount, creditamount, dataexists, bgblue])
                    failedcount += 1
                    existscount += 1
                else:
                    try:
                        postingdate = datetime.datetime.strptime(str(postingdate), '%d-%b-%y').strftime('%Y-%m-%d')
                        Bankrecon.objects.create(
                            bank_id=request.POST['bank_id'],
                            bankaccount_id=request.POST['bank_account'],
                            generatedkey=generatedkey,
                            transaction_date=postingdate,
                            posting_date=postingdate,
                            particulars=str(transactiondescription),
                            debit_amount=debitamount,
                            credit_amount=creditamount,
                            balance_amount=runningbalance,
                            narrative=str(narrative)
                        )
                        successdata.append([postingdate, "", transactiondescription, debitamount, creditamount])
                        successcount += 1
                    except:
                        if debitamount.replace(' ', '').isalpha() or creditamount.replace(' ', '').isalpha() or runningbalance.replace(' ', '').isalpha():
                            faileddata.append([postingdate, "", transactiondescription, '', '', catchheader, bggrey])
                            headorfootcount += 1
                        elif not is_date(postingdate):
                            faileddata.append([postingdate, "", transactiondescription, '', '', catchheaderorfooter, bggrey])
                            headorfootcount += 1
                        else:
                            # can be special characters detected. - enye
                            faileddata.append([postingdate, "", transactiondescription, debitamount, creditamount, errorunabletoimport, bgorange])
                            failedcount += 1
                            dberrorcount += 1
            else: 
                faileddata.append([postingdate, "", transactiondescription, debitamount, creditamount, errorcommaorcolumnexceeded + str(columnlength), bgyellow])
                failedcount += 1
                commadetectedcount += 1
        else:
            faileddata.append([postingdate, "", transactiondescription, '', '', catchheaderorfooter, bggrey])
            headorfootcount += 1
    
    count = successcount + failedcount
    bodycount = len(rows) - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


def EastWestBank(request, columnlength=9):
    csv_file = request.FILES["data_file"]
    file_data = csv_file.read().decode("utf-8")
    rows = file_data.split("\n")
    
    allowedemptyfield = 3
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    successdata = []
    faileddata = []
    fields = []
    increment = 0
    
    for row in rows:
        
        fields = row.split(",")
        increment += 1
        # validation
        postingdatetime = fields[0] if fields[0] != '' else ''
        description = fields[1] if fields[1] != '' else ''
        store = fields[2] if fields[2] != '' else ''
        debit = fields[3] if fields[3] != '' else '0.00'
        credit = fields[4] if fields[4] != '' else '0.00'
        runningbalance = fields[5] if fields[5] != '' else '0.00'
        ftreferenceno = fields[6] if fields[6] != '' else ''
        batchreferenceno = fields[7] if fields[7] != '' else ''
        checknumber = fields[8] if fields[8] != '' else ''

        if fields.count('') <= allowedemptyfield:
            
            if len(fields) == columnlength:
                # Hash: transdate,particulars,debit,credit,balance
                unique_description = str(description) + '-seprtr-' + str(increment)
                generatedkey = generate_hash_key(postingdatetime,unique_description,debit,credit,runningbalance)

                if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                    faileddata.append([postingdatetime, store, description, debit, credit, dataexists, bgblue])
                    failedcount += 1
                    existscount += 1
                else:
                    try:
                        date = postingdatetime.split(' ')[0]
                        time = postingdatetime.split(' ')[1]
                        postingdate = datetime.datetime.strptime(str(date), '%m/%d/%Y').strftime('%Y-%m-%d')
                        Bankrecon.objects.create(
                            bank_id=request.POST['bank_id'],
                            bankaccount_id=request.POST['bank_account'],
                            generatedkey=generatedkey,
                            transaction_date=postingdate,
                            transaction_time=time,
                            posting_date=postingdate,
                            particulars=str(description),
                            branch=str(store),
                            debit_amount=debit,
                            credit_amount=credit,
                            balance_amount=runningbalance,
                            transactioncode=str(ftreferenceno),
                            refno=str(batchreferenceno),
                            checknumber=str(checknumber)
                        )
                        successdata.append([postingdatetime, store, description, debit, credit])
                        successcount += 1
                    except:
                        if debit.replace(' ', '').isalpha() or credit.replace(' ', '').isalpha() or runningbalance.replace(' ', '').isalpha():
                            faileddata.append([postingdatetime, store, description, '', '', catchheader, bggrey])
                            headorfootcount += 1
                        elif not is_date(postingdatetime):
                            faileddata.append([postingdatetime, store, description, '', '', catchheaderorfooter, bggrey])
                            headorfootcount += 1
                        else:
                            faileddata.append([postingdatetime, store, description, debit, credit, errorunabletoimport, bgorange])
                            failedcount += 1
                            dberrorcount += 1
            else: 
                faileddata.append([postingdatetime, store, description, debit, credit, errorcommaorcolumnexceeded + str(columnlength), bgyellow])
                failedcount += 1
                commadetectedcount += 1
        else:
            faileddata.append([postingdatetime, store, description, '', '', catchheaderorfooter, bggrey])
            headorfootcount += 1
    
    count = successcount + failedcount
    bodycount = len(rows) - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


def LandBank(request, columnlength=7):
    csv_file = request.FILES["data_file"]
    file_data = csv_file.read().decode("utf-8")
    rows = file_data.split("\n")
    
    allowedemptyfield = 2
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    successdata = []
    faileddata = []
    fields = []
    increment = 0
    
    for row in rows:
        
        fields = row.split(",")
        increment += 1
        # validation
        transdatetime = fields[0] if fields[0] != '' else ''
        description = fields[1] if fields[1] != '' else ''
        debit = fields[2] if fields[2] != '' else '0.00'
        credit = fields[3] if fields[3] != '' else '0.00'
        balance = fields[4] if fields[4] != '' else '0.00'
        branch = fields[5] if fields[5] != '' else ''
        chequenumber = fields[6] if fields[6] != '' else ''

        if fields.count('') <= allowedemptyfield:
            
            if len(fields) == columnlength:
                # Hash: transdate,particulars,debit,credit,balance
                unique_description = str(description) + '-seprtr-' + str(increment)
                generatedkey = generate_hash_key(transdatetime,unique_description,debit,credit,balance)

                if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                    faileddata.append([transdatetime, branch, description, debit, credit, dataexists, bgblue])
                    failedcount += 1
                    existscount += 1
                else:
                    try:
                        date = transdatetime.split(' ')[0]
                        time = transdatetime.split(' ')[1]
                        transactiondate = datetime.datetime.strptime(str(date), '%m/%d/%Y').strftime('%Y-%m-%d')
                        Bankrecon.objects.create(
                            bank_id=request.POST['bank_id'],
                            bankaccount_id=request.POST['bank_account'],
                            generatedkey=generatedkey,
                            transaction_date=transactiondate,
                            transaction_time=time,
                            posting_date=transactiondate,
                            particulars=str(description),
                            branch=str(branch),
                            debit_amount=debit,
                            credit_amount=credit,
                            balance_amount=balance,
                            checknumber=str(chequenumber)
                        )
                        successdata.append([transdatetime, branch, description, debit, credit])
                        successcount += 1
                    except:
                        if debit.replace(' ', '').isalpha() or credit.replace(' ', '').isalpha() or balance.replace(' ', '').isalpha():
                            faileddata.append([transdatetime, branch, description, '', '', catchheader, bggrey])
                            headorfootcount += 1
                        elif not is_date(transdatetime):
                            faileddata.append([transdatetime, branch, description, '', '', catchheaderorfooter, bggrey])
                            headorfootcount += 1
                        else:
                            faileddata.append([transdatetime, branch, description, debit, credit, errorunabletoimport, bgorange])
                            failedcount += 1
                            dberrorcount += 1
            else: 
                faileddata.append([transdatetime, branch, description, debit, credit, errorcommaorcolumnexceeded + str(columnlength), bgyellow])
                failedcount += 1
                commadetectedcount += 1
        else:
            faileddata.append([transdatetime, branch, description, '', '', catchheaderorfooter, bggrey])
            headorfootcount += 1
    
    count = successcount + failedcount
    bodycount = len(rows) - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


def PNB(request, columnlength=9):
    csv_file = request.FILES["data_file"]
    file_data = csv_file.read().decode("utf-8")
    rows = file_data.split("\n")
    
    allowedemptyfield = 2
    headorfootcount = 0
    count = 0
    successcount = 0
    failedcount = 0
    existscount = 0
    commadetectedcount = 0
    dberrorcount = 0
    successdata = []
    faileddata = []
    fields = []
    increment = 0
    
    for row in rows:
        
        fields = row.split(",")
        increment += 1
        # validation
        transdate = fields[0] if fields[0] != '' else ''
        checkno = fields[1] if fields[1] != '' else ''
        sbareferenceno = fields[2] if fields[2] != '' else ''
        negotiatingbranch = fields[3] if fields[3] != '' else ''
        transactioncode = fields[4] if fields[4] != '' else ''
        transactiondescription = fields[5] if fields[5] != '' else ''
        withdrawals = fields[6] if fields[6] != '' else '0.00'
        deposits = fields[7] if fields[7] != '' else '0.00'
        runningbalance = fields[8] if fields[8] != '' else '0.00'

        if fields.count('') <= allowedemptyfield:
            
            if len(fields) == columnlength:
                # Hash: transdate,particulars,debit,credit,balance
                unique_description = str(transactiondescription) + '-seprtr-' + str(increment)
                generatedkey = generate_hash_key(transdate,unique_description,withdrawals,deposits,runningbalance)

                if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                    faileddata.append([transdate, negotiatingbranch, transactiondescription, withdrawals, deposits, dataexists, bgblue])
                    failedcount += 1
                    existscount += 1
                else:
                    try:
                        date = datetime.datetime.strptime(str(transdate), '%m/%d/%Y').strftime('%Y-%m-%d')
                        Bankrecon.objects.create(
                            bank_id=request.POST['bank_id'],
                            bankaccount_id=request.POST['bank_account'],
                            generatedkey=generatedkey,
                            transaction_date=date,
                            particulars=str(transactiondescription),
                            branch=str(negotiatingbranch),
                            debit_amount=withdrawals,
                            credit_amount=deposits,
                            balance_amount=runningbalance,
                            checknumber=str(checkno),
                            transactioncode=str(transactioncode),
                            refno=str(sbareferenceno)
                        )
                        successdata.append([transdate, negotiatingbranch, transactiondescription, withdrawals, deposits])
                        successcount += 1
                    except:
                        if withdrawals.replace(' ', '').isalpha() or deposits.replace(' ', '').isalpha() or runningbalance.replace(' ', '').isalpha():
                            faileddata.append([transdate, negotiatingbranch, transactiondescription, '', '', catchheader, bggrey])
                            headorfootcount += 1
                        elif not is_date(transdate):
                            faileddata.append([transdate, negotiatingbranch, transactiondescription, '', '', catchheaderorfooter, bggrey])
                            headorfootcount += 1
                        else:
                            faileddata.append([transdate, negotiatingbranch, transactiondescription, withdrawals, deposits, errorunabletoimport, bgorange])
                            failedcount += 1
                            dberrorcount += 1
            else: 
                faileddata.append([transdate, negotiatingbranch, transactiondescription, withdrawals, deposits, errorcommaorcolumnexceeded + str(columnlength), bgyellow])
                failedcount += 1
                commadetectedcount += 1
        else:
            faileddata.append([transdate, negotiatingbranch, transactiondescription, '', '', catchheaderorfooter, bggrey])
            headorfootcount += 1
    
    count = successcount + failedcount
    bodycount = len(rows) - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result)


@csrf_exempt
def ajaxbankaccount(request):
    if request.is_ajax and request.method == "GET":
        bank_id = request.GET['bank_id']
        try:
            bankaccount = Bankaccount.objects.filter(bank_id=bank_id).values('id', 'code', 'accountnumber').order_by('-pk')
            return JsonResponse({
                'bankaccount': list(bankaccount)
            })
        except Exception as e:
            return JsonResponse({
                'errstatus': 1,
                'error': str(e)
            })
    else:
        return JsonResponse({
            'errstatus': 1,
            'error': 'Method not allowed'
        })


@csrf_exempt
def ajaxbankinfo(request):
    if request.is_ajax and request.method == "GET":
        bank_account = request.GET['bank_account']
        try:
            bankinfo = Bankaccount.objects.filter(id=bank_account).values('id', 'code', 'accountnumber', 'bankbranch', 'bankaccounttype', 'currency')
            bankbranch = Bankbranch.objects.filter(id=bankinfo[0]['bankbranch']).values('description')
            bankaccounttype = Bankaccounttype.objects.filter(id=bankinfo[0]['bankaccounttype']).values('description')
            currency = Currency.objects.filter(id=bankinfo[0]['currency']).values('description')
            return JsonResponse({
                'bankinfo': list(bankinfo),
                'bankbranch': list(bankbranch),
                'bankaccounttype': list(bankaccounttype),
                'currency': list(currency)
            })
        except Exception as e:
            return JsonResponse({
                'errstatus': 1,
                'error': str(e)
            })
    else:
        return JsonResponse({
            'errstatus': 1,
            'error': 'Method not allowed'
        })


def importguide(request):
    context = {}
    return render(request, 'bankrecon/import_guide.html', context)


def transgenerate(request):
    dfrom = request.GET["dfrom"]
    dto = request.GET["dto"]
    document_type = request.GET["document_type"]
    bankaccount_id = request.GET["bankaccount"]
    autoadd = request.GET["autoadd"]

    cashinbank_id = Companyparameter.objects.filter(code='PDI').values('coa_cashinbank_id')
    pdi_data = Subledger.objects.filter(\
        bankaccount_id=bankaccount_id, \
        chartofaccount_id=cashinbank_id, \
        document_date__range=[dfrom, dto]\
    ).values('id', 'document_type', 'document_num', 'document_date', 'balancecode', 'amount', 'fxrate', 'fxamount', 'particulars').order_by('document_date')

    if document_type != '':
        pdi_data = pdi_data.filter(document_type=document_type)

    bank_data = Bankrecon.objects.filter(\
        bankaccount_id=bankaccount_id, \
        transaction_date__range=[dfrom, dto]\
    ).values('id', 'tag_id', 'transaction_date', 'debit_amount', 'credit_amount', 'particulars').order_by('transaction_date')

    bankdebit_total = 0
    bankcredit_total = 0
    pdidebit_total = 0
    pdicredit_total = 0
    sorted_dailysum = []
    daily_documentdate = []
    # 5-bd5
    foreign_currencyaccounts = ['5']
    is_currency_peso = 1
    
    for i, pdi in enumerate(pdi_data):
        if pdi['balancecode'] == 'D':
            if bankaccount_id in foreign_currencyaccounts:
                pdidebit_total = pdidebit_total + pdi['fxamount']
            else:
                pdidebit_total = pdidebit_total + pdi['amount']
        elif pdi['balancecode'] == 'C':
            if bankaccount_id in foreign_currencyaccounts:
                pdicredit_total = pdicredit_total + pdi['fxamount']
            else:
                pdicredit_total = pdicredit_total + pdi['amount']

        if bank_data.filter(tag_id=pdi['id']).exists():
            pdi_data[i]['id'] = str(pdi['id']) + ' matched'

    if bankaccount_id in foreign_currencyaccounts:
        is_currency_peso = 0
        for b, bank in enumerate(bank_data):
            
            bankdebit_total = bankdebit_total + bank['debit_amount']
            bankcredit_total = bankcredit_total + bank['credit_amount']

            for p, pdi in enumerate(pdi_data):
                if ((bank['debit_amount'] != Decimal(0.00) and bank['debit_amount'] == pdi['fxamount'])\
                    or (bank['credit_amount'] != Decimal(0.00) and bank['credit_amount'] == pdi['fxamount'])) \
                    and (bank['tag_id'] is None):
                    if re.search('[a-zA-Z]', str(pdi['id'])):
                        pdi['id'] = str(pdi['id']).split(' ')[0]
                        
                    bank_data[b]['tag_id'] = pdi['id']
                    pdi_data[p]['id'] = str(pdi['id']) + ' matched'
                    break
    elif document_type == 'OR' and autoadd == 'true':
        dates = list(set([docdate['document_date'] for docdate in pdi_data]))
        for date in dates:
            sorted_dailysum.append(sum_daily_amount(date, pdi_data))
        
        for b, bank in enumerate(bank_data):
            bankdebit_total = bankdebit_total + bank['debit_amount']
            bankcredit_total = bankcredit_total + bank['credit_amount']
            for p, pdi in enumerate(pdi_data):
                
                if (bank['debit_amount'] == pdi['amount'] or bank['credit_amount'] == pdi['amount']) \
                    and (bank['tag_id'] is None):
                    if re.search('[a-zA-Z]', str(pdi['id'])):
                        pdi['id'] = str(pdi['id']).split(' ')[0]
                        
                    bank_data[b]['tag_id'] = pdi['id']
                    pdi_data[p]['id'] = str(pdi['id']) + ' matched'
                    break
                elif bank['credit_amount'] != Decimal('0.00'):
                    if any([bank['credit_amount'], pdi_data[p]['document_date']] == dailysum for dailysum in sorted_dailysum) \
                        and bank_data[b]['tag_id'] is None:
                        bank_data[b]['tag_id'] = 'Total daily sum of ' + str(pdi['document_date'])
                        daily_documentdate.append(str(pdi['document_date']))
                        break
                elif bank['debit_amount'] != Decimal('0.00'):
                    if any([bank['debit_amount'], pdi_data[p]['document_date']] == dailysum for dailysum in sorted_dailysum) \
                        and bank_data[b]['tag_id'] is None:
                        bank_data[b]['tag_id'] = 'Total daily sum of ' + str(pdi['document_date'])
                        daily_documentdate.append(str(pdi['document_date']))
                        break
    else:
        for b, bank in enumerate(bank_data):
            
            bankdebit_total = bankdebit_total + bank['debit_amount']
            bankcredit_total = bankcredit_total + bank['credit_amount']

            for p, pdi in enumerate(pdi_data):
                if (bank['debit_amount'] == pdi['amount'] or bank['credit_amount'] == pdi['amount']) \
                    and (bank['tag_id'] is None):
                    if re.search('[a-zA-Z]', str(pdi['id'])):
                        pdi['id'] = str(pdi['id']).split(' ')[0]
                        
                    bank_data[b]['tag_id'] = pdi['id']
                    pdi_data[p]['id'] = str(pdi['id']) + ' matched'
                    break
                  
    viewhtml = ''
    context = {}
    record = {
        'pdi_data_len': len(pdi_data),
        'bank_data_len': len(bank_data),
        'bankdebit_total': bankdebit_total,
        'bankcredit_total': bankcredit_total,
        'pdidebit_total': pdidebit_total,
        'pdicredit_total': pdicredit_total,
        'daily_documentdate': daily_documentdate,
        'is_currency_peso': is_currency_peso
    }

    context['transdfrom'] = dfrom
    context['transdto'] = dto
    context['record'] = record
    context['pdi_data'] = pdi_data
    context['bank_data'] = bank_data
    viewhtml = render_to_string('bankrecon/transaction_result.html', context)

    data = {
        'status': 'success',
        'viewhtml': viewhtml
    }
    return JsonResponse(data)


def sum_daily_amount(date, pdi_data):
    a = 0.00
    for each in pdi_data:
        if date == each['document_date'] and str(each['id']).isdigit():
            a += float(each['amount'])
    return [a,date]


@csrf_exempt
def tagging(request):
    if request.method == 'POST':
        try:
            Bankrecon.objects.filter(id=request.POST['bank_id']).update(tag_id=request.POST['tag_id'], modifyby_id=request.user.id, modifydate=datetime.datetime.now())
            data = {'result': True}
        except:
            data = {'result': False}
    else:
        data = {'result': False}

    return JsonResponse(data)


@csrf_exempt
def fxsave(request):
    if request.method == 'POST':
        try:
            fxamount = str(request.POST['fx_amount']).replace(',', '')
            Subledger.objects.filter(id=request.POST['tag_id']).update(
                fxrate=float(request.POST['fx_rate']),
                fxamount=float(fxamount),
                modifyby_id=request.user.id, 
                modifydate=datetime.datetime.now()
            )
            data = {'result': True}
        except:
            data = {'result': False}
    else:
        data = {'result': False}
        
    return JsonResponse(data)


@csrf_exempt
def reportxls(request):
    if request.method == 'POST':
        try:
            bank_account = request.POST['report_bank_account']
            date_from = request.POST['report_date_from']
            date_to = request.POST['report_date_to']
            currency_details = json.loads(request.POST.getlist('report_currency_details')[0])
            book_data = json.loads(request.POST.getlist('report_book_data')[0])
            bank_data = json.loads(request.POST.getlist('report_bank_data')[0])

            bookdebit_total = request.POST['report_bookdebit_total']
            bookcredit_total = request.POST['report_bookcredit_total']
            bankdebit_total = request.POST['report_bankdebit_total']
            bankcredit_total = request.POST['report_bankcredit_total']

            title = bank_account + " from " + date_from + " to " + date_to
            response = HttpResponse(content_type='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename="' + title + '.xls"'

            wb = xlwt.Workbook(encoding='utf-8')
            ws = wb.add_sheet('Book')

            row_num = 0
            font_style = xlwt.XFStyle()
            font_style.font.bold=True
            horiz_right = xlwt.easyxf('align: horiz right')
            
            if currency_details:
                if currency_details['name'] == 'USD':
                    bookcolumns = ['', 'Date', 'Tag ID', 'Document Type', 'Document Number', 'Particulars', 'Debit (USD)', 'Credit (USD)', 'Debit (PHP)', 'Credit (PHP)']
            else:
                bookcolumns = ['', 'Date', 'Tag ID', 'Document Type', 'Document Number', 'Particulars', 'Debit', 'Credit']

            for col_num in range(len(bookcolumns)):
                ws.write(row_num, col_num, bookcolumns[col_num], font_style)

            font_style = xlwt.XFStyle()

            if currency_details:
                if currency_details['name'] == 'USD':
                    for row in list(book_data):
                        row_num +=1
                        ws.write(row_num, 0, row_num, font_style)
                        ws.write(row_num, 1, row['date'], font_style)
                        ws.write(row_num, 2, row['tag_id'], font_style)
                        ws.write(row_num, 3, row['doc_type'], font_style)
                        ws.write(row_num, 4, row['doc_num'], font_style)
                        ws.write(row_num, 5, row['particulars'], font_style)
                        ws.write(row_num, 6, row['debit_dollar'], horiz_right)
                        ws.write(row_num, 7, row['credit_dollar'], horiz_right)
                        ws.write(row_num, 8, row['debit_php'], horiz_right)
                        ws.write(row_num, 9, row['credit_php'], horiz_right)
            else:
                for row in list(book_data):
                    row_num +=1
                    ws.write(row_num, 0, row_num, font_style)
                    ws.write(row_num, 1, row['date'], font_style)
                    ws.write(row_num, 2, row['tag_id'], font_style)
                    ws.write(row_num, 3, row['doc_type'], font_style)
                    ws.write(row_num, 4, row['doc_num'], font_style)
                    ws.write(row_num, 5, row['particulars'], font_style)
                    ws.write(row_num, 6, row['debit'], horiz_right)
                    ws.write(row_num, 7, row['credit'], horiz_right)

            row_num +=2
            ws.write(row_num, 5, "Total:", font_style)
            ws.write(row_num, 6, bookdebit_total, horiz_right)
            ws.write(row_num, 7, bookcredit_total, horiz_right)

            ws = wb.add_sheet('Bank')

            row_num = 0
            font_style = xlwt.XFStyle()
            font_style.font.bold=True

            bankcolumns = ['', 'Date', 'Tag ID', 'Particulars', 'Debit', 'Credit']

            for col_num in range(len(bankcolumns)):
                ws.write(row_num, col_num, bankcolumns[col_num], font_style)

            font_style = xlwt.XFStyle()

            for row in list(bank_data):
                row_num +=1
                ws.write(row_num, 0, row_num, font_style)
                ws.write(row_num, 1, row['date'], font_style)
                ws.write(row_num, 2, row['tag_id'], font_style)
                ws.write(row_num, 3, row['particulars'], font_style)
                ws.write(row_num, 4, row['debit'], horiz_right)
                ws.write(row_num, 5, row['credit'], horiz_right)

            row_num +=2
            ws.write(row_num, 3, "Total:", font_style)
            ws.write(row_num, 4, bankdebit_total, horiz_right)
            ws.write(row_num, 5, bankcredit_total, horiz_right)
            
            wb.save(response)
            return response
        except:
            raise Http404


@method_decorator(login_required, name='dispatch')
class ManualEntryView(CreateView):
    model = Bankrecon
    template_name = 'bankrecon/manual_upload.html'
    fields = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankrecon.upload_bankstatements'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
       context = super(ManualEntryView, self).get_context_data(**kwargs)
       context['bankaccount'] = Bankaccount.objects.all().filter(isdeleted=0).order_by('code')
       context['banks'] = Bank.objects.all().order_by('description')
       
       return context

@csrf_exempt
def savemanualentry(request):
    form_data = json.loads(request.POST.getlist('form_data')[0])
    basic_info = form_data[0]['basic_info']
    entries = form_data[1]['entries']
    
    successdata = []
    successcount = 0
    faileddata = []
    failedcount = 0

    for entry in list(entries):
        try:
            
            Bankrecon.objects.create(
                bank_id=basic_info['bank_id'],
                bankaccount_id=basic_info['bank_account'],
                transaction_date=basic_info['dto'],
                particulars=str(entry['particulars']),
                debit_amount=Decimal(entry['debit']),
                credit_amount=Decimal(entry['credit'])
            )
            successdata.append([basic_info['dto'], entry['particulars'], entry['debit'], entry['credit']])
            successcount += 1
        except:
            faileddata.append([basic_info['dto'], entry['particulars'], entry['debit'], entry['credit']])
            failedcount += 1

    return JsonResponse({
        'successdata': successdata,
        'successcount': successcount,
        'faileddata': faileddata,
        'failedcount': failedcount,
        'datacount': successcount + failedcount
    })

