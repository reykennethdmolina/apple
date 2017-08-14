from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from ataxcode.models import Ataxcode
from bankaccount.models import Bankaccount
from bankbranchdisburse.models import Bankbranchdisburse
from branch.models import Branch
from creditterm.models import Creditterm
from currency.models import Currency
from inputvattype.models import Inputvattype
from cvtype.models import Cvtype
from supplier.models import Supplier
from vat.models import Vat
from . models import Dcmain
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Dcmain
    template_name = 'debitcreditmemo/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Dcmain.objects.all().order_by('-enterdate')[0:10]
