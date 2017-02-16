from django.views.generic import ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from chartofaccount.models import Chartofaccount
from easy_pdf.views import PDFTemplateView
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import xlwt


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Chartofaccount
    template_name = 'rep_chartofaccount/index.html'
    context_object_name = 'data_list'


@csrf_exempt
def report(request):
    if request.method == 'POST':
        date_from = datetime.combine(datetime.strptime(request.POST['from'], '%Y-%m-%d'), datetime.min.time())
        date_to = datetime.combine(datetime.strptime(request.POST['to'], '%Y-%m-%d'), datetime.max.time())

        list_chartofaccount = Chartofaccount.objects.all().filter(enterdate__range=(date_from, date_to)).filter(isdeleted=0).order_by('-pk')[0:10]
        data = {
            'status': 'success',
            'list_chartofaccount': serializers.serialize('json', list_chartofaccount),
        }
    else:
        data = {
            'status': 'error',
        }
    print data
    return JsonResponse(data)


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Chartofaccount
    template_name = 'rep_chartofaccount/pdf.html'

    def get_context_data(self, **kwargs):
        try:
            context = super(Pdf, self).get_context_data(**kwargs)
            date_from = self.request.GET.get('from')
            date_to = self.request.GET.get('to')

            date_from = date_from + ' 00:00:00'
            date_to = date_to + ' 23:59:59'
            date_limit = '1990-01-01 00:00:00'
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S')
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S')
            date_limit = datetime.datetime.strptime(date_limit, '%Y-%m-%d %H:%M:%S')

            # invalid dates
            if date_from > datetime.datetime.now() or date_from < date_limit or date_to > datetime.datetime.now() or date_to < date_limit:
                context['data_list'] = Chartofaccount.objects.all()[0:0]
            else:
                # context['data_list'] = Chartofaccount.objects.filter(enterdate__date__gt=date_from, enterdate__date__lt=date_to).filter(isdeleted=0)
                context['data_list'] = Chartofaccount.objects.all().filter(enterdate__range=(date_from, date_to)).filter(isdeleted=0).order_by('-pk')

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
        date_from = request.GET.get('from')
        date_to = request.GET.get('to')

        date_from = date_from + ' 00:00:00'
        date_to = date_to + ' 23:59:59'
        date_limit = '1990-01-01 00:00:00'
        date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S')
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S')
        date_limit = datetime.datetime.strptime(date_limit, '%Y-%m-%d %H:%M:%S')

        if date_from > datetime.datetime.now() or date_from < date_limit or date_to > datetime.datetime.now() or date_to < date_limit:
            rows = Chartofaccount.objects.values_list('accountcode', 'title', 'description')[0:0]
        else:
            rows = Chartofaccount.objects.filter(enterdate__range=(date_from, date_to)).filter(isdeleted=0).values_list('accountcode', 'title', 'description')

    except ValueError:
            rows = Chartofaccount.objects.values_list('accountcode', 'title', 'description')[0:0]

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response