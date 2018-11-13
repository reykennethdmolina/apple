import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from chartofaccount.models import Chartofaccount
from . models import Outputvat
from outputvattype.models import Outputvattype
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Outputvat
    template_name = 'outputvat/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Outputvat.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Outputvat
    template_name = 'outputvat/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Outputvat
    template_name = 'outputvat/create.html'
    fields = ['code', 'description', 'chartofaccount', 'title', 'outputvattype']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('outputvat.add_outputvat'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/outputvat')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Outputvat
    template_name = 'outputvat/edit.html'
    fields = ['code', 'description', 'chartofaccount', 'title', 'outputvattype']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('outputvat.change_outputvat'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        elif self.object.chartofaccount:
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.object.chartofaccount.id, isdeleted=0)
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'chartofaccount', 'title',
                                        'modifyby', 'modifydate', 'outputvattype'])
        return HttpResponseRedirect('/outputvat')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Outputvat
    template_name = 'outputvat/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('outputvat.delete_outputvat'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/outputvat')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Outputvat.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Output VAT Masterfile List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('outputvat/list.html', context)
