import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from mainunit.models import Mainunit
from . models import Unit
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Unit
    template_name = 'unit/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Unit.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Unit
    template_name = 'unit/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Unit
    template_name = 'unit/create.html'
    fields = ['code', 'description', 'mainunit']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('unit.add_unit'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/unit')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['mainunit'] = Mainunit.objects.filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Unit
    template_name = 'unit/edit.html'
    fields = ['code', 'description', 'mainunit']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('unit.change_unit'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/unit')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['mainunit'] = Mainunit.objects.filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Unit
    template_name = 'unit/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('unit.delete_unit'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/unit')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Unit.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Unit Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('unit/list.html', context)
