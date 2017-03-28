from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from . models import Rfmain, Rfdetail, Rfdetailtemp
from inventoryitemtype.models import Inventoryitemtype
from branch.models import Branch
from department.models import Department
from inventoryitem.models import Inventoryitem
from django.contrib.auth.models import User
from acctentry.views import generatekey
import datetime

# Create your views here.


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Rfmain
    template_name = 'requisitionform/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Rfmain.objects.all().filter(isdeleted=0).order_by('enterdate')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Rfmain
    template_name = 'requisitionform/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['rfdetail'] = Rfdetail.objects.filter(isdeleted=0).filter(rfmain=self.kwargs['pk']).\
            order_by('item_counter')
        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Rfmain
    template_name = 'requisitionform/create.html'
    fields = ['rfdate', 'inventoryitemtype', 'refnum', 'rftype', 'unit', 'urgencytype', 'dateneeded',
              'branch', 'department', 'particulars', 'designatedapprover']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0, code='SI')
        context['branch'] = Branch.objects.filter(isdeleted=0, code='HO')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).\
            filter(inventoryitemclass__inventoryitemtype__code='SI').order_by('description')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').\
            order_by('first_name')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        try:
            rfnumlast = Rfmain.objects.latest('rfnum')
            latestrfnum = str(rfnumlast)
            if latestrfnum[0:4] == str(datetime.datetime.now().year):
                rfnum = str(datetime.datetime.now().year)
                last = str(int(latestrfnum[4:])+1)
                zero_addon = 6 - len(last)
                for x in range(0, zero_addon):
                    rfnum += '0'
                rfnum += last
            else:
                rfnum = str(datetime.datetime.now().year) + '000001'
        except Rfmain.DoesNotExist:
            rfnum = str(datetime.datetime.now().year) + '000001'

        print 'rfnum: ' + rfnum
        self.object.rfnum = rfnum

        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        detailtemp = Rfdetailtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
            order_by('enterdate')
        i = 1
        for dt in detailtemp:
            detail = Rfdetail()
            detail.item_counter = i
            detail.rfmain = Rfmain.objects.get(rfnum=rfnum)
            detail.invitem = dt.invitem
            detail.invitem_code = dt.invitem_code
            detail.invitem_name = dt.invitem_name
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
            detail.save()
            dt.delete()
            i += 1

        return HttpResponseRedirect('/requisitionform/')


