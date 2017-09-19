import re
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

# add models here
from supplier.models import Supplier
from chartofaccount.models import Chartofaccount
from employee.models import Employee
from department.models import Department
from customer.models import Customer
from accountspayable.models import Apmain
from inventoryitem.models import Inventoryitem
from operationalfund.models import Ofmain
from checkvoucher.models import Cvmain


@csrf_exempt
def ajaxSelect(request):
    if request.method == 'GET':

        # add model query here
        if request.GET['table'] == "supplier" \
                or request.GET['table'] == "supplier_payee" \
                or request.GET['table'] == "supplier_notmultiple":
            items = Supplier.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))

        elif request.GET['table'] == "employee" or request.GET['table'] == "employee_notmultiple":
            items = Employee.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(firstname__icontains=request.GET['q']) |
                                                  Q(middlename__icontains=request.GET['q']) |
                                                  Q(lastname__icontains=request.GET['q']))

        elif request.GET['table'] == "customer" or request.GET['table'] == "customer_notmultiple":
            items = Customer.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))

        elif request.GET['table'] == "chartofaccount":
            items = Chartofaccount.objects.all().filter(Q(accountcode__icontains=request.GET['q']) |
                                                        Q(title__icontains=request.GET['q']))
        elif request.GET['table'] == "chartofaccount_posting":
            items = Chartofaccount.objects.all().filter(Q(accountcode__icontains=request.GET['q']) |
                                                        Q(title__icontains=request.GET['q'])).filter(accounttype='P')
        elif request.GET['table'] == "chartofaccount_arcode":
            items = Chartofaccount.objects.all().filter(Q(accountcode__icontains=request.GET['q']) |
                                                        Q(title__icontains=request.GET['q'])).filter(main=1)
        elif request.GET['table'] == "chartofaccount_revcode":
            items = Chartofaccount.objects.all().filter(Q(accountcode__icontains=request.GET['q']) |
                                                        Q(title__icontains=request.GET['q'])).filter(main__in=[2, 4])

        elif request.GET['table'] == "department":
            items = Department.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                    Q(departmentname__icontains=request.GET['q']))

        elif request.GET['table'] == "inventoryitem_SV" \
                or request.GET['table'] == "inventoryitem_SI" \
                or request.GET['table'] == "inventoryitem_FA" \
                or request.GET['table'] == "inventoryitem":
            items = Inventoryitem.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                    Q(description__icontains=request.GET['q']))
            if request.GET['table'] == "inventoryitem_SV":
                items = items.filter(inventoryitemclass__inventoryitemtype__code='SV')
            elif request.GET['table'] == "inventoryitem_SI":
                items = items.filter(inventoryitemclass__inventoryitemtype__code='SI')
            elif request.GET['table'] == "inventoryitem_FA":
                items = items.filter(inventoryitemclass__inventoryitemtype__code='FA')

        if request.GET['table'] == "supplier_notmultiple" \
                or request.GET['table'] == "employee_notmultiple" \
                or request.GET['table'] == "customer_notmultiple":
            items = items.filter(multiplestatus='N')

        items = items.filter(isdeleted=0).order_by('-enterdate')

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
            if request.GET['table'] == "supplier" \
                    or request.GET['table'] == "supplier_notmultiple":
                text = data.code + " - " + data.name
            elif request.GET['table'] == "supplier_payee":
                text = data.name
            elif request.GET['table'] == "employee" \
                    or request.GET['table'] == "employee_notmultiple":
                text = data.code + " - " + data.lastname + ", " + data.firstname + " " + data.middlename
            elif request.GET['table'] == "customer" \
                    or request.GET['table'] == "customer_notmultiple":
                text = data.name
            elif request.GET['table'] == "chartofaccount" \
                    or request.GET['table'] == "chartofaccount_posting" \
                    or request.GET['table'] == "chartofaccount_arcode" \
                    or request.GET['table'] == "chartofaccount_revcode":
                text = "[" + data.accountcode + "] - " + data.description
            elif request.GET['table'] == "department":
                text = data.departmentname
            elif request.GET['table'] == "inventoryitem" \
                    or request.GET['table'] == "inventoryitem_SV" \
                    or request.GET['table'] == "inventoryitem_SI" \
                    or request.GET['table'] == "inventoryitem_FA":
                text = data.code + " | " + data.description

            newtext = re.compile(re.escape(request.GET['q']), re.IGNORECASE)
            newtext = newtext.sub(q.upper(), text)
            # listitems.append({'text': newtext, 'id': data.id}

            if request.GET['table'] == "inventoryitem" \
                    or request.GET['table'] == "inventoryitem_SV" \
                    or request.GET['table'] == "inventoryitem_SI" \
                    or request.GET['table'] == "inventoryitem_FA":
                listitems.append({'text': newtext,
                                  'id': data.id,
                                  'um': data.unitofmeasure.id,
                                  'code': data.code,
                                  'type': data.inventoryitemclass.inventoryitemtype.code})
            else:
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
                items = items.filter(apnum__range=[int(request.POST['cache_apnum_from']),
                                                   int(request.POST['cache_apnum_to'])])
            elif request.POST['cache_apnum_from']:
                items = items.filter(apnum__gte=int(request.POST['cache_apnum_from']))
            elif request.POST['cache_apnum_to']:
                items = items.filter(apnum__lte=int(request.POST['cache_apnum_to']))
            if request.POST['cache_apdate_from'] and request.POST['cache_apdate_to']:
                items = items.filter(apdate__range=[request.POST['cache_apdate_from'],
                                                    request.POST['cache_apdate_to']])
            elif request.POST['cache_apdate_from']:
                items = items.filter(apdate__gte=request.POST['cache_apdate_from'])
            elif request.POST['cache_apdate_to']:
                items = items.filter(apdate__lte=request.POST['cache_apdate_to'])
            if request.POST['cache_payee']:
                items = items.filter(payee=int(request.POST['cache_payee']))
            if request.POST['cache_aptype']:
                items = items.filter(aptype=str(request.POST['cache_aptype']))
            if request.POST['cache_apstatus']:
                items = items.filter(apstatus=str(request.POST['cache_apstatus']))
            if request.POST['cache_branch']:
                items = items.filter(branch=int(request.POST['cache_branch']))
            if request.POST['cache_disbursingbranch']:
                items = items.filter(bankbranchdisburse=int(request.POST['cache_disbursingbranch']))
            if request.POST['cache_vat']:
                items = items.filter(vat=int(request.POST['cache_vat']))
            if request.POST['cache_atc']:
                items = items.filter(atax=int(request.POST['cache_atc']))
            if request.POST['cache_inputvattype']:
                items = items.filter(inputvattype=int(request.POST['cache_inputvattype']))
            if request.POST['cache_terms']:
                items = items.filter(creditterm=int(request.POST['cache_terms']))
            if request.POST['cache_deferred']:
                items = items.filter(deferred=str(request.POST['cache_deferred']))
            if request.POST['cache_particulars']:
                items = items.filter(particulars__icontains=str(request.POST['cache_particulars']))
            if request.POST['cache_refno']:
                items = items.filter(refno__icontains=str(request.POST['cache_refno']))
            if request.POST['cache_duedate_from'] and request.POST['cache_duedate_to']:
                items = items.filter(duedate__range=[request.POST['cache_duedate_from'],
                                                     request.POST['cache_duedate_to']])
            elif request.POST['cache_duedate_from']:
                items = items.filter(duedate__gte=request.POST['cache_duedate_from'])
            elif request.POST['cache_duedate_from']:
                items = items.filter(duedate__lte=request.POST['cache_duedate_to'])

        elif request.POST['table'] == "ofmain":
            items = Ofmain.objects.all().filter(isdeleted=0).order_by('pk')
            if request.user.has_perm('operationalfund.is_cashier'):
                items = items.filter(Q(ofstatus='A') | Q(ofstatus='I') | Q(ofstatus='R'))

            if request.POST['cache_ofnum_from'] and request.POST['cache_ofnum_to']:
                items = items.filter(ofnum__range=[int(request.POST['cache_ofnum_from']),
                                                   int(request.POST['cache_ofnum_to'])])
            elif request.POST['cache_ofnum_from']:
                items = items.filter(ofnum__gte=int(request.POST['cache_ofnum_from']))
            elif request.POST['cache_ofnum_to']:
                items = items.filter(ofnum__lte=int(request.POST['cache_ofnum_to']))
            if request.POST['cache_ofdate_from'] and request.POST['cache_ofdate_to']:
                items = items.filter(ofdate__range=[request.POST['cache_ofdate_from'],
                                                    request.POST['cache_ofdate_to']])
            elif request.POST['cache_ofdate_from']:
                items = items.filter(ofdate__gte=request.POST['cache_ofdate_from'])
            elif request.POST['cache_ofdate_to']:
                items = items.filter(ofdate__lte=request.POST['cache_ofdate_to'])
            if request.POST['cache_amount_from'] and request.POST['cache_amount_to']:
                items = items.filter(approvedamount__range=[request.POST['cache_amount_from'].replace(',', ''),
                                                    request.POST['cache_amount_to'].replace(',', '')])
            elif request.POST['cache_amount_from']:
                items = items.filter(approvedamount__gte=request.POST['cache_amount_from'].replace(',', ''))
            elif request.POST['cache_amount_to']:
                items = items.filter(approvedamount__lte=request.POST['cache_amount_to'].replace(',', ''))
            if request.POST['cache_oftype']:
                items = items.filter(oftype=int(request.POST['cache_oftype']))
            if request.POST['cache_branch']:
                items = items.filter(branch=int(request.POST['cache_branch']))
            if request.POST['cache_ofstatus']:
                items = items.filter(ofstatus=str(request.POST['cache_ofstatus']))
            if request.POST['cache_employee']:
                items = items.filter(employee=int(request.POST['cache_employee']))
            if request.POST['cache_department']:
                items = items.filter(department=int(request.POST['cache_department']))
            if request.POST['cache_creditterm']:
                items = items.filter(creditterm=int(request.POST['cache_creditterm']))
            if request.POST['cache_refnum']:
                items = items.filter(refnum__icontains=str(request.POST['cache_refnum']))
            if request.POST['cache_particulars']:
                items = items.filter(particulars__icontains=str(request.POST['cache_particulars']))

        elif request.POST['table'] == "cvmain":
            items = Cvmain.objects.all().filter(isdeleted=0).order_by('pk')
            if request.POST['cache_cvnum_from'] and request.POST['cache_cvnum_to']:
                items = items.filter(cvnum__range=[int(request.POST['cache_cvnum_from']),
                                                   int(request.POST['cache_cvnum_to'])])
            elif request.POST['cache_cvnum_from']:
                items = items.filter(cvnum__gte=int(request.POST['cache_cvnum_from']))
            elif request.POST['cache_cvnum_to']:
                items = items.filter(cvnum__lte=int(request.POST['cache_cvnum_to']))
            if request.POST['cache_cvdate_from'] and request.POST['cache_cvdate_to']:
                items = items.filter(cvdate__range=[request.POST['cache_cvdate_from'],
                                                    request.POST['cache_cvdate_to']])
            elif request.POST['cache_cvdate_from']:
                items = items.filter(cvdate__gte=request.POST['cache_cvdate_from'])
            elif request.POST['cache_cvdate_to']:
                items = items.filter(cvdate__lte=request.POST['cache_cvdate_to'])
            if request.POST['cache_payee_name']:
                items = items.filter(payee_name__icontains=str(request.POST['cache_payee_name']))
            if request.POST['cache_checknum']:
                items = items.filter(checknum__icontains=str(request.POST['cache_checknum']))
            if request.POST['cache_amount_from'] and request.POST['cache_amount_to']:
                items = items.filter(amount__range=[request.POST['cache_amount_from'].replace(',', ''),
                                                    request.POST['cache_amount_to'].replace(',', '')])
            elif request.POST['cache_amount_from']:
                items = items.filter(amount__gte=request.POST['cache_amount_from'].replace(',', ''))
            elif request.POST['cache_amount_to']:
                items = items.filter(amount__lte=request.POST['cache_amount_to'].replace(',', ''))
            if request.POST['cache_cvtype']:
                items = items.filter(cvtype=int(request.POST['cache_cvtype']))
            if request.POST['cache_cvsubtype']:
                items = items.filter(cvsubtype=int(request.POST['cache_cvsubtype']))
            if request.POST['cache_branch']:
                items = items.filter(branch=int(request.POST['cache_branch']))
            if request.POST['cache_cvstatus']:
                items = items.filter(cvstatus=str(request.POST['cache_cvstatus']))
            if request.POST['cache_vat']:
                items = items.filter(vat=int(request.POST['cache_vat']))
            if request.POST['cache_atc']:
                items = items.filter(atc=int(request.POST['cache_atc']))
            if request.POST['cache_inputvattype']:
                items = items.filter(inputvattype=int(request.POST['cache_inputvattype']))
            if request.POST['cache_deferredvat']:
                items = items.filter(deferredvat=str(request.POST['cache_deferredvat']))
            if request.POST['cache_currency']:
                items = items.filter(currency=int(request.POST['cache_currency']))
            if request.POST['cache_bankaccount']:
                items = items.filter(bankaccount=int(request.POST['cache_bankaccount']))
            if request.POST['cache_disbursingbranch']:
                items = items.filter(disbursingbranch=int(request.POST['cache_disbursingbranch']))
            if request.POST['cache_refnum']:
                items = items.filter(refnum__icontains=str(request.POST['cache_refnum']))
            if request.POST['cache_particulars']:
                items = items.filter(particulars__icontains=str(request.POST['cache_particulars']))

        items = items[:500]
        listitems = []

        for data in items:
            if request.POST['table'] == "apmain":
                listitems.append({'text': data.apnum, 'id': data.id})
            elif request.POST['table'] == "ofmain":
                listitems.append({'text': data.ofnum, 'id': data.id})
            elif request.POST['table'] == "cvmain":
                listitems.append({'text': data.cvnum, 'id': data.id})

        data = {
            'status': 'success',
            'items': listitems,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)

