from django.views.generic import View, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from supplier.models import Supplier
from companyparameter.models import Companyparameter
from easy_pdf.views import PDFTemplateView
from django.db.models import Q
from django.http import HttpResponse
from datetime import datetime
from json_views.views import JSONDataView
import xlwt
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Supplier
    template_name = 'rep_supplier/index.html'
    context_object_name = 'data_list'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        return context

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        report = request.GET['report']
        dfrom = request.GET['from']
        dto = request.GET['to']
        title = "Supplier Master List"
        list = Supplier.objects.filter(isdeleted=0).order_by('code')[:0]

        if report == '1':
            title = "Supplier Master List"
            q = Supplier.objects.filter(isdeleted=0).order_by('code')
        elif report == '2':
            title = "Supplier Master List (Include Beginning Balance)"
            q = Supplier.objects.filter(isdeleted=0).order_by('code')
        elif report == '3':
            title = "Supplier Master List (Exclude Beginning Balance)"
            q = Supplier.objects.filter(isdeleted=0).order_by('code')
        elif report == '4':
            title = "Supplier Master List (BIR)"
            q = Supplier.objects.filter(isdeleted=0).order_by('code')

        if dfrom != '':
            q = q.filter(enterdate__gte=dfrom)
        if dto != '':
            q = q.filter(enterdate__lte=dto)

        list = q
        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        if report == '1':
            return Render.render('rep_supplier/report_1.html', context)
        elif report == '2':
            return Render.render('rep_supplier/report_2.html', context)
        elif report == '3':
            return Render.render('rep_supplier/report_3.html', context)
        elif report == '4':
            return Render.render('rep_supplier/report_4.html', context)
        else:
            return Render.render('rep_supplier/report_1.html', context)

