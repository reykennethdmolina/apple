from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from annoying.functions import get_object_or_None
from datetime import datetime
from datetime import timedelta
from django.utils.crypto import get_random_string
from utils.views import wccount, storeupload
import decimal
from dbfread import DBF
from django.conf import settings
from agent.models import Agent
from agent.models import Newsboy
from agenttype.models import Agenttype
from customer.models import Customer
from customertype.models import Customertype
from industry.models import Industry
from supplier.models import Supplier
from suppliertype.models import Suppliertype
from ataxcode.models import Ataxcode
from inputvat.models import Inputvat
from inputvattype.models import Inputvattype
from vat.models import Vat
from creditterm.models import Creditterm


upload_directory = 'processing_data/'
upload_size = 3


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'processing_data/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context


@csrf_exempt
def upload(request):
    if request.method == 'POST':

        # data-result definition:
        #   1: success
        #   2: failed - upload error
        #   3: failed - file error or Type invalid
        #   4: failed - file size too large (> 3mb)
        #   5: failed - file array columns does not match requirement

        if request.FILES.get('upload_file', False):
            if request.FILES['upload_file']._size < float(upload_size)*1024*1024:
                sequence = datetime.now().isoformat().replace(':', '-')
                datacount = 0
                successcount = 0
                failedcount = 0
                successdata = []
                faileddata = []
                upload_directory = 'processing_data/'

                ########################### Agent #########################
                ########################### Agent #########################
                ########################### Agent #########################
                if request.POST['upload_type'] == 'agent' and request.FILES['upload_file'].name.endswith('.dbf'):
                    if storeupload(request.FILES['upload_file'], sequence, 'dbf', upload_directory + 'imported_agent/'):
                        breakstatus = 1
                        for data in DBF(settings.MEDIA_ROOT + '/' + upload_directory + 'imported_agent/' + str(sequence) + '.dbf', char_decode_errors='ignore'):
                            datacount += 1
                            saveproceed = 1

                            if len(data) == 3:
                                if get_object_or_None(Agenttype, code=data['AGNT_TYPE']) is None:
                                    faileddata.append([data['AGNT_CODE'] + ' - ' + data['AGNT_TYPE'], 'Agent Type does not exist',])
                                    saveproceed = 0

                                if saveproceed == 1:
                                    if get_object_or_None(Agent, code=data['AGNT_CODE']) is not None:
                                        Agent.objects.filter(code=data['AGNT_CODE']).update(
                                            agenttype=get_object_or_None(Agenttype, code=data['AGNT_TYPE']),
                                            name=data['AGNT_NAME'],
                                            status='A',
                                            enterby=request.user,
                                            modifyby=request.user,
                                            modifydate=datetime.now(),
                                        )
                                    else:
                                        Agent.objects.create(
                                            code=data['AGNT_CODE'],
                                            agenttype=get_object_or_None(Agenttype, code=data['AGNT_TYPE']),
                                            name=data['AGNT_NAME'],
                                            status='A',
                                            enterby=request.user,
                                            modifyby=request.user,
                                            enterdate=datetime.now(),
                                        ).save()

                                    successdata.append(data['AGNT_CODE'] + ' - ' + data['AGNT_TYPE'])
                                    successcount += 1
                                else:
                                    failedcount += 1

                                breakstatus = 0
                            else:
                                breakstatus = 1
                                break
                        if breakstatus == 0:
                            data = {
                                'result': 1,
                                'datacount': datacount,
                                'successcount': successcount,
                                'failedcount': failedcount,
                                'successdata': successdata,
                                'faileddata': faileddata,
                            }
                        else:
                            data = {
                                'result': 5
                            }
                    else:
                        data = {
                            'result': 2
                        }
                elif request.POST['upload_type'] == 'newsboy' and request.FILES['upload_file'].name.endswith('.dbf'):
                    print 'hoy'
                    if storeupload(request.FILES['upload_file'], sequence, 'dbf', upload_directory + 'imported_newsboy/'):
                        breakstatus = 1
                        for data in DBF(settings.MEDIA_ROOT + '/' + upload_directory + 'imported_newsboy/' + str(sequence) + '.dbf', char_decode_errors='ignore'):
                            datacount += 1
                            saveproceed = 1

                            if len(data) == 18:
                                print data['DOC_NUM']
                                newsboy = Newsboy.objects.filter(doc_num=data['DOC_NUM']).first()

                                if newsboy is None:
                                    print 'not existing'
                                    if saveproceed == 1:
                                        Newsboy.objects.create(
                                            doc_num=str(data['DOC_NUM']),
                                            doc_date=str(data['DOC_DATE']),
                                            glf_act=str(data['GLF_ACCT']),
                                            glf_code=str(data['GLF_CODE']),
                                            glf_amt=data['GLF_AMT'],
                                            glf_rem1=str(data['GLF_REM1']),
                                            glf_rem2=str(data['GLF_REM2']),
                                            glf_rem3=str(data['GLF_REM3']),
                                            status=str(data['STATUS']),
                                            status_d=str(data['STATUS_D']),
                                            user_n=str(data['USER_N']),
                                            user_d=str(data['USER_D']),
                                            item_id=str(data['ITEM_ID']),
                                            smf_code=str(data['SMF_CODE']),
                                            smf_name=str(data['SMF_NAME']),
                                            smf_atccod=str(data['SMF_ATCCOD']),
                                            doc_type=str(data['DOC_TYPE']),
                                            smf_trate=data['SMF_TRATE'],
                                            enterby=request.user,
                                            modifyby=request.user,
                                            enterdate=datetime.now(),
                                        ).save()
                                        successdata.append(data['DOC_NUM'] + ' - ' + str(data['DOC_DATE']))
                                        successcount += 1
                                    else:
                                        failedcount += 1
                                else:
                                    faileddata.append([data['DOC_NUM'] + ' - ' + str(data['DOC_DATE']), 'Doc Num exist',])
                                    saveproceed = 0
                                    failedcount += 1


                                breakstatus = 0
                            else:
                                breakstatus = 1
                                break
                        if breakstatus == 0:
                            data = {
                                'result': 1,
                                'datacount': datacount,
                                'successcount': successcount,
                                'failedcount': failedcount,
                                'successdata': successdata,
                                'faileddata': faileddata,
                            }
                        else:
                            data = {
                                'result': 5
                            }
                    else:
                        data = {
                            'result': 2
                        }
                ####################### Client/Agency #####################
                ####################### Client/Agency #####################
                ####################### Client/Agency #####################
                elif (request.POST['upload_type'] == 'agency' or request.POST['upload_type'] == 'client') \
                        and request.FILES['upload_file'].name.endswith('.txt'):
                    if request.POST['upload_type'] == 'agency':
                        upload_directory = upload_directory + 'imported_agency/'
                        customertype = get_object_or_None(Customertype, code='A')
                    else:
                        upload_directory = upload_directory + 'imported_client/'
                        customertype = get_object_or_None(Customertype, code='C')

                    if storeupload(request.FILES['upload_file'], sequence, 'txt', upload_directory):
                        breakstatus = 1

                        with open(settings.MEDIA_ROOT + '/' + upload_directory + str(sequence) + ".txt") as textFile:
                            for line in textFile:
                                datacount += 1
                                data = line.split("\t")
                                for n, i in enumerate(data):
                                    data[n] = data[n].replace('"', '')

                                saveproceed = 1
                                print len(data)
                                if len(data) == 26:
                                    if get_object_or_None(Customer, code=data[0]) is not None:
                                        Customer.objects.filter(code=data[0]).update(
                                            name=data[1],
                                            address1=data[2],
                                            address2=data[3],
                                            address3=data[4],
                                            telno1=data[5],
                                            telno2=data[6],
                                            telno3=data[7],
                                            faxno1=data[8],
                                            faxno2=data[9],
                                            tin=data[25],
                                            pagerno=data[10],
                                            payterms=data[11],
                                            creditlimit=data[12] if data[12].isdigit() else None,
                                            creditrating=data[13],
                                            remarks=data[14],
                                            multiplestatus='N',
                                            beg_amount=data[15] if data[15].isdigit() else None,
                                            beg_code=data[16],
                                            beg_date=data[17] if data[17] != '' else None,
                                            end_amount=data[18] if data[18].isdigit() else None,
                                            end_code=data[19],
                                            end_date=data[20] if data[20] != '' else None,
                                            customertype=customertype,
                                            status='A',
                                            enterby=request.user,
                                            modifyby=request.user,
                                            enterdate=datetime.now(),
                                        )
                                    else:
                                        Customer.objects.create(
                                            code=data[0],
                                            name=data[1],
                                            address1=data[2],
                                            address2=data[3],
                                            address3=data[4],
                                            telno1=data[5],
                                            telno2=data[6],
                                            telno3=data[7],
                                            faxno1=data[8],
                                            faxno2=data[9],
                                            tin=data[25],
                                            pagerno=data[10],
                                            payterms=data[11],
                                            creditlimit=data[12] if data[12].isdigit() else None,
                                            creditrating=data[13],
                                            remarks=data[14],
                                            multiplestatus='N',
                                            beg_amount=data[15] if data[15].isdigit() else None,
                                            beg_code=data[16],
                                            beg_date=data[17] if data[17] != '' else None,
                                            end_amount=data[18] if data[18].isdigit() else None,
                                            end_code=data[19],
                                            end_date=data[20] if data[20] != '' else None,
                                            customertype=customertype,
                                            status='A',
                                            enterby=request.user,
                                            modifyby=request.user,
                                            enterdate=datetime.now(),
                                        ).save()

                                    successdata.append(data[0] + ' - ' + data[1])
                                    successcount += 1
                                    breakstatus = 0
                                else:
                                    breakstatus = 1
                                    break
                        if breakstatus == 0:
                            data = {
                                'result': 1,
                                'datacount': datacount,
                                'successcount': successcount,
                                'failedcount': failedcount,
                                'successdata': successdata,
                                'faileddata': faileddata,
                            }
                        else:
                            print data[0]
                            data = {
                                'result': 5
                            }
                    else:
                        data = {
                            'result': 2
                        }
                ####################### Supplier #####################
                ####################### Supplier #####################
                ####################### Supplier #####################
                elif request.POST['upload_type'] == 'supplier' and request.FILES['upload_file'].name.endswith('.txt'):
                    upload_directory = upload_directory + 'imported_supplier/'

                    if storeupload(request.FILES['upload_file'], sequence, 'txt', upload_directory):
                        breakstatus = 1

                        with open(settings.MEDIA_ROOT + '/' + upload_directory + str(
                                sequence) + ".txt") as textFile:
                            for line in textFile:
                                datacount += 1
                                data = line.split("\t")
                                for n, i in enumerate(data):
                                    data[n] = data[n].replace('"', '')

                                saveproceed = 1
                                if len(data) == 20:
                                    print data[0]
                                    new_inputvat = data[16] if data[16] != '' else 'GOTCG'
                                    new_vatrate = data[17] if data[17] != '' else '12'
                                    new_vat = data[18] if data[18] != '' else 'VAT12'
                                    new_atc = data[14] if data[14] != '' else 'WC011'
                                    new_atcrate = data[3] if data[3] != '' else '15'
                                    if get_object_or_None(Supplier, code=data[0]) is not None:
                                        Supplier.objects.filter(code=data[0]).update(
                                            name=data[1],
                                            remarks=data[2],
                                            atcrate=new_atcrate,
                                            address1=strip_non_ascii(data[4]),
                                            address2=strip_non_ascii(data[5]),
                                            address3=strip_non_ascii(data[6]),
                                            tin=data[7],
                                            contactperson=strip_non_ascii(data[9]) + ' ' + strip_non_ascii(data[10]) + ' ' + strip_non_ascii(data[8]),
                                            ccc_code=data[11],
                                            ccc_code2=data[12],
                                            ccc_code3=data[13],
                                            atc=get_object_or_None(Ataxcode, code=new_atc),
                                            zipcode=data[15],
                                            inputvat=get_object_or_None(Inputvat, code=new_inputvat),
                                            inputvattype=get_object_or_None(Inputvat, code=new_inputvat).inputvattype,
                                            vatrate=new_vatrate,
                                            vat=get_object_or_None(Vat, code=new_vat),
                                            serv_code=data[19],
                                            creditterm=get_object_or_None(Creditterm, pk=2),
                                            industry=get_object_or_None(Industry, pk=1),
                                            status='A',
                                            modifyby=request.user,
                                            modifydate=datetime.now(),
                                        )
                                    else:
                                        Supplier.objects.create(
                                            code=data[0],
                                            name=strip_non_ascii(data[1]),
                                            remarks=data[2],
                                            atcrate=new_atcrate,
                                            address1=strip_non_ascii(data[4]),
                                            address2=strip_non_ascii(data[5]),
                                            address3=strip_non_ascii(data[6]),
                                            tin=data[7],
                                            contactperson=strip_non_ascii(data[9]) + ' ' + strip_non_ascii(data[10]) + ' ' + strip_non_ascii(data[8]),
                                            ccc_code=data[11],
                                            ccc_code2=data[12],
                                            ccc_code3=data[13],
                                            atc=get_object_or_None(Ataxcode, code=new_atc),
                                            zipcode=data[15],
                                            inputvat=get_object_or_None(Inputvat, code=new_inputvat),
                                            #inputvattype=get_object_or_None(Inputvat, code=new_inputvat).inputvattype,
                                            vatrate=new_vatrate,
                                            vat=get_object_or_None(Vat, code=new_vat),
                                            serv_code=data[19],
                                            creditterm=get_object_or_None(Creditterm, pk=2),
                                            industry=get_object_or_None(Industry, pk=1),
                                            multiplestatus='N',
                                            suppliertype=get_object_or_None(Suppliertype, pk=1),
                                            status='A',
                                            enterby=request.user,
                                            enterdate=datetime.now(),
                                        ).save()

                                    successdata.append(data[0] + ' - ' + data[1])
                                    successcount += 1
                                    breakstatus = 0
                                else:
                                    breakstatus = 1
                                    break
                        if breakstatus == 0:
                            data = {
                                'result': 1,
                                'datacount': datacount,
                                'successcount': successcount,
                                'failedcount': failedcount,
                                'successdata': successdata,
                                'faileddata': faileddata,
                            }
                        else:
                            data = {
                                'result': 5
                            }
                    else:
                        data = {
                            'result': 2
                        }
                else:
                    data = {
                        'result': 3
                    }
            else:
                data = {
                    'result': 4
                }
        else:
            data = {
                'result': 2
            }
    else:
        data = {
            'result': 2
        }
    return JsonResponse(data)


