from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from . models import Prfmain
from requisitionform.models import Rfmain, Rfdetail
from purchaserequisitionform.models import Prfmain, Prfdetail, Prfdetailtemp, Rfprftransaction
from canvasssheet.models import Csmain, Csdetail, Csdata
from supplier.models import Supplier
from inventoryitemtype.models import Inventoryitemtype
from inventoryitem.models import Inventoryitem
from branch.models import Branch
from companyparameter.models import Companyparameter
from department.models import Department
from employee.models import Employee
from purchaseorder.models import Pomain
from unitofmeasure.models import Unitofmeasure
from currency.models import Currency
from vat.models import Vat
from budgetapproverlevels.models import Budgetapproverlevels
from django.contrib.auth.models import User
from django.db.models import Q, F, Sum
from acctentry.views import generatekey
from easy_pdf.views import PDFTemplateView
from utils.mixins import ReportContentMixin
from django.utils.dateformat import DateFormat
from dateutil.relativedelta import relativedelta
import datetime

from django.db import connection
from collections import namedtuple
# pagination and search
from endless_pagination.views import AjaxListView


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Prfmain
    template_name = 'purchaserequisitionform/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'purchaserequisitionform/index_list.html'
    def get_queryset(self):
        print self.request.user.has_perm('puchaserequisitionform.view_assignprf')
        print 'test'
        if self.request.user.has_perm('purchaserequisitionform.view_assignprf') and not self.request.user.has_perm(
                'purchaserequisitionform.view_allassignprf'):
            # print self.request.user.id
            user_employee = get_object_or_None(Employee, user_id=self.request.user.id)
            # print 'hey'
            if user_employee is not None:
                query = Prfmain.objects.filter(designatedapprover_id=self.request.user.id) | Prfmain.objects.filter(
                    enterby=self.request.user.id)
                query = query.filter(isdeleted=0)

            else:
                query = Prfmain.objects.all().filter(isdeleted=0)
        else:
            if self.request.user.has_perm('purchaserequisitionform.view_assignprf'):
                query = Prfmain.objects.all().filter(isdeleted=0)
            else:
                query = Prfmain.objects.all().filter(isdeleted=0, enterby=self.request.user.id)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(rfnum__icontains=keysearch) |
                                 Q(rfdate__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch))

        # query = Prfmain.objects.all().filter(isdeleted=0)
        # if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
        #     keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
        #     query = query.filter(Q(prfnum__icontains=keysearch) |
        #                          Q(prfdate__icontains=keysearch) |
        #                          Q(particulars__icontains=keysearch))
        return query


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Prfmain
    template_name = 'purchaserequisitionform/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['prfdetail'] = Prfdetail.objects.filter(isdeleted=0, prfmain=self.kwargs['pk']).order_by('item_counter')
        context['totalamount'] = Prfdetail.objects.filter(isdeleted=0, prfmain=self.kwargs['pk']).aggregate(Sum('amount'))
        context['totalpoquantity'] = Prfmain.objects.get(pk=self.kwargs['pk']).\
                                        totalquantity - Prfmain.objects.\
                                        get(pk=self.kwargs['pk']).totalremainingquantity
        pos = Pomain.objects.raw('SELECT DISTINCT prfm.prfnum, pom.ponum, pom.id, pom.postatus, pom.modifydate '
                                 'FROM podetail pod LEFT JOIN prfdetail prfd ON pod.prfdetail_id = prfd.id '
                                 'LEFT JOIN prfmain prfm ON prfd.prfmain_id = prfm.id '
                                 'LEFT JOIN pomain pom ON pod.pomain_id = pom.id '
                                 'WHERE prfm.prfnum = ' + self.object.prfnum + ' AND pom.isdeleted = 0 '
                                                                               'ORDER BY pom.modifydate')

        context['pos'] = []
        for data in pos:
            context['pos'].append([data.ponum,
                                   data.postatus,
                                   data.modifydate,
                                   data.id])
        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Prfmain
    template_name = 'purchaserequisitionform/create.html'
    fields = ['prfdate', 'inventoryitemtype', 'designatedapprover', 'prftype', 'particulars', 'branch', 'urgencytype', 'dateneeded']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('purchaserequisitionform.add_prfmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0)
        context['branch'] = Branch.objects.filter(isdeleted=0)
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('inventoryitemclass__inventoryitemtype__code', 'description')
        context['rfmain'] = Rfmain.objects.filter(isdeleted=0, rfstatus='A', status='A')
        context['currency'] = Currency.objects.filter(isdeleted=0, status='A').order_by('id')
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('code')
        managers = Employee.objects.filter(managementlevel=6).values_list('user_id', flat=True)
        context['designatedapprover'] = User.objects.filter(id__in=managers, is_active=1).exclude(username='admin').order_by('first_name')
        context['totalremainingquantity'] = 0

        closetransaction = Companyparameter.objects.all().first().last_closed_date
        validtransaction = closetransaction + relativedelta(months=1)
        context['validtransaction'] = validtransaction

        return context

    def form_valid(self, form):
        if Prfdetailtemp.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0):
            self.object = form.save(commit=False)

            year = str(form.cleaned_data['prfdate'].year)
            yearQS = Prfmain.objects.filter(prfnum__startswith=year)

            prfnumlast = lastNumber('true')
            latestprfnum = str(prfnumlast[0])

            prfnum = year
            last = str(int(latestprfnum) + 1)

            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                prfnum += '0'
            prfnum += last

            self.object.prfnum = prfnum
            self.object.branch = Branch.objects.get(pk=5)  # head office
            self.object.quantity = 0
            self.object.enterby = self.request.user
            self.object.modifyby = self.request.user
            self.object.save()

            itemquantity = 0
            detailtemp = Prfdetailtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).order_by('enterdate')
            prfmain = Prfmain.objects.get(prfnum=prfnum)
            i = 1

            # delete and update of prfdetailtemp and prfdetail (respectively)
            total_amount = 0
            for dt in detailtemp:
                total_amount = total_amount + (float(self.request.POST.getlist('temp_amount')[i-1]) * float(self.request.POST.getlist('temp_quantity')[i-1]))
                department = Department.objects.get(pk=self.request.POST.getlist('temp_department')[i-1], isdeleted=0)

                detail = Prfdetail()
                detail.item_counter = i
                detail.prfmain = prfmain
                detail.invitem_code = dt.invitem_code
                detail.invitem_name = dt.invitem_name
                detail.invitem_unitofmeasure = Unitofmeasure.objects.get(code=self.request.POST.getlist('temp_item_um')[i-1], isdeleted=0, status='A')
                detail.invitem_unitofmeasure_code = Unitofmeasure.objects.get(code=self.request.POST.getlist('temp_item_um')[i-1], isdeleted=0, status='A').code
                detail.quantity = self.request.POST.getlist('temp_quantity')[i-1]
                detail.amount = self.request.POST.getlist('temp_amount')[i-1]
                detail.department = Department.objects.get(pk=self.request.POST.getlist('temp_department')[i-1])
                detail.department_code = department.code
                detail.department_name = department.departmentname
                detail.remarks = self.request.POST.getlist('temp_remarks')[i-1]
                detail.currency = Currency.objects.get(pk=self.request.POST.getlist('temp_item_currency')[i-1])
                detail.fxrate = self.request.POST.getlist('temp_fxrate')[i-1]
                detail.status = dt.status
                detail.enterby = dt.enterby
                detail.enterdate = dt.enterdate
                detail.modifyby = dt.modifyby
                detail.modifydate = dt.modifydate
                detail.postby = dt.postby
                detail.postdate = dt.postdate
                detail.isdeleted = dt.isdeleted
                detail.invitem = dt.invitem
                detail.rfmain = dt.rfmain
                detail.rfdetail = dt.rfdetail
                detail.poremainingquantity = self.request.POST.getlist('temp_quantity')[i-1]
                detail.save()
                dt.delete()

                if dt.rfmain:
                    if addRfprftransactionitem(detail.id):
                        itemquantity = int(itemquantity) + int(detail.quantity)
                    else:
                        detail.delete()
                else:
                    itemquantity = int(itemquantity) + int(detail.quantity)

                i += 1

            prfmain.quantity = int(itemquantity)
            prfmain.totalquantity = int(itemquantity)
            prfmain.totalremainingquantity = int(itemquantity)
            prfmain.netamount = total_amount

            prfmain.approverlevel_required = 1

            approverreached = Budgetapproverlevels.objects.filter(expwithinbudget__lte=total_amount).order_by('-level').first()

            if approverreached:
                prfmain.approverlevel_required = approverreached.level + (1 if total_amount > approverreached.expwithinbudget else 0)

            prfmain.save()

            return HttpResponseRedirect('/purchaserequisitionform/' + str(self.object.id) + '/update/')


