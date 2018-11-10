import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from artype.models import Artype
from chartofaccount.models import Chartofaccount
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Artype
    template_name = 'artype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Artype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Artype
    template_name = 'artype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Artype
    template_name = 'artype/create.html'
    fields = ['code', 'description', 'creditchartofaccount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('artype.add_artype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/artype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Artype
    template_name = 'artype/edit.html'
    fields = ['code', 'description', 'creditchartofaccount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('artype.change_artype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)

        if self.request.POST.get('creditchartofaccount', False):
            context['creditchartofaccount'] = Chartofaccount.objects.all().filter(accounttype='P')
        elif self.object.creditchartofaccount:
            context['creditchartofaccount'] = Chartofaccount.objects.get(pk=self.object.creditchartofaccount.id,
                                                                         isdeleted=0)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'modifyby', 'modifydate', 'creditchartofaccount'])
        return HttpResponseRedirect('/artype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Artype
    template_name = 'artype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('artype.delete_artype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/artype')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Artype.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "AR Type Masterfile List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('artype/list.html', context)