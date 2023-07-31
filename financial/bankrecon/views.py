''' Bankrecon Utility '''
import datetime
import hashlib
import itertools
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render
from bank.models import Bank
from bankrecon.models import Bankrecon
# from bankrecon.importexcel import RobinsonSavingsBank, RobinsonSavingsBankDBF, UnionBank, UnionBankDBF
from bankaccount.models import Bankaccount
from bankbranch.models import Bankbranch
from bankaccounttype.models import Bankaccounttype
from subledger.models import Subledger
from currency.models import Currency
from endless_pagination.views import AjaxListView
from django.db.models import Q, Sum
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
        
        try:
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
                        # 15-rs1
                    elif request.POST['bank_account'] in ['15']:
                        return RobinsonSavingsBank(request, columnlength=13)
                        # 19-sb7, 22-sb9
                    elif request.POST['bank_account'] in ['19', '22']:
                        return SecurityBank(request, columnlength=6)
                        # 23-ub2
                    elif request.POST['bank_account'] in ['23']:
                        return UnionBank(request, columnlength=13)
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
            # elif request.FILES['data_file'] and (request.FILES['data_file'].name.endswith('.dbf')):
            #         if request.FILES['data_file']._size < float(upload_size) * 1024 * 1024:

            #             if request.POST['bank_account'] in ['15']:
            #                 # 15-rs1
            #                 return RobinsonSavingsBankDBF(request)
            #             elif request.POST['bank_account'] in ['23']:
            #                 # 23-ubs
            #                 return UnionBankDBF(request)

            #         else:
            #             return JsonResponse({
            #                 'result': 4
            #             })
            else:
                return JsonResponse({
                    'result': 5
                })
        except Exception as e:
            print("An error occurred while uploading the CSV file:", str(e))
            return JsonResponse({
                'result': 9
            })
    else:
        context = {
            "today": timezone.now(),
            "banks": Bank.objects.all().order_by('description'),
            "bankaccount": Bankaccount.objects.all().filter(isdeleted=0).order_by('code'),
            "username": request.user,
        }
        return render(request, 'bankrecon/upload.html', context)
    

@csrf_exempt
def delete_upload(request):
    if request.method == 'POST':
        ids_list = request.POST.getlist('list_ids')[0].split(',')
        existing_ids = Bankrecon.objects.filter(pk__in=ids_list).values_list('id', flat=True)

        if len(ids_list) == len(existing_ids):
            # All ids exist as primary keys, proceed with the delete operation
            Bankrecon.objects.filter(pk__in=ids_list).delete()
            message = "Delete operation performed successfully. Click OK to reload."
            result = True
        else:
            message = "Cannot perform delete operation. One or more IDs do not exist."
            result = False

        return JsonResponse({
            'result': result,
            'message': message
        })
    

def generate_hash_key(transdate,particulars,debit,credit,balance):
    hash = hashlib.md5(str(transdate) + str(particulars) + str(debit) + str(credit) + str(balance))
    return hash.hexdigest()


def json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result,list_ids):
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
        'list_ids': list_ids
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
    elif existscount == (bodycount - 1):
        # if csv is edited  using ms excel do minus 1 for extra row
        result = 2
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
    list_ids = []
    increment = 0

    for row in rows:
        
        fields = row.split(",")

        if len(fields) < 2:
            continue

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

                        new_object = Bankrecon.objects.create(
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

                        list_ids.append([new_object.id])
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

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result,list_ids)


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
    list_ids = []
    increment = 0

    for row in rows:

        fields = row.split(",")

        if len(fields) < 2:
            continue

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

                        new_object = Bankrecon.objects.create(
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

                        list_ids.append([new_object.id])
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

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result,list_ids)


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
    list_ids = []
    increment = 0
    
    for row in rows:
        
        fields = row.split(",")

        if len(fields) < 2:
            continue

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
                        
                        new_object = Bankrecon.objects.create(
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

                        list_ids.append([new_object.id])
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

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result,list_ids)