def addRfprftransactionitem(id):
    prfdetail = Prfdetail.objects.get(pk=id)

    # validate quantity
    # print prfdetail.quantity
    # print prfdetail.rfdetail.prfremainingquantity
    # print prfdetail.rfdetail.isfullyprf
    if prfdetail.quantity <= prfdetail.rfdetail.prfremainingquantity and prfdetail.rfdetail.isfullyprf == 0:
        data = Rfprftransaction()
        data.rfmain = prfdetail.rfmain
        data.rfdetail = prfdetail.rfdetail
        data.prfmain = Prfdetail.objects.get(pk=id).prfmain
        data.prfdetail = Prfdetail.objects.get(pk=id)
        data.prfquantity = Prfdetail.objects.get(pk=id).quantity
        data.save()

        # adjust rf detail
        newprftotalquantity = prfdetail.rfdetail.prftotalquantity + data.prfquantity
        newprfremainingquantity = prfdetail.rfdetail.prfremainingquantity - data.prfquantity
        if newprfremainingquantity == 0:
            isfullyprf = 1
        else:
            isfullyprf = 0

        Rfdetail.objects.filter(pk=data.rfdetail.id).update(prftotalquantity=newprftotalquantity,
                                                            prfremainingquantity=newprfremainingquantity,
                                                            isfullyprf=isfullyprf)

        # adjust rf main
        rfmain_prfquantity = Rfmain.objects.get(pk=data.rfmain.id)
        newtotalremainingquantity = rfmain_prfquantity.totalremainingquantity - data.prfquantity
        Rfmain.objects.filter(pk=data.rfmain.id).update(totalremainingquantity=newtotalremainingquantity)

        return True

    else:
        return False


