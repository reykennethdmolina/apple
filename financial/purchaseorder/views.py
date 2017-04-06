from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Pomain, Podetail, Podetailtemp
from supplier.models import Supplier
from ataxcode.models import Ataxcode
from inputvat.models import Inputvat
from vat.models import Vat
from creditterm.models import Creditterm
from inventoryitem.models import Inventoryitem
from branch.models import Branch
from department.models import Department
from django.contrib.auth.models import User
from acctentry.views import generatekey
import datetime

# Create your views here.


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Pomain
    template_name = 'purchaseorder/create.html'
    fields = ['ponum', 'podate', 'potype', 'refnum', 'urgencytype', 'dateneeded', 'supplier', 'ataxcode', 'inputvat',
              'vat', 'creditterm']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('pk')
        context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('description')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        return context

    def form_valid(self, form):
        # self.object = form.save(commit=False)
        #
        # jvyear = form.cleaned_data['jvdate'].year
        # num = len(Jvmain.objects.all().filter(jvdate__year=jvyear)) + 1
        # padnum = '{:06d}'.format(num)
        #
        # self.object.jvnum = str(jvyear)+str(padnum)
        # self.object.modifyby = self.request.user
        # self.object.modifydate = datetime.datetime.now()
        # self.object.save()
        # mainid = self.object.id

        # Save Data To JVDetail
        # detail = Potype()
        # detail.modifyby = self.request.user
        # detail.modifydate = datetime.datetime.now()
        # detail.save()

        return HttpResponseRedirect('/purchaseorder/create')


@csrf_exempt
def savedetailtemp(request):

    if request.method == 'POST':
        print request.POST
        detailtemp = Podetailtemp()
        detailtemp.item_counter = request.POST['itemno']
        detailtemp.invitem = Inventoryitem.objects.get(pk=request.POST['id_item'])
        detailtemp.invitem_code = Inventoryitem.objects.get(pk=request.POST['id_item']).code
        detailtemp.invitem_name = Inventoryitem.objects.get(pk=request.POST['id_item']).description
        detailtemp.invitem_unitofmeasure = Inventoryitem.objects.get(pk=request.POST['id_item']).unitofmeasure.code
        detailtemp.quantity = request.POST['id_quantity']
        detailtemp.unitcost = request.POST['id_unitcost']
        detailtemp.discountrate = int(request.POST['id_discountrate'])
        detailtemp.remarks = request.POST['id_remarks']
        detailtemp.branch = Branch.objects.get(pk=5)
        detailtemp.department = Department.objects.get(pk=request.POST['id_department'])
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
            'unitcost': request.POST['id_unitcost'],
            'department': Department.objects.get(pk=request.POST['id_department']).code,
            'discountrate': request.POST['id_discountrate'],
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
            detailtemp = Podetailtemp.objects.get(item_counter=request.POST['itemno'],
                                                  secretkey=request.POST['secretkey'],
                                                  pomain=None)
            detailtemp.delete()
        except Podetailtemp.DoesNotExist:
            print "temp detail has pomain"
            detailtemp = Podetailtemp.objects.get(item_counter=request.POST['itemno'], pomain__ponum=request.POST['ponum'])
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
