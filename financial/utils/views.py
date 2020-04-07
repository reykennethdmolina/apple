import re
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import subprocess

# add models here
from supplier.models import Supplier
from chartofaccount.models import Chartofaccount
from employee.models import Employee
from department.models import Department
from customer.models import Customer
from accountspayable.models import Apmain
from journalvoucher.models import Jvmain
from inventoryitem.models import Inventoryitem
from operationalfund.models import Ofmain
from checkvoucher.models import Cvmain
from debitcreditmemo.models import Dcmain
from acknowledgementreceipt.models import Armain
from officialreceipt.models import Ormain
from agent.models import Agent
from bankaccount.models import Bankaccount


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
                                                  Q(lastname__icontains=request.GET['q'])).\
                exclude(Q(firstname='') | Q(lastname='') | Q(firstname=None) | Q(lastname=None)).order_by('lastname')

        elif request.GET['table'] == "customer" or request.GET['table'] == "customer_notmultiple":
            items = Customer.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))

        elif request.GET['table'] == "agency":
            items = Customer.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))
        elif request.GET['table'] == "client":
            items = Customer.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))
        elif request.GET['table'] == "agent":
            items = Agent.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))

        elif request.GET['table'] == "chartofaccount":
            print 'pasok'
            items = Chartofaccount.objects.all().filter(Q(accountcode__startswith=request.GET['q']) |
                                                        Q(description__startswith=request.GET['q'].upper())).order_by('accountcode')
        elif request.GET['table'] == "chartofaccount_posting":
            items = Chartofaccount.objects.all().filter(Q(accountcode__startswith=request.GET['q']) |
                                                        Q(description__startswith=request.GET['q'].upper())).filter(accounttype='P').order_by('accountcode')
        elif request.GET['table'] == "chartofaccount_arcode":
            items = Chartofaccount.objects.all().filter(Q(accountcode__startswith=request.GET['q']) |
                                                        Q(description__startswith=request.GET['q'].upper())).filter(main=1).order_by('accountcode')
        elif request.GET['table'] == "chartofaccount_revcode":
            items = Chartofaccount.objects.all().filter(Q(accountcode__startswith=request.GET['q']) |
                                                        Q(description__startswith=request.GET['q'].upper())).filter(main__in=[2, 4]).order_by('accountcode')
        elif request.GET['table'] == "chartofaccount_subgroup":
            items = Chartofaccount.objects.all().filter(Q(accountcode__startswith=request.GET['q']) |
                                                        Q(description__startswith=request.GET['q'].upper())).filter(accounttype='P').order_by('accountcode')
            items = items.filter(subgroup__in=request.GET.getlist('subgroup[]'))

        elif request.GET['table'] == "department":
            items = Department.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                    Q(departmentname__icontains=request.GET['q']))

        elif request.GET['table'] == "bankaccount":
            items = Bankaccount.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                    Q(accountnumber__icontains=request.GET['q']))

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

        items = items.filter(isdeleted=0)

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
                text = data.code + " | " + data.name + " - " + data.tin
            elif request.GET['table'] == "supplier_payee":
                text = data.name
            elif request.GET['table'] == "employee" \
                    or request.GET['table'] == "employee_notmultiple":
                text = data.code + " - " + data.lastname + ", " + data.firstname
            elif request.GET['table'] == "customer" \
                    or request.GET['table'] == "customer_notmultiple":
                text = data.name
            elif request.GET['table'] == "agency" \
                    or request.GET['table'] == "client" \
                    or request.GET['table'] == "agent":
                text = "[" + data.code + "] " + data.name
            elif request.GET['table'] == "chartofaccount" \
                    or request.GET['table'] == "chartofaccount_posting" \
                    or request.GET['table'] == "chartofaccount_arcode" \
                    or request.GET['table'] == "chartofaccount_revcode" \
                    or request.GET['table'] == "chartofaccount_subgroup":
                text = "[" + data.accountcode + "] - " + data.description
            elif request.GET['table'] == "department":
                text = data.departmentname
            elif request.GET['table'] == "bankaccount":
                text = data.code + " - " + data.accountnumber
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
                                  'type': data.inventoryitemclass.inventoryitemtype.code,
                                  'typecode': data.inventoryitemclass.code,
                                  'itemtype': data.inventoryitemclass.inventoryitemtype.code})
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
            if request.POST['cache_apsubtype']:
                items = items.filter(apsubtype=str(request.POST['cache_apsubtype']))
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
            if request.POST['cache_approver']:
                items = items.filter(designatedapprover_id=int(request.POST['cache_approver']))

            elif request.POST['cache_duedate_from']:
                items = items.filter(duedate__gte=request.POST['cache_duedate_from'])
            elif request.POST['cache_duedate_from']:
                items = items.filter(duedate__lte=request.POST['cache_duedate_to'])

        elif request.POST['table'] == "jvmain":
            items = Jvmain.objects.all().filter(isdeleted=0).order_by('pk')

            if request.POST['cache_jvnum_from']:
                items = items.filter(jvnum__gte=int(request.POST['cache_jvnum_from']))
            if request.POST['cache_jvnum_to']:
                items = items.filter(jvnum__lte=int(request.POST['cache_jvnum_to']))
            if request.POST['cache_jvdate_from']:
                items = items.filter(jvdate__gte=request.POST['cache_jvdate_from'])
            if request.POST['cache_jvdate_to']:
                items = items.filter(jvdate__lte=request.POST['cache_jvdate_to'])
            if request.POST['cache_jvtype']:
                items = items.filter(jvtype=str(request.POST['cache_jvtype']))
            if request.POST['cache_jvsubtype']:
                items = items.filter(jvsubtype=str(request.POST['cache_jvsubtype']))
            if request.POST['cache_refnum']:
                items = items.filter(refnum__icontains=str(request.POST['cache_refnum']))
            if request.POST['cache_branch']:
                items = items.filter(branch=int(request.POST['cache_branch']))
            if request.POST['cache_department']:
                items = items.filter(department=int(request.POST['cache_department']))
            if request.POST['cache_jvstatus']:
                items = items.filter(jvstatus=str(request.POST['cache_jvstatus']))
            if request.POST['cache_currency']:
                items = items.filter(currency=int(request.POST['cache_currency']))
            if request.POST['cache_particulars']:
                items = items.filter(particular__icontains=str(request.POST['cache_particulars']))
            if request.POST['cache_approver']:
                items = items.filter(designatedapprover_id=int(request.POST['cache_approver']))

        elif request.POST['table'] == "ofmain":
            items = Ofmain.objects.all().filter(isdeleted=0).order_by('pk')
            items = items.filter(Q(ofstatus='F') | Q(ofstatus='A') | Q(ofstatus='I') | Q(ofstatus='R') | Q(ofstatus='O') | Q(ofstatus='P'))

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
                print request.POST['cache_employee']
                items = items.filter(requestor_id=int(request.POST['cache_employee']))
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
            if request.POST['cache_approver']:
                items = items.filter(designatedapprover_id=int(request.POST['cache_approver']))

        elif request.POST['table'] == "dcmain":
            items = Dcmain.objects.all().filter(isdeleted=0).order_by('pk')
            if request.POST['cache_dcnum_from'] and request.POST['cache_dcnum_to']:
                items = items.filter(dcnum__range=[int(request.POST['cache_dcnum_from']),
                                                   int(request.POST['cache_dcnum_to'])])
            elif request.POST['cache_dcnum_from']:
                items = items.filter(dcnum__gte=int(request.POST['cache_dcnum_from']))
            elif request.POST['cache_dcnum_to']:
                items = items.filter(dcnum__lte=int(request.POST['cache_dcnum_to']))
            if request.POST['cache_dcdate_from'] and request.POST['cache_dcdate_to']:
                items = items.filter(dcdate__range=[request.POST['cache_dcdate_from'],
                                                    request.POST['cache_dcdate_to']])
            elif request.POST['cache_dcdate_from']:
                items = items.filter(dcdate__gte=request.POST['cache_dcdate_from'])
            elif request.POST['cache_dcdate_to']:
                items = items.filter(dcdate__lte=request.POST['cache_dcdate_to'])
            if request.POST['cache_customer_name']:
                items = items.filter(customer_name__icontains=str(request.POST['cache_customer_name']))
            if request.POST['cache_dctype']:
                items = items.filter(dctype=str(request.POST['cache_dctype']))
            if request.POST['cache_dcsubtype']:
                items = items.filter(dcsubtype=str(request.POST['cache_dcsubtype']))
            if request.POST['cache_dcclasstype']:
                items = items.filter(dcclasstype=int(request.POST['cache_dcclasstype']))
            if request.POST['cache_branch']:
                items = items.filter(branch=int(request.POST['cache_branch']))
            if request.POST['cache_vat']:
                items = items.filter(vat=int(request.POST['cache_vat']))
            if request.POST['cache_outputvattype']:
                items = items.filter(outputvattype=int(request.POST['cache_outputvattype']))
            if request.POST['cache_particulars']:
                items = items.filter(particulars__icontains=str(request.POST['cache_particulars']))

        elif request.POST['table'] == "armain":
            items = Armain.objects.all().filter(isdeleted=0).order_by('pk')
            if request.POST['cache_arnum_from'] and request.POST['cache_arnum_to']:
                items = items.filter(arnum__range=[int(request.POST['cache_arnum_from']),
                                                   int(request.POST['cache_arnum_to'])])
            elif request.POST['cache_arnum_from']:
                items = items.filter(arnum__gte=int(request.POST['cache_arnum_from']))
            elif request.POST['cache_arnum_to']:
                items = items.filter(arnum__lte=int(request.POST['cache_arnum_to']))
            if request.POST['cache_artype']:
                items = items.filter(artype=int(request.POST['cache_artype']))
            if request.POST['cache_ardate_from'] and request.POST['cache_ardate_to']:
                items = items.filter(ardate__range=[request.POST['cache_ardate_from'],
                                                    request.POST['cache_ardate_to']])
            elif request.POST['cache_ardate_from']:
                items = items.filter(ardate__gte=request.POST['cache_ardate_from'])
            elif request.POST['cache_ardate_to']:
                items = items.filter(ardate__lte=request.POST['cache_ardate_to'])
            if request.POST['cache_branch']:
                items = items.filter(branch=int(request.POST['cache_branch']))
            if request.POST['cache_amount_from'] and request.POST['cache_amount_to']:
                items = items.filter(amount__range=[request.POST['cache_amount_from'].replace(',', ''),
                                                    request.POST['cache_amount_to'].replace(',', '')])
            elif request.POST['cache_amount_from']:
                items = items.filter(amount__gte=request.POST['cache_amount_from'].replace(',', ''))
            elif request.POST['cache_amount_to']:
                items = items.filter(amount__lte=request.POST['cache_amount_to'].replace(',', ''))
            if request.POST['cache_payor_name']:
                items = items.filter(payor_name__icontains=str(request.POST['cache_payor_name']))
            if request.POST['cache_collector']:
                items = items.filter(collector=int(request.POST['cache_collector']))
            if request.POST['cache_depositorybank']:
                items = items.filter(depositorybank=int(request.POST['cache_depositorybank']))
            if request.POST['cache_particulars']:
                items = items.filter(particulars__icontains=str(request.POST['cache_particulars']))

        elif request.POST['table'] == "ormain":
            items = Ormain.objects.all().filter(isdeleted=0).order_by('pk')
            if request.POST['cache_ornum_from'] and request.POST['cache_ornum_to']:
                items = items.filter(ornum__range=[int(request.POST['cache_ornum_from']),
                                                   int(request.POST['cache_ornum_to'])])
            elif request.POST['cache_ornum_from']:
                items = items.filter(ornum__gte=int(request.POST['cache_ornum_from']))
            elif request.POST['cache_ornum_to']:
                items = items.filter(ornum__lte=int(request.POST['cache_ornum_to']))
            if request.POST['cache_ortype']:
                items = items.filter(ortype=int(request.POST['cache_ortype']))
            if request.POST['cache_ordate_from'] and request.POST['cache_ordate_to']:
                items = items.filter(ordate__range=[request.POST['cache_ordate_from'],
                                                    request.POST['cache_ordate_to']])
            elif request.POST['cache_ordate_from']:
                items = items.filter(ordate__gte=request.POST['cache_ordate_from'])
            elif request.POST['cache_ordate_to']:
                items = items.filter(ordate__lte=request.POST['cache_ordate_to'])
            if request.POST['cache_artype']:
                print request.POST['cache_artype']
                items = items.filter(orsource=request.POST['cache_artype'])
            if request.POST['cache_amount_from'] and request.POST['cache_amount_to']:
                items = items.filter(amount__range=[request.POST['cache_amount_from'].replace(',', ''),
                                                    request.POST['cache_amount_to'].replace(',', '')])
            elif request.POST['cache_amount_from']:
                items = items.filter(amount__gte=request.POST['cache_amount_from'].replace(',', ''))
            elif request.POST['cache_amount_to']:
                items = items.filter(amount__lte=request.POST['cache_amount_to'].replace(',', ''))
            if request.POST['cache_branch']:
                items = items.filter(branch=int(request.POST['cache_branch']))
            if request.POST['cache_collector']:
                items = items.filter(collector=int(request.POST['cache_collector']))
            if request.POST['cache_payee_name']:
                items = items.filter(payee_name__icontains=str(request.POST['cache_payee_name']))
            if request.POST['cache_vat']:
                items = items.filter(vat=int(request.POST['cache_vat']))
            if request.POST['cache_outputvattype']:
                items = items.filter(outputvattype=int(request.POST['cache_outputvattype']))
            if request.POST['cache_deferredvat']:
                items = items.filter(deferredvat=str(request.POST['cache_deferredvat']))
            if request.POST['cache_wtax']:
                items = items.filter(wtax=int(request.POST['cache_wtax']))
            if request.POST['cache_bankaccount']:
                items = items.filter(bankaccount=int(request.POST['cache_bankaccount']))
            if request.POST['cache_government']:
                items = items.filter(government=str(request.POST['cache_government']))
            if request.POST['cache_particulars']:
                items = items.filter(particulars__icontains=str(request.POST['cache_particulars']))
            if request.POST['cache_product']:
                items = items.filter(product=int(request.POST['cache_product']))
            if request.POST['cache_remarks']:
                items = items.filter(remarks__icontains=str(request.POST['cache_remarks']))

        items = items[:500]
        listitems = []

        for data in items:
            if request.POST['table'] == "apmain":
                listitems.append({'text': data.apnum, 'id': data.id})
            elif request.POST['table'] == "jvmain":
                listitems.append({'text': data.jvnum, 'id': data.id})
            elif request.POST['table'] == "ofmain":
                listitems.append({'text': data.ofnum, 'id': data.id})
            elif request.POST['table'] == "cvmain":
                listitems.append({'text': data.cvnum, 'id': data.id})
            elif request.POST['table'] == "dcmain":
                listitems.append({'text': data.dcnum, 'id': data.id})
            elif request.POST['table'] == "armain":
                listitems.append({'text': data.arnum, 'id': data.id})
            elif request.POST['table'] == "ormain":
                listitems.append({'text': data.ornum, 'id': data.id})

        data = {
            'status': 'success',
            'items': listitems,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


# count items in .txt file
def wccount(filename):
    out = subprocess.Popen(['wc', '-l', filename],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT
                         ).communicate()[0]
    return int(out.partition(b' ')[0])


# upload file
def storeupload(file, file_name, file_extension, upload_directory):
    from django.core.files.storage import FileSystemStorage
    fs = FileSystemStorage()
    filename = fs.save(upload_directory+file_name+'.'+file_extension, file)
    fs.url(filename)
    return True


# round bytes
def roundBytes(size, unit):
    roundoff = 2
    if unit.lower() == 'mb':
        return round(float(size)/1000024, roundoff)
    elif unit.lower() == 'kb':
        return round(float(size)/1024, roundoff)
    else:
        return size


@csrf_exempt
def ajaxSelect2(request):
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
                                                  Q(lastname__icontains=request.GET['q'])).\
                exclude(Q(firstname='') | Q(lastname='') | Q(firstname=None) | Q(lastname=None)).order_by('lastname')

        elif request.GET['table'] == "customer" or request.GET['table'] == "customer_notmultiple":
            items = Customer.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))

        elif request.GET['table'] == "agency":
            items = Customer.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))
        elif request.GET['table'] == "client":
            items = Customer.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))
        elif request.GET['table'] == "agent":
            items = Agent.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                  Q(name__icontains=request.GET['q']))

        elif request.GET['table'] == "chartofaccount":
            items = Chartofaccount.objects.all().filter(Q(accountcode__startswith=request.GET['q']) |
                                                        Q(description__startswith=request.GET['q'].upper())).order_by('accountcode')
        elif request.GET['table'] == "chartofaccount_posting":
            items = Chartofaccount.objects.all().filter(Q(accountcode__startswith=request.GET['q']) |
                                                        Q(description__startswith=request.GET['q'].upper())).filter(accounttype='P').order_by('accountcode')
        elif request.GET['table'] == "chartofaccount_arcode":
            items = Chartofaccount.objects.all().filter(Q(accountcode__startswith=request.GET['q']) |
                                                        Q(description__startswith=request.GET['q'].upper())).filter(main=1).order_by('accountcode')
        elif request.GET['table'] == "chartofaccount_revcode":
            items = Chartofaccount.objects.all().filter(Q(accountcode__startswith=request.GET['q']) |
                                                        Q(description__startswith=request.GET['q'].upper())).filter(main__in=[2, 4]).order_by('accountcode')
        elif request.GET['table'] == "chartofaccount_subgroup":
            items = Chartofaccount.objects.all().filter(Q(accountcode__startswith=request.GET['q']) |
                                                        Q(description__startswith=request.GET['q'].upper())).filter(accounttype='P').order_by('accountcode')
            items = items.filter(subgroup__in=request.GET.getlist('subgroup[]'))

        elif request.GET['table'] == "department":
            items = Department.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                    Q(departmentname__icontains=request.GET['q']))

        elif request.GET['table'] == "bankaccount":
            items = Bankaccount.objects.all().filter(Q(code__icontains=request.GET['q']) |
                                                    Q(accountnumber__icontains=request.GET['q']))

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

        items = items.filter(isdeleted=0)

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
                #text = data.code + " - " + data.name
                text = data.code + " | " + data.name + " - " + data.tin
            elif request.GET['table'] == "supplier_payee":
                text = data.code + " | " + data.name + " - " + data.tin
            elif request.GET['table'] == "employee" \
                    or request.GET['table'] == "employee_notmultiple":
                text = data.code + " - " + data.lastname + ", " + data.firstname
            elif request.GET['table'] == "customer" \
                    or request.GET['table'] == "customer_notmultiple":
                text = data.name
            elif request.GET['table'] == "agency" \
                    or request.GET['table'] == "client" \
                    or request.GET['table'] == "agent":
                text = "[" + data.code + "] " + data.name
            elif request.GET['table'] == "chartofaccount" \
                    or request.GET['table'] == "chartofaccount_posting" \
                    or request.GET['table'] == "chartofaccount_arcode" \
                    or request.GET['table'] == "chartofaccount_revcode" \
                    or request.GET['table'] == "chartofaccount_subgroup":
                text = "[" + data.accountcode + "] - " + data.description
            elif request.GET['table'] == "department":
                text = data.departmentname
            elif request.GET['table'] == "bankaccount":
                text = data.code + " - " + data.accountnumber
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
                                  'type': data.inventoryitemclass.inventoryitemtype.code,
                                  'typecode': data.inventoryitemclass.code,
                                  'itemtype': data.inventoryitemclass.inventoryitemtype.code})
            else:
                listitems.append({'text': newtext, 'id': data.code})

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