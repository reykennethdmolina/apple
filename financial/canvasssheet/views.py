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
from department.models import Department
from branch.models import Branch
from unitofmeasure.models import Unitofmeasure
from vat.models import Vat
from currency.models import Currency
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from acctentry.views import generatekey
from purchaserequisitionform.views import updateTransaction
import datetime

# pagination and search
from endless_pagination.views import AjaxListView


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Csmain
    template_name = 'canvasssheet/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'canvasssheet/index_list.html'
    def get_queryset(self):
        query = Csmain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(csnum__icontains=keysearch) |
                                 Q(csdate__icontains=keysearch) |
                                 Q(cstype__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch) |
                                 Q(remarks__icontains=keysearch))
        return query


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
        csdata = Csdata.objects.filter(isdeleted=0).exclude(csmain=None).values_list('prfmain', flat=True)
        context['prfmain'] = Prfmain.objects.filter(isdeleted=0, prfstatus='A', status='A').exclude(id__in=csdata)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('code')
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('name')
        context['suppliertype'] = Suppliertype.objects.filter(isdeleted=0).order_by('description')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('code')
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('description')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('pk')
        context['industry'] = Industry.objects.filter(isdeleted=0).order_by('name')

        return context

    def form_valid(self, form):
        csdata = Csdata.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0)

        for data in csdata:
            csdata_item = Csdata.objects.filter(prfmain=data.prfmain, isdeleted=0)\
                                        .exclude(csmain=None)

            if not csdata_item:
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

                    Csdata.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0).update(csmain=csmain)

                    importTemptodetail(self.request.POST['secretkey'], csmain)
                    updateCsmainvat(csnum)

                    return HttpResponseRedirect('/canvasssheet/' + str(self.object.id) + '/update/')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Csmain
    template_name = 'canvasssheet/edit.html'
    fields = ['csdate', 'cstype', 'particulars', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('canvasssheett.change_csmain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        csdata = Csdata.objects.filter(isdeleted=0).exclude(csmain=None).values_list('prfmain', flat=True)
        context['prfmain'] = Prfmain.objects.filter(isdeleted=0, prfstatus='A', status='A').exclude(id__in=csdata)
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('code')
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('name')
        context['suppliertype'] = Suppliertype.objects.filter(isdeleted=0).order_by('description')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('code')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('code')
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('description')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('pk')
        context['industry'] = Industry.objects.filter(isdeleted=0).order_by('name')
        context['prfimported'] = Csdata.objects.filter(csmain=self.object.pk, isdeleted=0).exclude(prfmain=None)
        context['csmain'] = self.object.pk
        context['pagetype'] = 'update'

        Csdetailtemp.objects.filter(csmain=self.object.pk).delete()  # clear all temp data

        # move to temp
        detail = Csdetail.objects.filter(isdeleted=0, csmain=self.object.pk).order_by('item_counter')
        for d in detail:
            detailtemp = Csdetailtemp()
            detailtemp.invitem_code = d.invitem_code
            detailtemp.invitem_name = d.invitem_name
            detailtemp.item_counter = d.item_counter
            detailtemp.suppliercode = d.suppliercode
            detailtemp.suppliername = d.suppliername
            detailtemp.vatrate = d.vatrate
            detailtemp.unitcost = d.unitcost
            detailtemp.negocost = d.negocost
            detailtemp.csstatus = d.csstatus
            detailtemp.status = d.status
            detailtemp.enterdate = d.enterdate
            detailtemp.modifydate = d.modifydate
            detailtemp.postdate = d.postdate
            detailtemp.isdeleted = d.isdeleted
            detailtemp.vatable = d.vatable
            detailtemp.vatexempt = d.vatexempt
            detailtemp.vatzerorated = d.vatzerorated
            detailtemp.grossamount = d.grossamount
            detailtemp.vatamount = d.vatamount
            detailtemp.netamount = d.netamount
            detailtemp.csmain = d.csmain
            detailtemp.currency = d.currency
            detailtemp.enterby = d.enterby
            detailtemp.invitem = d.invitem
            detailtemp.modifyby = d.modifyby
            detailtemp.postby = d.postby
            detailtemp.supplier = d.supplier
            detailtemp.vat = d.vat
            detailtemp.quantity = d.quantity
            detailtemp.uc_grossamount = d.uc_grossamount
            detailtemp.uc_netamount = d.uc_netamount
            detailtemp.uc_vatable = d.uc_vatable
            detailtemp.uc_vatamount = d.uc_vatamount
            detailtemp.uc_vatexempt = d.uc_vatexempt
            detailtemp.uc_vatzerorated = d.uc_vatzerorated
            detailtemp.prfmain = d.prfmain
            detailtemp.prfdetail = d.prfdetail
            detailtemp.csdetail = Csdetail.objects.get(pk=d.pk)
            detailtemp.itemdetailkey = d.itemdetailkey
            detailtemp.department = d.department
            detailtemp.department_code = d.department_code
            detailtemp.department_name = d.department_name
            detailtemp.invitem_unitofmeasure = d.invitem_unitofmeasure
            detailtemp.invitem_unitofmeasure_code = d.invitem_unitofmeasure_code
            detailtemp.grosscost = d.grosscost
            detailtemp.uc_grosscost = d.uc_grosscost
            detailtemp.estimateddateofdelivery = d.estimateddateofdelivery
            detailtemp.remarks = d.remarks
            detailtemp.branch = d.branch
            detailtemp.secretkey = context['secretkey']
            detailtemp.save()

        context['csdetailtemp'] = Csdetailtemp.objects.filter(isdeleted=0, csmain=self.object.pk).\
            order_by('itemdetailkey', '-csstatus')

        return context

    def form_valid(self, form):
        csdata = Csdata.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0)

        csmain = Csmain.objects.get(pk=self.object.id)

        for data in csdata:
            csdata_item = Csdata.objects.filter(prfmain=data.prfmain, isdeleted=0)\
                                        .exclude(csmain=None)

            if not csdata_item:
                Csdata.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0).update(csmain=csmain)

        # for removed csdatas
        csdata = Csdata.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=2)

        for data in csdata:
            Csdata.objects.filter(csmain=data.csmain.id, prfmain=data.prfmain.id, isdeleted=0).update(isdeleted=1)
            data.delete()

        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()

        updateimportTemptodetail(csmain)
        updateCsmainvat(csmain.csnum)

        return HttpResponseRedirect('/canvasssheet/' + str(self.object.id) + '/update/')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Csmain
    template_name = 'canvasssheet/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('canvasssheet.delete_csmain') or self.object.status == 'O' or self.object.csstatus == 'A':
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
    csmain_aggregates = Csdetail.objects.filter(csmain__csnum=csnum, csstatus=1).aggregate(Sum('quantity'),
                                                                               Sum('vatable'),
                                                                               Sum('vatexempt'),
                                                                               Sum('vatzerorated'),
                                                                               Sum('grosscost'),
                                                                               Sum('grossamount'),
                                                                               Sum('vatamount'),
                                                                               Sum('netamount'),
                                                                               Sum('uc_vatable'),
                                                                               Sum('uc_vatexempt'),
                                                                               Sum('uc_vatzerorated'),
                                                                               Sum('uc_grosscost'),
                                                                               Sum('uc_grossamount'),
                                                                               Sum('uc_vatamount'),
                                                                               Sum('uc_netamount'))

    Csmain.objects.filter(csnum=csnum, isdeleted=0, status='A').\
                  update(quantity=csmain_aggregates['quantity__sum'],
                         vatable=csmain_aggregates['vatable__sum'],
                         vatexempt=csmain_aggregates['vatexempt__sum'],
                         vatzerorated=csmain_aggregates['vatzerorated__sum'],
                         grosscost=csmain_aggregates['grosscost__sum'],
                         grossamount=csmain_aggregates['grossamount__sum'],
                         vatamount=csmain_aggregates['vatamount__sum'],
                         netamount=csmain_aggregates['netamount__sum'],
                         uc_vatable=csmain_aggregates['uc_vatable__sum'],
                         uc_vatexempt=csmain_aggregates['uc_vatexempt__sum'],
                         uc_vatzerorated=csmain_aggregates['uc_vatzerorated__sum'],
                         uc_grosscost=csmain_aggregates['uc_grosscost__sum'],
                         uc_grossamount=csmain_aggregates['uc_grossamount__sum'],
                         uc_vatamount=csmain_aggregates['uc_vatamount__sum'],
                         uc_netamount=csmain_aggregates['uc_netamount__sum'])


