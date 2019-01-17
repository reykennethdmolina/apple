import datetime
from django.views.generic import View, ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from chartofaccount.models import Chartofaccount
from . models import Wtax
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Wtax
    template_name = 'wtax/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Wtax.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Wtax
    template_name = 'wtax/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Wtax
    template_name = 'wtax/create.html'
    fields = ['code', 'description', 'rate', 'wtaxtype_id', 'chartofaccount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('wtax.add_wtax'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/wtax')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Wtax
    template_name = 'wtax/edit.html'
    fields = ['code', 'description', 'rate', 'wtaxtype_id', 'chartofaccount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('wtax.change_wtax'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/wtax')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        elif self.object.chartofaccount:
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.object.chartofaccount.id, isdeleted=0)
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Wtax
    template_name = 'wtax/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('wtax.delete_wtax'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/wtax')
    
@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Wtax.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "WTAX Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('wtax/list.html', context)
