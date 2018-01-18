import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from circulationpaytype.models import Circulationpaytype
from locationcategory.models import Locationcategory

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Circulationpaytype
    template_name = 'circulationpaytype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Circulationpaytype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Circulationpaytype
    template_name = 'circulationpaytype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Circulationpaytype
    template_name = 'circulationpaytype/create.html'
    fields = ['code', 'description', 'ss_groupname', 'category']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('circulationpaytype.add_circulationpaytype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['category'] = Locationcategory.objects.filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/circulationpaytype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Circulationpaytype
    template_name = 'circulationpaytype/edit.html'
    fields = ['code', 'description', 'ss_groupname', 'category']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('circulationpaytype.change_circulationpaytype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['category'] = Locationcategory.objects.filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['category', 'ss_groupname','description', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/circulationpaytype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Circulationpaytype
    template_name = 'circulationpaytype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('circulationpaytype.delete_circulationpaytype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/circulationpaytype')