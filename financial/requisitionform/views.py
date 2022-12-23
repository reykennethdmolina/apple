"""This module handles the processing of requisition form transactions."""

import datetime
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from branch.models import Branch
from companyparameter.models import Companyparameter
from department.models import Department
from inventoryitem.models import Inventoryitem
from inventoryitemtype.models import Inventoryitemtype
from unitofmeasure.models import Unitofmeasure
from django.contrib.auth.models import User
from acctentry.views import generatekey
from easy_pdf.views import PDFTemplateView
from . models import Rfmain, Rfdetail, Rfdetailtemp
from dateutil.relativedelta import relativedelta
import datetime
from annoying.functions import get_object_or_None
from employee.models import Employee

# pagination and search
from endless_pagination.views import AjaxListView
from django.db.models import Q, Sum

from utils.mixins import ReportContentMixin
from django.utils.dateformat import DateFormat
import datetime
from django.db import connection
from collections import namedtuple


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    """This class enlists all requisition forms."""
    model = Rfmain
    template_name = 'requisitionform/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'requisitionform/index_list.html'
    def get_queryset(self):
        print self.request.user.has_perm('requisitionform.view_assignrf')
        print 'test'
        if self.request.user.has_perm('requisitionform.view_assignrf') and not self.request.user.has_perm('requisitionform.view_allassignrf'):
            #print self.request.user.id
            user_employee = get_object_or_None(Employee, user_id=self.request.user.id)
            #print 'hey'
            if user_employee is not None:
                query = Rfmain.objects.filter(designatedapprover_id=self.request.user.id) | Rfmain.objects.filter(enterby=self.request.user.id)
                query = query.filter(isdeleted=0)

            else:
                query = Rfmain.objects.all().filter(isdeleted=0)
        else:
            if self.request.user.has_perm('requisitionform.view_assignrf'):
                query = Rfmain.objects.all().filter(isdeleted=0)
            else:
                query = Rfmain.objects.all().filter(isdeleted=0, enterby=self.request.user.id)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(rfnum__icontains=keysearch) |
                                 Q(rfdate__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch))
        return query


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Rfmain
    template_name = 'requisitionform/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['rfdetail'] = Rfdetail.objects.filter(isdeleted=0).\
            filter(rfmain=self.kwargs['pk']).order_by('item_counter')
        context['totalprfquantity'] = Rfmain.objects.get(pk=self.kwargs['pk']).\
                                          totalquantity - Rfmain.objects.\
            get(pk=self.kwargs['pk']).totalremainingquantity
        prfs = Rfmain.objects.raw('SELECT DISTINCT '
                                  'rfm.rfnum, prfm.prfnum, prfm.id, '
                                  'prfm.prfstatus, prfm.modifydate '
                                  'FROM prfdetail prfd '
                                  'LEFT JOIN rfdetail rfd '
                                  'ON prfd.rfdetail_id = rfd.id '
                                  'LEFT JOIN rfmain rfm '
                                  'ON rfd.rfmain_id = rfm.id '
                                  'LEFT JOIN prfmain prfm '
                                  'ON prfd.prfmain_id = prfm.id '
                                  'WHERE '
                                  'rfm.rfnum = ' + self.object.rfnum + ' AND '
                                  'prfm.isdeleted = 0 '
                                  'ORDER BY prfm.modifydate')
        context['prfs'] = []
        for data in prfs:
            context['prfs'].append([data.prfnum,
                                    data.prfstatus,
                                    data.modifydate,
                                    data.id])

        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Rfmain
    template_name = 'requisitionform/create.html'
    fields = ['rfdate', 'inventoryitemtype', 'refnum', 'rftype', 'unit', 'urgencytype',
              'dateneeded', 'branch', 'department', 'particulars', 'designatedapprover',
              'totalquantity']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('requisitionform.add_rfmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0, code='SI')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['headoffice'] = Branch.objects.get(code='HO').id
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).\
            filter(inventoryitemclass__inventoryitemtype__code='SI').order_by('description')
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('code')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').\
            order_by('first_name')
        context['totalremainingquantity'] = 0

        closetransaction = Companyparameter.objects.all().first().last_closed_date
        validtransaction = closetransaction + relativedelta(months=1)
        context['validtransaction'] = validtransaction

        return context

    def form_valid(self, form):
        if Rfdetailtemp.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0):
            self.object = form.save(commit=False)

            year = str(form.cleaned_data['rfdate'].year)
            yearqs = Rfmain.objects.filter(rfnum__startswith=year)

            rfnumlast = lastNumber('true')
            latestrfnum = str(rfnumlast[0])

            rfnum = year
            last = str(int(latestrfnum) + 1)

            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                rfnum += '0'
            rfnum += last

            # if yearqs:
            #     rfnumlast = yearqs.latest('rfnum')
            #     latestrfnum = str(rfnumlast)
            #     print "latest: " + latestrfnum
            #
            #     rfnum = year
            #     last = str(int(latestrfnum[4:])+1)
            #     zero_addon = 6 - len(last)
            #     for num in range(0, zero_addon):
            #         rfnum += '0'
            #     rfnum += last
            #
            # else:
            #     rfnum = year + '000001'

            print 'rfnum: ' + rfnum
            self.object.rfnum = rfnum
            self.object.enterby = self.request.user
            self.object.modifyby = self.request.user
            self.object.totalremainingquantity = self.request.POST['totalquantity']
            self.object.save()

            detailtemp = Rfdetailtemp.objects.filter(isdeleted=0,
                                                     secretkey=self.request.
                                                     POST['secretkey']).\
                order_by('enterdate')
            i = 1
            for dt in detailtemp:
                detail = Rfdetail()
                detail.item_counter = i
                detail.rfmain = Rfmain.objects.get(rfnum=rfnum)
                detail.invitem = dt.invitem
                detail.invitem_code = dt.invitem_code
                detail.invitem_name = dt.invitem_name
                detail.invitem_unitofmeasure = Unitofmeasure.objects\
                                                            .get(code=self.request.POST
                                                                 .getlist('temp_item_um')[i-1],
                                                                 isdeleted=0, status='A')
                detail.invitem_unitofmeasure_code = Unitofmeasure.objects\
                    .get(code=self.request.POST.getlist('temp_item_um')[i - 1],
                         isdeleted=0, status='A').code
                detail.quantity = self.request.POST.getlist('temp_quantity')[i-1]
                detail.remarks = self.request.POST.getlist('temp_remarks')[i-1]
                detail.status = dt.status
                detail.enterby = dt.enterby
                detail.enterdate = dt.enterdate
                detail.modifyby = dt.modifyby
                detail.modifydate = dt.modifydate
                detail.postby = dt.postby
                detail.postdate = dt.postdate
                detail.isdeleted = dt.isdeleted
                detail.prfremainingquantity = self.request.POST.getlist('temp_quantity')[i-1]
                detail.save()
                dt.delete()
                i += 1

            return HttpResponseRedirect('/requisitionform/' + str(self.object.id) + '/update')


