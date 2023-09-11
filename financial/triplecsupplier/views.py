import datetime
from typing import Any, Dict
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from django import forms
from triplecclassification.models import Triplecclassification
from triplecvariousaccount.models import Triplecvariousaccount
from . models import Triplecsupplier
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter
from supplier.models import Supplier
from triplecbureau.models import Triplecbureau
from triplecsection.models import Triplecsection
from department.models import Department
from triplecrate.models import Triplecrate
from bankaccount.models import Bankaccount
from endless_pagination.views import AjaxListView
from django.db.models import Q

# Create your views here.
@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Triplecsupplier
    template_name = 'triplecsupplier/index.html'
    context_object_name = 'data_list'
    page_template = 'triplecsupplier/index_list.html'

    def get_queryset(self):
        query = Triplecsupplier.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(supplier__name__icontains=keysearch) | Q(supplier__code__icontains=keysearch))
        return query
       
    def get_context_data(self, **kwargs):
        context = super(AjaxListView, self).get_context_data(**kwargs)
        context['authors'] = Supplier.objects.all().filter(isdeleted=0, triplec=1).order_by('code')

        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Triplecsupplier
    template_name = 'triplecsupplier/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Triplecsupplier
    template_name = 'triplecsupplier/create.html'
    fields = ['supplier', 'bureau', 'section', 'department', 'rate']

    # def __init__(self, *args, **kwargs):
    #     super(CreateView, self).__init__(*args, **kwargs)
    #     self.fields[2, 3, 4, 5].required = False

    def dispatch(self, request, *args, **kwargs):

        if not request.user.has_perm('triplecsupplier.add_triplecsupplier'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['authors'] = Supplier.objects.all().filter(isdeleted=0, triplec=1)
        context['bureaus'] = Triplecbureau.objects.all().filter(isdeleted=0)
        context['sections'] = Triplecsection.objects.all().filter(isdeleted=0).order_by('code')
        context['departments'] = Department.objects.all().filter(isdeleted=0, \
                                expchartofaccount__main__contains=5, expchartofaccount__clas__contains=1).order_by('code')
        context['rates'] = Triplecrate.objects.all().filter(isdeleted=0)
        # context['bankaccounts'] = Bankaccount.objects.all().filter(isdeleted=0)

        return context
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/triplecsupplier')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Triplecsupplier
    template_name = 'triplecsupplier/edit.html'
    fields = ['bureau', 'section', 'department', 'rate', 'various_account']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecsupplier.change_triplecsupplier'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['author'] = Supplier.objects.get(pk=self.object.supplier_id).name
        context['code'] = Supplier.objects.get(pk=self.object.supplier_id).code
        ccc = Supplier.objects.get(pk=self.object.supplier_id).ccc
        context['classification'] = Triplecclassification.objects.get(code=ccc).description
        context['bureaus'] = Triplecbureau.objects.all().filter(isdeleted=0)
        context['sections'] = Triplecsection.objects.all().filter(isdeleted=0).order_by('code')
        context['departments'] = Department.objects.all().filter(isdeleted=0, expchartofaccount__main__contains=5).order_by('code')
        context['rates'] = Triplecrate.objects.all().filter(isdeleted=0).order_by('code')
        context['various_account'] = Triplecvariousaccount.objects.all().filter(isdeleted=0, type='coa').order_by('code')
        # context['bankaccounts'] = Bankaccount.objects.all().filter(isdeleted=0)

        return context
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['bureau', 'section', 'department', 'rate', 'various_account', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/triplecsupplier')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Triplecsupplier
    template_name = 'triplecsupplier/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplecsupplier.delete_triplecsupplier'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/triplecsupplier')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Triplecsupplier.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Triple C Parameter Supplier",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('triplecsupplier/list.html', context)
    