def strip_non_ascii(string):
    ''' Returns the string without non ASCII characters'''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)


@csrf_exempt
def datafix(request):
    print 'datafix'

    # agent = Agent.objects.filter(isdeleted=0).order_by('pk')
    #
    # for a in agent:
    #     print a.id
    #     newsboy = Newsboy.objects.filter(smf_code=a.code).count()
    #     print newsboy
    #     if newsboy > 0:
    #         print a.code
    #         print '______________________________________________'
    #
    #         a.agent_type = 1
    #         a.save()
    #     # if newsboy:
    #     #     print newsboy
    #     # else:
    #     #     print 'not existing'

    # agent = Agent.objects.filter(isdeleted=0, agent_type = 1).order_by('pk')
    #
    # for a in agent:
    #     print a.id
    #     print a.code
    #     # newsboy = Newsboy.objects.filter(smf_code=a.code).count()
    #     # print newsboy
    #     # if newsboy > 0:
    #     #     print a.code
    #     #     print '______________________________________________'
    #     #
    #     #     a.agent_type = 1
    #     #     a.save()
    #     # # if newsboy:
    #     # #     print newsboy
    #     # # else:
    #     # #     print 'not existing'

    data = {
        'status': 'success',
        'agent': agent,

    }
    return JsonResponse(data)

