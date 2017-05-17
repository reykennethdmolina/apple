from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from . models import Csmain, Csdata, Csdetailtemp, Csdetail
from purchaserequisitionform.models import Prfmain, Prfdetail
from inventoryitem.models import Inventoryitem
from supplier.models import Supplier
from industry.models import Industry
from suppliertype.models import Suppliertype
from vat.models import Vat
from currency.models import Currency
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from acctentry.views import generatekey
from easy_pdf.views import PDFTemplateView
from django.core import serializers
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Csmain
    template_name = 'canvasssheet/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Csmain.objects.all().filter(isdeleted=0).order_by('enterdate')[0:10]

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['listcount'] = Csmain.objects.filter(isdeleted=0).count()
        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Csmain
    template_name = 'canvasssheet/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['csdetail'] = Csdetail.objects.filter(isdeleted=0, csmain=self.kwargs['pk'], csstatus=1).order_by('item_counter')
        context['csdata'] = Csdata.objects.filter(isdeleted=0, csmain=self.kwargs['pk'])
        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Csmain
    template_name = 'canvasssheet/create.html'
    fields = ['csdate', 'cstype', 'particulars', 'designatedapprover']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['prfmain'] = Prfmain.objects.filter(isdeleted=0, prfstatus='A', status='A')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('inventoryitemclass__inventoryitemtype__code', 'description')
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('name')
        context['suppliertype'] = Suppliertype.objects.filter(isdeleted=0).order_by('description')
        context['industry'] = Industry.objects.filter(isdeleted=0).order_by('name')

        return context

    def form_valid(self, form):
        if Csdetailtemp.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0):
            self.object = form.save(commit=False)

            try:
                csnumlast = Csmain.objects.latest('csnum')
                latestcsnum = str(csnumlast)
                if latestcsnum[0:4] == str(datetime.datetime.now().year):
                    csnum = str(datetime.datetime.now().year)
                    last = str(int(latestcsnum[4:])+1)
                    zero_addon = 6 - len(last)
                    for x in range(0, zero_addon):
                        csnum += '0'
                    csnum += last
                else:
                    csnum = str(datetime.datetime.now().year) + '000001'
            except Csmain.DoesNotExist:
                csnum = str(datetime.datetime.now().year) + '000001'

            self.object.csnum = csnum

            self.object.enterby = self.request.user
            self.object.modifyby = self.request.user
            self.object.save()

            csmain = Csmain.objects.get(csnum=csnum)

            # update csdata
            # apply itemdetail key
            # apply itemdetail key
            # apply itemdetail key
            # apply itemdetail key
            Csdata.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0).update(csmain=csmain)


            importTemptodetail(self.request.POST['secretkey'], csmain)
            updateCsmainvat(csnum)

            # return HttpResponseRedirect('/canvasssheet/' + str(self.object.id) + '/update/')
            return HttpResponseRedirect('/canvasssheet/' + str(self.object.id) + '/')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Csmain
    template_name = 'canvasssheet/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('canvasssheet.delete_csmain') or self.object.status == 'O':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/canvasssheet')


@csrf_exempt
def updateCsmainvat(csnum):
    csmain_aggregates = Csdetail.objects.filter(csmain__csnum=csnum, csstatus=1).aggregate(Sum('grossamount'),
                                                                               Sum('netamount'),
                                                                               Sum('quantity'),
                                                                               Sum('vatable'),
                                                                               Sum('vatamount'),
                                                                               Sum('vatexempt'),
                                                                               Sum('vatzerorated'))

    Csmain.objects.filter(csnum=csnum, isdeleted=0, status='A').\
                  update(grossamount=csmain_aggregates['grossamount__sum'],
                         netamount=csmain_aggregates['netamount__sum'],
                         quantity=csmain_aggregates['quantity__sum'],
                         vatable=csmain_aggregates['vatable__sum'],
                         vatamount=csmain_aggregates['vatamount__sum'],
                         vatexempt=csmain_aggregates['vatexempt__sum'],
                         vatzerorated=csmain_aggregates['vatzerorated__sum'])


