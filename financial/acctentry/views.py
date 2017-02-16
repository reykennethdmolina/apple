from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from chartofaccount.models import Chartofaccount
from bank.models import Bank

import json

# Create your views here.
@csrf_exempt
def maccountingentry(request):
    if request.method == 'POST':

        #context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0).order_by('accountcode')
        context = {
            'chartofaccount':  Chartofaccount.objects.filter(isdeleted=0).order_by('accountcode'),
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('acctentry/manualentry.html', context),
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

@csrf_exempt
def checkchartvalidatetion(request):

    if request.method == 'POST':
        chartid = request.POST['chartid']
        chartdata = Chartofaccount.objects.filter(pk=chartid)
        bank = Bank.objects.filter(isdeleted=0)
        data = {
            'status': 'success',
            'chart': serializers.serialize("json", chartdata),
            'bank': serializers.serialize("json", bank),
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)
    #return HttpResponse(data, content_type='application/json')
    #return HttpResponse(data, content_type="application/json")
