from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from accountspayable.models import Apmain, Apdetail, Apdetailbreakdown
from checkvoucher.models import Cvmain, Cvdetail, Cvdetailbreakdown
from journalvoucher.models import Jvmain, Jvdetail, Jvdetailbreakdown
from officialreceipt.models import Ormain, Ordetail, Ordetailbreakdown
from customer.models import Customer
from subledger.models import Subledger, logs_subledger
from transactionposting.models import Logs_posted
from acctentry.views import generatekey
from annoying.functions import get_object_or_None
from datetime import datetime, timedelta
from django.db.models import Q, Sum


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Subledger
    template_name = 'transactionposting/index.html'
    context_object_name = 'data_list'


@csrf_exempt
def verifytransactions(request):
    item_count = 0

    if request.method == 'POST':
        if request.POST['id_datefrom'] and request.POST['id_dateto']:
            datefrom = datetime.strptime(request.POST['id_datefrom'], "%Y-%m-%d").date()
            dateto = datetime.strptime(request.POST['id_dateto'], "%Y-%m-%d").date()
            newbatchkey = generatekey(1)
            status_success = 0
            status_skipped = 0
            status_unbalanced = 0
            status_invaliddate = 0

            validate_date = Logs_posted.objects.filter(status='P', dateto__gte=datefrom - timedelta(days=1))

            if request.POST['type'] == 'ap':
                batchkey = newbatchkey
                if 'ap' in request.POST.getlist('id_transtype[]'):
                    if datetime.today().date() > datefrom and validate_date.filter(doctype='AP').count() > 0:
                        unbalanced = Apdetail.objects.filter(apmain__apstatus='R', apmain__status='A', apmain__postby__isnull=True, apmain__postdate__isnull=True) \
                                                     .filter(apmain__apdate__gte=datefrom, apmain__apdate__lte=dateto)\
                                                     .values('apmain__apnum') \
                                                     .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),creditsum=Sum('creditamount')) \
                                                     .values('apmain__apnum', 'margin', 'apmain__apdate', 'debitsum', 'creditsum', 'apmain__pk').order_by('apmain__apnum')\
                                                     .exclude(margin=0)

                        if unbalanced.count() == 0:
                            item_count, batchkey = logap(datefrom, dateto, newbatchkey, request.user)
                            status_success = 1
                        else:
                            ub_list = []
                            for data in unbalanced:
                                ub_list.append(['/accountspayable/' + str(data['apmain__pk']) + '/update',
                                                data['apmain__apnum'],
                                                data['apmain__apdate'],
                                                data['debitsum'],
                                                data['creditsum'],
                                                data['margin'],
                                                ])
                            status_unbalanced = 1
                    else:
                        status_invaliddate = 1
                else:
                    status_skipped = 1

            elif request.POST['type'] == 'cv':
                batchkey = request.POST['batchkey']
                if 'cv' in request.POST.getlist('id_transtype[]'):
                    if datetime.today().date() > datefrom and validate_date.filter(doctype='CV').count() > 0:
                        unbalanced = Cvdetail.objects.filter(cvmain__cvstatus='R', cvmain__status='A', cvmain__postby__isnull=True, cvmain__postdate__isnull=True) \
                                                     .filter(cvmain__cvdate__gte=datefrom, cvmain__cvdate__lte=dateto)\
                                                     .values('cvmain__cvnum') \
                                                     .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),creditsum=Sum('creditamount')) \
                                                     .values('cvmain__cvnum', 'margin', 'cvmain__cvdate', 'debitsum', 'creditsum', 'cvmain__pk').order_by('cvmain__cvnum')\
                                                     .exclude(margin=0)

                        if unbalanced.count() == 0:
                            item_count, batchkey = logcv(datefrom, dateto, batchkey, request.user)
                            status_success = 1
                        else:
                            ub_list = []
                            for data in unbalanced:
                                ub_list.append(['/checkvoucher/' + str(data['cvmain__pk']) + '/update',
                                                data['cvmain__cvnum'],
                                                data['cvmain__cvdate'],
                                                data['debitsum'],
                                                data['creditsum'],
                                                data['margin'],
                                                ])
                            status_unbalanced = 1
                    else:
                        status_invaliddate = 1
                else:
                    status_skipped = 1

            elif request.POST['type'] == 'jv':
                batchkey = request.POST['batchkey']
                if 'jv' in request.POST.getlist('id_transtype[]'):
                    if datetime.today().date() > datefrom and validate_date.filter(doctype='JV').count() > 0:
                        unbalanced = Jvdetail.objects.filter(jvmain__jvstatus='R', jvmain__status='A', jvmain__postby__isnull=True, jvmain__postdate__isnull=True) \
                                                     .filter(jvmain__jvdate__gte=datefrom, jvmain__jvdate__lte=dateto)\
                                                     .values('jvmain__jvnum') \
                                                     .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),creditsum=Sum('creditamount')) \
                                                     .values('jvmain__jvnum', 'margin', 'jvmain__jvdate', 'debitsum', 'creditsum', 'jvmain__pk').order_by('jvmain__jvnum')\
                                                     .exclude(margin=0)
                        if unbalanced.count() == 0:
                            item_count, batchkey = logjv(datefrom, dateto, batchkey, request.user)
                            status_success = 1
                        else:
                            ub_list = []
                            for data in unbalanced:
                                ub_list.append(['/journalvoucher/' + str(data['jvmain__pk']) + '/update',
                                                data['jvmain__jvnum'],
                                                data['jvmain__jvdate'],
                                                data['debitsum'],
                                                data['creditsum'],
                                                data['margin'],
                                                ])
                            status_unbalanced = 1
                    else:
                        status_invaliddate = 1
                else:
                    status_skipped = 1

            elif request.POST['type'] == 'or':
                batchkey = request.POST['batchkey']
                if 'or' in request.POST.getlist('id_transtype[]'):
                    if datetime.today().date() > datefrom and validate_date.filter(doctype='OR').count() > 0:
                        unbalanced = Ordetail.objects.filter(ormain__orstatus='R', ormain__status='A', ormain__postby__isnull=True, ormain__postdate__isnull=True) \
                                                     .filter(ormain__ordate__gte=datefrom, ormain__ordate__lte=dateto)\
                                                     .values('ormain__ornum') \
                                                     .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),creditsum=Sum('creditamount')) \
                                                     .values('ormain__ornum', 'margin', 'ormain__ordate', 'debitsum', 'creditsum', 'ormain__pk').order_by('ormain__ornum')\
                                                     .exclude(margin=0)

                        if unbalanced.count() == 0:
                            item_count, batchkey = logor(datefrom, dateto, batchkey, request.user)
                            status_success = 1
                        else:
                            ub_list = []
                            for data in unbalanced:
                                ub_list.append(['/officialreceipt/' + str(data['ormain__pk']) + '/update',
                                                data['ormain__ornum'],
                                                data['ormain__ordate'],
                                                data['debitsum'],
                                                data['creditsum'],
                                                data['margin'],
                                                ])
                            status_unbalanced = 1
                    else:
                        status_invaliddate = 1
                else:
                    status_skipped = 1

            if status_success == 1:
                data = {
                    'status': 'success',
                    'response': 'success',
                    'item_count': item_count,
                    'batchkey': batchkey,
                    'message': 'Success!',
                }
            elif status_skipped == 1:
                data = {
                    'status': 'success',
                    'response': 'success',
                    'batchkey': batchkey,
                    'message': 'Skipped',
                }
            elif status_unbalanced == 1:
                data = {
                    'status': 'success',
                    'response': 'failed',
                    'message': 'Found ' + str(unbalanced.count()) + ' unbalanced entry',
                    'ub_list': ub_list,
                    'ub_type': 'OR',
                }
            elif status_invaliddate == 1:
                data = {
                    'status': 'success',
                    'response': 'failed',
                    'message': 'Date From should be a day after or within the previous POSTED DATES',
                }
        else:
            data = {
                'status': 'success',
                'response': 'failed',
                'message': 'Date From/ Date To missing',
            }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def logap(datefrom, dateto, batchkey, user):
    item = Apdetail.objects.filter(isdeleted=0, status='A', postdate__isnull=True, postby__isnull=True) \
                .filter(apmain__apstatus='R', apmain__status='A', apmain__postby__isnull=True, apmain__postdate__isnull=True) \
                .filter(apmain__apdate__gte=datefrom, apmain__apdate__lte=dateto)
    items = [
        logs_subledger(
            chartofaccount=data.chartofaccount,
            item_counter=data.item_counter,
            document_type='AP',
            document_id=data.pk,
            document_num=data.ap_num,
            document_date=data.ap_date,
            subtype=data.apmain.aptype,
            bankaccount=data.bankaccount,
            department=data.department,
            employee=data.employee,
            customer=data.customer,
            product=data.product,
            branch=data.branch,
            unit=data.unit,
            inputvat=data.inputvat,
            outputvat=data.outputvat,
            ataxcode=data.ataxcode,
            atccode=data.ataxcode.code if data.ataxcode else None,
            atcrate=data.ataxcode.rate if data.ataxcode else None,
            vat=data.vat,
            vatcode=data.vat.code if data.vat else None,
            vatrate=data.vat.rate if data.vat else None,
            wtax=data.wtax,
            wtaxcode=data.wtax.code if data.wtax else None,
            wtaxrate=data.wtax.rate if data.wtax else None,
            balancecode=data.balancecode,
            amount=data.debitamount if data.balancecode == 'D' else data.creditamount,
            particulars=data.apmain.particulars,
            remarks=data.apmain.remarks,
            # document_refnum=data.apmain.refno
            # document_refapnum=data.apmain.
            # document_refapdate=data.apmain. da
            document_status=data.apmain.status,
            document_supplier=data.apmain.payee,
            document_supplieratc=data.apmain.payee.atc if data.apmain.payee else None,
            document_supplieratccode=data.apmain.payee.atc.code if data.apmain.payee else None,
            document_supplieratcrate=data.apmain.payee.atc.rate if data.apmain.payee else None,
            document_suppliervat=data.apmain.payee.vat if data.apmain.payee else None,
            document_suppliervatcode=data.apmain.payee.vat.code if data.apmain.payee else None,
            document_suppliervatrate=data.apmain.payee.vat.rate if data.apmain.payee else None,
            document_supplierinputvat=data.apmain.payee.inputvat if data.apmain.payee else None,
            document_branch=data.apmain.branch,
            document_payee=data.apmain.payeename,
            document_amount=data.apmain.amount,
            document_duedate=data.apmain.duedate,
            document_currency=data.apmain.currency,
            document_fxrate=data.apmain.fxrate,
            enterby=user,
            modifyby=user,
            batchkey=batchkey,
        )
        for data in item
    ]
    logs_subledger.objects.bulk_create(items)

    # breakdown
    item_breakdown = Apdetailbreakdown.objects.filter(isdeleted=0, apmain__apstatus='R', apmain__status='A', apmain__postby__isnull=True,
                                                      apmain__postdate__isnull=True) \
                                              .filter(apmain__apdate__gte=datefrom, apmain__apdate__lte=dateto)
    items_breakdown = [
        logs_subledger(
            chartofaccount=data.chartofaccount,
            item_counter=data.item_counter,
            document_type='AP',
            document_id=data.pk,
            document_num=data.ap_num,
            document_date=data.ap_date,
            subtype=data.apmain.aptype,
            bankaccount=data.bankaccount,
            department=data.department,
            employee=data.employee,
            customer=data.customer,
            product=data.product,
            branch=data.branch,
            unit=data.unit,
            inputvat=data.inputvat,
            outputvat=data.outputvat,
            ataxcode=data.ataxcode,
            atccode=data.ataxcode.code if data.ataxcode else None,
            atcrate=data.ataxcode.rate if data.ataxcode else None,
            vat=data.vat,
            vatcode=data.vat.code if data.vat else None,
            vatrate=data.vat.rate if data.vat else None,
            wtax=data.wtax,
            wtaxcode=data.wtax.code if data.wtax else None,
            wtaxrate=data.wtax.rate if data.wtax else None,
            balancecode=data.balancecode,
            amount=data.debitamount if data.balancecode == 'D' else data.creditamount,
            particulars=data.apmain.particulars,
            remarks=data.apmain.remarks,
            # document_refnum=data.apmain.refno
            # document_refapnum=data.apmain.
            # document_refapdate=data.apmain. da
            document_status=data.apmain.status,
            document_supplier=data.apmain.payee,
            document_supplieratc=data.apmain.payee.atc if data.apmain.payee else None,
            document_supplieratccode=data.apmain.payee.atc.code if data.apmain.payee else None,
            document_supplieratcrate=data.apmain.payee.atc.rate if data.apmain.payee else None,
            document_suppliervat=data.apmain.payee.vat if data.apmain.payee else None,
            document_suppliervatcode=data.apmain.payee.vat.code if data.apmain.payee else None,
            document_suppliervatrate=data.apmain.payee.vat.rate if data.apmain.payee else None,
            document_supplierinputvat=data.apmain.payee.inputvat if data.apmain.payee else None,
            document_branch=data.apmain.branch,
            document_payee=data.apmain.payeename,
            document_amount=data.apmain.amount,
            document_duedate=data.apmain.duedate,
            document_currency=data.apmain.currency,
            document_fxrate=data.apmain.fxrate,
            enterby=user,
            modifyby=user,
            batchkey=batchkey,
            breakdownsource_id=data.apdetail.pk,
        )
        for data in item_breakdown
    ]
    logs_subledger.objects.bulk_create(items_breakdown)

    item_count = item.count() + item_breakdown.count()

    return item_count, batchkey