@csrf_exempt
def updateCsdetailtemp(request):
    if request.method == 'POST':

        i = 0
        # assign quantity
        for data in request.POST.getlist('arr_quantity_item[]'):
            Csdetailtemp.objects.filter(secretkey=request.POST['secretkey'],
                                        itemdetailkey=request.POST.getlist('arr_item_detail_key[]')[i],
                                        invitem=data,
                                        isdeleted=0,
                                        status='A').update(quantity=request.POST.getlist('arr_item_quantity_input[]')[i])
            i += 1

        i = 0

        # assign checked supplier
        for data in request.POST.getlist('arr_checked_supplier[]'):
            # filter if supplier is changed
            # filter if supplier is changed
            # filter if supplier is changed
            # filter if supplier is changed
            # filter if supplier is changed
            csdetail = Csdetailtemp.objects.filter(secretkey=request.POST['secretkey'],
                                        invitem=request.POST.getlist('arr_checked_supplier_item[]')[i],
                                        isdeleted=0,
                                        status='A')
            csdetail.update(csstatus=0)

            if csdetail.count() > 1:
                csdetail.filter(supplier=data).update(csstatus=1)
            else:
                csdetail.update(csstatus=1, supplier=data)

            i += 1

        i = 0
        # assign nego cost per supplier item
        for data in request.POST.getlist('arr_item_cost_supplier[]'):
            detail = Csdetailtemp.objects.filter(secretkey=request.POST['secretkey'],
                                        invitem=request.POST.getlist('arr_item_cost_item[]')[i],
                                        itemdetailkey=request.POST.getlist('arr_item_each_detail_key[]')[i],
                                        supplier=data,
                                        isdeleted=0,
                                        status='A')


            detail.update(negocost=request.POST.getlist('arr_item_cost[]')[i])

            detailget = Csdetailtemp.objects.get(secretkey=request.POST['secretkey'],
                                        invitem=request.POST.getlist('arr_item_cost_item[]')[i],
                                        itemdetailkey=request.POST.getlist('arr_item_each_detail_key[]')[i],
                                        supplier=data,
                                        isdeleted=0,
                                        status='A')
            # compute vat etc
            # nego cost
            item_total_amount = float(detailget.quantity) * float(detailget.negocost)
            item_vat_rate = detailget.vatrate
            item_gross_amount = item_total_amount
            item_vatcode = Vat.objects.get(pk=detailget.vat.id, status='A', isdeleted=0).code
            item_vatable = 0
            item_vatexempt = 0
            item_vatzero = 0

            if item_vat_rate > 0:
                item_gross_amount = float(item_total_amount)/(1+(float(item_vat_rate)/100))
                item_vatable = item_gross_amount
            else:
                if item_vatcode == 'VE':
                    item_vatexempt = item_gross_amount

                elif item_vatcode == 'ZE':
                    item_vatzero = item_gross_amount

            item_addvat = float(item_total_amount) - float(item_gross_amount)

            # unit cost
            uc_item_total_amount = float(detailget.quantity) * float(detailget.unitcost)
            uc_item_vat_rate = detailget.vatrate
            uc_item_gross_amount = uc_item_total_amount
            uc_item_vatcode = Vat.objects.get(pk=detailget.vat.id, status='A', isdeleted=0).code
            uc_item_vatable = 0
            uc_item_vatexempt = 0
            uc_item_vatzero = 0

            if uc_item_vat_rate > 0:
                uc_item_gross_amount = float(uc_item_total_amount)/(1+(float(uc_item_vat_rate)/100))
                uc_item_vatable = item_gross_amount
            else:
                if uc_item_vatcode == 'VE':
                    uc_item_vatexempt = uc_item_gross_amount

                elif item_vatcode == 'ZE':
                    uc_item_vatzero = item_gross_amount

            uc_item_addvat = float(uc_item_total_amount) - float(uc_item_gross_amount)

            # update prfdetail
            csdata = Csdata.objects.filter(secretkey=request.POST['secretkey'], isdeleted=0)

            detailget_checked = Csdetailtemp.objects.filter(secretkey=request.POST['secretkey'],
                                        invitem=request.POST.getlist('arr_item_cost_item[]')[i],
                                        itemdetailkey=request.POST.getlist('arr_item_each_detail_key[]')[i],
                                        supplier=data,
                                        csstatus=1,
                                        isdeleted=0,
                                        status='A')

            if detailget_checked.exists():
                for data in csdata:

                    prfdetail = Prfdetail.objects.filter(prfmain=data.prfmain,
                                             status='A',
                                             isdeleted=0,
                                             invitem=request.POST.getlist('arr_item_cost_item[]')[i])

                    for data2 in prfdetail:
                        prfdetail_specific = Prfdetail.objects.filter(pk=data2.id)
                        prfdetail_get = Prfdetail.objects.get(pk=data2.id)
                        item_total_amount = float(prfdetail_get.quantity) * float(detailget.negocost)
                        item_vat_rate = detailget.vatrate
                        item_gross_amount = item_total_amount
                        item_vatcode = Vat.objects.get(pk=detailget.vat.id, status='A', isdeleted=0).code
                        item_vatable = 0
                        item_vatexempt = 0
                        item_vatzero = 0

                        if item_vat_rate > 0:
                            item_gross_amount = float(item_total_amount)/(1+(float(item_vat_rate)/100))
                            item_vatable = item_gross_amount
                        else:
                            if item_vatcode == 'VE':
                                item_vatexempt = item_gross_amount

                            elif item_vatcode == 'ZE':
                                item_vatzero = item_gross_amount

                        uc_item_addvat = float(uc_item_total_amount) - float(uc_item_gross_amount)

                        prfdetail_specific.update(cost=detailget.negocost,
                                                  netamount=item_total_amount,
                                                  vatable=item_vatable,
                                                  vatexempt=item_vatexempt,
                                                  vatzerorated=item_vatzero,
                                                  vatamount=item_addvat,
                                                  grossamount=item_gross_amount,
                                                  amount=item_total_amount)

            detail.update(netamount=item_total_amount,
                          vatable=item_vatable,
                          vatexempt=item_vatexempt,
                          vatzerorated=item_vatzero,
                          vatamount=item_addvat,
                          grossamount=item_gross_amount,
                          uc_netamount=uc_item_total_amount,
                          uc_vatable=uc_item_vatable,
                          uc_vatexempt=uc_item_vatexempt,
                          uc_vatzerorated=uc_item_vatzero,
                          uc_vatamount=uc_item_addvat,
                          uc_grossamount=uc_item_gross_amount)

            i += 1

        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def importTemptodetail(secretkey, csmain):
    csdetailtemp = Csdetailtemp.objects.filter(secretkey=secretkey, isdeleted=0, status='A').order_by('id')

    i = 1
    for data in csdetailtemp:
        csdetail = Csdetail()
        csdetail.item_counter = i
        csdetail.invitem_code = data.invitem_code
        csdetail.invitem_name = data.invitem_name
        csdetail.suppliercode = data.suppliercode
        csdetail.suppliername = data.suppliername
        csdetail.vatrate = data.vatrate
        csdetail.unitcost = data.unitcost
        csdetail.negocost = data.negocost
        csdetail.csstatus = data.csstatus
        csdetail.status = data.status
        csdetail.enterby = data.enterby
        csdetail.enterdate = data.enterdate
        csdetail.modifyby = data.modifyby
        csdetail.modifydate = data.modifydate
        csdetail.postby = data.postby
        csdetail.postdate = data.postdate
        csdetail.isdeleted = data.isdeleted
        csdetail.vatable = data.vatable
        csdetail.vatexempt = data.vatexempt
        csdetail.vatzerorated = data.vatzerorated
        csdetail.grossamount = data.grossamount
        csdetail.vatamount = data.vatamount
        csdetail.netamount = data.netamount
        csdetail.uc_vatable = data.uc_vatable
        csdetail.uc_vatexempt = data.uc_vatexempt
        csdetail.uc_vatzerorated = data.uc_vatzerorated
        csdetail.uc_grossamount = data.uc_grossamount
        csdetail.uc_vatamount = data.uc_vatamount
        csdetail.uc_netamount = data.uc_netamount
        csdetail.csmain = csmain
        csdetail.currency = data.currency
        csdetail.invitem = data.invitem
        csdetail.supplier = data.supplier
        csdetail.vat = data.vat
        csdetail.quantity = data.quantity
        csdetail.save()
        i += 1

    csdetailtemp.delete()


