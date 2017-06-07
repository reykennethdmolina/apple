from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F
from django.core import serializers
from .models import Pomain, Podetail, Podetailtemp, Podata, Prfpotransaction
from purchaserequisitionform.models import Prfmain, Prfdetail
from employee.models import Employee
from supplier.models import Supplier
from ataxcode.models import Ataxcode
from inputvattype.models import Inputvattype
from vat.models import Vat
from creditterm.models import Creditterm
from inventoryitem.models import Inventoryitem
from branch.models import Branch
from currency.models import Currency
from department.models import Department
from unitofmeasure.models import Unitofmeasure
from wtax.models import Wtax
from django.contrib.auth.models import User
from django.db.models import Sum
from acctentry.views import generatekey
import datetime

# Create your views here.


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Pomain
    template_name = 'purchaseorder/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Pomain.objects.all().filter(isdeleted=0).order_by('-enterdate')[0:10]

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['listcount'] = Pomain.objects.filter(isdeleted=0).count()
        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Pomain
    template_name = 'purchaseorder/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['podetail'] = Podetail.objects.filter(isdeleted=0).filter(pomain=self.kwargs['pk']).\
            order_by('item_counter')
        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Pomain
    template_name = 'purchaseorder/create.html'
    fields = ['podate', 'potype', 'refnum', 'urgencytype', 'dateneeded', 'postatus', 'supplier', 'inputvattype',
              'deferredvat', 'creditterm', 'particulars', 'creditterm', 'vat', 'atc', 'currency', 'deliverydate',
              'designatedapprover', 'wtax']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('purchaseorder.add_pomain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('description')
        context['prfmain'] = Prfmain.objects.filter(isdeleted=0, prfstatus='A', status='A',
                                                    totalremainingquantity__gt=0)
        context['secretkey'] = generatekey(self)
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('pk')
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        return context

    def form_valid(self, form):
        # START: save po main
        if Podetailtemp.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0):
            self.object = form.save(commit=False)

            year = str(form.cleaned_data['podate'].year)
            yearQS = Pomain.objects.filter(ponum__startswith=year)

            if yearQS:
                ponumlast = yearQS.latest('ponum')
                latestponum = str(ponumlast)
                print "latest: " + latestponum

                ponum = year
                last = str(int(latestponum[4:]) + 1)
                zero_addon = 6 - len(last)
                for x in range(0, zero_addon):
                    ponum += '0'
                ponum += last

            else:
                ponum = year + '000001'

            print 'ponum: ' + ponum

            self.object.ponum = ponum
            self.object.supplier_code = Supplier.objects.get(pk=self.request.POST['supplier']).code
            self.object.supplier_name = Supplier.objects.get(pk=self.request.POST['supplier']).name
            self.object.enterby = self.request.user
            self.object.modifyby = self.request.user
            self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
            self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
            self.object.fxrate = Currency.objects.get(pk=self.request.POST['currency']).fxrate
            self.object.wtaxrate = Wtax.objects.get(pk=self.request.POST['wtax']).rate
            self.object.save()
            # END: save po main

            # START: transfer po detail temp data to po detail, reflecting changes made in the screen
            detailtemp = Podetailtemp.objects.filter(secretkey=self.request.POST['secretkey'],
                                                     isdeleted=0,
                                                     status='A').order_by('enterdate')

            i = 1
            pomain_totalamount = 0
            for dt in detailtemp:
                if dt.prfdetail is None or int(self.request.POST.getlist('temp_quantity')[i - 1]) <= int(dt.prfdetail.poremainingquantity):
                    detail = Podetail()
                    detail.item_counter = i
                    detail.pomain = Pomain.objects.get(ponum=ponum)
                    detail.invitem = dt.invitem
                    detail.invitem_code = dt.invitem_code
                    detail.invitem_name = dt.invitem_name
                    detail.unitofmeasure = Unitofmeasure.objects.get(pk=self.request.POST.
                                                                     getlist('temp_item_um')[i - 1], isdeleted=0,
                                                                     status='A')
                    detail.invitem_unitofmeasure = Unitofmeasure.objects.get(
                        pk=self.request.POST.getlist('temp_item_um')[i - 1],
                        isdeleted=0,
                        status='A').code
                    detail.quantity = self.request.POST.getlist('temp_quantity')[i - 1]
                    detail.unitcost = self.request.POST.getlist('temp_unitcost')[i - 1]
                    detail.discountrate = self.request.POST.getlist('temp_discountrate')[i - 1] if self.request.POST.getlist('temp_discounttype')[i - 1] == "rate" else 0
                    detail.remarks = self.request.POST.getlist('temp_remarks')[i - 1]
                    detail.status = dt.status
                    detail.enterdate = dt.enterdate
                    detail.modifydate = dt.modifydate
                    detail.postdate = dt.postdate
                    detail.isdeleted = dt.isdeleted
                    detail.branch = Branch.objects.get(pk=self.request.POST.getlist('temp_branch')[i - 1], isdeleted=0,
                                                       status='A')
                    detail.department = Department.objects.get(pk=self.request.POST.getlist('temp_department')[i - 1],
                                                               isdeleted=0)
                    detail.department_code = detail.department.code
                    detail.department_name = detail.department.departmentname
                    detail.enterby = dt.enterby
                    detail.modifyby = dt.modifyby
                    detail.postby = dt.postby
                    detail.vat = Vat.objects.get(pk=self.request.POST['vat'], isdeleted=0, status='A')
                    detail.vatrate = detail.vat.rate
                    detail.currency = dt.currency

                    grossUnitCost = float(detail.unitcost) / (1 + (float(detail.vatrate) / 100))
                    detail.grossamount = grossUnitCost * float(detail.quantity)
                    detail.discountamount = detail.grossamount * float(detail.discountrate) / 100 if self.request.POST.getlist('temp_discounttype')[i - 1] == "rate" else float(self.request.POST.getlist('temp_discountamount')[i - 1])
                    discountedAmount = detail.grossamount - detail.discountamount
                    detail.vatamount = discountedAmount * (float(detail.vatrate) / 100)
                    detail.netamount = discountedAmount + detail.vatamount

                    if detail.vatrate > 0:
                        detail.vatable = discountedAmount
                        detail.vatexempt = 0
                        detail.vatzerorated = 0
                    elif detail.vat.code == "VE":
                        detail.vatable = 0
                        detail.vatexempt = discountedAmount
                        detail.vatzerorated = 0
                    elif detail.vat.code == "ZE":
                        detail.vatable = 0
                        detail.vatexempt = 0
                        detail.vatzerorated = discountedAmount

                    if 'temp_expirationdate' in self.request.POST:
                        if self.request.POST.getlist('temp_expirationdate')[i - 1] != '':
                            detail.expirationdate = self.request.POST.getlist('temp_expirationdate')[i - 1]
                    if 'temp_employee' in self.request.POST:
                        if self.request.POST.getlist('temp_employee')[i - 1] != '':
                            detail.employee = Employee.objects.get(pk=self.request.POST.getlist('temp_employee')[i - 1])
                            detail.employee_code = detail.employee.code
                            detail.employee_name = detail.employee.firstname + ' ' + detail.employee.lastname
                    if 'temp_assetnum' in self.request.POST:
                        if self.request.POST.getlist('temp_assetnum')[i - 1] != '':
                            detail.assetnum = self.request.POST.getlist('temp_assetnum')[i - 1]
                    if 'temp_serialnum' in self.request.POST:
                        if self.request.POST.getlist('temp_serialnum')[i - 1] != '':
                            detail.serialnum = self.request.POST.getlist('temp_serialnum')[i - 1]

                    detail.prfmain = dt.prfmain
                    detail.prfdetail = dt.prfdetail

                    detail.save()
                    # END: transfer po detail temp data to po detail, reflecting changes made in the screen

                    # START: update po-related fields in prf detail
                    if detail.prfdetail is not None:
                        prfd = Prfdetail.objects.get(pk=detail.prfdetail.id)
                        prfd.pototalquantity = int(prfd.pototalquantity) + int(detail.quantity)
                        prfd.poremainingquantity = int(prfd.poremainingquantity) - int(detail.quantity)
                        if prfd.poremainingquantity == 0:
                            prfd.isfullypo = 1
                        prfd.save()
                        # END: update po-related fields in prf detail
                        # START: save in prfpotransaction
                        prfpotrans = Prfpotransaction()
                        prfpotrans.poquantity = detail.quantity
                        prfpotrans.podetail = detail
                        prfpotrans.pomain = detail.pomain
                        prfpotrans.prfdetail = detail.prfdetail
                        prfpotrans.prfmain = detail.prfmain
                        prfpotrans.save()
                        # END: save in prfpotransaction

                    # START: update total fields in po main
                    pomain_totalamount += ((float(detail.unitcost) * float(detail.quantity)) - float(detail.discountamount))
                i += 1

            po_main_aggregates = Podetail.objects.filter(pomain__ponum=ponum).aggregate(Sum('discountamount'),
                                                                                        Sum('grossamount'),
                                                                                        Sum('netamount'),
                                                                                        Sum('vatable'),
                                                                                        Sum('vatamount'),
                                                                                        Sum('vatexempt'),
                                                                                        Sum('vatzerorated'),
                                                                                        Sum('unitcost'),
                                                                                        Sum('quantity'))

            Pomain.objects.filter(ponum=ponum, isdeleted=0, status='A').\
                update(discountamount=po_main_aggregates['discountamount__sum'],
                       grossamount=po_main_aggregates['grossamount__sum'],
                       netamount=po_main_aggregates['netamount__sum'], vatable=po_main_aggregates['vatable__sum'],
                       vatamount=po_main_aggregates['vatamount__sum'], vatexempt=po_main_aggregates['vatexempt__sum'],
                       vatzerorated=po_main_aggregates['vatzerorated__sum'],
                       totalamount=pomain_totalamount,
                       totalquantity=po_main_aggregates['quantity__sum'])
            # END: update total fields in po main

            # START: update po-related fields in prf main
            temp_prfmain = 0
            prfmains = detailtemp.values('prfmain').order_by('prfmain')
            for data in prfmains:
                if data['prfmain'] is not None:
                    if temp_prfmain != data['prfmain']:
                        existingtotalremqty = Prfmain.objects.get(id=data['prfmain']).totalremainingquantity
                        print existingtotalremqty
                        totalpoqty = Podetail.objects.filter(pomain__ponum=ponum, prfmain=data['prfmain']). \
                            aggregate(Sum('quantity'))['quantity__sum']
                        print totalpoqty
                        totalremainingqty = existingtotalremqty - totalpoqty
                        if totalremainingqty > -1:
                            Prfmain.objects.filter(id=data['prfmain']).\
                                update(totalremainingquantity=totalremainingqty)
                    temp_prfmain = data['prfmain']
                    # END: update po-related fields in prf main

            # START: delete po detail temp data
            detailtemp.delete()
            # END: delete po detail temp data

            # START: update po data
            Podata.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0).\
                update(pomain=Pomain.objects.get(ponum=ponum))
            # END: update po data

            # return HttpResponseRedirect('/purchaseorder/' + str(self.object.id) + '/update')
            return HttpResponseRedirect('/purchaseorder/create')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Pomain
    template_name = 'purchaseorder/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('purchaseorder.delete_pomain') or self.object.status == 'O':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/purchaseorder')


