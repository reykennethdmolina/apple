from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.apps import apps
from django.db.models import Sum, F, Count


# transaction keys
transactiontype = {
    'or': ['officialreceipt', 'Ormain', 'Ordetail'],
    'jv': ['journalvoucher', 'Jvmain', 'Jvdetail'],
    'cv': ['checkvoucher', 'Cvmain', 'Cvdetail'],
}

# dropdown keys
transactiontype_select = [['or', 'Official Receipt'],
                          ['jv', 'Journal Voucher'],
                          ['cv', 'Check Voucher'], ]
reporttype_select = [['custom', 'Customized'],
                     ['ub', 'Unbalanced Accounting Entry']]
groupby_select = [['t_id', 'Inquiry No.'],
                  ['t_date', 'Date'],
                  ['t_status', 'Inquiry Status'],
                  ['vat', 'VAT'],
                  ['branch', 'Branch']]

# order by keys
orderby = [[['t_id', 'Inquiry No.'],
            ['t_date', 'Date'],
            ['-debit', 'Debit'],
            ['-credit', 'Credit']],
           [['t_id', 'Inquiry No.'],
            ['t_date', 'Date'],
            ['-debit', 'Debit'],
            ['-credit', 'Credit']]]


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'generaljournalbook/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['transactiontype_select'] = transactiontype_select
        context['reporttype_select'] = reporttype_select
        context['groupby_select'] = groupby_select
        context['orderby'] = orderby

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if self.request.GET:

            # transaction type
            initial = self.request.GET['rep_f_transactiontype']
            initialapp = transactiontype[self.request.GET['rep_f_transactiontype']][0]
            initialmain = transactiontype[self.request.GET['rep_f_transactiontype']][1]
            initialdetail = transactiontype[self.request.GET['rep_f_transactiontype']][2]

            # report type
            if self.request.GET['rep_f_reporttype'] == 'custom':
                initialquery = apps.get_model(initialapp, initialdetail).objects.all()

                # universal filters
                if self.request.GET['rep_f_datefrom']:
                    initialquery = initialquery.annotate(t_date=F(initial+'main__'+initial+'date')).filter(t_date__gte=self.request.GET['rep_f_datefrom'])
                if self.request.GET['rep_f_dateto']:
                    initialquery = initialquery.annotate(t_date=F(initial+'main__'+initial+'date')).filter(t_date__lte=self.request.GET['rep_f_dateto'])

                initialquery = initialquery \
                    .annotate(t_date=F(initial + 'main__' + initial + 'date'),
                              t_status=F(initial + 'main__' + initial + 'status'),
                              t_id=F(initialmain.lower() + '_id'),
                              t_num=F(initial + '_num'),
                              debit=Sum('debitamount'),
                              credit=Sum('creditamount')).order_by(initial + '_num') \
                    .values('t_id', 't_num', 't_date', 't_status', 'debit', 'credit') \

                if self.request.GET.getlist('rep_f_order_custom[]'):
                    initialquery = initialquery.order_by(*self.request.GET.getlist('rep_f_order_custom[]'))

                context['data'] = initialquery
                context['rep_f_order'] = ','.join(map(str, self.request.GET.getlist('rep_f_order_custom[]')))

            elif self.request.GET['rep_f_reporttype'] == 'ub':
                initialquery = apps.get_model(initialapp, initialdetail).objects.all()

                # universal filters
                if self.request.GET['rep_f_datefrom']:
                    initialquery = initialquery.annotate(t_date=F(initial+'main__'+initial+'date')).filter(t_date__gte=self.request.GET['rep_f_datefrom'])
                if self.request.GET['rep_f_dateto']:
                    initialquery = initialquery.annotate(t_date=F(initial+'main__'+initial+'date')).filter(t_date__lte=self.request.GET['rep_f_dateto'])

                initialquery = initialquery \
                    .annotate(t_date=F(initial+'main__'+initial+'date'),
                              t_status=F(initial + 'main__' + initial + 'status'),
                              t_id=F(initialmain.lower() + '_id'),
                              t_num=F(initial + '_num'),
                              debit=Sum('debitamount'),
                              credit=Sum('creditamount')).order_by(initial+'_num') \
                    .values('t_id', 't_num', 't_date', 't_status', 'debit', 'credit') \
                    .annotate(margin=F('debit')-F('credit')) \
                    .exclude(debit=F('credit')) \

                if self.request.GET.getlist('rep_f_order_ub[]'):
                    initialquery = initialquery.order_by(*self.request.GET.getlist('rep_f_order_ub[]'))

                context['data'] = initialquery
                context['rep_f_order'] = ','.join(map(str, self.request.GET.getlist('rep_f_order_ub[]')))

            # return GET
            context['rep_f_datefrom'] = self.request.GET['rep_f_datefrom']
            context['rep_f_dateto'] = self.request.GET['rep_f_dateto']
            context['rep_f_reporttype'] = self.request.GET['rep_f_reporttype']
            context['rep_f_transactiontype'] = self.request.GET['rep_f_transactiontype']

            # links
            context['datalink_update'] = initialapp + ':update'
            context['datalink_detail'] = initialapp + ':detail'

        return self.render_to_response(context)
