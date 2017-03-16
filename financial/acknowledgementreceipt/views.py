from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
# from acknowledgementreceipt.models import Acknowledgementreceipt
from journalvoucher.models import Jvmain


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Jvmain
    template_name = 'acknowledgementreceipt/create.html'
    fields = ['jvdate', 'jvtype', 'refnum', 'particular', 'branch', 'currency', 'department']