from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from journalvoucher.models import Jvdetail
from officialreceipt.models import Ordetail
from checkvoucher.models import Cvdetail
from django.db.models import Sum


@method_decorator(login_required, name='dispatch')
class GeneralJournalBookView(TemplateView):
    template_name = 'rep_generalledger/generaljournalbook.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Jvdetail.objects.filter(jvmain__isdeleted=0, jvmain__status='A', status='A', isdeleted=0).exclude(jvmain=None)
        querytotal = ''

        if self.request.GET:

            if self.request.GET['rep_datefrom']:
                key_data = str(self.request.GET['rep_datefrom'])
                query = query.filter(jvmain__jvdate__gte=key_data)
            if self.request.GET['rep_dateto']:
                key_data = str(self.request.GET['rep_dateto'])
                query = query.filter(jvmain__jvdate__lte=key_data)
            if self.request.GET['rep_status']:
                key_data = str(self.request.GET['rep_status'])
                query = query.filter(jvmain__jvstatus=key_data)

            querytotal = query.aggregate(Sum('debitamount'), Sum('creditamount'))

            if self.request.GET['rep_type'] == 's':
                query = query.values('chartofaccount__accountcode',
                                     'chartofaccount__title',
                                     'chartofaccount__description',
                                     'bankaccount__accountnumber',
                                     'department__departmentname',
                                     'employee__firstname',
                                     'employee__lastname',
                                     'supplier__name',
                                     'customer__name',
                                     'unit__description',
                                     'branch__description',
                                     'product__description',
                                     'inputvat__description',
                                     'outputvat__description',
                                     'vat__description',
                                     'wtax__description',
                                     'ataxcode__code',
                                     'balancecode') \
                            .annotate(Sum('debitamount'), Sum('creditamount')) \
                            .order_by('-balancecode',
                                      '-chartofaccount__accountcode',
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
                query = query.annotate(Sum('debitamount'), Sum('creditamount')).order_by('jv_num',
                                                                                         '-balancecode',
                                                                                         '-chartofaccount__accountcode',
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

            context['rep_datefrom'] = self.request.GET['rep_datefrom']
            context['rep_dateto'] = self.request.GET['rep_dateto']
            context['rep_type'] = self.request.GET['rep_type']
            context['rep_status'] = self.request.GET['rep_status']

        context['query'] = query
        context['querytotal'] = querytotal

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class CashReceiptsBookView(TemplateView):
    template_name = 'rep_generalledger/cashreceiptsbook.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Ordetail.objects.filter(ormain__isdeleted=0, ormain__status='A', status='A', isdeleted=0).exclude(ormain=None)
        querytotal = ''

        if self.request.GET:

            if self.request.GET['rep_datefrom']:
                key_data = str(self.request.GET['rep_datefrom'])
                query = query.filter(ormain__ordate__gte=key_data)
            if self.request.GET['rep_dateto']:
                key_data = str(self.request.GET['rep_dateto'])
                query = query.filter(ormain__ordate__lte=key_data)
            if self.request.GET['rep_status']:
                key_data = str(self.request.GET['rep_status'])
                query = query.filter(ormain__orstatus=key_data)

            querytotal = query.aggregate(Sum('debitamount'), Sum('creditamount'))

            if self.request.GET['rep_type'] == 's':
                query = query.values('chartofaccount__accountcode',
                                     'chartofaccount__title',
                                     'chartofaccount__description',
                                     'bankaccount__accountnumber',
                                     'department__departmentname',
                                     'employee__firstname',
                                     'employee__lastname',
                                     'supplier__name',
                                     'customer__name',
                                     'unit__description',
                                     'branch__description',
                                     'product__description',
                                     'inputvat__description',
                                     'outputvat__description',
                                     'vat__description',
                                     'wtax__description',
                                     'ataxcode__code',
                                     'balancecode') \
                            .annotate(Sum('debitamount'), Sum('creditamount')) \
                            .order_by('-balancecode',
                                      '-chartofaccount__accountcode',
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
                query = query.annotate(Sum('debitamount'), Sum('creditamount')).order_by('or_num',
                                                                                         '-balancecode',
                                                                                         '-chartofaccount__accountcode',
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

            context['rep_datefrom'] = self.request.GET['rep_datefrom']
            context['rep_dateto'] = self.request.GET['rep_dateto']
            context['rep_type'] = self.request.GET['rep_type']
            context['rep_status'] = self.request.GET['rep_status']

        context['query'] = query
        context['querytotal'] = querytotal

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class CashDisbursementBook(TemplateView):
    template_name = 'rep_generalledger/cashdisbursementbook.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Cvdetail.objects.filter(cvmain__isdeleted=0, cvmain__status='A', status='A', isdeleted=0).exclude(cvmain=None)
        querytotal = ''

        if self.request.GET:

            if self.request.GET['rep_datefrom']:
                key_data = str(self.request.GET['rep_datefrom'])
                query = query.filter(cvmain__cvdate__gte=key_data)
            if self.request.GET['rep_dateto']:
                key_data = str(self.request.GET['rep_dateto'])
                query = query.filter(cvmain__cvdate__lte=key_data)
            if self.request.GET['rep_status']:
                key_data = str(self.request.GET['rep_status'])
                query = query.filter(cvmain__cvstatus=key_data)

            querytotal = query.aggregate(Sum('debitamount'), Sum('creditamount'))

            if self.request.GET['rep_type'] == 's':
                query = query.values('chartofaccount__accountcode',
                                     'chartofaccount__title',
                                     'chartofaccount__description',
                                     'bankaccount__accountnumber',
                                     'department__departmentname',
                                     'employee__firstname',
                                     'employee__lastname',
                                     'supplier__name',
                                     'customer__name',
                                     'unit__description',
                                     'branch__description',
                                     'product__description',
                                     'inputvat__description',
                                     'outputvat__description',
                                     'vat__description',
                                     'wtax__description',
                                     'ataxcode__code',
                                     'balancecode') \
                            .annotate(Sum('debitamount'), Sum('creditamount')) \
                            .order_by('-balancecode',
                                      '-chartofaccount__accountcode',
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
                query = query.annotate(Sum('debitamount'), Sum('creditamount')).order_by('cv_num',
                                                                                         '-balancecode',
                                                                                         '-chartofaccount__accountcode',
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

            context['rep_datefrom'] = self.request.GET['rep_datefrom']
            context['rep_dateto'] = self.request.GET['rep_dateto']
            context['rep_type'] = self.request.GET['rep_type']
            context['rep_status'] = self.request.GET['rep_status']

        context['query'] = query
        context['querytotal'] = querytotal

        return self.render_to_response(context)
