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
from django.db.models import Count, Sum
from datetime import datetime
from datetime import timedelta
from annoying.functions import get_object_or_None
from utils.views import wccount, storeupload
from acctentry.views import generatekey
from dbfread import DBF
from django.utils.crypto import get_random_string
from django.db.models import Q


upload_directory = 'processing_or/uploaded_files/ormain/'
upload_d_directory = 'processing_or/uploaded_files/ordetail/'
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
            # if request.FILES['or_file'] and request.FILES['or_file'].name.endswith('.txt'):     # 3
            if request.FILES['or_file'] \
                    and request.FILES['or_file'].name.endswith('.txt') \
                    and request.FILES['or_d_file'] \
                    and request.FILES['or_d_file'].name.endswith('.txt'):     # 3
                # if request.FILES['or_file']._size < float(upload_size)*1024*1024:
                if request.FILES['or_file']._size < float(upload_size)*1024*1024 \
                        and request.FILES['or_d_file']._size < float(upload_size)*1024*1024:

                    sequence = datetime.now().isoformat().replace(':', '-')
                    batchkey = generatekey(1)

                    if storeupload(request.FILES['or_file'], sequence, 'txt', upload_directory)\
                            and storeupload(request.FILES['or_d_file'], sequence, 'txt', upload_d_directory):    # 2
                        orcount = 0
                        datatotal = wccount(upload_directory + str(sequence) + '.txt') + 1
                        datacurrent = 0

                        with open(upload_directory + str(sequence) + ".txt") as textFile:
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
                                    elif not Product.objects.filter(code=data[35]):
                                        importstatus = 'F'
                                        importremarks = 'Failed: Product does not exist'
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
                                    ).save()
                                    breakstatus = 0
                                else:
                                    breakstatus = 1
                                    break

                            # inspect/insert detail
                            with open(upload_d_directory + str(sequence) + ".txt") as textFile2:
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
                                    ordata_d_list.append([data.orno,
                                                          float(data.assignamount) + float(data.assignvatamount),
                                                          data.importstatus,
                                                          data.adtypedesc,
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
        elif request.POST['or_artype'] == 'c' and request.POST['batchkey']:
            if request.FILES['or_file'] and request.FILES['or_file'].name.endswith('.dbf'):
                if request.FILES['or_file']._size < float(upload_size)*1024*1024:
                    try:
                        data = Temp_ormain.objects.latest('importsequence')
                        sequence = int(data.importsequence) + 1
                    except Temp_ormain.DoesNotExist:
                        sequence = 1

                    if storeupload(request.FILES['or_file'], sequence, 'dbf', upload_directory):
                        orcount = 0
                        failedcount = 0

                        datatotal = wccount(upload_directory + str(sequence) + '.dbf') + 1
                        datacurrent = 0

                        for data in DBF(upload_directory + str(sequence) + '.dbf', char_decode_errors='ignore'):
                            orcount += 1

                            if len(data) == 21:
                                Temp_ormain.objects.create(
                                    orno=data['OR_NUM'],
                                    ordate=data['OR_DATE'],
                                    prno=data['PR_NUM'],
                                    accounttype=data['ACCT_TYPE'],
                                    collector=data['COLL_INIT'],
                                    payeetype='A',
                                    agencycode=data['AGY_CODE'],
                                    clientcode=data['CLNT_CODE'],
                                    agentcode=data['AGNT_CODE'],
                                    payeename=data['PAY_NAME'],
                                    amount=data['TOT_PAID'],
                                    amountinwords=data['AMT_WORD'],
                                    bankaccount=data['BANKCODE'],
                                    particulars=data['REMARKS'],
                                    artype=data['OR_ARTYPE'],
                                    status=data['STATUS'],
                                    statusdate=data['STATUS_D'],
                                    enterby=data['USER_ID'],
                                    enterdate=data['USER_D'],
                                    product=data['PRODUCT'],
                                    importsequence=sequence,
                                    importby=request.user,
                                ).save()
                                breakstatus = 0
                            else:
                                breakstatus = 1
                                break
                            datacurrent += 1
                        if breakstatus == 0:
                            # existing data
                            ormain_existing = Ormain.objects.filter(importornum__in=set(Temp_ormain.objects.filter(importsequence=sequence).values_list('orno', flat=True))).order_by('importornum').values('importornum').distinct()
                            existingcount = len(ormain_existing)
                            existingdata = list(ormain_existing)
                            # failed data
                            temp_ormain_distinct = Temp_ormain.objects.filter(importsequence=sequence).values('orno').annotate(Count('orno')).count()
                            failedcount = orcount - temp_ormain_distinct
                            tempormain_duplicate = Temp_ormain.objects.filter(importsequence=sequence).values('orno').annotate(Count('id')).order_by().filter(id__count__gt=1)
                            faileddata = list(tempormain_duplicate)
                            #success data
                            temp_ormain_distinct = Temp_ormain.objects.filter(importsequence=sequence).values_list('orno', flat=True).annotate(Count('id')).order_by().distinct()
                            successdata = list(set(temp_ormain_distinct) - set(ormain_existing.values_list('importornum', flat=True)))
                            successcount = len(successdata)

                            rate = (float(successcount) / float(orcount)) * 100
                            data = {
                                'result': 1,
                                'sequence': sequence,
                                'artype': request.POST['or_artype'],
                                'orcount': orcount,
                                'successcount': successcount,
                                'successdata': successdata,
                                'failedcount': failedcount,
                                'faileddata': faileddata,
                                'existingcount': existingcount,
                                'existingdata': existingdata,
                                'rate': rate,
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

            if request.POST['artype'] == 'a':
                ormain = Logs_ormain.objects.filter(importstatus='S', batchkey=request.POST['batchkey'])
                ormain_list = []
                ordetail_list = []

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
                                    vatrate=data_d.vatrate,
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

                    else: # if account type = 'R' (r/e)
                        print "no setup yet"

                    # temp ormain to ormain
                    Ormain.objects.create(
                        ornum=temp_ormain.orno,
                        ordate=temp_ormain.ordate,
                        prnum=temp_ormain.prno,
                        orstatus='F',
                        amount=temp_ormain.amount,
                        amountinwords=temp_ormain.amountinwords,
                        vatrate=temp_ormain.vatrate,
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
                        ortype=Ortype.objects.get(pk=2),
                        vat=Vat.objects.get(code=temp_ormain.vatcode),
                        agency=get_object_or_None(Customer, code=temp_ormain.agencycode),
                        client=get_object_or_None(Customer, code=temp_ormain.clientcode),
                        orsource='A',
                        payee_code=temp_ormain.payeecode,
                        payee_name=temp_ormain.payeename,
                        payee_type=temp_ormain.payeetype,
                        product=Product.objects.get(code=temp_ormain.productcode),
                        product_code=temp_ormain.productcode,
                        product_name=Product.objects.get(code=temp_ormain.productcode).description,
                        wtaxrate=temp_ormain.wtaxrate,
                        wtaxamount=temp_ormain.totalwtax,
                        importby=request.user,
                        importornum=temp_ormain.orno,
                        adtype=Adtype.objects.get(code=temp_ormain.adtypecode),
                        transaction_type='A',
                        outputvattype=Outputvattype.objects.get(code='OVT - S'),
                    ).save()

                    # temp ordetail to ordetail
                    temp_ordetail = Temp_ordetail.objects.filter(orno=temp_ormain.orno, batchkey=temp_ormain.batchkey, postingstatus='F')\
                                                         .values('orno', 'ordate', 'chartofaccountcode', 'payeecode', 'vatcode', 'balancecode', 'bankaccountcode').order_by()\
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
                            customer=get_object_or_None(Customer, code=data2['payeecode']),
                            bankaccount=get_object_or_None(Bankaccount, code=data2['bankaccountcode']),
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


# @csrf_exempt
# def exportsave(request):
#     if request.method == 'POST':
#         if request.POST['artype'] == 'a' or request.POST['artype'] == 'c':
#
#             # get unique in temp
#             temp_unique = Temp_ormain.objects.filter(importsequence=request.POST['sequence']).values_list('orno', flat=True).annotate(Count('id')).order_by().filter(id__count=1)
#             # compare if exists in ormain
#             main_temp_unique = Ormain.objects.filter(importornum__in=set(temp_unique)).order_by('importornum').values_list('importornum', flat=True)
#             # get duplicate in temp (distinct)
#             temp_duplicate = Temp_ormain.objects.filter(importsequence=request.POST['sequence']).values_list('orno', flat=True).annotate(Count('id')).order_by().filter(id__count__gt=1)
#             # compare if exists in ormain
#             main_temp_duplicate = Ormain.objects.filter(importornum__in=set(temp_duplicate)).order_by('importornum').values_list('importornum', flat=True)
#
#             # subtract list to list
#             temp_unique = list(map(str, set(temp_unique) - set(main_temp_unique)))
#             temp_duplicate = list(map(str, set(temp_duplicate) - set(main_temp_duplicate)))
#
#             temp_unique = list(map(str, set(Temp_ormain.objects.values_list('id', flat=True).filter(importsequence=request.POST['sequence'], orno__in=temp_unique))))
#             temp_duplicate_new = []
#             for data in temp_duplicate:
#                 or_id = Temp_ormain.objects.values_list('id', flat=True).filter(importsequence=request.POST['sequence'], orno=data).first()
#                 temp_duplicate_new.append(str(or_id))
#             temp_data = temp_unique + temp_duplicate_new
#
#             temp_ormain = Temp_ormain.objects.filter(importsequence=request.POST['sequence'], pk__in=temp_data)
#
#             processedcount = 0
#             successcount = 0
#             successdata = []
#             failedcount = 0
#             faileddata = []
#
#             for data in temp_ormain:
#
#                 if request.POST['artype'] == 'a':
#                     data_date = datetime.strptime(data.ordate, '%m/%d/%Y')
#                 else:
#                     data_date = datetime.strptime(data.ordate, '%Y-%m-%d')
#                 year = str(data_date.year)
#                 yearqs = Ormain.objects.filter(ornum__startswith=year)
#                 if yearqs:
#                     ornumlast = yearqs.latest('ornum')
#                     latestornum = str(ornumlast)
#                     ornum = year
#                     last = str(int(latestornum[4:]) + 1)
#                     zero_addon = 6 - len(last)
#                     for num in range(0, zero_addon):
#                         ornum += '0'
#                     ornum += last
#                 else:
#                     ornum = year + '000001'
#
#                 processedcount += 1
#                 saveproceed = 1
#
#                 if request.POST['artype'] == 'a':
#                     if get_object_or_None(Branch, code=data.branchcode) == None:
#                         faileddata.append([data.orno, 'Branch not found',])
#                         saveproceed = 0
#                     if get_object_or_None(Collector, code=data.collector) == None:
#                         faileddata.append([data.orno, 'Collector not found',])
#                         saveproceed = 0
#                     if data.payeetype == 'Y' and get_object_or_None(Customer, code=data.agencycode) == None:
#                         faileddata.append([data.orno, 'Customer(Agency) not found',])
#                         saveproceed = 0
#                     elif data.payeetype == 'C' and get_object_or_None(Customer, code=data.clientcode) == None:
#                         faileddata.append([data.orno, 'Customer(Client) not found',])
#                         saveproceed = 0
#
#                     if saveproceed == 1:
#                         Ormain.objects.create(
#                             ornum=str(data.orno),
#                             ordate=data_date,
#                             ortype=get_object_or_None(Ortype, code='AR'),
#                             orsource='A',
#                             prnum=data.prno if data.prno != '' else None,
#                             collector=get_object_or_None(Collector, code=data.collector),
#                             collector_code=Collector.objects.get(code=data.collector).code,
#                             collector_name=Collector.objects.get(code=data.collector).name,
#                             branch=get_object_or_None(Branch, code=data.branchcode),
#                             payee_type='AG' if data.payeetype == 'Y' else 'C',
#                             adtype=get_object_or_None(Adtype, code=data.adtype),
#                             agency=get_object_or_None(Customer, code=data.agencycode),
#                             client=get_object_or_None(Customer, code=data.clientcode),
#                             payee_code=data.agencycode if data.payeetype == 'Y' else data.clientcode,
#                             payee_name=data.payeename if data.payeename != '' else None,
#                             outputvattype=get_object_or_None(Outputvattype, pk=2),
#                             deferredvat='N',
#                             currency=get_object_or_None(Currency, symbol='PHP'),
#                             fxrate=1.00,
#                             wtaxamount=data.totalwtax if data.totalwtax != '' else None,
#                             amount=data.amount,
#                             amountinwords=data.amountinwords,
#                             particulars=data.particulars if data.particulars != '' else None,
#                             orstatus='F',
#                             government='G' if data.gov == '1' else 'NG' if data.gov == '0' else 'M',
#                             status='A',
#                             enterby=request.user,
#                             enterdate=datetime.now(),
#                             modifyby=request.user,
#                             modifydate=datetime.now(),
#                             isdeleted=0,
#                             print_ctr=0,
#                             initmark=data.initmark if data.initmark != '' else None,
#                             glsmark=data.glsmark if data.glsmark != '' else None,
#                             glsdate=data.glsdate if data.glsdate != '' else None,
#                             importornum=data.orno,
#                             importordate=data_date,
#                             importdate=datetime.now(),
#                             importby=request.user,
#                         ).save()
#                         successdata.append(data.orno)
#                         successcount += 1
#                     else:
#                         failedcount += 1
#
#                 elif request.POST['artype'] == 'c':
#                     # if get_object_or_None(Branch, code=data.branchcode) == None:
#                     #     faileddata.append([data.orno, 'Branch not found',])
#                     #     saveproceed = 0
#                     if get_object_or_None(Collector, code=data.collector) == None:
#                         faileddata.append([data.orno, 'Collector not found',])
#                         saveproceed = 0
#                     if get_object_or_None(Agent, code=data.agentcode) == None:
#                         faileddata.append([data.orno, 'Agent not found',])
#                         saveproceed = 0
#
#                     if saveproceed == 1:
#                         Ormain.objects.create(
#                             ornum=str(ornum),
#                             ordate=data_date,
#                             ortype=get_object_or_None(Ortype, code='AR'),
#                             orsource='C',
#                             prnum=data.prno if data.prno != '' else None,
#                             collector=get_object_or_None(Collector, code=data.collector),
#                             collector_code=Collector.objects.get(code=data.collector).code,
#                             collector_name=Collector.objects.get(code=data.collector).name,
#                             # branch=get_object_or_None(Branch, code=data.branchcode),
#                             branch=get_object_or_None(Branch, code='HO'),
#                             payee_type='A',
#                             agent=get_object_or_None(Agent, code=data.agentcode),
#                             payee_code=data.agentcode,
#                             payee_name=data.payeename if data.payeename != '' else None,
#                             outputvattype=get_object_or_None(Outputvattype, pk=2),
#                             deferredvat='N',
#                             currency=get_object_or_None(Currency, symbol='PHP'),
#                             fxrate=1.00,
#                             wtaxamount=data.totalwtax if data.totalwtax != '' else None,
#                             amount=data.amount,
#                             amountinwords=data.amountinwords,
#                             particulars=data.particulars if data.particulars != '' else None,
#                             orstatus='F',
#                             government='0',
#                             status='A',
#                             enterby=request.user,
#                             enterdate=datetime.now(),
#                             modifyby=request.user,
#                             modifydate=datetime.now(),
#                             isdeleted=0,
#                             print_ctr=0,
#                             importornum=data.orno,
#                             importordate=data_date,
#                             importdate=datetime.now(),
#                             importby=request.user,
#                         ).save()
#                         successdata.append(data.orno)
#                         successcount += 1
#                     else:
#                         failedcount += 1
#
#         rate = (float(successcount) / float(processedcount)) * 100
#         data = {
#             'result': 'success',
#             'processedcount': processedcount,
#             'successcount': successcount,
#             'successdata': successdata,
#             'failedcount': failedcount,
#             'faileddata': faileddata,
#             'rate': rate,
#         }
#         return JsonResponse(data)


def progressVerify(current, total):
    max_age = 60
    expires = datetime.strftime(datetime.utcnow() + timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
    progress = int((float(current) / float(total)) * 100)
