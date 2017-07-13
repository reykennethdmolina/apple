from django.views.generic import ListView, CreateView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from acctentry.views import generatekey
from employee.models import Employee
from supplier.models import Supplier
from . models import Ofmain
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Ofmain
    template_name = 'operationalfund/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Ofmain.objects.all().order_by('-enterdate')[0:10]

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['listcount'] = Ofmain.objects.all().count()
        context['forapproval'] = Ofmain.objects.filter(designatedapprover=self.request.user).count()
        return context


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Ofmain
    template_name = 'operationalfund/create.html'
    fields = ['ofdate', 'amount', 'particulars', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('operationalfund.add_ofmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['secretkey'] = generatekey(self)
        context['payee'] = Employee.objects.filter(isdeleted=0).order_by('pk')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if float(self.request.POST['amount'])  <= 1000:
            year = str(form.cleaned_data['ofdate'].year)
            yearqs = Ofmain.objects.filter(ofnum__startswith=year)

            if yearqs:
                ofnumlast = yearqs.latest('ofnum')
                latestofnum = str(ofnumlast)
                print "latest: " + latestofnum

                ofnum = year
                last = str(int(latestofnum[4:]) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    ofnum += '0'
                ofnum += last

            else:
                ofnum = year + '000001'

            print 'ofnum: ' + ofnum
            print self.request.POST['payee']
            print self.request.POST['hiddenpayee']
            print self.request.POST['hiddenpayeeid']
            if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
                self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
                self.object.payee_code = self.object.payee.code
                self.object.payee_name = self.object.payee.name
            else:
                self.object.payee_name = self.request.POST['payee']

            self.object.ofnum = ofnum
            self.object.enterby = self.request.user
            self.object.modifyby = self.request.user
            self.object.save()

        # return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/update')
        return HttpResponseRedirect('/operationalfund/')


@csrf_exempt
def approve(request):
    valid = True
    return valid
    # if request.method == 'POST':
    #     valid = True
    #
    #     if request.POST['response'] == 'A' and request.user.has_perm('operational.can_approverf'):
    #         approve = Rfmain.objects.get(pk=request.POST['main_id'])
    #         approve.rfstatus = request.POST['response']
    #     elif request.POST['response'] == 'D' and request.user.has_perm('requisitionform.can_disapproverf'):
    #         approve = Rfmain.objects.get(pk=request.POST['main_id'])
    #         approve.rfstatus = request.POST['response']
    #         approve.isdeleted = 0
    #         approve.status = 'C'
    #     else:
    #         valid = False
    #
    #     if valid:
    #         approve.approverresponse = request.POST['response']
    #         approve.responsedate = datetime.datetime.now()
    #         approve.remarks = request.POST['remarks']
    #         approve.actualapprover = User.objects.get(pk=request.user.id)
    #         approve.save()
    #
    #     data = {
    #         'status': 'success',
    #         'valid': valid,
    #     }
    # else:
    #     data = {
    #         'status': 'error',
    #     }
    #
    # return JsonResponse(data)
