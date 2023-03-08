from django.contrib.auth.decorators import login_required
from endless_pagination.views import AjaxListView
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db.models import Sum
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.template.defaulttags import register
from accountspayable.models import Apmain, Apdetail
from companyparameter.models import Companyparameter
from replenish_rfv.models import Reprfvmain
import datetime
import json


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Apmain
    template_name = 'batchprinting_accountspayable/index.html'
    
    def get_context_data(self, **kwargs):
       context = super(IndexView, self).get_context_data(**kwargs)
       return context


def check_monthandyear(dfrom, dto):
    d1 = datetime.datetime.strptime(dfrom, '%Y-%m-%d').date()
    d2 = datetime.datetime.strptime(dto, '%Y-%m-%d').date()

    if d1.month == d2.month and d1.year == d2.year:
        return True
    
    return False


def retrieve(request):
    dfrom = request.GET["dfrom"]
    dto = request.GET["dto"]
    docnum_from = request.GET["docnum_from"]
    docnum_to = request.GET["docnum_to"]

    if dfrom != '' and dto != '':
        is_same = check_monthandyear(dfrom, dto)
    else:
        is_same = True

    if not is_same:
        data = {
            'status': 'failed',
            'message': 'Both dates in range must be on the same month.'
        }
    else:
        ap_data = {}
        
        # apdate filter
        if dfrom != '' and dto != '':
            ap_data = Apmain.objects.filter(apdate__range=[dfrom, dto]).order_by('apdate')
        elif dfrom != '' and dto == '':
            ap_data = Apmain.objects.filter(apdate=dfrom).order_by('apdate')
        elif dfrom == '' and dto != '':
            ap_data = Apmain.objects.filter(apdate=dto).order_by('apdate')
        
        # apnum filter
        if ap_data:
            if docnum_from != '' and docnum_to != '':
                ap_data = ap_data.filter(apnum__range=[docnum_from, docnum_to])
            elif docnum_from != '' and docnum_to == '':
                ap_data = ap_data.filter(apnum=docnum_from)
            elif docnum_from == '' and docnum_to != '':
                ap_data = ap_data.filter(apnum=docnum_to)
        else:
            if docnum_from != '' and docnum_to != '':
                ap_data = Apmain.objects.filter(apnum__range=[docnum_from, docnum_to])
            elif docnum_from != '' and docnum_to == '':
                ap_data = Apmain.objects.filter(apnum=docnum_from)
            elif docnum_from == '' and docnum_to != '':
                ap_data = Apmain.objects.filter(apnum=docnum_to)

        context = {}
        context['ap_data'] = ap_data
        viewhtml = render_to_string('batchprinting_accountspayable/index_list.html', context)
        
        data = {
            'status': 'success',
            'viewhtml': viewhtml
        }

    return JsonResponse(data)


@register.filter
def keyvalue(dict, key):    
    return dict[key]


