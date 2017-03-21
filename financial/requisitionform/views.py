from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from . models import Rfmain
from journalvoucher.models import Jvmain
from inventoryitemtype.models import Inventoryitemtype
from branch.models import Branch
from department.models import Department
from acctentry.views import generatekey
import datetime

# Create your views here.


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Rfmain
    template_name = 'requisitionform/create.html'
    fields = ['rfnum', 'rfdate', 'inventoryitemtype', 'refnum', 'jonum', 'sonum', 'urgencytype', 'dateneeded',
              'branch', 'department', 'particulars', 'rfstatus', 'designatedapprover']

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['inventoryitemtype'] = Inventoryitemtype.objects.filter(isdeleted=0).filter(code='SI')
        context['branch'] = Branch.objects.filter(isdeleted=0).filter(code='HO')
        context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
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

        return HttpResponseRedirect('/requisitionform/create')