@csrf_exempt
def logcv(datefrom, dateto, batchkey, user):
    item = Cvdetail.objects.filter(isdeleted=0, status='A', postdate__isnull=True, postby__isnull=True) \
                .filter(cvmain__cvstatus='R', cvmain__status='A', cvmain__postby__isnull=True, cvmain__postdate__isnull=True) \
                .filter(cvmain__cvdate__gte=datefrom, cvmain__cvdate__lte=dateto)
    items = [
        logs_subledger(
            chartofaccount=data.chartofaccount,
            item_counter=data.item_counter,
            document_type='CV',
            document_id=data.pk,
            document_num=data.cv_num,
            document_date=data.cv_date,
            subtype=data.cvmain.cvtype,
            bankaccount=data.bankaccount,
            department=data.department,
            employee=data.employee,
            customer=data.customer,
            product=data.product,
            branch=data.branch,
            unit=data.unit,
            inputvat=data.inputvat,
            outputvat=data.outputvat,
            ataxcode=data.ataxcode,
            atccode=data.ataxcode.code if data.ataxcode else None,
            atcrate=data.ataxcode.rate if data.ataxcode else None,
            vat=data.vat,
            vatcode=data.vat.code if data.vat else None,
            vatrate=data.vat.rate if data.vat else None,
            wtax=data.wtax,
            wtaxcode=data.wtax.code if data.wtax else None,
            wtaxrate=data.wtax.rate if data.wtax else None,
            balancecode=data.balancecode,
            amount=data.debitamount if data.balancecode == 'D' else data.creditamount,
            particulars=data.cvmain.particulars,
            remarks=data.cvmain.remarks,
            document_status=data.cvmain.status,
            document_supplier=data.cvmain.payee,
            document_supplieratc=data.cvmain.payee.atc if data.cvmain.payee else None,
            document_supplieratccode=data.cvmain.payee.atc.code if data.cvmain.payee else None,
            document_supplieratcrate=data.cvmain.payee.atc.rate if data.cvmain.payee else None,
            document_suppliervat=data.cvmain.payee.vat if data.cvmain.payee else None,
            document_suppliervatcode=data.cvmain.payee.vat.code if data.cvmain.payee else None,
            document_suppliervatrate=data.cvmain.payee.vat.rate if data.cvmain.payee else None,
            document_supplierinputvat=data.cvmain.payee.inputvat if data.cvmain.payee else None,
            document_branch=data.cvmain.branch,
            document_payee=data.cvmain.payee_name,
            document_bankaccount=data.cvmain.bankaccount,
            document_checknum=data.cvmain.checknum,
            document_checkdate=data.cvmain.checkdate,
            document_amount=data.cvmain.amount,
            document_currency=data.cvmain.currency,
            document_fxrate=data.cvmain.fxrate,
            enterby=user,
            modifyby=user,
            batchkey=batchkey,
        )
        for data in item
    ]
    logs_subledger.objects.bulk_create(items)

    # breakdown
    item_breakdown = Cvdetailbreakdown.objects.filter(isdeleted=0, cvmain__cvstatus='R', cvmain__status='A', cvmain__postby__isnull=True, cvmain__postdate__isnull=True) \
                        .filter(cvmain__cvdate__gte=datefrom, cvmain__cvdate__lte=dateto)
    items_breakdown = [
        logs_subledger(
            chartofaccount=data.chartofaccount,
            item_counter=data.item_counter,
            document_type='CV',
            document_id=data.pk,
            document_num=data.cv_num,
            document_date=data.cv_date,
            subtype=data.cvmain.cvtype,
            bankaccount=data.bankaccount,
            department=data.department,
            employee=data.employee,
            customer=data.customer,
            product=data.product,
            branch=data.branch,
            unit=data.unit,
            inputvat=data.inputvat,
            outputvat=data.outputvat,
            ataxcode=data.ataxcode,
            atccode=data.ataxcode.code if data.ataxcode else None,
            atcrate=data.ataxcode.rate if data.ataxcode else None,
            vat=data.vat,
            vatcode=data.vat.code if data.vat else None,
            vatrate=data.vat.rate if data.vat else None,
            wtax=data.wtax,
            wtaxcode=data.wtax.code if data.wtax else None,
            wtaxrate=data.wtax.rate if data.wtax else None,
            balancecode=data.balancecode,
            amount=data.debitamount if data.balancecode == 'D' else data.creditamount,
            particulars=data.cvmain.particulars,
            remarks=data.cvmain.remarks,
            document_status=data.cvmain.status,
            document_supplier=data.cvmain.payee,
            document_supplieratc=data.cvmain.payee.atc if data.cvmain.payee else None,
            document_supplieratccode=data.cvmain.payee.atc.code if data.cvmain.payee else None,
            document_supplieratcrate=data.cvmain.payee.atc.rate if data.cvmain.payee else None,
            document_suppliervat=data.cvmain.payee.vat if data.cvmain.payee else None,
            document_suppliervatcode=data.cvmain.payee.vat.code if data.cvmain.payee else None,
            document_suppliervatrate=data.cvmain.payee.vat.rate if data.cvmain.payee else None,
            document_supplierinputvat=data.cvmain.payee.inputvat if data.cvmain.payee else None,
            document_branch=data.cvmain.branch,
            document_payee=data.cvmain.payee_name,
            document_bankaccount=data.cvmain.bankaccount,
            document_checknum=data.cvmain.checknum,
            document_checkdate=data.cvmain.checkdate,
            document_amount=data.cvmain.amount,
            document_currency=data.cvmain.currency,
            document_fxrate=data.cvmain.fxrate,
            enterby=user,
            modifyby=user,
            batchkey=batchkey,
            breakdownsource_id=data.cvdetail.pk,
        )
        for data in item_breakdown
    ]
    logs_subledger.objects.bulk_create(items_breakdown)

    item_count = item.count() + item_breakdown.count()

    return item_count, batchkey