@csrf_exempt
def start(request):
    ap_ids = json.loads(request.GET['s'])
    parameter = {}
    info = {}
    pagenum = 0

    for ap_id in ap_ids:
        ap_id = int(ap_id)
        try:
            detail_length = 0
            parameter[ap_id] = {}
            parameter[ap_id]['is_multi_page'] = False

            parameter[ap_id]['apmain'] = Apmain.objects.get(pk=ap_id, isdeleted=0, confi=0)
            
            detail = Apdetail.objects.filter(isdeleted=0). \
                filter(apmain_id=ap_id).order_by('-balancecode', 'item_counter')

            parameter[ap_id]['totaldebitamount'] = Apdetail.objects.filter(isdeleted=0). \
                filter(apmain_id=ap_id).aggregate(Sum('debitamount'))
            parameter[ap_id]['totalcreditamount'] = Apdetail.objects.filter(isdeleted=0). \
                filter(apmain_id=ap_id).aggregate(Sum('creditamount'))

            parameter[ap_id]['reprfvmain'] = Reprfvmain.objects.filter(isdeleted=0, \
                apmain=ap_id).order_by('enterdate')
            ap_main_aggregate = Reprfvmain.objects.filter(isdeleted=0, apmain=ap_id).aggregate(Sum('amount'))
            parameter[ap_id]['reprfv_total_amount'] = ap_main_aggregate['amount__sum']

            taxable_entries = detail.filter(balancecode='D', debitamount__gt=0.00).exclude(
                chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat).order_by('item_counter')
            taxable_total = taxable_entries.aggregate(Sum('debitamount'))
            vat_entries = detail.filter(balancecode='D', debitamount__gt=0.00, chartofaccount=Companyparameter.
                                                objects.get(code='PDI').coa_inputvat).order_by('item_counter')
            vat_total = vat_entries.aggregate(Sum('debitamount'))
            aptrade_entries = detail.filter(balancecode='C', creditamount__gt=0.00).exclude(
                chartofaccount = Companyparameter.objects.get(code='PDI').coa_ewtax).order_by('item_counter')
            aptrade_total = aptrade_entries.aggregate(Sum('creditamount'))
            wtax_entries = detail.filter(balancecode='C', creditamount__gt=0.00, chartofaccount=Companyparameter.
                                                objects.get(code='PDI').coa_ewtax).order_by('item_counter')
            wtax_total = wtax_entries.aggregate(Sum('creditamount'))

            if parameter[ap_id]['apmain'].vatrate > 0:
                parameter[ap_id]['vatablesale'] = taxable_total['debitamount__sum']
                parameter[ap_id]['vatexemptsale'] = 0
                parameter[ap_id]['vatzeroratedsale'] = 0
            elif parameter[ap_id]['apmain'].vatcode == 'VE':
                parameter[ap_id]['vatablesale'] = 0
                parameter[ap_id]['vatexemptsale'] = taxable_total['debitamount__sum']
                parameter[ap_id]['vatzeroratedsale'] = 0
            elif parameter[ap_id]['apmain'].vatcode == 'ZE' or parameter[ap_id]['apmain'].vatcode == 'VATNA':
                parameter[ap_id]['vatablesale'] = 0
                parameter[ap_id]['vatexemptsale'] = 0
                parameter[ap_id]['vatzeroratedsale'] = taxable_total['debitamount__sum']

            parameter[ap_id]['totalsale'] = taxable_total['debitamount__sum']
            parameter[ap_id]['addvat'] = vat_total['debitamount__sum']
            parameter[ap_id]['totalpayment'] = aptrade_total['creditamount__sum']
            parameter[ap_id]['wtaxamount'] = wtax_total['creditamount__sum']
            parameter[ap_id]['wtaxrate'] = parameter[ap_id]['apmain'].ataxrate
            
            detail_length = len(detail)
            if detail_length > 15:
                parameter[ap_id]['is_multi_page'] = True
                segment = 15
                iterable = float(detail_length) / segment
                # check wether whole number or decimal
                if not (iterable).is_integer():
                    iterable = int(iterable) + 1
                else:
                    iterable = int(iterable)
                
                parameter[ap_id]['interval'] = range(iterable)
                parameter[ap_id]['sorteddetail'] = [detail[i * segment:(i + 1) * segment] for i in range((detail_length + segment - 1) // segment)]
                
                # sub page number generator
                for i in range(iterable):
                    pagenum += 1
                    parameter[ap_id][int(i)] = pagenum
            else:
                pagenum += 1
                parameter[ap_id]['pagenum'] = pagenum
                parameter[ap_id]['detail'] = detail
            
            printedap = Apmain.objects.get(pk=ap_id, isdeleted=0)
            printedap.print_ctr += 1
            printedap.save()
           
        except Exception as e:
            print e

    info['logo'] = request.build_absolute_uri('/static/images/pdi.jpg')
    info['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
    info['pagenum'] = pagenum
    return render(request, 'batchprinting_accountspayable/preprint.html', {'info': info, 'parameter': parameter})


