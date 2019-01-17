from django.views.generic import View, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from chartofaccountmaingroup.models import ChartofAccountMainGroup
from chartofaccountsubgroup.models import ChartofAccountSubGroup
from . models import MainGroupSubgroup
from django.core import serializers
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter


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


@csrf_exempt
def getsubgroups(request):
    if request.method == 'POST':
        maingroup = request.POST['maingroup']
        subgroup = MainGroupSubgroup.objects.filter(main=maingroup, isdeleted=0, sub__isdeleted=0)

        subgroup_list = []

        for data in subgroup:
            subgroup_list.append([data.sub.pk,
                                  data.sub.code,
                                  data.sub.description,
                                  ])

        data = {
            'status': 'success',
            'subgroup': subgroup_list,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = MainGroupSubgroup.objects.filter(isdeleted=0).order_by('main_id', 'sub_id')
        context = {
            "title": "Chart of Account Grouping Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('chartofaccountmainsubgroup/list.html', context)