from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from requisitionform.models import Rfmain
from django.db.models import F
from django.contrib.auth.models import User
from purchaserequisitionform.models import Prfmain, Prfdetail
from purchaserequisitionform.views import deleteRfprftransactionitem
from canvasssheet.models import Csdata
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime

# Create your views here.


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Rfmain
    template_name = 'rfprfapproval/index.html'
    context_object_name = 'data_list'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        rfdata = Rfmain.objects.all().filter(isdeleted=0)

        context['rfapprovers'] = User.objects.filter(id__in=set(Rfmain.objects.values_list('designatedapprover',
                                                                                           flat=True))).\
            order_by('first_name')
        context['prfapprovers'] = User.objects.filter(id__in=set(Prfmain.objects.values_list('designatedapprover',
                                                                                             flat=True))).\
            order_by('first_name')

        if not self.request.user.has_perm('requisitionform.view_allassignrf'):
            rfdata = rfdata.filter(designatedapprover=self.request.user.id)
            context['rfapprovers'] = context['rfapprovers'].filter(id=self.request.user.id)

        context['rfpending'] = rfdata.filter(rfstatus='F').order_by('enterdate')
        # exclude approved RFs that already have dependent PRFs
        context['rfapproved'] = rfdata.filter(rfstatus='A', totalremainingquantity=F('totalquantity')).\
            order_by('enterdate')
        context['rfdisapproved'] = rfdata.filter(rfstatus='D', status='C').order_by('enterdate')

        prfdata = Prfmain.objects.all().filter(isdeleted=0, status='A')

        if not self.request.user.has_perm('purchaserequisitionform.view_allassignprf'):
            prfdata = prfdata.filter(designatedapprover=self.request.user.id)
            context['prfapprovers'] = context['prfapprovers'].filter(id=self.request.user.id)

        context['prfpending'] = prfdata.filter(prfstatus='F').order_by('enterdate')

        # exclude approved PRFs that already have dependent CSs (prfmain_id is used in csdata)
        csdata_exclude = Csdata.objects.filter(isdeleted=0, csmain__isnull=False)
        context['prfapproved'] = prfdata.filter(prfstatus='A').\
            exclude(id__in=set(csdata_exclude.values_list('prfmain', flat=True))).order_by('enterdate')

        context['prfdisapproved'] = prfdata.filter(prfstatus='D').order_by('enterdate')

        context['formtype'] = 'ALL'
        context['formrfapprover'] = 'ALL'
        context['formprfapprover'] = 'ALL'

        if self.request.method == 'GET':
            if 'selectrfapprover' in self.request.GET:
                if self.request.GET['selectrfapprover'] != 'ALL':
                    context['rfpending'] = context['rfpending'].filter(designatedapprover=self.request.GET['selectrfapprover']).\
                        order_by('enterdate')
                    context['rfapproved'] = context['rfapproved'].filter(designatedapprover=self.request.GET['selectrfapprover']).\
                        order_by('enterdate')
                    context['rfdisapproved'] = context['rfdisapproved'].filter(designatedapprover=self.request.GET['selectrfapprover']).\
                        order_by('enterdate')
                    context['formrfapprover'] = self.request.GET['selectrfapprover']
            if 'selectprfapprover' in self.request.GET:
                if self.request.GET['selectprfapprover'] != 'ALL':
                    context['prfpending'] = context['prfpending'].filter(designatedapprover=self.request.GET['selectprfapprover']). \
                        order_by('enterdate')
                    context['prfapproved'] = context['prfapproved'].filter(designatedapprover=self.request.GET['selectprfapprover']). \
                        order_by('enterdate')
                    context['prfdisapproved'] = context['prfdisapproved'].filter(designatedapprover=self.request.GET['selectprfapprover']). \
                        order_by('enterdate')
                    context['formprfapprover'] = self.request.GET['selectprfapprover']
            if 'selecttype' in self.request.GET:
                if self.request.GET['selecttype'] == 'RF':
                    context['prfpending'] = context['prfpending'][0:0]
                    context['prfapproved'] = context['prfapproved'][0:0]
                    context['prfdisapproved'] = context['prfdisapproved'][0:0]
                    context['formtype'] = 'RF'
                elif self.request.GET['selecttype'] == 'PRF':
                    context['rfpending'] = context['rfpending'][0:0]
                    context['rfapproved'] = context['rfapproved'][0:0]
                    context['rfdisapproved'] = context['rfdisapproved'][0:0]
                    context['formtype'] = 'PRF'

        if not self.request.user.has_perm('requisitionform.view_assignrf') and not self.request.user.has_perm(
                'requisitionform.view_allassignrf'):
            context['rfpending'] = context['rfpending'][0:0]
            context['rfapproved'] = context['rfapproved'][0:0]
            context['rfdisapproved'] = context['rfdisapproved'][0:0]

        if not self.request.user.has_perm('purchaserequisitionform.view_assignprf') and not self.request.user.has_perm(
                'purchaserequisitionform.view_allassignprf'):
            context['prfpending'] = context['prfpending'][0:0]
            context['prfapproved'] = context['prfapproved'][0:0]
            context['prfdisapproved'] = context['prfdisapproved'][0:0]

        return context


@csrf_exempt
def approve(request):

    if request.method == 'POST':
        print request.POST['main_id']
        print request.POST['response']
        print request.POST['main_type']
        print request.POST['remarks']

        valid = True

        if request.POST['main_type'] == 'RF':
            if request.POST['response'] == 'A' and request.user.has_perm('requisitionform.can_approverf'):
                approve = Rfmain.objects.get(pk=request.POST['main_id'])
                approve.rfstatus = request.POST['response']
            elif request.POST['response'] == 'D' and request.user.has_perm('requisitionform.can_disapproverf'):
                approve = Rfmain.objects.get(pk=request.POST['main_id'])
                approve.rfstatus = request.POST['response']
                approve.isdeleted = 0
                approve.status = 'C'
            else:
                valid = False

        elif request.POST['main_type'] == 'PRF':
            if request.POST['response'] == 'A' and request.user.has_perm('purchaserequisitionform.can_approveprf'):
                approve = Prfmain.objects.get(pk=request.POST['main_id'])
                approve.prfstatus = request.POST['response']
            elif request.POST['response'] == 'D' and request.user.has_perm('purchaserequisitionform.can_disapproveprf'):
                approve = Prfmain.objects.get(pk=request.POST['main_id'])
                approve.prfstatus = request.POST['response']
                approve.status = 'C'

                prfdetail = Prfdetail.objects.filter(prfmain=request.POST['main_id'])
                for data in prfdetail:
                    deleteRfprftransactionitem(data)
            else:
                valid = False

        else:
            valid = False

        if valid:
            approve.approverresponse = request.POST['response']
            approve.responsedate = datetime.datetime.now()
            approve.remarks = request.POST['remarks']
            approve.actualapprover = User.objects.get(pk=request.user.id)
            approve.save()

        data = {
            'status': 'success',
            'valid': valid,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)
