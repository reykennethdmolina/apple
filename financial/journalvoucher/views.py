from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from bank.models import Bank
import datetime

# Create your views here.

@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Bank
    template_name = 'journalvoucher/create.html'
    fields = ['code', 'description']