@csrf_exempt
def logjv(datefrom, dateto, batchkey, user):
    item = Jvdetail.objects.filter(isdeleted=0, status='A', postdate__isnull=True, postby__isnull=True) \
                .filter(jvmain__jvstatus='R', jvmain__status='A', jvmain__postby__isnull=True, jvmain__postdate__isnull=True) \
                .filter(jvmain__jvdate__gte=datefrom, jvmain__jvdate__lte=dateto)
    items = [
        logs_subledger(
            chartofaccount=data.chartofaccount,
            item_counter=data.item_counter,
            document_type='JV',
            document_id=data.pk,
            document_num=data.jv_num,
            document_date=data.jv_date,
            subtype=data.jvmain.jvtype,
            bankaccount=data.bankaccount,
            department=data.department,
            employee=data.employee,
            customer=data.customer,
            product=data.product,
            branch=data.branch,
            unit=data.unit,
            inputvat=data.inputvat,
            outputvat=data.outputvat,
            ataxcode=data.ataxcode,
            atccode=data.ataxcode.code if data.ataxcode else None,
            atcrate=data.ataxcode.rate if data.ataxcode else None,
            vat=data.vat,
            vatcode=data.vat.code if data.vat else None,
            vatrate=data.vat.rate if data.vat else None,
            wtax=data.wtax,
            wtaxcode=data.wtax.code if data.wtax else None,
            wtaxrate=data.wtax.rate if data.wtax else None,
            balancecode=data.balancecode,
            amount=data.debitamount if data.balancecode == 'D' else data.creditamount,
            particulars=data.jvmain.particular,
            remarks=data.jvmain.remarks,
            document_status=data.jvmain.status,
            document_branch=data.jvmain.branch,
            document_amount=data.jvmain.amount,
            document_currency=data.jvmain.currency,
            document_fxrate=data.jvmain.fxrate,
            enterby=user,
            modifyby=user,
            batchkey=batchkey,
        )
        for data in item
    ]
    logs_subledger.objects.bulk_create(items)

    # breakdown
    item_breakdown = Jvdetailbreakdown.objects.filter(isdeleted=0, jvmain__jvstatus='R', jvmain__status='A', jvmain__postby__isnull=True, jvmain__postdate__isnull=True) \
                        .filter(jvmain__jvdate__gte=datefrom, jvmain__jvdate__lte=dateto)
    items_breakdown = [
        logs_subledger(
            chartofaccount=data.chartofaccount,
            item_counter=data.item_counter,
            document_type='JV',
            document_id=data.pk,
            document_num=data.jv_num,
            document_date=data.jv_date,
            subtype=data.jvmain.jvtype,
            bankaccount=data.bankaccount,
            department=data.department,
            employee=data.employee,
            customer=data.customer,
            product=data.product,
            branch=data.branch,
            unit=data.unit,
            inputvat=data.inputvat,
            outputvat=data.outputvat,
            ataxcode=data.ataxcode,
            atccode=data.ataxcode.code if data.ataxcode else None,
            atcrate=data.ataxcode.rate if data.ataxcode else None,
            vat=data.vat,
            vatcode=data.vat.code if data.vat else None,
            vatrate=data.vat.rate if data.vat else None,
            wtax=data.wtax,
            wtaxcode=data.wtax.code if data.wtax else None,
            wtaxrate=data.wtax.rate if data.wtax else None,
            balancecode=data.balancecode,
            amount=data.debitamount if data.balancecode == 'D' else data.creditamount,
            particulars=data.jvmain.particular,
            remarks=data.jvmain.remarks,
            document_status=data.jvmain.status,
            document_branch=data.jvmain.branch,
            document_amount=data.jvmain.amount,
            document_currency=data.jvmain.currency,
            document_fxrate=data.jvmain.fxrate,
            enterby=user,
            modifyby=user,
            batchkey=batchkey,
            breakdownsource_id=data.jvdetail.pk,
        )
        for data in item_breakdown
    ]
    logs_subledger.objects.bulk_create(items_breakdown)

    item_count = item.count() + item_breakdown.count()

    return item_count, batchkey