def RobinsonSavingsBank(request, columnlength):
    csv_file = request.FILES["data_file"]
    file_data = csv_file.read().decode("utf-8")
    rows = file_data.split("\n")
    
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
    fields = []
    list_ids = []
    increment = 0
    creditamount = '0.00'
    debitamount = '0.00'

    for row in rows:
        
        fields = row.split(",")

        if len(fields) < 2:
            continue

        increment += 1
        # validation
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
            
            if len(fields) == columnlength:
                # Hash: transdate,particulars,debit,credit,balance
                unique_description = str(transactionnarration) + '-seprtr-' + str(increment)
                generatedkey = generate_hash_key(postingdate,unique_description,debitamount,creditamount,balance)

                if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                    faileddata.append([postingdate, "", transactionnarration, debitamount, creditamount, dataexists, bgblue])
                    failedcount += 1
                    existscount += 1
                else:
                    try:
                        postingdate = datetime.datetime.strptime(str(postingdate), '%d/%m/%Y').strftime('%Y-%m-%d')
                        new_object = Bankrecon.objects.create(
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

                        list_ids.append([new_object.id])
                        successdata.append([postingdate, "", transactionnarration, debitamount, creditamount])
                        successcount += 1
                    except:
                        if debitamount.replace(' ', '').isalpha() or creditamount.replace(' ', '').isalpha() or balance.replace(' ', '').isalpha():
                            faileddata.append([postingdate, "", transactionnarration, '', '', catchheader, bggrey])
                            headorfootcount += 1
                        elif not is_date(postingdate):
                            faileddata.append([postingdate, "", transactionnarration, '', '', catchheaderorfooter, bggrey])
                            headorfootcount += 1
                        else:
                            # can be special characters detected. - enye
                            faileddata.append([postingdate, "", transactionnarration, debitamount, creditamount, errorunabletoimport, bgorange])
                            failedcount += 1
                            dberrorcount += 1
            else: 
                faileddata.append([postingdate, "", transactionnarration, debitamount, creditamount, errorcommaorcolumnexceeded + str(columnlength), bgyellow])
                failedcount += 1
                commadetectedcount += 1
        else:
            faileddata.append([postingdate, "", transactionnarration, '', '', catchheaderorfooter, bggrey])
            headorfootcount += 1
    
    count = successcount + failedcount
    bodycount = len(rows) - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result,list_ids)


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
    list_ids = []
    increment = 0
    
    for row in rows:
        
        fields = row.split(",")
        
        if len(fields) < 2:
            continue

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
                        new_object = Bankrecon.objects.create(
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

                        list_ids.append([new_object.id])
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

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result,list_ids)


