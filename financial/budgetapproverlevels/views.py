import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from . models import Budgetapproverlevels

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Budgetapproverlevels
    template_name = 'budgetapproverlevels/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Budgetapproverlevels.objects.all().filter(isdeleted=0).order_by('-expwithinbudget')


# @method_decorator(login_required, name='dispatch')
# class DetailView(DetailView):
#     model = Currency
#     template_name = 'currency/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Budgetapproverlevels
    template_name = 'budgetapproverlevels/create.html'
    fields = ['name', 'description', 'expwithinbudget']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('budgetapproverlevels.add_budgetapproverlevels'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/budgetapproverlevels')


# @method_decorator(login_required, name='dispatch')
# class UpdateView(UpdateView):
#     model = Currency
#     template_name = 'currency/edit.html'
#     fields = ['code', 'symbol', 'description', 'country', 'fxrate']

#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.has_perm('currency.change_currency'):
#             raise Http404
#         return super(UpdateView, self).dispatch(request, *args, **kwargs)

#     def form_valid(self, form):
#         self.object = form.save(commit=False)
#         self.object.modifyby = self.request.user
#         self.object.modifydate = datetime.datetime.now()
#         self.object.save(update_fields=['symbol', 'description', 'country', 'fxrate', 'modifyby', 'modifydate'])
#         return HttpResponseRedirect('/currency')


# @method_decorator(login_required, name='dispatch')
# class DeleteView(DeleteView):
#     model = Currency
#     template_name = 'currency/delete.html'

#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.has_perm('currency.delete_currency'):
#             raise Http404
#         return super(DeleteView, self).dispatch(request, *args, **kwargs)

#     def delete(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         self.object.modifyby = self.request.user
#         self.object.modifydate = datetime.datetime.now()
#         self.object.isdeleted = 1
#         self.object.status = 'I'
#         self.object.save()
#         return HttpResponseRedirect('/currency')
