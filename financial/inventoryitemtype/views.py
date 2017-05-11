import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from inventoryitemtype.models import Inventoryitemtype

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Inventoryitemtype
    template_name = 'inventoryitemtype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Inventoryitemtype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Inventoryitemtype
    template_name = 'inventoryitemtype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Inventoryitemtype
    template_name = 'inventoryitemtype/create.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitemtype.add_inventoryitemtype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/inventoryitemtype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Inventoryitemtype
    template_name = 'inventoryitemtype/edit.html'
    fields = ['code', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitemtype.change_inventoryitemtype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/inventoryitemtype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Inventoryitemtype
    template_name = 'inventoryitemtype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitemtype.delete_inventoryitemtype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/inventoryitemtype')