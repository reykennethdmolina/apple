from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import Temp_jvmain, Temp_jvdetail, Logs_jvmain, Logs_jvdetail
from journalvoucher.models import Jvmain, Jvdetail
from ortype.models import Ortype
from collector.models import Collector
from branch.models import Branch
from vat.models import Vat
from bankaccount.models import Bankaccount
from chartofaccount.models import Chartofaccount
from customer.models import Customer
from department.models import Department
from product.models import Product
from agent.models import Agent
from outputvattype.models import Outputvattype
from jvsubtype.models import Jvsubtype
from jvtype.models import Jvtype
from currency.models import Currency
from adtype.models import Adtype
from companyparameter.models import Companyparameter
from circulationpaytype.models import Circulationpaytype
from productgroupcategory.models import Productgroupcategory
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
import datetime
from django.db import connection
from collections import namedtuple


upload_directory = 'processing_jv/imported_main/'
upload_d_directory = 'processing_jv/imported_detail/'
upload_size = 3

adv_headers = ["jv_m_tm_", "jv_a_tm_"]
adv_adjustment = [adv_headers[0] + "adjustment", adv_headers[1] + "adjustment"]
adv_exdeal = [adv_headers[0] + "exdeal", adv_headers[1] + "exdeal"]
adv_cancelled_ai = [adv_headers[0] + "cancelled_ai", adv_headers[1] + "cancelled_ai"]
adv_ppd = [adv_headers[0] + "ppd", adv_headers[1] + "ppd"]
adv_rar = [adv_headers[0] + "rar", adv_headers[1] + "rar"]
adv_tax = [adv_headers[0] + "tax", adv_headers[1] + "tax"]
adv_vod = [adv_headers[0] + "vod", adv_headers[1] + "vod"]
adv_si = [adv_headers[0] + "si", adv_headers[1] + "si"]

cir_headers = ["pjv_m", "pjv_a"]

sub_headers = ["jv_main_", "jv_detail_"]
sub_regular = [sub_headers[0] + "regular", sub_headers[1] + "regular"]
sub_complimentary = [sub_headers[0] + "complimentary", sub_headers[1] + "complimentary"]

today = datetime.datetime.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=1)
oth_payroll_header = str(lastMonth.strftime("%y")) + str(lastMonth.strftime("%m")) + '0003'
oth_payroll = [oth_payroll_header + "MAIN", oth_payroll_header + "DET"]


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'processing_jv/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        context['adv_adjustment'] = adv_adjustment
        context['adv_exdeal'] = adv_exdeal
        context['adv_cancelled_ai'] = adv_cancelled_ai
        context['adv_ppd'] = adv_ppd
        context['adv_rar'] = adv_rar
        context['adv_tax'] = adv_tax
        context['adv_vod'] = adv_vod
        context['adv_si'] = adv_si
        context['cir_all'] = cir_headers
        context['sub_regular'] = sub_regular
        context['sub_complimentary'] = sub_complimentary
        context['oth_payroll'] = oth_payroll

        return context


