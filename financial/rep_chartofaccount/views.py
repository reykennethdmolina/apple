from django.views.generic import ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from chartofaccount.models import Chartofaccount
from easy_pdf.views import PDFTemplateView
from django.core import serializers
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import xlwt


default_header = ['accountcode', 'title', 'description']


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Chartofaccount
    template_name = 'rep_chartofaccount/index.html'
    context_object_name = 'data_list'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        # insert aliases
        context['list_header'] = default_header
        return context


@csrf_exempt
def report(request):
    if request.method == 'POST':

        list_table = Chartofaccount.objects
        list_header = default_header

        if request.POST.getlist('list_header[]'):
            list_header = request.POST.getlist('list_header[]')

        if request.POST['from']:
            date_from = datetime.combine(datetime.strptime(request.POST['from'], '%Y-%m-%d'), datetime.min.time())
            list_table = list_table.filter(Q(enterdate__gt=date_from))

        if request.POST['to']:
            date_to = datetime.combine(datetime.strptime(request.POST['to'], '%Y-%m-%d'), datetime.max.time())
            list_table = list_table.filter(Q(enterdate__lt=date_to))

        if request.POST.getlist('orderby[]') and request.POST['orderasc']:
            orderby = request.POST.getlist('orderby[]')
            orderasc = request.POST['orderasc']

            list_table.order_by(*orderby)

            if orderasc == 'a':
                list_table = list_table.reverse()

        list_table = list_table.only(*list_header).filter(isdeleted=0)[0:10]

        data = {
            'status': 'success',
            'list_table': serializers.serialize('json', list_table),
            'list_header': list_header,
        }
    else:
        data = {
            'status': 'error',
        }

    # apply universal name for js response
    # apply to pdf,xls
    return JsonResponse(data)


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Chartofaccount
    template_name = 'rep_chartofaccount/pdf.html'

    def get_context_data(self, **kwargs):
        try:
            context = super(Pdf, self).get_context_data(**kwargs)
            date_from = datetime.combine(datetime.strptime(self.request.GET.get('from'), '%Y-%m-%d'), datetime.min.time())
            date_to = datetime.combine(datetime.strptime(self.request.GET.get('to'), '%Y-%m-%d'), datetime.max.time())
            date_limit = datetime.combine(datetime.strptime('1990-01-01', '%Y-%m-%d'), datetime.min.time())

            # invalid dates
            if date_from > datetime.now() or date_from < date_limit or date_to > datetime.now() or date_to < date_limit:
                context['data_list'] = Chartofaccount.objects.all()[0:0]
            else:
                context['data_list'] = Chartofaccount.objects.all().filter(enterdate__range=(date_from, date_to)).filter(isdeleted=0).order_by('-pk')[0:10]

        except ValueError:
            context['data_list'] = Chartofaccount.objects.all()[0:0]

        return context


def xls(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="chartofaccount.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Chart of Account')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Account Code', 'Title', 'Description', ]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    try:
        date_from = datetime.combine(datetime.strptime(request.GET.get('from'), '%Y-%m-%d'), datetime.min.time())
        date_to = datetime.combine(datetime.strptime(request.GET.get('to'), '%Y-%m-%d'), datetime.max.time())
        date_limit = datetime.combine(datetime.strptime('1990-01-01', '%Y-%m-%d'), datetime.min.time())

        if date_from > datetime.now() or date_from < date_limit or date_to > datetime.now() or date_to < date_limit:
            rows = Chartofaccount.objects.values_list('accountcode', 'title', 'description')[0:0]
        else:
            rows = Chartofaccount.objects.filter(enterdate__range=(date_from, date_to)).filter(isdeleted=0).values_list('accountcode', 'title', 'description')[0:10]

    except ValueError:
            rows = Chartofaccount.objects.values_list('accountcode', 'title', 'description')[0:0]

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response