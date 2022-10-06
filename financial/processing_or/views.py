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
from wtax.models import Wtax
from bankaccount.models import Bankaccount
from chartofaccount.models import Chartofaccount
from customer.models import Customer
from product.models import Product
from agent.models import Agent
from outputvattype.models import Outputvattype
from outputvat.models import Outputvat
from currency.models import Currency
from adtype.models import Adtype
from companyparameter.models import Companyparameter
from circulationpaytype.models import Circulationpaytype
from productgroupcategory.models import Productgroupcategory
from circulationproduct.models import Circulationproduct
from productgroup.models import Productgroup
from agenttype.models import Agenttype
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
import re


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
        #   7: failed - some file array columns does not match requirement

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
                        breakmain = 0
                        breakstatus = 0
                        status_total = len(open(settings.MEDIA_ROOT + '/' + upload_directory + str(sequence) + ".txt").readlines(  ))
                        with open(settings.MEDIA_ROOT + '/' + upload_directory + str(sequence) + ".txt") as textFile:
                            for line in textFile:
                                orcount += 1
                                data = line.split("\t")

                                for n, i in enumerate(data):
                                    data[n] = data[n].replace('"', '')

                                print len(data)
                                print str(data[0])
                                print data[13]
                                print breakmain
                                print breakstatus
                                if len(data) > 37 and breakmain == 0:
                                    status_percentage = str(int((float(orcount) / float(status_total)) * 100))
                                    print "(1/2 - " + status_percentage + "%) Processing: " + data[0]

                                    # log status filtering
                                    if Logs_ormain.objects.filter(orno=data[0], importstatus='P'):
                                        importstatus = 'F'
                                        importremarks = 'Skipped: Already posted'
                                    elif Logs_ormain.objects.filter(orno=data[0], batchkey=batchkey, importstatus='S'):
                                        importstatus = 'F'
                                        importremarks = 'Skipped: Already exists in this batch'
                                    elif not Bankaccount.objects.filter(code=data[13]):
                                        print '**'
                                        print data[13]
                                        print '***'
                                        print data[14]
                                        print '****'
                                        importstatus = 'F'
                                        importremarks = 'Failed: Bank account does not exist'
                                        print 'Failed: Bank account does not exist'
                                        breakmain = 1
                                    elif not Adtype.objects.filter(code=data[6]):
                                        importstatus = 'F'
                                        importremarks = 'Failed: Adtype does not exist'
                                        print 'Failed: Adtype does not exist'
                                        breakmain = 1
                                    elif not Customer.objects.filter(code=data[7] if data[7] else data[8]):
                                        importstatus = 'F'
                                        importremarks = 'Failed: Customer does not exist, please upload Client/Agency'
                                        print 'Failed: Customer does not exist, please upload Client/Agency'
                                        breakmain = 1
                                    elif not Vat.objects.filter(code=data[33]):
                                        print data[30]
                                        print data[31]
                                        print data[32]
                                        print data[33]
                                        importstatus = 'F'
                                        importremarks = 'Failed: Vat Type does not exist'
                                        print 'Failed: Vat Type does not exist'
                                        breakmain = 1
                                    elif not Circulationproduct.objects.filter(code=data[35]):
                                        importstatus = 'F'
                                        importremarks = 'Failed: Circulation Product does not exist'
                                        print 'Failed: Circulation Product does not exist'
                                        breakmain = 1
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
                                    accttype = data[3].lower()
                                    if data[3].lower() == 'd':
                                        accttype = 'r'
                                    Logs_ormain.objects.create(
                                        orno=data[0],
                                        ordate=data[1],
                                        prno=data[2],
                                        ##accounttype=data[3].lower(),
                                        accounttype=accttype,
                                        collector=unicode_escape(data[4]),
                                        collectordesc=unicode_escape(data[31]),
                                        payeetype=data[5],
                                        adtype=data[6],
                                        agencycode=data[7],
                                        clientcode=data[8],
                                        agentcode=data[9],
                                        payeename=unicode_escape(data[10]),
                                        amount=data[11],
                                        amountinwords=data[12],
                                        vatcode=data[33],
                                        vatrate=data[34],
                                        bankaccount=data[13],
                                        particulars=unicode_escape(data[14]),
                                        artype=data[15],
                                        status=data[16],
                                        statusdate=data[17],
                                        enterby=unicode_escape(data[18]),
                                        enterdate=data[19],
                                        product=unicode_escape(data[35]),
                                        initmark=data[21],
                                        glsmark=data[22],
                                        glsdate=data[23],
                                        totalwtax=data[24],
                                        wtaxrate=data[36],
                                        gov=data[25],
                                        branchcode=data[26],
                                        address1=unicode_escape(data[27]),
                                        address2=unicode_escape(data[28]),
                                        address3=unicode_escape(data[29]),
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
                            if breakstatus == 0 and breakmain == 0:
                                orcountd = 0
                                status_total = len(open(settings.MEDIA_ROOT + '/' + upload_d_directory + str(sequence) + ".txt").readlines())
                                with open(settings.MEDIA_ROOT + '/' + upload_d_directory + str(sequence) + ".txt") as textFile2:
                                    for line in textFile2:
                                        orcountd += 1
                                        data = line.split("\t")
                                        for n, i in enumerate(data):
                                            data[n] = data[n].replace('"', '')

                                        if len(data) == 19:
                                            status_percentage = str(int((float(orcountd) / float(status_total)) * 100))
                                            print "(2/2 - " + status_percentage + "%) Processing: " + data[0]

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
                            if breakstatus == 0 or breakmain == 1:    # 5
                                ordata_list = []
                                ordata_d_list = []

                                ordata = Logs_ormain.objects.filter(batchkey=batchkey).order_by('importstatus', 'orno')
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
                                    totalassignamount = 0
                                    totalvatamount = 0

                                    def RepresentsInt(assignamount):
                                        try:
                                            int(s)
                                            return True
                                        except ValueError:
                                            return False

                                    if RepresentsInt:
                                        if data.assignamount:
                                            totalassignamount = float(data.assignamount)


                                    def RepresentsInt(assignvatamount):
                                        try:
                                            int(s)
                                            return True
                                        except ValueError:
                                            return False

                                    if RepresentsInt:
                                        if data.assignvatamount:
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
        elif request.POST['or_artype'] == 'c':  # 6
            if request.FILES['or_file'] \
                    and request.FILES['or_file'].name.endswith('.txt') \
                    and request.FILES['or_d_file'] \
                    and request.FILES['or_d_file'].name.endswith('.txt'):  # 3
                if request.FILES['or_file']._size < float(upload_size) * 1024 * 1024 \
                        and request.FILES['or_d_file']._size < float(upload_size) * 1024 * 1024:

                    sequence = datetime.now().isoformat().replace(':', '-')
                    batchkey = generatekey(1)

                    if storeupload(request.FILES['or_file'], sequence, 'txt', upload_directory) \
                            and storeupload(request.FILES['or_d_file'], sequence, 'txt',
                                            upload_d_directory):  # 2
                        orcount = 0
                        breakmain = 0
                        status_total = len(open(settings.MEDIA_ROOT + '/' + upload_directory + str(sequence) + ".txt").readlines())

                        with open(settings.MEDIA_ROOT + '/' + upload_directory + str(
                                sequence) + ".txt") as textFile:
                            for line in textFile:
                                orcount += 1
                                data = line.split("\t")

                                print 'len'
                                print len(data)

                                for n, i in enumerate(data):
                                    data[n] = data[n].replace('"', '')

                                if len(data) == 22 and breakmain == 0:
                                    status_percentage = str(int((float(orcount) / float(status_total)) * 100))
                                    print "(1/2 - " + status_percentage + "%) Processing: " + data[0]

                                    # log status filtering
                                    if Logs_ormain.objects.filter(orno=data[0], importstatus='P'):
                                        importstatus = 'F'
                                        importremarks = 'Skipped: Already posted'
                                    elif Logs_ormain.objects.filter(orno=data[0], batchkey=batchkey, importstatus='S'):
                                        importstatus = 'F'
                                        importremarks = 'Skipped: Already exists in this batch'
                                    elif not Bankaccount.objects.filter(code=data[13]):
                                        print '**'
                                        print data[13]
                                        print '**'
                                        importstatus = 'F'
                                        importremarks = 'Failed: Bank account does not exist'
                                        breakmain = 1
                                    elif not Circulationpaytype.objects.filter(code=data[6]) and data[3] is 'C':
                                        importstatus = 'F'
                                        importremarks = 'Failed: Circulation Pay Type does not exist'
                                        breakmain = 1
                                    else:
                                        importstatus = 'S'
                                        importremarks = 'Passed'

                                    if importstatus is not 'F':
                                        # new collector checking.
                                        if not Collector.objects.filter(code=data[4]):
                                            Collector.objects.create(code=data[4],
                                                                     name=data[18],
                                                                     enterby=request.user,
                                                                     modifyby=request.user)
                                        # new agent checking
                                        if not Agent.objects.filter(code=data[9]) and data[3] is 'C':
                                            Agent.objects.create(code=data[9],
                                                                 name=data[10],
                                                                 agenttype=Agenttype.objects.get(code='OTHERS'),
                                                                 enterby=request.user,
                                                                 modifyby=request.user)
                                    accttype = data[3].lower()
                                    if data[3].lower() == 'b':
                                        accttype = 's'
                                    Logs_ormain.objects.create(
                                        orno=data[0],
                                        ordate=data[1],
                                        prno=data[2],
                                        amount=data[11],
                                        amountinwords=data[12],
                                        bankaccount=data[13],
                                        particulars=unicode_escape(data[14]),
                                        ##accounttype=data[3].lower(),
                                        accounttype=accttype,
                                        vatcode='VE',
                                        vatrate=0,
                                        artype='C',
                                        collector=unicode_escape(data[4]),
                                        collectordesc=unicode_escape(data[18]),
                                        agentcode=data[9],
                                        payeename=unicode_escape(data[10]),
                                        payeetype='A',
                                        paytype=data[6],
                                        branchcode='HO',
                                        batchkey=batchkey,
                                        importstatus=importstatus,
                                        importremarks=importremarks,
                                        importby=request.user,
                                        subscription=data[21].strip(),
                                        status=data[16],
                                    ).save()
                                    breakstatus = 0
                                else:
                                    breakstatus = 1
                                    check = data[0]
                                    break

                            if breakstatus == 1:
                                data = {
                                    'result': 7,
                                    'check': check
                                }
                                return JsonResponse(data)

                            # inspect/insert detail
                            if breakstatus == 0 and breakmain == 0:
                                from django.db import connection
                                cursor = connection.cursor()
                                cursor.execute("UPDATE logs_ormain SET ordate = DATE_FORMAT(STR_TO_DATE(SUBSTRING(ordate, 1, 10), '%m/%d/%Y'), '%m/%d/%Y') WHERE batchkey = batchkey")

                                orcountd = 0
                                status_total = len(open(settings.MEDIA_ROOT + '/' + upload_d_directory + str(sequence) + ".txt").readlines())

                                with open(settings.MEDIA_ROOT + '/' + upload_d_directory + str(
                                        sequence) + ".txt") as textFile2:
                                    for line in textFile2:
                                        orcountd += 1
                                        data = line.split("\t")
                                        for n, i in enumerate(data):
                                            data[n] = data[n].replace('"', '')

                                        if len(data) == 17:
                                            status_percentage = str(int((float(orcountd) / float(status_total)) * 100))
                                            print "(2/2 - " + status_percentage + "%) Processing: " + data[0]

                                            if Logs_ormain.objects.filter(orno=data[0], batchkey=batchkey, accounttype='C'):
                                                print data[16]
                                                if not Productgroup.objects.filter(code=data[16].strip()):
                                                    importstatus = 'F'
                                                    importremarks = 'Failed: Product Group does not exist'
                                                else:
                                                    importstatus = 'S'
                                                    importremarks = 'Passed'

                                                Logs_ordetail.objects.create(
                                                    orno=data[0],
                                                    assignamount=data[4],
                                                    assignvatamount=0,
                                                    product=data[16].strip(),
                                                    batchkey=batchkey,
                                                    importstatus=importstatus,
                                                    importremarks=importremarks,
                                                    importby=request.user,
                                                ).save()
                                                breakstatus = 0
                                        else:
                                            breakstatus = 1
                                            break

                            if breakstatus == 0 or breakmain == 1:    # 5
                                ordata_list = []
                                ordata_d_list = []

                                ordata = Logs_ormain.objects.filter(batchkey=batchkey).order_by('importstatus', 'orno')
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
                                                          '',
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
            log_remarks = ''
            successdebit = 0
            successcredit = 0

            if request.POST['artype'] == 'a':
                orcount = 0
                status_total = len(ormain)
                for data in ormain:
                    vatamount = 0
                    vatable = 0
                    vatexempt = 0
                    vatzerorated = 0

                    orcount += 1
                    status_percentage = str(int((float(orcount) / float(status_total)) * 100))
                    print "(1/1 - " + status_percentage + "%) Processing: " + data.orno
                    print "ok"
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
                        importdate=data.importdate,
                        batchkey=data.batchkey,
                        status=data.status,
                        enterby=data.enterby,
                        enterdate=data.enterdate,
                        add1=data.address1,
                        add2=data.address2,
                        add3=data.address3,
                        tin=data.tin,
                        postingremarks='Processing...',
                    )
                    temp_ormain.save()

                    if (temp_ormain.accounttype == 'a' or temp_ormain.accounttype == 's') and temp_ormain.status.upper() == 'A':
                        # cash in bank
                        if data.bankaccount != 'EXDEAL': # handle exdeal
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
                            totalamount = 0
                            if ordetail:
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
                                        outputvatcode=Outputvat.objects.get(outputvattype__code='OVT-S').code,
                                        payeecode=temp_ormain.payeecode,
                                        batchkey=data.batchkey,
                                        postingremarks='Processing...',
                                    ).save()

                                    vatamount = float(vatamount) + float(data_d.assignvatamount)

                                    remainingamount = remainingamount - (float(data_d.assignamount) + float(data_d.assignvatamount))
                                    totalamount = format(float(data_d.assignamount) + float(data_d.assignvatamount), ',')
                                    remainingamount = float(format(remainingamount, '.2f'))

                                # transfer leftovers
                                if remainingamount > 0:
                                    log_remarks = "Has partially applied: <b>" + str(totalamount) + "</b><br>"
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
                                        outputvatcode=Outputvat.objects.get(outputvattype__code='OVT-S').code,
                                        payeecode=temp_ormain.payeecode,
                                        batchkey=data.batchkey,
                                        postingremarks='Processing...',
                                    ).save()
                                    vatamount = float(vatamount) + float(leftover_vatamount)

                                else:
                                    log_remarks = "Has fully applied: <b>" + str(totalamount) + "</b><br>"

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

                    elif temp_ormain.status.upper() == 'A': # if account type = 'R or D' (r/e)
                        # cash in bank
                        if data.bankaccount != 'EXDEAL':  # handle exdeal
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

                        log_remarks = "Has fully applied: <b>" + str(format(remainingamount, ',')) + "</b><br>"

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
                            outputvatcode=Outputvat.objects.get(outputvattype__code='OVT-S').code,
                            payeecode=temp_ormain.payeecode,
                            batchkey=data.batchkey,
                            postingremarks='Processing...',
                        ).save()
                        vatamount = float(vatamount) + float(re_vatamount)

                    # temp ormain to ormain
                    if temp_ormain.accounttype == 'd':
                        ortype_accounttype = 'r'
                    ##elif temp_ormain.accounttype == 'b':
                    ##    ortype_accounttype = 's'
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
                        status=temp_ormain.status.upper(),
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
                        wtax=Wtax.objects.filter(rate=int(float(temp_ormain.wtaxrate))).order_by('code').first(),   # conflict if wtax codes have same rates
                        importby=request.user,
                        importornum=temp_ormain.orno,
                        importdate=temp_ormain.importdate,
                        importordate=temp_ormain.ordate,
                        add1=temp_ormain.add1,
                        add2=temp_ormain.add2,
                        add3=temp_ormain.add3,
                        tin=temp_ormain.tin,
                        adtype=Adtype.objects.get(code=temp_ormain.adtypecode),
                        transaction_type='A',
                        outputvattype=Outputvattype.objects.get(code='OVT-S'),
                        remarks="Payee name: " + temp_ormain.payeename if temp_ormain.payeecode.upper() == 'WI' else '',
                        logs=log_remarks + "Enter by: <b>" + str(temp_ormain.enterby) + "</b><br>OR date: <b>" + str(temp_ormain.ordate) + "</b>"
                    ).save()

                    # temp ordetail to ordetail
                    temp_ordetail = Temp_ordetail.objects.filter(orno=temp_ormain.orno, batchkey=temp_ormain.batchkey, postingstatus='F')\
                                                         .values('orno', 'ordate', 'chartofaccountcode', 'payeecode', 'outputvatcode', 'vatcode', 'balancecode', 'bankaccountcode').order_by()\
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
                                amount=float(debit)+float(credit),
                                balancecode=data2['balancecode'],
                                status='A',
                                chartofaccount=Chartofaccount.objects.get(pk=data2['chartofaccountcode']),
                                customer=get_object_or_None(Customer, code=data2['payeecode']),
                                outputvat=get_object_or_None(Outputvat, code=data2['outputvatcode']),
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
                        successdebit = successdebit + datalist.debitamount
                        successcredit = successcredit + datalist.creditamount

            elif request.POST['artype'] == 'c':
                orcount = 0
                status_total = len(ormain)
                for data in ormain:
                    vatexempt = float(data.amount)
                    vatamount = 0
                    vatable = 0
                    vatzerorated = 0

                    orcount += 1
                    status_percentage = str(int((float(orcount) / float(status_total)) * 100))
                    # print "(1/1 - " + status_percentage + "%) Processing: " + data.orno

                    if data.accounttype == 'c':
                        ortype_accounttype = 'a'
                    else:
                        ortype_accounttype = data.accounttype

                    if data.status.upper() == 'C':
                        if ortype_accounttype == 's' and data.agentcode == '':
                            orpayeecode = get_object_or_None(Agent, code='SUNDRIES').code
                        elif data.agentcode == '':
                            orpayeecode = get_object_or_None(Agent, code='CANCELLED').code

                        if ortype_accounttype == 's' and data.payeename == '':
                            orpayeename = get_object_or_None(Agent, code='SUNDRIES').name
                        elif data.payeename == '':
                            orpayeename = get_object_or_None(Agent, code='CANCELLED').name

                    else:
                        orpayeecode = data.agentcode
                        orpayeename = data.payeename


                    # logsormain to tempormain
                    temp_ordate = datetime.strptime(data.ordate, '%m/%d/%Y')
                    temp_ormain = Temp_ormain.objects.create(
                        orno=data.orno,
                        ordate=temp_ordate,
                        prno=data.prno,
                        amount=data.amount,
                        amountinwords=data.amountinwords,
                        bankaccountcode=data.bankaccount,
                        particulars=data.particulars,
                        accounttype=data.accounttype,
                        vatrate=data.vatrate,
                        vatcode=data.vatcode,
                        artype=data.artype,
                        collectorcode=data.collector,
                        collectordesc=data.collectordesc,
                        agentcode=orpayeecode,
                        payeecode=orpayeecode,
                        payeename=orpayeename,
                        payeetype=data.payeetype,
                        paytype=data.paytype,
                        branchcode=data.branchcode,
                        importby=data.importby,
                        importdate=data.importdate,
                        batchkey=data.batchkey,
                        status=data.status,
                        subscription=data.subscription,
                        postingremarks='Processing...',
                    )
                    temp_ormain.save()

                    if temp_ormain.status.upper() == 'A':
                        # cash in bank
                        if data.bankaccount != 'EXDEAL':  # handle exdeal
                            Temp_ordetail.objects.create(
                                orno=data.orno,
                                ordate=temp_ordate,
                                debitamount=data.amount,
                                balancecode='D',
                                chartofaccountcode=Companyparameter.objects.get(code='PDI').coa_cashinbank.pk,
                                bankaccountcode=data.bankaccount,
                                batchkey=data.batchkey,
                                postingremarks='Processing...',
                            ).save()

                        if str(temp_ormain.subscription.strip()) == '1':
                            # transfer ordetails
                            Temp_ordetail.objects.create(
                                orno=data.orno,
                                ordate=temp_ordate,
                                creditamount=data.amount,
                                balancecode='C',
                                chartofaccountcode=Companyparameter.objects.get(code='PDI').coa_unsubscribe.pk,
                                batchkey=data.batchkey,
                                postingremarks='Processing...',
                            ).save()
                        elif temp_ormain.accounttype == 'c':
                            # transfer ordetails
                            ordetail = Logs_ordetail.objects.filter(importstatus='S', batchkey=request.POST['batchkey'], orno=data.orno)
                            for data_d in ordetail:
                                temp_category = Circulationpaytype.objects.get(code=data.paytype, isdeleted=0).category
                                print data_d.product
                                temp_product = Productgroup.objects.get(code=data_d.product, isdeleted=0)

                                temp_chartofaccount = Productgroupcategory.objects.get(category=temp_category, productgroup=temp_product)

                                Temp_ordetail.objects.create(
                                    orno=data_d.orno,
                                    ordate=temp_ordate,
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
                        status=temp_ormain.status.upper(),
                        bankaccount=Bankaccount.objects.get(code=temp_ormain.bankaccountcode),
                        branch=Branch.objects.get(code=temp_ormain.branchcode),
                        collector=Collector.objects.get(code=temp_ormain.collectorcode),
                        collector_code=temp_ormain.collectorcode,
                        collector_name=temp_ormain.collectordesc,
                        designatedapprover_id= 7, # default sir jhun
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
                        importdate=temp_ormain.importdate,
                        importordate=temp_ormain.ordate,
                        transaction_type='A',
                        outputvattype=Outputvattype.objects.get(code='OVT-G'),
                        logs="Enter by: <b>" + temp_ormain.collectordesc + "</b><br>OR date: <b>" + re.sub('\ 00:00:00$', '', str(temp_ormain.ordate)) + "</b>"
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
                            amount=float(debit) + float(credit),
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

                        successdebit = successdebit + datalist.debitamount
                        successcredit = successcredit + datalist.creditamount

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
                'successdebit': successdebit,
                'successcredit': successcredit,
            }
        else:
            data = {
                'result': 2
            }

        return JsonResponse(data)


def unicode_escape(unistr):
    """
    Tidys up unicode entities into HTML friendly entities

    Takes a unicode string as an argument

    Returns a unicode string
    """
    import htmlentitydefs
    escaped = ""

    for char in unistr:
        if ord(char) in htmlentitydefs.codepoint2name:
            name = htmlentitydefs.codepoint2name.get(ord(char))
            entity = htmlentitydefs.name2codepoint.get(name)
            # escaped +="&#" + str(entity)
            if str(entity) == '195':
                escaped += 'N'
            elif str(entity) == '177':
                escaped = escaped[:-1]
                escaped += 'n'
        else:
            escaped += char
    return strip_non_ascii(escaped)


def strip_non_ascii(string):
    ''' Returns the string without non ASCII characters'''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)
