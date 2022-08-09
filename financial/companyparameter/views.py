import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from company.models import Company
from . models import Companyparameter
from chartofaccount.models import Chartofaccount
from bankaccount.models import Bankaccount
from employee.models import Employee
from django.contrib.auth.models import User
from ofsubtype.models import Ofsubtype
from oftype.models import Oftype
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Companyparameter
    template_name = 'companyparameter/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Companyparameter.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Companyparameter
    template_name = 'companyparameter/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Companyparameter
    template_name = 'companyparameter/create.html'
    fields = ['code', 'description', 'address1', 'address2', 'telno1', 'telno2',
              'zipcode', 'contactperson_acctg1',
              'contactperson_acctg2', 'contactperson_it1', 'contactperson_it2',
              'contactperson_other1',
              'contactperson_other2', 'sssnum', 'tinnum', 'rescertnum',
              'issued_at', 'issued_date',
              'wtaxsign_name', 'wtaxsign_tin', 'wtaxsign_position', 'company',
              'report_footer1', 'report_footer2', 'report_footer3', 'report_footer4',
              'report_footer5', 'report_footer6', 'report_footer7', 'report_footer8',
              'report_footer9', 'report_footer10', 'report_footer11', 'report_footer12',
              'report_footer13', 'report_footer14',
              'pcv_meal_budget_limit', 'pcv_meal_expenses',
              'coa_retainedearnings', 'coa_currentearnings', 'coa_incometaxespayable', 'coa_provisionincometax',
              'coa_cashinbank', 'coa_aptrade',
              'coa_inputvat', 'coa_deferredinputvat', 'coa_outputvat', 'coa_ewtax',
              'coa_unsubscribe', 'coa_subsrev',
              'def_bankaccount',
              'last_closed_date', 'income_tax_rate',
              'budgetapprover', 'pcv_initial_approver', 'pcv_final_approver',
              'rfv_initial_approver', 'rfv_final_approver']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('companyparameter.add_companyparameter'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['company'] = Company.objects.filter(isdeleted=0).order_by('description')

        # context['pcv_meal_expenses'] = Ofsubtype.objects.all().filter(code='ME').order_by('code')

        context['coa_retainedearnings'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_currentearnings'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_incometaxespayable'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_provisionincometax'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')

        context['coa_cashinbank'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_aptrade'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_inputvat'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_deferredinputvat'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_outputvat'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_ewtax'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_unsubscribe'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_subsrev'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['def_bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')

        context['budgetapprover'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['pcv_initial_approver'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['pcv_final_approver'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['rfv_initial_approver'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['rfv_final_approver'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/companyparameter')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Companyparameter
    template_name = 'companyparameter/edit.html'
    fields = ['code', 'description', 'address1', 'address2', 'telno1', 'telno2',
              'zipcode', 'contactperson_acctg1',
              'contactperson_acctg2', 'contactperson_it1',
              'contactperson_it2', 'contactperson_other1',
              'contactperson_other2', 'sssnum', 'tinnum', 'rescertnum',
              'issued_at', 'issued_date',
              'wtaxsign_name', 'wtaxsign_tin', 'wtaxsign_position', 'company',
              'report_footer1', 'report_footer2', 'report_footer3', 'report_footer4',
              'report_footer5', 'report_footer6', 'report_footer7', 'report_footer8',
              'report_footer9', 'report_footer10', 'report_footer11', 'report_footer12',
              'report_footer13', 'report_footer14',
              'pcv_meal_budget_limit', 'pcv_meal_expenses',
              'coa_retainedearnings', 'coa_currentearnings', 'coa_incometaxespayable', 'coa_provisionincometax',
              'coa_cashinbank', 'coa_aptrade',
              'coa_inputvat', 'coa_deferredinputvat', 'coa_outputvat', 'coa_ewtax',
              'coa_unsubscribe', 'coa_subsrev',
              'def_bankaccount',
              'last_closed_date', 'income_tax_rate',
              'budgetapprover', 'pcv_initial_approver', 'pcv_final_approver',
              'rfv_initial_approver', 'rfv_final_approver']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('companyparameter.change_companyparameter'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['company'] = Company.objects.filter(isdeleted=0).order_by('description')

        # context['pcv_meal_expenses'] = Ofsubtype.objects.all().filter(code='ME').order_by('code')

        context['coa_retainedearnings'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_currentearnings'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_incometaxespayable'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_provisionincometax'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')

        context['coa_cashinbank'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_aptrade'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_inputvat'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_deferredinputvat'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_outputvat'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_ewtax'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_unsubscribe'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['coa_subsrev'] = Chartofaccount.objects.all().filter(accounttype='P').order_by('accountcode')
        context['def_bankaccount'] = Bankaccount.objects.filter(isdeleted=0).order_by('code')

        context['budgetapprover'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['pcv_initial_approver'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['pcv_final_approver'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['rfv_initial_approver'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')
        context['rfv_final_approver'] = User.objects.filter(is_active=1).exclude(username='admin').order_by('first_name')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save(update_fields=['description', 'address1', 'address2', 'telno1',
                                        'telno2', 'zipcode',
                                        'contactperson_acctg1', 'contactperson_acctg2',
                                        'contactperson_it1',
                                        'contactperson_it2', 'contactperson_other1',
                                        'contactperson_other2', 'sssnum',
                                        'tinnum', 'rescertnum', 'issued_at', 'issued_date',
                                        'wtaxsign_name',
                                        'wtaxsign_tin', 'wtaxsign_position', 'modifyby',
                                        'modifydate', 'company',
                                        'pcv_meal_budget_limit',
                                        'report_footer1', 'report_footer2', 'report_footer3',
                                        'report_footer4', 'report_footer5', 'report_footer6',
                                        'report_footer7', 'report_footer8', 'report_footer9',
                                        'report_footer10', 'report_footer11', 'report_footer12',
                                        'report_footer13', 'report_footer14',
                                        'coa_retainedearnings', 'coa_currentearnings', 'coa_incometaxespayable', 'coa_provisionincometax',
                                        'coa_cashinbank', 'coa_aptrade',
                                        'coa_inputvat', 'coa_deferredinputvat', 'coa_outputvat', 'coa_ewtax',
                                        'coa_unsubscribe', 'coa_subsrev',
                                        'def_bankaccount',
                                        'last_closed_date', 'income_tax_rate',
                                        'budgetapprover', 'pcv_initial_approver', 'pcv_final_approver',
                                        'rfv_initial_approver', 'rfv_final_approver'])
        return HttpResponseRedirect('/companyparameter')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Companyparameter
    template_name = 'companyparameter/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('companyparameter.delete_companyparameter'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/companyparameter')

@csrf_exempt
def view(request):

    code = request.GET["code"]

    if code == 'f8505470e5e0e434fd83008577a862cc2faf5a10f5a3b62bf69cf9697c215010':
        data = Companyparameter.objects.filter(isdeleted=0,pk=3).values()
        return JsonResponse({'status': 'valid', 'data': list(data)})
    else:
        #return str('invalid')
        return JsonResponse({'status': 'invalid'})