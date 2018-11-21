import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from unitofmeasure.models import Unitofmeasure
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Unitofmeasure
    template_name = 'unitofmeasure/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Unitofmeasure.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Unitofmeasure
    template_name = 'unitofmeasure/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Unitofmeasure
    template_name = 'unitofmeasure/create.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('unitofmeasure.add_unitofmeasure'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/unitofmeasure')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Unitofmeasure
    template_name = 'unitofmeasure/edit.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('unitofmeasure.change_unitofmeasure'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/unitofmeasure')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Unitofmeasure
    template_name = 'unitofmeasure/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('unitofmeasure.delete_unitofmeasure'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/unitofmeasure')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Unitofmeasure.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Unit of Measure Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('unitofmeasure/list.html', context)
