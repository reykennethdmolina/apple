from django.views.generic import CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
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

        detail = Rfdetailtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
            order_by('enterdate')
        i = 1
        for d in detail:
            detailfinal = Rfdetail()
            detailfinal.item_counter = i
            detailfinal.rfmain = Rfmain.objects.get(rfnum=rfnum)
            detailfinal.invitem = d.invitem
            detailfinal.invitem_code = d.invitem_code
            detailfinal.invitem_name = d.invitem_name
            detailfinal.quantity = d.quantity
            detailfinal.remarks = d.remarks
            detailfinal.status = d.status
            detailfinal.enterby = d.enterby
            detailfinal.enterdate = d.enterdate
            detailfinal.modifyby = d.modifyby
            detailfinal.modifydate = d.modifydate
            detailfinal.postby = d.postby
            detailfinal.postdate = d.postdate
            detailfinal.isdeleted = d.isdeleted
            detailfinal.save()
            d.delete()
            i += 1

        return HttpResponseRedirect('/requisitionform/create')


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
        context['rfdetail'] = Rfdetail.objects.filter(isdeleted=0, rfmain=self.object.pk)
        return context

    def form_valid(self, form):
        # self.object = form.save(commit=False)
        #
        # try:
        #     rfnumlast = Rfmain.objects.latest('rfnum')
        #     latestrfnum = str(rfnumlast)
        #     if latestrfnum[0:4] == str(datetime.datetime.now().year):
        #         rfnum = str(datetime.datetime.now().year)
        #         last = str(int(latestrfnum[4:])+1)
        #         zero_addon = 6 - len(last)
        #         for x in range(0, zero_addon):
        #             rfnum += '0'
        #         rfnum += last
        #     else:
        #         rfnum = str(datetime.datetime.now().year) + '000001'
        # except Rfmain.DoesNotExist:
        #     rfnum = str(datetime.datetime.now().year) + '000001'
        #
        # print 'rfnum: ' + rfnum
        # self.object.rfnum = rfnum
        #
        # self.object.enterby = self.request.user
        # self.object.modifyby = self.request.user
        # self.object.save()
        #
        # detail = Rfdetailtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
        #     order_by('enterdate')
        # i = 1
        # for d in detail:
        #     detailfinal = Rfdetail()
        #     detailfinal.item_counter = i
        #     detailfinal.rfmain = Rfmain.objects.get(rfnum=rfnum)
        #     detailfinal.invitem = d.invitem
        #     detailfinal.invitem_code = d.invitem_code
        #     detailfinal.invitem_name = d.invitem_name
        #     detailfinal.quantity = d.quantity
        #     detailfinal.remarks = d.remarks
        #     detailfinal.status = d.status
        #     detailfinal.enterby = d.enterby
        #     detailfinal.enterdate = d.enterdate
        #     detailfinal.modifyby = d.modifyby
        #     detailfinal.modifydate = d.modifydate
        #     detailfinal.postby = d.postby
        #     detailfinal.postdate = d.postdate
        #     detailfinal.isdeleted = d.isdeleted
        #     detailfinal.save()
        #     d.delete()
        #     i += 1

        return HttpResponseRedirect('/requisitionform/create')


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
        detailtemp.enterby = request.user
        detailtemp.modifyby = request.user
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
        detailtemp = Rfdetailtemp.objects.get(item_counter=request.POST['itemno'], secretkey=request.POST['secretkey'])
        if detailtemp.rfmain is None:
            detailtemp.delete()
        else:
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

