import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Agent
from agenttype.models import Agenttype
from supplier.models import Supplier
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Agent
    template_name = 'agent/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Agent.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Agent
    template_name = 'agent/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Agent
    template_name = 'agent/create.html'
    fields = ['code', 'agenttype', 'name', 'street', 'remarks', 'comments']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('agent.add_agent'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['agenttype'] = Agenttype.objects.filter(isdeleted=0).order_by('code')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/agent')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Agent
    template_name = 'agent/edit.html'
    fields = ['code', 'agenttype', 'name', 'street', 'supplier', 'remarks', 'comments']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('agent.change_agent'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['agenttype'] = Agenttype.objects.filter(isdeleted=0).order_by('code')

        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('name')

        if self.request.POST.get('supplier', False):
            context['supplier'] = Supplier.objects.get(pk=self.request.POST['supplier'], isdeleted=0)
        elif self.object.supplier:
            context['supplier'] = Supplier.objects.get(pk=self.object.supplier.id, isdeleted=0)

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['agenttype', 'name', 'street', 'remarks', 'comments', 'modifyby', 'modifydate', 'supplier'])
        return HttpResponseRedirect('/agent')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Agent
    template_name = 'agent/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('agent.delete_agent'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/agent')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Agent.objects.filter(isdeleted=0).order_by('code')
        # list = Agent.objects.filter(isdeleted=0, code__lte='B').order_by('code')
        context = {
            "title": "Agent Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('agent/list.html', context)
