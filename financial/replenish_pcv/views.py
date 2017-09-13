from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView
from utils.mixins import ReportContentMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from . models import Reppcvmain, Reppcvdetail
from ataxcode.models import Ataxcode
from branch.models import Branch
from chartofaccount.models import Chartofaccount
from companyparameter.models import Companyparameter
from creditterm.models import Creditterm
from currency.models import Currency
from inputvattype.models import Inputvattype
from oftype.models import Oftype
from ofsubtype.models import Ofsubtype
from supplier.models import Supplier
from vat.models import Vat
from wtax.models import Wtax
from employee.models import Employee
from department.models import Department
from inputvat.models import Inputvat
from operationalfund. models import Ofmain, Ofdetail, Ofdetailtemp, Ofdetailbreakdown, Ofdetailbreakdowntemp, Ofitem, Ofitemtemp
from acctentry.views import generatekey, querystmtdetail, querytotaldetail, savedetail, updatedetail, updateallquery, \
    validatetable, deleteallquery
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime
from endless_pagination.views import AjaxListView
from annoying.functions import get_object_or_None
from easy_pdf.views import PDFTemplateView
import json
from pprint import pprint
from dateutil.relativedelta import relativedelta


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Reppcvmain
    template_name = 'replenish_pcv/index.html'
    page_template = 'replenish_pcv/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Reppcvmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(reppcvnum__icontains=keysearch) |
                                 Q(reppcvdate__icontains=keysearch) |
                                 Q(cvmain__cvnum__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query

    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)

        context['listcount'] = Ofmain.objects.all().count()
        context['canbeapproved'] = Ofmain.objects.filter(Q(ofstatus='F') | Q(ofstatus='A') | Q(ofstatus='D')).\
            filter(isdeleted=0).count()
        context['forapproval'] = Ofmain.objects.filter(designatedapprover=self.request.user).count()
        context['userrole'] = 'C' if self.request.user.has_perm('operationalfund.is_cashier') else 'U'

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(ListView):
    model = Ofmain
    template_name = 'replenish_pcv/create.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Ofmain.objects.all().filter(isdeleted=0, ofstatus='R', oftype__code='PCV', reppcvmain=None).\
            order_by('ofnum')

        if self.request.GET:
            if self.request.GET['ofdatefrom']:
                query = query.filter(ofdate__gte=self.request.GET['ofdatefrom'])
            if self.request.GET['ofdateto']:
                query = query.filter(ofdate__lte=self.request.GET['ofdateto'])

        return query

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['oftype'] = Oftype.objects.filter(code='PCV', isdeleted=0)
        if self.request.GET:
            context['ofdatefrom'] = self.request.GET['ofdatefrom']
            context['ofdateto'] = self.request.GET['ofdateto']

        return context


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Reppcvmain
    template_name = 'replenish_pcv/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['reppcvmain'] = Reppcvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['reppcvdetail'] = Reppcvdetail.objects.filter(reppcvmain=self.kwargs['pk'], isdeleted=0).\
            order_by('ofmain_id')
        context['ofitem'] = Ofitem.objects.filter(isdeleted=0, status='A', ofmain__reppcvmain=self.kwargs['pk'],
                                                  ofitemstatus='A')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedreppcv = Reppcvmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedreppcv.print_ctr += 1
        printedreppcv.save()
        return context


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Ofmain
    template_name = 'replenish_pcv/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Ofmain
    template_name = 'replenish_pcv/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0
        query = ''

        if self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name) == 's':
            context['report_type'] = "Petty Cash Replenishment Summary Report"
            query = Reppcvmain.objects.all().filter(isdeleted=0)

            if self.request.COOKIES.get('rep_f_numfrom_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_numfrom_' + self.request.resolver_match.app_name))
                query = query.filter(reppcvnum__gte=int(key_data))
            if self.request.COOKIES.get('rep_f_numto_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_numto_' + self.request.resolver_match.app_name))
                query = query.filter(reppcvnum__lte=int(key_data))

            if self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name))
                query = query.filter(reppcvdate__gte=key_data)
            if self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name))
                query = query.filter(reppcvdate__lte=key_data)

            if self.request.COOKIES.get('rep_f_status_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_status_' + self.request.resolver_match.app_name))
                if key_data == 'req':
                    query = query.filter(cvmain__isnull=True)
                elif key_data == 'rep':
                    query = query.filter(cvmain__isnull=False)

            if self.request.COOKIES.get('rep_f_order_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_order_' + self.request.resolver_match.app_name))
                if key_data != 'null':
                    key_data = key_data.split(",")
                    query = query.order_by(*key_data)
        elif self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name) == 'd':
            context['report_type'] = "Petty Cash Replenishment Detailed Report"
            defaultorder = ['ofmain__reppcvmain__reppcvnum', 'ofmain__reppcvmain__cvmain__cvnum',
                            'ofmain__ofnum', 'ofsubtype__description']

            query = Ofitem.objects.all().filter(isdeleted=0,
                                                ofitemstatus='A',
                                                ofmain__isnull=False,
                                                ofmain__reppcvdetail__isnull=False,
                                                ofmain__reppcvmain__isnull=False)

            if self.request.COOKIES.get('rep_f_status_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_status_' + self.request.resolver_match.app_name))
                if key_data == 'req':
                    query = query.filter(ofmain__reppcvmain__cvmain__isnull=True)
                elif key_data == 'rep':
                    query = query.filter(ofmain__reppcvmain__cvmain__isnull=False)

            if self.request.COOKIES.get('rep_f_numfrom_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_numfrom_' + self.request.resolver_match.app_name))
                query = query.filter(ofmain__reppcvmain__reppcvnum__gte=int(key_data))
            if self.request.COOKIES.get('rep_f_numto_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_numto_' + self.request.resolver_match.app_name))
                query = query.filter(ofmain__reppcvmain__reppcvnum__lte=int(key_data))

            if self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name))
                query = query.filter(ofmain__reppcvmain__reppcvdate__gte=key_data)
            if self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name))
                query = query.filter(ofmain__reppcvmain__reppcvdate__lte=key_data)

            if self.request.COOKIES.get('rep_f_order2_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_order2_' + self.request.resolver_match.app_name))
                if key_data != 'null':
                    defaultorder = key_data.split(",")

            query = query.order_by(*defaultorder)

        elif self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name) == 'a_s'\
                or self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name) == 'a_d':
            query = Ofdetail.objects.all().filter(isdeleted=0, ofmain__reppcvmain__isnull=False)

            if self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name) == 'a_d':
                if self.request.COOKIES.get('rep_f_debit_amountfrom_' + self.request.resolver_match.app_name):
                    key_data = str(self.request.COOKIES.get('rep_f_debit_amountfrom_' + self.request.resolver_match.app_name))
                    query = query.filter(debitamount__gte=float(key_data.replace(',', '')))
                if self.request.COOKIES.get('rep_f_debit_amountto_' + self.request.resolver_match.app_name):
                    key_data = str(self.request.COOKIES.get('rep_f_debit_amountto_' + self.request.resolver_match.app_name))
                    query = query.filter(debitamount__lte=float(key_data.replace(',', '')))

                if self.request.COOKIES.get('rep_f_credit_amountfrom_' + self.request.resolver_match.app_name):
                    key_data = str(self.request.COOKIES.get('rep_f_credit_amountfrom_' + self.request.resolver_match.app_name))
                    query = query.filter(creditamount__gte=float(key_data.replace(',', '')))
                if self.request.COOKIES.get('rep_f_credit_amountto_' + self.request.resolver_match.app_name):
                    key_data = str(self.request.COOKIES.get('rep_f_credit_amountto_' + self.request.resolver_match.app_name))
                    query = query.filter(creditamount__lte=float(key_data.replace(',', '')))

            if self.request.COOKIES.get('rep_f_numfrom_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_numfrom_' + self.request.resolver_match.app_name))
                query = query.filter(ofmain__reppcvmain__reppcvnum__gte=int(key_data))
            if self.request.COOKIES.get('rep_f_numto_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_numto_' + self.request.resolver_match.app_name))
                query = query.filter(ofmain__reppcvmain__reppcvnum__lte=int(key_data))

            if self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name))
                query = query.filter(ofmain__reppcvmain__reppcvdate__gte=key_data)
            if self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name))
                query = query.filter(ofmain__reppcvmain__reppcvdate__lte=key_data)

            if self.request.COOKIES.get('rep_f_status_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_status_' + self.request.resolver_match.app_name))
                if key_data == 'req':
                    query = query.filter(ofmain__reppcvmain__cvmain__isnull=True)
                elif key_data == 'rep':
                    query = query.filter(ofmain__reppcvmain__cvmain__isnull=False)

            if self.request.COOKIES.get('rep_f_balancecode_' + self.request.resolver_match.app_name) == 'd':
                query = query.filter(balancecode='D')
            elif self.request.COOKIES.get('rep_f_balancecode_' + self.request.resolver_match.app_name) == 'c':
                query = query.filter(balancecode='C')

            context['report_total'] = query.aggregate(Sum('debitamount'), Sum('creditamount'))

            if self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name) == 'a_s':
                context['report_type'] = "Petty Cash Replenishment Accounting Entry - Summary Report"

                query = query.values('chartofaccount__accountcode',
                                     'chartofaccount__title',
                                     'chartofaccount__description',
                                     'bankaccount__accountnumber',
                                     'department__departmentname',
                                     'employee__firstname',
                                     'supplier__name',
                                     'customer__name',
                                     'unit__description',
                                     'branch__description',
                                     'product__description',
                                     'inputvat__description',
                                     'outputvat__description',
                                     'vat__description',
                                     'wtax__description',
                                     'ataxcode__code')\
                             .annotate(Sum('debitamount'), Sum('creditamount'))\
                             .order_by('chartofaccount__accountcode',
                                       'bankaccount__accountnumber',
                                       'department__departmentname',
                                       'employee__firstname',
                                       'supplier__name',
                                       'customer__name',
                                       'unit__description',
                                       'branch__description',
                                       'product__description',
                                       'inputvat__description',
                                       'outputvat__description',
                                       '-vat__description',
                                       'wtax__description',
                                       'ataxcode__code')
            else:
                context['report_type'] = "Petty Cash Replenishment Accounting Entry - Detailed Report"

                query = query.annotate(Sum('debitamount'), Sum('creditamount')).order_by('chartofaccount__accountcode',
                                                                                         'bankaccount__accountnumber',
                                                                                         'department__departmentname',
                                                                                         'employee__firstname',
                                                                                         'supplier__name',
                                                                                         'customer__name',
                                                                                         'unit__description',
                                                                                         'branch__description',
                                                                                         'product__description',
                                                                                         'inputvat__description',
                                                                                         'outputvat__description',
                                                                                         '-vat__description',
                                                                                         'wtax__description',
                                                                                         'ataxcode__code',
                                                                                         'of_num')

        if self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name) == 's' \
                or self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name) == 'd':
            if self.request.COOKIES.get('rep_f_amountfrom_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_amountfrom_' + self.request.resolver_match.app_name))
                query = query.filter(amount__gte=float(key_data.replace(',', '')))
            if self.request.COOKIES.get('rep_f_amountto_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_amountto_' + self.request.resolver_match.app_name))
                query = query.filter(amount__lte=float(key_data.replace(',', '')))

            if self.request.COOKIES.get('rep_f_asc_' + self.request.resolver_match.app_name):
                key_data = str(self.request.COOKIES.get('rep_f_asc_' + self.request.resolver_match.app_name))

                if key_data == 'd':
                    query = query.reverse()

            context['report_total'] = query.aggregate(Sum('amount'))

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "Petty Cash Replenishment"
        context['rc_title'] = "Petty Cash Replenishment"

        return context