@csrf_exempt
def fetchitems(request):
    if request.method == 'POST':
        prfmain = Prfmain.objects.get(pk=request.POST['prfid'],
                                      prfstatus='A',
                                      status='A',
                                      isdeleted=0)

        if Podata.objects.filter(prfmain=prfmain, isdeleted=0).exclude(pomain=None).exists():
            data = {
                'status': 'error',
            }
        else:
            prfdetail = Prfdetail.objects.filter(prfmain=prfmain, status='A', isdeleted=0, isfullypo=0)
            prfdetail_list = []

            for data in prfdetail:
                temp_csmain = data.csmain if data.csmain else None
                temp_detail = data.csdetail if data.csdetail else None
                temp_supplier = data.supplier.pk if data.supplier else None
                prfdetail_list.append([data.id,
                                       data.invitem.id,
                                       data.invitem_code,
                                       data.invitem_name,
                                       data.invitem_unitofmeasure_code,
                                       data.item_counter,
                                       data.quantity,
                                       data.remarks,
                                       data.amount,
                                       data.currency.id,
                                       data.currency.symbol,
                                       data.currency.description,
                                       data.fxrate,
                                       data.grossamount,
                                       data.netamount,
                                       data.vatable,
                                       data.vatamount,
                                       data.vatexempt,
                                       data.vatzerorated,
                                       data.grosscost,
                                       data.department.id,
                                       data.department_code,
                                       data.department_name,
                                       data.uc_grossamount,
                                       data.uc_grosscost,
                                       data.uc_netamount,
                                       data.uc_vatable,
                                       data.uc_vatamount,
                                       data.uc_vatexempt,
                                       data.uc_vatzerorated,
                                       temp_csmain,
                                       data.csnum,
                                       data.csdate,
                                       temp_detail,
                                       temp_supplier,
                                       data.suppliercode,
                                       data.suppliername,
                                       data.estimateddateofdelivery,
                                       data.negocost,
                                       data.uc_cost,
                                       data.poremainingquantity,
                                       ])

            data = {
                'status': 'success',
                'prfdetail': prfdetail_list
            }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def savedetailtemp(request):
    if request.method == 'POST':
        detailtemp = Podetailtemp()
        detailtemp.item_counter = request.POST['itemno']
        detailtemp.branch = Branch.objects.get(pk=request.POST['id_branch'])
        detailtemp.currency = Currency.objects.get(pk=request.POST['id_currency'])
        detailtemp.department = Department.objects.get(pk=request.POST['id_department'])
        if request.POST['id_employee']:
            detailtemp.employee = Employee.objects.get(pk=request.POST['id_employee'])
            detailtemp.employee_code = Employee.objects.get(pk=request.POST['id_employee']).code
            detailtemp.employee_name = Employee.objects.get(pk=request.POST['id_employee']).firstname + ' ' + Employee.\
                objects.get(pk=request.POST['id_employee']).lastname
        detailtemp.enterby = User.objects.get(pk=request.user.id)
        detailtemp.invitem = Inventoryitem.objects.get(pk=request.POST['id_itemid'])
        detailtemp.modifyby = User.objects.get(pk=request.user.id)
        detailtemp.unitofmeasure = Unitofmeasure.objects.get(pk=request.POST['id_um'])
        detailtemp.vat = Vat.objects.get(pk=request.POST['id_vat'])
        detailtemp.invitem_code = Inventoryitem.objects.get(pk=request.POST['id_itemid']).code
        detailtemp.invitem_name = Inventoryitem.objects.get(pk=request.POST['id_itemid']).description
        detailtemp.invitem_unitofmeasure = Unitofmeasure.objects.get(pk=request.POST['id_um']).code
        detailtemp.quantity = request.POST['id_quantity']
        detailtemp.unitcost = request.POST['id_unitcost']
        detailtemp.discountrate = request.POST['id_discountrate']
        detailtemp.remarks = request.POST['id_remarks']
        detailtemp.status = 'A'
        detailtemp.enterdate = datetime.datetime.now()
        detailtemp.modifydate = datetime.datetime.now()
        detailtemp.secretkey = request.POST['secretkey']
        detailtemp.discountamount = request.POST['id_discountamount']
        detailtemp.grossamount = request.POST['id_grossamount']
        detailtemp.netamount = request.POST['id_totalamount']
        detailtemp.vatable = request.POST['id_vatable']
        detailtemp.vatamount = request.POST['id_addvat']
        detailtemp.vatexempt = request.POST['id_vatexempt']
        detailtemp.vatrate = request.POST['id_vatrate']
        detailtemp.vatzerorated = request.POST['id_vatzerorated']
        detailtemp.assetnum = request.POST['id_assetnum']
        if request.POST['id_expirationdate']:
            detailtemp.expirationdate = request.POST['id_expirationdate']
        detailtemp.serialnum = request.POST['id_serialnum']
        detailtemp.department_code = Department.objects.get(pk=request.POST['id_department']).code
        detailtemp.department_name = Department.objects.get(pk=request.POST['id_department']).departmentname
        detailtemp.save()

        data = {
            'status': 'success',
            'podetailid': detailtemp.pk,
            # 'remarks': request.POST['id_remarks'],
            # 'department': Department.objects.get(pk=request.POST['id_department']).code,
            # 'currency': Currency.objects.get(pk=request.POST['id_currency']).symbol,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def saveimporteddetailtemp(request):
    if request.method == 'POST':
        prfmain = Prfmain.objects.get(pk=request.POST['prfmainid'], prfstatus='A', status='A', isdeleted=0)
        prfdata = [prfmain.prfnum]
        print prfdata
        i = 1
        podetail_list = []
        for data in request.POST.getlist('imported_items[]'):
            prfitemdetails = Prfdetail.objects.get(pk=data)
            if prfitemdetails.isdeleted == 0 and prfitemdetails.isfullypo == 0 and \
                prfitemdetails.poremainingquantity > 0 and prfitemdetails.prfmain.prfstatus == 'A' and \
                prfitemdetails.prfmain.isdeleted == 0 and prfitemdetails.prfmain.status == 'A' and \
                    prfitemdetails.prfmain.totalremainingquantity > 0:

                detailtemp = Podetailtemp()
                detailtemp.item_counter = i
                detailtemp.branch = prfitemdetails.prfmain.branch
                detailtemp.currency = prfitemdetails.currency
                detailtemp.department = prfitemdetails.department
                detailtemp.enterby = User.objects.get(pk=request.user.id)
                detailtemp.invitem = prfitemdetails.invitem
                detailtemp.modifyby = User.objects.get(pk=request.user.id)
                detailtemp.unitofmeasure = prfitemdetails.invitem_unitofmeasure
                detailtemp.vat = Vat.objects.get(pk=request.POST['id_vat'])
                detailtemp.invitem_code = prfitemdetails.invitem_code
                detailtemp.invitem_name = prfitemdetails.invitem_name
                detailtemp.invitem_unitofmeasure = prfitemdetails.invitem_unitofmeasure_code
                detailtemp.quantity = prfitemdetails.quantity
                if prfitemdetails.supplier:
                    if int(request.POST['id_supplier']) == int(prfitemdetails.supplier.id):
                        detailtemp.unitcost = prfitemdetails.negocost
                detailtemp.status = 'A'
                detailtemp.enterdate = datetime.datetime.now()
                detailtemp.modifydate = datetime.datetime.now()
                detailtemp.secretkey = request.POST['secretkey']
                detailtemp.vatrate = Vat.objects.get(pk=request.POST['id_vat']).rate
                detailtemp.department_code = prfitemdetails.department_code
                detailtemp.department_name = prfitemdetails.department_name
                detailtemp.prfmain = prfitemdetails.prfmain
                detailtemp.prfdetail = prfitemdetails
                detailtemp.save()
                i += 1
                podetail_list.append([detailtemp.pk,
                                      detailtemp.invitem.inventoryitemclass.inventoryitemtype.code,
                                      detailtemp.invitem.id,
                                      detailtemp.invitem_code,
                                      detailtemp.invitem_name,
                                      detailtemp.prfmain.prfnum,
                                      detailtemp.invitem.unitofmeasure.id,
                                      detailtemp.branch.id,
                                      detailtemp.department.id,
                                      detailtemp.unitcost,
                                      detailtemp.vatrate,
                                      detailtemp.vat.code,
                                      detailtemp.quantity,
                                      detailtemp.prfmain.id,
                                      detailtemp.prfdetail.id,
                                      prfitemdetails.poremainingquantity,
                                      ])

        # store temppodata
        if not Podata.objects.filter(prfmain=prfmain, secretkey=request.POST['secretkey'], pomain=None).exists():
            detail = Podata()
            detail.secretkey = request.POST['secretkey']
            detail.prfmain = prfmain
            detail.save()

        data = {
            'status': 'success',
            'podetail': podetail_list,
            'prfdata': prfdata,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def deleteimportedprf(request):
    if request.method == 'POST':
        podetailfordeletion = Podetailtemp.objects.filter(secretkey=request.POST['secretkey'],
                                                          prfmain__prfnum=request.POST['prfnum'],
                                                          pomain=None)      # applicable for CREATE page
        for data in podetailfordeletion:
            data.delete()

        Podata.objects.get(secretkey=request.POST['secretkey'], prfmain__prfnum=request.POST['prfnum'],
                           pomain=None).delete()                            # applicable for CREATE page

        data = {
            'status': 'success',
            'prfmainid': Prfmain.objects.get(prfnum=request.POST['prfnum']).id,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def deletedetailtemp(request):
    podatadeleted = 'false'
    prfnum = None
    if request.method == 'POST':
        try:
            detailtemp = Podetailtemp.objects.get(pk=request.POST['podetailid'],
                                                  secretkey=request.POST['secretkey'],
                                                  pomain=None)
            detailtemp.delete()

            if request.POST['prfmainid'] != '':
                if not Podetailtemp.objects.filter(secretkey=request.POST['secretkey'],
                                                   prfmain=request.POST['prfmainid'], pomain=None).exists():
                    Podata.objects.get(secretkey=request.POST['secretkey'], prfmain=request.POST['prfmainid'],
                                       pomain=None).delete()
                    podatadeleted = 'true'
                    prfnum = Prfmain.objects.get(id=request.POST['prfmainid']).prfnum

        except Podetailtemp.DoesNotExist:
            print "temp detail has pomain"
            detailtemp = Podetailtemp.objects.get(pk=request.POST['podetailid'],
                                                  pomain__ponum=request.POST['ponum'])
            detailtemp.isdeleted = 1
            detailtemp.save()

        data = {
            'status': 'success',
            'podatadeleted': podatadeleted,
            'prfnum': prfnum,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


def paginate(request, command, current, limit, search):
    current = int(current)
    limit = int(limit)

    if command == "search" and search != "null":
        search_not_slug = search.replace('-', ' ')
        pomain = Pomain.objects.all().filter(Q(ponum__icontains=search) |
                                             Q(podate__icontains=search) |
                                             Q(particulars__icontains=search) |
                                             Q(postatus__icontains=search) |
                                             Q(ponum__icontains=search_not_slug) |
                                             Q(podate__icontains=search_not_slug) |
                                             Q(particulars__icontains=search_not_slug) |
                                             Q(postatus__icontains=search_not_slug))\
                                            .filter(isdeleted=0).order_by('-enterdate')
    else:
        pomain = Pomain.objects.all().filter(isdeleted=0).order_by('-enterdate')[current:current+limit]

    json_models = serializers.serialize("json", pomain)
    print json_models
    return HttpResponse(json_models, content_type="application/javascript")


