import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404

from triplecvariousaccount.models import Triplecvariousaccount
from .models import Triplecclassification
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Triplecclassification
    template_name = 'triplecclassification/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Triplecclassification.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Triplecclassification
    template_name = 'triplecclassification/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Triplecclassification
    template_name = 'triplecclassification/create.html'
    fields = ['code', 'description', 'various_account', 'various_account2']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecclassification.add_triplecclassification'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/triplecclassification')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Triplecclassification
    template_name = 'triplecclassification/edit.html'
    fields = ['code', 'description', 'various_account', 'various_account2', 'various_account3', 'various_account4']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecclassification.change_triplecclassification'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        
        context['various_account'] = Triplecvariousaccount.objects.all().filter(type='coa')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'various_account', 'various_account2', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/triplecclassification')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Triplecclassification
    template_name = 'triplecclassification/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecclassification.delete_triplecclassification'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/triplecclassification')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Triplecclassification.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Triple C Classification List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('triplecclassification/list.html', context)