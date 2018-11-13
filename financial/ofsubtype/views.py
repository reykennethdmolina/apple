import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from ofsubtype.models import Ofsubtype
from oftype.models import Oftype
from chartofaccount.models import Chartofaccount
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Ofsubtype
    template_name = 'ofsubtype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Ofsubtype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Ofsubtype
    template_name = 'ofsubtype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Ofsubtype
    template_name = 'ofsubtype/create.html'
    fields = ['code', 'description', 'oftype', 'chartexpcostofsale', 'chartexpgenandadmin', 'chartexpsellexp']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('ofsubtype.add_ofsubtype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['oftype'] = Oftype.objects.all().filter(isdeleted=0)

        # context['chartexpcostofsale'] = Chartofaccount.objects.all().filter(main=5, clas=1).filter(accounttype='P')
        # context['chartexpgenandadmin'] = Chartofaccount.objects.all().filter(main=5, clas=2).filter(accounttype='P')
        # context['chartexpsellexp'] = Chartofaccount.objects.all().filter(main=5, clas=3).filter(accounttype='P')

        context['chartexpcostofsale'] = Chartofaccount.objects.all().filter(accounttype='P')
        context['chartexpgenandadmin'] = Chartofaccount.objects.all().filter(accounttype='P')
        context['chartexpsellexp'] = Chartofaccount.objects.all().filter(accounttype='P')

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/ofsubtype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Ofsubtype
    template_name = 'ofsubtype/edit.html'
    fields = ['code', 'description', 'oftype', 'chartexpcostofsale', 'chartexpgenandadmin', 'chartexpsellexp']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('ofsubtype.change_ofsubtype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['oftype'] = Oftype.objects.all().filter(isdeleted=0)

        # context['chartexpcostofsale'] = Chartofaccount.objects.all().filter(main=5, clas=1).filter(accounttype='P')
        # context['chartexpgenandadmin'] = Chartofaccount.objects.all().filter(main=5, clas=2).filter(accounttype='P')
        # context['chartexpsellexp'] = Chartofaccount.objects.all().filter(main=5, clas=3).filter(accounttype='P')
        context['chartexpcostofsale'] = Chartofaccount.objects.all().filter(accounttype='P')
        context['chartexpgenandadmin'] = Chartofaccount.objects.all().filter(accounttype='P')
        context['chartexpsellexp'] = Chartofaccount.objects.all().filter(accounttype='P')

        # if self.request.POST.get('debitchartofaccount', False):
        #     context['debitchartofaccount'] = Chartofaccount.objects.all().filter(accounttype='P')
        # elif self.object.debitchartofaccount:
        #     context['debitchartofaccount'] = Chartofaccount.objects.get(pk=self.object.debitchartofaccount.id, isdeleted=0)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'oftype',
                                        'chartexpcostofsale', 'chartexpgenandadmin', 'chartexpsellexp',
                                        'modifyby', 'modifydate'])
        return HttpResponseRedirect('/ofsubtype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Ofsubtype
    template_name = 'ofsubtype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('ofsubtype.delete_ofsubtype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/ofsubtype')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Ofsubtype.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "OF Subtype Masterfile List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('ofsubtype/list.html', context)