@csrf_exempt
def fileupload(request):
    if request.method == 'POST':

        # data-result definition:
        #   1: success
        #   2: failed - upload error
        #   3: failed - file error
        #   4: failed - file size too large (> 3mb)
        #   5: failed - file array columns do not match requirements
        #   6: failed - invalid upload_type


        if request.FILES['jv_file'] \
                and request.FILES['jv_file'].name.endswith('.txt') \
                and request.FILES['jv_d_file'] \
                and request.FILES['jv_d_file'].name.endswith('.txt'):     # 3
            if request.FILES['jv_file']._size < float(upload_size)*1024*1024 \
                    and request.FILES['jv_d_file']._size < float(upload_size)*1024*1024:  # 4
                sequence = datetime.datetime.today().isoformat().replace(':', '-')
                batchkey = generatekey(1)
                if storeupload(request.FILES['jv_file'], sequence, 'txt', upload_directory)\
                        and storeupload(request.FILES['jv_d_file'], sequence, 'txt', upload_d_directory):    # 2
                    jvcount = 0
                    if request.POST['upload_type'] == 'SUB-REG' or request.POST['upload_type'] == 'SUB-COM' or \
                        request.POST['upload_type'] == 'ADV-ADJ' or request.POST['upload_type'] == 'ADV-EXD' or \
                            request.POST['upload_type'] == 'ADV-CAI' or request.POST['upload_type'] == 'ADV-PPD' or \
                            request.POST['upload_type'] == 'ADV-RAR' or request.POST['upload_type'] == 'ADV-TAX' or \
                            request.POST['upload_type'] == 'ADV-VOD' or request.POST['upload_type'] == 'ADV-USI' or \
                            request.POST['upload_type'] == 'OTH-PAY':  # 6
                        with open(settings.MEDIA_ROOT + '/' + upload_directory + str(sequence) + ".txt") as textFile:
                            for line in textFile:
                                jvcount += 1
                                data = line.split("\t")
                                for n, i in enumerate(data):
                                    data[n] = data[n].replace('"', '')

                                if len(data) == 13:
                                    # log status filtering
                                    if Logs_jvmain.objects.filter(jvnum=data[1], importstatus='P',
                                                                  jvsubtype=request.POST['upload_type']):
                                        importstatus = 'F'
                                        importremarks = 'Skipped: Already posted'
                                    elif Logs_jvmain.objects.filter(jvnum=data[0], batchkey=batchkey, importstatus='S'):
                                        importstatus = 'F'
                                        importremarks = 'Skipped: Already exists in this batch'
                                    else:
                                        importstatus = 'S'
                                        importremarks = 'Passed'

                                    if request.POST['upload_type'] == 'OTH-PAY':
                                        Logs_jvmain.objects.create(
                                            jvnum=data[0],
                                            jvdate=data[1],
                                            particulars=data[6],
                                            remarks=data[7],
                                            comments=data[8],
                                            status=data[9],
                                            datecreated=data[10],
                                            datemodified=data[12],
                                            batchkey=batchkey,
                                            importstatus=importstatus,
                                            importremarks=importremarks,
                                            importby=request.user,
                                            jvsubtype=request.POST['upload_type'],
                                        ).save()
                                    else:
                                        Logs_jvmain.objects.create(
                                            jvnum=data[0],
                                            jvdate=data[1],
                                            particulars=data[2],
                                            remarks=data[3],
                                            comments=data[8],
                                            status=data[9],
                                            datecreated=data[10],
                                            datemodified=data[12],
                                            batchkey=batchkey,
                                            importstatus=importstatus,
                                            importremarks=importremarks,
                                            importby=request.user,
                                            jvsubtype=request.POST['upload_type'],
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

                                        if len(data) == 14:
                                            if Logs_jvmain.objects.filter(jvnum=data[0], batchkey=batchkey):
                                                if not Chartofaccount.objects.filter(accountcode=str(data[2]).strip()+'0000'):
                                                    importstatus = 'F'
                                                    importremarks = 'Failed: Chart of account does not exist'
                                                elif data[3].strip() != '' and not Bankaccount.objects.filter(
                                                        code=data[3].strip()):
                                                    importstatus = 'F'
                                                    importremarks = 'Failed: Bank account does not exist'
                                                elif data[4].strip() != '' and not Department.objects.filter(
                                                        code=data[4].strip()):
                                                        importstatus = 'F'
                                                        importremarks = 'Failed: Department does not exist'
                                                elif data[13].strip() != '' and not Branch.objects.filter(
                                                        code=data[13].strip()):
                                                        importstatus = 'F'
                                                        importremarks = 'Failed: Branch does not exist'
                                                else:
                                                    importstatus = 'S'
                                                    importremarks = 'Passed'



                                                # branch = ''
                                                #
                                                # if branch_enabled == 'Y':
                                                #     if data[13].strip() == '' and data[13].strip() is None:
                                                #         print data[2]
                                                #         print 'dito blank'
                                                #         #branch = data[13]
                                                #     else:
                                                #         print data[2]
                                                #         print 'hindi blank'
                                                        #branch = 'HO'
                                                #     if data3.branch.strip() != 'HO':
                                                #         print 'dito ako' + data3.branch.strip()
                                                #         finaljvdetail.branch = Branch.objects.get(
                                                #             code=data3.branch.strip())
                                                #         finaljvdetail.save(update_fields=['branch'])
                                                #     else:
                                                #         print 'def HO'
                                                #         finaljvdetail.branch = Branch.objects.get(code='HO')
                                                #         finaljvdetail.save(update_fields=['branch'])


                                                # #print data[13]
                                                # branch = ''
                                                # if branch_enabled == 'Y':
                                                #     #branch = 'HO'
                                                #     if data[13]:
                                                #         branch = 'HO'
                                                #         #print 'may laman '+data[13]
                                                #         if data[13] != 'HO':
                                                #             print 'hindi HO'
                                                #         #     branch = data[13]
                                                #         # else:
                                                #         #     print 'hindi'
                                                #             #branch = 'HO'
                                                #     # if data[13] != 'HO':
                                                #     #     branch = data[13]
                                                #     # if data[13] == '' or data[13] == None:
                                                #     #     print 'hey'
                                                #     #     branch = 'HO'
                                                #     # if data[13] != 'HO':
                                                #     #     branch = data[13]
                                                #     # else:
                                                #     #     branch = 'HO'
                                                # # else:
                                                # #     branch = ''
                                                #
                                                # print branch_enabled + ' | ' + branch

                                                Logs_jvdetail.objects.create(
                                                    jvnum=data[0],
                                                    jvdate=data[1],
                                                    chartofaccount=data[2],
                                                    bankaccount=data[3],
                                                    department=data[4],
                                                    charttype=data[5],
                                                    amount=data[6],
                                                    status=data[7],
                                                    datecreated=data[8],
                                                    datemodified=data[10],
                                                    sortnum=data[11],
                                                    branch=data[13],
                                                    batchkey=batchkey,
                                                    importstatus=importstatus,
                                                    importremarks=importremarks,
                                                    importby=request.user,
                                                ).save()

                                                # branch_enabled = Chartofaccount.objects.get(accountcode=data[2] + '0000').branch_enable
                                                # temjvdet = Logs_jvdetail.objects.get(chartofaccount=data[2],batchkey=batchkey).branch
                                                # print temjvdet
                                                #print ljvdet.pk.first(
                                                #.chartofaccount
                                                #print ljdet.branch
                                                breakstatus = 0
                                        elif len(data) == 17 and request.POST['upload_type'] == 'OTH-PAY':
                                            if Logs_jvmain.objects.filter(jvnum=data[0], batchkey=batchkey):
                                                if not Chartofaccount.objects.filter(accountcode=str(data[2]).strip()+'0000'):
                                                    importstatus = 'F'
                                                    importremarks = 'Failed: Chart of account does not exist'
                                                elif data[4].strip() != '' and not Department.objects.filter(
                                                        code=data[4].strip()):
                                                        importstatus = 'F'
                                                        importremarks = 'Failed: Department does not exist'
                                                elif data[13].strip() != '' and not Branch.objects.filter(
                                                        code=data[13].strip()):
                                                        importstatus = 'F'
                                                        importremarks = 'Failed: Branch does not exist'
                                                else:
                                                    importstatus = 'S'
                                                    importremarks = 'Passed'

                                                Logs_jvdetail.objects.create(
                                                    jvnum=data[0],
                                                    jvdate=data[1],
                                                    chartofaccount=data[2],
                                                    bankaccount=data[3],
                                                    department=data[4],
                                                    charttype=data[5],
                                                    amount=data[6],
                                                    status=data[7],
                                                    datecreated=data[8],
                                                    datemodified=data[10],
                                                    sortnum=data[11],
                                                    branch=data[13],
                                                    batchkey=batchkey,
                                                    importstatus=importstatus,
                                                    importremarks=importremarks,
                                                    importby=request.user,
                                                ).save()
                                                breakstatus = 0
                                        else:
                                            breakstatus = 1
                                            break

                            #branch_enabled = Chartofaccount.objects.filter(branch_enable='Y',accounttype='P')
                            # logs_ids = Logs_jvdetail.objects.filter(batchkey=batchkey).filter(~Q(branch__in=['PR0', 'ALA', 'ANT', 'CAB', 'CUB', 'HO', 'INT', 'MEG', 'MKT', 'SAN','NRT'])).values_list('pk', flat=True)
                            logs_ids = Logs_jvdetail.objects.filter(batchkey=batchkey,importstatus='S')

                            for lo in logs_ids:
                                if str(lo.branch).lstrip() == '':
                                    branch_enabled = Chartofaccount.objects.get(accountcode=lo.chartofaccount + '0000').branch_enable
                                    if branch_enabled == 'Y':
                                        Logs_jvdetail.objects.filter(pk=lo.id).update(branch='HO')
                                        print lo.id
                                        print 'tanga'
                                        #print lo.branch

                            if breakstatus == 0:    # 5
                                jvdata_list = []
                                jvdata_d_list = []
                                jvdata_d_total_list = []


                                # for be in branch_enabled:
                                #     ##print be.accountcode[0:6]
                                #     ll = Logs_jvdetail.objects.filter(batchkey=batchkey,chartofaccount=be.accountcode[0:6]).exclude(branch__in=['PR0','ALA','ANT','CAB','CUB','HO','INT','MEG','MKT','SAN','NRT']) #.update(branch='HO')
                                #     print ll
                                #     #ll = Logs_jvdetail.objects.filter(batchkey=batchkey,chartofaccount=be.accountcode[0:6]).filter(branch__in=['PR0','ALA','ANT','CAB','CUB','HO','INT','MEG','MKT','SAN','NRT']) #.update(branch='HO')
                                #     # for l in ll:
                                #     #     if l.branch == '':
                                #     #         print 'blank'
                                #     #     else:
                                #     #         print l.branch

                                jvdata = Logs_jvmain.objects.filter(batchkey=batchkey).order_by('jvnum')
                                jvdata_d = Logs_jvdetail.objects.filter(batchkey=batchkey).extra(
                                    select={'myinteger': 'CAST(sortnum AS SIGNED)'}
                                ).order_by('jvnum', '-myinteger')

                                jvdata_d_debit = jvdata_d.filter(charttype='D').values('jvnum').annotate(total=Sum('amount')).order_by('jvnum')
                                jvdata_d_credit = jvdata_d.filter(charttype='C').values('jvnum').annotate(total=Sum('amount')).order_by('jvnum')

                                for data in jvdata:
                                    jvdata_list.append([data.jvnum,
                                                        data.jvdate,
                                                        data.particulars,
                                                        data.importstatus,
                                                        data.importremarks,
                                                        ])
                                for data in jvdata_d:
                                    debitamount = ''
                                    creditamount = ''
                                    if data.charttype == 'D':
                                        debitamount = data.amount
                                    elif data.charttype == 'C':
                                        creditamount = data.amount
                                    jvdata_d_list.append([data.jvnum,
                                                          data.chartofaccount,
                                                          data.department,
                                                          debitamount,
                                                          creditamount,
                                                          data.importstatus,
                                                          data.bankaccount if data.bankaccount else '',
                                                          data.branch,
                                                          data.importremarks,
                                                          Chartofaccount.objects.get(accountcode=data.chartofaccount+'0000').description
                                                          ])

                                for index, data in enumerate(jvdata_d_debit):
                                    jvdata_d_total_list.append([data['jvnum'],
                                                                data['total'],
                                                                jvdata_d_credit[index]['total'],
                                                                ])

                                successcount = jvdata.filter(importstatus='S').count()
                                rate = (float(successcount) / float(jvcount)) * 100


                                #print branch_enabled
                                #Logs_jvdetail.objects.filter(batchkey=batchkey, )
                                data = {
                                    'result': 1,
                                    'upload_type': request.POST['upload_type'],
                                    'jvcount': jvcount,
                                    'jvdata_list': jvdata_list,
                                    'jvdata_d_list': jvdata_d_list,
                                    'jvdata_d_total_list': jvdata_d_total_list,
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
                            'result': 6
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
        elif request.FILES['jv_file'] \
                and request.FILES['jv_file'].name.endswith('.dbf') \
                and request.FILES['jv_d_file'] \
                and request.FILES['jv_d_file'].name.endswith('.dbf'):     # 3
            print "------------------"
            if request.FILES['jv_file']._size < float(upload_size)*1024*1024 \
                    and request.FILES['jv_d_file']._size < float(upload_size)*1024*1024:  # 4
                sequence = datetime.datetime.today().isoformat().replace(':', '-')
                batchkey = generatekey(1)
                if storeupload(request.FILES['jv_file'], sequence, 'dbf', upload_directory)\
                        and storeupload(request.FILES['jv_d_file'], sequence, 'dbf', upload_d_directory):    # 2
                    jvcount = 0
                    if request.POST['upload_type'] == 'CIR-CTR' or request.POST['upload_type'] == 'CIR-DR' or \
                        request.POST['upload_type'] == 'CIR-INCS' or request.POST['upload_type'] == 'CIR-REIM' or \
                            request.POST['upload_type'] == 'CIR-RS':  # 6
                        for data in DBF(settings.MEDIA_ROOT + '/' + upload_directory + str(sequence) + '.dbf', char_decode_errors='ignore'):
                            jvcount += 1
                            if len(data) == 13:
                                # log status filtering
                                if Logs_jvmain.objects.filter(jvdate=data['JV_DATE'], importstatus='P',
                                                              jvsubtype=request.POST['upload_type']):
                                    importstatus = 'F'
                                    importremarks = 'Skipped: Already posted'
                                elif Logs_jvmain.objects.filter(jvnum=data['JV_NUM'], batchkey=batchkey, importstatus='S'):
                                    importstatus = 'F'
                                    importremarks = 'Skipped: Already exists in this batch'
                                else:
                                    importstatus = 'S'
                                    importremarks = 'Passed'

                                Logs_jvmain.objects.create(
                                    jvnum=data['JV_NUM'],
                                    jvdate=str(data['JV_DATE']),
                                    particulars=data['JV_PART1'],
                                    remarks=data['JV_PART2'],
                                    comments=data['JV_PART3'],
                                    status=data['STATUS'],
                                    datecreated=data['STATUS_D'],
                                    datemodified=data['USER_D'],
                                    batchkey=batchkey,
                                    importstatus=importstatus,
                                    importremarks=importremarks,
                                    importby=request.user,
                                    jvsubtype=request.POST['upload_type'],
                                ).save()
                                breakstatus = 0
                            else:
                                breakstatus = 1
                                break

                        # inspect/insert detail
                        if breakstatus == 0:
                            for data in DBF(settings.MEDIA_ROOT + '/' + upload_d_directory + str(sequence) + '.dbf', char_decode_errors='ignore'):
                                if len(data) == 13:
                                    if Logs_jvmain.objects.filter(jvnum=data['JV_NUM'], batchkey=batchkey):
                                        if not Chartofaccount.objects.filter(accountcode=str(data['JV_ACCT']).strip()+'0000'):
                                            importstatus = 'F'
                                            importremarks = 'Failed: Chart of account does not exist'
                                        elif data['JV_DEPT'].strip() != '' and not Department.objects.filter(code=data['JV_DEPT'].strip()):
                                                importstatus = 'F'
                                                importremarks = 'Failed: Department does not exist'
                                        else:
                                            importstatus = 'S'
                                            importremarks = 'Passed'

                                        Logs_jvdetail.objects.create(
                                            jvnum=data['JV_NUM'],
                                            jvdate=data['JV_DATE'],
                                            chartofaccount=data['JV_ACCT'],
                                            bankaccount=data['JV_BANK'],
                                            department=data['JV_DEPT'],
                                            charttype=data['JV_CODE'],
                                            amount=data['JV_AMT'],
                                            status=data['STATUS'],
                                            datecreated=data['STATUS_D'],
                                            datemodified=data['USER_D'],
                                            sortnum=data['JV_ITEM_ID'],
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
                            jvdata_list = []
                            jvdata_d_list = []
                            jvdata_d_total_list = []

                            jvdata = Logs_jvmain.objects.filter(batchkey=batchkey).order_by('jvnum')
                            jvdata_d = Logs_jvdetail.objects.filter(batchkey=batchkey).extra(
                                select={'myinteger': 'CAST(sortnum AS SIGNED)'}
                            ).order_by('jvnum', '-myinteger')

                            jvdata_d_debit = jvdata_d.filter(charttype='D').values('jvnum').annotate(total=Sum('amount')).order_by('jvnum')
                            jvdata_d_credit = jvdata_d.filter(charttype='C').values('jvnum').annotate(total=Sum('amount')).order_by('jvnum')

                            for data in jvdata:
                                jvdata_list.append([data.jvnum,
                                                    data.jvdate,
                                                    data.particulars,
                                                    data.importstatus,
                                                    data.importremarks,
                                                    ])
                            for data in jvdata_d:
                                debitamount = ''
                                creditamount = ''
                                if data.charttype == 'D':
                                    debitamount = data.amount
                                elif data.charttype == 'C':
                                    creditamount = data.amount

                                jvdata_d_list.append([data.jvnum,
                                                      data.chartofaccount,
                                                      data.department,
                                                      debitamount,
                                                      creditamount,
                                                      data.importstatus,
                                                      data.bankaccount if data.bankaccount else '',
                                                      data.branch,
                                                      data.importremarks,
                                                      Chartofaccount.objects.get(
                                                          accountcode=data.chartofaccount + '0000').description
                                                      ])

                            for index, data in enumerate(jvdata_d_debit):
                                jvdata_d_total_list.append([data['jvnum'],
                                                            data['total'],
                                                            jvdata_d_credit[index]['total'],
                                                            ])

                            successcount = jvdata.filter(importstatus='S').count()
                            rate = (float(successcount) / float(jvcount)) * 100

                            data = {
                                'result': 1,
                                'upload_type': request.POST['upload_type'],
                                'jvcount': jvcount,
                                'jvdata_list': jvdata_list,
                                'jvdata_d_list': jvdata_d_list,
                                'jvdata_d_total_list': jvdata_d_total_list,
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
                            'result': 6
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


@csrf_exempt
def exportsave(request):
    if request.method == 'POST':
        # data-result definition:
        #   1: success
        #   2: failed - upload_type error
        print request.POST['upload_type']
        if request.POST['upload_type'] == 'SUB-REG' or request.POST['upload_type'] == 'SUB-COM' or \
                        request.POST['upload_type'] == 'ADV-ADJ' or request.POST['upload_type'] == 'ADV-EXD' or \
                        request.POST['upload_type'] == 'ADV-CAI' or request.POST['upload_type'] == 'ADV-PPD' or \
                        request.POST['upload_type'] == 'ADV-RAR' or request.POST['upload_type'] == 'ADV-TAX' or \
                        request.POST['upload_type'] == 'ADV-VOD' or request.POST['upload_type'] == 'ADV-USI' or \
                        request.POST['upload_type'] == 'OTH-PAY' or request.POST['upload_type'] == 'CIR-CTR' or \
                        request.POST['upload_type'] == 'CIR-DR' or request.POST['upload_type'] == 'CIR-INCS' or \
                        request.POST['upload_type'] == 'CIR-REIM' or request.POST['upload_type'] == 'CIR-RS':
            jvmain = Logs_jvmain.objects.filter(importstatus='S', batchkey=request.POST['batchkey'])
            jvmain_list = []
            jvdetail_list = []
            jvdetail_total_list = []

            for data in jvmain:

                # logsjvmain to tempjvmain
                temp_jvmain = Temp_jvmain.objects.create(
                    importedjvnum=data.jvnum,
                    jvdate=data.jvdate,
                    particulars=data.particulars + '; ' + data.remarks + '; ' + data.comments,
                    importby=data.importby,
                    batchkey=data.batchkey,
                    postingremarks='Processing...',
                )
                temp_jvmain.save()

                # get logsjvdetail
                jvdetail = Logs_jvdetail.objects.filter(jvnum=data.jvnum, batchkey=request.POST['batchkey'],
                                                        importstatus='S')
                for data2 in jvdetail:

                    # logsjvdetail to tempjvdetail
                    temp_jvdetail = Temp_jvdetail.objects.create(
                        item_counter=str(int(data2.sortnum)+1),
                        importedjvnum=data2.jvnum,
                        jvdate=data2.jvdate,
                        chartofaccount=data2.chartofaccount,
                        bankaccount=data2.bankaccount,
                        department=data2.department,
                        branch=data2.branch,
                        balancecode=data2.charttype,
                        debitamount=data2.amount if data2.charttype == 'D' else '0.00',
                        creditamount=data2.amount if data2.charttype == 'C' else '0.00',
                        batchkey=data2.batchkey,
                        postingremarks='Processing...',
                    )
                    temp_jvdetail.save()

                if request.POST['upload_type'] == 'OTH-PAY' or request.POST['upload_type'] == 'CIR-CTR' or \
                        request.POST['upload_type'] == 'CIR-DR' or request.POST['upload_type'] == 'CIR-INCS' or \
                        request.POST['upload_type'] == 'CIR-REIM' or request.POST['upload_type'] == 'CIR-RS':

                    # generate jvnum, get jvyear
                    if request.POST['upload_type'] == 'CIR-CTR' or request.POST['upload_type'] == 'CIR-DR' \
                            or request.POST['upload_type'] == 'CIR-INCS' or request.POST['upload_type'] == 'CIR-REIM' \
                            or request.POST['upload_type'] == 'CIR-RS':
                        dt = datetime.datetime.strptime(data.jvdate, '%Y-%m-%d')
                        temp_date = datetime.datetime.strptime(temp_jvmain.jvdate + ' 00:00:00', '%Y-%m-%d %X')
                    else:
                        dt = datetime.datetime.strptime(data.jvdate, '%m/%d/%Y')
                        temp_date = datetime.datetime.strptime(temp_jvmain.jvdate + ' 00:00:00', '%m/%d/%Y %X')

                    jvyear = dt.year

                    # num = Jvmain.objects.all().filter(jvdate__year=jvyear).count() + 1
                    # padnum = '{:06d}'.format(num)
                    # actualjvnum = str(jvyear) + str(padnum)
                    #dt = datetime.datetime.strptime(data.jvdate)
                    #jvyear = dt.year
                    #num = len(Jvmain.objects.all().filter(jvdate__year=jvyear)) + 1
                    #padnum = '{:06d}'.format(num)
                    #actualjvnum = str(jvyear) + str(padnum)
                    # num = Jvmain.objects.all().filter(jvdate__year=jvyear).aggregate(Max('jvnum'))
                    # padnum = '{:06d}'.format(num)
                    # print padnum
                    # print 'hy'
                    #yearqs = Jvmain.objects.filter(jvnum__startswith=jvyear)
                    #year = str(form.cleaned_data['jvdate'].year)
                    year = jvyear
                    yearqs = Jvmain.objects.filter(jvnum__startswith=year)

                    # if yearqs:
                    jvnumlast = lastNumber('true')
                    latestjvnum = str(jvnumlast[0])
                    print "latest: " + latestjvnum

                    jvnum = str(year)
                    # print str(int(latestapnum[4:]))
                    last = str(int(latestjvnum) + 1)

                    zero_addon = 6 - len(last)
                    for num in range(0, zero_addon):
                        jvnum += '0'

                    jvnum += last

                    actualjvnum = jvnum

                    # if yearqs:
                    #     jvnumlast = yearqs.latest('jvnum')
                    #     latestjvnum = str(jvnumlast)
                    #     print "latest: " + latestjvnum
                    #
                    #     jvnum = str(jvyear)
                    #     last = str(int(latestjvnum[4:]) + 1)
                    #     zero_addon = 6 - len(last)
                    #     for num in range(0, zero_addon):
                    #         jvnum += '0'
                    #     jvnum += last
                    #     #self.object.jvnum = jvnum
                    #     actualjvnum = jvnum
                    #     print jvnum

                    # temp jvmain to jvmain
                    finaljvmain = Jvmain.objects.create(
                        jvnum=actualjvnum,
                        jvdate=temp_date,
                        jvtype=Jvtype.objects.get(pk=1),
                        jvsubtype=Jvsubtype.objects.get(code=request.POST['upload_type']),
                        currency=Currency.objects.get(pk=1),
                        branch=Branch.objects.get(code='HO'),
                        particular=temp_jvmain.particulars,
                        enterby=temp_jvmain.importby,
                        modifyby=temp_jvmain.importby,
                        importedjvnum=temp_jvmain.importedjvnum,
                        #designatedapprover=request.user,
                        designatedapprover_id=226,
                    )
                    finaljvmain.save()
                else:
                    # generate jvnum, get jvyear
                    dt = datetime.datetime.strptime(data.jvdate, '%Y-%m-%d')
                    jvyear = dt.year
                    # num = len(Jvmain.objects.all().filter(jvdate__year=jvyear)) + 1
                    # padnum = '{:06d}'.format(num)
                    # actualjvnum = str(jvyear) + str(padnum)
                    yearqs = Jvmain.objects.filter(jvnum__startswith=jvyear)

                    year = str(jvyear)
                    yearqs = Jvmain.objects.filter(jvnum__startswith=year)

                    # if yearqs:
                    jvnumlast = lastNumber('true')
                    latestjvnum = str(jvnumlast[0])
                    print "latest: " + latestjvnum

                    jvnum = year
                    # print str(int(latestapnum[4:]))
                    last = str(int(latestjvnum) + 1)

                    zero_addon = 6 - len(last)
                    for num in range(0, zero_addon):
                        jvnum += '0'

                    jvnum += last

                    actualjvnum = jvnum

                    # temp jvmain to jvmain
                    finaljvmain = Jvmain.objects.create(
                        jvnum=actualjvnum,
                        jvdate=datetime.datetime.strptime(temp_jvmain.jvdate + ' 00:00:00', '%Y-%m-%d %X'),
                        jvtype=Jvtype.objects.get(pk=1),
                        jvsubtype=Jvsubtype.objects.get(code=request.POST['upload_type']),
                        currency=Currency.objects.get(pk=1),
                        branch=Branch.objects.get(code='HO'),
                        particular=temp_jvmain.particulars,
                        enterby=temp_jvmain.importby,
                        modifyby=temp_jvmain.importby,
                        importedjvnum=temp_jvmain.importedjvnum,
                        #designatedapprover=request.user,
                        designatedapprover_id=226,
                    )
                    finaljvmain.save()

                # temp jvdetail to jvdetail
                temp_jvdetail = Temp_jvdetail.objects.filter(importedjvnum=temp_jvmain.importedjvnum,
                                                             batchkey=temp_jvmain.batchkey, postingstatus='F')

                totaldebitamount = 0.00
                totalcreditamount = 0.00

                for data3 in temp_jvdetail:
                    finaljvdetail = Jvdetail.objects.create(
                        item_counter=data3.item_counter,
                        jvmain=finaljvmain,
                        jv_num=finaljvmain.jvnum,
                        jv_date=finaljvmain.jvdate,
                        chartofaccount=Chartofaccount.objects.get(accountcode=data3.chartofaccount+'0000'),
                        debitamount=float(data3.debitamount),
                        creditamount=float(data3.creditamount),
                        balancecode=data3.balancecode,
                        enterby=request.user,
                        modifyby=request.user,
                    )

                    finaljvdetail.save()
                    if data3.department and data3.department.strip() != '' and data3.department.strip() is not None:
                        finaljvdetail.department = Department.objects.get(code=data3.department.strip())
                        finaljvdetail.save(update_fields=['department'])
                    if data3.bankaccount and data3.bankaccount.strip() != '' and data3.bankaccount.strip() is not None:
                        finaljvdetail.bankaccount = Bankaccount.objects.get(code=data3.bankaccount.strip())
                        finaljvdetail.save(update_fields=['bankaccount'])
                    if data3.branch and data3.branch.strip() != '' and data3.branch.strip() is not None:
                        finaljvdetail.branch = Branch.objects.get(code=data3.branch.strip())
                        finaljvdetail.save(update_fields=['branch'])

                    totaldebitamount += finaljvdetail.debitamount
                    totalcreditamount += finaljvdetail.creditamount

                # save total amount in jvmain
                if round(totaldebitamount, 2) == round(totalcreditamount, 2):
                    finaljvmain.amount = totaldebitamount
                    finaljvmain.save(update_fields=['amount'])
                else:
                    print 'Total amounts for debit and credit are not equal. Jvmain Amount is not saved.'

                # set posting status to success for temp
                temp_jvmain.postingstatus = 'S'
                temp_jvmain.save()
                temp_jvdetail.update(postingstatus='S')

                # set to posted after success of jvnum and batch
                data.importstatus = 'P'
                data.save()
                Logs_jvdetail.objects.filter(batchkey=request.POST['batchkey'], jvnum=data.jvnum).update(
                    importstatus='P')

                # save for preview
                jvmain_data = Jvmain.objects.filter(jvnum=finaljvmain.jvnum, jvstatus='F', status='A')
                jvmain_data = jvmain_data.filter(Q(jvsubtype=Jvsubtype.objects.get(code='SUB-REG')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='SUB-COM')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='ADV-ADJ')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='ADV-EXD')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='ADV-CAI')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='ADV-PPD')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='ADV-RAR')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='ADV-TAX')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='ADV-VOD')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='ADV-USI')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='OTH-PAY')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='CIR-CTR')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='CIR-DR')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='CIR-INCS')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='CIR-REIM')) |
                                                 Q(jvsubtype=Jvsubtype.objects.get(code='CIR-RS'))).order_by('jvnum')

                for datalist in jvmain_data:
                    jvmain_list.append([datalist.jvnum,
                                        datalist.jvdate,
                                        datalist.importedjvnum,
                                        datalist.particular,
                                        'S',
                                        ])

                jvdetail_data = Jvdetail.objects.filter(jv_num=finaljvmain.jvnum, status='A',
                                                        isdeleted=0).order_by('-item_counter')
                for datalist in jvdetail_data:
                    jvdetail_list.append([datalist.jv_num,
                                          datalist.chartofaccount.accountcode,
                                          datalist.chartofaccount.title,
                                          datalist.department.code if datalist.department else '',
                                          datalist.department.departmentname if datalist.department else '',
                                          datalist.debitamount,
                                          datalist.creditamount,
                                          'S',
                                          datalist.bankaccount.code if datalist.bankaccount else '',
                                          datalist.bankaccount.bank.code if datalist.bankaccount else '',
                                          datalist.bankaccount.bankbranch.description if datalist.bankaccount else '',
                                          datalist.bankaccount.bankaccounttype.description if datalist.bankaccount else '',
                                          datalist.branch.code if datalist.branch else '',
                                          datalist.branch.description if datalist.branch else '',
                                          ])

                jvdata_d_debit = Jvdetail.objects.filter(jv_num=finaljvmain.jvnum, status='A', isdeleted=0).\
                    values('jv_num').annotate(total=Sum('debitamount')).order_by('jv_num')
                jvdata_d_credit = Jvdetail.objects.filter(jv_num=finaljvmain.jvnum, status='A', isdeleted=0). \
                    values('jv_num').annotate(total=Sum('creditamount')).order_by('jv_num')

                for index, value in enumerate(jvdata_d_debit):
                    jvdetail_total_list.append([value['jv_num'],
                                                value['total'],
                                                jvdata_d_credit[index]['total'],
                                                ])

            # append failed items from temp to jvmain_list, jvdetail_list
            jvmain_data = Temp_jvmain.objects.filter(batchkey=request.POST['batchkey'], postingstatus='F')
            for datalist in jvmain_data:
                jvmain_list.append(['-',
                                    datalist.jvdate,
                                    datalist.importedjvnum,
                                    datalist.particulars,
                                    'F',
                                    ])

            totalcount = Temp_jvmain.objects.filter(batchkey=request.POST['batchkey']).count()
            successcount = Temp_jvmain.objects.filter(batchkey=request.POST['batchkey'],
                                                      postingstatus='S').count()
            rate = (int(successcount) / int(totalcount)) * 100

            # delete temp
            Temp_jvmain.objects.filter(batchkey=request.POST['batchkey']).delete()
            Temp_jvdetail.objects.filter(batchkey=request.POST['batchkey']).delete()

            data = {
                'result': 1,
                'jvdata_list': jvmain_list,
                'jvdata_d_list': jvdetail_list,
                'jvdata_d_total_list': jvdetail_total_list,
                'totalcount': totalcount,
                'successcount': successcount,
                'rate': rate,
            }
        else:
            data = {
                'result': 2
            }

        return JsonResponse(data)


def lastNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  SUBSTRING(jvnum, 5) AS num FROM jvmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
