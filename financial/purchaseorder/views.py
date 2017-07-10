from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
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
        context['podata'] = Podata.objects.filter(isdeleted=0, pomain=self.kwargs['pk'])
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
        context['pagetype'] = "create"
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
                        totalpoqty = Podetail.objects.filter(pomain__ponum=ponum, prfmain=data['prfmain']). \
                            aggregate(Sum('quantity'))['quantity__sum']
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

            return HttpResponseRedirect('/purchaseorder/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Pomain
    template_name = 'purchaseorder/edit.html'
    fields = ['ponum', 'podate', 'potype', 'refnum', 'urgencytype', 'dateneeded', 'postatus', 'supplier',
              'inputvattype', 'deferredvat', 'creditterm', 'particulars', 'creditterm', 'vat', 'atc', 'currency',
              'deliverydate', 'designatedapprover', 'wtax']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('purchaseorder.change_pomain') or self.object.isdeleted == 1:
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').\
            order_by('first_name')
        context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('description')
        context['postatus'] = Pomain.objects.get(pk=self.object.pk).get_postatus_display()
        context['prfimported'] = Podata.objects.filter(pomain=self.object.pk, isdeleted=0).exclude(prfmain=None)
        context['prfmain'] = Prfmain.objects.filter(isdeleted=0, prfstatus='A', status='A',
                                                    totalremainingquantity__gt=0)
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('pk')
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')

        detail = Podetail.objects.filter(isdeleted=0, pomain=self.object.pk).order_by('item_counter')

        if self.object.postatus != 'A':
            Podetailtemp.objects.filter(pomain=self.object.pk).delete()        # clear all temp data
            for d in detail:
                detailtemp = Podetailtemp()
                detailtemp.item_counter = d.item_counter
                detailtemp.invitem_code = d.invitem_code
                detailtemp.invitem_name = d.invitem_name
                detailtemp.invitem_unitofmeasure = d.invitem_unitofmeasure
                detailtemp.quantity = d.quantity
                detailtemp.unitcost = d.unitcost
                detailtemp.discountrate = d.discountrate
                detailtemp.remarks = d.remarks
                detailtemp.status = d.status
                detailtemp.enterdate = d.enterdate
                detailtemp.modifydate = d.modifydate
                detailtemp.postdate = d.postdate
                detailtemp.isdeleted = d.isdeleted
                detailtemp.branch = d.branch
                detailtemp.department = d.department
                detailtemp.enterby = d.enterby
                detailtemp.invitem = d.invitem
                detailtemp.modifyby = d.modifyby
                # detailtemp.podetail = Podetail.objects.get(pk=d.id)
                detailtemp.pomain = d.pomain
                detailtemp.postby = d.postby
                detailtemp.discountamount = d.discountamount
                detailtemp.grossamount = d.grossamount
                detailtemp.netamount = d.netamount
                detailtemp.vat = d.vat
                detailtemp.vatable = d.vatable
                detailtemp.vatamount = d.vatamount
                detailtemp.vatexempt = d.vatexempt
                detailtemp.vatrate = d.vatrate
                detailtemp.vatzerorated = d.vatzerorated
                detailtemp.currency = d.currency
                detailtemp.unitofmeasure = d.unitofmeasure
                detailtemp.assetnum = d.assetnum
                detailtemp.employee = d.employee
                detailtemp.employee_code = d.employee_code
                detailtemp.employee_name = d.employee_name
                detailtemp.serialnum = d.serialnum
                detailtemp.expirationdate = d.expirationdate
                detailtemp.department_code = d.department_code
                detailtemp.department_name = d.department_name
                detailtemp.prfdetail = d.prfdetail
                detailtemp.prfmain = d.prfmain
                detailtemp.save()
            podetailtemp = Podetailtemp.objects.filter(isdeleted=0, pomain=self.object.pk).order_by('item_counter')
        else:
            podetailtemp = Podetail.objects.filter(isdeleted=0, pomain=self.object.pk).order_by('item_counter')

        context['podetailtemp'] = podetailtemp

        context['grossunitcost'] = []

        for data in context['podetailtemp']:
            grossunitcost = float(data.unitcost) / (1 + (float(data.vatrate) / 100))
            context['grossunitcost'].append(grossunitcost)

        context['data'] = zip(context['podetailtemp'], context['grossunitcost'])
        context['pagetype'] = "update"
        context['pomain'] = self.object.pk
        return context

    def form_valid(self, form):
        if Podetailtemp.objects.filter(  # this will not include APPROVED purchase orders
                Q(isdeleted=0), Q(pomain=self.object.pk) | Q(secretkey=self.request.POST['secretkey'])):
            self.object = form.save(commit=False)
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()

            # if self.object.rfstatus == 'A':  the save line below will be used for APPROVED purchase orders
            #     self.object.save(update_fields=['particulars', 'modifyby', 'modifydate'])

            self.object.save(update_fields=['podate', 'potype', 'refnum', 'urgencytype', 'dateneeded',
                                            'supplier', 'inputvattype', 'deferredvat', 'creditterm', 'particulars',
                                            'creditterm', 'vat', 'atc', 'currency', 'deliverydate',
                                            'wtax'])

            if self.request.POST['postatus'] == 'F':
                self.object.designatedapprover = User.objects.get(pk=self.request.POST['designatedapprover'])
                self.object.save()
            else:
                self.object.postatus = self.request.POST['postatus']
                self.object.approverresponse = self.request.POST['postatus']
                self.object.responsedate = datetime.datetime.now()
                self.object.actualapprover = self.request.user
                if self.request.POST['postatus'] == 'D':
                    self.object.isdeleted = 0
                    self.object.status = 'C'
                self.object.save()

            Podetailtemp.objects.filter(isdeleted=1, pomain=self.object.pk).delete()

            Podetail.objects.filter(pomain=self.object.pk).update(isdeleted=1)

            alltempdetail = Podetailtemp.objects.filter(
                Q(isdeleted=0), Q(pomain=self.object.pk) | Q(secretkey=self.request.POST['secretkey'])
            ).order_by('enterdate')
            podetaildeleted = Podetail.objects.filter(pomain=self.object.id, isdeleted=1)
            for data in podetaildeleted:
                if Prfpotransaction.objects.filter(podetail=data.id):
                    deleteprfpotransactionitem(data)
            i = 1
            pomain_totalamount = 0
            for atd in alltempdetail:
                # START: transfer po detail temp data to po detail, reflecting changes made in the screen
                alldetail = Podetail()
                alldetail.item_counter = i
                alldetail.pomain = Pomain.objects.get(ponum=self.request.POST['ponum'])
                alldetail.invitem = atd.invitem
                alldetail.invitem_code = atd.invitem_code
                alldetail.invitem_name = atd.invitem_name
                alldetail.invitem_unitofmeasure = Unitofmeasure.objects.get(pk=self.request.POST.
                                                                            getlist('temp_item_um')[i - 1], isdeleted=0,
                                                                            status='A').code
                alldetail.quantity = self.request.POST.getlist('temp_quantity')[i - 1]
                alldetail.unitcost = self.request.POST.getlist('temp_unitcost')[i - 1]
                alldetail.discountrate = self.request.POST.getlist('temp_discountrate')[i - 1] if \
                    self.request.POST.getlist('temp_discounttype')[i - 1] == "rate" else 0
                alldetail.remarks = self.request.POST.getlist('temp_remarks')[i - 1]
                alldetail.status = atd.status
                alldetail.enterdate = atd.enterdate
                alldetail.modifydate = atd.modifydate
                alldetail.postdate = atd.postdate
                alldetail.isdeleted = atd.isdeleted
                alldetail.branch = Branch.objects.get(pk=self.request.POST.getlist('temp_branch')[i - 1], isdeleted=0,
                                                      status='A')
                alldetail.department = Department.objects.get(pk=self.request.POST.getlist('temp_department')[i - 1],
                                                              isdeleted=0)
                alldetail.department_code = alldetail.department.code
                alldetail.department_name = alldetail.department.departmentname
                alldetail.enterby = atd.enterby
                alldetail.modifyby = atd.modifyby
                alldetail.postby = atd.postby
                alldetail.vat = Vat.objects.get(pk=self.request.POST['vat'], isdeleted=0, status='A')
                alldetail.vatrate = alldetail.vat.rate
                alldetail.currency = atd.currency
                alldetail.unitofmeasure = Unitofmeasure.objects.get(pk=self.request.POST.getlist('temp_item_um')[i - 1],
                                                                    isdeleted=0, status='A')

                grossUnitCost = float(alldetail.unitcost) / (1 + (float(alldetail.vatrate) / 100))
                alldetail.grossamount = grossUnitCost * float(alldetail.quantity)
                alldetail.discountamount = alldetail.grossamount * float(alldetail.discountrate) / 100 if \
                    self.request.POST.getlist('temp_discounttype')[i - 1] == "rate" else float(
                    self.request.POST.getlist('temp_discountamount')[i - 1])
                discountedAmount = alldetail.grossamount - alldetail.discountamount
                alldetail.vatamount = discountedAmount * (float(alldetail.vatrate) / 100)
                alldetail.netamount = discountedAmount + alldetail.vatamount

                if alldetail.vatrate > 0:
                    alldetail.vatable = discountedAmount
                    alldetail.vatexempt = 0
                    alldetail.vatzerorated = 0
                elif alldetail.vat.code == "VE":
                    alldetail.vatable = 0
                    alldetail.vatexempt = discountedAmount
                    alldetail.vatzerorated = 0
                elif alldetail.vat.code == "ZE":
                    alldetail.vatable = 0
                    alldetail.vatexempt = 0
                    alldetail.vatzerorated = discountedAmount

                if 'temp_expirationdate' in self.request.POST:
                    if self.request.POST.getlist('temp_expirationdate')[i - 1] != '':
                        alldetail.expirationdate = self.request.POST.getlist('temp_expirationdate')[i - 1]
                if 'temp_employee' in self.request.POST:
                    if self.request.POST.getlist('temp_employee')[i - 1] != '':
                        alldetail.employee = Employee.objects.get(pk=self.request.POST.getlist('temp_employee')[i - 1])
                        alldetail.employee_code = alldetail.employee.code
                        alldetail.employee_name = alldetail.employee.firstname + ' ' + alldetail.employee.lastname
                if 'temp_assetnum' in self.request.POST:
                    if self.request.POST.getlist('temp_assetnum')[i - 1] != '':
                        alldetail.assetnum = self.request.POST.getlist('temp_assetnum')[i - 1]
                if 'temp_serialnum' in self.request.POST:
                    if self.request.POST.getlist('temp_serialnum')[i - 1] != '':
                        alldetail.serialnum = self.request.POST.getlist('temp_serialnum')[i - 1]

                alldetail.prfmain = atd.prfmain
                alldetail.prfdetail = atd.prfdetail

                alldetail.save()
                # END: transfer po detail temp data to po detail, reflecting changes made in the screen

                # START: updates on prfpotransaction, prfdetail and prfmain
                if atd.prfmain:
                    podetail = Podetail.objects.get(pk=alldetail.id)

                    if podetail.quantity <= podetail.prfdetail.poremainingquantity and \
                                    podetail.prfdetail.isfullypo == 0:
                        data = Prfpotransaction()
                        data.prfmain = podetail.prfmain
                        data.prfdetail = podetail.prfdetail
                        data.pomain = podetail.pomain
                        data.podetail = podetail
                        data.poquantity = podetail.quantity
                        data.save()

                        # adjust prf detail
                        newpototalquantity = podetail.prfdetail.pototalquantity + data.poquantity
                        newporemainingquantity = podetail.prfdetail.poremainingquantity - data.poquantity
                        if newporemainingquantity == 0:
                            isfullypo = 1
                        else:
                            isfullypo = 0

                        Prfdetail.objects.filter(pk=data.prfdetail.id).update(pototalquantity=newpototalquantity,
                                                                              poremainingquantity=newporemainingquantity,
                                                                              isfullypo=isfullypo)

                        # adjust prf main
                        prfmain_poquantity = Prfmain.objects.get(pk=data.prfmain.id)
                        newtotalremainingquantity = prfmain_poquantity.totalremainingquantity - data.poquantity
                        Prfmain.objects.filter(pk=data.prfmain.id).update(
                            totalremainingquantity=newtotalremainingquantity)
                # END: updates on prfpotransaction, prfdetail and prfmain

                # START: update total fields in po main
                pomain_totalamount += ((float(alldetail.unitcost) * float(alldetail.quantity)) -
                                       float(alldetail.discountamount))
                atd.delete()
                i += 1

            Podetailtemp.objects.filter(pomain=self.object.pk).delete()  # clear all temp data
            Podetail.objects.filter(pomain=self.object.pk, isdeleted=1).delete()

            po_main_aggregates = Podetail.objects.filter(pomain=self.object.pk).aggregate(Sum('discountamount'),
                                                                                          Sum('grossamount'),
                                                                                          Sum('netamount'),
                                                                                          Sum('vatable'),
                                                                                          Sum('vatamount'),
                                                                                          Sum('vatexempt'),
                                                                                          Sum('vatzerorated'),
                                                                                          Sum('unitcost'),
                                                                                          Sum('quantity'))

            Pomain.objects.filter(pk=self.object.pk, isdeleted=0, status='A'). \
                update(discountamount=po_main_aggregates['discountamount__sum'],
                       grossamount=po_main_aggregates['grossamount__sum'],
                       netamount=po_main_aggregates['netamount__sum'], vatable=po_main_aggregates['vatable__sum'],
                       vatamount=po_main_aggregates['vatamount__sum'], vatexempt=po_main_aggregates['vatexempt__sum'],
                       vatzerorated=po_main_aggregates['vatzerorated__sum'],
                       totalamount=pomain_totalamount,
                       totalquantity=po_main_aggregates['quantity__sum'])
            # END: update total fields in po main

            # START: update po data
            podatafordeletion = Podata.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=2,
                                                      pomain=self.object.pk)
            for data in podatafordeletion:
                Podata.objects.filter(isdeleted=0, pomain=data.pomain, prfmain=data.prfmain).update(isdeleted=1)
                data.delete()
            Podata.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0, pomain=None).\
                update(pomain=self.object.pk)
            # END: update po data
        else:
            self.object = form.save(commit=False)
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['particulars', 'modifyby', 'modifydate'])

            if self.request.POST['postatus'] != 'A':
                self.object.postatus = self.request.POST['postatus']
                self.object.responsedate = datetime.datetime.now()
                self.object.actualapprover = self.request.user
                if self.request.POST['postatus'] == 'D':
                    self.object.isdeleted = 0
                    self.object.approverresponse = 'D'
                    self.object.status = 'C'
            self.object.save()

            approvedpoitems = Podetail.objects.filter(pomain=self.object.pk)
            i = 0
            for data in approvedpoitems:
                data.remarks = self.request.POST.getlist('temp_remarks')[i]
                data.save()
                i += 1

        return HttpResponseRedirect('/purchaseorder/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Pomain
    template_name = 'purchaseorder/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('purchaseorder.delete_pomain') or self.object.status == 'O' \
                or self.object.postatus == 'A':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.postatus = 'D'
        self.object.save()

        podetail = Podetail.objects.filter(pomain=self.object.id)
        for data in podetail:
            deleteprfpotransactionitem(data)

        podata = Podata.objects.filter(pomain=self.object.id)
        for data in podata:
            data.isdeleted = 1
            data.save()

        return HttpResponseRedirect('/purchaseorder')


@csrf_exempt
def fetchitems(request):
    if request.method == 'POST':
        prfmain = Prfmain.objects.get(pk=request.POST['prfid'],
                                      prfstatus='A',
                                      status='A',
                                      isdeleted=0)

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
        Podata.objects.filter(secretkey=request.POST['secretkey'], isdeleted=2, pomain__ponum=request.POST['ponumber'],
                              prfmain=prfmain).delete()
        if not Podata.objects.filter(prfmain=prfmain, isdeleted=0, secretkey=request.POST['secretkey'],
                                     pomain=None).exists():
            if not Podata.objects.filter(prfmain=prfmain, isdeleted=0, pomain__ponum=request.POST['ponumber']).exists():
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
    print request.POST['ponum']
    if request.method == 'POST':
        try:
            detailtemp = Podetailtemp.objects.get(pk=request.POST['podetailid'],
                                                  secretkey=request.POST['secretkey'],
                                                  pomain=None)
            detailtemp.delete()
            if request.POST['prfmainid'] != '':
                if not Podetailtemp.objects.filter(secretkey=request.POST['secretkey'],
                                                   prfmain=request.POST['prfmainid']).exists():
                    try:
                        Podata.objects.get(secretkey=request.POST['secretkey'], prfmain=request.POST['prfmainid'],
                                           pomain=None).delete()
                    except Podata.DoesNotExist:
                        print "po data does not exist"
                    if not Podata.objects.filter(prfmain=request.POST['prfmainid'], pomain__ponum=request.POST['ponum']).\
                            exists():
                        podatadeleted = 'true'
                        prfnum = Prfmain.objects.get(id=request.POST['prfmainid']).prfnum
                    else:
                        if Podata.objects.filter(prfmain=request.POST['prfmainid'], pomain__ponum=request.POST['ponum'],
                                                 isdeleted=0).exclude(secretkey=request.POST['secretkey']).exists():
                            podatatobecopied = Podata.objects.get(prfmain=request.POST['prfmainid'],
                                                                  pomain__ponum=request.POST['ponum'], isdeleted=0)
                            if not Podata.objects.filter(prfmain=request.POST['prfmainid'],
                                                         pomain__ponum=request.POST['ponum'],
                                                         isdeleted=2).exists():
                                if not Podetailtemp.objects.filter(pomain__ponum=request.POST['ponum'],
                                                                   prfmain=request.POST['prfmainid'],
                                                                   isdeleted=0).exists():
                                    podatadeleted = 'true'
                                    prfnum = Prfmain.objects.get(id=request.POST['prfmainid']).prfnum
                                    podatacopy = Podata()
                                    podatacopy.secretkey = request.POST['secretkey']
                                    podatacopy.isdeleted = 2
                                    podatacopy.pomain = podatatobecopied.pomain
                                    podatacopy.prfmain = podatatobecopied.prfmain
                                    podatacopy.save()
        except Podetailtemp.DoesNotExist:
            detailtemp = Podetailtemp.objects.get(pk=request.POST['podetailid'],
                                                  pomain__ponum=request.POST['ponum'])
            detailtemp.isdeleted = 1
            detailtemp.save()

            if request.POST['prfmainid'] != '':
                podetailtemp = Podetailtemp.objects.filter(secretkey=request.POST['secretkey'],
                                                           prfmain=request.POST['prfmainid'])
                if not podetailtemp.filter(isdeleted=0).exists():
                    podatatobecopied = Podata.objects.get(prfmain=request.POST['prfmainid'],
                                                          pomain__ponum=request.POST['ponum'], isdeleted=0)
                    if not Podata.objects.filter(prfmain=request.POST['prfmainid'], pomain__ponum=request.POST['ponum'],
                                                 isdeleted=2).exists():
                        if not Podetailtemp.objects.filter(pomain__ponum=request.POST['ponum'],
                                                           prfmain=request.POST['prfmainid'], isdeleted=0).exists():
                            podatadeleted = 'true'
                            prfnum = Prfmain.objects.get(id=request.POST['prfmainid']).prfnum
                            podatacopy = Podata()
                            podatacopy.secretkey = request.POST['secretkey']
                            podatacopy.isdeleted = 2
                            podatacopy.pomain = podatatobecopied.pomain
                            podatacopy.prfmain = podatatobecopied.prfmain
                            podatacopy.save()
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


def deleteprfpotransactionitem(podetail):
    print podetail.id
    data = Prfpotransaction.objects.get(podetail=podetail.id, status='A')
    # update prfdetail
    remainingquantity = podetail.prfdetail.poremainingquantity + data.poquantity
    isfullypo = 0 if remainingquantity != 0 else 1
    Prfdetail.objects.filter(pk=data.prfdetail.id).update(pototalquantity=F('pototalquantity') - data.poquantity,
                                                          poremainingquantity=F('poremainingquantity') + data.poquantity
                                                          , isfullypo=isfullypo)

    # update prfmain
    Prfmain.objects.filter(pk=data.prfmain.id).update(totalremainingquantity=F('totalremainingquantity') + data.
                                                      poquantity)

    # delete prfpotransaction, podetail
    data.delete()
    Podetail.objects.filter(pk=podetail.id).delete()
    Pomain.objects.filter(pk=podetail.pomain.id).update(totalquantity=0, totalamount=0.00, grossamount=0.00,
                                                        discountamount=0.00, netamount=0.00, vatable=0.00,
                                                        vatamount=0.00, vatexempt=0.00, vatzerorated=0.00)


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


