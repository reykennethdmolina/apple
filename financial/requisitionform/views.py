from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . models import Rfmain, Rfdetailtemp
from inventoryitemtype.models import Inventoryitemtype
from branch.models import Branch
from department.models import Department
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
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0).filter(code='SI')
        context['branch'] = Branch.objects.filter(isdeleted=0).filter(code='HO')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
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



        return HttpResponseRedirect('/requisitionform/create')


@csrf_exempt
def saverfdetailtemp(request):

    if request.method == 'POST':
        detailtemp = Rfdetailtemp()
        detailtemp.item_counter = request.POST['itemno']
        detailtemp.item_name = request.POST['id_item_name']
        detailtemp.unitofmeasure = 'kg'
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
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def deleterfdetailtemp(request):

    if request.method == 'POST':
        detailtemp = Rfdetailtemp.objects.get(item_counter=request.POST['itemno'], secretkey=request.POST['secretkey'])
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

