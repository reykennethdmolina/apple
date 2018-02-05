from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import Temp_ormain, Temp_ordetail, Logs_ormain, Logs_ordetail
from officialreceipt.models import Ormain, Ordetail
from ortype.models import Ortype
from collector.models import Collector
from branch.models import Branch
from vat.models import Vat
from bankaccount.models import Bankaccount
from chartofaccount.models import Chartofaccount
from customer.models import Customer
from product.models import Product
from agent.models import Agent
from outputvattype.models import Outputvattype
from currency.models import Currency
from adtype.models import Adtype
from companyparameter.models import Companyparameter
from circulationpaytype.models import Circulationpaytype
from productgroupcategory.models import Productgroupcategory
from circulationproduct.models import Circulationproduct
from productgroup.models import Productgroup
from django.db.models import Count, Sum
from datetime import datetime
from datetime import timedelta
from annoying.functions import get_object_or_None
from utils.views import wccount, storeupload
from acctentry.views import generatekey
from dbfread import DBF
from django.utils.crypto import get_random_string
from django.db.models import Q
from django.conf import settings


upload_directory = 'processing_or/imported_main/'
upload_d_directory = 'processing_or/imported_detail/'
upload_size = 3


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'processing_or/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context


@csrf_exempt
def fileupload(request):
    if request.method == 'POST':        

        # data-result definition:
        #   1: success
        #   2: failed - upload error
        #   3: failed - file error
        #   4: failed - file size too large (> 3mb)
        #   5: failed - file array columns does not match requirement
        #   6: failed - invalid artype

        if request.POST['or_artype'] == 'a':    # 6
            if request.FILES['or_file'] \
                    and request.FILES['or_file'].name.endswith('.txt') \
                    and request.FILES['or_d_file'] \
                    and request.FILES['or_d_file'].name.endswith('.txt'):     # 3
                if request.FILES['or_file']._size < float(upload_size)*1024*1024 \
                        and request.FILES['or_d_file']._size < float(upload_size)*1024*1024:

                    sequence = datetime.now().isoformat().replace(':', '-')
                    batchkey = generatekey(1)

                    if storeupload(request.FILES['or_file'], sequence, 'txt', upload_directory)\
                            and storeupload(request.FILES['or_d_file'], sequence, 'txt', upload_d_directory):    # 2
                        orcount = 0

                        with open(settings.MEDIA_ROOT + '/' + upload_directory + str(sequence) + ".txt") as textFile:
                            for line in textFile:
                                orcount += 1
                                data = line.split("\t")
                                for n, i in enumerate(data):
                                    data[n] = data[n].replace('"', '')

                                if len(data) == 38:
                                    # log status filtering
                                    if Logs_ormain.objects.filter(orno=data[0], importstatus='P'):
                                        importstatus = 'F'
                                        importremarks = 'Skipped: Already posted'
                                    elif Logs_ormain.objects.filter(orno=data[0], batchkey=batchkey, importstatus='S'):
                                        importstatus = 'F'
                                        importremarks = 'Skipped: Already exists in this batch'
                                    elif not Bankaccount.objects.filter(code=data[13]):
                                        importstatus = 'F'
                                        importremarks = 'Failed: Bank account does not exist'
                                    elif not Adtype.objects.filter(code=data[6]):
                                        importstatus = 'F'
                                        importremarks = 'Failed: Adtype does not exist'
                                    elif not Vat.objects.filter(code=data[33]):
                                        importstatus = 'F'
                                        importremarks = 'Failed: Vat Type does not exist'
                                    elif not Circulationproduct.objects.filter(code=data[35]):
                                        importstatus = 'F'
                                        importremarks = 'Failed: Circulation Product does not exist'
                                    else:
                                        importstatus = 'S'
                                        importremarks = 'Passed'

                                    if importstatus is not 'F':
                                        # new branch checking
                                        if not Branch.objects.filter(code=data[26]):
                                            Branch.objects.create(code=data[26],
                                                                  description=data[32],
                                                                  enterby=request.user,
                                                                  modifyby=request.user)
                                        # new collector checking
                                        if not Collector.objects.filter(code=data[4]):
                                            Collector.objects.create(code=data[4],
                                                                     name=data[31],
                                                                     enterby=request.user,
                                                                     modifyby=request.user)

                                    Logs_ormain.objects.create(
                                        orno=data[0],
                                        ordate=data[1],
                                        prno=data[2],
                                        accounttype=data[3].lower(),
                                        collector=data[4],
                                        collectordesc=data[31],
                                        payeetype=data[5],
                                        adtype=data[6],
                                        agencycode=data[7],
                                        clientcode=data[8],
                                        agentcode=data[9],
                                        payeename=data[10],
                                        amount=data[11],
                                        amountinwords=data[12],
                                        vatcode=data[33],
                                        vatrate=data[34],
                                        bankaccount=data[13],
                                        particulars=data[14],
                                        artype=data[15],
                                        status=data[16],
                                        statusdate=data[17],
                                        enterby=data[18],
                                        enterdate=data[19],
                                        product=data[35],
                                        initmark=data[21],
                                        glsmark=data[22],
                                        glsdate=data[23],
                                        totalwtax=data[24],
                                        wtaxrate=data[36],
                                        gov=data[25],
                                        branchcode=data[26],
                                        address1=data[27],
                                        address2=data[28],
                                        address3=data[29],
                                        tin=data[30],
                                        subscription=data[37].rstrip(),
                                        batchkey=batchkey,
                                        importstatus=importstatus,
                                        importremarks=importremarks,
                                        importby=request.user,
                                        branchdesc=data[32],
                                    ).save()
                                    breakstatus = 0
                                else:
                                    breakstatus = 1
                                    break

                            # inspect/insert detail
                            if breakstatus == 0:
                                with open(settings.MEDIA_ROOT + '/' + upload_d_directory + str(sequence) + ".txt") as textFile2:
                                    for line in textFile2:
                                        data = line.split("\t")
                                        for n, i in enumerate(data):
                                            data[n] = data[n].replace('"', '')

                                        if len(data) == 19:
                                            if Logs_ormain.objects.filter(orno=data[0], batchkey=batchkey):
                                                if not Adtype.objects.filter(code=data[16]):
                                                    importstatus = 'F'
                                                    importremarks = 'Failed: Adtype does not exist'
                                                elif not Vat.objects.filter(code=data[17]):
                                                    importstatus = 'F'
                                                    importremarks = 'Failed: Vat Type does not exist'
                                                # elif data[1] == "":
                                                #     importstatus = 'F'
                                                #     importremarks = 'Failed: Doc Type does not exist'
                                                else:
                                                    importstatus = 'S'
                                                    importremarks = 'Passed'

                                                Logs_ordetail.objects.create(
                                                    orno=data[0],
                                                    doctype=data[1],
                                                    docnum=data[2],
                                                    balance=data[3],
                                                    assignamount=data[4],
                                                    assignvatamount=data[5],
                                                    vatcode=data[17],
                                                    vatrate=data[18],
                                                    status=data[6],
                                                    statusdate=data[7],
                                                    usercode=data[8],
                                                    userdate=data[9],
                                                    docitem=data[10],
                                                    initmark=data[11],
                                                    glsmark=data[12],
                                                    glsdate=data[13],
                                                    assignwtaxamount=data[14],
                                                    assignwvatamount=data[15],
                                                    batchkey=batchkey,
                                                    importstatus=importstatus,
                                                    importremarks=importremarks,
                                                    importby=request.user,
                                                    adtype=data[16],
                                                    adtypedesc=get_object_or_None(Adtype, code=data[16]).description,
                                                ).save()
                                                breakstatus = 0
                                        else:
                                            breakstatus = 1
                                            break

                            if breakstatus == 0:    # 5
                                ordata_list = []
                                ordata_d_list = []

                                ordata = Logs_ormain.objects.filter(batchkey=batchkey).order_by('orno')
                                ordata_d = Logs_ordetail.objects.filter(batchkey=batchkey).order_by('orno')

                                for data in ordata:
                                    ordata_list.append([data.orno,
                                                        data.ordate,
                                                        data.payeename,
                                                        data.amount,
                                                        data.importstatus,
                                                        data.importremarks,
                                                       ])
                                for data in ordata_d:
                                    totalassign = 0
                                    totalassignamount = 0
                                    totalvatamount = 0

                                    def RepresentsInt(assignamount):
                                        try: 
                                            int(s)
                                            return True
                                        except ValueError:
                                            return False

                                    if RepresentsInt:
                                        totalassignamount = float(data.assignamount)

                                    def RepresentsInt(assignvatamount):
                                        try: 
                                            int(s)
                                            return True
                                        except ValueError:
                                            return False

                                    if RepresentsInt:
                                        totalvatamount = float(data.assignvatamount)
                                        
                                    totalassign = totalassignamount + totalvatamount

                                    ordata_d_list.append([data.orno,
                                                          totalassign,
                                                          data.importstatus,
                                                          data.adtypedesc,
                                                          data.importremarks,
                                                         ])

                                successcount = ordata.filter(importstatus='S').count()
                                rate = (float(successcount) / float(orcount)) * 100
                                data = {
                                    'result': 1,
                                    'artype': request.POST['or_artype'],
                                    'orcount': orcount,
                                    'ordata_list': ordata_list,
                                    'ordata_d_list': ordata_d_list,
                                    'successcount': successcount,
                                    'rate': rate,
                                    'batchkey': batchkey,
                                }
                            else:
                                data = {
                                    'result': 5
                                }
                            return JsonResponse(data)
                    # add detail upload here
                    else:
                        data = {
                            'result': 2
                        }
                    return JsonResponse(data)
                else:
                    data = {
                        'result': 4
                    }
                return JsonResponse(data)
            else:
                data = {
                    'result': 3
                }
                return JsonResponse(data)
        elif request.POST['or_artype'] == 'c':
            if request.FILES['or_file'] \
                    and request.FILES['or_file'].name.endswith('.dbf')\
                    and request.FILES['or_d_file'] \
                    and request.FILES['or_d_file'].name.endswith('.dbf'):   # 3
                if request.FILES['or_file']._size < float(upload_size)*1024*1024\
                        and request.FILES['or_d_file']._size < float(upload_size)*1024*1024:

                    sequence = datetime.now().isoformat().replace(':', '-')
                    batchkey = generatekey(1)

                    if storeupload(request.FILES['or_file'], sequence, 'dbf', upload_directory)\
                            and storeupload(request.FILES['or_d_file'], sequence, 'dbf', upload_d_directory):
                        orcount = 0

                        for data in DBF(settings.MEDIA_ROOT + '/' + upload_directory + str(sequence) + '.dbf', char_decode_errors='ignore'):
                            orcount += 1

                            if len(data) == 21:

                                # log status filtering
                                if Logs_ormain.objects.filter(orno=data['OR_NUM'], importstatus='P'):
                                    importstatus = 'F'
                                    importremarks = 'Skipped: Already posted'
                                elif Logs_ormain.objects.filter(orno=data['OR_NUM'], batchkey=batchkey, importstatus='S'):
                                    importstatus = 'F'
                                    importremarks = 'Skipped: Already exists in this batch'
                                elif not Bankaccount.objects.filter(code=data['BANKCODE']):
                                    importstatus = 'F'
                                    importremarks = 'Failed: Bank account does not exist'
                                elif not Circulationpaytype.objects.filter(code=data['PAY_TYPE']) and data['ACCT_TYPE'] is 'C':
                                    importstatus = 'F'
                                    importremarks = 'Failed: Circulation Pay Type does not exist'
                                else:
                                    importstatus = 'S'
                                    importremarks = 'Passed'

                                if importstatus is not 'F':
                                    # new collector checking
                                    if not Collector.objects.filter(code=data['COLL_INIT']):
                                        Collector.objects.create(code=data['COLL_INIT'],
                                                                 name=data['USER_ID'],
                                                                 enterby=request.user,
                                                                 modifyby=request.user)
                                    # new agent checking
                                    if not Agent.objects.filter(code=data['AGNT_CODE']) and data['ACCT_TYPE'] is 'C':
                                        Agent.objects.create(code=data['AGNT_CODE'],
                                                             name=data['PAY_NAME'],
                                                             enterby=request.user,
                                                             modifyby=request.user)

                                Logs_ormain.objects.create(
                                    orno=data['OR_NUM'],
                                    ordate=data['OR_DATE'],
                                    prno=data['PR_NUM'],
                                    amount=data['TOT_PAID'],
                                    amountinwords=data['AMT_WORD'],
                                    bankaccount=data['BANKCODE'],
                                    accounttype=data['ACCT_TYPE'].lower(),
                                    vatcode='VE',
                                    vatrate=0,
                                    artype='C',
                                    collector=data['COLL_INIT'],
                                    collectordesc=data['USER_ID'],
                                    agentcode=data['AGNT_CODE'],
                                    payeename=data['PAY_NAME'],
                                    payeetype='A',
                                    paytype=data['PAY_TYPE'],
                                    branchcode='HO',
                                    batchkey=batchkey,
                                    importstatus=importstatus,
                                    importremarks=importremarks,
                                    importby=request.user,
                                ).save()
                                breakstatus = 0
                            else:
                                breakstatus = 1
                                break

                        # inspect/insert detail
                        if breakstatus == 0:
                            for data in DBF(settings.MEDIA_ROOT + '/' + upload_d_directory + str(sequence) + '.dbf', char_decode_errors='ignore'):
                            # for data in DBF(settings.MEDIA_ROOT + '/' + upload_d_directory + str(sequence) + '.dbf'):
                                if len(data) == 17:
                                    if Logs_ormain.objects.filter(orno=data['OR_NUM'], batchkey=batchkey, accounttype='C'):
                                        if not Productgroup.objects.filter(code=data['PRODUCT']):
                                            importstatus = 'F'
                                            importremarks = 'Failed: Product Group does not exist'
                                        else:
                                            importstatus = 'S'
                                            importremarks = 'Passed'

                                        Logs_ordetail.objects.create(
                                            orno=data['OR_NUM'],
                                            assignamount=data['AMT_PAID'],
                                            assignvatamount=0,
                                            product=data['PRODUCT'],
                                            batchkey=batchkey,
                                            importstatus=importstatus,
                                            importremarks=importremarks,
                                            importby=request.user,
                                        ).save()
                                        breakstatus = 0
                                else:
                                    breakstatus = 1
                                    break

                        if breakstatus == 0:    # 5
                            ordata_list = []
                            ordata_d_list = []

                            ordata = Logs_ormain.objects.filter(batchkey=batchkey).order_by('orno')
                            ordata_d = Logs_ordetail.objects.filter(batchkey=batchkey).order_by('orno')

                            for data in ordata:
                                ordata_list.append([data.orno,
                                                    data.ordate,
                                                    data.payeename,
                                                    data.amount,
                                                    data.importstatus,
                                                    data.importremarks,
                                                   ])
                            for data in ordata_d:
                                if request.POST['or_artype'] == 'A':
                                    data_adtype = data.adtypedesc
                                else:
                                    data_adtype = data.product
                                ordata_d_list.append([data.orno,
                                                      float(data.assignamount) + float(data.assignvatamount),
                                                      data.importstatus,
                                                      data_adtype,
                                                     ])

                            successcount = ordata.filter(importstatus='S').count()
                            rate = (float(successcount) / float(orcount)) * 100
                            data = {
                                'result': 1,
                                'artype': request.POST['or_artype'],
                                'orcount': orcount,
                                'ordata_list': ordata_list,
                                'ordata_d_list': ordata_d_list,
                                'successcount': successcount,
                                'rate': rate,
                                'batchkey': batchkey,
                            }
                        else:
                            data = {
                                'result': 5
                            }
                        return JsonResponse(data)
                    else:
                        data = {
                            'result': 2
                        }
                    return JsonResponse(data)
                else:
                    data = {
                        'result': 4
                    }
                return JsonResponse(data)
            else:
                data = {
                    'result': 3
                }
                return JsonResponse(data)
        else:
            data = {
                'result': 6
            }
            return JsonResponse(data)


