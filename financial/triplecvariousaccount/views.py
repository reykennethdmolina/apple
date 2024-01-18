import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404

from chartofaccount.models import Chartofaccount
from . models import Triplecvariousaccount
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter
from triplecsubtype.models import Triplecsubtype

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Triplecvariousaccount
    template_name = 'triplecvariousaccount/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Triplecvariousaccount.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Triplecvariousaccount
    template_name = 'triplecvariousaccount/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Triplecvariousaccount
    template_name = 'triplecvariousaccount/create.html'
    fields = ['code', 'description', 'amount', 'chartexpcostofsale', 'chartexpgenandadmin', 'chartexpsellexp', 'type', 'subtype']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecvariousaccount.add_triplecvariousaccount'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        
        context['chartexpcostofsale'] = Chartofaccount.objects.all().filter(accounttype='P')
        context['chartexpgenandadmin'] = Chartofaccount.objects.all().filter(accounttype='P')
        context['chartexpsellexp'] = Chartofaccount.objects.all().filter(accounttype='P')
        context['subtype'] = Triplecsubtype.objects.all().filter(isdeleted=0).order_by('code')

        return context
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/triplecvariousaccount')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Triplecvariousaccount
    template_name = 'triplecvariousaccount/edit.html'
    fields = ['code', 'description', 'amount', 'chartexpcostofsale', 'chartexpgenandadmin', 'chartexpsellexp', 'type', 'subtype']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecvariousaccount.change_triplecvariousaccount'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        
        context['chartexpcostofsale'] = Chartofaccount.objects.all().filter(accounttype='P')
        context['chartexpgenandadmin'] = Chartofaccount.objects.all().filter(accounttype='P')
        context['chartexpsellexp'] = Chartofaccount.objects.all().filter(accounttype='P')
        context['subtype'] = Triplecsubtype.objects.all().filter(isdeleted=0).order_by('code')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'amount', 'chartexpcostofsale', 'chartexpgenandadmin', 'chartexpsellexp', 'type', 'subtype', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/triplecvariousaccount')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Triplecvariousaccount
    template_name = 'triplecvariousaccount/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecvariousaccount.delete_triplecvariousaccount'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/triplecvariousaccount')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Triplecvariousaccount.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Triple C Various Account List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('triplecvariousaccount/list.html', context)
    