@csrf_exempt
def logor(datefrom, dateto, batchkey, user):
    item = Ordetail.objects.filter(isdeleted=0, status='A', postdate__isnull=True, postby__isnull=True) \
                .filter(ormain__orstatus='R', ormain__status='A', ormain__postby__isnull=True, ormain__postdate__isnull=True) \
                .filter(ormain__ordate__gte=datefrom, ormain__ordate__lte=dateto)
    items = [
        logs_subledger(
            chartofaccount=data.chartofaccount,
            item_counter=data.item_counter,
            document_type='OR',
            document_id=data.pk,
            document_num=data.or_num,
            document_date=data.or_date,
            subtype=data.ormain.ortype,
            bankaccount=data.bankaccount,
            department=data.department,
            employee=data.employee,
            customer=data.customer,
            product=data.product,
            branch=data.branch,
            unit=data.unit,
            inputvat=data.inputvat,
            outputvat=data.outputvat,
            ataxcode=data.ataxcode,
            atccode=data.ataxcode.code if data.ataxcode else None,
            atcrate=data.ataxcode.rate if data.ataxcode else None,
            vat=data.vat,
            vatcode=data.vat.code if data.vat else None,
            vatrate=data.vat.rate if data.vat else None,
            wtax=data.wtax,
            wtaxcode=data.wtax.code if data.wtax else None,
            wtaxrate=data.wtax.rate if data.wtax else None,
            balancecode=data.balancecode,
            amount=data.debitamount if data.balancecode == 'D' else data.creditamount,
            particulars=data.ormain.particulars,
            remarks=data.ormain.remarks,
            document_status=data.ormain.status,
            document_customer=Customer.objects.get(code=data.ormain.payee_code) if Customer.objects.filter(code=data.ormain.payee_code).count() > 0 and (data.ormain.payee_type == 'AG' or data.ormain.payee_type == 'C') else None,
            document_branch=data.ormain.branch,
            document_payee=data.ormain.payee_name,
            document_bankaccount=data.ormain.bankaccount,
            document_amount=data.ormain.amount,
            document_currency=data.ormain.currency,
            document_fxrate=data.ormain.fxrate,
            enterby=user,
            modifyby=user,
            batchkey=batchkey,
        )
        for data in item
    ]
    logs_subledger.objects.bulk_create(items)

    # breakdown
    item_breakdown = Ordetailbreakdown.objects.filter(isdeleted=0, ormain__orstatus='R', ormain__status='A', ormain__postby__isnull=True, ormain__postdate__isnull=True) \
                        .filter(ormain__ordate__gte=datefrom, ormain__ordate__lte=dateto)
    items_breakdown = [
        logs_subledger(
            chartofaccount=data.chartofaccount,
            item_counter=data.item_counter,
            document_type='OR',
            document_id=data.pk,
            document_num=data.or_num,
            document_date=data.or_date,
            subtype=data.ormain.ortype,
            bankaccount=data.bankaccount,
            department=data.department,
            employee=data.employee,
            customer=data.customer,
            product=data.product,
            branch=data.branch,
            unit=data.unit,
            inputvat=data.inputvat,
            outputvat=data.outputvat,
            ataxcode=data.ataxcode,
            atccode=data.ataxcode.code if data.ataxcode else None,
            atcrate=data.ataxcode.rate if data.ataxcode else None,
            vat=data.vat,
            vatcode=data.vat.code if data.vat else None,
            vatrate=data.vat.rate if data.vat else None,
            wtax=data.wtax,
            wtaxcode=data.wtax.code if data.wtax else None,
            wtaxrate=data.wtax.rate if data.wtax else None,
            balancecode=data.balancecode,
            amount=data.debitamount if data.balancecode == 'D' else data.creditamount,
            particulars=data.ormain.particulars,
            remarks=data.ormain.remarks,
            document_status=data.ormain.status,
            document_customer=Customer.objects.get(code=data.ormain.payee_code) if Customer.objects.filter(code=data.ormain.payee_code).count() > 0 and (data.ormain.payee_type == 'AG' or data.ormain.payee_type == 'C') else None,
            document_branch=data.ormain.branch,
            document_payee=data.ormain.payee_name,
            document_bankaccount=data.ormain.bankaccount,
            document_amount=data.ormain.amount,
            document_currency=data.ormain.currency,
            document_fxrate=data.ormain.fxrate,
            enterby=user,
            modifyby=user,
            batchkey=batchkey,
            breakdownsource_id=data.ordetail.pk,
        )
        for data in item_breakdown
    ]
    logs_subledger.objects.bulk_create(items_breakdown)

    item_count = item.count() + item_breakdown.count()

    return item_count, batchkey


