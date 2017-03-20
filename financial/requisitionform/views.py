from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from journalvoucher.models import Jvmain
from potype.models import Potype
from supplier.models import Supplier
from ataxcode.models import Ataxcode
from inputvat.models import Inputvat
from vat.models import Vat
from creditterm.models import Creditterm
from acctentry.views import generatekey
import datetime

# Create your views here.


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Jvmain
    template_name = 'requisitionform/create.html'
    fields = ['jvdate', 'jvtype', 'refnum', 'particular', 'branch', 'currency', 'department']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['potype'] = Potype.objects.filter(isdeleted=0).order_by('pk')
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('pk')
        context['ataxcode'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['inputvat'] = Inputvat.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0).order_by('pk')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        return context

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

        return HttpResponseRedirect('/purchaseorder/create')
