import re
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# add models here
from supplier.models import Supplier
from chartofaccount.models import Chartofaccount
from employee.models import Employee
from department.models import Department
from accountspayable.models import Apmain


@csrf_exempt
def ajaxSelect(request):
    if request.method == 'GET':

        # add model query here
        if request.GET['table'] == "supplier" or request.GET['table'] == "payee":
            items = Supplier.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))\
                .filter(isdeleted=0).order_by('-enterdate')
        elif request.GET['table'] == "chartofaccount":
            items = Chartofaccount.objects.all().filter(Q(accountcode__icontains=request.GET['q']) |
                                                        Q(title__icontains=request.GET['q']))\
                .filter(isdeleted=0).order_by('-enterdate')
        elif request.GET['table'] == "employee":
            items = Employee.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(firstname__icontains=request.GET['q']) |
                                                  Q(middlename__icontains=request.GET['q']) |
                                                  Q(lastname__icontains=request.GET['q']))\
                .filter(isdeleted=0).order_by('-enterdate')
        elif request.GET['table'] == "department":
            items = Department.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                    Q(departmentname__icontains=request.GET['q']))\
                .filter(isdeleted=0).order_by('-enterdate')

        count = items.count()
        limit = 10
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
            elif request.GET['table'] == "payee":
                text = data.name
            elif request.GET['table'] == "chartofaccount":
                text = data.accountcode + " - " + data.title
            elif request.GET['table'] == "employee":
                text = data.code + " - " + data.lastname + ", " + data.firstname + " " + data.middlename
            elif request.GET['table'] == "department":
                text = data.code + " - " + data.departmentname

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


@csrf_exempt
def ajaxSearch(request):
    if request.method == 'POST':

        # add model query here
        if request.POST['table'] == "apmain":
            items = Apmain.objects.all().filter(isdeleted=0).order_by('pk')

            if request.POST['cache_apnum_from'] and request.POST['cache_apnum_to']:
                items =items.filter(apnum__range=[int(request.POST['cache_apnum_from']),
                                                  int(request.POST['cache_apnum_to'])])

        listitems = []

        for data in items:
            if request.POST['table'] == "apmain":
                listitems.append({'text': data.apnum, 'id': data.id})

        data = {
            'status': 'success',
            'items': listitems,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

# pagination function goes here
