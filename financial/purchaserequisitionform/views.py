from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from . models import Prfmain
from requisitionform.models import Rfmain, Rfdetail
from purchaserequisitionform.models import Prfmain, Prfdetail, Prfdetailtemp, Rfprftransaction
from inventoryitemtype.models import Inventoryitemtype
from inventoryitem.models import Inventoryitem
from branch.models import Branch
from department.models import Department
from unitofmeasure.models import Unitofmeasure
from currency.models import Currency
from django.contrib.auth.models import User
from django.db.models import Q, F
from django.core import serializers
from acctentry.views import generatekey
from easy_pdf.views import PDFTemplateView
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Prfmain
    template_name = 'purchaserequisitionform/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Prfmain.objects.all().order_by('enterdate')[0:10]

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['listcount'] = Prfmain.objects.filter(isdeleted=0).count()
        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Prfmain
    template_name = 'purchaserequisitionform/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['prfdetail'] = Prfdetail.objects.filter(isdeleted=0, prfmain=self.kwargs['pk']).order_by('item_counter')
        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Prfmain
    template_name = 'purchaserequisitionform/create.html'
    fields = ['prfdate', 'inventoryitemtype', 'designatedapprover', 'prftype', 'particulars', 'department', 'branch', 'urgencytype', 'dateneeded']

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
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        return context

    def form_valid(self, form):
        if Prfdetailtemp.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0):
            self.object = form.save(commit=False)

            year = str(form.cleaned_data['prfdate'].year)
            yearQS = Prfmain.objects.filter(prfnum__startswith=year)

            if yearQS:
                prfnumlast = yearQS.latest('prfnum')
                latestprfnum = str(prfnumlast)

                prfnum = year
                last = str(int(latestprfnum[4:])+1)
                zero_addon = 6 - len(last)
                for x in range(0, zero_addon):
                    prfnum += '0'
                prfnum += last

            else:
                prfnum = year + '000001'

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
            for dt in detailtemp:
                detail = Prfdetail()
                detail.item_counter = i
                detail.prfmain = prfmain
                detail.invitem_code = dt.invitem_code
                detail.invitem_name = dt.invitem_name
                detail.invitem_unitofmeasure = Unitofmeasure.objects.get(code=self.request.POST.getlist('temp_item_um')[i-1], isdeleted=0, status='A')
                detail.invitem_unitofmeasure_code = Unitofmeasure.objects.get(code=self.request.POST.getlist('temp_item_um')[i-1], isdeleted=0, status='A').code
                detail.quantity = self.request.POST.getlist('temp_quantity')[i-1]
                detail.amount = 0
                detail.remarks = dt.remarks
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
    Prfmain.objects.filter(pk=prfdetail.prfmain.id).update(quantity=0, amount=0.00, grossamount=0.00,
                                                           netamount=0.00, vatable=0.00, vatamount=0.00,
                                                           vatexempt=0.00, vatzerorated=0.00)


class UpdateView(UpdateView):
    model = Prfmain
    template_name = 'purchaserequisitionform/edit.html'
    fields = ['prfnum', 'prfdate', 'inventoryitemtype', 'designatedapprover', 'prftype', 'particulars', 'department', 'branch', 'urgencytype', 'dateneeded']

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
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')

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
            self.object.save(update_fields=['prfdate', 'inventoryitemtype', 'prftype', 'urgencytype',
                                            'dateneeded', 'branch', 'department', 'particulars', 'designatedapprover',
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
            for atd in alltempdetail:
                alldetail = Prfdetail()
                alldetail.item_counter = i
                alldetail.prfmain = Prfmain.objects.get(prfnum=self.request.POST['prfnum'])
                alldetail.invitem = atd.invitem
                alldetail.invitem_code = atd.invitem_code
                alldetail.invitem_name = atd.invitem_name
                alldetail.invitem_unitofmeasure = Unitofmeasure.objects.get(code=self.request.POST.getlist('temp_item_um')[i-1], isdeleted=0, status='A')
                alldetail.invitem_unitofmeasure_code = Unitofmeasure.objects.get(code=self.request.POST.getlist('temp_item_um')[i-1], isdeleted=0, status='A').code
                alldetail.quantity = self.request.POST.getlist('temp_quantity')[i-1]
                alldetail.remarks = atd.remarks
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
            prfmain.save()

            Prfdetailtemp.objects.filter(prfmain=self.object.pk).delete()

            return HttpResponseRedirect('/purchaserequisitionform/' + str(self.object.id) + '/update/')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Prfmain
    template_name = 'purchaserequisitionform/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('purchaserequisitionform.delete_prfmain') or self.object.status == 'O':
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
    model = Prfmain
    template_name = 'purchaserequisitionform/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(Pdf, self).get_context_data(**kwargs)
        context['prfmain'] = Prfmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['prfdetail'] = Prfdetail.objects.filter(prfmain=self.kwargs['pk'], isdeleted=0, status='A').order_by('item_counter')

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
                                data.prfremainingquantity])

                detailtemp = Prfdetailtemp()
                detailtemp.invitem_code = data.invitem_code
                detailtemp.invitem_name = data.invitem_name
                detailtemp.invitem_unitofmeasure = Unitofmeasure.objects.get(pk=data.um_id)
                detailtemp.invitem_unitofmeasure_code = data.um_code
                detailtemp.item_counter = item_counter
                detailtemp.quantity = data.quantity
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
                                    'inv.id, '
                                    'um.code AS um_code '
                            'FROM inventoryitem inv '
                            'LEFT JOIN unitofmeasure um '
                            'ON um.id = inv.unitofmeasure_id '
                            'WHERE '
                                'inv.status = "A" AND '
                                'inv.id = ' + request.POST['inv_id'])

        for data in invdetail:
            prfdata = [data.code,
                       data.description,
                       data.um_code,
                       data.unitcost,
                       data.id]

            detailtemp = Prfdetailtemp()
            detailtemp.invitem_code = data.code
            detailtemp.invitem_name = data.description
            detailtemp.item_counter = request.POST['itemno']
            detailtemp.quantity = request.POST['quantity']
            detailtemp.remarks = request.POST['remarks']
            detailtemp.invitem_unitofmeasure = Inventoryitem.objects.get(pk=request.POST['inv_id']).unitofmeasure
            detailtemp.invitem_unitofmeasure_code = Inventoryitem.objects.get(pk=request.POST['inv_id']).unitofmeasure.code
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


def paginate(request, command, current, limit, search):
    current = int(current)
    limit = int(limit)

    if command == "search" and search != "null":
        search_not_slug = search.replace('-', ' ')
        prfmain = Prfmain.objects.all().filter(Q(prfnum__icontains=search) |
                                             Q(prfdate__icontains=search) |
                                             Q(particulars__icontains=search) |
                                             Q(prfstatus__icontains=search) |
                                             Q(prfnum__icontains=search_not_slug) |
                                             Q(prfdate__icontains=search_not_slug) |
                                             Q(particulars__icontains=search_not_slug) |
                                             Q(prfstatus__icontains=search_not_slug))\
                                            .filter(isdeleted=0).order_by('-enterdate')
    else:
        prfmain = Prfmain.objects.all().filter(isdeleted=0).order_by('-enterdate')[current:current+limit]

    json_models = serializers.serialize("json", prfmain)
    print json_models
    return HttpResponse(json_models, content_type="application/javascript")


def comments():
    print 123
    # update import select behind modal
    # quantity cost front end change
    # delete item prompt
    # delete prfmain prompt
    # handle bloating in prfdetailtemp