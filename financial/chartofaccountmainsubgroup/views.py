from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from chartofaccountmaingroup.models import ChartofAccountMainGroup
from chartofaccountsubgroup.models import ChartofAccountSubGroup
from . models import MainGroupSubgroup


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = MainGroupSubgroup
    template_name = 'chartofaccountmainsubgroup/index.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['main_groups'] = ChartofAccountMainGroup.objects.filter(isdeleted=0, status='A').order_by('code')

        if self.request.GET:
            if 'selected_main_group' in self.request.GET:
                context['all_subgroups'] = ChartofAccountSubGroup.objects.filter(isdeleted=0, status='A').\
                    order_by('code')
                context['selected_subgroups'] = MainGroupSubgroup.objects.\
                    filter(isdeleted=0, main=int(self.request.GET['selected_main_group'])).\
                    order_by('sub__code')

        return context


@csrf_exempt
def savesubgroups(request):
    if request.method == 'POST':
        MainGroupSubgroup.objects.filter(main=int(request.POST['selected_main_group'])).delete()

        for i in range(0, request.POST.getlist('selected_subgroups[]').__len__()):
            maingroupsubgroup = MainGroupSubgroup()
            maingroupsubgroup.main = ChartofAccountMainGroup.objects.filter(pk=int(
                request.POST['selected_main_group'])).first()
            maingroupsubgroup.sub = ChartofAccountSubGroup.objects.filter(pk=int(
                request.POST.getlist('selected_subgroups[]')[i])).first()
            maingroupsubgroup.enterby = request.user
            maingroupsubgroup.modifyby = request.user
            maingroupsubgroup.save()
            i += 1

        data = {
            'status': 'success',
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)
