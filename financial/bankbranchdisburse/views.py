import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from bankbranchdisburse.models import Bankbranchdisburse
from bank.models import Bank
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Bankbranchdisburse
    template_name = 'bankbranchdisburse/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Bankbranchdisburse.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Bankbranchdisburse
    template_name = 'bankbranchdisburse/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Bankbranchdisburse
    template_name = 'bankbranchdisburse/create.html'
    fields = ['bank', 'branch',
              'address1', 'address2', 'address3',
              'telephone1', 'telephone2',
              'contact_person', 'contact_position', 'remarks']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankbranchdisburse.add_bankbranchdisburse'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['bank'] = Bank.objects.filter(isdeleted=0).order_by('code')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/bankbranchdisburse')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Bankbranchdisburse
    template_name = 'bankbranchdisburse/edit.html'
    fields = ['bank', 'branch',
              'address1', 'address2', 'address3',
              'telephone1', 'telephone2',
              'contact_person', 'contact_position', 'remarks']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankbranchdisburse.bankbranchdisburse'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['bank'] = Bank.objects.filter(isdeleted=0).order_by('code')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['bank', 'branch',
                                        'address1', 'address2', 'address3',
                                        'telephone1', 'telephone2',
                                        'contact_person', 'contact_position', 'remarks',
                                        'modifyby', 'modifydate'])
        return HttpResponseRedirect('/bankbranchdisburse')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Bankbranchdisburse
    template_name = 'bankbranchdisburse/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('bankbranchdisburse.delete_bankbranchdisburse'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/bankbranchdisburse')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Bankbranchdisburse.objects.filter(isdeleted=0).order_by('id')
        context = {
            "title": "Bank Branch Disburse Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('bankbranchdisburse/list.html', context)