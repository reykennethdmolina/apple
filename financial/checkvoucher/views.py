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
from . models import Cvmain
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Cvmain
    template_name = 'checkvoucher/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Cvmain.objects.all().order_by('-enterdate')[0:10]


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Cvmain
    template_name = 'checkvoucher/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Cvmain
    template_name = 'checkvoucher/create.html'
    fields = ['cvdate', 'cvtype', 'amount', 'refnum', 'particulars', 'vat', 'atc', 'checknum', 'checkdate',
              'inputvattype', 'deferredvat', 'currency', 'fxrate', 'branch', 'bankaccount', 'disbursingbranch',
              'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('checkvoucher.add_cvmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('pk')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        year = str(form.cleaned_data['cvdate'].year)
        yearqs = Cvmain.objects.filter(cvnum__startswith=year)

        if yearqs:
            cvnumlast = yearqs.latest('cvnum')
            latestcvnum = str(cvnumlast)
            print "latest: " + latestcvnum

            cvnum = year
            last = str(int(latestcvnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                cvnum += '0'
            cvnum += last

        else:
            cvnum = year + '000001'

        print 'cvnum: ' + cvnum
        print self.request.POST['payee']
        print self.request.POST['hiddenpayee']
        print self.request.POST['hiddenpayeeid']
        if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
            self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
            self.object.payee_code = self.object.payee.code
            self.object.payee_name = self.object.payee.name
        else:
            self.object.payee_name = self.request.POST['payee']

        self.object.cvnum = cvnum
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.cvstatus = 'F'
        self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
        self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
        self.object.save()

        return HttpResponseRedirect('/checkvoucher/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Cvmain
    template_name = 'checkvoucher/edit.html'
    fields = ['cvnum', 'cvdate', 'cvtype', 'amount', 'refnum', 'particulars', 'vat', 'atc', 'bankaccount',
              'disbursingbranch', 'inputvattype', 'deferredvat', 'currency', 'fxrate', 'cvstatus', 'remarks',
              'branch', 'checknum', 'checkdate', 'vatrate', 'atcrate', 'designatedapprover']

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('checkvoucher.change_cvmain') or self.object.isdeleted == 1:
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
        context['bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('pk')
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('pk')
        context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
        context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
            order_by('first_name')
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        context['payee'] = Cvmain.objects.get(pk=self.object.id).payee.id if Cvmain.objects.get(
            pk=self.object.id).payee is not None else ''
        context['payee_name'] = Cvmain.objects.get(pk=self.object.id).payee_name
        context['originalcvstatus'] = Cvmain.objects.get(pk=self.object.id).cvstatus
        context['actualapprover'] = None if Cvmain.objects.get(pk=self.object.id).actualapprover is None else Cvmain.objects.get(pk=self.object.id).actualapprover.id
        context['approverremarks'] = Cvmain.objects.get(pk=self.object.id).approverremarks
        context['responsedate'] = Cvmain.objects.get(pk=self.object.id).responsedate
        context['releaseby'] = Cvmain.objects.get(pk=self.object.id).releaseby
        context['releasedate'] = Cvmain.objects.get(pk=self.object.id).releasedate
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        if self.request.POST['originalcvstatus'] != 'R':
            if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
                self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
                self.object.payee_code = self.object.payee.code
                self.object.payee_name = self.object.payee.name
            else:
                self.object.payee = None
                self.object.payee_code = None
                self.object.payee_name = self.request.POST['payee']

            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.vatrate = Vat.objects.get(pk=self.request.POST['vat']).rate
            self.object.atcrate = Ataxcode.objects.get(pk=self.request.POST['atc']).rate
            self.object.save(update_fields=['cvdate', 'cvtype', 'amount', 'refnum', 'particulars', 'vat', 'atc',
                                            'bankaccount', 'disbursingbranch', 'inputvattype', 'deferredvat',
                                            'currency', 'fxrate', 'cvstatus', 'remarks', 'branch', 'checknum',
                                            'checkdate', 'vatrate', 'atcrate'])

            if self.object.cvstatus == 'F':
                print "heyy F"
                self.object.designatedapprover = User.objects.get(pk=self.request.POST['designatedapprover'])
                self.object.save(update_fields=['designatedapprover'])

            # revert status from APPROVED/DISAPPROVED to For Approval if no response date or approver response is saved
            # remove approval details if CVSTATUS is not APPROVED/DISAPPROVED
            if self.object.cvstatus == 'A' or self.object.cvstatus == 'D':
                if self.object.responsedate is None or self.object.approverresponse is None or \
                        self.object.actualapprover is None:
                    print self.object.responsedate
                    print self.object.approverresponse
                    print self.object.actualapprover
                    self.object.responsedate = None
                    self.object.approverremarks = None
                    self.object.approverresponse = None
                    self.object.actualapprover = None
                    self.object.cvstatus = 'F'
                    self.object.save(update_fields=['responsedate', 'approverremarks', 'approverresponse',
                                                    'actualapprover', 'cvstatus'])
            elif self.object.cvstatus == 'F':
                self.object.responsedate = None
                self.object.approverremarks = None
                self.object.approverresponse = None
                self.object.actualapprover = None
                self.object.save(update_fields=['responsedate', 'approverremarks', 'approverresponse',
                                                'actualapprover'])

            # revert status from RELEASED to Approved if no release date is saved
            # remove release details if CVSTATUS is not RELEASED
            if self.object.cvstatus == 'R' and self.object.releasedate is None:
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.cvstatus = 'A'
                self.object.save(update_fields=['releaseby', 'releasedate', 'cvstatus'])
            elif self.object.cvstatus != 'R':
                self.object.releaseby = None
                self.object.releasedate = None
                self.object.save(update_fields=['releaseby', 'releasedate'])

        else:
            self.object.modifyby = self.request.user
            self.object.modifydate = datetime.datetime.now()
            self.object.save(update_fields=['modifyby', 'modifydate', 'remarks'])

        return HttpResponseRedirect('/checkvoucher/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Cvmain
    template_name = 'checkvoucher/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('checkvoucher.delete_cvmain') or self.object.status == 'O' \
                or self.object.cvstatus == 'A':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.cvstatus = 'D'
        self.object.save()

        return HttpResponseRedirect('/checkvoucher')


@csrf_exempt
def approve(request):
    if request.method == 'POST':
        cv_for_approval = Cvmain.objects.get(cvnum=request.POST['cvnum'])
        if request.user.has_perm('checkvoucher.approve_allcv') or \
                request.user.has_perm('checkvoucher.approve_assignedcv'):
            if request.user.has_perm('checkvoucher.approve_allcv') or \
                    (request.user.has_perm('checkvoucher.approve_assignedcv') and
                        cv_for_approval.designatedapprover == request.user):
                if request.POST['originalcvstatus'] != 'R' or int(request.POST['backtoinprocess']) == 1:
                    cv_for_approval.cvstatus = request.POST['approverresponse']
                    cv_for_approval.isdeleted = 0
                    if request.POST['approverresponse'] == 'D':
                        cv_for_approval.status = 'C'
                    else:
                        cv_for_approval.status = 'A'
                    cv_for_approval.approverresponse = request.POST['approverresponse']
                    cv_for_approval.responsedate = request.POST['responsedate']
                    cv_for_approval.actualapprover = User.objects.get(pk=request.user.id)
                    cv_for_approval.approverremarks = request.POST['approverremarks']
                    cv_for_approval.releaseby = None
                    cv_for_approval.releasedate = None
                    cv_for_approval.save()
                    data = {
                        'status': 'success',
                        'cvnum': cv_for_approval.cvnum,
                        'newcvstatus': cv_for_approval.cvstatus,
                    }
                else:
                    data = {
                        'status': 'error',
                    }
            else:
                data = {
                    'status': 'error',
                }
        else:
            data = {
                'status': 'error',
            }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@csrf_exempt
def release(request):
    if request.method == 'POST':
        cv_for_release = Cvmain.objects.get(cvnum=request.POST['cvnum'])
        if cv_for_release.cvstatus != 'F' and cv_for_release.cvstatus != 'D':
            cv_for_release.releaseby = User.objects.get(pk=request.POST['releaseby'])
            cv_for_release.releasedate = request.POST['releasedate']
            cv_for_release.cvstatus = 'R'
            cv_for_release.save()
            data = {
                'status': 'success',
            }
        else:
            data = {
                'status': 'error',
            }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)

