from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from endless_pagination.views import AjaxListView
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db.models import Sum
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.template.defaulttags import register
from journalvoucher.models import Jvmain, Jvdetail
from operationalfund.models import Ofmain
from companyparameter.models import Companyparameter
from companyparameter.models import Companyparameter
import datetime
import json


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Jvmain
    template_name = 'batchprinting_journalvoucher/index.html'
    
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

    is_same = True
    if dfrom != '' and dto != '':
        is_same = check_monthandyear(dfrom, dto)
    
    if not is_same:
        data = {
            'status': 'failed',
            'message': 'Both dates in range must be on the same month.'
        }
    else:
        jv_data = {}
        jv_data = Jvmain.objects.filter(confi=0)
        # jvdate filter
        if dfrom != '' and dto != '':
            jv_data = jv_data.filter(jvdate__range=[dfrom, dto]).order_by('jvdate')
        elif dfrom != '' and dto == '':
            jv_data = jv_data.filter(jvdate=dfrom).order_by('jvdate')
        elif dfrom == '' and dto != '':
            jv_data = jv_data.filter(jvdate=dto).order_by('jvdate')
        
        # jvnum filter
        if jv_data:
            if docnum_from != '' and docnum_to != '':
                jv_data = jv_data.filter(jvnum__range=[docnum_from, docnum_to])
            elif docnum_from != '' and docnum_to == '':
                jv_data = jv_data.filter(jvnum=docnum_from)
            elif docnum_from == '' and docnum_to != '':
                jv_data = jv_data.filter(jvnum=docnum_to)
        else:
            if docnum_from != '' and docnum_to != '':
                jv_data = Jvmain.objects.filter(jvnum__range=[docnum_from, docnum_to])
            elif docnum_from != '' and docnum_to == '':
                jv_data = Jvmain.objects.filter(jvnum=docnum_from)
            elif docnum_from == '' and docnum_to != '':
                jv_data = Jvmain.objects.filter(jvnum=docnum_to)

        context = {}
        context['jv_data'] = jv_data
        viewhtml = render_to_string('batchprinting_journalvoucher/index_list.html', context)
        
        data = {
            'status': 'success',
            'viewhtml': viewhtml
        }

    return JsonResponse(data)


@csrf_exempt
def start(request):
    jv_ids = json.loads(request.GET['s'])
    parameter = {}
    detail = {}
    pagenum = 0
    
    for jv_id in jv_ids:
        
        jv_id = int(jv_id)
        try:
            parameter[jv_id] = {}
            parameter[jv_id]['is_multi_page'] = False

            parameter[jv_id]['jvmain'] = Jvmain.objects.get(pk=jv_id, isdeleted=0)
            parameter[jv_id]['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
            accounting_entries = Jvdetail.objects.filter(isdeleted=0). \
                filter(jvmain_id=jv_id).order_by('item_counter')
            
            detail_length = len(accounting_entries)
            
            if detail_length > 25:
                parameter[jv_id]['is_multi_page'] = True
                segment = 25
                
                iterable = float(detail_length) / segment
                
                # check wether whole number or decimal
                if not (iterable).is_integer():
                    iterable += 1
                
                parameter[jv_id]['interval'] = range(int(iterable))
                parameter[jv_id]['sorteddetail'] = [accounting_entries[i * segment:(i + 1) * segment] for i in range((detail_length + segment - 1) // segment)]
                
                for i in range(int(iterable)):
                    pagenum += 1
                    parameter[jv_id][int(i)] = pagenum
            else:
                pagenum += 1
                parameter[jv_id]['pagenum'] = pagenum
                parameter[jv_id]['detail'] = accounting_entries

            parameter[jv_id]['totaldebitamount'] = Jvdetail.objects.filter(isdeleted=0). \
                filter(jvmain_id=jv_id).aggregate(Sum('debitamount'))
            parameter[jv_id]['totalcreditamount'] = Jvdetail.objects.filter(isdeleted=0). \
                filter(jvmain_id=jv_id).aggregate(Sum('creditamount'))

            parameter[jv_id]['ofmain'] = Ofmain.objects.filter(isdeleted=0, jvmain=jv_id).order_by(
                'enterdate')
            jv_main_aggregate = Ofmain.objects.filter(isdeleted=0, jvmain=jv_id).aggregate(
                Sum('amount'))
            parameter[jv_id]['ofcsvmain_total_amount'] = jv_main_aggregate['amount__sum']

            printedjv = Jvmain.objects.get(pk=jv_id, isdeleted=0)
            printedjv.print_ctr += 1
            printedjv.save()

        except Exception as e:
            print e
    
    # reorder the array to fix page numbering
    ordered_parameter = OrderedDict(sorted(parameter.items(), key=lambda x:int(x[0])))
    
    detail['logo'] = request.build_absolute_uri('/static/images/pdi.jpg')
    detail['pagenum'] = pagenum
    return render(request, 'batchprinting_journalvoucher/preprint.html', {'detail': detail, 'parameter': ordered_parameter})

    
@register.filter
def keyvalue(dict, key):    
    return dict[key]
