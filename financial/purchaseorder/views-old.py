from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F
from .models import Pomain, Podetail, Podetailtemp, Podata, Prfpotransaction
from purchaserequisitionform.models import Prfmain, Prfdetail
from companyparameter.models import Companyparameter
from employee.models import Employee
from supplier.models import Supplier
from ataxcode.models import Ataxcode
from inputvattype.models import Inputvattype
from inputvat.models import Inputvat
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
from processing_transaction.models import Poapvtransaction
from dateutil.relativedelta import relativedelta
import datetime

# pagination and search
from endless_pagination.views import AjaxListView

from utils.mixins import ReportContentMixin
from easy_pdf.views import PDFTemplateView
from django.utils.dateformat import DateFormat

# Create your views here.


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Pomain
    template_name = 'purchaseorder/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'purchaseorder/index_list.html'
    def get_queryset(self):
        query = Pomain.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(ponum__icontains=keysearch) |
                                 Q(podate__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch) |
                                 Q(postatus__icontains=keysearch))
        return query


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
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('pk')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('description')
        # context['prfmain'] = Prfmain.objects.filter(isdeleted=0, prfstatus='A', status='A',
        #                                             totalremainingquantity__gt=0)
        context['secretkey'] = generatekey(self)
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('pk')
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['pagetype'] = "create"

        closetransaction = Companyparameter.objects.all().first().last_closed_date
        validtransaction = closetransaction + relativedelta(months=1)
        context['validtransaction'] = validtransaction

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
            if self.request.POST['vat']:
                self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
            if self.request.POST['atc']:
                self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
            if self.request.POST['currency']:
                self.object.fxrate = Currency.objects.get(pk=self.request.POST['currency']).fxrate
            if self.request.POST['wtax']:
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
                    if self.request.POST.getlist('temp_branch')[i - 1]:
                        detail.branch = Branch.objects.filter(pk=self.request.POST.getlist('temp_branch')[i - 1],
                                                              isdeleted=0, status='A').first()
                    if self.request.POST.getlist('temp_department')[i - 1]:
                        detail.department = Department.objects.filter(pk=self.request.POST.
                                                                      getlist('temp_department')[i - 1], isdeleted=0).\
                            first()
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

                    # replaced the computed values with values provided by user on screens

                    # detail.vatamount = discountedAmount * (float(detail.vatrate) / 100)
                    # detail.netamount = discountedAmount + detail.vatamount
                    # detail.apvremainingamount = detail.netamount
                    #
                    # if detail.vatrate > 0:
                    #     detail.vatable = discountedAmount
                    #     detail.vatexempt = 0
                    #     detail.vatzerorated = 0
                    # elif detail.vat.code == "VE":
                    #     detail.vatable = 0
                    #     detail.vatexempt = discountedAmount
                    #     detail.vatzerorated = 0
                    # elif detail.vat.code == "ZE":
                    #     detail.vatable = 0
                    #     detail.vatexempt = 0
                    #     detail.vatzerorated = discountedAmount

                    detail.vatable = self.request.POST.getlist('hdn_tblVatable')[i - 1]
                    detail.vatexempt = self.request.POST.getlist('hdn_tblVatExempt')[i - 1]
                    detail.vatzerorated = self.request.POST.getlist('hdn_tblZeroRated')[i - 1]
                    detail.vatamount = self.request.POST.getlist('hdn_tblAddedVat')[i - 1]
                    detail.netamount = float(detail.vatable) + float(detail.vatexempt) + float(detail.vatzerorated) + float(detail.vatamount)

                    # replaced the computed values with values provided by user on screens

                    if self.request.POST['atc']:
                        detail.atc = Ataxcode.objects.get(pk=self.request.POST['atc'], isdeleted=0, status='A')
                        detail.atcrate = detail.atc.rate
                        detail.atcamount = self.request.POST.getlist('hdn_tblWTax')[i - 1]

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
                    detail.inputvattype = dt.inputvattype

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
                                                                                        Sum('quantity'),
                                                                                        Sum('atcamount'))

            Pomain.objects.filter(ponum=ponum, isdeleted=0, status='A').\
                update(discountamount=po_main_aggregates['discountamount__sum'],
                       grossamount=po_main_aggregates['grossamount__sum'],
                       netamount=po_main_aggregates['netamount__sum'], vatable=po_main_aggregates['vatable__sum'],
                       vatamount=po_main_aggregates['vatamount__sum'], vatexempt=po_main_aggregates['vatexempt__sum'],
                       vatzerorated=po_main_aggregates['vatzerorated__sum'],
                       totalamount=pomain_totalamount,
                       totalquantity=po_main_aggregates['quantity__sum'],
                       atcamount=po_main_aggregates['atcamount__sum'],
                       totalremainingamount=pomain_totalamount)
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
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('pk')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('description')
        context['postatus'] = Pomain.objects.get(pk=self.object.pk).get_postatus_display()
        context['prfimported'] = Podata.objects.filter(pomain=self.object.pk, isdeleted=0).exclude(prfmain=None)
        context['prfmain'] = Prfmain.objects.filter(isdeleted=0, prfstatus='A', status='A',
                                                    totalremainingquantity__gt=0)
        if self.request.POST.get('supplier', False):
            context['supplier'] = Supplier.objects.get(pk=self.request.POST['supplier'], isdeleted=0)
        elif self.object.supplier:
            context['supplier'] = Supplier.objects.get(pk=self.object.supplier.id, isdeleted=0)
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('code')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')

        detail = Podetail.objects.filter(isdeleted=0, pomain=self.object.pk).order_by('item_counter')
        context['editable'] = 'false' if Poapvtransaction.objects.filter(pomain=self.object.pk) else 'true'

        if self.object.postatus != 'A' or context['editable'] == 'true':
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
                detailtemp.inputvattype = d.inputvattype
                detailtemp.atc = d.atc
                detailtemp.atcrate = d.atcrate
                detailtemp.atcamount = d.atcamount
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
            if self.request.POST['vat']:
                self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
            if self.request.POST['atc']:
                self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
            if self.request.POST['currency']:
                self.object.fxrate = Currency.objects.get(pk=self.request.POST['currency']).fxrate
            if self.request.POST['wtax']:
                self.object.wtaxrate = Wtax.objects.get(pk=self.request.POST['wtax']).rate
            self.object.save()

            # if self.object.rfstatus == 'A':  the save line below will be used for APPROVED purchase orders
            #     self.object.save(update_fields=['particulars', 'modifyby', 'modifydate'])

            self.object.save(update_fields=['podate', 'potype', 'refnum', 'urgencytype', 'dateneeded',
                                            'supplier', 'inputvattype', 'deferredvat', 'creditterm', 'particulars',
                                            'creditterm', 'vat', 'atc', 'currency', 'deliverydate',
                                            'wtax', 'vatrate', 'atcrate', 'fxrate', 'wtaxrate'])

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
            discounttype = 0
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
                if self.request.POST.getlist('temp_branch')[i - 1]:
                    alldetail.branch = Branch.objects.filter(pk=self.request.POST.getlist('temp_branch')[i - 1],
                                                             isdeleted=0, status='A').first()
                if self.request.POST.getlist('temp_department')[i - 1]:
                    alldetail.department = Department.objects.filter(pk=self.request.POST.
                                                                     getlist('temp_department')[i - 1], isdeleted=0).\
                        first()
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

                # replaced the computed values with values provided by user on screens
                temp_grossUnitCost = 0
                temp_grossAmount = 0
                temp_discountAmt = 0
                temp_discountedAmount = 0
                temp_vatable = 0
                temp_vatExempt = 0
                temp_vatZeroRated = 0
                temp_totalPurchase = 0
                temp_addedVat = 0
                temp_totalAmount = 0
                temp_withholdingTaxAmount = 0

                # print alldetail.quantity
                # print alldetail.unitcost
                # print alldetail.discountrate
                # print alldetail.vat.rate
                if self.request.POST.getlist('temp_discounttype')[i - 1] == "rate":
                    discounttype = self.request.POST.getlist('temp_discountrate')[i - 1]
                else:
                    discounttype = 0


                # grossUnitCost = float(alldetail.unitcost) / (1 + (float(alldetail.vatrate) / 100))
                # alldetail.grossamount = grossUnitCost * float(alldetail.quantity)
                # alldetail.discountamount = alldetail.grossamount * float(alldetail.discountrate) / 100 if \
                #      self.request.POST.getlist('temp_discounttype')[i - 1] == "rate" else float(
                #      self.request.POST.getlist('temp_discountamount')[i - 1])
                # discountedAmount = alldetail.grossamount - alldetail.discountamount

                #temp_grossUnitCost = alldetail.unitcost / (1 + alldetail.vat.rate)
                #temp_grossAmount = temp_grossUnitCost * alldetail.quantity
                #temp_discountAmt = temp_discountType == "rate" ? temp_grossAmount * temp_discountRate / 100: temp_discountAmount
                # temp_discountedAmount = temp_grossAmount - temp_discountAmt(vat > 0) ? temp_vatable = temp_discountedAmount: (vatCode == 'VE') ? temp_vatExempt = temp_discountedAmount:(vatCode == 'ZE') ? temp_vatZeroRated = temp_discountedAmount: temp_discountedAmount
                # temp_totalPurchase = temp_discountedAmount
                # temp_addedVat = temp_totalPurchase * vat
                # temp_totalAmount = temp_totalPurchase + temp_addedVat
                # temp_withholdingTaxAmount = temp_vatable * atc

                alldetail.vatable = 0
                alldetail.vatexempt = 0
                alldetail.vatzerorated = 0
                alldetail.vatamount = 0
                alldetail.netamount = 0


                #alldetail.vatable = self.request.POST.getlist('hdn_tblVatable')[i - 1]
                #alldetail.vatexempt = self.request.POST.getlist('hdn_tblVatExempt')[i - 1]
                #alldetail.vatzerorated = self.request.POST.getlist('hdn_tblZeroRated')[i - 1]
                #alldetail.vatamount = self.request.POST.getlist('hdn_tblAddedVat')[i - 1]
                #alldetail.netamount = float(alldetail.vatable) + float(alldetail.vatexempt) + \
                                      #float(alldetail.vatzerorated) + float(alldetail.vatamount)

                if self.request.POST['atc']:
                    alldetail.atc = Ataxcode.objects.get(pk=self.request.POST['atc'], isdeleted=0, status='A')
                    alldetail.atcrate = alldetail.atc.rate
                    alldetail.atcamount = self.request.POST.getlist('hdn_tblWTax')[i - 1]

                # alldetail.vatamount = discountedAmount * (float(alldetail.vatrate) / 100)
                # alldetail.netamount = discountedAmount + alldetail.vatamount
                #
                # if alldetail.vatrate > 0:
                #     alldetail.vatable = discountedAmount
                #     alldetail.vatexempt = 0
                #     alldetail.vatzerorated = 0
                # elif alldetail.vat.code == "VE":
                #     alldetail.vatable = 0
                #     alldetail.vatexempt = discountedAmount
                #     alldetail.vatzerorated = 0
                # elif alldetail.vat.code == "ZE":
                #     alldetail.vatable = 0
                #     alldetail.vatexempt = 0
                #     alldetail.vatzerorated = discountedAmount
                #
                # if self.request.POST['atc']:
                #     alldetail.atc = Ataxcode.objects.get(pk=self.request.POST['atc'], isdeleted=0, status='A')
                #     alldetail.atcrate = alldetail.atc.rate
                #     alldetail.atcamount = alldetail.vatable * (float(alldetail.atcrate) / 100)

                # replaced the computed values with values provided by user on screens

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
                alldetail.inputvattype = atd.inputvattype

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
                                                                                          Sum('quantity'),
                                                                                          Sum('atcamount'))

            Pomain.objects.filter(pk=self.object.pk, isdeleted=0, status='A'). \
                update(discountamount=po_main_aggregates['discountamount__sum'],
                       grossamount=po_main_aggregates['grossamount__sum'],
                       netamount=po_main_aggregates['netamount__sum'], vatable=po_main_aggregates['vatable__sum'],
                       vatamount=po_main_aggregates['vatamount__sum'], vatexempt=po_main_aggregates['vatexempt__sum'],
                       vatzerorated=po_main_aggregates['vatzerorated__sum'],
                       totalamount=pomain_totalamount,
                       totalquantity=po_main_aggregates['quantity__sum'],
                       atcamount=po_main_aggregates['atcamount__sum'])
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
def fetchprfs(request):
    if request.method == 'POST':
        prf_data = Prfdetail.objects.filter(isdeleted=0, status='A', supplier=int(request.POST['supplier']),
                                            vat=int(request.POST['vat']), poremainingquantity__gt=0,
                                            prfmain__isdeleted=0, prfmain__prfstatus='A', prfmain__status='A').\
            values('prfmain', 'prfmain__prfnum', 'prfmain__prfdate', 'prfmain__urgencytype', 'prfmain__dateneeded',
                   'prfmain__actualapprover', 'prfmain__enterby').distinct(). \
            annotate(Sum('poremainingquantity')). \
            order_by('-prfmain', 'prfmain__prfnum', 'prfmain__prfdate', 'prfmain__urgencytype', 'prfmain__dateneeded',
                     'prfmain__actualapprover', 'prfmain__enterby')
        prf_data_list = []
        for data in prf_data:
            prf_data_list.append([data['prfmain'],
                                  data['prfmain__prfnum'],
                                  'Normal' if data['prfmain__urgencytype'] == 'N' else 'Rush' if data['prfmain__urgencytype'] == 'R' else '',
                                  data['prfmain__dateneeded'],
                                  User.objects.get(pk=int(data['prfmain__actualapprover'])).username,
                                  data['prfmain__prfdate'],
                                  User.objects.get(pk=int(data['prfmain__enterby'])).first_name + ' ' + User.objects.get(pk=int(data['prfmain__enterby'])).last_name,
                                  data['poremainingquantity__sum']
                                  ])
        data = {
            'prfs_for_import': prf_data_list,
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def fetchitems(request):
    if request.method == 'POST':
        prfdetail = Prfdetail.objects.filter(isdeleted=0, status='A', prfmain=int(request.POST['prfid']),
                                             supplier=int(request.POST['supplier']), vat=int(request.POST['vat']),
                                             poremainingquantity__gt=0, prfmain__isdeleted=0, prfmain__prfstatus='A',
                                             prfmain__status='A').order_by('item_counter')
        #
        #
        # prfmain = Prfmain.objects.get(pk=request.POST['prfid'],
        #                               prfstatus='A',
        #                               status='A',
        #                               isdeleted=0)
        #
        # prfdetail = Prfdetail.objects.filter(prfmain=prfmain, status='A', isdeleted=0, isfullypo=0)
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
        if request.POST['id_branch']:
            detailtemp.branch = Branch.objects.get(pk=request.POST['id_branch'])
        if request.POST['id_department']:
            detailtemp.department = Department.objects.get(pk=request.POST['id_department'])
        detailtemp.currency = Currency.objects.get(pk=request.POST['id_currency'])
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
        if request.POST['id_department']:
            detailtemp.department_code = Department.objects.get(pk=request.POST['id_department']).code
            detailtemp.department_name = Department.objects.get(pk=request.POST['id_department']).departmentname
        detailtemp.inputvattype = detailtemp.invitem.inventoryitemclass.inventoryitemtype.inputvattype
        if request.POST['id_atc']:
            detailtemp.atc = Ataxcode.objects.get(pk=request.POST['id_atc'])
            detailtemp.atcrate = request.POST['id_atcrate']
            detailtemp.atcamount = request.POST['id_atcamount']
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
                if prfitemdetails.supplier and request.POST['id_supplier']:
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
                detailtemp.inputvattype = detailtemp.invitem.inventoryitemclass.inventoryitemtype.inputvattype
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


# @change add report class and def
@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Pomain
    # @change template link
    template_name = 'purchaseorder/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        # context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        # context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0).order_by('description')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Prfmain
    # @change template link
    template_name = 'purchaseorder/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        # @change totals
        query, context['report_type'], context['report_totalgross'], context['report_totalnet'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        # @change default title
        context['rc_headtitle'] = "PURCHASE ORDER"
        context['rc_title'] = "PURCHASE ORDER"

        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''

    # @change totals
    report_totalgross = ''
    report_totalnet = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        # @change report title
        report_type = "PO Summary"

        # @change table for main
        query = Pomain.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(ponum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(ponum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(podate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(podate__lte=key_data)

        if request.COOKIES.get('rep_f_net_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_net_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(netamount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_net_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_net_amountto_' + request.resolver_match.app_name))
            query = query.filter(netamount__lte=float(key_data.replace(',', '')))

        if request.COOKIES.get('rep_f_postatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_postatus_' + request.resolver_match.app_name))
            query = query.filter(postatus=str(key_data))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)

        # @change amount format
        report_totalgross = query.aggregate(Sum('grossamount'))
        report_totalnet = query.aggregate(Sum('netamount'))
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        # @change report title
        report_type = "PO Detailed"

        # @change table for detailed
        query = Podetail.objects.all().filter(isdeleted=0).order_by('prfmain')

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(pomain__ponum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(pomain__ponum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(pomain__podate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(pomain__podate__lte=key_data)

        if request.COOKIES.get('rep_f_net_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_net_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(pomain__netamount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_net_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_net_amountto_' + request.resolver_match.app_name))
            query = query.filter(pomain__netamount__lte=float(key_data.replace(',', '')))

        if request.COOKIES.get('rep_f_postatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_postatus_' + request.resolver_match.app_name))
            query = query.filter(pomain__postatus=str(key_data))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                for n,data in enumerate(key_data):
                    key_data[n] = "pomain__" + data
                query = query.order_by(*key_data)

        # @change amount format
        report_total = query.values_list('pomain', flat=True).order_by('pomain').distinct()
        report_totalgross = Pomain.objects.filter(pk__in=report_total).aggregate(Sum('grossamount'))
        report_totalnet = Pomain.objects.filter(pk__in=report_total).aggregate(Sum('netamount'))

    if request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name):
        key_data = str(request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name))
        if key_data == 'd':
            query = query.reverse()

    # @change totals
    return query, report_type, report_totalgross, report_totalnet


@csrf_exempt
def reportresultxlsx(request):
    # imports and workbook config
    import xlsxwriter
    try:
        import cStringIO as StringIO
    except ImportError:
        import StringIO
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)

    # query and default variables
    queryset, report_type, report_totalgross, report_totalnet = reportresultquery(request)
    report_type = report_type if report_type != '' else 'PO Report'
    worksheet = workbook.add_worksheet(report_type)
    bold = workbook.add_format({'bold': 1})
    bold_right = workbook.add_format({'bold': 1, 'align': 'right'})
    bold_center = workbook.add_format({'bold': 1, 'align': 'center'})
    money_format = workbook.add_format({'num_format': '#,##0.00'})
    bold_money_format = workbook.add_format({'num_format': '#,##0.00', 'bold': 1})
    worksheet.set_column(1, 1, 15)
    row = 0
    data = []

    # config: placement
    amount_placement = 0
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        amount_placement = 6
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        amount_placement = 12

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'PO Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Ref No.', bold)
        worksheet.write('D1', 'PO Status', bold)
        worksheet.write('E1', 'Supplier', bold)
        worksheet.write('F1', 'Quantity', bold)
        worksheet.write('G1', 'Gross Amount', bold_right)
        worksheet.write('H1', 'Net Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.merge_range('A1:A2', 'PO Number', bold)
        worksheet.merge_range('B1:B2', 'Date', bold)
        worksheet.merge_range('C1:C2', 'Status', bold)
        worksheet.merge_range('D1:D2', 'Supplier', bold)
        worksheet.merge_range('E1:K1', 'PO Detail', bold_center)
        worksheet.merge_range('L1:L2', 'Total Quantity', bold)
        worksheet.merge_range('M1:M2', 'Total Gross', bold_right)
        worksheet.merge_range('N1:N2', 'Total Net', bold_right)
        worksheet.write('E2', 'Item', bold)
        worksheet.write('F2', 'Branch', bold)
        worksheet.write('G2', 'Department', bold)
        worksheet.write('H2', 'Item Cost', bold_right)
        worksheet.write('I2', 'Quantity', bold_right)
        worksheet.write('J2', 'Gross Amount', bold_right)
        worksheet.write('K2', 'Net Amount', bold_right)
        row += 1

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            data = [
                obj.ponum,
                DateFormat(obj.podate).format('Y-m-d'),
                obj.refnum,
                obj.get_postatus_display(),
                str(obj.supplier_code) + " - " + str(obj.supplier_name),
                obj.totalquantity,
                obj.grossamount,
                obj.netamount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            data = [
                obj.pomain.ponum,
                DateFormat(obj.pomain.podate).format('Y-m-d'),
                obj.pomain.get_postatus_display(),
                str(obj.pomain.supplier_code) + " - " + str(obj.pomain.supplier_name),
                obj.invitem_code + " - " + obj.invitem_name,
                obj.branch.code + " - " + obj.branch.description,
                obj.department.code + " - " + obj.department.departmentname,
                obj.unitcost,
                obj.quantity,
                obj.grossamount,
                obj.netamount,
                obj.pomain.totalquantity,
                obj.pomain.grossamount,
                obj.pomain.netamount,
            ]

        temp_amount_placement = amount_placement
        for col_num in xrange(len(data)):
            if col_num == temp_amount_placement:
                temp_amount_placement += 1
                worksheet.write_number(row, col_num, data[col_num], money_format)
            else:
                worksheet.write(row, col_num, data[col_num])

    # config: totals
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        data = [
            "", "", "", "", "",
            "Total", report_totalgross['grossamount__sum'], report_totalnet['netamount__sum'],
        ]
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        data = [
            "", "", "", "", "", "", "", "", "", "", "",
            "Total", report_totalgross['grossamount__sum'], report_totalnet['netamount__sum'],
        ]

    row += 1
    for col_num in xrange(len(data)):
        worksheet.write(row, col_num, data[col_num], bold_money_format)

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+report_type+".xlsx"
    return response


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Pomain
    template_name = 'purchaseorder/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(Pdf, self).get_context_data(**kwargs)
        context['pomain'] = Pomain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['detail'] = Podetail.objects.filter(pomain=self.kwargs['pk'], isdeleted=0, status='A').\
            order_by('item_counter')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')

        po_detail_aggregates = Podetail.objects.filter(pomain=self.kwargs['pk'], isdeleted=0, status='A').\
            aggregate(Sum('quantity'),
                      Sum('grossamount'),
                      Sum('discountamount'),
                      Sum('vatable'),
                      Sum('vatexempt'),
                      Sum('vatzerorated'),
                      Sum('vatamount'),
                      Sum('netamount'))
        context['detail_total_quantity'] = po_detail_aggregates['quantity__sum']
        context['detail_total_grossamount'] = po_detail_aggregates['grossamount__sum']
        context['detail_total_discountamount'] = po_detail_aggregates['discountamount__sum']
        context['detail_total_vatable'] = po_detail_aggregates['vatable__sum'] + po_detail_aggregates['vatexempt__sum'] + po_detail_aggregates['vatzerorated__sum']
        context['detail_total_vatamount'] = po_detail_aggregates['vatamount__sum']
        context['detail_total_netamount'] = po_detail_aggregates['netamount__sum']

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedpo = Pomain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedpo.print_ctr += 1
        printedpo.save()

        return context