class UpdateView(UpdateView):
    model = Rfmain
    template_name = 'requisitionform/edit.html'
    fields = ['rfnum', 'rfdate', 'inventoryitemtype', 'refnum', 'rftype', 'unit', 'urgencytype', 'dateneeded',
              'branch', 'department', 'particulars', 'designatedapprover']

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0, code='SI')
        context['branch'] = Branch.objects.filter(isdeleted=0, code='HO')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).\
            filter(inventoryitemclass__inventoryitemtype__code='SI').order_by('description')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').\
            order_by('first_name')

        detail = Rfdetail.objects.filter(isdeleted=0, rfmain=self.object.pk).order_by('item_counter')

        Rfdetailtemp.objects.filter(rfmain=self.object.pk).delete()        # clear all temp data
        for d in detail:
            detailtemp = Rfdetailtemp()
            detailtemp.rfdetail = Rfdetail.objects.get(pk=d.id)
            detailtemp.item_counter = d.item_counter
            detailtemp.rfmain = d.rfmain
            detailtemp.invitem = d.invitem
            detailtemp.invitem_code = d.invitem_code
            detailtemp.invitem_name = d.invitem_name
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
            detailtemp.save()

        context['rfdetailtemp'] = Rfdetailtemp.objects.filter(isdeleted=0, rfmain=self.object.pk).order_by('item_counter')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['rfdate', 'inventoryitemtype', 'refnum', 'rftype', 'unit', 'urgencytype',
                                        'dateneeded', 'branch', 'department', 'particulars', 'designatedapprover',
                                        'modifyby', 'modifydate'])

        deletedtempdetail = Rfdetailtemp.objects.filter(isdeleted=1, rfmain=self.object.pk)
        for dd in deletedtempdetail:
            detailfordeletion = Rfdetail.objects.get(pk=dd.rfdetail.id)
            detailfordeletion.delete()
            dd.delete()

        newtempdetail = Rfdetailtemp.objects.filter(isdeleted=0, rfmain=None, rfdetail=None,
                                                    secretkey=self.request.POST['secretkey'])

        alltempdetail = Rfdetailtemp.objects.filter(
            Q(isdeleted=0),
            Q(rfmain=self.object.pk) | Q(secretkey=self.request.POST['secretkey'])
        ).order_by('enterdate')

        for a in alltempdetail:
            print a.remarks

        for ntd in newtempdetail:
            newdetail = Rfdetail()
            newdetail.item_counter = ntd.item_counter
            newdetail.rfmain = Rfmain.objects.get(rfnum=self.request.POST['rfnum'])
            newdetail.invitem = ntd.invitem
            newdetail.invitem_code = ntd.invitem_code
            newdetail.invitem_name = ntd.invitem_name
            newdetail.quantity = ntd.quantity
            newdetail.remarks = ntd.remarks
            newdetail.status = ntd.status
            newdetail.enterby = ntd.enterby
            newdetail.enterdate = ntd.enterdate
            newdetail.modifyby = ntd.modifyby
            newdetail.modifydate = ntd.modifydate
            newdetail.postby = ntd.postby
            newdetail.postdate = ntd.postdate
            newdetail.isdeleted = ntd.isdeleted
            newdetail.save()
            ntd.delete()

        alldetail = Rfdetail.objects.filter(isdeleted=0, rfmain=self.object.pk).order_by('enterdate')
        i = 1
        for ad in alldetail:
            ad.item_counter = i
            ad.save()
            i += 1

        Rfdetailtemp.objects.filter(rfmain=self.object.pk).delete()  # clear all temp data

        return HttpResponseRedirect('/requisitionform/')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Rfmain
    template_name = 'requisitionform/delete.html'

    def dispatch(self, request, *args, **kwargs):
        # if not request.user.has_perm('product.delete_product'):
        #     raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/requisitionform')


@csrf_exempt
def savedetailtemp(request):

    if request.method == 'POST':
        detailtemp = Rfdetailtemp()
        detailtemp.item_counter = request.POST['itemno']
        detailtemp.invitem = Inventoryitem.objects.get(pk=request.POST['id_item'])
        detailtemp.invitem_code = Inventoryitem.objects.get(pk=request.POST['id_item']).code
        detailtemp.invitem_name = Inventoryitem.objects.get(pk=request.POST['id_item']).description
        detailtemp.quantity = request.POST['id_quantity']
        detailtemp.remarks = request.POST['id_remarks']
        detailtemp.secretkey = request.POST['secretkey']
        detailtemp.status = 'A'
        detailtemp.enterdate = datetime.datetime.now()
        detailtemp.modifydate = datetime.datetime.now()
        detailtemp.enterby = User.objects.get(pk=request.user.id)
        detailtemp.modifyby = User.objects.get(pk=request.user.id)
        detailtemp.save()

        data = {
            'status': 'success',
            'itemno': request.POST['itemno'],
            'quantity': request.POST['id_quantity'],
            'remarks': request.POST['id_remarks'],
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
            detailtemp = Rfdetailtemp.objects.get(item_counter=request.POST['itemno'],
                                                  secretkey=request.POST['secretkey'],
                                                  rfmain=None)
            detailtemp.delete()
        except Rfdetailtemp.DoesNotExist:
            print "this happened"
            detailtemp = Rfdetailtemp.objects.get(item_counter=request.POST['itemno'], rfmain__rfnum=request.POST['rfnum'])
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

