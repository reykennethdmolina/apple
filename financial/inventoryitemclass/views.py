import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from inventoryitemclass.models import Inventoryitemclass
from chartofaccount.models import Chartofaccount
from inventoryitemtype.models import Inventoryitemtype
from annoying.functions import get_object_or_None
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Inventoryitemclass
    template_name = 'inventoryitemclass/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Inventoryitemclass.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Inventoryitemclass
    template_name = 'inventoryitemclass/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Inventoryitemclass
    template_name = 'inventoryitemclass/create.html'
    fields = ['code', 'description', 'inventoryitemtype', 'chartofaccountinventory',
              'chartexpcostofsale', 'chartexpgenandadmin', 'chartexpsellexp', 'depreciationchartofaccount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitemclass.add_inventoryitemclass'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/inventoryitemclass')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['inventoryitemtype'] = Inventoryitemtype.objects.\
            filter(isdeleted=0).order_by('description')
        if self.request.POST.get('chartofaccountinventory', False):
            context['chartofaccountinventory'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccountinventory'], isdeleted=0)
        if self.request.POST.get('chartexpcostofsale', False):
            context['chartexpcostofsale'] = Chartofaccount.objects.get(pk=self.request.POST['chartexpcostofsale'], isdeleted=0)
        if self.request.POST.get('chartexpgenandadmin', False):
            context['chartexpgenandadmin'] = Chartofaccount.objects.get(pk=self.request.POST['chartexpgenandadmin'], isdeleted=0)
        if self.request.POST.get('chartexpsellexp', False):
            context['chartexpsellexp'] = Chartofaccount.objects.get(pk=self.request.POST['chartexpsellexp'], isdeleted=0)
        if self.request.POST.get('depreciationchartofaccount', False):
            context['depreciationchartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['depreciationchartofaccount'], isdeleted=0)
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Inventoryitemclass
    template_name = 'inventoryitemclass/edit.html'
    fields = ['code', 'description', 'inventoryitemtype', 'chartofaccountinventory',
              'chartexpcostofsale', 'chartexpgenandadmin', 'chartexpsellexp', 'depreciationchartofaccount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitemclass.change_inventoryitemclass'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['inventoryitemtype'] = Inventoryitemtype.objects.\
            filter(isdeleted=0).order_by('description')
        if self.request.POST.get('chartofaccountinventory', False):
            context['chartofaccountinventory'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccountinventory'], isdeleted=0)
        elif self.object.chartofaccountinventory:
            context['chartofaccountinventory'] = get_object_or_None(Chartofaccount, pk=self.object.chartofaccountinventory.id)
        if self.request.POST.get('chartexpcostofsale', False):
            context['chartexpcostofsale'] = Chartofaccount.objects.get(pk=self.request.POST['chartexpcostofsale'], isdeleted=0)
        elif self.object.chartexpcostofsale:
            context['chartexpcostofsale'] = get_object_or_None(Chartofaccount, pk=self.object.chartexpcostofsale.id)
        if self.request.POST.get('chartexpgenandadmin', False):
            context['chartexpgenandadmin'] = Chartofaccount.objects.get(pk=self.request.POST['chartexpgenandadmin'], isdeleted=0)
        elif self.object.chartexpgenandadmin:
            context['chartexpgenandadmin'] = get_object_or_None(Chartofaccount, pk=self.object.chartexpgenandadmin.id)
        if self.request.POST.get('chartexpsellexp', False):
            context['chartexpsellexp'] = Chartofaccount.objects.get(pk=self.request.POST['chartexpsellexp'], isdeleted=0)
        elif self.object.chartexpsellexp:
            context['chartexpsellexp'] = get_object_or_None(Chartofaccount, pk=self.object.chartexpsellexp.id)
        if self.request.POST.get('depreciationchartofaccount', False):
            context['depreciationchartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['depreciationchartofaccount'], isdeleted=0)
        elif self.object.depreciationchartofaccount:
            context['depreciationchartofaccount'] = get_object_or_None(Chartofaccount, pk=self.object.depreciationchartofaccount.id)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'inventoryitemtype',
                                        'chartofaccountinventory', 'chartexpcostofsale',
                                        'chartexpgenandadmin', 'chartexpsellexp', 'depreciationchartofaccount',
                                        'modifyby', 'modifydate'])
        return HttpResponseRedirect('/inventoryitemclass')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Inventoryitemclass
    template_name = 'inventoryitemclass/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitemclass.delete_inventoryitemclass'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/inventoryitemclass')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Inventoryitemclass.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Inventory Item Class Masterfile List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('inventoryitemclass/list.html', context)