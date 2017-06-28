import re
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# add models here
from supplier.models import Supplier
from chartofaccount.models import Chartofaccount

@csrf_exempt
def ajaxSelect(request):
    if request.method == 'GET':

        # add model query here
        if request.GET['table'] == "supplier":
            items = Supplier.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))\
                .filter(isdeleted=0).order_by('-enterdate')
        elif request.GET['table'] == "chartofaccount":
            items = Chartofaccount.objects.all().filter(Q(accountcode__icontains=request.GET['q']) |
                                                        Q(title__icontains=request.GET['q']))\
                .filter(isdeleted=0).order_by('-enterdate')

        count = items.count()
        limit = 6
        offset = (int(request.GET['page']) - 1) * limit
        items = items[offset:offset+limit]
        endcount = offset + limit
        morepages = endcount > count
        listitems = []

        for data in items:
            q = "<b>" + request.GET['q'] + "</b>"

            # add model text format here
            if request.GET['table'] == "supplier":
                text = data.code + " - " + data.name
            elif request.GET['table'] == "chartofaccount":
                text = data.accountcode + " - " + data.title

            newtext = re.compile(re.escape(request.GET['q']), re.IGNORECASE)
            newtext = newtext.sub(q.upper(), text)
            listitems.append({'text': newtext, 'id': data.id})

        data = {
            'status': 'success',
            'items': listitems,
            'more': morepages,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)
