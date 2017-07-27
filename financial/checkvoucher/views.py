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


# @method_decorator(login_required, name='dispatch')
# class DetailView(DetailView):
#     model = Ofmain
#     template_name = 'operationalfund/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Cvmain
    template_name = 'checkvoucher/create.html'
    fields = ['cvdate', 'cvtype', 'amount', 'refnum', 'particulars', 'vat', 'atc', 'checknum', 'checkdate',
              'inputvattype', 'deferredvat', 'currency', 'fxrate', 'branch', 'bankaccountnumber', 'bankaccountname',
              'disbursingbranch']

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
        context['disbursingbranch'] = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('pk')
        context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
        context['cvtype'] = Cvtype.objects.filter(isdeleted=0).order_by('pk')
        context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
        return context

    # def form_valid(self, form):
    #     self.object = form.save(commit=False)
    #
    #     if float(self.request.POST['amount']) <= 1000:
    #         year = str(form.cleaned_data['ofdate'].year)
    #         yearqs = Ofmain.objects.filter(ofnum__startswith=year)
    #
    #         if yearqs:
    #             ofnumlast = yearqs.latest('ofnum')
    #             latestofnum = str(ofnumlast)
    #             print "latest: " + latestofnum
    #
    #             ofnum = year
    #             last = str(int(latestofnum[4:]) + 1)
    #             zero_addon = 6 - len(last)
    #             for num in range(0, zero_addon):
    #                 ofnum += '0'
    #             ofnum += last
    #
    #         else:
    #             ofnum = year + '000001'
    #
    #         print 'ofnum: ' + ofnum
    #         print self.request.POST['payee']
    #         print self.request.POST['hiddenpayee']
    #         print self.request.POST['hiddenpayeeid']
    #         if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
    #             self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
    #             self.object.payee_code = self.object.payee.code
    #             self.object.payee_name = self.object.payee.name
    #         else:
    #             self.object.payee_name = self.request.POST['payee']
    #
    #         self.object.ofnum = ofnum
    #         self.object.enterby = self.request.user
    #         self.object.modifyby = self.request.user
    #         self.object.employee_code = Employee.objects.get(pk=self.request.POST['employee']).code
    #         self.object.employee_name = Employee.objects.get(pk=self.request.POST['employee']).firstname.\
    #             strip(' \t\n\r') + ' ' + Employee.objects.get(pk=self.request.POST['employee']).lastname.\
    #             strip(' \t\n\r')
    #         self.object.department_code = Department.objects.get(pk=self.request.POST['department']).code
    #         self.object.department_name = Department.objects.get(pk=self.request.POST['department']).departmentname
    #         self.object.ofstatus = 'I'
    #         self.object.receiveby = self.request.user
    #         self.object.receivedate = datetime.datetime.now()
    #         self.object.designatedapprover = self.request.user
    #         self.object.actualapprover = self.request.user
    #         self.object.approverresponse = 'A'
    #         self.object.responsedate = datetime.datetime.now()
    #         self.object.save()
    #
    #         return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/cashierupdate')
    #     else:
    #         return HttpResponseRedirect('/operationalfund/')


