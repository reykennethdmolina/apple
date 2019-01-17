import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from fxrate.models import Fxrate
from currency.models import Currency
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Fxrate
    template_name = 'fxrate/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Fxrate.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Fxrate
    template_name = 'fxrate/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Fxrate
    template_name = 'fxrate/create.html'
    fields = ['currency', 'startdate', 'enddate',
              'fxrate', 'fxrateselling', 'remarks']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('fxrate.add_fxrate'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/fxrate')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Fxrate
    template_name = 'fxrate/edit.html'
    fields = ['currency', 'startdate', 'enddate',
              'fxrate', 'fxrateselling', 'remarks']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('fxrate.change_fxrate'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['currency'] = Currency.objects.filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['currency', 'startdate', 'enddate',
                                        'fxrate', 'fxrateselling', 'remarks',
                                        'modifyby', 'modifydate'])
        return HttpResponseRedirect('/fxrate')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Fxrate
    template_name = 'fxrate/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('fxrate.delete_fxrate'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/fxrate')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Fxrate.objects.filter(isdeleted=0).order_by('currency', 'startdate', 'enddate')
        context = {
            "title": "FX Rate Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('fxrate/list.html', context)