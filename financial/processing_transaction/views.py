from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from annoying.functions import get_object_or_None
from datetime import datetime
from datetime import timedelta
from django.utils.crypto import get_random_string
from utils.views import wccount, storeupload
import decimal
from dbfread import DBF

from purchaseorder.models import Pomain
from accountspayable.models import Apmain


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'processing_transaction/index.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if self.request.GET:
            if self.request.GET['selectprocess'] == 'potoapv':
                context['data_list'] = Pomain.objects.all().filter(isdeleted=0, postatus='A', isfullyapv=0).\
                    order_by('supplier_name', 'inputvattype_id', 'vat_id')
                if self.request.GET['datefrom']:
                    context['data_list'] = context['data_list'].filter(podate__gte=self.request.GET['datefrom'])
                if self.request.GET['dateto']:
                    context['data_list'] = context['data_list'].filter(podate__lte=self.request.GET['dateto'])
            elif self.request.GET['selectprocess'] == 'apvtocv':
                context['data_list'] = Apmain.objects.all().filter(isdeleted=0, apstatus='R', isfullycv=0). \
                    order_by('payeecode', 'inputvattype_id', 'vat_id')
                if self.request.GET['datefrom']:
                    context['data_list'] = context['data_list'].filter(apdate__gte=self.request.GET['datefrom'])
                if self.request.GET['dateto']:
                    context['data_list'] = context['data_list'].filter(apdate__lte=self.request.GET['dateto'])

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        if self.request.GET:
            context['selectprocess'] = self.request.GET['selectprocess']
            context['datefrom'] = self.request.GET['datefrom']
            context['dateto'] = self.request.GET['dateto']

        return context