@csrf_exempt
def updateCsdetailtemp(request):
    if request.method == 'POST':

        i = 0
        # assign quantity
        for data in request.POST.getlist('arr_quantity_item[]'):
            department = Department.objects.get(pk=request.POST.getlist('arr_item_department_input[]')[i], isdeleted=0)
            branch = Branch.objects.get(pk=request.POST.getlist('arr_item_branch_input[]')[i], isdeleted=0)
            unitofmeasure = Unitofmeasure.objects.get(pk=request.POST.getlist('arr_item_unitofmeasure_input[]')[i], isdeleted=0)


            request.POST.getlist('arr_item_unitofmeasure_input[]')[i]
            csdetailtempupdate = Csdetailtemp.objects.filter(secretkey=request.POST['secretkey'],
                                        itemdetailkey=request.POST.getlist('arr_item_detail_key[]')[i],
                                        invitem=data,
                                        isdeleted=0,
                                        status='A')

            csdetailtempupdate.update(quantity=request.POST.getlist('arr_item_quantity_input[]')[i],
                                                           department=department.id,
                                                           department_code=department.code,
                                                           department_name=department.departmentname,
                                                           branch=branch.id,
                                                           invitem_unitofmeasure=unitofmeasure.id,
                                                           invitem_unitofmeasure_code=unitofmeasure.code,
                                                           remarks=request.POST.getlist('arr_item_remarks_input[]')[i])

            if request.POST.getlist('arr_item_etd_input[]')[i]:
                csdetailtempupdate.update(estimateddateofdelivery=request.POST.getlist('arr_item_etd_input[]')[i])

            i += 1

        i = 0

        # assign checked supplier
        for data in request.POST.getlist('arr_checked_supplier[]'):
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
        # assign nego cost and vat per supplier item
        for data in request.POST.getlist('arr_item_cost_supplier[]'):
            detail = Csdetailtemp.objects.filter(secretkey=request.POST['secretkey'],
                                        invitem=request.POST.getlist('arr_item_cost_item[]')[i],
                                        itemdetailkey=request.POST.getlist('arr_item_each_detail_key[]')[i],
                                        supplier=data, isdeleted=0, status='A')

            # assignment of negocost, vat
            detail.update(negocost=request.POST.getlist('arr_item_cost[]')[i])
            detail.update(vatrate=request.POST.getlist('arr_item_cost_vatrate[]')[i])
            detail.update(vat=Vat.objects.get(pk=request.POST.getlist('arr_item_cost_vat[]')[i], status='A', isdeleted=0))

            detailget = Csdetailtemp.objects.get(secretkey=request.POST['secretkey'],
                                        invitem=request.POST.getlist('arr_item_cost_item[]')[i],
                                        itemdetailkey=request.POST.getlist('arr_item_each_detail_key[]')[i],
                                        supplier=data, isdeleted=0, status='A')

            # compute vat etc
            # nego cost
            item_total_amount = float(detailget.quantity) * float(detailget.negocost)
            item_vat_rate = detailget.vatrate
            item_gross_amount = item_total_amount
            item_gross_cost = float(detailget.negocost)
            item_vatcode = Vat.objects.get(pk=detailget.vat.id, status='A', isdeleted=0).code
            item_vatable = 0
            item_vatexempt = 0
            item_vatzero = 0

            if item_vat_rate > 0:
                item_gross_amount = float(item_total_amount)/(1+(float(item_vat_rate)/100))
                item_gross_cost = float(detailget.negocost)/(1+(float(item_vat_rate)/100))
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
            uc_item_gross_cost = float(detailget.unitcost)
            uc_item_vatcode = Vat.objects.get(pk=detailget.vat.id, status='A', isdeleted=0).code
            uc_item_vatable = 0
            uc_item_vatexempt = 0
            uc_item_vatzero = 0

            if uc_item_vat_rate > 0:
                uc_item_gross_amount = float(uc_item_total_amount)/(1+(float(uc_item_vat_rate)/100))
                uc_item_gross_cost = float(detailget.unitcost)/(1+(float(uc_item_vat_rate)/100))
                uc_item_vatable = item_gross_amount
            else:
                if uc_item_vatcode == 'VE':
                    uc_item_vatexempt = uc_item_gross_amount

                elif item_vatcode == 'ZE':
                    uc_item_vatzero = item_gross_amount

            uc_item_addvat = float(uc_item_total_amount) - float(uc_item_gross_amount)

            detail.update(netamount=item_total_amount,
                          vatable=item_vatable,
                          vatexempt=item_vatexempt,
                          vatzerorated=item_vatzero,
                          vatamount=item_addvat,
                          grossamount=item_gross_amount,
                          grosscost=item_gross_cost,
                          uc_netamount=uc_item_total_amount,
                          uc_vatable=uc_item_vatable,
                          uc_vatexempt=uc_item_vatexempt,
                          uc_vatzerorated=uc_item_vatzero,
                          uc_vatamount=uc_item_addvat,
                          uc_grossamount=uc_item_gross_amount,
                          uc_grosscost=uc_item_gross_cost)

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
def updateimportTemptodetail(csmain):
    csdetailtemp = Csdetailtemp.objects.filter(csmain=csmain.id, isdeleted=0, status='A').order_by('id')

    Csdetail.objects.filter(csmain=csmain.id, isdeleted=0, status='A').update(isdeleted=2)

    i = 1
    for data in csdetailtemp:
        csdetail = Csdetail()
        csdetail.item_counter = i
        csdetail.invitem_code = data.invitem_code
        csdetail.invitem_name = data.invitem_name
        csdetail.suppliercode = data.suppliercode
        csdetail.suppliername = data.suppliername
        csdetail.department = data.department
        csdetail.department_code = data.department_code
        csdetail.department_name = data.department_name
        csdetail.branch = data.branch
        csdetail.invitem_unitofmeasure = data.invitem_unitofmeasure
        csdetail.invitem_unitofmeasure_code = data.invitem_unitofmeasure_code
        csdetail.estimateddateofdelivery = data.estimateddateofdelivery
        csdetail.remarks = data.remarks
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
        csdetail.grosscost = data.grosscost
        csdetail.grossamount = data.grossamount
        csdetail.vatamount = data.vatamount
        csdetail.netamount = data.netamount
        csdetail.uc_vatable = data.uc_vatable
        csdetail.uc_vatexempt = data.uc_vatexempt
        csdetail.uc_vatzerorated = data.uc_vatzerorated
        csdetail.uc_grosscost = data.uc_grosscost
        csdetail.uc_grossamount = data.uc_grossamount
        csdetail.uc_vatamount = data.uc_vatamount
        csdetail.uc_netamount = data.uc_netamount
        csdetail.csmain = csmain
        csdetail.currency = data.currency
        csdetail.invitem = data.invitem
        csdetail.supplier = data.supplier
        csdetail.vat = data.vat
        csdetail.quantity = data.quantity
        csdetail.itemdetailkey = data.itemdetailkey
        csdetail.prfmain = data.prfmain
        csdetail.prfdetail = data.prfdetail
        csdetail.save()
        i += 1

    csdetailtemp.delete()
    Csdetail.objects.filter(csmain=csmain.id, isdeleted=2, status='A').delete()


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
        csdetail.department = data.department
        csdetail.department_code = data.department_code
        csdetail.department_name = data.department_name
        csdetail.branch = data.branch
        csdetail.invitem_unitofmeasure = data.invitem_unitofmeasure
        csdetail.invitem_unitofmeasure_code = data.invitem_unitofmeasure_code
        csdetail.estimateddateofdelivery = data.estimateddateofdelivery
        csdetail.remarks = data.remarks
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
        csdetail.grosscost = data.grosscost
        csdetail.grossamount = data.grossamount
        csdetail.vatamount = data.vatamount
        csdetail.netamount = data.netamount
        csdetail.uc_vatable = data.uc_vatable
        csdetail.uc_vatexempt = data.uc_vatexempt
        csdetail.uc_vatzerorated = data.uc_vatzerorated
        csdetail.uc_grosscost = data.uc_grosscost
        csdetail.uc_grossamount = data.uc_grossamount
        csdetail.uc_vatamount = data.uc_vatamount
        csdetail.uc_netamount = data.uc_netamount
        csdetail.csmain = csmain
        csdetail.currency = data.currency
        csdetail.invitem = data.invitem
        csdetail.supplier = data.supplier
        csdetail.vat = data.vat
        csdetail.quantity = data.quantity
        csdetail.itemdetailkey = data.itemdetailkey
        csdetail.prfmain = data.prfmain
        csdetail.prfdetail = data.prfdetail
        csdetail.save()
        i += 1

    csdetailtemp.delete()


