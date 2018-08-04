from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from companyparameter.models import Companyparameter
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from . models import Cmmain, Cmitem
from easy_pdf.views import PDFTemplateView
from dateutil.relativedelta import relativedelta
import datetime
from product.models import Product
import decimal

from utils.mixins import ReportContentMixin
from django.utils.dateformat import DateFormat


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Cmmain
    template_name = 'cmsadjustment/index.html'
    page_template = 'cmsadjustment/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Cmmain.objects.all().filter(isdeleted=0)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(cmnum__icontains=keysearch) |
                                 Q(cmdate__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Cmmain
    template_name = 'cmsadjustment/create.html'
    fields = ['cmdate', 'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('cmsadjustment.add_cmmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['product'] = Product.objects.filter(isdeleted=0, status='A').order_by('code')

        closetransaction = Companyparameter.objects.all().first().last_closed_date
        validtransaction = closetransaction + relativedelta(months=1)
        context['validtransaction'] = validtransaction

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        year = str(form.cleaned_data['cmdate'].year)
        yearqs = Cmmain.objects.filter(cmnum__startswith=year)

        if yearqs:
            cmnumlast = yearqs.latest('cmnum')
            latestcmnum = str(cmnumlast)
            print "latest: " + latestcmnum

            cmnum = year
            last = str(int(latestcmnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                cmnum += '0'
            cmnum += last
        else:
            cmnum = year + '000001'

        print 'cmnum: ' + cmnum
        self.object.cmnum = cmnum
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        totaldebitamount = 0
        totalcreditamount = 0
        i = 0

        for data in self.request.POST.getlist('product[]'):
            cmitem = Cmitem()
            cmitem.cmmain = self.object
            cmitem.item_counter = i + 1
            cmitem.cmnum = self.object.cmnum
            cmitem.cmdate = self.object.cmdate
            cmitem.product = Product.objects.get(pk=int(data))
            cmitem.product_code = cmitem.product.code
            cmitem.product_name = cmitem.product.description
            cmitem.debitamount = float(self.request.POST.getlist('debitamount[]')[i].replace(',', ''))
            cmitem.creditamount = float(self.request.POST.getlist('creditamount[]')[i].replace(',', ''))
            cmitem.enterby = self.request.user
            cmitem.modifyby = self.request.user
            cmitem.save()
            totaldebitamount += cmitem.debitamount
            totalcreditamount += cmitem.creditamount
            i += 1

        if totaldebitamount == totalcreditamount:
            self.object.amount = totaldebitamount
        else:
            print "--------------Debit and Credit amounts are not balanced!--------------------"
        self.object.save()

        return HttpResponseRedirect('/cmsadjustment/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Cmmain
    template_name = 'cmsadjustment/update.html'
    fields = ['cmdate', 'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('cmsadjustment.change_cmmain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['product'] = Product.objects.filter(isdeleted=0, status='A').order_by('code')
        context['items'] = Cmitem.objects.filter(isdeleted=0, status='A', cmmain=self.object.pk).\
            order_by('item_counter')
        context['currentcounter'] = Cmitem.objects.filter(isdeleted=0, status='A', cmmain=self.object.pk). \
            order_by('item_counter').last().item_counter + 1
        context['cmnum'] = self.object.cmnum
        context['totalamount'] = self.object.amount

        return context

    def form_valid(self, form):
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['cmdate', 'particulars', 'modifyby', 'modifydate'])

        Cmitem.objects.filter(isdeleted=0, status='A', cmmain=self.object.pk).delete()

        totaldebitamount = 0
        totalcreditamount = 0
        i = 0

        for data in self.request.POST.getlist('product[]'):
            cmitem = Cmitem()
            cmitem.cmmain = self.object
            cmitem.item_counter = i + 1
            cmitem.cmnum = self.object.cmnum
            cmitem.cmdate = self.object.cmdate
            cmitem.product = Product.objects.get(pk=int(data))
            cmitem.product_code = cmitem.product.code
            cmitem.product_name = cmitem.product.description
            cmitem.debitamount = float(self.request.POST.getlist('debitamount[]')[i].replace(',', ''))
            cmitem.creditamount = float(self.request.POST.getlist('creditamount[]')[i].replace(',', ''))
            cmitem.enterby = self.request.user
            cmitem.modifyby = self.request.user
            cmitem.save()
            totaldebitamount += cmitem.debitamount
            totalcreditamount += cmitem.creditamount
            i += 1

        if totaldebitamount == totalcreditamount:
            self.object.amount = totaldebitamount
        else:
            print "--------------Debit and Credit amounts are not balanced!--------------------"
        self.object.save(update_fields=['amount'])

        return HttpResponseRedirect('/cmsadjustment/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Cmmain
    template_name = 'cmsadjustment/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)

        # items
        context['items'] = Cmitem.objects.filter(isdeleted=0, status='A', cmmain=self.object.pk).\
            order_by('item_counter')

        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Cmmain
    template_name = 'cmsadjustment/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('cmsadjustment.delete_cmmain') or self.object.status == 'O' \
                or self.object.cmstatus == 'A' or self.object.cmstatus == 'I' or self.object.cmstatus == 'R':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.cmstatus = 'D'
        self.object.save()

        return HttpResponseRedirect('/cmsadjustment')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Cmmain
    template_name = 'cmsadjustment/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['cmmain'] = Cmmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['items'] = Cmitem.objects.filter(cmmain=self.kwargs['pk'], isdeleted=0).order_by('item_counter')

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedcm = Cmmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedcm.print_ctr += 1
        printedcm.save()
        return context


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Cmmain
    template_name = 'cmsadjustment/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        # context['dcsubtype'] = Debitcreditmemosubtype.objects.filter(isdeleted=0).order_by('description')
        # context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        # context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        # context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Cmmain
    template_name = 'cmsadjustment/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "CONTRIBUTION MARGIN BOOK"
        context['rc_title'] = "CONTRIBUTION MARGIN BOOK"

        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_total = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        report_type = "CM Summary"
        query = Cmmain.objects.all().filter(isdeleted=0)
        
        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(cmnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(cmnum__lte=int(key_data))
        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(cmdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(cmdate__lte=key_data)
        if request.COOKIES.get('rep_f_cmstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_cmstatus_' + request.resolver_match.app_name))
            query = query.filter(cmstatus=str(key_data))

        if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(amount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
            query = query.filter(amount__lte=float(key_data.replace(',', '')))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)

        report_total = query.aggregate(Sum('amount'))

        if request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name))
            if key_data == 'd':
                query = query.reverse()

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        report_type = "CM Detailed"
        query = Cmitem.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(cmmain__cmnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(cmmain__cmnum__lte=int(key_data))
        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(cmmain__cmdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(cmmain__cmdate__lte=key_data)
        if request.COOKIES.get('rep_f_cmstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_cmstatus_' + request.resolver_match.app_name))
            query = query.filter(cmmain__cmstatus=str(key_data))

        if request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(cmmain__amount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_amountto_' + request.resolver_match.app_name))
            query = query.filter(cmmain__amount__lte=float(key_data.replace(',', '')))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                for n,data in enumerate(key_data):
                    key_data[n] = "cmmain__" + data
                query = query.order_by(*key_data)
            else:
                query = query.order_by('cmmain')

        report_total = query.values('cmmain').annotate(Sum('amount')).aggregate(Sum('cmmain__amount'))

        if request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name))
            if key_data == 'd':
                query = query.reverse()

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s'\
            or request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        print 123
        # query = Dcdetail.objects.all().filter(isdeleted=0)

        # if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        #     if request.COOKIES.get('rep_f_debit_amountfrom_' + request.resolver_match.app_name):
        #         key_data = str(request.COOKIES.get('rep_f_debit_amountfrom_' + request.resolver_match.app_name))
        #         query = query.filter(debitamount__gte=float(key_data.replace(',', '')))
        #     if request.COOKIES.get('rep_f_debit_amountto_' + request.resolver_match.app_name):
        #         key_data = str(request.COOKIES.get('rep_f_debit_amountto_' + request.resolver_match.app_name))
        #         query = query.filter(debitamount__lte=float(key_data.replace(',', '')))
        #     if request.COOKIES.get('rep_f_credit_amountfrom_' + request.resolver_match.app_name):
        #         key_data = str(request.COOKIES.get('rep_f_credit_amountfrom_' + request.resolver_match.app_name))
        #         query = query.filter(creditamount__gte=float(key_data.replace(',', '')))
        #     if request.COOKIES.get('rep_f_credit_amountto_' + request.resolver_match.app_name):
        #         key_data = str(request.COOKIES.get('rep_f_credit_amountto_' + request.resolver_match.app_name))
        #         query = query.filter(creditamount__lte=float(key_data.replace(',', '')))
        # if request.COOKIES.get('rep_f_balancecode_' + request.resolver_match.app_name) == 'd':
        #     query = query.filter(balancecode='D')
        # elif request.COOKIES.get('rep_f_balancecode_' + request.resolver_match.app_name) == 'c':
        #     query = query.filter(balancecode='C')

        # if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
        #     query = query.filter(dcmain__dcnum__gte=int(key_data))
        # if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
        #     query = query.filter(dcmain__dcnum__lte=int(key_data))
        # if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
        #     query = query.filter(dcmain__dcdate__gte=key_data)
        # if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
        #     query = query.filter(dcmain__dcdate__lte=key_data)
        # if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
        #     query = query.filter(dcmain__branch=int(key_data))
        # if request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_vat_' + request.resolver_match.app_name))
        #     query = query.filter(dcmain__vat=int(key_data))
        # if request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_outputvattype_' + request.resolver_match.app_name))
        #     query = query.filter(dcmain__outputvattype=int(key_data))
        # if request.COOKIES.get('rep_f_dctype_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_dctype_' + request.resolver_match.app_name))
        #     query = query.filter(dcmain__dctype=str(key_data))
        # if request.COOKIES.get('rep_f_dcstatus_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_dcstatus_' + request.resolver_match.app_name))
        #     query = query.filter(dcmain__dcstatus=str(key_data))
        # if request.COOKIES.get('rep_f_dcsubtype_' + request.resolver_match.app_name):
        #     key_data = str(request.COOKIES.get('rep_f_dcsubtype_' + request.resolver_match.app_name))
        #     query = query.filter(dcmain__dcsubtype=int(key_data))

        # report_total = query.aggregate(Sum('debitamount'), Sum('creditamount'))

        # if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        #     report_type = "DC Acctg Entry - Summary"

        #     query = query.values('chartofaccount__accountcode',
        #                          'chartofaccount__title',
        #                          'chartofaccount__description',
        #                          'bankaccount__accountnumber',
        #                          'department__departmentname',
        #                          'employee__firstname',
        #                          'employee__lastname',
        #                          'supplier__name',
        #                          'customer__name',
        #                          'unit__description',
        #                          'branch__description',
        #                          'product__description',
        #                          'inputvat__description',
        #                          'outputvat__description',
        #                          'vat__description',
        #                          'wtax__description',
        #                          'ataxcode__code',
        #                          'balancecode')\
        #                  .annotate(Sum('debitamount'), Sum('creditamount'))\
        #                  .order_by('-balancecode',
        #                            '-chartofaccount__accountcode',
        #                            'bankaccount__accountnumber',
        #                            'department__departmentname',
        #                            'employee__firstname',
        #                            'supplier__name',
        #                            'customer__name',
        #                            'unit__description',
        #                            'branch__description',
        #                            'product__description',
        #                            'inputvat__description',
        #                            'outputvat__description',
        #                            '-vat__description',
        #                            'wtax__description',
        #                            'ataxcode__code')
        # else:
        #     report_type = "DC Acctg Entry - Detailed"

        #     query = query.annotate(Sum('debitamount'), Sum('creditamount')).order_by('-balancecode',
        #                                                                              '-chartofaccount__accountcode',
        #                                                                              'bankaccount__accountnumber',
        #                                                                              'department__departmentname',
        #                                                                              'employee__firstname',
        #                                                                              'supplier__name',
        #                                                                              'customer__name',
        #                                                                              'unit__description',
        #                                                                              'branch__description',
        #                                                                              'product__description',
        #                                                                              'inputvat__description',
        #                                                                              'outputvat__description',
        #                                                                              '-vat__description',
        #                                                                              'wtax__description',
        #                                                                              'ataxcode__code',
        #                                                                              'dc_num')

    return query, report_type, report_total


@csrf_exempt
def reportresultxlsx(request):
    import xlsxwriter
    try:
        import cStringIO as StringIO
    except ImportError:
        import StringIO
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)

    # query and default variables
    queryset, report_type, report_total = reportresultquery(request)
    report_type = report_type if report_type != '' else 'DC Report'
    worksheet = workbook.add_worksheet(report_type)
    bold = workbook.add_format({'bold': 1})
    bold_right = workbook.add_format({'bold': 1, 'align': 'right'})
    bold_center = workbook.add_format({'bold': 1, 'align': 'center'})
    money_format = workbook.add_format({'num_format': '#,##0.00'})
    bold_money_format = workbook.add_format({'num_format': '#,##0.00', 'bold': 1})
    worksheet.set_column(1, 1, 15)
    row = 0
    data = []

    # config: placement
    amount_placement = 0
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        amount_placement = 3
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        amount_placement = 5
    # elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
    #     amount_placement = 14
    # elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
    #     amount_placement = 15

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'CM Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Status', bold)
        worksheet.write('D1', 'Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.merge_range('A1:A2', 'CM Number', bold)
        worksheet.merge_range('B1:B2', 'Date', bold)
        worksheet.merge_range('C1:C2', 'Status', bold)
        worksheet.merge_range('D1:E1', 'Item', bold)
        worksheet.write('D2', 'Product', bold)
        worksheet.write('E2', 'Amount', bold)
        worksheet.merge_range('F1:F2', 'Amount', bold_right)
    # elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
    #     worksheet.merge_range('A1:A2', 'Chart of Account', bold)
    #     worksheet.merge_range('B1:N1', 'Details', bold_center)
    #     worksheet.merge_range('O1:O2', 'Debit', bold_right)
    #     worksheet.merge_range('P1:P2', 'Credit', bold_right)
    #     worksheet.write('B2', 'Bank Account', bold)
    #     worksheet.write('C2', 'Department', bold)
    #     worksheet.write('D2', 'Employee', bold)
    #     worksheet.write('E2', 'Supplier', bold)
    #     worksheet.write('F2', 'Customer', bold)
    #     worksheet.write('G2', 'Unit', bold)
    #     worksheet.write('H2', 'Branch', bold)
    #     worksheet.write('I2', 'Product', bold)
    #     worksheet.write('J2', 'Input VAT', bold)
    #     worksheet.write('K2', 'Output VAT', bold)
    #     worksheet.write('L2', 'VAT', bold)
    #     worksheet.write('M2', 'WTAX', bold)
    #     worksheet.write('N2', 'ATAX Code', bold)
    #     row += 1
    # elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
    #     worksheet.merge_range('A1:A2', 'Chart of Account', bold)
    #     worksheet.merge_range('B1:N1', 'Details', bold_center)
    #     worksheet.merge_range('O1:O2', 'Date', bold)
    #     worksheet.merge_range('P1:P2', 'Debit', bold_right)
    #     worksheet.merge_range('Q1:Q2', 'Credit', bold_right)
    #     worksheet.write('B2', 'Bank Account', bold)
    #     worksheet.write('C2', 'Department', bold)
    #     worksheet.write('D2', 'Employee', bold)
    #     worksheet.write('E2', 'Supplier', bold)
    #     worksheet.write('F2', 'Customer', bold)
    #     worksheet.write('G2', 'Unit', bold)
    #     worksheet.write('H2', 'Branch', bold)
    #     worksheet.write('I2', 'Product', bold)
    #     worksheet.write('J2', 'Input VAT', bold)
    #     worksheet.write('K2', 'Output VAT', bold)
    #     worksheet.write('L2', 'VAT', bold)
    #     worksheet.write('M2', 'WTAX', bold)
    #     worksheet.write('N2', 'ATAX Code', bold)
    #     row += 1

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            data = [
                obj.cmnum,
                DateFormat(obj.cmdate).format('Y-m-d'),
                obj.get_cmstatus_display(),
                obj.amount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            data = [
                obj.cmnum,
                DateFormat(obj.cmdate).format('Y-m-d'),
                obj.cmmain.get_cmstatus_display(),
                obj.product_code + " - " + obj.product_name,
                obj.amount,
                obj.cmmain.amount,
            ]
        # elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
        #     str_firstname = obj['employee__firstname'] if obj['employee__firstname'] is not None else ''
        #     str_lastname = obj['employee__lastname'] if obj['employee__lastname'] is not None else ''

        #     data = [
        #         obj['chartofaccount__accountcode'] + " - " + obj['chartofaccount__description'],
        #         obj['bankaccount__accountnumber'],
        #         obj['department__departmentname'],
        #         str_firstname + " " + str_lastname,
        #         obj['supplier__name'],
        #         obj['customer__name'],
        #         obj['unit__description'],
        #         obj['branch__description'],
        #         obj['product__description'],
        #         obj['inputvat__description'],
        #         obj['outputvat__description'],
        #         obj['vat__description'],
        #         obj['wtax__description'],
        #         obj['ataxcode__code'],
        #         obj['debitamount__sum'],
        #         obj['creditamount__sum'],
        #     ]
        # elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
        #     str_firstname = obj.employee.firstname if obj.employee is not None else ''
        #     str_lastname = obj.employee.lastname if obj.employee is not None else ''

        #     data = [
        #         obj.chartofaccount.accountcode + " - " + obj.chartofaccount.description,
        #         obj.bankaccount.accountnumber if obj.bankaccount is not None else '',
        #         obj.department.departmentname if obj.department is not None else '',
        #         str_firstname + " " + str_lastname,
        #         obj.supplier.name if obj.supplier is not None else '',
        #         obj.customer.name if obj.customer is not None else '',
        #         obj.unit.description if obj.unit is not None else '',
        #         obj.branch.description if obj.branch is not None else '',
        #         obj.product.description if obj.product is not None else '',
        #         obj.inputvat.description if obj.inputvat is not None else '',
        #         obj.outputvat.description if obj.outputvat is not None else '',
        #         obj.vat.description if obj.vat is not None else '',
        #         obj.wtax.description if obj.wtax is not None else '',
        #         obj.ataxcode.code if obj.ataxcode is not None else '',
        #         DateFormat(obj.dc_date).format('Y-m-d'),
        #         obj.debitamount__sum,
        #         obj.creditamount__sum,
        #     ]

        temp_amount_placement = amount_placement
        for col_num in xrange(len(data)):
            if col_num == temp_amount_placement:
                temp_amount_placement += 1
                worksheet.write_number(row, col_num, data[col_num], money_format)
            else:
                worksheet.write(row, col_num, data[col_num])

    # config: totals
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        data = [
            "", "",
            "Total", report_total['amount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        data = [
            "", "", "", "",
            "Total", report_total['cmmain__amount__sum'],
        ]
    # elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_s':
    #     data = [
    #         "", "", "", "", "", "", "", "", "", "", "", "", "",
    #         "Total", report_total['debitamount__sum'], report_total['creditamount__sum'],
    #     ]
    # elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'a_d':
    #     data = [
    #         "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    #         "Total", report_total['debitamount__sum'], report_total['creditamount__sum'],
    #     ]

    row += 1
    for col_num in xrange(len(data)):
        worksheet.write(row, col_num, data[col_num], bold_money_format)

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+report_type+".xlsx"
    return response
