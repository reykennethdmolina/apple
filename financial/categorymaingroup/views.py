import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import CategoryMainGroup
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = CategoryMainGroup
    template_name = 'categorymaingroup/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return CategoryMainGroup.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = CategoryMainGroup
    template_name = 'categorymaingroup/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = CategoryMainGroup
    template_name = 'categorymaingroup/create.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('categorymaingroup.add_categorymaingroup'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/categorymaingroup')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = CategoryMainGroup
    template_name = 'categorymaingroup/edit.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('categorymaingroup.change_categorymaingroup'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        # self.object.save(update_fields=self._meta.get_fields())
        # print Cvtype._meta.get_fields()
        self.object.save(update_fields=['description', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/categorymaingroup')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = CategoryMainGroup
    template_name = 'categorymaingroup/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('categorymaingroup.delete_categorymaingroup'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/categorymaingroup')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = CategoryMainGroup.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Category Main Group Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('categorymaingroup/list.html', context)
