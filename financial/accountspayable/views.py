import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Accountspayable


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Accountspayable
    template_name = 'accountspayable/create.html'
    fields = []

    # def dispatch(self, request, *args, **kwargs):
    #     if not request.user.has_perm('accountspayable.add_accountspayable'):
    #         raise Http404
    #     return super(CreateView, self).dispatch(request, *args, **kwargs)
    #
    # def form_valid(self, form):
    #     self.object = form.save(commit=False)
    #     self.object.enterby = self.request.user
    #     self.object.modifyby = self.request.user
    #     self.object.save()
    #     return HttpResponseRedirect('/accountspayable')