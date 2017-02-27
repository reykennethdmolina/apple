from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from jvtype.models import Jvtype
from currency.models import Currency
from branch.models import Branch
from department.models import Department
from journalvoucher.models import Jvmain
from chartofaccount.models import Chartofaccount
from potype.models import Potype
import datetime
from random import randint

# Create your views here.

@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Jvmain
    template_name = 'journalvoucher/create.html'
    fields = ['jvdate', 'jvtype', 'refnum', 'particular', 'branch', 'currency', 'department']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['chartofaccount'] = Chartofaccount.objects.filter(isdeleted=0).order_by('accountcode')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['jvtype'] = Jvtype.objects.filter(isdeleted=0).order_by('pk')
        return context

    # def dispatch(self, request, *args, **kwargs):
    #     if not request.user.has_perm('bank.change_bank'):
    #         raise Http404
    #     return super(UpdateView, self).dispatch(request, *args, **kwargs)

    # def post(self, request, *args, **kwargs):
    #     self.object.jvnum = random(10)
    #     return super(CreateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # Get JVYear
        jvyear = form.cleaned_data['jvdate'].year
        num = len(Jvmain.objects.all().filter(jvdate__year=jvyear)) + 1
        padnum = '{:06d}'.format(num)

        self.object.jvnum = str(jvyear)+str(padnum)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        mainid = self.object.id

        # Save Data To JVDetail
        # detail = Potype()
        # detail.modifyby = self.request.user
        # detail.modifydate = datetime.datetime.now()
        # detail.save()

        return HttpResponseRedirect('/journalvoucher/create')