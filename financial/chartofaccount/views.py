from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from chartofaccount.models import Chartofaccount
from product.models import Product
from typeofexpense.models import Typeofexpense
from kindofexpense.models import Kindofexpense
from mainunit.models import Mainunit
import datetime

#pagination
from django.core import serializers
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404, HttpResponse


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Chartofaccount
    template_name = 'chartofaccount/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Chartofaccount.objects.all().filter(isdeleted=0).order_by('-pk')[0:10]

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['listcount'] = Chartofaccount.objects.filter(isdeleted=0).count()
        return context


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Chartofaccount
    template_name = 'chartofaccount/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Chartofaccount
    template_name = 'chartofaccount/create.html'
    fields = ['main', 'clas', 'item',
              'cont', 'sub', 'accountcode', 'title',
              'description', 'balancecode', 'charttype',
              'accounttype', 'ctax', 'taxstatus',
              'wtaxstatus', 'mainposting', 'fixedasset',
              'taxespayable', 'kindofexpense', 'product',
              'typeofexpense', 'mainunit', 'bankaccount_enable',
              'department_enable', 'employee_enable', 'supplier_enable',
              'customer_enable', 'branch_enable', 'product_enable',
              'unit_enable', 'inputvat_enable', 'outputvat_enable',
              'vat_enable', 'wtax_enable', 'ataxcode_enable']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('chartofaccount.add_chartofaccount'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['product'] = Product.objects.filter(isdeleted=0).order_by('description')
        context['typeofexpense'] = Typeofexpense.objects.filter(isdeleted=0).order_by('description')
        context['kindofexpense'] = Kindofexpense.objects.filter(isdeleted=0).order_by('description')
        context['mainunit'] = Mainunit.objects.filter(isdeleted=0).order_by('description')
        return context

    def post(self, request, **kwargs):
        request.POST = request.POST.copy()

        # manual validation of sub
        try:
            request.POST['sub'] = str(request.POST['sub'])

            # mask sub with leading zeros
            zero_addon = 6 - len(str(request.POST['sub']))
            for x in range(0, zero_addon):
                request.POST['sub'] = '0' + str(request.POST['sub'])

            # generate accountcode
            request.POST['accountcode'] = str(request.POST['main']) \
                                      + str(request.POST['clas']) \
                                      + str(request.POST['item']) \
                                      + str(request.POST['cont']) \
                                      + request.POST['sub']

        except ValueError:
            request.POST['sub'] = ''

        return super(CreateView, self).post(request, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/chartofaccount')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Chartofaccount
    template_name = 'chartofaccount/edit.html'
    fields = ['main', 'clas', 'item',
              'cont', 'sub', 'accountcode', 'title',
              'description', 'balancecode', 'charttype',
              'accounttype', 'ctax', 'taxstatus',
              'wtaxstatus', 'mainposting', 'fixedasset',
              'taxespayable', 'kindofexpense', 'product',
              'typeofexpense', 'mainunit', 'bankaccount_enable',
              'department_enable', 'employee_enable', 'supplier_enable',
              'customer_enable', 'branch_enable', 'product_enable',
              'unit_enable', 'inputvat_enable', 'outputvat_enable',
              'vat_enable', 'wtax_enable', 'ataxcode_enable']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('chartofaccount.change_chartofaccount'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['product'] = Product.objects.filter(isdeleted=0).order_by('description')
        context['typeofexpense'] = Typeofexpense.objects.filter(isdeleted=0).order_by('description')
        context['kindofexpense'] = Kindofexpense.objects.filter(isdeleted=0).order_by('description')
        context['mainunit'] = Mainunit.objects.filter(isdeleted=0).order_by('description')
        return context

    def post(self, request, **kwargs):
        request.POST = request.POST.copy()

        # manual validation of sub
        try:
            request.POST['sub'] = str(request.POST['sub'])

            # mask sub with leading zeros
            zero_addon = 6 - len(str(request.POST['sub']))
            for x in range(0, zero_addon):
                request.POST['sub'] = '0' + str(request.POST['sub'])

            # generate accountcode
            request.POST['accountcode'] = str(request.POST['main']) \
                                      + str(request.POST['clas']) \
                                      + str(request.POST['item']) \
                                      + str(request.POST['cont']) \
                                      + request.POST['sub']

        except ValueError:
            request.POST['sub'] = ''

        return super(UpdateView, self).post(request, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['title', 'description', 'balancecode', 'charttype', 'accounttype', 'ctax',
                                        'taxstatus', 'wtaxstatus', 'mainposting', 'fixedasset', 'taxespayable',
                                        'kindofexpense', 'product', 'typeofexpense', 'mainunit', 'bankaccount_enable',
                                        'department_enable', 'employee_enable', 'supplier_enable', 'customer_enable',
                                        'branch_enable', 'product_enable', 'unit_enable', 'inputvat_enable',
                                        'outputvat_enable', 'vat_enable', 'wtax_enable', 'ataxcode_enable', 'modifyby',
                                        'modifydate'])
        return HttpResponseRedirect('/chartofaccount')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Chartofaccount
    template_name = 'chartofaccount/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('chartofaccount.delete_chartofaccount'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/chartofaccount')


def paginate(request, command, current, limit, search):
    current = int(current)
    limit = int(limit)

    if command == "search" and search != "null":
        search_not_slug = search.replace('-', ' ')
        chartofaccount = Chartofaccount.objects.all().filter(Q(id__icontains=search) |
                                                             Q(accountcode__icontains=search) |
                                                             Q(description__icontains=search) |
                                                             Q(title__icontains=search) |
                                                             Q(accountcode__icontains=search_not_slug) |
                                                             Q(description__icontains=search_not_slug) |
                                                             Q(title__icontains=search_not_slug))\
                                                            .filter(isdeleted=0).order_by('-pk')
    else:
        chartofaccount = Chartofaccount.objects.all().filter(isdeleted=0).order_by('-pk')[current:current+limit]

    json_models = serializers.serialize("json", chartofaccount)
    print json_models
    return HttpResponse(json_models, content_type="application/javascript")
