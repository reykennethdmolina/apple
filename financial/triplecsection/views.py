import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Triplecsection
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Triplecsection
    template_name = 'triplecsection/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Triplecsection.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Triplecsection
    template_name = 'triplecsection/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Triplecsection
    template_name = 'triplecsection/create.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecsection.add_triplecsection'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/triplecsection')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Triplecsection
    template_name = 'triplecsection/edit.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecsection.change_triplecsection'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/triplecsection')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Triplecsection
    template_name = 'triplecsection/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecsection.delete_triplecsection'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/triplecsection')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Triplecsection.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Triple C Section List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('triplecsection/list.html', context)