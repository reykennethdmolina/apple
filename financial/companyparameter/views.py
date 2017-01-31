from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Companyparameter
import datetime


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
    fields = ['code', 'description', 'address', 'telno1', 'telno2', 'zipcode', 'contactperson_acctg1',
              'contactperson_acctg2', 'contactperson_it1', 'contactperson_it2', 'contactperson_other1',
              'contactperson_other2', 'sssnum', 'tinnum', 'rescertnum', 'issued_at', 'issued_date',
              'wtaxsign_name', 'wtaxsign_tin', 'wtaxsign_position']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('companyparameter.add_companyparameter'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

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
    fields = ['code', 'description', 'address', 'telno1', 'telno2', 'zipcode', 'contactperson_acctg1',
              'contactperson_acctg2', 'contactperson_it1', 'contactperson_it2', 'contactperson_other1',
              'contactperson_other2', 'sssnum', 'tinnum', 'rescertnum', 'issued_at', 'issued_date',
              'wtaxsign_name', 'wtaxsign_tin', 'wtaxsign_position']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('companyparameter.change_companyparameter'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
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

