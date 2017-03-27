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
    fields = ['prftype', 'prfstatus']

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

    # def form_valid(self, form):
    #     self.object = form.save(commit=False)
    #
    #     try:
    #         rfnumlast = Rfmain.objects.latest('rfnum')
    #         latestrfnum = str(rfnumlast)
    #         if latestrfnum[0:4] == str(datetime.datetime.now().year):
    #             rfnum = str(datetime.datetime.now().year)
    #             last = str(int(latestrfnum[4:])+1)
    #             zero_addon = 6 - len(last)
    #             for x in range(0, zero_addon):
    #                 rfnum += '0'
    #             rfnum += last
    #         else:
    #             rfnum = str(datetime.datetime.now().year) + '000001'
    #     except Rfmain.DoesNotExist:
    #         rfnum = str(datetime.datetime.now().year) + '000001'
    #
    #     print 'rfnum: ' + rfnum
    #     self.object.rfnum = rfnum
    #
    #     self.object.enterby = self.request.user
    #     self.object.modifyby = self.request.user
    #     self.object.save()



        # return HttpResponseRedirect('/purchaserequisitionform/create')


@csrf_exempt
def importItems(request):

    # insert saving to temp
    # update newly imported items
    # validation on save

    if request.method == 'POST':
        rfdetail = Rfdetail.objects\
                        .raw('SELECT inv.unitcost, '
                                    'rfm.refnum, '
                                    'rfd.invitem_code, '
                                    'rfd.invitem_name, '
                                    'rfd.quantity, '
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

        rfdata = []

        for data in rfdetail:
            rfdata.append([data.invitem_code, data.invitem_name, data.code, data.refnum, data.quantity, data.unitcost,  data.id])

        detailtemp = Prfdetailtemp()
        detailtemp.invitem_code = request.POST['id_item_name']
        detailtemp.invitem_name = request.POST['id_item_name']
        detailtemp.item_counter = request.POST['itemno']
        detailtemp.quantity = request.POST['quantity']
        detailtemp.status = 'A'
        detailtemp.enterdate = datetime.datetime.now()
        detailtemp.modifydate = datetime.datetime.now()
        detailtemp.enterby = request.user
        detailtemp.modifyby = request.user
        detailtemp.secretkey = request.POST['secretkey']
        detailtemp.invitem = request.POST['id_item_name']
        detailtemp.rfdetail = request.POST['id_item_name']

        # detailtemp.unitofmeasure = 'kg'
        # detailtemp.quantity = request.POST['id_quantity']
        # detailtemp.remarks = request.POST['id_remarks']
        # detailtemp.save()

        data = {
            'status': 'success',
            'rfdata': rfdata,
        }
    else:
        data = {
            'status': 'error',
            # 'rfdetail': serializers.serialize('json', rfdetail),
        }

    return JsonResponse(data)


# @csrf_exempt
# def savedetailtemp(request):
#
#     if request.method == 'POST':
#         detailtemp = Rfdetailtemp()
#         detailtemp.item_counter = request.POST['itemno']
#         detailtemp.item_name = request.POST['id_item_name']
#         detailtemp.unitofmeasure = 'kg'
#         detailtemp.quantity = request.POST['id_quantity']
#         detailtemp.remarks = request.POST['id_remarks']
#         detailtemp.secretkey = request.POST['secretkey']
#         detailtemp.status = 'A'
#         detailtemp.enterdate = datetime.datetime.now()
#         detailtemp.modifydate = datetime.datetime.now()
#         detailtemp.enterby = request.user
#         detailtemp.modifyby = request.user
#         detailtemp.save()
#
#         data = {
#             'status': 'success',
#             'itemno': request.POST['itemno'],
#             'quantity': request.POST['id_quantity'],
#         }
#     else:
#         data = {
#             'status': 'error',
#         }
#
#     return JsonResponse(data)
#
#
# @csrf_exempt
# def deletedetailtemp(request):
#
#     if request.method == 'POST':
#         detailtemp = Rfdetailtemp.objects.get(item_counter=request.POST['itemno'], secretkey=request.POST['secretkey'])
#         detailtemp.isdeleted = 1
#         detailtemp.save()
#
#         data = {
#             'status': 'success',
#         }
#     else:
#         data = {
#             'status': 'error',
#         }
#
#     return JsonResponse(data)