@csrf_exempt
def replenish(request):
    if request.method == 'POST':
        year = str(datetime.date.today().year)
        yearqs = Reppcvmain.objects.filter(reppcvnum__startswith=year)

        if yearqs:
            reppcvnumlast = yearqs.latest('reppcvnum')
            latestreppcvnum = str(reppcvnumlast)
            print "latest: " + latestreppcvnum

            reppcvnum = year
            last = str(int(latestreppcvnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                reppcvnum += '0'
            reppcvnum += last

        else:
            reppcvnum = year + '000001'

        print 'reppcvnum: ' + reppcvnum

        newreppcv = Reppcvmain()
        newreppcv.reppcvnum = reppcvnum
        newreppcv.reppcvdate = datetime.date.today()
        newreppcv.enterby = request.user
        newreppcv.modifyby = request.user
        newreppcv.save()

        total_amount = 0
        replenishedofs = Ofmain.objects.filter(id__in=request.POST.getlist('pcv_checkbox'))
        for data in replenishedofs:
            newreppcvdetail = Reppcvdetail()
            newreppcvdetail.amount = data.approvedamount
            newreppcvdetail.enterby = request.user
            newreppcvdetail.modifyby = request.user
            newreppcvdetail.ofmain = Ofmain.objects.get(pk=data.id)
            newreppcvdetail.reppcvmain = newreppcv
            total_amount += newreppcvdetail.amount
            newreppcvdetail.save()
            data.reppcvdetail = newreppcvdetail
            data.reppcvmain = newreppcv
            data.save()

        newreppcv.amount = total_amount
        newreppcv.save()
        print "PCV successfully replenished."
    else:
        print "Something went wrong in saving REPPCV."
    return redirect('/replenish_pcv/')


@csrf_exempt
def fetch_details(request):
    if request.method == 'POST':
        details = Reppcvdetail.objects.filter(isdeleted=0, reppcvmain__reppcvnum=request.POST['reppcvnum'])

        details_list = []

        for data in details:
            details_list.append([data.id,
                                 'OF-' + data.ofmain.oftype.code + '-' + data.ofmain.ofnum,
                                 data.ofmain.ofdate,
                                 data.ofmain.particulars,
                                 data.amount,
                                 ])

        data = {
            'status': 'success',
            'detail': details_list
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)
