from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import Temp_ormain
from officialreceipt.models import Ormain
from ortype.models import Ortype
from collector.models import Collector
from branch.models import Branch
from customer.models import Customer
from agent.models import Agent
from outputvattype.models import Outputvattype
from currency.models import Currency
from adtype.models import Adtype
from django.db.models import Count
from datetime import datetime
from datetime import timedelta
from annoying.functions import get_object_or_None
from utils.views import wccount, storeupload
from dbfread import DBF


upload_directory = 'processing_or/uploaded_files/ormain/'
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
        #   3: failed - file error or AR Type invalid
        #   4: failed - file size too large (> 3mb)
        #   5: failed - file array columns does not match requirement
        #   6: failed - invalid artype

        if request.POST['or_artype'] == 'a':
            if request.FILES['or_file'] and request.FILES['or_file'].name.endswith('.txt'):
                if request.FILES['or_file']._size < float(upload_size)*1024*1024:
                    try:
                        data = Temp_ormain.objects.latest('importsequence')
                        sequence = int(data.importsequence) + 1
                    except Temp_ormain.DoesNotExist:
                        sequence = 1

                    if storeupload(request.FILES['or_file'], sequence, 'txt', upload_directory):
                        orcount = 0
                        failedcount = 0

                        datatotal = wccount(upload_directory + str(sequence) + '.txt') + 1
                        datacurrent = 0

                        with open(upload_directory + str(sequence) + ".txt") as textFile:
                            for line in textFile:
                                orcount += 1
                                data = line.split("\t")
                                for n, i in enumerate(data):
                                    data[n] = data[n].replace('"', '')

                                if len(data) == 31:
                                    Temp_ormain.objects.create(
                                        orno=data[0],
                                        ordate=data[1],
                                        prno=data[2],
                                        accounttype=data[3],
                                        collector=data[4],
                                        payeetype=data[5],
                                        adtype=data[6],
                                        agencycode=data[7],
                                        clientcode=data[8],
                                        agentcode=data[9],
                                        payeename=data[10],
                                        amount=data[11],
                                        amountinwords=data[12],
                                        bankaccount=data[13],
                                        particulars=data[14],
                                        artype=data[15],
                                        status=data[16],
                                        statusdate=data[17],
                                        enterby=data[18],
                                        enterdate=data[19],
                                        product=data[20],
                                        initmark=data[21],
                                        glsmark=data[22],
                                        glsdate=data[23],
                                        totalwtax=data[24],
                                        gov=data[25],
                                        branchcode=data[26],
                                        address1=data[27],
                                        address2=data[28],
                                        address3=data[29],
                                        tin=data[30],
                                        importsequence=sequence,
                                        importby=request.user,
                                    ).save()
                                    breakstatus = 0
                                else:
                                    breakstatus = 1
                                    break
                                datacurrent += 1
                                progressVerify(datacurrent, datatotal)
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
                            progressVerify(datacurrent, datatotal)
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
        elif request.POST['or_artype'] == 'c':
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
        if request.POST['artype'] == 'a' or request.POST['artype'] == 'c':

            # get unique in temp
            temp_unique = Temp_ormain.objects.filter(importsequence=request.POST['sequence']).values_list('orno', flat=True).annotate(Count('id')).order_by().filter(id__count=1)
            # compare if exists in ormain
            main_temp_unique = Ormain.objects.filter(importornum__in=set(temp_unique)).order_by('importornum').values_list('importornum', flat=True)
            # get duplicate in temp (distinct)
            temp_duplicate = Temp_ormain.objects.filter(importsequence=request.POST['sequence']).values_list('orno', flat=True).annotate(Count('id')).order_by().filter(id__count__gt=1)
            # compare if exists in ormain
            main_temp_duplicate = Ormain.objects.filter(importornum__in=set(temp_duplicate)).order_by('importornum').values_list('importornum', flat=True)

            # subtract list to list
            temp_unique = list(map(str, set(temp_unique) - set(main_temp_unique)))
            temp_duplicate = list(map(str, set(temp_duplicate) - set(main_temp_duplicate)))

            temp_unique = list(map(str, set(Temp_ormain.objects.values_list('id', flat=True).filter(importsequence=request.POST['sequence'], orno__in=temp_unique))))
            temp_duplicate_new = []
            for data in temp_duplicate:
                or_id = Temp_ormain.objects.values_list('id', flat=True).filter(importsequence=request.POST['sequence'], orno=data).first()
                temp_duplicate_new.append(str(or_id))
            temp_data = temp_unique + temp_duplicate_new

            temp_ormain = Temp_ormain.objects.filter(importsequence=request.POST['sequence'], pk__in=temp_data)

            processedcount = 0
            successcount = 0
            successdata = []
            failedcount = 0
            faileddata = []

            for data in temp_ormain:

                if request.POST['artype'] == 'a':
                    data_date = datetime.strptime(data.ordate, '%m/%d/%Y')
                else:
                    data_date = datetime.strptime(data.ordate, '%Y-%m-%d')
                year = str(data_date.year)
                yearqs = Ormain.objects.filter(ornum__startswith=year)
                if yearqs:
                    ornumlast = yearqs.latest('ornum')
                    latestornum = str(ornumlast)
                    ornum = year
                    last = str(int(latestornum[4:]) + 1)
                    zero_addon = 6 - len(last)
                    for num in range(0, zero_addon):
                        ornum += '0'
                    ornum += last
                else:
                    ornum = year + '000001'

                processedcount += 1
                saveproceed = 1

                if request.POST['artype'] == 'a':
                    if get_object_or_None(Branch, code=data.branchcode) == None:
                        faileddata.append([data.orno, 'Branch not found',])
                        saveproceed = 0
                    if get_object_or_None(Collector, code=data.collector) == None:
                        faileddata.append([data.orno, 'Collector not found',])
                        saveproceed = 0
                    if data.payeetype == 'Y' and get_object_or_None(Customer, code=data.agencycode) == None:
                        faileddata.append([data.orno, 'Customer(Agency) not found',])
                        saveproceed = 0
                    elif data.payeetype == 'C' and get_object_or_None(Customer, code=data.clientcode) == None:
                        faileddata.append([data.orno, 'Customer(Client) not found',])
                        saveproceed = 0

                    if saveproceed == 1:
                        Ormain.objects.create(
                            ornum=str(data.orno),
                            ordate=data_date,
                            ortype=get_object_or_None(Ortype, code='AR'),
                            orsource='A',
                            prnum=data.prno if data.prno != '' else None,
                            collector=get_object_or_None(Collector, code=data.collector),
                            collector_code=Collector.objects.get(code=data.collector).code,
                            collector_name=Collector.objects.get(code=data.collector).name,
                            branch=get_object_or_None(Branch, code=data.branchcode),
                            payee_type='AG' if data.payeetype == 'Y' else 'C',
                            adtype=get_object_or_None(Adtype, code=data.adtype),
                            agency=get_object_or_None(Customer, code=data.agencycode),
                            client=get_object_or_None(Customer, code=data.clientcode),
                            payee_code=data.agencycode if data.payeetype == 'Y' else data.clientcode,
                            payee_name=data.payeename if data.payeename != '' else None,
                            outputvattype=get_object_or_None(Outputvattype, pk=2),
                            deferredvat='N',
                            currency=get_object_or_None(Currency, symbol='PHP'),
                            fxrate=1.00,
                            wtaxamount=data.totalwtax if data.totalwtax != '' else None,
                            amount=data.amount,
                            amountinwords=data.amountinwords,
                            particulars=data.particulars if data.particulars != '' else None,
                            orstatus='F',
                            government='G' if data.gov == '1' else 'NG' if data.gov == '0' else 'M',
                            status='A',
                            enterby=request.user,
                            enterdate=datetime.now(),
                            modifyby=request.user,
                            modifydate=datetime.now(),
                            isdeleted=0,
                            print_ctr=0,
                            initmark=data.initmark if data.initmark != '' else None,
                            glsmark=data.glsmark if data.glsmark != '' else None,
                            glsdate=data.glsdate if data.glsdate != '' else None,
                            importornum=data.orno,
                            importordate=data_date,
                            importdate=datetime.now(),
                            importby=request.user,
                        ).save()
                        successdata.append(data.orno)
                        successcount += 1
                    else:
                        failedcount += 1

                elif request.POST['artype'] == 'c':
                    # if get_object_or_None(Branch, code=data.branchcode) == None:
                    #     faileddata.append([data.orno, 'Branch not found',])
                    #     saveproceed = 0
                    if get_object_or_None(Collector, code=data.collector) == None:
                        faileddata.append([data.orno, 'Collector not found',])
                        saveproceed = 0
                    if get_object_or_None(Agent, code=data.agentcode) == None:
                        faileddata.append([data.orno, 'Agent not found',])
                        saveproceed = 0

                    if saveproceed == 1:
                        Ormain.objects.create(
                            ornum=str(ornum),
                            ordate=data_date,
                            ortype=get_object_or_None(Ortype, code='AR'),
                            orsource='C',
                            prnum=data.prno if data.prno != '' else None,
                            collector=get_object_or_None(Collector, code=data.collector),
                            collector_code=Collector.objects.get(code=data.collector).code,
                            collector_name=Collector.objects.get(code=data.collector).name,
                            # branch=get_object_or_None(Branch, code=data.branchcode),
                            branch=get_object_or_None(Branch, code='HO'),
                            payee_type='A',
                            agent=get_object_or_None(Agent, code=data.agentcode),
                            payee_code=data.agentcode,
                            payee_name=data.payeename if data.payeename != '' else None,
                            outputvattype=get_object_or_None(Outputvattype, pk=2),
                            deferredvat='N',
                            currency=get_object_or_None(Currency, symbol='PHP'),
                            fxrate=1.00,
                            wtaxamount=data.totalwtax if data.totalwtax != '' else None,
                            amount=data.amount,
                            amountinwords=data.amountinwords,
                            particulars=data.particulars if data.particulars != '' else None,
                            orstatus='F',
                            government='0',
                            status='A',
                            enterby=request.user,
                            enterdate=datetime.now(),
                            modifyby=request.user,
                            modifydate=datetime.now(),
                            isdeleted=0,
                            print_ctr=0,
                            importornum=data.orno,
                            importordate=data_date,
                            importdate=datetime.now(),
                            importby=request.user,
                        ).save()
                        successdata.append(data.orno)
                        successcount += 1
                    else:
                        failedcount += 1

        rate = (float(successcount) / float(processedcount)) * 100
        data = {
            'result': 'success',
            'processedcount': processedcount,
            'successcount': successcount,
            'successdata': successdata,
            'failedcount': failedcount,
            'faileddata': faileddata,
            'rate': rate,
        }
        return JsonResponse(data)    


def progressVerify(current, total):
    max_age = 60
    expires = datetime.strftime(datetime.utcnow() + timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
    progress = int((float(current) / float(total)) * 100)
