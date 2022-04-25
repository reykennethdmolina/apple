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
from chartofaccount.models import Chartofaccount
from companyparameter.models import Companyparameter
from accountexpensebalance.models import Accountexpensebalance
from subledger.models import Subledger, logs_subledger
from transactionposting.models import Logs_posted
from bankaccount.models import Bankaccount
from acctentry.views import generatekey
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar
from django.db.models import F, Sum
from django.db.models.functions import Concat


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Subledger
    template_name = 'transactionposting/index.html'
    context_object_name = 'data_list'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        company = Companyparameter.objects.all().first()
        yearend_year = company.year_end_date
        context['yearend_year'] = yearend_year.year
        context['today_year'] = datetime.today().year
        context['today_month'] = datetime.today().month
        context['toclose_year'] = yearend_year.year
        context['count'] = datetime.today().year - company.year_end_date.year
        context['last'] =Companyparameter.objects.all().first().last_closed_date
        context['param'] = company

        return context


@csrf_exempt
def verifytransactions(request):
    item_count = 0

    if request.method == 'POST':
        if request.POST['id_datefrom'] and request.POST['id_dateto']:
            datefrom = datetime.strptime(request.POST['id_datefrom'], "%Y-%m-%d").date()
            dateto = datetime.strptime(request.POST['id_dateto'], "%Y-%m-%d").date()

            data = {
                'status': 'success',
                'response': 'failed',
                'message': 'Posting month invalid',
            }

            closetransaction = Companyparameter.objects.all().first().last_closed_date
            validtransaction = closetransaction + relativedelta(months=1)

            if dateto.year == validtransaction.year and dateto.month == validtransaction.month:
                newbatchkey = generatekey(1)
                status_success = 0
                status_skipped = 0
                status_unbalanced = 0
                status_invaliddate = 0
                status_undept = 0

                print 'hoy'
                validate_date = Logs_posted.objects.filter(status='P', dateto__gte=datefrom - timedelta(days=1))
                #print datefrom
                #print 'datefrom'
                #validate_date = Logs_posted.objects.filter(status='P', dateto__gte=datefrom)
                #print 'validate'
                #print validate_date

                #print datefrom - timedelta(days=1)

                if request.POST['type'] == 'ap':
                    print 'ap'
                    batchkey = newbatchkey
                    #if 'ap' in request.POST.getlist('id_transtype[]'):
                    if 'ap' in request.POST.getlist('id_transtype'):
                        if datetime.today().date() > datefrom and validate_date.filter(doctype='AP').count() > 0:
                            unbalanced = Apdetail.objects.filter(apmain__apstatus='R', apmain__status='A',
                                                                 apmain__postby__isnull=True,
                                                                 apmain__postdate__isnull=True) \
                                .filter(apmain__apdate__gte=datefrom, apmain__apdate__lte=dateto) \
                                .values('apmain__apnum') \
                                .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),
                                          creditsum=Sum('creditamount')) \
                                .values('apmain__apnum', 'margin', 'apmain__apdate', 'debitsum', 'creditsum',
                                        'apmain__pk').order_by('apmain__apnum') \
                                .exclude(margin=0)

                            # undept = Apdetail.objects.filter(apmain__apstatus='R', apmain__status='A',
                            #                                  apmain__postby__isnull=True, apmain__postdate__isnull=True) \
                            #     .filter(apmain__apdate__gte=datefrom, apmain__apdate__lte=dateto) \
                            #     .filter(department__isnull=False) \
                            #     .exclude(
                            #     department__expchartofaccount__accountcode__startswith=Concat(F('chartofaccount__main'),
                            #                                                                   F(
                            #                                                                       'chartofaccount__clas')))

                            undept_count = 0
                            undept_id = []
                            undept = Apdetail.objects.filter(apmain__apstatus='R', apmain__status='A',
                                                             apmain__postby__isnull=True, apmain__postdate__isnull=True) \
                                .filter(apmain__apdate__gte=datefrom, apmain__apdate__lte=dateto)

                            for item in undept:
                                # print str(item.id) + ' ' + str(item.department_id) + ' ' + str(item.chartofaccount_id) + ' ' + str(item.chartofaccount.accountcode) + ' ' + str(item.chartofaccount.department_enable)
                                if item.department_id is not None and item.chartofaccount.department_enable == 'N':
                                    undept_count += 1
                                    undept_id.append(item.id)
                                elif item.department_id is None and item.chartofaccount.department_enable == 'Y':
                                    undept_count += 1
                                    undept_id.append(item.id)

                            # for data in undept:
                            #     print str(data.department.expchartofaccount.accountcode) + '--' + str(
                            #         data.chartofaccount.main) + str(data.chartofaccount.clas)

                            if unbalanced.count() == 0 and undept_count == 0:
                                item_count, batchkey = logap(datefrom, dateto, newbatchkey, request.user)
                                status_success = 1
                            elif undept_count != 0:
                                ud_list = []
                                ud_type = 'AP'
                                undept = Apdetail.objects.filter(id__in=undept_id)
                                for data in undept:
                                    ud_list.append(['/accountspayable/' + str(data.apmain.pk) + '/update',
                                                    data.apmain.apnum,
                                                    data.apmain.apdate,
                                                    ])
                                status_undept = 1
                            else:
                                ub_list = []
                                ub_type = 'AP'
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
                    print 'cv'
                    batchkey = request.POST['batchkey']
                    if 'cv' in request.POST.getlist('id_transtype'):
                        if datetime.today().date() > datefrom and validate_date.filter(doctype='CV').count() > 0:
                            unbalanced = Cvdetail.objects.filter(cvmain__cvstatus='R', cvmain__status='A',
                                                                 cvmain__postby__isnull=True,
                                                                 cvmain__postdate__isnull=True) \
                                .filter(cvmain__cvdate__gte=datefrom, cvmain__cvdate__lte=dateto) \
                                .values('cvmain__cvnum') \
                                .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),
                                          creditsum=Sum('creditamount')) \
                                .values('cvmain__cvnum', 'margin', 'cvmain__cvdate', 'debitsum', 'creditsum',
                                        'cvmain__pk').order_by('cvmain__cvnum') \
                                .exclude(margin=0)

                            # undept = Cvdetail.objects.filter(cvmain__cvstatus='R', cvmain__status='A',
                            #                                  cvmain__postby__isnull=True, cvmain__postdate__isnull=True) \
                            #     .filter(cvmain__cvdate__gte=datefrom, cvmain__cvdate__lte=dateto) \
                            #     .filter(department__isnull=False) \
                            #     .exclude(
                            #     department__expchartofaccount__accountcode__startswith=Concat(F('chartofaccount__main'),
                            #                                                                   F(
                            #                                                                       'chartofaccount__clas')))

                            undept_count = 0
                            undept_id = []
                            undept = Cvdetail.objects.filter(cvmain__cvstatus='R', cvmain__status='A',
                                                             cvmain__postby__isnull=True, cvmain__postdate__isnull=True) \
                                .filter(cvmain__cvdate__gte=datefrom, cvmain__cvdate__lte=dateto)

                            for item in undept:
                                # print str(item.id) + ' ' + str(item.department_id) + ' ' + str(item.chartofaccount_id) + ' ' + str(item.chartofaccount.accountcode) + ' ' + str(item.chartofaccount.department_enable)
                                if item.department_id is not None and item.chartofaccount.department_enable == 'N':
                                    undept_count += 1
                                    undept_id.append(item.id)
                                elif item.department_id is None and item.chartofaccount.department_enable == 'Y':
                                    undept_count += 1
                                    undept_id.append(item.id)

                            if unbalanced.count() == 0 and undept_count == 0:
                                item_count, batchkey = logcv(datefrom, dateto, batchkey, request.user)
                                status_success = 1
                            elif undept_count != 0:
                                ud_list = []
                                ud_type = 'CV'
                                undept = Cvdetail.objects.filter(id__in=undept_id)
                                for data in undept:
                                    ud_list.append(['/checkvoucher/' + str(data.cvmain.pk) + '/update',
                                                    data.cvmain.cvnum,
                                                    data.cvmain.cvdate,
                                                    ])
                                status_undept = 1
                            else:
                                ub_list = []
                                ub_type = 'CV'
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
                    print 'jv'
                    batchkey = request.POST['batchkey']
                    if 'jv' in request.POST.getlist('id_transtype'):
                        if datetime.today().date() > datefrom and validate_date.filter(doctype='JV').count() > 0:
                            unbalanced = Jvdetail.objects.filter(jvmain__jvstatus='R', jvmain__status='A',
                                                                 jvmain__postby__isnull=True,
                                                                 jvmain__postdate__isnull=True) \
                                .filter(jvmain__jvdate__gte=datefrom, jvmain__jvdate__lte=dateto) \
                                .values('jvmain__jvnum') \
                                .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),
                                          creditsum=Sum('creditamount')) \
                                .values('jvmain__jvnum', 'margin', 'jvmain__jvdate', 'debitsum', 'creditsum',
                                        'jvmain__pk').order_by('jvmain__jvnum') \
                                .exclude(margin=0)


                            # undept = Jvdetail.objects.filter(jvmain__jvstatus='R', jvmain__status='A', jvmain__postby__isnull=True, jvmain__postdate__isnull=True) \
                            #     .filter(jvmain__jvdate__gte=datefrom, jvmain__jvdate__lte=dateto) \
                            #     .filter(department__isnull=False) \
                            #     .exclude(
                            #     department__expchartofaccount__accountcode__startswith=Concat(F('chartofaccount__main'),
                            #                                                                   F('chartofaccount__clas')))
                            undept_count = 0
                            undept_id = []
                            undept = Jvdetail.objects.filter(jvmain__jvstatus='R', jvmain__status='A',jvmain__postby__isnull=True, jvmain__postdate__isnull=True) \
                                .filter(jvmain__jvdate__gte=datefrom, jvmain__jvdate__lte=dateto)

                            for item in undept:
                                #print str(item.id) + ' ' + str(item.department_id) + ' ' + str(item.chartofaccount_id) + ' ' + str(item.chartofaccount.accountcode) + ' ' + str(item.chartofaccount.department_enable)
                                if item.department_id is not None and item.chartofaccount.department_enable == 'N':
                                    undept_count += 1
                                    undept_id.append(item.id)
                                elif item.department_id is None and item.chartofaccount.department_enable == 'Y':
                                    undept_count += 1
                                    undept_id.append(item.id)

                            if unbalanced.count() == 0 and undept_count == 0:
                                item_count, batchkey = logjv(datefrom, dateto, batchkey, request.user)
                                status_success = 1
                            #elif undept.count() != 0:
                            elif undept_count != 0:
                                ud_list = []
                                ud_type = 'JV'
                                undept = Jvdetail.objects.filter(id__in=undept_id)
                                for data in undept:
                                    #print data.id
                                    #print data.chartofaccount_id
                                    #print data.jv_num
                                    #print data.department_id
                                    #print data.department
                                    ud_list.append(['/journalvoucher/' + str(data.jvmain.pk) + '/update',
                                                    data.jvmain.jvnum+' item:'+str(data.chartofaccount.accountcode),
                                                    data.jvmain.jvdate,
                                                    ])
                                status_undept = 1
                            else:
                                ub_list = []
                                ub_type = 'JV'
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
                    print 'or'
                    batchkey = request.POST['batchkey']
                    if 'or' in request.POST.getlist('id_transtype'):
                        if datetime.today().date() > datefrom and validate_date.filter(doctype='OR').count() > 0:
                            unbalanced = Ordetail.objects.filter(ormain__orstatus='R', ormain__status='A',
                                                                 ormain__postby__isnull=True,
                                                                 ormain__postdate__isnull=True) \
                                .filter(ormain__ordate__gte=datefrom, ormain__ordate__lte=dateto) \
                                .values('ormain__ornum') \
                                .annotate(margin=Sum('debitamount') - Sum('creditamount'), debitsum=Sum('debitamount'),
                                          creditsum=Sum('creditamount')) \
                                .values('ormain__ornum', 'margin', 'ormain__ordate', 'debitsum', 'creditsum',
                                        'ormain__pk').order_by('ormain__ornum') \
                                .exclude(margin=0)

                            # undept = Ordetail.objects.filter(ormain__orstatus='R', ormain__status='A',
                            #                                  ormain__postby__isnull=True, ormain__postdate__isnull=True) \
                            #     .filter(ormain__ordate__gte=datefrom, ormain__ordate__lte=dateto) \
                            #     .filter(department__isnull=False) \
                            #     .exclude(
                            #     department__expchartofaccount__accountcode__startswith=Concat(F('chartofaccount__main'),
                            #                                                                   F(
                            #                                                                       'chartofaccount__clas')))

                            undept_count = 0
                            undept_id = []
                            undept = Ordetail.objects.filter(ormain__orstatus='R', ormain__status='A',
                                                             ormain__postby__isnull=True, ormain__postdate__isnull=True) \
                                .filter(ormain__ordate__gte=datefrom, ormain__ordate__lte=dateto)

                            for item in undept:
                                if item.department_id is not None and item.chartofaccount.department_enable == 'N':
                                    undept_count += 1
                                    undept_id.append(item.id)
                                elif item.department_id is None and item.chartofaccount.department_enable == 'Y':
                                    undept_count += 1
                                    undept_id.append(item.id)

                            if unbalanced.count() == 0 and undept_count == 0:
                                item_count, batchkey = logor(datefrom, dateto, batchkey, request.user)
                                status_success = 1
                            elif undept_count != 0:
                                undept = Ordetail.objects.filter(id__in=undept_id)
                                ud_list = []
                                ud_type = 'OR'
                                undept = Ordetail.objects.filter(id__in=undept_id)
                                for data in undept:
                                    ud_list.append(['/officialreceipt/' + str(data.ormain.pk) + '/update',
                                                    data.ormain.ornum,
                                                    data.ormain.ordate,
                                                    ])
                                status_undept = 1
                            elif unbalanced.count() != 0:
                                ub_list = []
                                ub_type = 'OR'
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
                        'item_count': '0',
                        'batchkey': batchkey,
                        'message': 'Skipped',
                    }
                elif status_undept == 1:
                    data = {
                        'status': 'success',
                        'response': 'failed',
                        'message': 'Found ' + str(undept.count()) + ' error in department entry',
                        'ud_list': ud_list,
                        'ud_type': ud_type,
                    }
                elif status_unbalanced == 1:
                    data = {
                        'status': 'success',
                        'response': 'failed',
                        'message': 'Found ' + str(unbalanced.count()) + ' unbalanced entry',
                        'ub_list': ub_list,
                        'ub_type': ub_type,
                    }
                elif status_invaliddate == 1:
                    data = {
                        'status': 'success',
                        'response': 'failed',
                        'message': 'Date From should be a day after or within the previous POSTED DATES',
                    }
            elif dateto.year < closetransaction.year or dateto.year <= closetransaction.year and dateto.month <= closetransaction.month:
                data = {
                    'status': 'success',
                    'response': 'failed',
                    'message': 'The month of '+str(calendar.month_name[dateto.month])+' '+str(dateto.year)+' is already closed',
                }
            else:
                data = {
                    'status': 'success',
                    'response': 'failed',
                    'message': 'Transaction month is invalid. Need to close the month of '+str(calendar.month_name[validtransaction
                                                                                               .month])+' '+str(validtransaction.year),
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
            document_customer_id=data.customer_id,
            document_supplier_id=data.supplier_id,
            # document_supplier=data.apmain.payee,
            # document_supplieratc=data.apmain.payee.atc if data.apmain.payee else None,
            # document_supplieratccode=data.apmain.payee.atc.code if data.apmain.payee else None,
            # document_supplieratcrate=data.apmain.payee.atc.rate if data.apmain.payee else None,
            # document_suppliervat=data.apmain.payee.vat if data.apmain.payee else None,
            # document_suppliervatcode=data.apmain.payee.vat.code if data.apmain.payee else None,
            # document_suppliervatrate=data.apmain.payee.vat.rate if data.apmain.payee else None,
            # document_supplierinputvat=data.apmain.payee.inputvat if data.apmain.payee else None,
            # document_branch=data.apmain.branch,
            # document_payee=data.apmain.payeename,
            # document_amount=data.apmain.amount,
            # document_duedate=data.apmain.duedate,
            # document_currency=data.apmain.currency,
            # document_fxrate=data.apmain.fxrate,
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
            # document_supplier=data.cvmain.payee,
            # document_supplieratc=data.cvmain.payee.atc if data.cvmain.payee else None,
            # document_supplieratccode=data.cvmain.payee.atc.code if data.cvmain.payee else None,
            # document_supplieratcrate=data.cvmain.payee.atc.rate if data.cvmain.payee else None,
            # document_suppliervat=data.cvmain.payee.vat if data.cvmain.payee else None,
            # document_suppliervatcode=data.cvmain.payee.vat.code if data.cvmain.payee else None,
            # document_suppliervatrate=data.cvmain.payee.vat.rate if data.cvmain.payee else None,
            # document_supplierinputvat=data.cvmain.payee.inputvat if data.cvmain.payee else None,
            document_customer_id=data.customer_id,
            document_supplier_id=data.supplier_id,
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
            document_supplier=data.supplier,
            document_customer=data.customer,
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
            #document_customer_id=data.customer_id,
            document_supplier_id=data.supplier_id,
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
    skipcount = 999999999

    if request.method == 'POST':
        # locking/posting of transactions goes here
        items = logs_subledger.objects.filter(batchkey=request.POST['batchkey'], importstatus='S')

        if items.count() > 0:
            # add subledger
            seq_item = items[:skipcount]
            #seq_item = items[999999999
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
                    .update(postby=request.user, postdate=datetime.now(), status='O')

                # detail
                if data.breakdownsource_id is None:
                    trans_detail\
                        .filter(pk=data.document_id)\
                        .filter(status='A', postby__isnull=True, postdate__isnull=True)\
                        .update(postby=request.user, postdate=datetime.now(), status='O')
                else:
                    trans_detailbreakdown \
                        .filter(pk=data.breakdownsource_id) \
                        .filter(status='A', postby__isnull=True, postdate__isnull=True) \
                        .update(postby=request.user, postdate=datetime.now(), status='O')

                sub_item = Subledger.objects.create(
                               chartofaccount=data.chartofaccount,
                               item_counter=data.item_counter,
                               document_type=data.document_type,
                               document_id=data.document_id,
                               document_num=data.document_num,
                               document_date=data.document_date,
                               subtype=data.subtype,
                               dcsubtype=data.dcsubtype,
                               bankaccount=data.bankaccount,
                               department=data.department,
                               employee=data.employee,
                               customer=data.customer,
                               inventory=data.inventory,
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

                # ************************ set beg_code, end_code, year_to_date_code
                chart_item = Chartofaccount.objects.filter(pk=sub_item.chartofaccount.pk)
                if sub_item.chartofaccount.beginning_code is None or sub_item.chartofaccount.beginning_code == '':
                    chart_item.update(beginning_code=sub_item.chartofaccount.balancecode)
                if sub_item.chartofaccount.end_code is None or sub_item.chartofaccount.end_code == '':
                    chart_item.update(end_code=sub_item.chartofaccount.balancecode)
                if sub_item.chartofaccount.year_to_date_code is None or sub_item.chartofaccount.year_to_date_code == '':
                    chart_item.update(year_to_date_code=sub_item.chartofaccount.balancecode)

                # ************************ check if beg_code, end_amount, year_to_date_amount exists
                # if chart_item.first().beginning_amount is None or chart_item.first().beginning_amount == '':
                #     beginning_amount = 0
                # else:
                #     beginning_amount = chart_item.first().beginning_amount
                if chart_item.first().end_amount is None or chart_item.first().end_amount == '':
                    end_amount = 0
                else:
                    end_amount = chart_item.first().end_amount
                if chart_item.first().year_to_date_amount is None or chart_item.first().year_to_date_amount == '':
                    year_to_date_amount = 0
                else:
                    year_to_date_amount = chart_item.first().year_to_date_amount

                # ************************ beg code
                # if sub_item.balancecode == sub_item.chartofaccount.beginning_code:
                #     chart_item.update(beginning_amount=float(beginning_amount) + float(sub_item.amount))
                # else:
                #     if chart_item.first().beginning_amount < sub_item.amount:
                #         chart_item.update(beginning_code=sub_item.balancecode)
                #
                #     chart_item.update(beginning_amount=abs(float(beginning_amount) - float(sub_item.amount)))
                #
                # if chart_item.filter(beginning_date__lt=sub_item.document_date).count() > 0 or chart_item.filter(beginning_date__isnull=True).count() > 0:
                #     chart_item.update(beginning_date=sub_item.document_date)

                # ************************ end code
                if sub_item.balancecode == sub_item.chartofaccount.end_code:
                    chart_item.update(end_amount=float(end_amount) + float(sub_item.amount))
                else:
                    if chart_item.first().end_amount < sub_item.amount:
                        chart_item.update(end_code=sub_item.balancecode)

                    chart_item.update(end_amount=abs(float(end_amount) - float(sub_item.amount)))

                if chart_item.filter(end_date__lt=sub_item.document_date).count() > 0 or chart_item.filter(end_date__isnull=True).count() > 0:
                    chart_item.update(end_date=sub_item.document_date)

                # ************************ year code
                if sub_item.balancecode == sub_item.chartofaccount.year_to_date_code:
                    chart_item.update(year_to_date_amount=float(year_to_date_amount) + float(sub_item.amount))
                else:
                    if chart_item.first().year_to_date_amount < sub_item.amount:
                        chart_item.update(year_to_date_code=sub_item.balancecode)

                    chart_item.update(year_to_date_amount=abs(float(year_to_date_amount) - float(sub_item.amount)))

                if chart_item.filter(year_to_date_date__lt=sub_item.document_date).count() > 0 or chart_item.filter(year_to_date_date__isnull=True).count() > 0:
                    chart_item.update(year_to_date_date=sub_item.document_date)

                # ************************ account expense balance
                if sub_item.department is not None:
                    accexp_item = Accountexpensebalance.objects.filter(
                        year=sub_item.document_date.year,
                        month=sub_item.document_date.month,
                        chartofaccount=sub_item.chartofaccount,
                        department=sub_item.department,
                    )

                    if accexp_item.count() > 0:
                        accexp_amount = accexp_item.first().amount

                        if sub_item.balancecode == accexp_item.first().code:
                            accexp_item.update(amount=float(accexp_amount) + float(sub_item.amount))
                        else:
                            if accexp_item.first().amount < sub_item.amount:
                                accexp_item.update(code=sub_item.balancecode)

                            accexp_item.update(amount=abs(float(accexp_amount) - float(sub_item.amount)))

                        if accexp_item.filter(date__lt=sub_item.document_date).count() > 0:
                            accexp_item.update(date=sub_item.document_date)
                    else:
                        Accountexpensebalance.objects.create(
                            year=sub_item.document_date.year,
                            month=sub_item.document_date.month,
                            chartofaccount=sub_item.chartofaccount,
                            department=sub_item.department,
                            amount=sub_item.amount,
                            code=sub_item.balancecode,
                            enterby=request.user,
                            date=sub_item.document_date,
                        )

                # ************************ bank account
                if sub_item.bankaccount is not None:
                    bank_item = Bankaccount.objects.filter(pk=sub_item.bankaccount.pk)

                    if bank_item.first().run_code is None or bank_item.first().run_code == '':
                        bank_item.update(run_code=sub_item.balancecode)
                    if bank_item.first().year_to_date_code is None or bank_item.first().year_to_date_code == '':
                        bank_item.update(year_to_date_code=sub_item.balancecode)

                    if sub_item.bankaccount.run_amount is None or sub_item.bankaccount.run_amount == '':
                        run_amount = 0
                    else:
                        run_amount = sub_item.bankaccount.run_amount
                    if sub_item.bankaccount.year_to_date_amount is None or sub_item.bankaccount.year_to_date_amount == '':
                        year_to_date_amount = 0
                    else:
                        year_to_date_amount = sub_item.bankaccount.year_to_date_amount

                    if sub_item.balancecode == sub_item.bankaccount.run_code:
                        bank_item.update(run_amount=float(run_amount) + float(sub_item.amount))
                    else:
                        if sub_item.bankaccount.run_amount < sub_item.amount:
                            bank_item.update(run_code=sub_item.balancecode)

                        bank_item.update(run_amount=abs(float(run_amount) - float(sub_item.amount)))
                    if sub_item.balancecode == sub_item.bankaccount.year_to_date_code:
                        bank_item.update(year_to_date_amount=float(year_to_date_amount) + float(sub_item.amount))
                    else:
                        if sub_item.bankaccount.year_to_date_amount < sub_item.amount:
                            bank_item.update(year_to_date_code=sub_item.balancecode)

                        bank_item.update(year_to_date_amount=abs(float(year_to_date_amount) - float(sub_item.amount)))

                    if sub_item.bankaccount.run_date is None:
                        bank_item.update(run_date=sub_item.document_date)
                    elif sub_item.bankaccount.run_date < sub_item.document_date:
                        bank_item.update(run_date=sub_item.document_date)
                    if sub_item.bankaccount.year_to_date_date is None:
                        bank_item.update(year_to_date_date=sub_item.document_date)
                    elif sub_item.bankaccount.year_to_date_date < sub_item.document_date:
                        bank_item.update(year_to_date_date=sub_item.document_date)

            itemstotal = logs_subledger.objects.filter(batchkey=request.POST['batchkey'])
            percentage = 100 - int((float(items.count()) / float(itemstotal.count())) * 100)

            # update to posted
            seq_item = items.values_list('pk', flat=True)[:skipcount]
            logs_subledger.objects.filter(pk__in=list(seq_item)).update(importstatus='P')
        else:
            percentage = 100

        if percentage >= 100:
            percentage = 100

            for data in request.POST.getlist('id_transtype'):
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
