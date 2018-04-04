import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from subledgersummary.models import Subledgersummary


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Subledgersummary
    template_name = 'transactionclosing/index.html'
    context_object_name = 'data_list'
