import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from locationcategory.models import Locationcategory


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Locationcategory
    template_name = 'locationcategory/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Locationcategory.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Locationcategory
    template_name = 'locationcategory/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Locationcategory
    template_name = 'locationcategory/create.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('locationcategory.add_locationcategory'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/locationcategory')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Locationcategory
    template_name = 'locationcategory/edit.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('locationcategory.change_locationcategory'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/locationcategory')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Locationcategory
    template_name = 'locationcategory/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('locationcategory.delete_locationcategory'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/locationcategory')
