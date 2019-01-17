from django.views.generic import View, ListView
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from . models import Arsubtype
from chartofaccount.models import Chartofaccount
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Arsubtype
    template_name = 'arsubtype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Arsubtype.objects.all().filter(isdeleted=0).order_by('-pk')

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        chartofaccount = Chartofaccount.objects.filter(accounttype='P', isdeleted=0, main='1', clas='1').\
            exclude(id__in=set(Arsubtype.objects.values_list('arsubtypechartofaccount',
                                                             flat=True))).order_by('accountcode')
        arsubtype = Arsubtype.objects.filter(isdeleted=0).order_by('arsubtypechartofaccount__accountcode')

        arsubtypechartofaccount = []
        for data in chartofaccount:
            arsubtypechartofaccount.append({
                'id': data.id,
                'accountcode': data.accountcode,
                'description': data.description,
                'selected': 'F'
            })
        for data in arsubtype:
            arsubtypechartofaccount.append({
                'id': data.arsubtypechartofaccount.id,
                'accountcode': data.arsubtypechartofaccount.accountcode,
                'description': data.arsubtypechartofaccount.description,
                'selected': 'T'
            })

        context['arsubtypechartofaccount'] = arsubtypechartofaccount
        return context


@csrf_exempt
def savearsubtype(request):
    if request.method == 'POST':
        Arsubtype.objects.all().delete()

        for i in range(0, request.POST.getlist('selected_arsubtype[]').__len__()):
            arsubtype = Arsubtype()
            arsubtype.enterby = request.user
            arsubtype.modifyby = request.user
            arsubtype.arsubtypechartofaccount = Chartofaccount.objects.get(pk=int(request.POST.
                                                                                  getlist('selected_arsubtype[]')[i]))
            arsubtype.save()
            i += 1

        data = {
            'status': 'success',
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
        list = Arsubtype.objects.filter(isdeleted=0).order_by('arsubtypechartofaccount')
        context = {
            "title": "AR - NonTrade Masterfile List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('arsubtype/list.html', context)
