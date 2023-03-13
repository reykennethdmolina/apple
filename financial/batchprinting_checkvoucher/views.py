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
from checkvoucher.models import Cvmain, Cvdetail
from companyparameter.models import Companyparameter
from replenish_pcv.models import Reppcvmain
import datetime
import json


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Cvmain
    template_name = 'batchprinting_checkvoucher/index.html'
    
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
        cv_data = {}
        cv_data = Cvmain.objects.filter(confi=0)
        # cvdate filter
        if dfrom != '' and dto != '':
            cv_data = cv_data.filter(cvdate__range=[dfrom, dto]).order_by('cvdate')
        elif dfrom != '' and dto == '':
            cv_data = cv_data.filter(cvdate=dfrom).order_by('cvdate')
        elif dfrom == '' and dto != '':
            cv_data = cv_data.filter(cvdate=dto).order_by('cvdate')
        
        # cvnum filter
        if cv_data:
            if docnum_from != '' and docnum_to != '':
                cv_data = cv_data.filter(cvnum__range=[docnum_from, docnum_to])
            elif docnum_from != '' and docnum_to == '':
                cv_data = cv_data.filter(cvnum=docnum_from)
            elif docnum_from == '' and docnum_to != '':
                cv_data = cv_data.filter(cvnum=docnum_to)
        else:
            if docnum_from != '' and docnum_to != '':
                cv_data = Cvmain.objects.filter(cvnum__range=[docnum_from, docnum_to])
            elif docnum_from != '' and docnum_to == '':
                cv_data = Cvmain.objects.filter(cvnum=docnum_from)
            elif docnum_from == '' and docnum_to != '':
                cv_data = Cvmain.objects.filter(cvnum=docnum_to)

        context = {}
        context['cv_data'] = cv_data
        viewhtml = render_to_string('batchprinting_checkvoucher/index_list.html', context)
        
        data = {
            'status': 'success',
            'viewhtml': viewhtml
        }

    return JsonResponse(data)
    

@csrf_exempt
def start(request):
    cv_ids = json.loads(request.GET['s'])
    parameter = {}
    detail = {}
    pagenum = 0
    
    for cv_id in cv_ids:
        
        cv_id = int(cv_id)
        try:
            parameter[cv_id] = {}
            parameter[cv_id]['is_multi_page'] = False

            parameter[cv_id]['cvmain'] = Cvmain.objects.get(pk=cv_id)
            parameter[cv_id]['detail'] = Cvdetail.objects.filter(isdeleted=0). \
                filter(cvmain_id=cv_id).order_by('item_counter')
            
            detail_length = len(parameter[cv_id]['detail'])

            if detail_length > 8:
                parameter[cv_id]['is_multi_page'] = True
                succeeding_segment = 13
                segment = 8

                detail_length = detail_length - segment

                # plus 1 for the first page
                iterable = float(detail_length) / succeeding_segment + 1
                
                # check wether whole number or decimal
                if not (iterable).is_integer():
                    iterable += 1
                
                parameter[cv_id]['interval'] = range(int(iterable))
                
                first_details = [parameter[cv_id]['detail'][:8]]
                second = parameter[cv_id]['detail'][8:]
                succeeding_details = [second[i * succeeding_segment:(i + 1) * succeeding_segment] for i in range((detail_length + succeeding_segment - 1) // succeeding_segment)]
                parameter[cv_id]['sorteddetail'] = first_details + succeeding_details
                
                # sub page number generator
                for i in range(int(iterable)):
                    pagenum += 1
                    parameter[cv_id][int(i)] = pagenum
            else:
                pagenum += 1
                parameter[cv_id]['pagenum'] = pagenum

            parameter[cv_id]['totaldebitamount'] = Cvdetail.objects.filter(isdeleted=0). \
                filter(cvmain_id=cv_id).aggregate(Sum('debitamount'))
            parameter[cv_id]['totalcreditamount'] = Cvdetail.objects.filter(isdeleted=0). \
                filter(cvmain_id=cv_id).aggregate(Sum('creditamount'))

            parameter[cv_id]['convertedamount'] = Cvmain.objects.get(pk=cv_id, isdeleted=0).amount * Cvmain.objects.get(pk=cv_id, isdeleted=0).fxrate
            parameter[cv_id]['reppcvmain'] = Reppcvmain.objects.filter(isdeleted=0, cvmain=cv_id).order_by('enterdate')

            cv_main_aggregate = Reppcvmain.objects.filter(isdeleted=0, cvmain=cv_id).aggregate(
                Sum('amount'))
            parameter[cv_id]['reppcv_total_amount'] = cv_main_aggregate['amount__sum']

            printedcv = Cvmain.objects.get(pk=cv_id, isdeleted=0)
            printedcv.print_ctr += 1
            printedcv.save()
            
        except Exception as e:
            print e
    # reorder the array to fix page numbering
    ordered_parameter = OrderedDict(sorted(parameter.items(), key=lambda x:int(x[0])))
    
    detail['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
    detail['logo'] = request.build_absolute_uri('/static/images/pdi.jpg')
    detail['pagenum'] = pagenum
    return render(request, 'batchprinting_checkvoucher/preprint.html', {'detail': detail, 'parameter': ordered_parameter})


@register.filter
def keyvalue(dict, key):    
    return dict[key]