@csrf_exempt
def getSupplier(request):

    if request.method == 'POST':

        # check if data from updateview
        csdetail_exist = Csdetailtemp.objects.filter(itemdetailkey=request.POST['itemdetailkey']).exclude(csmain=None).order_by('modifydate')

        supplier = Supplier.objects.get(pk=request.POST['supplier'], isdeleted=0, status='A')
        detail = Csdetailtemp()
        if not csdetail_exist:
            # from createview
            item = Inventoryitem.objects.get(code=request.POST['item'], status='A', isdeleted=0)
            # check first if item supplier is first before creating new itemdetailkey
            detail.invitem = Inventoryitem.objects.get(pk=item.id)
            detail.invitem_code = item.code
            detail.invitem_name = item.description
            if int(request.POST['prfmain']) != 0 and int(request.POST['prfdetail']) != 0:
                detail.prfmain = Prfmain.objects.get(pk=request.POST['prfmain'])
                detail.prfdetail = Prfdetail.objects.get(pk=request.POST['prfdetail'])
            detail.quantity = 0
            detail.item_counter = 0
            if request.POST['pagetype'] == 'update':
                detail.csmain = Csmain.objects.get(pk=request.POST['csmain'])

        else:
            # from updateview
            csdetail_exist = csdetail_exist.first()
            if csdetail_exist.csdetail:
                detail.csdetail = Csdetail.objects.get(pk=csdetail_exist.csdetail.id)
            detail.csmain = Csmain.objects.get(pk=csdetail_exist.csmain.id)
            if csdetail_exist.department:
                detail.department = Department.objects.get(pk=csdetail_exist.department.id)
            detail.department_code = csdetail_exist.department_code
            detail.department_name = csdetail_exist.department_name
            detail.estimateddateofdelivery = csdetail_exist.estimateddateofdelivery
            detail.remarks = csdetail_exist.remarks
            if csdetail_exist.branch:
                detail.branch = Branch.objects.get(pk=csdetail_exist.branch.id)
            if csdetail_exist.invitem_unitofmeasure:
                detail.invitem_unitofmeasure = Unitofmeasure.objects.get(pk=csdetail_exist.invitem_unitofmeasure.id)
            detail.invitem_unitofmeasure_code = csdetail_exist.invitem_unitofmeasure_code

            detail.invitem = Inventoryitem.objects.get(pk=csdetail_exist.invitem.id)
            detail.invitem_code = csdetail_exist.invitem_code
            detail.invitem_name = csdetail_exist.invitem_name
            if csdetail_exist.prfmain and csdetail_exist.prfdetail:
                detail.prfmain = Prfmain.objects.get(pk=csdetail_exist.prfmain.id)
                detail.prfdetail = Prfdetail.objects.get(pk=csdetail_exist.prfdetail.id)
            detail.quantity = csdetail_exist.quantity
            detail.item_counter = int(csdetail_exist.item_counter) + 1

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
            'suppliervat': supplier.vat.id,
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
            if request.POST['pagetype'] == "update":
                detail.csmain = Csmain.objects.get(pk=request.POST['csmain'])
            detail.save()

            i += 1

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
    # front end - hover imported prf to show details
    # back - prf should only be cs once unless cancelled

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
                detail.department = Department.objects.get(pk=data.department.id)
                detail.department_code = data.department_code
                detail.department_name = data.department_name
                detail.branch = Branch.objects.get(pk=data.prfmain.branch.id)
                detail.invitem_unitofmeasure = Unitofmeasure.objects.get(pk=data.invitem_unitofmeasure.id)
                detail.invitem_unitofmeasure_code = data.invitem_unitofmeasure_code
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
                if request.POST['pagetype'] == "update":
                    detail.csmain = Csmain.objects.get(pk=request.POST['csmain'])
                detail.save()

                i += 1

        prfdata = [prfmain.prfnum]
        prfdetail_list = []

        for data in prfdetail:
            prfdetail_list.append([data.invitem_code,
                                   data.invitem_name,
                                   data.prfmain.prfnum,
                                   data.quantity,
                                   data.invitem.id,
                                   itemdetail_key,
                                   data.department.id,
                                   data.invitem_unitofmeasure.id,
                                   data.prfmain.branch.id,
                                   data.remarks,
                                   data.id,
                                   data.prfmain.id
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

        if request.POST['pagetype'] == 'update':
            csdata = Csdata()
            csdata.secretkey = request.POST['secretkey']
            csdata.isdeleted = 2
            csdata.csmain = Csmain.objects.get(pk=request.POST['csmain'])
            csdata.prfmain = Prfmain.objects.get(pk=prfmain.id)
            csdata.save()
        else:
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
        if request.POST['pagetype'] == 'update':
            Csdetailtemp.objects.filter(invitem=item, itemdetailkey=request.POST['itemdetailkey'], csmain=request.POST['csmain']).delete()
        else:
            Csdetailtemp.objects.filter(invitem=item, itemdetailkey=request.POST['itemdetailkey'], secretkey=request.POST['secretkey']).delete()

        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def updateStatus(request, command, pk):

    response = 'success'
    data = Csmain.objects.filter(pk=pk, isdeleted=0)

    if (command == "approve" or command == "disapprove") and data:
        if command == "approve":
            status = 'A'
        elif command == "disapprove":
            status = 'D'

        data.update(csstatus=status)

        for data2 in Csdata.objects.filter(csmain=pk, isdeleted=0):
            updateTransaction(data2.prfmain.pk, status)
            if command == "disapprove":
                data2.isdeleted = 1
                data2.save()

    else:
        response = 'error'

    data = {
        'status': response
    }

    # return JsonResponse(data)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def comments():
    print 123
    # removed from imported(doesnt remove prfdetail data of items) -> re-imported(diplicates item with same prfdetail)