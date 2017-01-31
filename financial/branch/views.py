from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from branch.models import Branch
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Branch
    template_name = 'branch/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Branch.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Branch
    template_name = 'branch/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Branch
    template_name = 'branch/create.html'
    fields = ['code', 'description', 'lastsino', 'lastorno']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('branch.add_branch'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/branch')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Branch
    template_name = 'branch/edit.html'
    fields = ['code', 'description', 'lastsino', 'lastorno']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('branch.change_branch'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/branch')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Branch
    template_name = 'branch/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('branch.delete_branch'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/branch')
