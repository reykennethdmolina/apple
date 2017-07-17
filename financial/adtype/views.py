''' Adtype Maintenance '''
import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from adtype.models import Adtype
from chartofaccount.models import Chartofaccount


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Adtype
    template_name = 'adtype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Adtype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Adtype
    template_name = 'adtype/detail.html'

@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Adtype
    template_name = 'adtype/create.html'
    fields = ['code', 'description', 'chartofaccount_arcode', 'chartofaccount_revcode']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('adtype.add_adtype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        if self.request.POST.get('chartofaccount_arcode', False):
            context['chartofaccount_arcode'] = Chartofaccount.objects.\
                get(pk=self.request.POST['chartofaccount_arcode'], isdeleted=0, main=1)
        if self.request.POST.get('chartofaccount_revcode', False):
            context['chartofaccount_revcode'] = Chartofaccount.objects.\
                get(pk=self.request.POST['chartofaccount_revcode'], isdeleted=0, main__in=[2, 4])
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/adtype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Adtype
    template_name = 'adtype/edit.html'
    fields = ['code', 'description', 'chartofaccount_arcode', 'chartofaccount_revcode']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('adtype.change_adtype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        if self.request.POST.get('chartofaccount_arcode', False):
            context['chartofaccount_arcode'] = Chartofaccount.objects.\
                get(pk=self.request.POST['chartofaccount_arcode'], isdeleted=0, main=1)
        elif self.object.chartofaccount_arcode:
            context['chartofaccount_arcode'] = Chartofaccount.objects.get(pk=self.object.chartofaccount_arcode.id, isdeleted=0, main=1)
        if self.request.POST.get('chartofaccount_revcode', False):
            context['chartofaccount_revcode'] = Chartofaccount.objects.\
                get(pk=self.request.POST['chartofaccount_revcode'], isdeleted=0, main__in=[2, 4])
        elif self.object.chartofaccount_revcode:
            context['chartofaccount_revcode'] = Chartofaccount.objects.get(pk=self.object.chartofaccount_revcode.id, isdeleted=0, main__in=[2, 4])
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'chartofaccount_arcode',
                                        'chartofaccount_revcode', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/adtype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Adtype
    template_name = 'adtype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('adtype.delete_adtype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/adtype')
