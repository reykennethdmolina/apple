import datetime
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from chartofaccountmaingroup.models import ChartofAccountMainGroup
from chartofaccountsubgroup.models import ChartofAccountSubGroup


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'generalledgerbook/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        context['coa_maingroup'] = ChartofAccountMainGroup.objects.filter(status='A', isdeleted=0).order_by('code')
        context['coa_subgroup'] = ChartofAccountSubGroup.objects.filter(status='A', isdeleted=0).order_by('code')

        return context
