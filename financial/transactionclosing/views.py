from dateutil.relativedelta import relativedelta
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from companyparameter.models import Companyparameter
from accountspayable.models import Apmain, Apdetail, Apdetailbreakdown
from checkvoucher.models import Cvmain, Cvdetail, Cvdetailbreakdown
from journalvoucher.models import Jvmain, Jvdetail, Jvdetailbreakdown
from officialreceipt.models import Ormain, Ordetail, Ordetailbreakdown
from subledger.models import Subledger
from chartofaccount.models import Chartofaccount
from bankaccount.models import Bankaccount
from branch.models import Branch
from jvtype.models import Jvtype
from jvsubtype.models import Jvsubtype
from currency.models import Currency
from subledgersummary.models import Subledgersummary
import calendar
import datetime
#from datetimex import datetime
from django.db.models import Sum, F


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'transactionclosing/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        # closingdate = Companyparameter.objects.all().first()

        company = Companyparameter.objects.all().first()
        yearend_year = company.year_end_date
        context['yearend_year'] = yearend_year.year
        context['today_year'] = datetime.datetime.now().year
        context['toclose_year'] = yearend_year.year + 1
        context['count'] = datetime.datetime.now().year - company.year_end_date.year
        context['param'] = company
        context['closingdate'] = company.last_closed_date + relativedelta(months=1)
        context['closingyear'] = company.last_closed_date.year
        context['closingyearmonth'] = company.last_closed_date.month
        return context


