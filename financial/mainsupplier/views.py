from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Mainsupplier
import datetime


# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Mainsupplier
    template_name = 'mainsupplier/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Mainsupplier.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Mainsupplier
    template_name = 'mainsupplier/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Mainsupplier
    template_name = 'mainsupplier/create.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mainsupplier.add_mainsupplier'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/mainsupplier')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Mainsupplier
    template_name = 'mainsupplier/edit.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mainsupplier.change_mainsupplier'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/mainsupplier')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Mainsupplier
    template_name = 'mainsupplier/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mainsupplier.delete_mainsupplier'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/mainsupplier')