@csrf_exempt
def exportsave(request):
    if request.method == 'POST':
        # data-result definition:
        #   1: success
        #   2: failed - artype error
        if request.POST['artype'] == 'a' or request.POST['artype'] == 'c':
            ormain = Logs_ormain.objects.filter(importstatus='S', batchkey=request.POST['batchkey'])
            ormain_list = []
            ordetail_list = []

            if request.POST['artype'] == 'a':
                for data in ormain:
                    vatamount = 0
                    vatable = 0
                    vatexempt = 0
                    vatzerorated = 0
                    
                    # logsormain to tempormain
                    temp_ormain = Temp_ormain.objects.create(
                        orno=data.orno,
                        ordate=datetime.strptime(data.ordate, '%m/%d/%Y'),
                        prno=data.prno,
                        accounttype=data.accounttype,
                        bankaccountcode=data.bankaccount,
                        branchcode=data.branchcode,
                        collectorcode=data.collector,
                        collectordesc=data.collectordesc,
                        artype=data.artype,
                        agencycode=data.agencycode,
                        clientcode=data.clientcode,
                        agentcode=data.agentcode,
                        payeecode=data.clientcode if data.payeetype == 'C' else data.agencycode,
                        payeename=data.payeename,
                        payeetype=data.payeetype,
                        productcode=data.product,
                        adtypecode=data.adtype,
                        amount=data.amount,
                        amountinwords=data.amountinwords,
                        vatrate=data.vatrate,
                        vatcode=data.vatcode,
                        totalwtax=data.totalwtax,
                        wtaxrate=data.wtaxrate,
                        particulars=data.particulars,
                        subscription=data.subscription,
                        importby=data.importby,
                        batchkey=data.batchkey,
                        postingremarks='Processing...',
                    )
                    temp_ormain.save()

                    if temp_ormain.accounttype == 'a' or temp_ormain.accounttype == 's':
                        # cash in bank
                        Temp_ordetail.objects.create(
                            orno=data.orno,
                            ordate=datetime.strptime(data.ordate, '%m/%d/%Y'),
                            debitamount=data.amount,
                            balancecode='D',
                            chartofaccountcode=Companyparameter.objects.get(code='PDI').coa_cashinbank.pk,
                            bankaccountcode=data.bankaccount,
                            batchkey=data.batchkey,
                            postingremarks='Processing...',
                        ).save()
                        remainingamount = float(data.amount)                        

                        # accounttype = (a/r)
                        if temp_ormain.accounttype == 'a':
                            # transfer ordetails
                            ordetail = Logs_ordetail.objects.filter(importstatus='S', batchkey=request.POST['batchkey'], orno=data.orno)
                            for data_d in ordetail:
                                Temp_ordetail.objects.create(
                                    orno=data_d.orno,
                                    ordate=datetime.strptime(data.ordate, '%m/%d/%Y'),
                                    adtypecode=data_d.adtype,
                                    amount=data_d.assignamount,
                                    vatamount=data_d.assignvatamount,
                                    creditamount=data_d.assignamount,
                                    balancecode='C',
                                    chartofaccountcode=Adtype.objects.get(code=data_d.adtype).chartofaccount_arcode.pk,
                                    payeecode=data.clientcode if data.payeetype == 'C' else data.agencycode,
                                    payeename=data.payeename,
                                    batchkey=data.batchkey,
                                    postingremarks='Processing...',
                                ).save()

                                if data_d.vatrate > 0:
                                    vatable = float(vatable) + float(data_d.assignamount)
                                elif data_d.vatcode == 'VE':
                                    vatexempt = float(vatexempt) + float(data_d.assignamount)
                                elif data_d.vatcode == 'ZE':
                                    vatzerorated = float(vatzerorated) + float(data_d.assignamount)

                                # do vat here
                                Temp_ordetail.objects.create(
                                    orno=data_d.orno,
                                    ordate=datetime.strptime(data.ordate, '%m/%d/%Y'),
                                    creditamount=data_d.assignvatamount,
                                    balancecode='C',
                                    chartofaccountcode=Companyparameter.objects.get(code='PDI').coa_outputvat.pk,
                                    vatrate=float(data_d.vatrate),
                                    vatcode=data_d.vatcode,
                                    batchkey=data.batchkey,
                                    postingremarks='Processing...',
                                ).save()

                                vatamount = float(vatamount) + float(data_d.assignvatamount)

                                remainingamount = remainingamount - (float(data_d.assignamount) + float(data_d.assignvatamount))
                                remainingamount = float(format(remainingamount, '.2f'))

                            # transfer leftovers
                            if remainingamount > 0:
                                leftover_amount = float(format(remainingamount / (1 + (float(data.vatrate) * 0.01)), '.2f'))
                                leftover_vatamount = float(format(leftover_amount * (float(data.vatrate) * 0.01), '.2f'))
                                Temp_ordetail.objects.create(
                                    orno=data.orno,
                                    ordate=datetime.strptime(data.ordate, '%m/%d/%Y'),
                                    adtypecode=data.adtype,
                                    amount=leftover_amount,
                                    vatamount=leftover_vatamount,
                                    creditamount=leftover_amount,
                                    balancecode='C',
                                    chartofaccountcode=Adtype.objects.get(code=data.adtype).chartofaccount_arcode.pk,
                                    payeecode=data.clientcode if data.payeetype == 'C' else data.agencycode,
                                    payeename=data.payeename,
                                    batchkey=data.batchkey,
                                    postingremarks='Processing...',
                                ).save()
                                if data_d.vatrate > 0:
                                    vatable = float(vatable) + float(leftover_amount)
                                elif data_d.vatcode == 'VE':
                                    vatexempt = float(vatexempt) + float(leftover_amount)
                                elif data_d.vatcode == 'ZE':
                                    vatzerorated = float(vatzerorated) + float(leftover_amount)

                                # do vat here
                                Temp_ordetail.objects.create(
                                    orno=data.orno,
                                    ordate=datetime.strptime(data.ordate, '%m/%d/%Y'),
                                    creditamount=leftover_vatamount,
                                    balancecode='C',
                                    chartofaccountcode=Companyparameter.objects.get(code='PDI').coa_outputvat.pk,
                                    vatrate=data.vatrate,
                                    vatcode=data.vatcode,
                                    batchkey=data.batchkey,
                                    postingremarks='Processing...',
                                ).save()
                                vatamount = float(vatamount) + float(leftover_vatamount)

                        # accounttype = 'S' (subscription) and sub type is 1
                        elif temp_ormain.subscription == '1':
                            Temp_ordetail.objects.create(
                                orno=data.orno,
                                ordate=datetime.strptime(data.ordate, '%m/%d/%Y'),
                                creditamount=data.amount,
                                balancecode='C',
                                chartofaccountcode=Companyparameter.objects.get(code='PDI').coa_unsubscribe.pk,
                                batchkey=data.batchkey,
                                postingremarks='Processing...',
                            ).save()

                    else: # if account type = 'R or D' (r/e)
                        # cash in bank
                        Temp_ordetail.objects.create(
                            orno=data.orno,
                            ordate=datetime.strptime(data.ordate, '%m/%d/%Y'),
                            debitamount=data.amount,
                            balancecode='D',
                            chartofaccountcode=Companyparameter.objects.get(code='PDI').coa_cashinbank.pk,
                            bankaccountcode=data.bankaccount,
                            batchkey=data.batchkey,
                            postingremarks='Processing...',
                        ).save()
                        remainingamount = float(data.amount)
                        remainingamount = float(format(remainingamount, '.2f'))

                        # (r/e)
                        re_amount = float(format(remainingamount / (1 + (float(data.vatrate) * 0.01)), '.2f'))
                        re_vatamount = float(format(re_amount * (float(data.vatrate) * 0.01), '.2f'))
                        Temp_ordetail.objects.create(
                            orno=data.orno,
                            ordate=datetime.strptime(data.ordate, '%m/%d/%Y'),
                            adtypecode=data.adtype,
                            amount=re_amount,
                            vatamount=re_vatamount,
                            creditamount=re_amount,
                            balancecode='C',
                            chartofaccountcode=Adtype.objects.get(code=data.adtype).chartofaccount_revcode.pk,
                            productcode=data.product,
                            batchkey=data.batchkey,
                            postingremarks='Processing...',
                        ).save()

                        if data.vatrate > 0:
                            vatable = float(vatable) + float(re_amount)
                        elif data.vatcode == 'VE':
                            vatexempt = float(vatexempt) + float(re_amount)
                        elif data.vatcode == 'ZE':
                            vatzerorated = float(vatzerorated) + float(re_amount)

                        # do vat here
                        Temp_ordetail.objects.create(
                            orno=data.orno,
                            ordate=datetime.strptime(data.ordate, '%m/%d/%Y'),
                            creditamount=re_vatamount,
                            balancecode='C',
                            chartofaccountcode=Companyparameter.objects.get(code='PDI').coa_outputvat.pk,
                            vatrate=data.vatrate,
                            vatcode=data.vatcode,
                            batchkey=data.batchkey,
                            postingremarks='Processing...',
                        ).save()
                        vatamount = float(vatamount) + float(re_vatamount)

                    # temp ormain to ormain
                    if temp_ormain.accounttype == 'd':
                        ortype_accounttype = 'r'
                    else:
                        ortype_accounttype = temp_ormain.accounttype

                    if temp_ormain.payeetype == 'y':
                        payeetype_payeetype = 'ag'
                    else:
                        payeetype_payeetype = temp_ormain.payeetype

                    if temp_ormain.payeecode.upper() == 'WI':
                        temp_remarks = temp_ormain.payeename
                    else:
                        temp_remarks = ''

                    Ormain.objects.create(
                        ornum=temp_ormain.orno,
                        ordate=temp_ormain.ordate,
                        prnum=temp_ormain.prno,
                        orstatus='F',
                        amount=temp_ormain.amount,
                        amountinwords=temp_ormain.amountinwords,
                        vatrate=float(temp_ormain.vatrate),
                        vatamount=vatamount,
                        particulars=temp_ormain.particulars,
                        vatablesale=vatable,
                        vatexemptsale=vatexempt,
                        vatzeroratedsale=vatzerorated,
                        totalsale=temp_ormain.amount,
                        status='A',
                        bankaccount=Bankaccount.objects.get(code=temp_ormain.bankaccountcode),
                        branch=Branch.objects.get(code=temp_ormain.branchcode),
                        collector=Collector.objects.get(code=temp_ormain.collectorcode),
                        collector_code=temp_ormain.collectorcode,
                        collector_name=temp_ormain.collectordesc,
                        enterby=request.user,
                        modifyby=request.user,
                        ortype=Ortype.objects.get(code=ortype_accounttype.upper()),
                        vat=Vat.objects.get(code=temp_ormain.vatcode),
                        agency=get_object_or_None(Customer, code=temp_ormain.agencycode),
                        client=get_object_or_None(Customer, code=temp_ormain.clientcode),
                        orsource='A',
                        payee_code=temp_ormain.payeecode,
                        payee_name=temp_ormain.payeename,
                        payee_type=payeetype_payeetype.upper(),
                        circulationproduct=Circulationproduct.objects.get(code=temp_ormain.productcode),
                        circulationproduct_code=temp_ormain.productcode,
                        circulationproduct_name=Circulationproduct.objects.get(code=temp_ormain.productcode).description,
                        wtaxrate=float(temp_ormain.wtaxrate),
                        wtaxamount=temp_ormain.totalwtax,
                        importby=request.user,
                        importornum=temp_ormain.orno,
                        adtype=Adtype.objects.get(code=temp_ormain.adtypecode),
                        transaction_type='A',
                        outputvattype=Outputvattype.objects.get(code='OVT - S'),
                        remarks="Payee name: " + temp_ormain.payeename if temp_ormain.payeecode.upper() == 'WI' else '',
                    ).save()

                    # temp ordetail to ordetail
                    temp_ordetail = Temp_ordetail.objects.filter(orno=temp_ormain.orno, batchkey=temp_ormain.batchkey, postingstatus='F')\
                                                         .values('orno', 'ordate', 'chartofaccountcode', 'payeecode', 'vatcode', 'balancecode', 'bankaccountcode').order_by()\
                                                         .annotate(debit=Sum('debitamount'), credit=Sum('creditamount'))
                                                         # .values('orno', 'ordate', 'chartofaccountcode', 'payeecode', 'vatcode', 'balancecode', 'bankaccountcode', 'productcode').order_by()\
                    for index, data2 in enumerate(temp_ordetail):
                        debit = data2['debit'] if data2['debit'] is not None else 0.00
                        credit = data2['credit'] if data2['credit'] is not None else 0.00

                        if (Vat.objects.filter(code=data2['vatcode']) and credit > 0) or not Vat.objects.filter(code=data2['vatcode']):
                            Ordetail.objects.create(
                                item_counter=index + 1,
                                or_num=data2['orno'],
                                or_date=data2['ordate'],
                                debitamount=debit,
                                creditamount=credit,
                                balancecode=data2['balancecode'],
                                status='A',
                                chartofaccount=Chartofaccount.objects.get(pk=data2['chartofaccountcode']),
                                customer=get_object_or_None(Customer, code=data2['payeecode']),
                                bankaccount=get_object_or_None(Bankaccount, code=data2['bankaccountcode']),
                                # product=get_object_or_None(Product, code=data2['productcode']),
                                enterby=request.user,
                                modifyby=request.user,
                                ormain=Ormain.objects.get(ornum=temp_ormain.orno, orstatus='F', status='A', orsource='A'),
                                vat=get_object_or_None(Vat, code=data2['vatcode']),
                            ).save()

                    # set posting status to success for temp
                    temp_ormain.postingstatus = 'S'
                    temp_ormain.save()
                    temp_ordetail.update(postingstatus='S')

                    # set to posted after success of orno and batch
                    data.importstatus = 'P'
                    data.save()
                    Logs_ordetail.objects.filter(batchkey=request.POST['batchkey'], orno=data.orno).update(importstatus='P')

                    # save for preview
                    ormain_data = Ormain.objects.filter(ornum=temp_ormain.orno, orstatus='F', status='A', orsource='A').order_by('ornum')
                    for datalist in ormain_data:
                        ormain_list.append([datalist.ornum,
                                            datalist.ordate,
                                            datalist.payee_name,
                                            datalist.payee_type,
                                            datalist.product_name,
                                            datalist.amount,
                                            'S',
                                           ])

                    ordetail_data = Ordetail.objects.filter(or_num=temp_ormain.orno, status='A', isdeleted=0).order_by('-item_counter')
                    for datalist in ordetail_data:
                        customer = datalist.customer.name if datalist.customer else None
                        vat = datalist.vat.code if datalist.vat else None
                        ordetail_list.append([datalist.or_num,
                                              datalist.chartofaccount.accountcode,
                                              datalist.chartofaccount.title,
                                              customer,
                                              vat,
                                              datalist.debitamount,
                                              datalist.creditamount,
                                              'S',
                                             ])

            elif request.POST['artype'] == 'c':
                for data in ormain:
                    vatexempt = float(data.amount)
                    vatamount = 0
                    vatable = 0
                    vatzerorated = 0

                    # logsormain to tempormain
                    temp_ormain = Temp_ormain.objects.create(
                        orno=data.orno,
                        ordate=datetime.strptime(data.ordate, '%Y-%m-%d'),
                        prno=data.prno,
                        amount=data.amount,
                        amountinwords=data.amountinwords,
                        bankaccountcode=data.bankaccount,
                        accounttype=data.accounttype,
                        vatrate=data.vatrate,
                        vatcode=data.vatcode,
                        artype=data.artype,
                        collectorcode=data.collector,
                        collectordesc=data.collectordesc,
                        agentcode=data.agentcode,
                        payeecode=data.agentcode,
                        payeename=data.payeename,
                        payeetype=data.payeetype,
                        paytype=data.paytype,
                        branchcode=data.branchcode,
                        importby=data.importby,
                        batchkey=data.batchkey,
                        postingremarks='Processing...',
                    )
                    temp_ormain.save()

                    # cash in bank
                    Temp_ordetail.objects.create(
                        orno=data.orno,
                        ordate=datetime.strptime(data.ordate, '%Y-%m-%d'),
                        debitamount=data.amount,
                        balancecode='D',
                        chartofaccountcode=Companyparameter.objects.get(code='PDI').coa_cashinbank.pk,
                        bankaccountcode=data.bankaccount,
                        batchkey=data.batchkey,
                        postingremarks='Processing...',
                    ).save()

                    if temp_ormain.accounttype == 'c':
                        # transfer ordetails
                        ordetail = Logs_ordetail.objects.filter(importstatus='S', batchkey=request.POST['batchkey'], orno=data.orno)
                        for data_d in ordetail:
                            temp_category = Circulationpaytype.objects.get(code=data.paytype, isdeleted=0).category
                            temp_product = Productgroup.objects.get(code=data_d.product, isdeleted=0)

                            temp_chartofaccount = Productgroupcategory.objects.get(category=temp_category, productgroup=temp_product)

                            Temp_ordetail.objects.create(
                                orno=data_d.orno,
                                ordate=datetime.strptime(data.ordate, '%Y-%m-%d'),
                                amount=data_d.assignamount,
                                vatamount=0,
                                creditamount=data_d.assignamount,
                                balancecode='C',
                                chartofaccountcode=temp_chartofaccount.chartofaccount.pk,
                                payeecode=data.agentcode,
                                payeename=data.payeename,
                                batchkey=data.batchkey,
                                postingremarks='Processing...',
                            ).save()

                    # temp ormain to ormain
                    if temp_ormain.accounttype == 'c':
                        ortype_accounttype = 'r'
                    else:
                        ortype_accounttype = temp_ormain.accounttype

                    Ormain.objects.create(
                        ornum=temp_ormain.orno,
                        ordate=temp_ormain.ordate,
                        prnum=temp_ormain.prno,
                        orstatus='F',
                        amount=temp_ormain.amount,
                        amountinwords=temp_ormain.amountinwords,
                        vatrate=temp_ormain.vatrate,
                        vatamount=vatamount,
                        vatablesale=vatable,
                        vatexemptsale=vatexempt,
                        vatzeroratedsale=vatzerorated,
                        particulars=temp_ormain.particulars,
                        totalsale=temp_ormain.amount,
                        status='A',
                        bankaccount=Bankaccount.objects.get(code=temp_ormain.bankaccountcode),
                        branch=Branch.objects.get(code=temp_ormain.branchcode),
                        collector=Collector.objects.get(code=temp_ormain.collectorcode),
                        collector_code=temp_ormain.collectorcode,
                        collector_name=temp_ormain.collectordesc,
                        enterby=request.user,
                        modifyby=request.user,
                        ortype=Ortype.objects.get(code=ortype_accounttype.upper()),
                        vat=Vat.objects.get(code=temp_ormain.vatcode),
                        agent=get_object_or_None(Agent, code=temp_ormain.agentcode),
                        orsource='C',
                        payee_code=temp_ormain.payeecode,
                        payee_name=temp_ormain.payeename,
                        payee_type=temp_ormain.payeetype.upper(),
                        importby=request.user,
                        importornum=temp_ormain.orno,
                        transaction_type='A',
                        outputvattype=Outputvattype.objects.get(code='OVT - G'),
                    ).save()

                    # temp ordetail to ordetail
                    temp_ordetail = Temp_ordetail.objects.filter(orno=temp_ormain.orno, batchkey=temp_ormain.batchkey, postingstatus='F')\
                                                         .values('orno', 'ordate', 'chartofaccountcode', 'balancecode', 'bankaccountcode').order_by()\
                                                         .annotate(debit=Sum('debitamount'), credit=Sum('creditamount'))
                    for index, data2 in enumerate(temp_ordetail):
                        debit = data2['debit'] if data2['debit'] is not None else 0.00
                        credit = data2['credit'] if data2['credit'] is not None else 0.00

                        Ordetail.objects.create(
                            item_counter=index + 1,
                            or_num=data2['orno'],
                            or_date=data2['ordate'],
                            debitamount=debit,
                            creditamount=credit,
                            balancecode=data2['balancecode'],
                            status='A',
                            chartofaccount=Chartofaccount.objects.get(pk=data2['chartofaccountcode']),
                            bankaccount=get_object_or_None(Bankaccount, code=data2['bankaccountcode']),
                            enterby=request.user,
                            modifyby=request.user,
                            ormain=Ormain.objects.get(ornum=temp_ormain.orno, orstatus='F', status='A', orsource='C'),
                        ).save()

                    # set posting status to success for temp
                    temp_ormain.postingstatus = 'S'
                    temp_ormain.save()
                    temp_ordetail.update(postingstatus='S')

                    # set to posted after success of orno and batch
                    data.importstatus = 'P'
                    data.save()
                    Logs_ordetail.objects.filter(batchkey=request.POST['batchkey'], orno=data.orno).update(importstatus='P')

                    # save for preview
                    ormain_data = Ormain.objects.filter(ornum=temp_ormain.orno, orstatus='F', status='A', orsource='C').order_by('ornum')
                    for datalist in ormain_data:
                        ormain_list.append([datalist.ornum,
                                            datalist.ordate,
                                            datalist.payee_name,
                                            datalist.payee_type,
                                            datalist.product_name,
                                            datalist.amount,
                                            'S',
                                           ])

                    ordetail_data = Ordetail.objects.filter(or_num=temp_ormain.orno, status='A', isdeleted=0).order_by('-item_counter')
                    for datalist in ordetail_data:
                        customer = datalist.customer.name if datalist.customer else None
                        vat = datalist.vat.code if datalist.vat else None
                        ordetail_list.append([datalist.or_num,
                                              datalist.chartofaccount.accountcode,
                                              datalist.chartofaccount.title,
                                              customer,
                                              vat,
                                              datalist.debitamount,
                                              datalist.creditamount,
                                              'S',
                                             ])
            # append failed items from temp to ormain_list, ordetail_list
            ormain_data = Temp_ormain.objects.filter(batchkey=request.POST['batchkey'], postingstatus='F')
            for datalist in ormain_data:
                ormain_list.append([datalist.orno,
                                    datalist.ordate,
                                    datalist.payeename,
                                    datalist.payeetype,
                                    datalist.productcode,
                                    datalist.amount,
                                    'F',
                                   ])

            totalcount = Temp_ormain.objects.filter(batchkey=request.POST['batchkey']).count()
            successcount = Temp_ormain.objects.filter(batchkey=request.POST['batchkey'], postingstatus='S').count()
            rate = (int(successcount) / int(totalcount)) * 100

            # delete temp
            Temp_ormain.objects.filter(batchkey=request.POST['batchkey']).delete()
            Temp_ordetail.objects.filter(batchkey=request.POST['batchkey']).delete()

            data = {
                'result': 1,
                'ordata_list': ormain_list,
                'ordata_d_list': ordetail_list,
                'totalcount': totalcount,
                'successcount': successcount,
                'rate': rate,
            }
        else:
            data = {
                'result': 2
            }

        return JsonResponse(data)
