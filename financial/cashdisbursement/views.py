from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from checkvoucher.models import Cvmain, Cvdetail
from django.utils.dateformat import DateFormat
from utils.mixins import ReportContentMixin
from easy_pdf.views import PDFTemplateView
from datetime import datetime
from django.db.models import Sum


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'cashdisbursement/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    template_name = 'cashdisbursement/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        report_total = 0
        query = Cvdetail.objects.all().filter(status='A').filter(isdeleted=0)

        if self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name):
            key_data = str(self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name))
        else:
            key_data = DateFormat(datetime.now()).format('Y-m-d')
        query = query.filter(cv_date__gte=key_data)

        if self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name):
            key_data = str(self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name))
        else:
            key_data = DateFormat(datetime.now()).format('Y-m-d')
        query = query.filter(cv_date__lte=key_data)

        if self.request.COOKIES.get('rep_f_status_' + self.request.resolver_match.app_name):
            key_data = self.request.COOKIES.get('rep_f_status_' + self.request.resolver_match.app_name)
            query = query.filter(cvmain__cvstatus=key_data)

        if context['report'] == 's':
            context['rc_title'] = "Summary Entries"

            report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

            query = query.values('chartofaccount__accountcode', 'chartofaccount__description')\
                    .annotate(Sum('debitamount'), Sum('creditamount'))\
                    .order_by('chartofaccount__accountcode')

        elif context['report'] == 'b':
            context['rc_title'] = "Summary of Cash in Bank"

            query = query.filter(chartofaccount__accountcode='1112000000').exclude(bankaccount__isnull=True)

            report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

            query = query.values('bankaccount__code', 'bankaccount__bank__code', 'bankaccount__run_code')\
                         .annotate(Sum('debitamount'), Sum('creditamount'))\
                         .order_by('bankaccount__code')

        context['data_list'] = query
        context['report_total'] = report_total

        if self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name):
            context['datefrom'] = self.request.COOKIES.get('rep_f_datefrom_' + self.request.resolver_match.app_name)
            context['datefrom'] = datetime.strptime(context['datefrom'], "%Y-%m-%d").date()
            context['datefrom'] = DateFormat(context['datefrom']).format('F d, Y')
        else:
            context['datefrom'] = DateFormat(datetime.now()).format('F d, Y')

        if self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name):
            context['dateto'] = self.request.COOKIES.get('rep_f_dateto_' + self.request.resolver_match.app_name)
            context['dateto'] = datetime.strptime(context['dateto'], "%Y-%m-%d").date()
            context['dateto'] = DateFormat(context['dateto']).format('F d, Y')
        else:
            context['dateto'] = DateFormat(datetime.now()).format('F d, Y')

        context['datenow'] = DateFormat(datetime.now()).format('m/d/Y')

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "CASH DISBURSEMENT BOOK"
        context['rc_font'] = "Times New Roman"

        return context
