import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404

from triplecvariousaccount.models import Triplecvariousaccount
from . models import Triplecsubtype
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Triplecsubtype
    template_name = 'triplecsubtype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Triplecsubtype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Triplecsubtype
    template_name = 'triplecsubtype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Triplecsubtype
    template_name = 'triplecsubtype/create.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecsubtype.add_triplecsubtype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/triplectype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Triplecsubtype
    template_name = 'triplecsubtype/edit.html'
    fields = ['code', 'description', 'various_account']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecsubtype.change_triplecsubtype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['various_account'] = Triplecvariousaccount.objects.all().filter(isdeleted=0, type='coa').order_by('code')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'various_account', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/triplectype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Triplecsubtype
    template_name = 'triplecsubtype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecsubtype.delete_triplecsubtype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/triplectype')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Triplecsubtype.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Triple C Type List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('triplecsubtype/list.html', context)