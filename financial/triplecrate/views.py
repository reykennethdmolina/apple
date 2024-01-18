import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Triplecrate
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Triplecrate
    template_name = 'triplecrate/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Triplecrate.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Triplecrate
    template_name = 'triplecrate/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Triplecrate
    template_name = 'triplecrate/create.html'
    fields = ['code', 'description', 'amount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecrate.add_triplecrate'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/triplecrate')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Triplecrate
    template_name = 'triplecrate/edit.html'
    fields = ['code', 'description', 'amount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecrate.change_triplecrate'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        return context
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'amount', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/triplecrate')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Triplecrate
    template_name = 'triplecrate/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecrate.delete_triplecrate'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/triplecrate')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Triplecrate.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Triple C Rate List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('triplecrate/list.html', context)
    