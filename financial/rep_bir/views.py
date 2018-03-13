from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from purchaseorder.models import Pomain


@method_decorator(login_required, name='dispatch')
class BirPurchaseBook(TemplateView):
    template_name = 'rep_bir/birpurchasebook.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Pomain.objects.filter(status='A', isdeleted=0)

        if self.request.GET:

            if self.request.GET['rep_datefrom']:
                key_data = str(self.request.GET['rep_datefrom'])
                query = query.filter(podate__gte=key_data)
            if self.request.GET['rep_dateto']:
                key_data = str(self.request.GET['rep_dateto'])
                query = query.filter(podate__lte=key_data)
            if self.request.GET['rep_postatus']:
                key_data = str(self.request.GET['rep_postatus'])
                query = query.filter(postatus=key_data)

            context['rep_datefrom'] = self.request.GET['rep_datefrom']
            context['rep_dateto'] = self.request.GET['rep_dateto']
            context['rep_postatus'] = self.request.GET['rep_postatus']

        context['query'] = query

        return self.render_to_response(context)