@csrf_exempt
def getSupplier(request):

    if request.method == 'POST':
        supplier = Supplier.objects.get(pk=request.POST['supplier'], isdeleted=0, status='A')
        item = Inventoryitem.objects.get(code=request.POST['item'], status='A', isdeleted=0)

        # check first if item supplier is first before creating new itemdetailkey

        detail = Csdetailtemp()
        detail.invitem = Inventoryitem.objects.get(pk=item.id)
        detail.invitem_code = item.code
        detail.invitem_name = item.description
        detail.quantity = 0
        detail.item_counter = 0
        detail.supplier = Supplier.objects.get(pk=supplier.id)
        detail.suppliercode = supplier.code
        detail.suppliername = supplier.name
        detail.vatrate = supplier.vat.rate
        detail.unitcost = 0
        detail.negocost = 0
        detail.secretkey = request.POST['secretkey']
        detail.csstatus = request.POST['csstatus']
        detail.status = 'A'
        detail.enterdate = datetime.datetime.now()
        detail.modifydate = datetime.datetime.now()
        detail.vat = Vat.objects.get(pk=supplier.vat.id, isdeleted=0)
        detail.vatable = 0
        detail.vatexempt = 0
        detail.vatzerorated = 0
        detail.grossamount = 0
        detail.vatamount = 0
        detail.netamount = 0
        detail.currency = Currency.objects.get(isdeleted=0, status='A', symbol='PHP')
        detail.enterby = request.user
        detail.modifyby = request.user
        detail.isdeleted = 0
        detail.itemdetailkey = request.POST['itemdetailkey']
        detail.save()

        data = {
            'success': 'success',
            'supplierid': supplier.id,
            'suppliername': supplier.name,
            # 'supplier': supplier_list,
        }

    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def importItemsManual(request):
    if request.method == 'POST':
        item = Inventoryitem.objects.get(pk=request.POST['inv_id'], status='A', isdeleted=0)

        itemsupplier_list = []
        itemdetail_key = generatekey(1)

        # query supplier
        itemsupplier = Inventoryitem.objects\
            .raw('SELECT b.id, i.id AS inv_id, i.code, i.description, b.price, b.processingdate, b.datetransaction, '
                 's.id AS supplier_id, s.code AS supplier_code, s.name AS supplier_name, '
                 'v.id AS vat_id, v.code AS vat_code, v.rate AS vat_rate '
                 'FROM (SELECT IF(@prev != a.supplier_id, @rownum := 1, @rownum := @rownum + 1) AS rownumber, '
                        '@prev := a.supplier_id, a.* '
                        'FROM (SELECT * FROM cshistory ch, (SELECT @rownum := 0, @prev := "") sq '
                        'WHERE invitem_id = ' + str(item.id) + ' '
                        'ORDER BY supplier_id, datetransaction DESC, price) a) b '
                 'LEFT JOIN inventoryitem i ON i.id = b.invitem_id '
                 'LEFT JOIN supplier s ON s.id = b.supplier_id '
                 'LEFT JOIN vat v ON v.id = s.vat_id '
                 'WHERE rownumber = 1 '
                 'ORDER BY price '
                 'LIMIT 3')

        i = 1

        # get supplier
        for data in itemsupplier:
            itemsupplier_list.append([data.code,
                                      data.description,
                                      data.price,
                                      data.processingdate,
                                      data.datetransaction,
                                      data.supplier_name,
                                      data.vat_id,
                                      data.vat_rate,
                                      data.vat_code,
                                      data.inv_id,
                                      data.supplier_id,
                                      ])

            # store temp with supplier
            detail = Csdetailtemp()
            detail.invitem = Inventoryitem.objects.get(pk=data.inv_id)
            detail.invitem_code = data.code
            detail.invitem_name = data.description
            detail.quantity = 0
            detail.item_counter = i
            detail.supplier = Supplier.objects.get(pk=data.supplier_id)
            detail.suppliercode = data.supplier_code
            detail.suppliername = data.supplier_name
            detail.vatrate = data.vat_rate
            detail.unitcost = data.price
            detail.negocost = data.price
            detail.secretkey = request.POST['secretkey']
            detail.csstatus = 1 if i == 1 else 0
            detail.status = 'A'
            detail.enterdate = datetime.datetime.now()
            detail.modifydate = datetime.datetime.now()
            detail.vat = Vat.objects.get(pk=data.vat_id)
            detail.vatable = 0
            detail.vatexempt = 0
            detail.vatzerorated = 0
            detail.grossamount = 0
            detail.vatamount = 0
            detail.netamount = 0
            detail.currency = Currency.objects.get(isdeleted=0, status='A', symbol='PHP')
            detail.enterby = request.user
            detail.modifyby = request.user
            detail.isdeleted = 0
            detail.itemdetailkey = itemdetail_key
            detail.save()

            i += 1

        # store temp with default supplier
        # supplierdetail = Supplier.objects.filter(isdeleted=0).order_by('name').first()
        #
        # detail = Csdetailtemp()
        # detail.invitem = Inventoryitem.objects.get(pk=item.id)
        # detail.invitem_code = item.code
        # detail.invitem_name = item.description
        # detail.quantity = 0
        # detail.item_counter = i
        # detail.supplier = Supplier.objects.get(pk=supplierdetail.id)
        # detail.suppliercode = supplierdetail.code
        # detail.suppliername = supplierdetail.name
        # detail.vatrate = supplierdetail.vat.rate
        # detail.unitcost = 0
        # detail.negocost = 0
        # detail.secretkey = request.POST['secretkey']
        # detail.csstatus = 1
        # detail.status = 'A'
        # detail.enterdate = datetime.datetime.now()
        # detail.modifydate = datetime.datetime.now()
        # detail.vat = Vat.objects.get(pk=supplierdetail.vat.id, isdeleted=0)
        # detail.vatable = 0
        # detail.vatexempt = 0
        # detail.vatzerorated = 0
        # detail.grossamount = 0
        # detail.vatamount = 0
        # detail.netamount = 0
        # detail.currency = Currency.objects.get(isdeleted=0, status='A', symbol='PHP')
        # detail.enterby = request.user
        # detail.modifyby = request.user
        # detail.isdeleted = 0
        # detail.save()

        data = {
                'status': 'success',
                'item': item.id,
                'item_code': item.code,
                'item_description': item.description,
                'item_supplier': itemsupplier_list,
                'itemdetail_key': itemdetail_key,
        }

    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def importItems(request):
    # print generatekey(1)
    # front end - hover imported prf to show details
    # front end - item supplier manual add(manual add of extra supplier)
    # back - prf should only be cs once unless cancelled\
    # back - prf item without a supplier data
    # back - prf item without cshistory

    if request.method == 'POST':
        # get selected prfmain data
        prfmain = Prfmain.objects.get(prfnum=request.POST['prfnum'],
                                      prfstatus="A",
                                      status="A",
                                      isdeleted=0)

        # get prfmain prfdetail data
        prfdetail = Prfdetail.objects.filter(prfmain=prfmain.id,
                                             status="A",
                                             isdeleted=0).order_by('item_counter')

        prfitemsupplier_list = []
        prfitemcshistory_list = []
        itemdetailkey_list = []

        # get prf items suggested supplier
        for data in prfdetail:
            itemdetail_key = generatekey(1)
            itemdetailkey_list.append([itemdetail_key])

            prfitemsupplier = Prfdetail.objects\
                .raw('SELECT b.id, i.id AS inv_id, i.code, i.description, b.price, b.processingdate, b.datetransaction, '
                     's.id AS supplier_id, s.code AS supplier_code, s.name AS supplier_name, '
                     'v.id AS vat_id, v.code AS vat_code, v.rate AS vat_rate , chid '
                     'FROM (SELECT IF(@prev != a.supplier_id, @rownum := 1, @rownum := @rownum + 1) AS rownumber, '
                            '@prev := a.supplier_id, a.*, a.id AS chid '
                            'FROM (SELECT * FROM cshistory ch, (SELECT @rownum := 0, @prev := "") sq '
                            'WHERE invitem_id = ' + str(data.invitem.id) + ' '
                            'ORDER BY supplier_id, datetransaction DESC, price) a) b '
                     'LEFT JOIN inventoryitem i ON i.id = b.invitem_id '
                     'LEFT JOIN supplier s ON s.id = b.supplier_id '
                     'LEFT JOIN vat v ON v.id = s.vat_id '
                     'WHERE rownumber = 1 '
                     'ORDER BY price '
                     'LIMIT 3')

            i = 1
            for data2 in prfitemsupplier:

                if data2.chid not in prfitemcshistory_list:
                    prfitemsupplier_list.append([data2.code,
                                                 data2.description,
                                                 data2.price,
                                                 data2.processingdate,
                                                 data2.datetransaction,
                                                 data2.supplier_name,
                                                 data2.vat_id,
                                                 data2.vat_rate,
                                                 data2.vat_code,
                                                 data2.inv_id,
                                                 data2.supplier_id,
                                                 ])

                prfitemcshistory_list.append(data2.chid)

                detail = Csdetailtemp()
                detail.prfmain = Prfmain.objects.get(pk=data.prfmain.id)
                detail.prfdetail = Prfdetail.objects.get(pk=data.id)
                detail.invitem = Inventoryitem.objects.get(pk=data2.inv_id)
                detail.invitem_code = data2.code
                detail.invitem_name = data2.description
                detail.quantity = 0
                detail.item_counter = i
                detail.supplier = Supplier.objects.get(pk=data2.supplier_id)
                detail.suppliercode = data2.supplier_code
                detail.suppliername = data2.supplier_name
                detail.vatrate = data2.vat_rate
                detail.unitcost = data2.price
                detail.negocost = data2.price
                detail.secretkey = request.POST['secretkey']
                detail.csstatus = 1 if i == 1 else 0
                detail.status = 'A'
                detail.enterdate = datetime.datetime.now()
                detail.modifydate = datetime.datetime.now()
                detail.vat = Vat.objects.get(pk=data2.vat_id)
                detail.vatable = 0
                detail.vatexempt = 0
                detail.vatzerorated = 0
                detail.grossamount = 0
                detail.vatamount = 0
                detail.netamount = 0
                detail.currency = Currency.objects.get(isdeleted=0, status='A', symbol='PHP')
                detail.enterby = request.user
                detail.modifyby = request.user
                detail.isdeleted = 0
                detail.itemdetailkey = itemdetail_key
                detail.save()

                i += 1

            # supplierdetail = Supplier.objects.filter(isdeleted=0).order_by('name').first()
            #
            # detail = Csdetailtemp()
            # detail.prfmain = Prfmain.objects.get(pk=data.prfmain.id)
            # detail.prfdetail = Prfdetail.objects.get(pk=data.id)
            # detail.invitem = Inventoryitem.objects.get(pk=data.invitem.id)
            # detail.invitem_code = data.invitem.code
            # detail.invitem_name = data.invitem.description
            # detail.quantity = 0
            # detail.item_counter = i
            # detail.supplier = Supplier.objects.get(pk=supplierdetail.id)
            # detail.suppliercode = supplierdetail.code
            # detail.suppliername = supplierdetail.name
            # detail.vatrate = supplierdetail.vat.rate
            # detail.unitcost = 0
            # detail.negocost = 0
            # detail.secretkey = request.POST['secretkey']
            # detail.csstatus = 1
            # detail.status = 'A'
            # detail.enterdate = datetime.datetime.now()
            # detail.modifydate = datetime.datetime.now()
            # detail.vat = Vat.objects.get(pk=supplierdetail.vat.id, isdeleted=0)
            # detail.vatable = 0
            # detail.vatexempt = 0
            # detail.vatzerorated = 0
            # detail.grossamount = 0
            # detail.vatamount = 0
            # detail.netamount = 0
            # detail.currency = Currency.objects.get(isdeleted=0, status='A', symbol='PHP')
            # detail.enterby = request.user
            # detail.modifyby = request.user
            # detail.isdeleted = 0
            # detail.save()

        prfdata = [prfmain.prfnum]
        prfdetail_list = []

        for data in prfdetail:
            prfdetail_list.append([data.invitem_code,
                                   data.invitem_name,
                                   data.prfmain.prfnum,
                                   data.quantity,
                                   data.invitem.id,
                                   itemdetail_key,
                                   ])

        # store temp csdata
        if Csdata.objects.filter(secretkey=request.POST['secretkey'], prfmain=prfmain).exists():
            data = {
                'status': 'error',
            }
        else:
            detail = Csdata()
            detail.secretkey = request.POST['secretkey']
            detail.prfmain = prfmain
            detail.save()

            data = {
                'status': 'success',
                'prfdata': prfdata,
                'prfsupplier': prfitemsupplier_list,
                'prfdetail': prfdetail_list,
                'itemdetailkey': itemdetailkey_list,
            }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def removePrf(request):

    if request.method == 'POST':
        prfmain = Prfmain.objects.get(prfnum=request.POST['prfnum'],
                                      prfstatus="A",
                                      status="A",
                                      isdeleted=0)

        Csdata.objects.filter(prfmain=prfmain.id, isdeleted=0, secretkey=request.POST['secretkey']).delete()

        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def removeItem(request):

    if request.method == 'POST':
        item = Inventoryitem.objects.get(code=request.POST['item']).id
        Csdetailtemp.objects.filter(invitem=item, itemdetailkey=request.POST['itemdetailkey'], secretkey=request.POST['secretkey']).delete()

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
        csmain = Csmain.objects.all().filter(Q(csnum__icontains=search) |
                                             Q(csdate__icontains=search) |
                                             Q(particulars__icontains=search) |
                                             Q(csstatus__icontains=search) |
                                             Q(csnum__icontains=search_not_slug) |
                                             Q(csdate__icontains=search_not_slug) |
                                             Q(particulars__icontains=search_not_slug) |
                                             Q(csstatus__icontains=search_not_slug))\
                                            .filter(isdeleted=0).order_by('-enterdate')
    else:
        csmain = Csmain.objects.all().filter(isdeleted=0).order_by('-enterdate')[current:current+limit]

    json_models = serializers.serialize("json", csmain)
    print json_models
    return HttpResponse(json_models, content_type="application/javascript")


def comments():
    print 123
