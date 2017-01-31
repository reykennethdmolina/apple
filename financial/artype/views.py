from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from artype.models import Artype
import datetime


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
    fields = ['code', 'description']

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
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('artype.change_artype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
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
