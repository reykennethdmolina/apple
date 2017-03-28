from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . models import Prfmain
from requisitionform.models import Rfmain, Rfdetail
from purchaserequisitionform.models import Prfmain, Prfdetail, Prfdetailtemp
from inventoryitemtype.models import Inventoryitemtype
from inventoryitem.models import Inventoryitem
from branch.models import Branch
from department.models import Department
from django.contrib.auth.models import User
from acctentry.views import generatekey
from django.core import serializers
import datetime


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Prfmain
    template_name = 'purchaserequisitionform/create.html'
    fields = ['prfdate', 'inventoryitemtype', 'designatedapprover', 'prftype', 'particulars', 'department', 'branch']

    # add delete all temp unused every fresh reload

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0)
        context['branch'] = Branch.objects.filter(isdeleted=0).filter(code='HO')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
        context['invitem'] = Inventoryitem.objects.filter(isdeleted=0).order_by('inventoryitemclass__inventoryitemtype__code', 'description')
        context['rfmain'] = Rfmain.objects.filter(isdeleted=0, rfstatus='A', status='A')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        try:
            prfnumlast = Prfmain.objects.latest('prfnum')
            latestprfnum = str(prfnumlast)
            if latestprfnum[0:4] == str(datetime.datetime.now().year):
                prfnum = str(datetime.datetime.now().year)
                last = str(int(latestprfnum[4:])+1)
                zero_addon = 6 - len(last)
                for x in range(0, zero_addon):
                    prfnum += '0'
                prfnum += last
            else:
                prfnum = str(datetime.datetime.now().year) + '000001'
        except Prfmain.DoesNotExist:
            prfnum = str(datetime.datetime.now().year) + '000001'

        self.object.prfnum = prfnum

        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        detailtemp = Prfdetailtemp.objects.filter(isdeleted=0, secretkey=self.request.POST['secretkey']).\
            order_by('enterdate')
        i = 1
        for dt in detailtemp:
            detail = Prfdetail()
            detail.item_counter = i
            detail.prfmain = Prfmain.objects.get(prfnum=prfnum)
            detail.invitem_code = dt.invitem_code
            detail.invitem_name = dt.invitem_name
            detail.quantity = self.request.POST.getlist('temp_quantity')[i-1]
            detail.status = dt.status
            detail.enterby = dt.enterby
            detail.enterdate = dt.enterdate
            detail.modifyby = dt.modifyby
            detail.modifydate = dt.modifydate
            detail.postby = dt.postby
            detail.postdate = dt.postdate
            detail.isdeleted = dt.isdeleted
            detail.invitem = dt.invitem
            detail.rfdetail = dt.rfdetail
            detail.save()
            dt.delete()
            i += 1

        return HttpResponseRedirect('/purchaserequisitionform/create')

@csrf_exempt
def importItems(request):
    # validation on save
    # item no / counter validation..

    if request.method == 'POST':
        rfdetail = Rfdetail.objects\
                        .raw('SELECT inv.unitcost, '
                                    'inv.id AS inv_id, '
                                    'rfm.rfnum, '
                                    'rfd.invitem_code, '
                                    'rfd.invitem_name, '
                                    'rfd.quantity, '
                                    'rfd.remarks, '
                                    'rfd.id, '
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
            prfdata.append([data.invitem_code,
                            data.invitem_name,
                            data.code,
                            data.rfnum,
                            data.remarks,
                            data.quantity,
                            data.unitcost,
                            data.id,
                            item_counter])

            detailtemp = Prfdetailtemp()
            detailtemp.invitem_code = data.invitem_code
            detailtemp.invitem_name = data.invitem_name
            detailtemp.item_counter = item_counter
            detailtemp.quantity = data.quantity
            detailtemp.status = 'A'
            detailtemp.enterdate = datetime.datetime.now()
            detailtemp.modifydate = datetime.datetime.now()
            detailtemp.enterby = request.user
            detailtemp.modifyby = request.user
            detailtemp.secretkey = request.POST['secretkey']
            detailtemp.invitem = Inventoryitem.objects.get(pk=data.inv_id)
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
            detailtemp.status = 'A'
            detailtemp.enterdate = datetime.datetime.now()
            detailtemp.modifydate = datetime.datetime.now()
            detailtemp.enterby = request.user
            detailtemp.modifyby = request.user
            detailtemp.secretkey = request.POST['secretkey']
            detailtemp.invitem = Inventoryitem.objects.get(pk=request.POST['inv_id'])
            detailtemp.save()

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