class UpdateView(UpdateView):
    model = Rfmain
    template_name = 'requisitionform/edit.html'
    fields = ['rfnum', 'rfdate', 'inventoryitemtype', 'refnum', 'rftype', 'unit',
              'urgencytype', 'dateneeded', 'branch', 'department', 'particulars',
              'designatedapprover', 'totalquantity']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('requisitionform.change_rfmain') or self.object.isdeleted == 1:
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0, code='SI')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['headoffice'] = Branch.objects.get(code='HO').id
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['rfstatus'] = Rfmain.objects.get(pk=self.object.pk).get_rfstatus_display()
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).\
            filter(inventoryitemclass__inventoryitemtype__code='SI').order_by('description')
        context['unitofmeasure'] = Unitofmeasure.objects.filter(isdeleted=0).order_by('code')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').\
            order_by('first_name')
        context['totalremainingquantity'] = Rfmain.objects.get(pk=self.object.pk).\
            totalremainingquantity
        prfs = Rfmain.objects.raw('SELECT DISTINCT '
                                  'rfm.rfnum, '
                                  'prfm.prfnum, '
                                  'prfm.id, '
                                  'prfm.prfstatus, '
                                  'prfm.modifydate '
                                  'FROM prfdetail prfd '
                                  'LEFT JOIN rfdetail rfd '
                                  'ON prfd.rfdetail_id = rfd.id '
                                  'LEFT JOIN rfmain rfm '
                                  'ON rfd.rfmain_id = rfm.id '
                                  'LEFT JOIN prfmain prfm '
                                  'ON prfd.prfmain_id = prfm.id '
                                  'WHERE '
                                  'rfm.rfnum = ' + self.object.rfnum + ' AND '
                                  'prfm.isdeleted = 0 '
                                  'ORDER BY prfm.modifydate')

        context['prfs'] = []
        for data in prfs:
            context['prfs'].append([data.prfnum,
                                    data.prfstatus,
                                    data.modifydate,
                                    data.id])

        detail = Rfdetail.objects.filter(isdeleted=0, rfmain=self.object.pk)\
            .order_by('item_counter')

        Rfdetailtemp.objects.filter(rfmain=self.object.pk).delete()        # clear all temp data
        for d in detail:
            detailtemp = Rfdetailtemp()
            detailtemp.rfdetail = Rfdetail.objects.get(pk=d.id)
            detailtemp.item_counter = d.item_counter
            detailtemp.rfmain = d.rfmain
            detailtemp.invitem = d.invitem
            detailtemp.invitem_code = d.invitem_code
            detailtemp.invitem_name = d.invitem_name
            detailtemp.invitem_unitofmeasure = d.invitem_unitofmeasure
            detailtemp.invitem_unitofmeasure_code = d.invitem_unitofmeasure_code
            detailtemp.quantity = d.quantity
            detailtemp.remarks = d.remarks
            detailtemp.status = d.status
            detailtemp.enterby = d.enterby
            detailtemp.enterdate = d.enterdate
            detailtemp.modifyby = d.modifyby
            detailtemp.modifydate = d.modifydate
            detailtemp.postby = d.postby
            detailtemp.postdate = d.postdate
            detailtemp.isdeleted = d.isdeleted
            detailtemp.isfullyprf = d.isfullyprf
            detailtemp.prftotalquantity = d.prftotalquantity
            detailtemp.prfremainingquantity = d.prfremainingquantity
            detailtemp.save()

        context['rfdetailtemp'] = Rfdetailtemp.objects.filter(isdeleted=0,
                                                              rfmain=self.object.pk).\
            order_by('item_counter')
        return context

    def form_valid(self, form):
        if Rfdetailtemp.objects.filter(
                Q(isdeleted=0),
                Q(rfmain=self.object.pk) | Q(secretkey=self.request.POST['secretkey'])):
            self.object = form.save(commit=False)
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.totalremainingquantity = self.request.POST['totalquantity']

            # check rfstatus, if "Approved", certain fields should not be updated
            if self.object.rfstatus == 'A':
                self.object.save(update_fields=['particulars', 'modifyby', 'modifydate'])
            else:
                self.object.save(update_fields=['rfdate', 'inventoryitemtype', 'refnum',
                                                'rftype', 'unit', 'urgencytype',
                                                'dateneeded', 'branch', 'department',
                                                'particulars', 'designatedapprover',
                                                'totalquantity', 'modifyby', 'modifydate',
                                                'totalremainingquantity'])

            Rfdetailtemp.objects.filter(isdeleted=1, rfmain=self.object.pk).delete()

            detailtagasdeleted = Rfdetail.objects.filter(rfmain=self.object.pk)
            for dtd in detailtagasdeleted:
                dtd.isdeleted = 1
                dtd.save()

            alltempdetail = Rfdetailtemp.objects.filter(
                Q(isdeleted=0),
                Q(rfmain=self.object.pk) | Q(secretkey=self.request.POST['secretkey'])
            ).order_by('enterdate')

            i = 1
            for atd in alltempdetail:
                alldetail = Rfdetail()
                alldetail.item_counter = i
                alldetail.rfmain = Rfmain.objects.get(rfnum=self.request.POST['rfnum'])
                alldetail.invitem = atd.invitem
                alldetail.invitem_code = atd.invitem_code
                alldetail.invitem_name = atd.invitem_name

                # if rfstatus == "Approved", unitofmeasure, unitofmeasurecode
                # and quantity will not be updated
                if self.object.rfstatus == 'Approved':
                    alldetail.invitem_unitofmeasure = atd.invitem_unitofmeasure
                    alldetail.invitem_unitofmeasure_code = atd.invitem_unitofmeasure_code
                    alldetail.quantity = atd.quantity
                else:
                    alldetail.invitem_unitofmeasure = Unitofmeasure.objects.get(
                        code=self.request.POST.getlist('temp_item_um')[i - 1],
                        isdeleted=0, status='A')
                    alldetail.invitem_unitofmeasure_code = Unitofmeasure.objects.get(
                        code=self.request.POST.getlist('temp_item_um')[i - 1],
                        isdeleted=0, status='A').code
                    alldetail.quantity = self.request.POST.getlist('temp_quantity')[i-1]
                    alldetail.prfremainingquantity = self.request.POST.getlist('temp_quantity')[i-1]

                alldetail.remarks = self.request.POST.getlist('temp_remarks')[i-1]
                alldetail.status = atd.status
                alldetail.enterby = atd.enterby
                alldetail.enterdate = atd.enterdate
                alldetail.modifyby = atd.modifyby
                alldetail.modifydate = atd.modifydate
                alldetail.postby = atd.postby
                alldetail.postdate = atd.postdate
                alldetail.isdeleted = atd.isdeleted
                alldetail.save()
                atd.delete()
                i += 1

            Rfdetailtemp.objects.filter(rfmain=self.object.pk).delete()  # clear all temp data
            Rfdetail.objects.filter(rfmain=self.object.pk, isdeleted=1).delete()

            return HttpResponseRedirect('/requisitionform/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Rfmain
    template_name = 'requisitionform/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('requisitionform.delete_rfmain') or \
                        self.object.status != 'A' or self.object.rfstatus != 'F' or \
                        self.object.isdeleted == 1:
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.rfstatus = 'D'
        self.object.save()
        return HttpResponseRedirect('/requisitionform')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Rfmain
    template_name = 'requisitionform/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(Pdf, self).get_context_data(**kwargs)
        context['rfmain'] = Rfmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['detail'] = Rfdetail.objects.filter(rfmain=self.kwargs['pk'], isdeleted=0,
                                                      status='A').order_by('item_counter')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')

        rf_detail_aggregate = Rfdetail.objects.filter(rfmain=self.kwargs['pk'], isdeleted=0, status='A').\
            aggregate(Sum('quantity'))
        context['detail_total_quantity'] = rf_detail_aggregate['quantity__sum']

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedrf = Rfmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedrf.print_ctr += 1
        printedrf.save()

        return context


@csrf_exempt
def savedetailtemp(request):

    if request.method == 'POST':
        detailtemp = Rfdetailtemp()
        detailtemp.item_counter = request.POST['itemno']
        detailtemp.invitem = Inventoryitem.objects.get(pk=request.POST['id_item'], status='A')
        detailtemp.invitem_code = Inventoryitem.objects.get(pk=request.POST['id_item'],
                                                            status='A').code
        detailtemp.invitem_name = Inventoryitem.objects.get(pk=request.POST['id_item'],
                                                            status='A').description
        detailtemp.invitem_unitofmeasure = Inventoryitem.objects.get(pk=request.POST['id_item'],
                                                                     status='A').unitofmeasure
        detailtemp.invitem_unitofmeasure_code = Inventoryitem.objects.get(
            pk=request.POST['id_item'], status='A').unitofmeasure.code
        detailtemp.quantity = request.POST['id_quantity']
        detailtemp.remarks = request.POST['id_remarks']
        detailtemp.secretkey = request.POST['secretkey']
        detailtemp.status = 'A'
        detailtemp.enterdate = datetime.datetime.now()
        detailtemp.modifydate = datetime.datetime.now()
        detailtemp.enterby = User.objects.get(pk=request.user.id)
        detailtemp.modifyby = User.objects.get(pk=request.user.id)
        detailtemp.prfremainingquantity = request.POST['id_quantity']
        detailtemp.save()

        data = {
            'status': 'success',
            'itemno': request.POST['itemno'],
            'quantity': request.POST['id_quantity'],
            'itemcode': detailtemp.invitem_code,
            'remarks': request.POST['id_remarks'],
            'rfdetailid': detailtemp.pk,
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
            detailtemp = Rfdetailtemp.objects.get(id=request.POST['rfdetailid'],
                                                  secretkey=request.POST['secretkey'],
                                                  rfmain=None)
            detailtemp.delete()
        except Rfdetailtemp.DoesNotExist:
            print "this happened"
            detailtemp = Rfdetailtemp.objects.get(id=request.POST['rfdetailid'],
                                                  rfmain__rfnum=request.POST['rfnum'])
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


# @change add report class and def
@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Rfmain
    # @change template link
    template_name = 'requisitionform/report.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0).order_by('description')

        return context


@method_decorator(login_required, name='dispatch')
class ReportResultView(ReportContentMixin, PDFTemplateView):
    model = Rfmain
    # @change template link
    template_name = 'requisitionform/reportresult.html'

    def get_context_data(self, **kwargs):
        context = super(ReportResultView, self).get_context_data(**kwargs)
        context['report_type'] = ''
        context['report_total'] = 0

        # @change totals
        query, context['report_type'] = reportresultquery(self.request)

        context['report'] = self.request.COOKIES.get('rep_f_report_' + self.request.resolver_match.app_name)
        context['data_list'] = query

        context['rc_orientation'] = ('portrait', 'landscape')[self.request.COOKIES.get('rep_f_orientation_' + self.request.resolver_match.app_name) == 'l']
        # @change default title
        context['rc_headtitle'] = "REQUISITION FORM"
        context['rc_title'] = "REQUISITION FORM"

        return context


@csrf_exempt
def reportresultquery(request):
    query = ''
    report_type = ''

    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        # @change report title
        report_type = "RF Summary"

        # @change table for main
        query = Rfmain.objects.all().filter(isdeleted=0)

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(rfnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(rfnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(rfdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(rfdate__lte=key_data)

        if request.COOKIES.get('rep_f_rfstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_rfstatus_' + request.resolver_match.app_name))
            query = query.filter(rfstatus=str(key_data))
        if request.COOKIES.get('rep_f_inventoryitemtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inventoryitemtype_' + request.resolver_match.app_name))
            query = query.filter(inventoryitemtype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(branch=int(key_data))
        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(department=int(key_data))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                query = query.order_by(*key_data)

    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        # @change report title
        report_type = "RF Detailed"

        # @change table for detailed
        query = Rfdetail.objects.all().filter(isdeleted=0).order_by('rfmain')

        if request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numfrom_' + request.resolver_match.app_name))
            query = query.filter(rfmain__rfnum__gte=int(key_data))
        if request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_numto_' + request.resolver_match.app_name))
            query = query.filter(rfmain__rfnum__lte=int(key_data))

        if request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_datefrom_' + request.resolver_match.app_name))
            query = query.filter(rfmain__rfdate__gte=key_data)
        if request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_dateto_' + request.resolver_match.app_name))
            query = query.filter(rfmain__rfdate__lte=key_data)

        if request.COOKIES.get('rep_f_rfstatus_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_rfstatus_' + request.resolver_match.app_name))
            query = query.filter(rfmain__rfstatus=str(key_data))
        if request.COOKIES.get('rep_f_inventoryitemtype_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_inventoryitemtype_' + request.resolver_match.app_name))
            query = query.filter(rfmain__inventoryitemtype=int(key_data))
        if request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_branch_' + request.resolver_match.app_name))
            query = query.filter(rfmain__branch=int(key_data))
        if request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_department_' + request.resolver_match.app_name))
            query = query.filter(rfmain__department=int(key_data))

        if request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name):
            key_data = str(request.COOKIES.get('rep_f_order_' + request.resolver_match.app_name))
            if key_data != 'null':
                key_data = key_data.split(",")
                for n, data in enumerate(key_data):
                    key_data[n] = "rfmain__" + data
                query = query.order_by(*key_data)

    if request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name):
        key_data = str(request.COOKIES.get('rep_f_asc_' + request.resolver_match.app_name))
        if key_data == 'd':
            query = query.reverse()

    # @change totals
    return query, report_type


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
    queryset, report_type = reportresultquery(request)
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

    # config: header
    if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
        worksheet.write('A1', 'RF Number', bold)
        worksheet.write('B1', 'Date', bold)
        worksheet.write('C1', 'Date Needed', bold)
        worksheet.write('D1', 'Inventory Item Type', bold)
        worksheet.write('E1', 'RF Status', bold)
        worksheet.write('F1', 'Designated Approver', bold)
        worksheet.write('G1', 'Actual Approver', bold)
        worksheet.write('H1', 'Approver Response', bold)
        worksheet.write('I1', 'Branch', bold)
        worksheet.write('J1', 'Department', bold)
        worksheet.write('K1', 'Quantity', bold)
    elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
        worksheet.merge_range('A1:A2', 'RF Number', bold)
        worksheet.merge_range('B1:B2', 'Date', bold)
        worksheet.merge_range('C1:C2', 'Date Needed', bold)
        worksheet.merge_range('D1:D2', 'Inventory Item Type', bold)
        worksheet.merge_range('E1:E2', 'RF Status', bold)
        worksheet.merge_range('F1:G1', 'RF Detail', bold_center)
        worksheet.merge_range('H1:H2', 'Total Quantity', bold_right)
        worksheet.write('F2', 'Item', bold)
        worksheet.write('G2', 'Quantity', bold)
        row += 1

    for obj in queryset:
        row += 1

        # config: content
        if request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 's':
            str_actualapprover = '-'
            if obj.actualapprover:
                str_actualapprover = str(obj.actualapprover.first_name) + " " + str(obj.actualapprover.last_name)

            data = [
                obj.rfnum,
                DateFormat(obj.rfdate).format('Y-m-d'),
                DateFormat(obj.dateneeded).format('Y-m-d'),
                obj.inventoryitemtype.description,
                obj.get_rfstatus_display(),
                str(obj.designatedapprover.first_name) + " " + str(obj.designatedapprover.last_name),
                str_actualapprover,
                obj.get_approverresponse_display(),
                obj.branch.code + " - " + obj.branch.description,
                obj.department.code + " - " + obj.department.departmentname,
                obj.totalquantity,
            ]
        elif request.COOKIES.get('rep_f_report_' + request.resolver_match.app_name) == 'd':
            data = [
                obj.rfmain.rfnum,
                DateFormat(obj.rfmain.rfdate).format('Y-m-d'),
                DateFormat(obj.rfmain.dateneeded).format('Y-m-d'),
                obj.rfmain.inventoryitemtype.description,
                obj.rfmain.get_rfstatus_display(),
                obj.invitem.code + " - " + obj.invitem.description,
                obj.quantity,
                obj.rfmain.totalquantity,
            ]

        for col_num in xrange(len(data)):
            worksheet.write(row, col_num, data[col_num])

    for col_num in xrange(len(data)):
        worksheet.write(row, col_num, data[col_num])

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+report_type+".xlsx"
    return response

def lastNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  SUBSTRING(rfnum, 5) AS num FROM rfmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
