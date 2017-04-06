from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from requisitionform.models import Rfmain
from django.contrib.auth.models import User
from purchaserequisitionform.models import Prfmain
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

        rfdata = Rfmain.objects.all().filter(isdeleted=0, status='A').order_by('enterdate')
        context['rfpending'] = rfdata.filter(rfstatus='F')
        context['rfapproved'] = rfdata.filter(rfstatus='A')
        context['rfdisapproved'] = rfdata.filter(rfstatus='D')

        prfdata = Prfmain.objects.all().filter(isdeleted=0, status='A').order_by('enterdate')
        context['prfpending'] = prfdata.filter(prfstatus='F')
        context['prfapproved'] = prfdata.filter(prfstatus='A')
        context['prfdisapproved'] = prfdata.filter(prfstatus='D')




        context['prfforapproval'] = Prfmain.objects.all().filter(isdeleted=0, prfstatus='F', status='A').\
            order_by('enterdate')





        context['formtype'] = 'ALL'
        context['formrfapprover'] = 'ALL'
        context['formprfapprover'] = 'ALL'

        if self.request.method == 'GET' and 'selecttype' in self.request.GET:
            if 'selectapprover' in self.request.GET:
                if self.request.GET['selectapprover'] == 'ME':
                    context['rfforapproval'] = context['rfforapproval'].filter(
                        designatedapprover=self.request.user.id).\
                        order_by('enterdate')
                    context['prfforapproval'] = context['prfforapproval'].filter(
                        designatedapprover=self.request.user.id). \
                        order_by('enterdate')
                    context['formapprover'] = 'ME'

            if self.request.GET['selecttype'] == 'RF':
                context['prfforapproval'] = context['prfforapproval'][0:0]
                context['formtype'] = 'RF'
            elif self.request.GET['selecttype'] == 'PRF':
                context['rfforapproval'] = context['rfforapproval'][0:0]
                context['formtype'] = 'PRF'

        return context


@csrf_exempt
def approve(request):

    if request.method == 'POST':
        print request.POST['main_id']
        print request.POST['response']
        print request.POST['main_type']
        print request.POST['remarks']

        if request.POST['main_type'] == 'RF':
            approve = Rfmain.objects.get(pk=request.POST['main_id'])
            approve.rfstatus = request.POST['response']
        elif request.POST['main_type'] == 'PRF':
            approve = Prfmain.objects.get(pk=request.POST['main_id'])
            approve.prfstatus = request.POST['response']

        if request.POST['main_type'] == 'RF' or request.POST['main_type'] == 'PRF':
            approve.approverresponse = request.POST['response']
            approve.responsedate = datetime.datetime.now()
            approve.remarks = request.POST['remarks']
            approve.actualapprover = User.objects.get(pk=request.user.id)
            approve.save()

        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)
