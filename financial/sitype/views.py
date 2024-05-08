import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from sitype.models import Sitype
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter
from outputvattype.models import Outputvattype

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Sitype
    template_name = 'sitype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Sitype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Sitype
    template_name = 'sitype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Sitype
    template_name = 'sitype/create.html'
    fields = ['code', 'description', 'outputvattype']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('sitype.add_sitype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/sitype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Sitype
    template_name = 'sitype/edit.html'
    fields = ['code', 'description', 'outputvattype']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('sitype.change_sitype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['outputvattype'] = Outputvattype.objects.filter(isdeleted=0).order_by('pk')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'outputvattype', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/sitype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Sitype
    template_name = 'sitype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('sitype.delete_sitype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/sitype')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Sitype.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "SI Type Masterfile List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('sitype/list.html', context)
