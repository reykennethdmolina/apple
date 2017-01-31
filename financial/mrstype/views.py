from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from mrstype.models import Mrstype
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Mrstype
    template_name = 'mrstype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Mrstype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Mrstype
    template_name = 'mrstype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Mrstype
    template_name = 'mrstype/create.html'
    fields = ['code', 'description', 'transtype', 'lastno']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mrstype.add_mrstype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/mrstype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Mrstype
    template_name = 'mrstype/edit.html'
    fields = ['code', 'description', 'transtype', 'lastno']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mrstype.change_mrstype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/mrstype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Mrstype
    template_name = 'mrstype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mrstype.delete_mrstype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/mrstype')
