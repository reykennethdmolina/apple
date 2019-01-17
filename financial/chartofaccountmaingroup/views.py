import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import ChartofAccountMainGroup
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = ChartofAccountMainGroup
    template_name = 'chartofaccountmaingroup/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return ChartofAccountMainGroup.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = ChartofAccountMainGroup
    template_name = 'chartofaccountmaingroup/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = ChartofAccountMainGroup
    template_name = 'chartofaccountmaingroup/create.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('chartofaccountmaingroup.add_chartofaccountmaingroup'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/chartofaccountmaingroup')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = ChartofAccountMainGroup
    template_name = 'chartofaccountmaingroup/edit.html'
    fields = ['code', 'description', 'group']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('chartofaccountmaingroup.change_chartofaccountmaingroup'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        # self.object.save(update_fields=self._meta.get_fields())
        # print Cvtype._meta.get_fields()
        self.object.save(update_fields=['description', 'modifyby', 'modifydate', 'group'])
        return HttpResponseRedirect('/chartofaccountmaingroup')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['group'] = ChartofAccountMainGroup.objects.filter(isdeleted=0).order_by('code')
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = ChartofAccountMainGroup
    template_name = 'chartofaccountmaingroup/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('chartofaccountmaingroup.delete_chartofaccountmaingroup'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/chartofaccountmaingroup')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = ChartofAccountMainGroup.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Chart of Account Main Group Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('chartofaccountmaingroup/list.html', context)