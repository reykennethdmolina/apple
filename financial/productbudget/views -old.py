import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404, HttpResponse
from productbudget.models import Productbudget
from product.models import Product
from chartofaccount.models import Chartofaccount
# pagination and search
from endless_pagination.views import AjaxListView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
from annoying.functions import get_object_or_None
from utils.mixins import ReportContentMixin
from easy_pdf.views import PDFTemplateView


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Productbudget
    template_name = 'productbudget/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'productbudget/index_list.html'

    def get_queryset(self):
        query = Productbudget.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(year__icontains=keysearch) |
                                 Q(product__code__icontains=keysearch) |
                                 Q(product__description__icontains=keysearch) |
                                 Q(chartofaccount__accountcode__icontains=keysearch) |
                                 Q(chartofaccount__description__icontains=keysearch))
        return query


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Productbudget
    template_name = 'productbudget/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Productbudget
    template_name = 'productbudget/create.html'
    fields = ['year', 'product', 'chartofaccount',
              'remarks', 'formula', 'method',
              'mjan', 'mfeb', 'mmar',
              'mapr', 'mmay', 'mjun',
              'mjul', 'maug', 'msep',
              'moct', 'mnov', 'mdec']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('productbudget.add_productbudget'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['product'] = Product.objects.filter(isdeleted=0).order_by('description')
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/productbudget')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Productbudget
    template_name = 'productbudget/edit.html'
    fields = ['year', 'product', 'chartofaccount',
              'remarks', 'formula', 'method',
              'mjan', 'mfeb', 'mmar',
              'mapr', 'mmay', 'mjun',
              'mjul', 'maug', 'msep',
              'moct', 'mnov', 'mdec']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('productbudget.change_productbudget'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['product'] = Product.objects.filter(isdeleted=0).order_by('description')
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        elif self.object.chartofaccount:
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.object.chartofaccount.id, isdeleted=0)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/productbudget')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Productbudget
    template_name = 'productbudget/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('productbudget.delete_productbudget'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/productbudget')


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Productbudget
    template_name = 'productbudget/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['product'] = Product.objects.filter(isdeleted=0).order_by('code')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultHtmlView(ListView):
    model = Productbudget
    template_name = 'productbudget/reportresulthtml.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['report_xls'], context['year'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_group_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "PRODUCT BUDGET"
        context['rc_title'] = "PRODUCT BUDGET"

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Productbudget
    template_name = 'productbudget/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        query, context['report_type'], context['report_total'], context['report_xls'], context['year'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_group_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        # pdf config
        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        context['rc_headtitle'] = "PRODUCT BUDGET"
        context['rc_title'] = "PRODUCT BUDGET"

        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''
    report_xls = ''
    report_total = ''
    report_year = ''

    # print request.COOKIES.get('rep_f_year_')
    # print 'hello'

    query = Productbudget.objects.all().filter(isdeleted=0)
    # t1 = request.COOKIES.get('rep_f_year_')
    # print t1
    # print "new"
    # test = request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name)
    # print test

    # if request.COOKIES.get('rep_f_year_' + request.resolver_match.app_name):
    #     key_data = str(request.COOKIES.get('rep_f_year_' + request.resolver_match.app_name))
    #     report_year = key_data
    #     print report_year
    #     print "hello year"
    #     #query = query.filter(year=key_data)
    #     # query = query.filter(year=int(key_data))
    #     # query = query.filter(year=str(key_data))
    if request.COOKIES.get('rep_f_year_' + request.resolver_match.app_name):
        key_data = str(request.COOKIES.get('rep_f_year_' + request.resolver_match.app_name))
        report_year = key_data
        #print report_year
        #print "hello year"
        # query = query.filter(year=int(key_data))
        query = query.filter(year=key_data)
        # print 'execute'
        # query = query.filter(year=int(key_data))
        # query = query.filter(year=str(key_data))
    if request.COOKIES.get('rep_f_product_' + request.resolver_match.app_name):
        key_data = str(request.COOKIES.get('rep_f_product_' + request.resolver_match.app_name))
        query = query.filter(product=int(key_data))
    if request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name) is not None \
            and request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name) != 'null':
        key_data = str(request.COOKIES.get('rep_f_gl_' + request.resolver_match.app_name))
        query = query.filter(chartofaccount=get_object_or_None(Chartofaccount, pk=int(key_data)))

    if request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ps':

        report_type = "Product Budget " + str(report_year) + " (Product Summary)"
        report_xls = "Product Budget " + str(report_year) + " (Product SM)"

        query = query.values('product', 'product__description', 'product__code')\
                     .annotate(
                               Sum('mjan'),
                               Sum('mfeb'),
                               Sum('mmar'),
                               Sum('mapr'),
                               Sum('mmay'),
                               Sum('mjun'),
                               Sum('mjul'),
                               Sum('maug'),
                               Sum('msep'),
                               Sum('moct'),
                               Sum('mnov'),
                               Sum('mdec'),
                               total=Sum('mjan')+Sum('mfeb')+Sum('mmar')+Sum('mapr')+Sum('mmay')+Sum('mjun')+Sum('mjul')+Sum('maug')+Sum('msep')+Sum('moct')+Sum('mnov')+Sum('mdec'),
                               )\
                     .order_by('product__code')\

        report_total = query.aggregate(
                                        Sum('mjan__sum'),
                                        Sum('mfeb__sum'),
                                        Sum('mmar__sum'),
                                        Sum('mapr__sum'),
                                        Sum('mmay__sum'),
                                        Sum('mjun__sum'),
                                        Sum('mjul__sum'),
                                        Sum('maug__sum'),
                                        Sum('msep__sum'),
                                        Sum('moct__sum'),
                                        Sum('mnov__sum'),
                                        Sum('mdec__sum'),
                                        Sum('total'),
                                      )
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'as':

        report_type = "Product Budget " + str(report_year) + " (Account Summary)"
        report_xls = "Product Budget " + str(report_year) + " (Acct. SM)"

        query = query.values('chartofaccount', 'chartofaccount__accountcode', 'chartofaccount__description')\
                     .annotate(
                               Sum('mjan'),
                               Sum('mfeb'),
                               Sum('mmar'),
                               Sum('mapr'),
                               Sum('mmay'),
                               Sum('mjun'),
                               Sum('mjul'),
                               Sum('maug'),
                               Sum('msep'),
                               Sum('moct'),
                               Sum('mnov'),
                               Sum('mdec'),
                               total=Sum('mjan')+Sum('mfeb')+Sum('mmar')+Sum('mapr')+Sum('mmay')+Sum('mjun')+Sum('mjul')+Sum('maug')+Sum('msep')+Sum('moct')+Sum('mnov')+Sum('mdec'),
                               )\
                     .order_by('chartofaccount__accountcode')\

        report_total = query.aggregate(
                                        Sum('mjan__sum'),
                                        Sum('mfeb__sum'),
                                        Sum('mmar__sum'),
                                        Sum('mapr__sum'),
                                        Sum('mmay__sum'),
                                        Sum('mjun__sum'),
                                        Sum('mjul__sum'),
                                        Sum('maug__sum'),
                                        Sum('msep__sum'),
                                        Sum('moct__sum'),
                                        Sum('mnov__sum'),
                                        Sum('mdec__sum'),
                                        Sum('total'),
                                      )
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'pd':

        print 'pasok'

        report_type = "Product Budget " + str(report_year) + " (Product Detailed)"
        report_xls = "Product Budget " + str(report_year) + " (Product DT)"

        query = query.values('product', 'product__description', 'product__code', 'chartofaccount', 'chartofaccount__accountcode', 'chartofaccount__description')\
                     .annotate(
                               Sum('mjan'),
                               Sum('mfeb'),
                               Sum('mmar'),
                               Sum('mapr'),
                               Sum('mmay'),
                               Sum('mjun'),
                               Sum('mjul'),
                               Sum('maug'),
                               Sum('msep'),
                               Sum('moct'),
                               Sum('mnov'),
                               Sum('mdec'),
                               total=Sum('mjan')+Sum('mfeb')+Sum('mmar')+Sum('mapr')+Sum('mmay')+Sum('mjun')+Sum('mjul')+Sum('maug')+Sum('msep')+Sum('moct')+Sum('mnov')+Sum('mdec'),
                               )\
                     .order_by('product__code', 'chartofaccount__accountcode')\

        report_total = query.aggregate(
                                        Sum('mjan__sum'),
                                        Sum('mfeb__sum'),
                                        Sum('mmar__sum'),
                                        Sum('mapr__sum'),
                                        Sum('mmay__sum'),
                                        Sum('mjun__sum'),
                                        Sum('mjul__sum'),
                                        Sum('maug__sum'),
                                        Sum('msep__sum'),
                                        Sum('moct__sum'),
                                        Sum('mnov__sum'),
                                        Sum('mdec__sum'),
                                        Sum('total'),
                                      )
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ad':

        report_type = "Product Budget " + str(report_year) + " (Account Detailed)"
        report_xls = "Product Budget " + str(report_year) + " (Acct. DT)"

        query = query.values('chartofaccount', 'chartofaccount__accountcode', 'chartofaccount__description', 'product', 'product__description', 'product__code')\
                     .annotate(
                               Sum('mjan'),
                               Sum('mfeb'),
                               Sum('mmar'),
                               Sum('mapr'),
                               Sum('mmay'),
                               Sum('mjun'),
                               Sum('mjul'),
                               Sum('maug'),
                               Sum('msep'),
                               Sum('moct'),
                               Sum('mnov'),
                               Sum('mdec'),
                               total=Sum('mjan')+Sum('mfeb')+Sum('mmar')+Sum('mapr')+Sum('mmay')+Sum('mjun')+Sum('mjul')+Sum('maug')+Sum('msep')+Sum('moct')+Sum('mnov')+Sum('mdec'),
                               )\
                     .order_by('chartofaccount__accountcode', 'product__code')\

        report_total = query.aggregate(
                                        Sum('mjan__sum'),
                                        Sum('mfeb__sum'),
                                        Sum('mmar__sum'),
                                        Sum('mapr__sum'),
                                        Sum('mmay__sum'),
                                        Sum('mjun__sum'),
                                        Sum('mjul__sum'),
                                        Sum('maug__sum'),
                                        Sum('msep__sum'),
                                        Sum('moct__sum'),
                                        Sum('mnov__sum'),
                                        Sum('mdec__sum'),
                                        Sum('total'),
                                      )

    return query, report_type, report_total, report_xls, report_year


