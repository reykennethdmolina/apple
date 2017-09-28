__author__ = 'kelvin'
from django.views.generic.base import ContextMixin

from companyparameter.models import Companyparameter


class ReportContentMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(ReportContentMixin, self).get_context_data(**kwargs)

        # required contents
        context['rc_logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"
        context['rc_param'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        # context['rc_user'] = request.user

        # should be altered in views
        context['rc_pagesize'] = "letter"
        context['rc_font'] = 'arial'
        context['rc_fontsize'] = '9px'
        context['rc_orientation'] = "portrait"
        context['rc_headtitle'] = "Reports"
        context['rc_title'] = "Reports"
        return context