def deleteRfprftransactionitem(prfdetail):
    data = Rfprftransaction.objects.get(prfdetail=prfdetail.id, status='A')
    # update rfdetail
    remainingquantity = prfdetail.rfdetail.prfremainingquantity + data.prfquantity
    isfullyprf = 0 if remainingquantity != 0 else 1
    Rfdetail.objects.filter(pk=data.rfdetail.id).update(prftotalquantity=F('prftotalquantity')-data.prfquantity,
                                                        prfremainingquantity=F('prfremainingquantity')+data.prfquantity,
                                                        isfullyprf=isfullyprf)

    # update rfmain
    Rfmain.objects.filter(pk=data.rfmain.id).update(totalremainingquantity=F('totalremainingquantity')+data.prfquantity)

    # delete rfprftransaction, prfdetail
    data.delete()
    Prfdetail.objects.filter(pk=prfdetail.id).delete()
    Prfmain.objects.filter(pk=prfdetail.prfmain.id).update(quantity=0, grossamount=0.00,
                                                           netamount=0.00, vatable=0.00, vatamount=0.00,
                                                           vatexempt=0.00, vatzerorated=0.00)


class UpdateView(UpdateView):
    model = Prfmain
    template_name = 'purchaserequisitionform/edit.html'
    fields = ['prfnum', 'prfdate', 'inventoryitemtype', 'designatedapprover', 'prftype', 'particulars', 'branch', 'urgencytype', 'dateneeded']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('purchaserequisitionform.change_prfmain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0)
        context['branch'] = Branch.objects.filter(isdeleted=0)
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('inventoryitemclass__inventoryitemtype__code', 'description')
        context['rfmain'] = Rfmain.objects.filter(isdeleted=0, rfstatus='A', status='A')
        context['currency'] = Currency.objects.filter(isdeleted=0, status='A')
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('code')
        context['prfstatus'] = Prfmain.objects.get(pk=self.object.pk).get_prfstatus_display()
        managers = Employee.objects.filter(managementlevel=6).values_list('user_id', flat=True)
        context['designatedapprover'] = User.objects.filter(id__in=managers, is_active=1).exclude(username='admin').order_by('first_name')
        context['totalremainingquantity'] = Prfmain.objects.get(pk=self.object.pk).\
            totalremainingquantity

        pos = Pomain.objects.raw('SELECT DISTINCT prfm.prfnum, pom.ponum, pom.id, pom.postatus, pom.modifydate '
                                 'FROM podetail pod LEFT JOIN prfdetail prfd ON pod.prfdetail_id = prfd.id '
                                 'LEFT JOIN prfmain prfm ON prfd.prfmain_id = prfm.id '
                                 'LEFT JOIN pomain pom ON pod.pomain_id = pom.id '
                                 'WHERE prfm.prfnum = ' + self.object.prfnum + ' AND pom.isdeleted = 0 '
                                                                               'ORDER BY pom.modifydate')

        context['pos'] = []
        for data in pos:
            context['pos'].append([data.ponum,
                                   data.postatus,
                                   data.modifydate,
                                   data.id])

        Prfdetailtemp.objects.filter(prfmain=self.object.pk).delete()        # clear all temp data

        detail = Prfdetail.objects.filter(isdeleted=0, prfmain=self.object.pk).order_by('item_counter')
        for d in detail:
            detailtemp = Prfdetailtemp()
            detailtemp.invitem_code = d.invitem_code
            detailtemp.invitem_name = d.invitem_name
            detailtemp.invitem_unitofmeasure = d.invitem_unitofmeasure
            detailtemp.invitem_unitofmeasure_code = d.invitem_unitofmeasure_code
            detailtemp.item_counter = d.item_counter
            detailtemp.quantity = d.quantity
            detailtemp.amount = d.amount
            detailtemp.department = d.department
            detailtemp.department_code = d.department_code
            detailtemp.department_name = d.department_name
            detailtemp.remarks = d.remarks
            detailtemp.currency = d.currency
            detailtemp.fxrate = d.fxrate
            detailtemp.status = d.status
            detailtemp.enterdate = d.enterdate
            detailtemp.modifydate = d.modifydate
            detailtemp.enterby = d.enterby
            detailtemp.modifyby = d.modifyby
            detailtemp.isdeleted = d.isdeleted
            detailtemp.postby = d.postby
            detailtemp.postdate = d.postdate
            detailtemp.invitem = d.invitem
            detailtemp.prfmain = d.prfmain
            detailtemp.rfmain = d.rfmain
            detailtemp.rfdetail = d.rfdetail
            detailtemp.isfullypo = d.isfullypo
            detailtemp.pototalquantity = d.pototalquantity
            detailtemp.poremainingquantity = d.poremainingquantity
            detailtemp.save()

        context['prfdetailtemp'] = Prfdetailtemp.objects.filter(isdeleted=0, prfmain=self.object.pk).order_by('item_counter')
        context['amount'] = []

        for data in context['prfdetailtemp']:
            amount = float(data.quantity) * float(data.invitem.unitcost)
            context['amount'].append(amount)

        context['data'] = zip(context['prfdetailtemp'], context['amount'])

        return context

    def form_valid(self, form):
        if Prfdetailtemp.objects.filter(Q(isdeleted=0), Q(prfmain=self.object.pk) | Q(secretkey=self.request.POST['secretkey'])):
            self.object = form.save(commit=False)
            self.object.branch = Branch.objects.get(pk=5)  # head office

            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()

            if self.object.prfstatus == 'A' or self.object.approverlevelbudget_response is not None:
                self.object.save(update_fields=['particulars', 'modifyby', 'modifydate'])
            else:
                self.object.save(update_fields=['prfdate', 'inventoryitemtype', 'prftype', 'urgencytype',
                                            'dateneeded', 'branch', 'particulars', 'designatedapprover',
                                            'modifyby', 'modifydate'])

                Prfdetailtemp.objects.filter(isdeleted=1, prfmain=self.object.pk).delete()

                detailtagasdeleted = Prfdetail.objects.filter(prfmain=self.object.pk)
                for dtd in detailtagasdeleted:
                    dtd.isdeleted = 1
                    dtd.save()

                alltempdetail = Prfdetailtemp.objects.filter(
                    Q(isdeleted=0),
                    Q(prfmain=self.object.pk) | Q(secretkey=self.request.POST['secretkey'])
                ).order_by('enterdate')

                # remove old detail in rfquantities
                prfdetail = Prfdetail.objects.filter(prfmain=self.object.id, isdeleted=1)
                for data in prfdetail:
                    if Rfprftransaction.objects.filter(prfdetail=data.id):
                        deleteRfprftransactionitem(data)
                Prfdetail.objects.filter(prfmain=self.object.pk, isdeleted=1).delete()

                itemquantity = 0
                prfmain = Prfmain.objects.get(pk=self.object.pk)
                i = 1
                total_amount = 0
                for atd in alltempdetail:
                    total_amount = total_amount + (float(self.request.POST.getlist('temp_amount')[i-1]) * float(self.request.POST.getlist('temp_quantity')[i-1]))
                    department = Department.objects.get(pk=self.request.POST.getlist('temp_department')[i-1], isdeleted=0)

                    alldetail = Prfdetail()
                    alldetail.item_counter = i
                    alldetail.prfmain = Prfmain.objects.get(prfnum=self.request.POST['prfnum'])
                    alldetail.invitem = atd.invitem
                    alldetail.invitem_code = atd.invitem_code
                    alldetail.invitem_name = atd.invitem_name
                    alldetail.invitem_unitofmeasure = Unitofmeasure.objects.get(code=self.request.POST.getlist('temp_item_um')[i-1], isdeleted=0, status='A')
                    alldetail.invitem_unitofmeasure_code = Unitofmeasure.objects.get(code=self.request.POST.getlist('temp_item_um')[i-1], isdeleted=0, status='A').code
                    alldetail.quantity = self.request.POST.getlist('temp_quantity')[i-1]
                    alldetail.amount = self.request.POST.getlist('temp_amount')[i-1]
                    alldetail.department = Department.objects.get(pk=self.request.POST.getlist('temp_department')[i-1])
                    alldetail.department_code = department.code
                    alldetail.department_name = department.departmentname
                    alldetail.remarks = self.request.POST.getlist('temp_remarks')[i-1]
                    alldetail.currency = Currency.objects.get(pk=self.request.POST.getlist('temp_item_currency')[i-1])
                    alldetail.fxrate = self.request.POST.getlist('temp_fxrate')[i-1]
                    alldetail.status = atd.status
                    alldetail.enterby = atd.enterby
                    alldetail.enterdate = atd.enterdate
                    alldetail.modifyby = atd.modifyby
                    alldetail.modifydate = atd.modifydate
                    alldetail.postby = atd.postby
                    alldetail.postdate = atd.postdate
                    alldetail.isdeleted = atd.isdeleted
                    alldetail.rfmain = atd.rfmain
                    alldetail.rfdetail = atd.rfdetail
                    alldetail.poremainingquantity = self.request.POST.getlist('temp_quantity')[i-1]
                    alldetail.save()
                    atd.delete()

                    if atd.rfmain:
                        if addRfprftransactionitem(alldetail.id):
                            itemquantity = int(itemquantity) + int(alldetail.quantity)
                        else:
                            alldetail.delete()
                    else:
                        itemquantity = int(itemquantity) + int(alldetail.quantity)

                    i += 1

                prfmain.quantity = int(itemquantity)
                prfmain.totalquantity = int(itemquantity)
                prfmain.totalremainingquantity = int(itemquantity)
                prfmain.netamount = total_amount

                if Budgetapproverlevels.objects.order_by('level').first().expwithinbudget > total_amount:
                    approver = Budgetapproverlevels.objects.order_by('level').first()
                else:
                    approver = Budgetapproverlevels.objects.filter(expwithinbudget__lte=total_amount).order_by('-level').first()
                    
                approverlevel = approver.level
                approverbudget = approver.expwithinbudget

                prfmain.approverlevel_required = approverlevel \
                                                 + (1 if total_amount > approverbudget else 0) \
                                                 + (1 if prfmain.approverlevelbudget_response == 'D' else 0)

                prfmain.save()

            Prfdetailtemp.objects.filter(prfmain=self.object.pk).delete()

            return HttpResponseRedirect('/purchaserequisitionform/' + str(self.object.id) + '/update/')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Prfmain
    template_name = 'purchaserequisitionform/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('purchaserequisitionform.delete_prfmain') or \
                        self.object.status == 'O' or \
                        self.object.prfstatus == 'A' or \
                        self.object.approverlevelbudget_response is not None:
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.prfstatus = 'D'
        self.object.save()

        prfdetail = Prfdetail.objects.filter(prfmain=self.object.id)
        for data in prfdetail:
            deleteRfprftransactionitem(data)

        return HttpResponseRedirect('/purchaserequisitionform')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Rfmain
    template_name = 'purchaserequisitionform/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(Pdf, self).get_context_data(**kwargs)
        context['prfmain'] = Prfmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['detail'] = Prfdetail.objects.filter(prfmain=self.kwargs['pk'], isdeleted=0, status='A').\
            order_by('item_counter')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')

        prf_detail_aggregate = Prfdetail.objects.filter(prfmain=self.kwargs['pk'], isdeleted=0, status='A').\
            aggregate(Sum('quantity'), Sum('amount'))
        context['detail_total_quantity'] = prf_detail_aggregate['quantity__sum']
        context['detail_total_amount'] = prf_detail_aggregate['amount__sum']

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedprf = Prfmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedprf.print_ctr += 1
        printedprf.save()

        return context


@csrf_exempt
def importItems(request):
    if request.method == 'POST':
        rfdetail = Rfdetail.objects\
                        .raw('SELECT inv.unitcost, '
                                    'inv.id AS inv_id, '
                                    'rfm.rfnum, '
                                    'rfm.department_id, '
                                    'rfm.id AS rfm_id, '
                                    'rfd.invitem_code, '
                                    'rfd.invitem_name, '
                                    'rfd.quantity, '
                                    'rfd.remarks, '
                                    'rfd.invitem_unitofmeasure_id AS um_id, '
                                    'rfd.invitem_unitofmeasure_code AS um_code, '
                                    'rfd.id, '
                                    'rfd.isfullyprf, '
                                    'rfd.prfremainingquantity, '
                                    'um.code '
                            'FROM rfmain rfm '
                            'LEFT JOIN rfdetail rfd '
                            'ON rfd.rfmain_id = rfm.id '
                            'LEFT JOIN inventoryitem inv '
                            'ON inv.id = rfd.invitem_id '
                            'LEFT JOIN unitofmeasure um '
                            'ON um.id = inv.unitofmeasure_id '
                            'WHERE '
                                'rfd.rfmain_id = ' + request.POST['rfnum'] + ' AND '
                                'rfm.rfstatus = "A" AND '
                                'rfm.status = "A" AND '
                                'rfm.isdeleted = 0 AND '
                                'rfd.status = "A" AND '
                                'rfd.isdeleted = 0 AND '
                                'inv.status = "A"'
                            'ORDER BY rfd.item_counter')

        prfdata = []

        item_counter = int(request.POST['itemno'])

        for data in rfdetail:
            if data.isfullyprf != 1 and data.prfremainingquantity > 0:
                prfdata.append([data.invitem_code,
                                data.invitem_name,
                                data.code,
                                data.rfnum,
                                data.remarks,
                                data.quantity,
                                data.unitcost,
                                data.id,
                                item_counter,
                                data.um_code,
                                data.prfremainingquantity,
                                data.department_id])

                department = Department.objects.get(pk=data.department_id, isdeleted=0)

                detailtemp = Prfdetailtemp()
                detailtemp.invitem_code = data.invitem_code
                detailtemp.invitem_name = data.invitem_name
                detailtemp.invitem_unitofmeasure = Unitofmeasure.objects.get(pk=data.um_id)
                detailtemp.invitem_unitofmeasure_code = data.um_code
                detailtemp.item_counter = item_counter
                detailtemp.quantity = data.quantity
                detailtemp.department_code = department.code
                detailtemp.department_name = department.departmentname
                detailtemp.department = Department.objects.get(pk=data.department_id)
                detailtemp.remarks = data.remarks
                detailtemp.currency = Currency.objects.get(pk=1)
                detailtemp.status = 'A'
                detailtemp.enterdate = datetime.datetime.now()
                detailtemp.modifydate = datetime.datetime.now()
                detailtemp.enterby = request.user
                detailtemp.modifyby = request.user
                detailtemp.secretkey = request.POST['secretkey']
                detailtemp.invitem = Inventoryitem.objects.get(pk=data.inv_id)
                detailtemp.rfmain = Rfmain.objects.get(pk=data.rfm_id)
                detailtemp.rfdetail = Rfdetail.objects.get(pk=data.id)
                detailtemp.save()

                item_counter += 1

        data = {
            'status': 'success',
            'prfdata': prfdata,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def savedetailtemp(request):
    if request.method == 'POST':
        invdetail = Inventoryitem.objects\
                        .raw('SELECT inv.unitcost, '
                                    'inv.code, '
                                    'inv.description, '
                                    'inv.id, inv.unitofmeasure_id, '
                                    'um.code AS um_code '
                            'FROM inventoryitem inv '
                            'LEFT JOIN unitofmeasure um '
                            'ON um.id = inv.unitofmeasure_id '
                            'WHERE '
                                'inv.status = "A" AND '
                                'inv.id = ' + request.POST['inv_id'])

        for data in invdetail:
            x = Inventoryitem.objects.get(pk=request.POST['inv_id'])

            prfdata = [data.code,
                       data.description,
                       data.um_code,
                       data.unitcost,
                       data.id,
                       data.unitofmeasure_id]

            department = Department.objects.get(pk=request.POST['department'], isdeleted=0)



            detailtemp = Prfdetailtemp()
            detailtemp.invitem_code = data.code
            detailtemp.invitem_name = data.description
            detailtemp.item_counter = request.POST['itemno']
            detailtemp.quantity = request.POST['quantity']
            detailtemp.department_code = department.code
            detailtemp.department_name = department.departmentname
            detailtemp.department = Department.objects.get(pk=request.POST['department'])
            detailtemp.remarks = request.POST['remarks']
            detailtemp.invitem_unitofmeasure = x.unitofmeasure
            detailtemp.invitem_unitofmeasure_code = x.unitofmeasure.code
            detailtemp.currency = Currency.objects.get(pk=request.POST['currency'], isdeleted=0, status='A')
            detailtemp.status = 'A'
            detailtemp.enterdate = datetime.datetime.now()
            detailtemp.modifydate = datetime.datetime.now()
            detailtemp.enterby = request.user
            detailtemp.modifyby = request.user
            detailtemp.secretkey = request.POST['secretkey']
            detailtemp.invitem = Inventoryitem.objects.get(pk=request.POST['inv_id'], status='A')
            detailtemp.save()

        data = {
            'status': 'success',
            'prfdata': prfdata,
            'remarks': request.POST['remarks'],
            'currency': Currency.objects.get(pk=request.POST['currency']).symbol,
            'itemno': request.POST['itemno'],
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
            detailtemp = Prfdetailtemp.objects.get(item_counter=request.POST['itemno'], secretkey=request.POST['secretkey'], prfmain=None)
            detailtemp.delete()
        except Prfdetailtemp.DoesNotExist:
            detailtemp = Prfdetailtemp.objects.get(item_counter=request.POST['itemno'], prfmain__prfnum=request.POST['prfnum'])
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


def updateTransaction(pk, status):
    csdata = Csdata.objects.exclude(csmain=None).get(prfmain=pk, isdeleted=0)
    if csdata and Csmain.objects.get(pk=csdata.csmain.pk, status='A', isdeleted=0):

        if status == 'A':

            prfdetail = Prfdetail.objects.filter(prfmain=pk, isdeleted=0)

            for data in prfdetail:
                csdetail = Csdetail.objects.filter(csmain=csdata.csmain.pk,
                                                csstatus=1,
                                                prfdetail=data.pk,
                                                status='A',
                                                isdeleted=0).first()

                if csdetail:
                    data.negocost = csdetail.negocost
                    data.vat = Vat.objects.get(pk=csdetail.vat.pk)
                    data.vatable = csdetail.vatable
                    data.vatexempt = csdetail.vatexempt
                    data.vatzerorated = csdetail.vatzerorated
                    data.grosscost = csdetail.grosscost
                    data.grossamount = csdetail.grossamount
                    data.vatamount = csdetail.vatamount
                    data.netamount = csdetail.netamount
                    data.uc_cost = csdetail.unitcost
                    data.uc_vatable = csdetail.uc_vatable
                    data.uc_vatexempt = csdetail.uc_vatexempt
                    data.uc_vatzerorated = csdetail.uc_vatzerorated
                    data.uc_grosscost = csdetail.uc_grosscost
                    data.uc_grossamount = csdetail.uc_grossamount
                    data.uc_vatamount = csdetail.uc_vatamount
                    data.uc_netamount = csdetail.uc_netamount

                    data.csmain = Csmain.objects.get(pk=csdata.csmain.pk).pk
                    data.csdetail = Csdetail.objects.get(pk=csdetail.pk).pk
                    data.csnum = csdata.csmain.csnum
                    data.csdate = csdata.csmain.csdate

                    data.supplier = Supplier.objects.get(pk=csdetail.supplier.pk)
                    data.suppliercode = csdetail.supplier.code
                    data.suppliername = csdetail.supplier.name
                    data.estimateddateofdelivery = csdetail.estimateddateofdelivery
                    data.save()

            data = Csdetail.objects.filter(csmain=csdata.csmain.pk,
                                           csstatus=1,
                                           prfmain=pk,
                                           status='A',
                                           isdeleted=0).aggregate(Sum('negocost'),
                                                                  Sum('vatable'),
                                                                  Sum('vatexempt'),
                                                                  Sum('vatzerorated'),
                                                                  Sum('grosscost'),
                                                                  Sum('grossamount'),
                                                                  Sum('vatamount'),
                                                                  Sum('netamount'),
                                                                  Sum('unitcost'),
                                                                  Sum('uc_vatable'),
                                                                  Sum('uc_vatexempt'),
                                                                  Sum('uc_vatzerorated'),
                                                                  Sum('uc_grosscost'),
                                                                  Sum('uc_grossamount'),
                                                                  Sum('uc_vatamount'),
                                                                  Sum('uc_netamount'))
            Prfmain.objects.filter(pk=pk,
                                   prfstatus='A',
                                   isdeleted=0).update(negocost=data['negocost__sum'],
                                                       vatable=data['vatable__sum'],
                                                       vatexempt=data['vatexempt__sum'],
                                                       vatzerorated=data['vatzerorated__sum'],
                                                       grosscost=data['grosscost__sum'],
                                                       grossamount=data['grossamount__sum'],
                                                       vatamount=data['vatamount__sum'],
                                                       netamount=data['netamount__sum'],
                                                       uc_cost=data['unitcost__sum'],
                                                       uc_vatable=data['uc_vatable__sum'],
                                                       uc_vatexempt=data['uc_vatexempt__sum'],
                                                       uc_vatzerorated=data['uc_vatzerorated__sum'],
                                                       uc_grosscost=data['uc_grosscost__sum'],
                                                       uc_grossamount=data['uc_grossamount__sum'],
                                                       uc_vatamount=data['uc_vatamount__sum'],
                                                       uc_netamount=data['uc_netamount__sum'])

        elif status == 'D':

            prfdetail = Prfdetail.objects.filter(prfmain=pk, isdeleted=0)

            for data in prfdetail:
                csdetail = Csdetail.objects.filter(csmain=csdata.csmain.pk,
                                                csstatus=1,
                                                prfdetail=data.pk,
                                                status='A',
                                                isdeleted=0).first()

                if csdetail:
                    data.negocost = 0
                    data.vat = None
                    data.vatable = 0
                    data.vatexempt = 0
                    data.vatzerorated = 0
                    data.grosscost = 0
                    data.grossamount = 0
                    data.vatamount = 0
                    data.netamount = 0
                    data.uc_cost = 0
                    data.uc_vatable = 0
                    data.uc_vatexempt = 0
                    data.uc_vatzerorated = 0
                    data.uc_grosscost = 0
                    data.uc_grossamount = 0
                    data.uc_vatamount = 0
                    data.uc_netamount = 0

                    data.csmain = None
                    data.csdetail = None
                    data.csnum = None
                    data.csdate = None

                    data.supplier = None
                    data.suppliercode = None
                    data.suppliername = None
                    data.estimateddateofdelivery = None
                    data.save()

            Prfmain.objects.filter(pk=pk,
                                   prfstatus='A',
                                   isdeleted=0).update(vatable=0, vatexempt=0, vatzerorated=0, grosscost=0,
                                                       grossamount=0, vatamount=0, netamount=0, uc_vatable=0,
                                                       uc_vatexempt=0, uc_vatzerorated=0, uc_grosscost=0,
                                                       uc_grossamount=0, uc_vatamount=0, uc_netamount=0)


def comments():
    print 123
    # handle cs getting vat total with different currency
    # update import select behind modal
    # quantity cost front end change
    # delete item prompt
    # delete prfmain prompt
    # handle bloating in prfdetailtemp


# @change add report class and def
@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Prfmain
    # @change template link
    template_name = 'purchaserequisitionform/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0).order_by('description')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Prfmain
    # @change template link
    template_name = 'purchaserequisitionform/reportresult.html'

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
        context['rc_headtitle'] = "PURCHASE REQUISITION FORM"
        context['rc_title'] = "PURCHASE REQUISITION FORM"

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
        report_type = "PRF Summary"

        # @change table for main
        query = Prfmain.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(prfnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(prfnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(prfdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(prfdate__lte=key_data)

        if request.COOKIES.get('rep_f_net_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_net_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(netamount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_net_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_net_amountto_' + request.resolver_match.app_name))
            query = query.filter(netamount__lte=float(key_data.replace(',', '')))

        if request.COOKIES.get('rep_f_prfstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_prfstatus_' + request.resolver_match.app_name))
            query = query.filter(prfstatus=str(key_data))
        if request.COOKIES.get('rep_f_inventoryitemtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inventoryitemtype_' + request.resolver_match.app_name))
            query = query.filter(inventoryitemtype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(branch=int(key_data))

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
        report_type = "PRF Detailed"

        # @change table for detailed
        query = Prfdetail.objects.all().filter(isdeleted=0).order_by('prfmain')

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(prfmain__prfnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(prfmain__prfnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(prfmain__prfdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(prfmain__prfdate__lte=key_data)

        if request.COOKIES.get('rep_f_net_amountfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_net_amountfrom_' + request.resolver_match.app_name))
            query = query.filter(prfmain__netamount__gte=float(key_data.replace(',', '')))
        if request.COOKIES.get('rep_f_net_amountto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_net_amountto_' + request.resolver_match.app_name))
            query = query.filter(prfmain__netamount__lte=float(key_data.replace(',', '')))

        if request.COOKIES.get('rep_f_prfstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_prfstatus_' + request.resolver_match.app_name))
            query = query.filter(prfmain__prfstatus=str(key_data))
        if request.COOKIES.get('rep_f_inventoryitemtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inventoryitemtype_' + request.resolver_match.app_name))
            query = query.filter(prfmain__inventoryitemtype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(prfmain__branch=int(key_data))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                for n,data in enumerate(key_data):
                    key_data[n] = "prfmain__" + data
                query = query.order_by(*key_data)

        # @change amount format
        report_total = query.values_list('prfmain', flat=True).order_by('prfmain').distinct()
        report_totalgross = Prfmain.objects.filter(pk__in=report_total).aggregate(Sum('grossamount'))
        report_totalnet = Prfmain.objects.filter(pk__in=report_total).aggregate(Sum('netamount'))
        # report_totalgross = query.aggregate(Sum('prfmain__grossamount'))
        # report_totalnet = query.aggregate(Sum('prfmain__netamount'))

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
    report_type = report_type if report_type != '' else 'PRF Report'
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
        amount_placement = 11

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'PRF Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Inventory Item Type', bold)
        worksheet.write('D1', 'PRF Status', bold)
        worksheet.write('E1', 'Branch', bold)
        worksheet.write('F1', 'Quantity', bold)
        worksheet.write('G1', 'Gross Amount', bold_right)
        worksheet.write('H1', 'Net Amount', bold_right)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.merge_range('A1:A2', 'PRF Number', bold)
        worksheet.merge_range('B1:B2', 'Date', bold)
        worksheet.merge_range('C1:C2', 'Item Type', bold)
        worksheet.merge_range('D1:D2', 'Status', bold)
        worksheet.merge_range('E1:I1', 'PRF Detail', bold_center)
        worksheet.merge_range('J1:J2', 'Total Quantity', bold)
        worksheet.merge_range('K1:K2', 'Total Gross', bold_right)
        worksheet.merge_range('L1:L2', 'Total Net', bold_right)
        worksheet.write('E2', 'Item', bold)
        worksheet.write('F2', 'Supplier', bold)
        worksheet.write('G2', 'Department', bold)
        worksheet.write('H2', 'Item Gross', bold_right)
        worksheet.write('I2', 'Item Net', bold_right)
        row += 1

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            data = [
                obj.prfnum,
                DateFormat(obj.prfdate).format('Y-m-d'),
                obj.inventoryitemtype.description,
                obj.get_prfstatus_display(),
                obj.branch.code + " - " + obj.branch.description,
                obj.totalquantity,
                obj.grossamount,
                obj.netamount,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            data = [
                obj.prfmain.prfnum,
                DateFormat(obj.prfmain.prfdate).format('Y-m-d'),
                obj.prfmain.inventoryitemtype.description,
                obj.prfmain.get_prfstatus_display(),
                obj.invitem.code + " - " + obj.invitem.description,
                str(obj.suppliercode) + " - " + str(obj.suppliername),
                obj.department.code + " - " + obj.department.departmentname,
                obj.grossamount,
                obj.netamount,
                obj.prfmain.totalquantity,
                obj.prfmain.grossamount,
                obj.prfmain.netamount,
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
            "", "", "", "", "", "", "", "", "",
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


def lastNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  SUBSTRING(prfnum, 5) AS num FROM prfmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