@csrf_exempt
def posttransactions(request):
    skipcount = 100

    if request.method == 'POST':
        # locking/posting of transactions goes here
        items = logs_subledger.objects.filter(batchkey=request.POST['batchkey'], importstatus='S')

        print items.count()
        print items.count()
        print items.count()
        if items.count() > 0:
            # add subledger
            seq_item = items[:skipcount]
            for data in seq_item:
                if data.document_type == 'AP':
                    trans_main = Apmain.objects.filter(apnum=data.document_num, apstatus='R')
                    trans_detail = Apdetail.objects.all()
                    trans_detailbreakdown = Apdetailbreakdown.objects.all()
                elif data.document_type == 'CV':
                    trans_main = Cvmain.objects.filter(cvnum=data.document_num, cvstatus='R')
                    trans_detail = Cvdetail.objects.all()
                    trans_detailbreakdown = Cvdetailbreakdown.objects.all()
                elif data.document_type == 'JV':
                    trans_main = Jvmain.objects.filter(jvnum=data.document_num, jvstatus='R')
                    trans_detail = Jvdetail.objects.all()
                    trans_detailbreakdown = Jvdetailbreakdown.objects.all()
                elif data.document_type == 'OR':
                    trans_main = Ormain.objects.filter(ornum=data.document_num, orstatus='R')
                    trans_detail = Ordetail.objects.all()
                    trans_detailbreakdown = Ordetailbreakdown.objects.all()

                # main
                trans_main\
                    .filter(status='A', postby__isnull=True, postdate__isnull=True)\
                    .update(postby=request.user, postdate=datetime.now())

                # detail
                if data.breakdownsource_id is None:
                    trans_detail\
                        .filter(pk=data.document_id)\
                        .filter(status='A', postby__isnull=True, postdate__isnull=True)\
                        .update(postby=request.user, postdate=datetime.now())
                else:
                    trans_detailbreakdown \
                        .filter(pk=data.breakdownsource_id) \
                        .filter(status='A', postby__isnull=True, postdate__isnull=True) \
                        .update(postby=request.user, postdate=datetime.now())

                Subledger.objects.create(
                    chartofaccount=data.chartofaccount,
                    item_counter=data.item_counter,
                    document_type=data.document_type,
                    document_id=data.document_id,
                    document_num=data.document_num,
                    document_date=data.document_date,
                    subtype=data.subtype,
                    dcsubtype=data.dcsubtype,
                    bankaccount=data.bankaccount,
                    product=data.product,
                    branch=data.branch,
                    unit=data.unit,
                    inputvat=data.inputvat,
                    outputvat=data.outputvat,
                    ataxcode=data.ataxcode,
                    atccode=data.atccode,
                    atcrate=data.atcrate,
                    vat=data.vat,
                    vatcode=data.vatcode,
                    vatrate=data.vatrate,
                    wtax=data.wtax,
                    wtaxcode=data.wtaxcode,
                    wtaxrate=data.wtaxrate,
                    balancecode=data.balancecode,
                    amount=data.amount,
                    particulars=data.particulars,
                    remarks=data.remarks,
                    comments=data.comments,
                    currency=data.currency,
                    fxrate=data.fxrate,
                    fxamount=data.fxamount,
                    document_reftype=data.document_reftype,
                    document_refnum=data.document_refnum,
                    document_refdate=data.document_refdate,
                    document_refamount=data.document_refamount,
                    document_refjv=data.document_refjv,
                    document_refjvnum=data.document_refjvnum,
                    document_refjvdate=data.document_refjvdate,
                    document_refap=data.document_refap,
                    document_refapnum=data.document_refapnum,
                    document_refapdate=data.document_refapdate,
                    document_status=data.document_status,
                    document_supplier=data.document_supplier,
                    document_supplieratc=data.document_supplieratc,
                    document_supplieratccode=data.document_supplieratccode,
                    document_supplieratcrate=data.document_supplieratcrate,
                    document_suppliervat=data.document_suppliervat,
                    document_suppliervatcode=data.document_suppliervatcode,
                    document_suppliervatrate=data.document_suppliervatrate,
                    document_supplierinputvat=data.document_supplierinputvat,
                    document_customer=data.document_customer,
                    document_customervat=data.document_customervat,
                    document_customervatcode=data.document_customervatcode,
                    document_customervatrate=data.document_customervatrate,
                    document_customerwtax=data.document_customerwtax,
                    document_customerwtaxcode=data.document_customerwtaxcode,
                    document_customerwtaxrate=data.document_customerwtaxrate,
                    document_customeroutputvat=data.document_customeroutputvat,
                    document_branch=data.document_branch,
                    document_payee=data.document_payee,
                    document_bankaccount=data.document_bankaccount,
                    document_checknum=data.document_checknum,
                    document_checkdate=data.document_checkdate,
                    document_amount=data.document_amount,
                    document_duedate=data.document_duedate,
                    document_currency=data.document_currency,
                    document_fxrate=data.document_fxrate,
                    document_fxamount=data.document_fxamount,
                    document_collector=data.document_collector,
                    enterby=data.enterby,
                    modifyby=data.modifyby,
                    breakdownsource_id=data.breakdownsource_id,
                )

            # update to posted
            seq_item = items.values_list('pk', flat=True)[:skipcount]
            logs_subledger.objects.filter(pk__in=list(seq_item)).update(importstatus='P')
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            print items.count()
            percentage = int((float(skipcount) / items.count()) * 100)

        else:
            percentage = 100

        if percentage >= 100:
            percentage = 100

            for data in request.POST.getlist('id_transtype[]'):
                Logs_posted.objects.create(datefrom=datetime.strptime(request.POST['datefrom'], "%Y-%m-%d").date(),
                                           dateto=datetime.strptime(request.POST['dateto'], "%Y-%m-%d").date(),
                                           transactioncount=items.count(),
                                           status='P',
                                           postedon=datetime.now(),
                                           postedby=request.user,
                                           doctype=data.upper(),
                                           )

        data = {
            'status': 'success',
            'response': 'success',
            'total': items.count(),
            'percentage': percentage,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)
