from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from jvtype.models import Jvtype
from currency.models import Currency
from branch.models import Branch
from department.models import Department
from bank.models import Bank
import datetime

# Create your views here.

@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Bank
    template_name = 'journalvoucher/create.html'
    fields = ['code', 'description']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['department'] = Department.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('pk')
        return context
