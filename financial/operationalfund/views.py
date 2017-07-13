from django.views.generic import ListView, CreateView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from acctentry.views import generatekey
from employee.models import Employee
from . models import Ofmain
from django.contrib.auth.models import User


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    """This class enlists all requisition forms."""
    model = Ofmain
    template_name = 'operationalfund/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Ofmain.objects.all().order_by('-enterdate')[0:10]

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['listcount'] = Ofmain.objects.all().count()
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
        print self.request.POST['hiddenpayee']
        self.object.ofnum = ofnum
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        # if Rfdetailtemp.objects.filter(secretkey=self.request.POST['secretkey'], isdeleted=0):
        #     self.object = form.save(commit=False)
        #
        #     year = str(form.cleaned_data['rfdate'].year)
        #     yearqs = Rfmain.objects.filter(rfnum__startswith=year)
        #
        #     if yearqs:
        #         rfnumlast = yearqs.latest('rfnum')
        #         latestrfnum = str(rfnumlast)
        #         print "latest: " + latestrfnum
        #
        #         rfnum = year
        #         last = str(int(latestrfnum[4:]) + 1)
        #         zero_addon = 6 - len(last)
        #         for num in range(0, zero_addon):
        #             rfnum += '0'
        #         rfnum += last
        #
        #     else:
        #         rfnum = year + '000001'
        #
        #     print 'rfnum: ' + rfnum
        #     self.object.rfnum = rfnum
        #     self.object.enterby = self.request.user
        #     self.object.modifyby = self.request.user
        #     self.object.totalremainingquantity = self.request.POST['totalquantity']
        #     self.object.save()
        #
        #     detailtemp = Rfdetailtemp.objects.filter(isdeleted=0,
        #                                              secretkey=self.request.
        #                                              POST['secretkey']). \
        #         order_by('enterdate')
        #     i = 1
        #     for dt in detailtemp:
        #         detail = Rfdetail()
        #         detail.item_counter = i
        #         detail.rfmain = Rfmain.objects.get(rfnum=rfnum)
        #         detail.invitem = dt.invitem
        #         detail.invitem_code = dt.invitem_code
        #         detail.invitem_name = dt.invitem_name
        #         detail.invitem_unitofmeasure = Unitofmeasure.objects \
        #             .get(code=self.request.POST
        #                  .getlist('temp_item_um')[i - 1],
        #                  isdeleted=0, status='A')
        #         detail.invitem_unitofmeasure_code = Unitofmeasure.objects \
        #             .get(code=self.request.POST.getlist('temp_item_um')[i - 1],
        #                  isdeleted=0, status='A').code
        #         detail.quantity = self.request.POST.getlist('temp_quantity')[i - 1]
        #         detail.remarks = self.request.POST.getlist('temp_remarks')[i - 1]
        #         detail.status = dt.status
        #         detail.enterby = dt.enterby
        #         detail.enterdate = dt.enterdate
        #         detail.modifyby = dt.modifyby
        #         detail.modifydate = dt.modifydate
        #         detail.postby = dt.postby
        #         detail.postdate = dt.postdate
        #         detail.isdeleted = dt.isdeleted
        #         detail.prfremainingquantity = self.request.POST.getlist('temp_quantity')[i - 1]
        #         detail.save()
        #         dt.delete()
        #         i += 1

        # return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/update')
        return HttpResponseRedirect('/operationalfund/')
