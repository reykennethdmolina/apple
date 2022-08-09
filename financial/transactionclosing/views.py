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
from accountexpensebalance.models import Accountexpensebalance
from chartofaccount.models import Chartofaccount
from bankaccount.models import Bankaccount, Bankaccountsummary
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

@method_decorator(login_required, name='dispatch')
class YearEndAdjustmentView(TemplateView):
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
            #ytd_amount = abs(abs(float(year_to_date_amount)) + abs(float(income)))
            ytd_amount = abs(float(year_to_date_amount)) + abs(float(income))
            ytd_code = balcode
        else:
            #ytd_amount = abs(abs(float(year_to_date_amount)) - abs(float(income)))
            ytd_amount = abs(float(year_to_date_amount)) - abs(float(income))
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
                          year_to_date_amount=abs(ytd_amount)),



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
    company = Companyparameter.objects.all().first()
    closingyear = company.last_closed_date.year

    for datax in bankaccount:
        bank_summary = Bankaccountsummary(year=closingyear, code=datax.code, accountnumber=datax.accountnumber,
                                          beg_amount=datax.beg_amount,beg_code=datax.beg_code,beg_date=datax.beg_date,
                                          status='A',bankaccount_id=datax.id,
                                          year_to_date_amount=datax.year_to_date_amount,year_to_date_code=datax.year_to_date_code,year_to_date_date=datax.year_to_date_date)
        bank_summary.save()

    ''' Update Year End Date  '''
    param.update(year_end_date=param.first().last_closed_date)

    data = {
            'status': 'success',
        }

    return JsonResponse(data)

@method_decorator(login_required, name='dispatch')
class YearEndAdjustmentView(TemplateView):
    template_name = 'yearendadjustment/index.html'

    def get_context_data(self, **kwargs):
        context = super(YearEndAdjustmentView, self).get_context_data(**kwargs)
        # closingdate = Companyparameter.objects.all().first()

        company = Companyparameter.objects.all().first()
        yearend_year = company.year_end_date

        ddate = str(yearend_year.year)+'-12-31'
        jvlist = Jvmain.objects.all().filter(jvdate=ddate, jvtype_id=6, status='A', jvstatus='R').order_by('jvnum')
        jv_id = jvlist.values_list('id', flat=True)

        jv_detail = Jvdetail.objects.filter(status='A', jvmain_id__in=jv_id).values('chartofaccount__accountcode', 'chartofaccount__description')\
            .annotate(debitamount_sum=Sum('debitamount'),creditamount_sum=Sum('creditamount')).order_by('chartofaccount__accountcode')


        context['jv'] = jvlist
        context['count'] = len(jvlist)
        context['detail'] = jv_detail
        context['jvtotal'] = jvlist.aggregate(amount=Sum('amount'))
        context['detailtotal'] = jv_detail.aggregate(debitamount=Sum('debitamount_sum'),creditamount=Sum('creditamount_sum'))
        context['adjustment_year'] = yearend_year.year
        return context