@csrf_exempt
def reportresultxlsx(request):
    # imports and workbook config
    import xlsxwriter
    try:
        import cStringIO as StringIO
    except ImportError:
        import StringIO
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)

    # query and default variables
    queryset, report_type, report_total, report_xls, report_year = reportresultquery(request)
    worksheet = workbook.add_worksheet(report_xls)
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
    if request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ps':
        amount_placement = 1
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'as':
        amount_placement = 1
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'pd':
        amount_placement = 2
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ad':
        amount_placement = 2

    # config: header
    if request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ps':
        worksheet.write('A1', 'Product', bold)
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'as':
        worksheet.write('A1', 'Account', bold)
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'pd':
        worksheet.write('A1', 'Product', bold)
        worksheet.write('B1', 'Account', bold)
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ad':
        worksheet.write('A1', 'Account', bold)
        worksheet.write('B1', 'Product', bold)

    if request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ps' or request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'as':
        worksheet.write('B1', 'Jan', bold_right)
        worksheet.write('C1', 'Feb', bold_right)
        worksheet.write('D1', 'Mar', bold_right)
        worksheet.write('E1', 'Apr', bold_right)
        worksheet.write('F1', 'May', bold_right)
        worksheet.write('G1', 'Jun', bold_right)
        worksheet.write('H1', 'Jul', bold_right)
        worksheet.write('I1', 'Aug', bold_right)
        worksheet.write('J1', 'Sep', bold_right)
        worksheet.write('K1', 'Oct', bold_right)
        worksheet.write('L1', 'Nov', bold_right)
        worksheet.write('M1', 'Dec', bold_right)
        worksheet.write('N1', 'Total', bold_right)
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'pd' or request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ad':
        worksheet.write('C1', 'Jan', bold_right)
        worksheet.write('D1', 'Feb', bold_right)
        worksheet.write('E1', 'Mar', bold_right)
        worksheet.write('F1', 'Apr', bold_right)
        worksheet.write('G1', 'May', bold_right)
        worksheet.write('H1', 'Jun', bold_right)
        worksheet.write('I1', 'Jul', bold_right)
        worksheet.write('J1', 'Aug', bold_right)
        worksheet.write('K1', 'Sep', bold_right)
        worksheet.write('L1', 'Oct', bold_right)
        worksheet.write('M1', 'Nov', bold_right)
        worksheet.write('N1', 'Dec', bold_right)
        worksheet.write('O1', 'Total', bold_right)

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ps':
            data = [
                obj['product__code'] + ' - ' + obj['product__description'],
                obj['mjan__sum'],
                obj['mfeb__sum'],
                obj['mmar__sum'],
                obj['mapr__sum'],
                obj['mmay__sum'],
                obj['mjun__sum'],
                obj['mjul__sum'],
                obj['maug__sum'],
                obj['msep__sum'],
                obj['moct__sum'],
                obj['mnov__sum'],
                obj['mdec__sum'],
                obj['total'],
            ]
        elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'as':
            data = [
                obj['chartofaccount__accountcode'] + ' - ' + obj['chartofaccount__description'],
                obj['mjan__sum'],
                obj['mfeb__sum'],
                obj['mmar__sum'],
                obj['mapr__sum'],
                obj['mmay__sum'],
                obj['mjun__sum'],
                obj['mjul__sum'],
                obj['maug__sum'],
                obj['msep__sum'],
                obj['moct__sum'],
                obj['mnov__sum'],
                obj['mdec__sum'],
                obj['total'],
            ]
        elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'pd':
            data = [
                obj['product__code'] + ' - ' + obj['product__description'],
                obj['chartofaccount__accountcode'] + ' - ' + obj['chartofaccount__description'],
                obj['mjan__sum'],
                obj['mfeb__sum'],
                obj['mmar__sum'],
                obj['mapr__sum'],
                obj['mmay__sum'],
                obj['mjun__sum'],
                obj['mjul__sum'],
                obj['maug__sum'],
                obj['msep__sum'],
                obj['moct__sum'],
                obj['mnov__sum'],
                obj['mdec__sum'],
                obj['total'],
            ]
        elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ad':
            data = [
                obj['chartofaccount__accountcode'] + ' - ' + obj['chartofaccount__description'],
                obj['product__code'] + ' - ' + obj['product__description'],
                obj['mjan__sum'],
                obj['mfeb__sum'],
                obj['mmar__sum'],
                obj['mapr__sum'],
                obj['mmay__sum'],
                obj['mjun__sum'],
                obj['mjul__sum'],
                obj['maug__sum'],
                obj['msep__sum'],
                obj['moct__sum'],
                obj['mnov__sum'],
                obj['mdec__sum'],
                obj['total'],
            ]

        temp_amount_placement = amount_placement
        for col_num in xrange(len(data)):
            if col_num == temp_amount_placement:
                temp_amount_placement += 1
                worksheet.write_number(row, col_num, data[col_num], money_format)
            else:
                worksheet.write(row, col_num, data[col_num])

    # config: totals
    if request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ps' or request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'as':
        data = [
            "Total",
            report_total['mjan__sum__sum'],
            report_total['mfeb__sum__sum'],
            report_total['mmar__sum__sum'],
            report_total['mapr__sum__sum'],
            report_total['mmay__sum__sum'],
            report_total['mjun__sum__sum'],
            report_total['mjul__sum__sum'],
            report_total['maug__sum__sum'],
            report_total['msep__sum__sum'],
            report_total['moct__sum__sum'],
            report_total['mnov__sum__sum'],
            report_total['mdec__sum__sum'],
            report_total['total__sum'],
        ]
    elif request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'pd' or request.COOKIES.get('rep_f_group_' + request.resolver_match.app_name) == 'ad':
        data = [
            "",
            "Total",
            report_total['mjan__sum__sum'],
            report_total['mfeb__sum__sum'],
            report_total['mmar__sum__sum'],
            report_total['mapr__sum__sum'],
            report_total['mmay__sum__sum'],
            report_total['mjun__sum__sum'],
            report_total['mjul__sum__sum'],
            report_total['maug__sum__sum'],
            report_total['msep__sum__sum'],
            report_total['moct__sum__sum'],
            report_total['mnov__sum__sum'],
            report_total['mdec__sum__sum'],
            report_total['total__sum'],
        ]

    row += 1
    for col_num in xrange(len(data)):
        worksheet.write(row, col_num, data[col_num], bold_money_format)

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+report_xls+".xlsx"
    return response
