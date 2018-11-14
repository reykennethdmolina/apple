import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from productgroupcategory.models import Productgroupcategory
from productgroup.models import Productgroup
from locationcategory.models import Locationcategory
from chartofaccount.models import Chartofaccount
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Productgroupcategory
    template_name = 'productgroupcategory/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Productgroupcategory.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Productgroupcategory
    template_name = 'productgroupcategory/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Productgroupcategory
    template_name = 'productgroupcategory/create.html'
    fields = ['productgroup', 'category', 'chartofaccount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('productgroupcategory.add_productgroupcategory'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['productgroup'] = Productgroup.objects.filter(isdeleted=0).order_by('description')
        context['locationcategory'] = Locationcategory.objects.filter(isdeleted=0).order_by('description')
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.\
                get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/productgroupcategory')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Productgroupcategory
    template_name = 'productgroupcategory/edit.html'
    fields = ['productgroup', 'category', 'chartofaccount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('productgroupcategory.change_productgroupcategory'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['productgroup'] = Productgroup.objects.filter(isdeleted=0).order_by('description')
        context['locationcategory'] = Locationcategory.objects.filter(isdeleted=0).order_by('description')
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.\
                get(pk=self.request.POST['chartofaccount'], isdeleted=0, main=1)
        elif self.object.chartofaccount:
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.object.chartofaccount.id, isdeleted=0, main=1)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['productgroup', 'category', 'chartofaccount', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/productgroupcategory')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Productgroupcategory
    template_name = 'productgroupcategory/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('productgroupcategory.delete_productgroupcategory'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/productgroupcategory')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Productgroupcategory.objects.filter(isdeleted=0).order_by('pk')
        context = {
            "title": "Product Group Category Masterfile List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('productgroupcategory/list.html', context)
