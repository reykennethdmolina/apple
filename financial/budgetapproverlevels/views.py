import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Budgetapproverlevels
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Budgetapproverlevels
    template_name = 'budgetapproverlevels/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Budgetapproverlevels.objects.all().filter(isdeleted=0).order_by('-level')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Budgetapproverlevels
    template_name = 'budgetapproverlevels/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Budgetapproverlevels
    template_name = 'budgetapproverlevels/create.html'
    fields = ['level', 'name', 'description', 'expwithinbudget']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('budgetapproverlevels.add_budgetapproverlevels'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/budgetapproverlevels')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Budgetapproverlevels
    template_name = 'budgetapproverlevels/edit.html'
    fields = ['level', 'name', 'description', 'expwithinbudget']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('budgetapproverlevels.change_budgetapproverlevels'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['level', 'name', 'description', 'expwithinbudget', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/budgetapproverlevels')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Budgetapproverlevels
    template_name = 'budgetapproverlevels/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('budgetapproverlevels.delete_budgetapproverlevels'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/budgetapproverlevels')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Budgetapproverlevels.objects.filter(isdeleted=0).order_by('level')
        context = {
            "title": "Budget Approver Levels Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('budgetapproverlevels/list.html', context)