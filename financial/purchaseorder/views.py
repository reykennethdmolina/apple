from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core import serializers
from .models import Pomain, Podetail, Podetailtemp, Podata
from purchaserequisitionform.models import Prfmain
from supplier.models import Supplier
from ataxcode.models import Ataxcode
from inputvat.models import Inputvat
from vat.models import Vat
from creditterm.models import Creditterm
from inventoryitem.models import Inventoryitem
from branch.models import Branch
from currency.models import Currency
from department.models import Department
from unitofmeasure.models import Unitofmeasure
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
    template_name = 'purchaseorder/create2.html'
    fields = ['podate', 'potype', 'refnum', 'urgencytype', 'dateneeded', 'supplier', 'ataxcode', 'inputvat',
              'creditterm', 'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('purchaseorder.add_pomain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('pk')
        context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('description')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('code')
        context['prfmain'] = Prfmain.objects.filter(isdeleted=0, prfstatus='A', status='A')
        return context

    def form_valid(self, form):
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
            self.object.vat = Vat.objects.get(pk=Supplier.objects.get(pk=self.request.POST['supplier']).vat.pk)
            self.object.vatrate = Vat.objects.get(pk=Supplier.objects.get(pk=self.request.POST['supplier']).vat.pk).rate
            self.object.save()

            detailtemp = Podetailtemp.objects.filter(secretkey=self.request.POST['secretkey'],
                                                     isdeleted=0,
                                                     status='A').order_by('enterdate')

            i = 1
            for dt in detailtemp:
                detail = Podetail()
                detail.item_counter = i
                detail.pomain = Pomain.objects.get(ponum=ponum)
                detail.invitem = dt.invitem
                detail.invitem_code = dt.invitem_code
                detail.invitem_name = dt.invitem_name
                detail.unitofmeasure = Unitofmeasure.objects.get(pk=self.request.POST.getlist('temp_item_um')[i - 1],
                                                                 isdeleted=0,
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
                detail.branch = dt.branch
                detail.department = dt.department
                detail.enterby = dt.enterby
                detail.modifyby = dt.modifyby
                detail.postby = dt.postby
                detail.vat = dt.vat
                detail.vatrate = dt.vatrate
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

                detail.save()
                dt.delete()
                i += 1

            po_main_aggregates = Podetail.objects.filter(pomain__ponum=ponum).aggregate(Sum('discountamount'),
                                                                                        Sum('grossamount'),
                                                                                        Sum('netamount'),
                                                                                        Sum('vatable'),
                                                                                        Sum('vatamount'),
                                                                                        Sum('vatexempt'),
                                                                                        Sum('vatzerorated'))

            Pomain.objects.filter(ponum=ponum, isdeleted=0, status='A').\
                update(discountamount=po_main_aggregates['discountamount__sum'],
                       grossamount=po_main_aggregates['grossamount__sum'],
                       netamount=po_main_aggregates['netamount__sum'], vatable=po_main_aggregates['vatable__sum'],
                       vatamount=po_main_aggregates['vatamount__sum'], vatexempt=po_main_aggregates['vatexempt__sum'],
                       vatzerorated=po_main_aggregates['vatzerorated__sum'])

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
def savedetailtemp(request):

    if request.method == 'POST':
        print request.POST
        detailtemp = Podetailtemp()
        detailtemp.item_counter = request.POST['itemno']
        detailtemp.invitem_code = Inventoryitem.objects.get(pk=request.POST['id_itemid']).code
        detailtemp.invitem_name = Inventoryitem.objects.get(pk=request.POST['id_itemid']).description
        detailtemp.invitem_unitofmeasure = Unitofmeasure.objects.get(pk=request.POST['id_um']).code
        detailtemp.unitofmeasure = Unitofmeasure.objects.get(pk=request.POST['id_um'])
        detailtemp.quantity = request.POST['id_quantity']
        detailtemp.unitcost = request.POST['id_unitcost']
        detailtemp.discountrate = request.POST['id_discountrate']
        detailtemp.remarks = request.POST['id_remarks']
        detailtemp.status = 'A'
        detailtemp.enterdate = datetime.datetime.now()
        detailtemp.modifydate = datetime.datetime.now()
        detailtemp.secretkey = request.POST['secretkey']
        detailtemp.branch = Branch.objects.get(pk=5)
        detailtemp.department = Department.objects.get(pk=request.POST['id_department'])
        detailtemp.enterby = User.objects.get(pk=request.user.id)
        detailtemp.invitem = Inventoryitem.objects.get(pk=request.POST['id_itemid'])
        detailtemp.modifyby = User.objects.get(pk=request.user.id)
        detailtemp.discountamount = request.POST['id_discountamount']
        detailtemp.grossamount = request.POST['id_grossamount']
        detailtemp.netamount = request.POST['id_totalamount']
        detailtemp.vat = Vat.objects.get(pk=request.POST['id_vat'])
        detailtemp.vatable = request.POST['id_vatable']
        detailtemp.vatamount = request.POST['id_addvat']
        detailtemp.vatexempt = request.POST['id_vatexempt']
        detailtemp.vatrate = request.POST['id_vatrate']
        detailtemp.vatzerorated = request.POST['id_vatzerorated']
        detailtemp.currency = Currency.objects.get(pk=request.POST['id_currency'])
        detailtemp.save()

        data = {
            'status': 'success',
            'itemno': request.POST['itemno'],
            'remarks': request.POST['id_remarks'],
            'department': Department.objects.get(pk=request.POST['id_department']).code,
            'currency': Currency.objects.get(pk=request.POST['id_currency']).symbol,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def deletedetailtemp(request):

    if request.method == 'POST':
        try:
            detailtemp = Podetailtemp.objects.get(item_counter=request.POST['itemno'],
                                                  secretkey=request.POST['secretkey'],
                                                  pomain=None)
            detailtemp.delete()
        except Podetailtemp.DoesNotExist:
            print "temp detail has pomain"
            detailtemp = Podetailtemp.objects.get(item_counter=request.POST['itemno'],
                                                  pomain__ponum=request.POST['ponum'])
            detailtemp.isdeleted = 1
            detailtemp.save()

        data = {
            'status': 'success',
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


@csrf_exempt
def importsuppliers(request):
    if request.method == 'POST':
        # get selected prfmain data
        prfmain = Prfmain.objects.get(prfnum=request.POST['prfnum'],
                                      prfstatus="A",
                                      status="A",
                                      isdeleted=0)
        prfdata = [prfmain.prfnum]

        itemsuppliers = Prfmain.objects.raw('SELECT a.id, a.prfnum, b.csmain_id, d.supplier_id, d.suppliercode, '
                                            'd.suppliername FROM prfmain a JOIN csdata b ON b.prfmain_id = a.id '
                                            'JOIN csmain c ON b.csmain_id = c.id JOIN csdetail d ON c.id = d.csmain_id '
                                            'WHERE a.prfnum = "' + request.POST['prfnum'] + '" '
                                            'AND b.csmain_id IS NOT NULL '
                                            'AND d.csstatus = 1 AND a.isdeleted = 0 AND a.status = "A" '
                                            'AND b.isdeleted = 0 AND c.isdeleted = 0 AND c.status = "A" '
                                            'AND d.isdeleted = 0 AND d.status = "A"')
        prfsupplier_list = []
        if itemsuppliers:
            for data in itemsuppliers:
                prfsupplier_list.append([data.id,
                                         data.prfnum,
                                         data.csmain_id,
                                         data.supplier_id,
                                         data.suppliercode,
                                         data.suppliername])

        data = {
            'status': 'success',
            'prfdata': prfdata,
            'prfsuppliers': prfsupplier_list,
            # 'prfdetail': prfdetail_list,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def importitems(request):
    if request.method == 'POST':
        prfmain = Prfmain.objects.get(prfnum=request.POST['prfnum'],
                                      prfstatus="A",
                                      status="A",
                                      isdeleted=0)

        if Podata.objects.filter(prfmain=prfmain).exists():
            data = {
                'status': 'error',
            }
        else:
            canvassedprfitems = Prfmain.objects.raw('SELECT a.id AS prfmain, a.prfnum, a.branch_id, a.department_id, b.id AS prfdetail, b.item_counter, '
                                                    'b.invitem_id, b.invitem_code, b.invitem_name, b.invitem_unitofmeasure_code, '
                                                    'b.invitem_unitofmeasure_id, b.remarks, c.id, c.csmain_id, d.id, e.id, '
                                                    'e.supplier_id, e.suppliername, b.quantity, e.negocost, '
                                                    'e.csstatus, e.isdeleted, e.status, e.grossamount, e.netamount, e.vat_id, '
                                                    'e.vatable, e.vatamount, e.vatexempt, e.vatrate, e.vatzerorated, b.currency_id '
                                                    'FROM prfmain a '
                                                    'LEFT JOIN prfdetail b ON a.id = b.prfmain_id '
                                                    'LEFT JOIN csdata c ON a.id = c.prfmain_id '
                                                    'LEFT JOIN csmain d ON c.csmain_id = d.id '
                                                    'LEFT JOIN csdetail e '
                                                    'ON d.id = e.csmain_id AND b.invitem_id = e.invitem_id '
                                                    'WHERE a.prfnum = "' + request.POST[
                                                        'prfnum']
                                                    + '" AND a.prfstatus = "A" AND a.status = "A" AND a.isdeleted = 0 '
                                                      'AND b.status = "A" AND b.isdeleted = 0 AND d.isdeleted = 0 '
                                                      'AND d.status = "A" '
                                                      'ORDER BY b.item_counter')

            supplier_vat = Supplier.objects.get(pk=request.POST['supplier'], isdeleted=0, status='A').vat
            prfitem_list = []
            if canvassedprfitems:
                for data in canvassedprfitems:
                    if data.csstatus == 1 and data.isdeleted == 0 and data.status == 'A':
                        if request.POST['supplier'] != '':
                            if str(data.supplier_id) == request.POST['supplier']:
                                prfitem_list.append([data.prfnum,
                                                     data.prfdetail,
                                                     data.item_counter,
                                                     data.invitem_id,
                                                     data.invitem_code,
                                                     data.invitem_name,
                                                     data.invitem_unitofmeasure_code,
                                                     data.quantity,
                                                     data.negocost,
                                                     data.remarks,
                                                     data.branch_id,
                                                     data.department_id,
                                                     data.grossamount,
                                                     data.netamount,
                                                     data.vat_id,
                                                     data.vatable,
                                                     data.vatamount,
                                                     data.vatexempt,
                                                     data.vatrate,
                                                     data.vatzerorated,
                                                     data.currency_id,
                                                     data.invitem_unitofmeasure_id,
                                                     data.suppliername])
                    if data.suppliername is None:
                        prfitem_list.append([data.prfnum,
                                             data.prfdetail,
                                             data.item_counter,
                                             data.invitem_id,
                                             data.invitem_code,
                                             data.invitem_name,
                                             data.invitem_unitofmeasure_code,
                                             data.quantity,
                                             data.negocost,
                                             data.remarks,
                                             data.branch_id,
                                             data.department_id,
                                             data.grossamount,
                                             data.netamount,
                                             data.vat_id,
                                             data.vatable,
                                             data.vatamount,
                                             data.vatexempt,
                                             data.vatrate,
                                             data.vatzerorated,
                                             data.currency_id,
                                             data.invitem_unitofmeasure_id,
                                             data.suppliername])

            if prfitem_list:
                # save in podata as temp data (secretkey and prfmain)
                podatatemp = Podata()
                podatatemp.secretkey = request.POST['secretkey']
                podatatemp.prfmain = prfmain
                podatatemp.save()

            i = 1
            # save in podetailtemp based on prfitem_list
            for data in prfitem_list:
                print i
                podetailtemp = Podetailtemp()
                podetailtemp.item_counter = data[2]
                podetailtemp.invitem_code = data[4]
                podetailtemp.invitem_name = data[5]
                podetailtemp.invitem_unitofmeasure = data[6]
                podetailtemp.quantity = data[7]                            # from prfdetail, won't change even if quantity is modified in CS
                unitcost = data[8] if data[8] is not None else 0.00
                podetailtemp.unitcost = unitcost                           # from csdetail
                podetailtemp.remarks = data[9]
                podetailtemp.secretkey = request.POST['secretkey']
                podetailtemp.branch = Branch.objects.get(pk=data[10], isdeleted=0, status='A')
                podetailtemp.department = Department.objects.get(pk=data[11], isdeleted=0)
                podetailtemp.enterby = request.user
                podetailtemp.invitem = Inventoryitem.objects.get(pk=data[3], isdeleted=0, status='A')
                podetailtemp.modifyby = request.user
                podetailtemp.vat = supplier_vat
                podetailtemp.vatrate = supplier_vat.rate
                grossamount = float(data[7]) * (float(unitcost) / (1 + (float(supplier_vat.rate)/100)))
                podetailtemp.grossamount = grossamount
                podetailtemp.vatable = grossamount if float(supplier_vat.rate) > 0 else 0.00
                podetailtemp.vatexempt = grossamount if supplier_vat.code == 'VE' else 0.00
                podetailtemp.vatzerorated = grossamount if supplier_vat.code == 'ZE' else 0.00
                podetailtemp.vatamount = grossamount * (float(supplier_vat.rate)/100)
                podetailtemp.netamount = grossamount + (grossamount * (float(supplier_vat.rate)/100))
                podetailtemp.currency = Currency.objects.get(pk=data[20], isdeleted=0, status='A') if data[20] is not None else None
                podetailtemp.unitofmeasure = Unitofmeasure.objects.get(pk=data[21], isdeleted=0, status='A')
                podetailtemp.save()
                i += 1

            data = {
                'status': 'success',
                'prfitems': prfitem_list
            }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


