import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from subledger.models import Subledger
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from accountspayable.models import Apdetail
from checkvoucher.models import Cvdetail
from journalvoucher.models import Jvdetail
from officialreceipt.models import Ordetail
from customer.models import Customer
from subledger.models import Subledger, logs_subledger
from acctentry.views import generatekey
from annoying.functions import get_object_or_None


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Subledger
    template_name = 'transactionposting/index.html'
    context_object_name = 'data_list'


@csrf_exempt
def verifytransactions(request):
    item_count = 0

    if request.method == 'POST':
        if request.POST['type'] == 'ap':
            # date filter soon
            # validations soon
            batchkey = generatekey(1)
            item = Apdetail.objects.filter(isdeleted=0)
            item_count = item.count()
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
                    enterby=request.user,
                    modifyby=request.user,
                    batchkey=batchkey,
            )
                for data in item
            ]
            logs_subledger.objects.bulk_create(items)

        elif request.POST['type'] == 'cv':
            # date filter soon
            # validations soon
            batchkey = request.POST['batchkey']
            item = Cvdetail.objects.filter(isdeleted=0)
            item_count = item.count()
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
                    enterby=request.user,
                    modifyby=request.user,
                    batchkey=batchkey,
            )
                for data in item
            ]
            logs_subledger.objects.bulk_create(items)

        elif request.POST['type'] == 'jv':
            # date filter soon
            # validations soon
            batchkey = request.POST['batchkey']
            item = Jvdetail.objects.filter(isdeleted=0)
            item_count = item.count()
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
                    enterby=request.user,
                    modifyby=request.user,
                    batchkey=batchkey,
                )
                for data in item
            ]
            logs_subledger.objects.bulk_create(items)

        elif request.POST['type'] == 'or':
            # date filter soon
            # validations soon
            batchkey = request.POST['batchkey']
            item = Ordetail.objects.filter(isdeleted=0)
            item_count = item.count()
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
                    document_customer=Customer.objects.get(code=data.ormain.payee_code).pk if Customer.objects.filter(code=data.ormain.payee_code).count() > 0 and (data.ormain.payee_type == 'AG' or data.ormain.payee_type == 'C') else None,
                    document_branch=data.ormain.branch,
                    document_payee=data.ormain.payee_name,
                    document_bankaccount=data.ormain.bankaccount,
                    document_amount=data.ormain.amount,
                    document_currency=data.ormain.currency,
                    document_fxrate=data.ormain.fxrate,
                    enterby=request.user,
                    modifyby=request.user,
                    batchkey=batchkey,
                )
                for data in item
            ]
            logs_subledger.objects.bulk_create(items)

        # maingroup = request.POST['maingroup']
        # subgroup = MainGroupSubgroup.objects.filter(main=maingroup, isdeleted=0, sub__isdeleted=0)
        #
        # subgroup_list = []
        #
        # for data in subgroup:
        #     subgroup_list.append([data.sub.pk,
        #                           data.sub.code,
        #                           data.sub.description,
        #                           ])

        data = {
            'status': 'success',
            'response': 'success',
            'item_count': item_count,
            'batchkey': batchkey,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@csrf_exempt
def posttransactions(request):
    skipcount = 100

    if request.method == 'POST':
        sequence = int(request.POST['sequence']) + skipcount
        # locking/posting of transactions goes here

        items = logs_subledger.objects.filter(batchkey=request.POST['batchkey'])

        # update to posted
        seq_item = items.values_list('pk', flat=True)[sequence-skipcount:sequence]
        logs_subledger.objects.filter(pk__in=list(seq_item), importstatus='S').update(importstatus='P')

        # add subledger
        seq_item = items[sequence-skipcount:sequence]

        items_set=[
            Subledger(
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
            )
            for data in seq_item
        ]
        Subledger.objects.bulk_create(items_set)

        percentage = int((float(sequence) / items.count()) * 100)
        if percentage > 100:
            percentage = 100

        data = {
            'status': 'success',
            'response': 'success',
            'sequence': sequence,
            'total': items.count(),
            'percentage': percentage,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)
