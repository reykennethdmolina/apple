import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from chartofaccount.models import Chartofaccount
from . models import Debitcreditmemosubtype

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Debitcreditmemosubtype
    template_name = 'debitcreditmemosubtype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Debitcreditmemosubtype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Debitcreditmemosubtype
    template_name = 'debitcreditmemosubtype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Debitcreditmemosubtype
    template_name = 'debitcreditmemosubtype/create.html'
    fields = ['code', 'description', 'group', 'applicationstatus',
              'particular', 'credit1chartofaccount',
              'credit2chartofaccount', 'debit1chartofaccount', 'debit2chartofaccount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('debitcreditmemosubtype.add_debitcreditmemosubtype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/debitcreditmemosubtype')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['chartofaccount'] = Chartofaccount.objects.\
            filter(isdeleted=0).order_by('accountcode')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Debitcreditmemosubtype
    template_name = 'debitcreditmemosubtype/edit.html'
    fields = ['code', 'description', 'group', 'applicationstatus',
              'particular', 'credit1chartofaccount',
              'credit2chartofaccount', 'debit1chartofaccount', 'debit2chartofaccount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('debitcreditmemosubtype.change_debitcreditmemosubtype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save(update_fields=['description', 'group', 'applicationstatus',
                                        'particular', 'credit1chartofaccount', 
                                        'credit2chartofaccount', 'debit1chartofaccount',
                                        'debit2chartofaccount', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/debitcreditmemosubtype')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['chartofaccount'] = Chartofaccount.objects.\
            filter(isdeleted=0).order_by('accountcode')
        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Debitcreditmemosubtype
    template_name = 'debitcreditmemosubtype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('debitcreditmemosubtype.delete_debitcreditmemosubtype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/debitcreditmemosubtype')