@csrf_exempt
def proc_yearendadjustment(request):
    print 'Initialization'

    company = Companyparameter.objects.all().first()
    yearend_year = company.year_end_date

    ddate = str(yearend_year.year) + '-12-31'
    jvlist = Jvmain.objects.all().filter(jvdate=ddate, jvtype_id=6, status='A', jvstatus='R').order_by('jvnum')

    dec_cur_debit_amt = 0
    dec_cur_credit_amt = 0
    dec_cur_code = 'D'
    dec_cur_amount = 0

    if len(jvlist) != 0:

        error = 0
        for jv in jvlist:
            jv_detail = Jvdetail.objects.filter(status='A', jvmain_id=jv.id).values('jvmain_id').aggregate(debitamount_sum=Sum('debitamount'), creditamount_sum=Sum('creditamount'))

            #  checking unequal debit and credit
            if jv_detail['debitamount_sum'] != jv_detail['creditamount_sum']:
                remarks = 'JV#'+str(jv.jvnum)+' accounting entry is not equal. Please check entry'
                data = {'status': 'error', 'remarks': remarks}
                error = 1
                return JsonResponse(data)

            #  checking unmatch expenses
            detail = Jvdetail.objects.all().filter(status='A', jvmain_id=jv.id, chartofaccount__main=5)
            for d in detail:
                print d.jv_num
                print d.id
                print d.department_id
                print d.chartofaccount_id
                print d.chartofaccount.accountcode

                if d.department_id:
                    print d.department_id
                    print 'None'
                    if str(d.chartofaccount.accountcode)[0:2] != str(d.department.expchartofaccount)[0:2]:
                        if d.department.code != 'IGC':
                            remarks = 'JV#' + str(d.jv_num) + ' account ' + str(
                                d.chartofaccount.accountcode) + ' unmacthed expense account vs department'
                            data = {'status': 'error', 'remarks': remarks}
                            error = 1
                            return JsonResponse(data)
                else:
                    print 'hey  '





        if error == 0:
            # update jvmain and jvdetails
            for jv in jvlist:
                main = Jvmain.objects.get(pk=jv.id)
                main.status = 'O'
                main.postby = request.user
                main.postdate = datetime.datetime.now()
                main.closeby = request.user
                main.closedate = datetime.datetime.now()
                main.save()

                # update details
                detail = Jvdetail.objects.all().filter(status='A', jvmain_id=jv.id)
                for data in detail:
                    print 'updating '+str(data.jv_num)
                    Jvdetail.objects.filter(pk=data.id).update(status='O', postby=request.user, postdate=datetime.datetime.now(),
                                                            closeby=request.user, closedate=datetime.datetime.now())
                    # Insert data in subsidiary ledger
                    Subledger.objects.create(
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
                        enterby=d.enterby,
                        modifyby=d.modifyby,
                    )

        #Compute for net of total debits and total credits of additional JV
        jvlist2 = Jvmain.objects.all().filter(jvdate=ddate, jvtype_id=6, status='O', jvstatus='R').order_by('jvnum')
        #jvlist2 = Jvmain.objects.all().filter(jvdate=ddate, jvtype_id=6, status='O', jvstatus='R').exclude(id=4485).order_by('jvnum')
        jv_id = jvlist2.values_list('id', flat=True)

        detail = Jvdetail.objects.filter(status='O', jvmain_id__in=jv_id).values('chartofaccount_id','chartofaccount__main','chartofaccount__clas','chartofaccount__item',
                                                                                    'chartofaccount__cont','chartofaccount__sub',
                                                                                    'chartofaccount__accountcode','chartofaccount__description') \
                            .annotate(debitamount_sum=Sum('debitamount'), creditamount_sum=Sum('creditamount')).order_by('chartofaccount__accountcode')

        # jvlist2 = Jvmain.objects.all().filter(jvdate=ddate, jvtype_id=6, status='O', jvstatus='R').exclude(id=4485).order_by('jvnum')
        # jv_id = jvlist2.values_list('id', flat=True)
        #
        # detail = Jvdetail.objects.filter(status='O', jvmain_id__in=jv_id).values('chartofaccount_id',
        #                                                                          'chartofaccount__main',
        #                                                                          'chartofaccount__clas',
        #                                                                          'chartofaccount__item',
        #                                                                          'chartofaccount__cont',
        #                                                                          'chartofaccount__sub',
        #                                                                          'chartofaccount__accountcode',
        #                                                                          'chartofaccount__description') \
        #     .annotate(debitamount_sum=Sum('debitamount'), creditamount_sum=Sum('creditamount')).order_by(
        #     'chartofaccount__accountcode')

        for d in detail:

            # Update/Insert Subledgersummary Adjustment Year December
            subledgersummary = Subledgersummary.objects.filter(chartofaccount_id=d['chartofaccount_id'],year=str(yearend_year.year),month=12).first()

            if subledgersummary:
                subledsum_end_amount = 0
                subledsum_end_code = 'D'
                newsubledsum_end_amount = 0
                subledsum_ytd_amount = 0
                subledsum_ytd_code = 'D'
                newsubledsum_ytd_amount = 0
                subledsum_jv_totalcredit = 0
                subledsum_jv_totaldebit = 0

                if subledgersummary.end_code == 'C':
                    subledsum_end_amount = subledgersummary.end_amount * -1
                else:
                    subledsum_end_amount = subledgersummary.end_amount

                newsubledsum_end_amount = subledsum_end_amount + (d['debitamount_sum'] - d['creditamount_sum'])
                if d['creditamount_sum']:
                    subledsum_jv_totalcredit = subledgersummary.journal_voucher_credit_total + d['creditamount_sum']
                else:
                    subledsum_jv_totalcredit = subledgersummary.journal_voucher_credit_total
                if d['debitamount_sum']:
                    subledsum_jv_totaldebit = subledgersummary.journal_voucher_debit_total + d['debitamount_sum']
                else:
                    subledsum_jv_totaldebit = subledgersummary.journal_voucher_debit_total

                if newsubledsum_end_amount < 0:
                    subledsum_end_code = 'C'

                if subledgersummary.year_to_date_code == 'C':
                    subledsum_ytd_amount = subledgersummary.year_to_date_amount * -1
                else:
                    subledsum_ytd_amount = subledgersummary.year_to_date_amount

                newsubledsum_ytd_amount = subledsum_ytd_amount + (d['debitamount_sum'] - d['creditamount_sum'])

                if newsubledsum_ytd_amount < 0:
                    subledsum_ytd_code = 'C'

                # ## for data fixing
                # #if d['chartofaccount_id'] == 30 or d['chartofaccount_id'] == 178 or d['chartofaccount_id'] == 788:
                # if d['chartofaccount_id'] == 30 or d['chartofaccount_id'] == 178:
                #     print 'ignore'
                #     print d['chartofaccount_id']
                #
                # else:
                #     subledgersummary.end_amount = abs(newsubledsum_end_amount)
                #     subledgersummary.end_code = subledsum_end_code
                #     subledgersummary.end_date = str(yearend_year.year) + '-12-31'
                #     subledgersummary.year_to_date_amount = abs(newsubledsum_ytd_amount)
                #     subledgersummary.year_to_date_code = subledsum_ytd_code
                #     subledgersummary.year_to_date_date = str(yearend_year.year) + '-12-31'
                #     subledgersummary.journal_voucher_debit_total = subledsum_jv_totaldebit
                #     subledgersummary.journal_voucher_credit_total = subledsum_jv_totalcredit
                #     subledgersummary.save()

                subledgersummary.end_amount = abs(newsubledsum_end_amount)
                subledgersummary.end_code = subledsum_end_code
                subledgersummary.end_date = str(yearend_year.year) + '-12-31'
                subledgersummary.year_to_date_amount = abs(newsubledsum_ytd_amount)
                subledgersummary.year_to_date_code = subledsum_ytd_code
                subledgersummary.year_to_date_date = str(yearend_year.year) + '-12-31'
                subledgersummary.journal_voucher_debit_total = subledsum_jv_totaldebit
                subledgersummary.journal_voucher_credit_total = subledsum_jv_totalcredit
                subledgersummary.save()
            else:
                subledsum_end_amount = 0
                subledsum_end_code = 'D'
                newsubledsum_end_amount = 0
                subledsum_ytd_amount = 0
                subledsum_ytd_code = 'D'
                newsubledsum_ytd_amount = 0
                subledsum_jv_totalcredit = 0
                subledsum_jv_totaldebit = 0

                newsubledsum_end_amount = (d['debitamount_sum'] - d['creditamount_sum'])
                newsubledsum_ytd_amount = (d['debitamount_sum'] - d['creditamount_sum'])
                subledsum_jv_totaldebit = d['debitamount_sum']
                subledsum_jv_totalcredit = d['creditamount_sum']

                if newsubledsum_end_amount < 0:
                    subledsum_end_code = 'C'

                if newsubledsum_ytd_amount < 0:
                    subledsum_ytd_code = 'C'

                if d['chartofaccount_id'] == '1093':
                    print newsubledsum_end_amount
                    subledsum_ytd_code

                ## for datafixing
                #if d['chartofaccount_id'] == 30 or d['chartofaccount_id'] == 178 or d['chartofaccount_id'] == 788:
                # if d['chartofaccount_id'] == 30 or d['chartofaccount_id'] == 178:
                #     print 'ignore'
                #     print d['chartofaccount_id']
                #
                # else:
                #     print d['chartofaccount_id']
                #     print 'hoyoyoyo'
                #     Subledgersummary.objects.create(year=str(yearend_year.year), month=12,
                #                                     chartofaccount_id=d['chartofaccount_id'],
                #                                     beginning_amount=abs(newsubledsum_end_amount),
                #                                     beginning_code=subledsum_end_code,
                #                                     beginning_date=str(yearend_year.year) + '-12-31',
                #                                     end_amount=abs(newsubledsum_end_amount),
                #                                     end_code=subledsum_end_code,
                #                                     end_date=str(yearend_year.year) + '-12-31',
                #                                     year_to_date_amount=abs(newsubledsum_ytd_amount),
                #                                     year_to_date_code=subledsum_ytd_code,
                #                                     year_to_date_date=str(yearend_year.year) + '-12-31',
                #                                     journal_voucher_debit_total=subledsum_jv_totaldebit,
                #                                     journal_voucher_credit_total=subledsum_jv_totalcredit)




                Subledgersummary.objects.create(year=str(yearend_year.year), month=12, chartofaccount_id=d['chartofaccount_id'],
                                                beginning_amount=abs(newsubledsum_end_amount), beginning_code=subledsum_end_code,beginning_date=str(yearend_year.year) + '-12-31',
                                                end_amount=abs(newsubledsum_end_amount), end_code=subledsum_end_code,end_date=str(yearend_year.year) + '-12-31',
                                                year_to_date_amount=abs(newsubledsum_ytd_amount), year_to_date_code=subledsum_ytd_code,year_to_date_date=str(yearend_year.year) + '-12-31',
                                                journal_voucher_debit_total = subledsum_jv_totaldebit, journal_voucher_credit_total=subledsum_jv_totalcredit)
                print 'new ata ito'


            # update chart main 1,2,3
            if d['chartofaccount__main'] == 1 or d['chartofaccount__main'] == 2 or d['chartofaccount__main'] == 3:

                chart = Chartofaccount.objects.filter(pk=d['chartofaccount_id']).first()
                beg_amount = 0
                beg_code = 'D'
                end_amount = 0
                end_code = 'D'
                new_beg_amount = 0
                new_end_amount = 0

                if chart.beginning_code == 'C':
                    beg_amount = chart.beginning_amount * -1
                else:
                    beg_amount = chart.beginning_amount

                new_beg_amount = beg_amount + (d['debitamount_sum'] - d['creditamount_sum'])

                if new_beg_amount < 0:
                    beg_code = 'C'

                if chart.end_code == 'C':
                    end_amount = chart.end_amount * -1
                else:
                    end_amount = chart.end_amount

                new_end_amount = end_amount + (d['debitamount_sum'] - d['creditamount_sum'])

                if new_end_amount < 0:
                    end_code = 'C'

                print str(chart.accountcode) + ' update beg and end'

                chart.beginning_amount = abs(new_beg_amount)
                chart.beginning_code = beg_code
                chart.beginning_date = str(yearend_year.year) + '-12-31'
                chart.end_amount = abs(new_end_amount)
                chart.end_code = end_code
                chart.end_date = str(yearend_year.year) + '-12-31'
                chart.save()

                # for cash in bank
                if d['chartofaccount_id'] == company.coa_cashinbank_id:
                    print 'hello cash in bank'
                    # update bank account file
                    jv_cash = Jvdetail.objects.filter(status='O', jvmain_id__in=jv_id, chartofaccount_id=company.coa_cashinbank_id).values('bankaccount_id', 'bankaccount__code')\
                        .annotate(debitamount_sum=Sum('debitamount'), creditamount_sum=Sum('creditamount'))\
                        .order_by('bankaccount_id')

                    print jv_cash

                    for c in jv_cash:
                        bankacount = Bankaccount.objects.filter(pk=c['bankaccount_id']).first()

                        bankaccount_beg_amount = 0
                        bankaccount_beg_code = 'D'
                        bankaccount_end_amount = 0
                        bankaccount_end_code = 'D'
                        bankaccount_new_beg_amount = 0
                        bankaccount_new_end_amount = 0

                        print bankacount

                        if bankacount.beg_code == 'C':
                            bankaccount_beg_amount = bankacount.beg_amount * -1
                        else:
                            bankaccount_beg_amount = bankacount.beg_amount

                        print c['debitamount_sum']
                        print c['creditamount_sum']
                        print bankacount

                        bankaccount_new_beg_amount = bankaccount_beg_amount + (c['debitamount_sum'] - c['creditamount_sum'])

                        if bankaccount_new_beg_amount < 0:
                            bankaccount_beg_code = 'C'

                        bankaccount_end_amount = 0
                        if bankacount.run_code == 'C':
                            bankaccount_end_amount = bankacount.run_amount * -1
                        else:
                            bankaccount_end_amount = bankacount.run_amount

                        print 'hehey'
                        if bankaccount_end_amount is None:
                            print 'ito na'
                            bankaccount_end_amount = 0

                        bankaccount_end_amount = bankaccount_end_amount + (c['debitamount_sum'] - c['creditamount_sum'])

                        if bankaccount_end_amount < 0:
                            bankaccount_end_code = 'C'

                        print str(bankacount.code) + ' update beg and run'

                        bankacount.beg_amount = abs(bankaccount_new_beg_amount)
                        bankacount.beg_code = bankaccount_beg_code
                        bankacount.beg_date = str(yearend_year.year) + '-12-31'
                        bankacount.run_amount = abs(bankaccount_end_amount)
                        bankacount.run_code = bankaccount_end_code
                        bankacount.run_date = str(yearend_year.year) + '-12-31'
                        bankacount.save()

                        #update Bank account summary
                        bankaccountsum = Bankaccountsummary.objects.filter(bankaccount_id=c['bankaccount_id'], year=str(yearend_year.year)).first()

                        if bankaccountsum:

                            bankaccountsum_ytd_amount = 0
                            bankaccountsum_ytd_code = 'D'

                            if bankaccountsum.year_to_date_code == 'C':
                                bankaccountsum_ytd_amount = bankaccountsum.year_to_date_amount * -1
                            else:
                                bankaccountsum_ytd_amount = bankaccountsum.year_to_date_amount

                                bankaccountsum_ytd_amount = bankaccountsum_ytd_amount + (c['debitamount_sum'] - c['creditamount_sum'])

                            if bankaccountsum_ytd_code < 0:
                                bankaccountsum_ytd_code = 'C'

                            bankaccountsum.beg_amount = abs(bankaccount_new_beg_amount)
                            bankaccountsum.beg_code = bankaccount_beg_code
                            bankaccountsum.beg_date = str(yearend_year.year) + '-12-31'
                            bankaccountsum.year_to_date_amount = abs(bankaccountsum_ytd_amount)
                            bankaccountsum.year_to_date_code = bankaccountsum_ytd_code
                            bankaccountsum.year_to_date_date = str(yearend_year.year) + '-12-31'
                            bankaccountsum.save()
                            print 'meron'
                        else:
                            Bankaccountsummary.objects.create(year=str(yearend_year.year), code=bankacount.code, accountnumber=bankacount.accountnumber, bankaccount_id=bankacount.id,
                                                              beg_amount=abs(bankaccount_new_beg_amount), beg_code=bankaccount_beg_code, beg_date=str(yearend_year.year) + '-12-31',
                                                              year_to_date_amount=abs(bankaccount_new_beg_amount),year_to_date_code=bankaccount_beg_code,year_to_date_date=str(yearend_year.year) + '-12-31')
                            print 'wala'

                else:
                    print 'ordinary'
            else:
                dec_cur_debit_amt += d['debitamount_sum']
                dec_cur_credit_amt += d['creditamount_sum']

        detailexpense = Jvdetail.objects.filter(status='O', jvmain_id__in=jv_id, chartofaccount__main=5).values('chartofaccount_id','chartofaccount__main', 'chartofaccount__clas',
                                                                                 'chartofaccount__item', 'chartofaccount__cont', 'chartofaccount__sub',
                                                                                'chartofaccount__accountcode','chartofaccount__description', 'department__code', 'department__id')\
            .annotate(debitamount_sum=Sum('debitamount'), creditamount_sum=Sum('creditamount')).order_by('chartofaccount__accountcode')

        for de in detailexpense:
            print de['chartofaccount_id']
            print de['department__id']

            acctexp = Accountexpensebalance.objects.filter(chartofaccount_id=de['chartofaccount_id'], department_id=de['department__id'], year=str(yearend_year.year), month=12).first()

            acctexpamount = 0
            acctexpcode = 'D'


            if acctexp:
                acctexpamount = acctexp.amount + (de['debitamount_sum'] - de['creditamount_sum'])
                if acctexpamount < 0:
                    acctexpcode = 'C'

                acctexp.amount = abs(acctexpamount)
                acctexp.code = acctexpcode
                acctexp.modifyby = request.user
                acctexp.modifydate = datetime.datetime.now()
                acctexp.save()

                print 'exist'
            else:
                acctexpamount = (de['debitamount_sum'] - de['creditamount_sum'])
                if acctexpamount < 0:
                    acctexpcode = 'C'

                print 'new'
                print de['chartofaccount_id']
                print de['department__id']
                print acctexp

                Accountexpensebalance.objects.create(year=str(yearend_year.year), month=12, date=str(yearend_year.year) + '-12-31',
                                                     chartofaccount_id=de['chartofaccount_id'], department_id=de['department__id'],
                                                     amount=abs(acctexpamount), code=acctexpcode)

            #print str(acctexp)
            #print str(de['chartofaccount_id'])+' '+str(de['department__id'])+' '+str(de['department__code'])+' '+str(de['debitamount_sum'])+' '+str(de['creditamount_sum'])

        detailothers = Jvdetail.objects.filter(status='O', jvmain_id__in=jv_id).values('chartofaccount_id','chartofaccount__main','chartofaccount__clas',
                                                                                 'chartofaccount__item','chartofaccount__cont','chartofaccount__sub',
                                                                                 'chartofaccount__accountcode','chartofaccount__description') \
            .annotate(debitamount_sum=Sum('debitamount'), creditamount_sum=Sum('creditamount')).order_by('chartofaccount__accountcode')

        for deo in detailothers:
            # update chart main 1,2,3
            if deo['chartofaccount__main'] == 1 or deo['chartofaccount__main'] == 2 or deo['chartofaccount__main'] == 3:
                print 'the month'
                for i in range(company.last_closed_date.month):
                    subledgersummary = Subledgersummary.objects.filter(chartofaccount_id=deo['chartofaccount_id'],year=str(company.last_closed_date.year), month=str(i + 1)).first()

                    if subledgersummary:
                        subledsum_end_amount = 0
                        subledsum_end_code = 'D'
                        newsubledsum_end_amount = 0
                        subledsum_ytd_amount = 0
                        subledsum_ytd_code = 'D'
                        newsubledsum_ytd_amount = 0
                        subledsum_jv_totalcredit = 0
                        subledsum_jv_totaldebit = 0

                        if subledgersummary.end_code == 'C':
                            subledsum_end_amount = subledgersummary.end_amount * -1
                        else:
                            subledsum_end_amount = subledgersummary.end_amount

                        newsubledsum_end_amount = subledsum_end_amount + (deo['debitamount_sum'] - deo['creditamount_sum'])
                        if deo['creditamount_sum']:
                            subledsum_jv_totalcredit = subledgersummary.journal_voucher_credit_total + deo['creditamount_sum']
                        else:
                            subledsum_jv_totalcredit = subledgersummary.journal_voucher_credit_total
                        if deo['debitamount_sum']:
                            subledsum_jv_totaldebit = subledgersummary.journal_voucher_debit_total + deo['debitamount_sum']
                        else:
                            subledsum_jv_totaldebit = subledgersummary.journal_voucher_debit_total

                        if newsubledsum_end_amount < 0:
                            subledsum_end_code = 'C'

                        if subledgersummary.year_to_date_code == 'C':
                            subledsum_ytd_amount = subledgersummary.year_to_date_amount * -1
                        else:
                            subledsum_ytd_amount = subledgersummary.year_to_date_amount

                        newsubledsum_ytd_amount = subledsum_ytd_amount + (deo['debitamount_sum'] - deo['creditamount_sum'])

                        if newsubledsum_ytd_amount < 0:
                            subledsum_ytd_code = 'C'

                        subledgersummary.end_amount = abs(newsubledsum_end_amount)
                        subledgersummary.end_code = subledsum_end_code
                        subledgersummary.end_date = str(yearend_year.year) + '-12-31'
                        subledgersummary.year_to_date_amount = abs(newsubledsum_ytd_amount)
                        subledgersummary.year_to_date_code = subledsum_ytd_code
                        subledgersummary.year_to_date_date = str(yearend_year.year) + '-12-31'
                        subledgersummary.save()
                    else:
                        subledsum_end_amount = 0
                        subledsum_end_code = 'D'
                        newsubledsum_end_amount = 0
                        subledsum_ytd_amount = 0
                        subledsum_ytd_code = 'D'
                        newsubledsum_ytd_amount = 0
                        subledsum_jv_totalcredit = 0
                        subledsum_jv_totaldebit = 0

                        newsubledsum_end_amount = (deo['debitamount_sum'] - deo['creditamount_sum'])
                        newsubledsum_ytd_amount = (deo['debitamount_sum'] - deo['creditamount_sum'])
                        subledsum_jv_totalcredit = deo['debitamount_sum']
                        subledsum_jv_totaldebit = deo['creditamount_sum']

                        if newsubledsum_end_amount < 0:
                            subledsum_end_code = 'C'

                        if newsubledsum_ytd_amount < 0:
                            subledsum_ytd_code = 'C'

                        Subledgersummary.objects.create(year=str(company.last_closed_date.year), month=str(i + 1),
                                                        chartofaccount_id=deo['chartofaccount_id'],
                                                        beginning_amount=abs(newsubledsum_end_amount),
                                                        beginning_code=subledsum_end_code,
                                                        beginning_date=str(yearend_year.year) + '-12-31',
                                                        end_amount=abs(newsubledsum_end_amount),
                                                        end_code=subledsum_end_code,
                                                        end_date=str(yearend_year.year) + '-12-31',
                                                        year_to_date_amount=abs(newsubledsum_ytd_amount),
                                                        year_to_date_code=subledsum_ytd_code,
                                                        year_to_date_date=str(yearend_year.year) + '-12-31')

        # update december current earnings
        dec_cur_amount = dec_cur_debit_amt - dec_cur_credit_amt

        print dec_cur_amount

        if dec_cur_amount < 0:
            dec_cur_code = 'C'

        subledgersummary_cur = Subledgersummary.objects.filter(chartofaccount_id=company.coa_currentearnings_id,year=str(yearend_year.year), month=12).first()

        if subledgersummary_cur:
            print 'subledgersummary_cur'
            subledsum_end_amount = 0
            subledsum_end_code = 'D'
            newsubledsum_end_amount = 0
            subledsum_ytd_amount = 0
            subledsum_ytd_code = 'D'
            newsubledsum_ytd_amount = 0

            if subledgersummary_cur.end_code == 'C':
                subledsum_end_amount = subledgersummary_cur.end_amount * -1
            else:
                subledsum_end_amount = subledgersummary_cur.end_amount
            print subledsum_end_amount
            newsubledsum_end_amount = subledsum_end_amount + dec_cur_amount

            if newsubledsum_end_amount < 0:
                subledsum_end_code = 'C'

            if subledgersummary_cur.year_to_date_code == 'C':
                subledsum_ytd_amount = subledgersummary_cur.year_to_date_amount * -1
            else:
                subledsum_ytd_amount = subledgersummary_cur.year_to_date_amount
            print subledsum_ytd_amount
            newsubledsum_ytd_amount = subledsum_ytd_amount + dec_cur_amount

            if newsubledsum_ytd_amount < 0:
                subledsum_ytd_code = 'C'

            print 'start updating'
            subledgersummary_cur.end_amount = abs(newsubledsum_end_amount)
            subledgersummary_cur.end_code = subledsum_end_code
            subledgersummary_cur.end_date = str(yearend_year.year) + '-12-31'
            subledgersummary_cur.year_to_date_amount = abs(newsubledsum_ytd_amount)
            subledgersummary_cur.year_to_date_code = subledsum_ytd_code
            subledgersummary_cur.year_to_date_date = str(yearend_year.year) + '-12-31'
            subledgersummary_cur.save()
            print 'end updating'

        # update retained earning dec
        chart_ret = Chartofaccount.objects.filter(id=company.coa_retainedearnings_id).first()

        beg_ret_amount = 0
        beg_new_ret_amount = 0
        beg_ret_code = 'D'
        end_ret_amount = 0
        end_new_ret_amount = 0
        end_ret_code = 'D'

        if chart_ret:
            if chart_ret.beginning_code == 'C':
                beg_ret_amount = chart_ret.beginning_amount * -1
            else:
                beg_ret_amount = chart_ret.beginning_amount

            beg_new_ret_amount = beg_ret_amount + dec_cur_amount

            if beg_new_ret_amount < 0:
                beg_ret_code = 'C'

            chart_ret.beginning_amount = abs(beg_new_ret_amount)
            chart_ret.beginning_code = beg_ret_code
            chart_ret.beginning_date = str(yearend_year.year) + '-12-31'
            chart_ret.end_amount = abs(beg_new_ret_amount)
            chart_ret.end_code = beg_ret_code
            chart_ret.end_date = str(yearend_year.year) + '-12-31'
            chart_ret.save()

            # update other month
            for i in range(company.last_closed_date.month):
                subledgersummary = Subledgersummary.objects.filter(chartofaccount_id=company.coa_retainedearnings_id,year=str(company.last_closed_date.year),month=str(i + 1)).first()

                if subledgersummary:
                    subledgersummary.beginning_amount = abs(beg_new_ret_amount)
                    subledgersummary.beginning_code = beg_ret_code
                    subledgersummary.beginning_date = str(yearend_year.year) + '-12-31'
                    subledgersummary.end_amount = abs(beg_new_ret_amount)
                    subledgersummary.end_code = beg_ret_code
                    subledgersummary.save()


        print 'tuloy'

        data = {'status': 'success'}
    else:
        data = {'status': 'error'}

    return JsonResponse(data)

    #jv_id = jvlist.values_list('id',flat=True)

    #jv_detail = Jvdetail.objects.filter(status='A', jvmain_id__in=jv_id).values('chartofaccount_id','chartofaccount__accountcode','chartofaccount__description') \
        #.annotate(debitamount_sum=Sum('debitamount'), creditamount_sum=Sum('creditamount')).order_by('chartofaccount__accountcode')