@csrf_exempt
def proc_validate(request):

    if request.method == 'POST':

        val_message = ''

        val_date = Companyparameter.objects.all().first().last_closed_date

        val_date = val_date + relativedelta(months=1)

        val_count = Apmain.objects.filter(apdate__month=val_date.month, apdate__year=val_date.year).exclude(status='C').exclude(status='O').exclude(apstatus='D').count()

        if val_count > 0:
            val_message += "All Accounts Payable must be released!<br>"

        val_count = Cvmain.objects.filter(cvdate__month=val_date.month, cvdate__year=val_date.year).exclude(status='C').exclude(status='O').exclude(cvstatus='D').count()
        if val_count > 0:
            val_message += "All Check Voucher must be released!<br>"

        val_count = Jvmain.objects.filter(jvdate__month=val_date.month, jvdate__year=val_date.year).exclude(status='C').exclude(status='O').exclude(jvstatus='D').count()
        if val_count > 0:
            val_message += "All Journal Voucher must be released!<br>"

        val_count = Ormain.objects.filter(ordate__month=val_date.month, ordate__year=val_date.year).exclude(status='C').exclude(status='O').exclude(orstatus='D').count()
        if val_count > 0:
            val_message += "All Official Receipt must be released!<br>"

        data = {
            'status': 'success',
            'message': val_message,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def proc_provision(request):

    if request.method == 'POST':
        dt = Companyparameter.objects.all().first().last_closed_date
        dt = dt + relativedelta(months=1)

        subledger = Subledger.objects.filter(chartofaccount__main__gte=Chartofaccount.objects.get(title='REVENUE').main,
                                             document_date__month=dt.month,
                                             document_date__year=dt.year)

        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back
        sub_credit = subledger.filter(balancecode='D').aggregate(amount=Sum('amount'))['amount']
        sub_debit = subledger.filter(balancecode='C').aggregate(amount=Sum('amount'))['amount']
        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back

        if sub_credit > sub_debit:
            comp_param = Companyparameter.objects.all().first()
            taxamount = float(sub_credit - sub_debit) * (float(comp_param.income_tax_rate) / 100)

            jvyear = dt.year
            num = len(Jvmain.objects.all().filter(jvdate__year=jvyear)) + 1
            padnum = '{:06d}'.format(num)
            actualjvnum = str(jvyear) + str(padnum)

            lastday = calendar.monthrange(dt.year, dt.month)[1]
            jv = Jvmain.objects.create(jvnum=actualjvnum,
                                       jvdate=str(dt.year) + '-' + str(dt.month) + '-' + str(lastday),
                                       status='O',
                                       jvstatus='R',
                                       branch=Branch.objects.get(code='HO'),
                                       jvtype=Jvtype.objects.get(code='N'),
                                       jvsubtype=Jvsubtype.objects.get(code='MJV'),
                                       currency=Currency.objects.get(symbol='PHP'),
                                       enterby=request.user,
                                       postby=request.user,
                                       postdate=datetime.datetime.now(),
                                       amount=taxamount)

            jv_d = Jvdetail.objects.create(chartofaccount=comp_param.coa_provisionincometax,
                                           item_counter=1,
                                           jv_num=jv.jvnum,
                                           jv_date=jv.jvdate,
                                           debitamount=taxamount,
                                           balancecode='D',
                                           amount=taxamount,
                                           status='O',
                                           jvmain=jv,
                                           postby=request.user,
                                           postdate=datetime.datetime.now())

            jv_d2 = Jvdetail.objects.create(chartofaccount=comp_param.coa_incometaxespayable,
                                            item_counter=2,
                                            jv_num=jv.jvnum,
                                            jv_date=jv.jvdate,
                                            creditamount=taxamount,
                                            balancecode='C',
                                            amount=taxamount,
                                            status='O',
                                            jvmain=jv,
                                            postby=request.user,
                                            postdate=datetime.datetime.now())
            jv_d_list = [jv_d.pk, jv_d2.pk]

            for data in jv_d_list:
                jv_data = Jvdetail.objects.get(pk=data)
                sub_item = Subledger.objects.create(
                                chartofaccount=jv_data.chartofaccount,
                                item_counter=jv_data.item_counter,
                                document_type='JV',
                                document_id=jv_data.pk,
                                document_num=jv_data.jv_num,
                                document_date=jv_data.jv_date,
                                subtype=jv_data.jvmain.jvtype,
                                balancecode=jv_data.balancecode,
                                amount=jv_data.amount,
                                document_status=jv_data.jvmain.status,
                                document_branch=jv_data.jvmain.branch,
                                document_amount=jv_data.jvmain.amount,
                                document_currency=jv_data.jvmain.currency,
                                document_fxrate=jv_data.jvmain.fxrate,
                                enterby=request.user,
                                modifyby=request.user,
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
                if chart_item.first().end_amount is None or chart_item.first().end_amount == '':
                    end_amount = 0
                else:
                    end_amount = chart_item.first().end_amount
                if chart_item.first().year_to_date_amount is None or chart_item.first().year_to_date_amount == '':
                    year_to_date_amount = 0
                else:
                    year_to_date_amount = chart_item.first().year_to_date_amount

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

        data = {
            'status': 'success',
            'message': 'Done: Provision for income tax<br>',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def proc_currentearnings(request):

    if request.method == 'POST':
        dt = Companyparameter.objects.all().first().last_closed_date
        dt = dt + relativedelta(months=1)

        subledger = Subledger.objects.filter(chartofaccount__main__gte=Chartofaccount.objects.get(title='REVENUE').main,
                                             document_date__month=dt.month,
                                             document_date__year=dt.year)

        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back
        sub_credit = subledger.filter(balancecode='C').aggregate(amount=Sum('amount'))['amount']
        sub_debit = subledger.filter(balancecode='D').aggregate(amount=Sum('amount'))['amount']
        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back
        # dont forget to bring this back

        balcode = 'D'
        income = float(sub_credit - sub_debit)

        if sub_credit > sub_debit:
            balcode = 'C'

        currentearnings = Companyparameter.objects.all().first().coa_currentearnings

        # ************************ set beg_code, end_code, year_to_date_code
        chart_item = Chartofaccount.objects.filter(pk=currentearnings.pk)
        if currentearnings.beginning_code is None or currentearnings.beginning_code == '':
            chart_item.update(beginning_code=currentearnings.balancecode)
        if currentearnings.end_code is None or currentearnings.end_code == '':
            chart_item.update(end_code=currentearnings.balancecode)
        if currentearnings.year_to_date_code is None or currentearnings.year_to_date_code == '':
            chart_item.update(year_to_date_code=currentearnings.balancecode)

        # ************************ check if beg_code, end_amount, year_to_date_amount exists
        if chart_item.first().end_amount is None or chart_item.first().end_amount == '':
            end_amount = 0
        else:
            end_amount = chart_item.first().end_amount
        if chart_item.first().year_to_date_amount is None or chart_item.first().year_to_date_amount == '':
            year_to_date_amount = 0
        else:
            year_to_date_amount = chart_item.first().year_to_date_amount

        # ************************ end code, year code

        #tdate =

        ytd_amount = 0
        ytd_code = 'D'

        if balcode == chart_item.first().year_to_date_code:
            ytd_amount = float(year_to_date_amount) + float(income)
            ytd_code = balcode
        else:
            ytd_amount = abs(float(year_to_date_amount) - float(income))
            ytd_code = balcode

        lastday = calendar.monthrange(dt.year, dt.month)[1]

        date_time_str = str(dt.year)+'-'+str(dt.month)+'-'+str(lastday)
        print date_time_str
        tdate = datetime.datetime.strptime(date_time_str, '%Y-%m-%d')

        chart_item.update(end_amount=abs(float(income)),
                          end_code = balcode,
                          end_date = tdate,
                          year_to_date_code = ytd_code,
                          year_to_date_date = tdate,
                          year_to_date_amount=ytd_amount)



        data = {
            'status': 'success',
            'message': 'Done: Current Earnings<br>',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

# @csrf_exempt
# def proc_retainedearnings(request):
#
#     if request.method == 'POST':
#         dt = Companyparameter.objects.all().first().last_closed_date
#         dt = dt + relativedelta(months=1)
#
#         subledger = Subledger.objects.filter(chartofaccount__main__gte=Chartofaccount.objects.get(title='REVENUE').main,
#                                              document_date__month=dt.month,
#                                              document_date__year=dt.year)
#
#         # dont forget to bring this back
#         # dont forget to bring this back
#         # dont forget to bring this back
#         # dont forget to bring this back
#         # dont forget to bring this back
#         sub_credit = subledger.filter(balancecode='D').aggregate(amount=Sum('amount'))['amount']
#         sub_debit = subledger.filter(balancecode='C').aggregate(amount=Sum('amount'))['amount']
#         # dont forget to bring this back
#         # dont forget to bring this back
#         # dont forget to bring this back
#         # dont forget to bring this back
#         # dont forget to bring this back
#
#         if sub_credit > sub_debit:
#             retainedearnings = Companyparameter.objects.all().first().coa_retainedearnings
#             income = float(sub_credit - sub_debit)
#
#             # ************************ set beg_code, end_code, year_to_date_code
#             chart_item = Chartofaccount.objects.filter(pk=retainedearnings.pk)
#             if retainedearnings.beginning_code is None or retainedearnings.beginning_code == '':
#                 chart_item.update(beginning_code=retainedearnings.balancecode)
#             if retainedearnings.end_code is None or retainedearnings.end_code == '':
#                 chart_item.update(end_code=retainedearnings.balancecode)
#             if retainedearnings.year_to_date_code is None or retainedearnings.year_to_date_code == '':
#                 chart_item.update(year_to_date_code=retainedearnings.balancecode)
#
#             # ************************ check if beg_code, end_amount, year_to_date_amount exists
#             if chart_item.first().end_amount is None or chart_item.first().end_amount == '':
#                 end_amount = 0
#             else:
#                 end_amount = chart_item.first().end_amount
#             if chart_item.first().year_to_date_amount is None or chart_item.first().year_to_date_amount == '':
#                 year_to_date_amount = 0
#             else:
#                 year_to_date_amount = chart_item.first().year_to_date_amount
#
#             # ************************ end code, year code
#             chart_item.update(end_amount=float(end_amount) + float(income),
#                               year_to_date_amount=float(year_to_date_amount) + float(income))
#
#         data = {
#             'status': 'success',
#             'message': 'Done: Retained Earnings<br>',
#         }
#     else:
#         data = {
#             'status': 'error',
#         }
#
#     return JsonResponse(data)


@csrf_exempt
def proc_generalledgersummary(request):

    if request.method == 'POST':
        chart = Chartofaccount.objects.filter(accounttype='P')
        chart.filter(beginning_code__isnull=True).update(beginning_code=F('balancecode'))
        chart.filter(end_code__isnull=True).update(end_code=F('balancecode'))
        chart.filter(year_to_date_code__isnull=True).update(year_to_date_code=F('balancecode'))

        dt = Companyparameter.objects.all().first().last_closed_date
        dt = dt + relativedelta(months=1)

        for data in chart:
            sub_item = Subledgersummary.objects.create(
                            year=dt.year,
                            month=dt.month,
                            chartofaccount=data,
                            beginning_amount=data.beginning_amount,
                            beginning_code=data.beginning_code,
                            beginning_date=data.beginning_date,
                            end_amount=data.end_amount,
                            end_code=data.end_code,
                            end_date=data.end_date,
                            year_to_date_amount=data.year_to_date_amount,
                            year_to_date_code=data.year_to_date_code,
                            year_to_date_date=data.year_to_date_date)

            sub = Subledger.objects.filter(chartofaccount=data,
                                           document_date__month=dt.month,
                                           document_date__year=dt.year)
            sub_debit = sub.filter(balancecode='D')
            sub_credit = sub.filter(balancecode='C')

            ap_d = sub_debit.filter(document_type='AP').aggregate(Sum('amount'))['amount__sum'] if sub_debit.filter(document_type='AP').aggregate(Sum('amount'))['amount__sum'] is not None else 0
            ap_c = sub_credit.filter(document_type='AP').aggregate(Sum('amount'))['amount__sum'] if sub_credit.filter(document_type='AP').aggregate(Sum('amount'))['amount__sum'] is not None else 0
            cv_d = sub_debit.filter(document_type='CV').aggregate(Sum('amount'))['amount__sum'] if sub_debit.filter(document_type='CV').aggregate(Sum('amount'))['amount__sum'] is not None else 0
            cv_c = sub_credit.filter(document_type='CV').aggregate(Sum('amount'))['amount__sum'] if sub_credit.filter(document_type='CV').aggregate(Sum('amount'))['amount__sum'] is not None else 0
            jv_d = sub_debit.filter(document_type='JV').aggregate(Sum('amount'))['amount__sum'] if sub_debit.filter(document_type='JV').aggregate(Sum('amount'))['amount__sum'] is not None else 0
            jv_c = sub_credit.filter(document_type='JV').aggregate(Sum('amount'))['amount__sum'] if sub_credit.filter(document_type='JV').aggregate(Sum('amount'))['amount__sum'] is not None else 0
            or_d = sub_debit.filter(document_type='OR').aggregate(Sum('amount'))['amount__sum'] if sub_debit.filter(document_type='OR').aggregate(Sum('amount'))['amount__sum'] is not None else 0
            or_c = sub_credit.filter(document_type='OR').aggregate(Sum('amount'))['amount__sum'] if sub_credit.filter(document_type='OR').aggregate(Sum('amount'))['amount__sum'] is not None else 0

            Subledgersummary.objects.filter(pk=sub_item.pk).update(journal_voucher_credit_total=jv_c,
                                                                journal_voucher_debit_total=jv_d,
                                                                check_voucher_credit_total=cv_c,
                                                                check_voucher_debit_total=cv_d,
                                                                accounts_payable_voucher_credit_total=ap_c,
                                                                accounts_payable_voucher_debit_total=ap_d,
                                                                official_receipt_credit_total=or_c,
                                                                official_receipt_debit_total=or_d)
        data = {
            'status': 'success',
            'message': 'Done: General Ledger Summary<br>',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def proc_zeroout(request):

    if request.method == 'POST':
        Chartofaccount.objects.filter(main__gte=Chartofaccount.objects.get(title='REVENUE').main).update(end_amount=0)
        #Chartofaccount.objects.filter(main__lt=4).update(end_amount=0)

        data = {
            'status': 'success',
            'message': 'Done: Zero-out all End Amounts<br>',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def proc_updateclosing(request):

    if request.method == 'POST':
        dt = Companyparameter.objects.all().first().last_closed_date
        newdt = dt + relativedelta(months=1)

        jvmain = Jvmain.objects.filter(jvstatus='R', status='O', jvdate__year=newdt.year, jvdate__month=newdt.month,
                                       postby__isnull=False, postdate__isnull=False, closeby__isnull=True,
                                       closedate__isnull=True).update(closeby=request.user, closedate=datetime.datetime.now())
        jvdetail = Jvdetail.objects.filter(status='O', jv_date__year=newdt.year, jv_date__month=newdt.month,
                                           postby__isnull=False, postdate__isnull=False, closeby__isnull=True,
                                           closedate__isnull=True).update(closeby=request.user, closedate=datetime.datetime.now())
        jvdetailbreakdown = Jvdetailbreakdown.objects.filter(status='O', jv_date__year=newdt.year, jv_date__month=newdt.month,
                                                             postby__isnull=False, postdate__isnull=False, closeby__isnull=True,
                                                             closedate__isnull=True).update(closeby=request.user, closedate=datetime.datetime.now())

        apmain = Apmain.objects.filter(apstatus='R', status='O', apdate__year=newdt.year, apdate__month=newdt.month,
                                       postby__isnull=False, postdate__isnull=False, closeby__isnull=True,
                                       closedate__isnull=True).update(closeby=request.user, closedate=datetime.datetime.now())
        apdetail = Apdetail.objects.filter(status='O', ap_date__year=newdt.year, ap_date__month=newdt.month,
                                           postby__isnull=False, postdate__isnull=False, closeby__isnull=True,
                                           closedate__isnull=True).update(closeby=request.user,closedate=datetime.datetime.now())
        apdetailbreakdown = Apdetailbreakdown.objects.filter(status='O', ap_date__year=newdt.year,
                                                             ap_date__month=newdt.month, postby__isnull=False,
                                                             postdate__isnull=False, closeby__isnull=True,
                                                             closedate__isnull=True).update(closeby=request.user,closedate=datetime.datetime.now())

        ormain = Ormain.objects.filter(orstatus='R', status='O', ordate__year=newdt.year, ordate__month=newdt.month,
                                       postby__isnull=False, postdate__isnull=False, closeby__isnull=True,
                                       closedate__isnull=True).update(closeby=request.user,
                                                                      closedate=datetime.datetime.now())
        ordetail = Ordetail.objects.filter(status='O', or_date__year=newdt.year, or_date__month=newdt.month,
                                           postby__isnull=False, postdate__isnull=False, closeby__isnull=True,
                                           closedate__isnull=True).update(closeby=request.user,
                                                                          closedate=datetime.datetime.now())
        ordetailbreakdown = Ordetailbreakdown.objects.filter(status='O', or_date__year=newdt.year,
                                                             or_date__month=newdt.month, postby__isnull=False,
                                                             postdate__isnull=False, closeby__isnull=True,
                                                             closedate__isnull=True).update(closeby=request.user,
                                                                                            closedate=datetime.datetime.now())

        cvmain = Cvmain.objects.filter(cvstatus='R', status='O', cvdate__year=newdt.year, cvdate__month=newdt.month,
                                       postby__isnull=False, postdate__isnull=False, closeby__isnull=True,
                                       closedate__isnull=True).update(closeby=request.user,
                                                                      closedate=datetime.datetime.now())
        cvdetail = Cvdetail.objects.filter(status='O', cv_date__year=newdt.year, cv_date__month=newdt.month,
                                           postby__isnull=False, postdate__isnull=False, closeby__isnull=True,
                                           closedate__isnull=True).update(closeby=request.user,
                                                                          closedate=datetime.datetime.now())
        cvdetailbreakdown = Cvdetailbreakdown.objects.filter(status='O', cv_date__year=newdt.year,
                                                             cv_date__month=newdt.month, postby__isnull=False,
                                                             postdate__isnull=False, closeby__isnull=True,
                                                             closedate__isnull=True).update(closeby=request.user,
                                                                                            closedate=datetime.datetime.now())

        Companyparameter.objects.all().update(last_closed_date=newdt)

        data = {
            'status': 'success',
            'message': 'Done: Log Closing Date<br>',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def yearend_init(request):
    print 'Initialization'

    param = Companyparameter.objects.all()

    ''' Init Current Earnings'''
    curearn = Chartofaccount.objects.filter(id=param.first().coa_currentearnings_id)
    curearn.update(end_amount=0,end_code=curearn.first().balancecode,end_date=curearn.first().year_to_date_date)

    ''' Init Retained Earnings'''
    retearn = Chartofaccount.objects.filter(id=param.first().coa_retainedearnings_id)
    run_amt = 0
    run_code = retearn.first().balancecode
    run_date = curearn.first().year_to_date_date

    if retearn.first().end_code == curearn.first().year_to_date_code:
        run_amt = retearn.first().end_amount + curearn.first().year_to_date_amount
        run_code = curearn.first().year_to_date_code
    else:
        run_amt = abs(retearn.first().end_amount - curearn.first().year_to_date_amount)
        if retearn.first().end_amount >= curearn.first().year_to_date_amount:
            run_code = retearn.first().end_code
        else:
            run_code = curearn.first().year_to_date_code

    retearn.update(end_amount=run_amt, end_code=run_code, end_date=run_date)

    ''' Process Real Accounts '''

    real = Chartofaccount.objects.filter(main__in=[1,2,3]).order_by('accountcode')

    for data in real:
        chart = Chartofaccount.objects.filter(pk=data.id)
        chart.update(beginning_amount=chart.first().end_amount,beginning_code=chart.first().end_code,beginning_date=chart.first().end_date,
                     year_to_date_amount=0,year_to_date_code=chart.first().balancecode,year_to_date_date=chart.first().end_date)

    ''' Process Nominal Accounts '''

    nominal = Chartofaccount.objects.filter(main__in=[4, 5, 6, 7, 8, 9]).order_by('accountcode')

    for data in nominal:
        chart2 = Chartofaccount.objects.filter(pk=data.id)
        chart2.update(beginning_amount=0, beginning_code=chart.first().balancecode,beginning_date=chart.first().end_date,
                      end_amount=0, end_code=chart.first().balancecode, end_date=chart.first().end_date,
                     year_to_date_amount=0, year_to_date_code=chart.first().balancecode,year_to_date_date=chart.first().end_date)

    ''' Process Bank Account Accounts '''

    bankaccount = Bankaccount.objects.all()

    for data in bankaccount:
        bank = Bankaccount.objects.filter(pk=data.id)
        bank.update(beg_amount=bank.first().run_amount, beg_code=bank.first().run_code,
                      beg_date=bank.first().run_date)

    ''' Process Bank Account Summary Accounts '''

    ''' TODO '''

    # bankaccount_summary = Bankaccount.objects.all()
    #
    # for data in bankaccount:
    #     bank = Bankaccount.objects.filter(pk=data.id)
    #     bank.update(beg_amount=bank.first().run_amount, beg_code=bank.first().run_code,
    #                 beg_date=bank.first().run_date)

    ''' Update Year End Date  '''
    param.update(year_end_date=param.first().last_closed_date)

    data = {
            'status': 'success',
        }

    return JsonResponse(data)

