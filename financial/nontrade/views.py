import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from mrstype.models import Mrstype
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter
from accountspayable.models import Apmain


class IndexView(ListView):
    model = Apmain
    template_name = 'nontrade/index.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)


        return context

