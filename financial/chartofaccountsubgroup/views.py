import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import ChartofAccountSubGroup
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = ChartofAccountSubGroup
    template_name = 'chartofaccountsubgroup/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return ChartofAccountSubGroup.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = ChartofAccountSubGroup
    template_name = 'chartofaccountsubgroup/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = ChartofAccountSubGroup
    template_name = 'chartofaccountsubgroup/create.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('chartofaccountsubgroup.add_chartofaccountsubgroup'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/chartofaccountsubgroup')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = ChartofAccountSubGroup
    template_name = 'chartofaccountsubgroup/edit.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('chartofaccountsubgroup.change_chartofaccountsubgroup'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        # self.object.save(update_fields=self._meta.get_fields())
        # print Cvtype._meta.get_fields()
        self.object.save(update_fields=['description', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/chartofaccountsubgroup')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = ChartofAccountSubGroup
    template_name = 'chartofaccountsubgroup/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('chartofaccountsubgroup.delete_chartofaccountsubgroup'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/chartofaccountsubgroup')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = ChartofAccountSubGroup.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Chart of Account Sub Group Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('chartofaccountsubgroup/list.html', context)