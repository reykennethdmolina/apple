from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
@csrf_exempt
def maccountingentry(request):
    if request.method == 'POST':
        context = {
            'users': 'hoy'
        }
        data = {
            'status': 'success',
            'viewhtml': render_to_string('acctentry/manualentry.html', context),
        }
    else:
        context = {
            'users': 'hoy'
        }
        data = {
            'status': 'error',
            'viewhtml': render_to_string('acctentry/manualentry.html', context),
        }

    print data
    return JsonResponse(data)