def UnionBank(request, columnlength):
    csv_file = request.FILES["data_file"]
    file_data = csv_file.read().decode("utf-8")
    rows = file_data.split("\n")
    
    allowedemptyfield = 32
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
    list_ids = []
    increment = 0

    for row in rows:
        
        fields = row.split(",")

        if len(fields) < 2:
            continue

        increment += 1
        # validation
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
            unique_description = str(transactiondescription) + '-seprtr-' + str(increment)
            generatedkey = generate_hash_key(transactiondescription,unique_description,debit,credit,endingbalance)

            if Bankrecon.objects.filter(generatedkey=generatedkey, bankaccount_id=request.POST['bank_account'], bank_id=request.POST['bank_id']).exists():
                faileddata.append([transactiondate, branch, transactiondescription, debit, credit, dataexists, bgblue])
                failedcount += 1
                existscount += 1
            else:
                try:
                    transactiondate = transactiondate.split('T')[0]
                    transactiondate = datetime.datetime.strptime(str(transactiondate), '%Y-%m-%d').strftime('%Y-%m-%d')

                    pdate = posteddate.split('T')[0]
                    pdate = datetime.datetime.strptime(str(pdate), '%Y-%m-%d').strftime('%Y-%m-%d')
                    new_object = Bankrecon.objects.create(
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

                    list_ids.append([new_object.id])
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
    bodycount = len(rows) - headorfootcount
    result = get_result(successcount, existscount, bodycount, dberrorcount, commadetectedcount)

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result,list_ids)


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
    list_ids = []
    increment = 0
    
    for row in rows:
        
        fields = row.split(",")

        if len(fields) < 2:
            continue

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
                        new_object = Bankrecon.objects.create(
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

                        list_ids.append([new_object.id])
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

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result,list_ids)


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
    list_ids = []
    increment = 0
    
    for row in rows:
        
        fields = row.split(",")

        if len(fields) < 2:
            continue

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
                        new_object = Bankrecon.objects.create(
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

                        list_ids.append([new_object.id])
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

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result,list_ids)


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
    list_ids = []
    increment = 0
    
    for row in rows:
        
        fields = row.split(",")

        if len(fields) < 2:
            continue

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
                        new_object = Bankrecon.objects.create(
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

                        list_ids.append([new_object.id])
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

    return json_response(successcount,failedcount,faileddata,successdata,count,existscount,dberrorcount,commadetectedcount,headorfootcount,result,list_ids)


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
    
    cashinbank_id = Companyparameter.objects.filter(code='PDI').values('coa_cashinbank_id')
    pdi_data = Subledger.objects.filter(\
        bankaccount_id=bankaccount_id, \
        chartofaccount_id=cashinbank_id, \
        document_date__range=[dfrom, dto]\
    ).values('id', 'reference_number', 'document_type', 'document_num', 'document_date', 'document_payee', 'balancecode', 'amount', 'fxrate', 'fxamount', 'document_checknum', 'document_branch_id', 'particulars').order_by('document_date')

    if document_type != '':
        pdi_data = pdi_data.filter(document_type=document_type)

    bank_data = Bankrecon.objects.filter(\
        bankaccount_id=bankaccount_id, \
        transaction_date__range=[dfrom, dto]\
    ).values('id', 'reference_number', 'transaction_date', 'debit_amount', 'credit_amount', 'branch', 'checknumber', 'particulars', 'transactioncode').order_by('transaction_date')

    bankdebit_total = 0
    bankcredit_total = 0
    pdidebit_total = 0
    pdicredit_total = 0
    sorted_book_dailysum = []
    sorted_bank_dailysum = []
    sorted_pdi_data = []
    sorted_bank_data = []
    posted_with_subtotal = []
    bank_posted_with_subtotal = []
    # 4-bd4, 5-bd5
    foreign_currencyaccounts = ['4', '5']
    is_currency_peso = 1
    
    if bankaccount_id in foreign_currencyaccounts:
        is_currency_peso = 0

        bank_reconciled = []
        bank_unreconciled = []

        for bank in bank_data:
            bankdebit_total += bank['debit_amount']
            bankcredit_total += bank['credit_amount']

            if bank['reference_number']:
                bank_reconciled.append(bank)
            else:
                bank_unreconciled.append(bank)

        # Sort transactions with refno to move at the last of records
        sorted_bank_data = bank_unreconciled + bank_reconciled

        pdi_reconciled = []
        pdi_unreconciled = []

        for pdi in pdi_data:
            if pdi['balancecode'] == 'D':
                pdidebit_total += pdi['fxamount']
            elif pdi['balancecode'] == 'C':
                pdicredit_total += pdi['fxamount']

            if pdi['reference_number']:
                pdi_reconciled.append(pdi)
            else:
                pdi_unreconciled.append(pdi)
        
        # Sort transactions with refno to move at the last of records
        sorted_pdi_data = pdi_unreconciled + pdi_reconciled
    else:
        dates = list(set([docdate['document_date'] for docdate in pdi_data]))
        for date in dates:
            sorted_book_dailysum.append(sum_daily_amount(date, pdi_data))

        bank_dates = list(set([transdate['transaction_date'] for transdate in bank_data]))
        for bank_date in bank_dates:
            sorted_bank_dailysum.append(bank_sum_daily_amount(bank_date, bank_data))
        
        # AP, CV, JV, OR
        if document_type != '':

            # process book daily sum, total, and separate data with refno
            book_iterator = 0
            with_refno = []
            for data in pdi_data:

                # totals
                if data['balancecode'] == 'D':
                    pdidebit_total += data['amount']
                elif data['balancecode'] == 'C':
                    pdicredit_total += data['amount']

                # sorting
                if data['reference_number']:
                    # separate data with refno
                    with_refno.append(data)
                    # pdi_data = pdi_data.exclude(pk=data['id'])

                else:
                    # process book daily sum
                    book_iterator += 1
                    sorted_pdi_data.append(data)
                    for dailysum in sorted_book_dailysum:
                        if data['document_date'] == dailysum['date'] and dailysum['count'] == book_iterator:
                            sorted_pdi_data.append({
                                'balancecode': 'subtotal',
                                'count': dailysum['count'],
                                'date': dailysum['date'],
                                'type': data['document_type'],
                                'debit_amount': dailysum['debit_amount'],
                                'credit_amount': dailysum['credit_amount']
                            })
                            book_iterator = 0

            # book process refno
            # sorted_pdi_data = pdi_data
            with_refno = sorted(with_refno)
            with_refno.sort(key=takeRefNo)
            
            iterator = 0
            increment = 0
            length = len(with_refno)
            advance_check = 0
            posted_debit = 0
            posted_credit = 0
            for i,data in enumerate(with_refno):
                iterator += 1
                increment += 1
                
                if data['balancecode'] == 'D':
                    posted_debit += data['amount']
                elif data['balancecode'] == 'C':
                    posted_credit += data['amount']

                advance_check = i + 1
                if increment != length and data['reference_number'] == with_refno[advance_check]['reference_number']:
                    posted_with_subtotal.append(data)
                else:
                    posted_with_subtotal.append(data)
                    posted_with_subtotal.append({
                        'balancecode': 'subtotal',
                        'count': iterator,
                        'debit_amount': posted_debit,
                        'credit_amount': posted_credit
                    })

                    # compute the total sum then re-initiate
                    posted_debit = 0
                    posted_credit = 0
                    iterator = 0
                
            # process bank daily sum, total, and exclude with refno
            bank_iterator = 0
            bank_with_refno = []
            for b in bank_data:
                # totals
                bankdebit_total += b['debit_amount']
                bankcredit_total += b['credit_amount']

                # sorting
                if b['reference_number']:
                    bank_with_refno.append(b)
                    
                else:
                    # process bank daily sum
                    bank_iterator += 1
                    sorted_bank_data.append(b)
                    for bank_dailysum in sorted_bank_dailysum:
                        if b['transaction_date'] == bank_dailysum['date'] and bank_dailysum['count'] == bank_iterator:
                            sorted_bank_data.append({
                                'transactioncode': 'subtotal',
                                'count': bank_dailysum['count'],
                                'date': bank_dailysum['date'],
                                'debit_amount': bank_dailysum['debit_amount'],
                                'credit_amount': bank_dailysum['credit_amount']
                            })
                            bank_iterator = 0
            # bank process refno  
            # sorted_bank_data = bank_data
            bank_with_refno = sorted(bank_with_refno)
            bank_with_refno.sort(key=takeRefNo)

            iterator = 0
            increment = 0
            length = len(bank_with_refno)
            advance_check = 0
            posted_debit = 0
            posted_credit = 0
            for i,bank_refno in enumerate(bank_with_refno):
                iterator += 1
                increment += 1

                posted_debit += bank_refno['debit_amount']
                posted_credit += bank_refno['credit_amount']

                advance_check = i + 1
                if increment != length and bank_refno['reference_number'] == bank_with_refno[advance_check]['reference_number']:
                    bank_posted_with_subtotal.append(bank_refno)
                else:
                    bank_posted_with_subtotal.append(bank_refno)
                    bank_posted_with_subtotal.append({
                        'transactioncode': 'subtotal',
                        'count': iterator,
                        'debit_amount': posted_debit,
                        'credit_amount': posted_credit
                    })

                    # compute the total sum then re-initiate
                    posted_debit = 0
                    posted_credit = 0
                    iterator = 0

        else:
            # all doc type

            # process book daily sum, total, and exclude with refno
            book_iterator = 0
            with_refno = []
            for data in pdi_data:

                # totals
                if data['balancecode'] == 'D':
                    pdidebit_total += data['amount']
                elif data['balancecode'] == 'C':
                    pdicredit_total += data['amount']

                # sorting
                if data['reference_number']:
                    # exclude with refno
                    with_refno.append(data)
                    # pdi_data = pdi_data.exclude(pk=data['id'])
                else:
                    sorted_pdi_data.append(data)

            # book process refno
            # sorted_pdi_data = pdi_data
            with_refno = sorted(with_refno)
            with_refno.sort(key=takeRefNo)
            
            iterator = 0
            increment = 0
            length = len(with_refno)
            advance_check = 0
            posted_debit = 0
            posted_credit = 0
            for i,data in enumerate(with_refno):
                iterator += 1
                increment += 1
                
                if data['balancecode'] == 'D':
                    posted_debit += data['amount']
                elif data['balancecode'] == 'C':
                    posted_credit += data['amount']

                advance_check = i + 1
                if increment != length and data['reference_number'] == with_refno[advance_check]['reference_number']:
                    posted_with_subtotal.append(data)
                else:
                    posted_with_subtotal.append(data)
                    posted_with_subtotal.append({
                        'balancecode': 'subtotal',
                        'count': iterator,
                        'debit_amount': posted_debit,
                        'credit_amount': posted_credit
                    })

                    # compute the total sum then re-initiate
                    posted_debit = 0
                    posted_credit = 0
                    iterator = 0

            # process bank daily sum, total, and exclude with refno
            bank_iterator = 0
            bank_with_refno = []
            for b in bank_data:
                # totals
                bankdebit_total += b['debit_amount']
                bankcredit_total += b['credit_amount']

                # sorting
                if b['reference_number']:
                    bank_with_refno.append(b)
                    # bank_data = bank_data.exclude(pk=b['id'])
            
                else:
                    sorted_bank_data.append(b)

            # bank process refno  
            bank_with_refno = sorted(bank_with_refno)
            bank_with_refno.sort(key=takeRefNo)

            iterator = 0
            increment = 0
            length = len(bank_with_refno)
            advance_check = 0
            posted_debit = 0
            posted_credit = 0
            for i,bank_refno in enumerate(bank_with_refno):
                iterator += 1
                increment += 1

                posted_debit += bank_refno['debit_amount']
                posted_credit += bank_refno['credit_amount']

                advance_check = i + 1
                if increment != length and bank_refno['reference_number'] == bank_with_refno[advance_check]['reference_number']:
                    bank_posted_with_subtotal.append(bank_refno)
                else:
                    bank_posted_with_subtotal.append(bank_refno)
                    bank_posted_with_subtotal.append({
                        'transactioncode': 'subtotal',
                        'count': iterator,
                        'debit_amount': posted_debit,
                        'credit_amount': posted_credit
                    })

                    # compute the total sum then re-initiate
                    posted_debit = 0
                    posted_credit = 0
                    iterator = 0
                  
    viewhtml = ''
    context = {}
    record = {
        'pdi_data_len': len(pdi_data),
        'bank_data_len': len(bank_data),
        'bankdebit_total': bankdebit_total,
        'bankcredit_total': bankcredit_total,
        'pdidebit_total': pdidebit_total,
        'pdicredit_total': pdicredit_total,
        'is_currency_peso': is_currency_peso
    }
    
    context['transdfrom'] = dfrom
    context['transdto'] = dto
    context['record'] = record
    context['pdi_data'] = sorted_pdi_data
    context['bank_data'] = sorted_bank_data
    context['posted_with_subtotal'] = posted_with_subtotal
    context['bank_posted_with_subtotal'] = bank_posted_with_subtotal
    context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
    viewhtml = render_to_string('bankrecon/transaction_result.html', context)
    
    data = {
        'status': 'success',
        'viewhtml': viewhtml
    }
    return JsonResponse(data)


# take second element for sort
def takeRefNo(elem):
    return elem['reference_number']

def sum_daily_amount(date, pdi_data):
    debit_amount = 0.00
    credit_amount = 0.00
    i = 0
    for each in pdi_data:
        if date == each['document_date'] and str(each['id']).isdigit():
            i += 1
            if each['balancecode'] == 'D':
                debit_amount += float(each['amount'])
            elif each['balancecode'] == 'C':
                credit_amount += float(each['amount'])

    return {
        'count': i, 
        'debit_amount': debit_amount,
        'credit_amount': credit_amount,
        'date': date
    }

def bank_sum_daily_amount(date, bank_data):
    debit_amount = 0.00
    credit_amount = 0.00
    i = 0
    for each in bank_data:
        if date == each['transaction_date'] and str(each['id']).isdigit():
            i += 1
            debit_amount += float(each['debit_amount'])
            credit_amount += float(each['credit_amount'])

    return {
        'count': i, 
        'debit_amount': debit_amount,
        'credit_amount': credit_amount,
        'date': date
    }


# @csrf_exempt
# def tagging(request):
#     if request.method == 'POST':
#         try:
#             Bankrecon.objects.filter(id=request.POST['bank_id']).update(tag_id=request.POST['tag_id'], modifyby_id=request.user.id, modifydate=datetime.datetime.now())
#             data = {'result': True}
#         except:
#             data = {'result': False}
#     else:
#         data = {'result': False}

#     return JsonResponse(data)


@csrf_exempt
def fxsave(request):
    if request.method == 'POST':
        try:
            fxamount = str(request.POST['fx_amount']).replace(',', '')
            Subledger.objects.filter(id=request.POST['book_id']).update(
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
            bank_account = str(request.POST['report_bank_account'])
            date_from = str(request.POST['report_date_from'])
            date_to = str(request.POST['report_date_to'])
            currency_details = json.loads(request.POST.getlist('report_currency_details')[0])
            book_data = json.loads(request.POST.getlist('report_book_data')[0])
            bank_data = json.loads(request.POST.getlist('report_bank_data')[0])

            bookdebit_total = request.POST['report_bookdebit_total']
            bookcredit_total = request.POST['report_bookcredit_total']
            bankdebit_total = request.POST['report_bankdebit_total']
            bankcredit_total = request.POST['report_bankcredit_total']

            title = "Bank Recon for " + bank_account.split('-')[0] + " from " + date_from + " to " + date_to
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
                    bookcolumns = ['', 'Date', 'Doc. Type', 'Doc. No.', 'Particulars', 'Debit (USD)', 'Credit (USD)', 'FX Rate', 'Debit (PHP)', 'Credit (PHP)', 'Check No.', 'Ref. No.']
            else:
                bookcolumns = ['', 'Date', 'Doc. Type', 'Doc. No.', 'Particulars', 'Debit', 'Credit', 'Check No.', 'Ref. No.']

            for col_num in range(len(bookcolumns)):
                ws.write(row_num, col_num, bookcolumns[col_num], font_style)

            font_style = xlwt.XFStyle()

            if currency_details:
                if currency_details['name'] == 'USD':
                    for row in list(book_data):
                        row_num +=1
                        ws.write(row_num, 0, row_num, font_style)
                        ws.write(row_num, 1, row['date'], font_style)
                        ws.write(row_num, 2, row['doc_type'], font_style)
                        ws.write(row_num, 3, row['doc_num'], font_style)
                        ws.write(row_num, 4, row['particulars'], font_style)
                        ws.write(row_num, 5, row['debit_dollar'], horiz_right)
                        ws.write(row_num, 6, row['credit_dollar'], horiz_right)
                        ws.write(row_num, 7, row['fxrate'], horiz_right)
                        ws.write(row_num, 8, row['debit_php'], horiz_right)
                        ws.write(row_num, 9, row['credit_php'], horiz_right)
                        ws.write(row_num, 10, row['check_number'], font_style)
                        ws.write(row_num, 11, row['reference_number'], font_style)
            else:
                for row in list(book_data):
                    row_num +=1
                    ws.write(row_num, 0, row_num, font_style)
                    ws.write(row_num, 1, row['date'], font_style)
                    ws.write(row_num, 2, row['doc_type'], font_style)
                    ws.write(row_num, 3, row['doc_num'], font_style)
                    ws.write(row_num, 4, row['particulars'], font_style)
                    ws.write(row_num, 5, row['debit'], horiz_right)
                    ws.write(row_num, 6, row['credit'], horiz_right)
                    ws.write(row_num, 7, row['check_number'], font_style)
                    ws.write(row_num, 8, row['reference_number'], font_style)

            row_num += 2
            ws.write(row_num, 4, "Total:", font_style)
            ws.write(row_num, 5, bookdebit_total, horiz_right)
            ws.write(row_num, 6, bookcredit_total, horiz_right)

            ws = wb.add_sheet('Bank')

            row_num = 0
            font_style = xlwt.XFStyle()
            font_style.font.bold=True

            bankcolumns = ['', 'Date', 'Doc. Type', 'Doc. No.', 'Particulars', 'Debit', 'Credit', 'Check No.', 'Ref. No.']

            for col_num in range(len(bankcolumns)):
                ws.write(row_num, col_num, bankcolumns[col_num], font_style)

            font_style = xlwt.XFStyle()

            for row in list(bank_data):
                row_num +=1
                ws.write(row_num, 0, row_num, font_style)
                ws.write(row_num, 1, row['date'], font_style)
                ws.write(row_num, 2, row['doc_type'], font_style)
                ws.write(row_num, 3, row['doc_num'], font_style)
                ws.write(row_num, 4, row['particulars'], font_style)
                ws.write(row_num, 5, row['debit'], horiz_right)
                ws.write(row_num, 6, row['credit'], horiz_right)
                ws.write(row_num, 7, row['check_number'], font_style)
                ws.write(row_num, 8, row['reference_number'], font_style)

            row_num +=2
            ws.write(row_num, 4, "Total:", font_style)
            ws.write(row_num, 5, bankdebit_total, horiz_right)
            ws.write(row_num, 6, bankcredit_total, horiz_right)
            
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


@csrf_exempt
def savebatchpostingbook(request):
    form_data = json.loads(request.POST.getlist('data')[0])
    successcount = 0
    failedcount = 0

    for data in form_data:
        
        try:
            trans = Subledger.objects.filter(pk=data['id'])
            if trans[0].reference_number != data['refno']:
                trans.update(reference_number=data['refno'], \
                    modifyby_id=request.user.id, modifydate=datetime.datetime.now())

                successcount += 1
        except:
            failedcount += 1

    return JsonResponse({
        'success_count': successcount,
        'failed_count': failedcount
    })


@csrf_exempt
def savebatchpostingbank(request):
    form_data = json.loads(request.POST.getlist('data')[0])
    successcount = 0
    failedcount = 0

    for data in form_data:
        
        try:
            bank = Bankrecon.objects.filter(id=data['id'])
            if bank[0].reference_number != data['refno']:
                bank.update(reference_number=data['refno'], \
                    modifyby_id=request.user.id, modifydate=datetime.datetime.now())
                successcount += 1
        except:
            failedcount += 1

    return JsonResponse({
        'success_count': successcount,
        'failed_count': failedcount
    })