# @method_decorator(login_required, name='dispatch')
# class UpdateViewUser(UpdateView):
#     model = Ofmain
#     template_name = 'operationalfund/userupdate.html'
#     fields = ['ofnum', 'ofdate', 'amount', 'particulars', 'designatedapprover']
#
#     def dispatch(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         if not request.user.has_perm('operationalfund.change_ofmain') or self.object.isdeleted == 1 or \
#                 request.user.has_perm('operationalfund.is_cashier'):
#             raise Http404
#         return super(UpdateView, self).dispatch(request, *args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         context = super(UpdateView, self).get_context_data(**kwargs)
#         context['designatedapprover'] = User.objects.filter(is_active=1).exclude(username='admin'). \
#             order_by('first_name')
#         context['payee'] = Ofmain.objects.get(pk=self.object.id).payee.id if Ofmain.objects.get(pk=self.object.id).payee is not None else ''
#         context['payee_name'] = Ofmain.objects.get(pk=self.object.id).payee_name
#         context['ofstatus'] = Ofmain.objects.get(pk=self.object.id).get_ofstatus_display()
#         return context
#
#     def form_valid(self, form):
#         self.object = form.save(commit=False)
#
#         if self.object.ofstatus != 'A' and self.object.ofstatus != 'I' and self.object.ofstatus != 'R':
#             if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
#                 self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
#                 self.object.payee_code = self.object.payee.code
#                 self.object.payee_name = self.object.payee.name
#             else:
#                 self.object.payee = None
#                 self.object.payee_code = None
#                 self.object.payee_name = self.request.POST['payee']
#
#             self.object.modifyby = self.request.user
#             self.object.modifydate = datetime.datetime.now()
#             self.object.save(update_fields=['ofdate', 'payee', 'payee_code', 'payee_name', 'amount', 'particulars',
#                                             'designatedapprover'])
#
#         return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/userupdate')
#
#
# @method_decorator(login_required, name='dispatch')
# class UpdateViewCashier(UpdateView):
#     model = Ofmain
#     template_name = 'operationalfund/cashierupdate.html'
#     fields = ['ofnum', 'ofdate', 'oftype', 'ofsubtype', 'amount', 'refnum', 'particulars', 'creditterm', 'vat', 'atc',
#               'inputvattype', 'deferredvat', 'currency', 'fxrate', 'wtax', 'ofstatus', 'employee', 'department',
#               'remarks', 'paymentreceivedby', 'paymentreceiveddate']
#
#     def dispatch(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         if not request.user.has_perm('operationalfund.change_ofmain') or self.object.isdeleted == 1 \
#                 or not request.user.has_perm('operationalfund.is_cashier') or self.object.ofstatus == 'F' \
#                 or self.object.ofstatus == 'D':
#             raise Http404
#         elif self.object.ofstatus == 'A':
#             self.object.ofstatus = 'I'
#             self.object.receiveby = self.request.user
#             self.object.receivedate = datetime.datetime.now()
#             self.object.save(update_fields=['ofstatus', 'receiveby', 'receivedate'])
#         return super(UpdateView, self).dispatch(request, *args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         context = super(UpdateView, self).get_context_data(**kwargs)
#         context['actualapprover'] = User.objects.get(pk=self.object.actualapprover.id).first_name + ' ' + \
#             User.objects.get(pk=self.object.actualapprover.id).last_name
#         context['atc'] = Ataxcode.objects.filter(isdeleted=0).order_by('pk')
#         context['creditterm'] = Creditterm.objects.filter(isdeleted=0).order_by('pk')
#         context['currency'] = Currency.objects.filter(isdeleted=0).order_by('pk')
#         context['department'] = Department.objects.filter(isdeleted=0).order_by('departmentname')
#         context['employee'] = Employee.objects.filter(isdeleted=0, status='A').order_by('lastname')
#         context['inputvattype'] = Inputvattype.objects.filter(isdeleted=0).order_by('pk')
#         context['oftype'] = Oftype.objects.filter(isdeleted=0).order_by('pk')
#         context['ofsubtype'] = Ofsubtype.objects.filter(isdeleted=0).order_by('pk')
#         context['vat'] = Vat.objects.filter(isdeleted=0, status='A').order_by('pk')
#         context['wtax'] = Wtax.objects.filter(isdeleted=0, status='A').order_by('pk')
#         context['payee'] = Ofmain.objects.get(pk=self.object.id).payee.id if Ofmain.objects.get(
#             pk=self.object.id).payee is not None else ''
#         context['payee_name'] = Ofmain.objects.get(pk=self.object.id).payee_name
#         context['originalofstatus'] = 'A' if self.object.creditterm is None else Ofmain.objects.get(pk=self.object.id).ofstatus
#         return context
#
#     def form_valid(self, form):
#         self.object = form.save(commit=False)
#
#         if self.request.POST['originalofstatus'] != 'R':
#             if self.request.POST['payee'] == self.request.POST['hiddenpayee']:
#                 self.object.payee = Supplier.objects.get(pk=self.request.POST['hiddenpayeeid'])
#                 self.object.payee_code = self.object.payee.code
#                 self.object.payee_name = self.object.payee.name
#             else:
#                 self.object.payee = None
#                 self.object.payee_code = None
#                 self.object.payee_name = self.request.POST['payee']
#
#             self.object.modifyby = self.request.user
#             self.object.modifydate = datetime.datetime.now()
#             self.object.save(update_fields=['ofdate', 'oftype', 'ofsubtype', 'amount', 'refnum', 'particulars',
#                                             'creditterm', 'vat', 'atc', 'inputvattype', 'deferredvat', 'currency',
#                                             'fxrate', 'wtax', 'ofstatus', 'employee', 'department', 'remarks', 'payee',
#                                             'payee_code', 'payee_name', 'modifyby', 'modifydate'])
#
#             # revert status from RELEASED to In Process if no release date is saved
#             if self.object.ofstatus == 'R' and self.object.releasedate is None:
#                 self.object.releaseby = None
#                 self.object.releasedate = None
#                 self.object.paymentreceivedby = None
#                 self.object.paymentreceiveddate = None
#                 self.object.ofstatus = 'I'
#                 self.object.save(update_fields=['releaseby', 'releasedate', 'paymentreceivedby', 'paymentreceiveddate',
#                                                 'ofstatus'])
#
#             # remove release details if OFSTATUS is not RELEASED
#             if self.object.ofstatus != 'R':
#                 self.object.releaseby = None
#                 self.object.releasedate = None
#                 self.object.paymentreceivedby = None
#                 self.object.paymentreceiveddate = None
#                 self.object.save(update_fields=['releaseby', 'releasedate', 'paymentreceivedby', 'paymentreceiveddate'])
#
#         else:
#             self.object.modifyby = self.request.user
#             self.object.modifydate = datetime.datetime.now()
#             self.object.save(update_fields=['modifyby', 'modifydate', 'remarks'])
#
#         return HttpResponseRedirect('/operationalfund/' + str(self.object.id) + '/cashierupdate')
#
#
# @method_decorator(login_required, name='dispatch')
# class DeleteView(DeleteView):
#     model = Ofmain
#     template_name = 'operationalfund/delete.html'
#
#     def dispatch(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         if not request.user.has_perm('operationalfund.delete_ofmain') or self.object.status == 'O' \
#                 or self.object.ofstatus == 'A':
#             raise Http404
#         return super(DeleteView, self).dispatch(request, *args, **kwargs)
#
#     def delete(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         self.object.modifyby = self.request.user
#         self.object.modifydate = datetime.datetime.now()
#         self.object.isdeleted = 1
#         self.object.status = 'C'
#         self.object.ofstatus = 'D'
#         self.object.save()
#
#         return HttpResponseRedirect('/operationalfund')


@csrf_exempt
def getsupplierdata(request):
    if request.method == 'POST':
        supplier = Supplier.objects.get(pk=request.POST['supplierid'])
        data = {
            'status': 'success',
            'creditterm': supplier.creditterm.id,
            'vat': supplier.vat.id,
            'atc': supplier.atc.id,
            'inputvattype': supplier.inputvattype.id,
            'deferredvat': supplier.deferredvat,
            'currency': supplier.currency.id,
            'fxrate': supplier.fxrate,
            'bankaccountnumber': supplier.bankaccountnumber,
            'bankaccountname': supplier.bankaccountname,
        }
    else:
        data = {
            'status': 'error',
        }
    return JsonResponse(data)

