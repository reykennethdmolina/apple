import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from chartofaccount.models import Chartofaccount
from product.models import Product
from typeofexpense.models import Typeofexpense
from kindofexpense.models import Kindofexpense
from mainunit.models import Mainunit
from chartofaccountsubgroup.models import ChartofAccountSubGroup
from django.http import HttpResponseRedirect, Http404
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

# pagination and search
from endless_pagination.views import AjaxListView
from django.db.models import Q


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Chartofaccount
    template_name = 'chartofaccount/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'chartofaccount/index_list.html'
    def get_queryset(self):
        query = Chartofaccount.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(accountcode__icontains=keysearch) |
                                 Q(title__icontains=keysearch) |
                                 Q(description__icontains=keysearch))
        return query


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
              'vat_enable', 'wtax_enable', 'ataxcode_enable',
              'reftype_enable', 'refnum_enable', 'refdate_enable', 'subgroup']

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
        context['subgroup'] = ChartofAccountSubGroup.objects.filter(isdeleted=0).order_by('description')
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
              'vat_enable', 'wtax_enable', 'ataxcode_enable',
              'reftype_enable', 'refnum_enable', 'refdate_enable', 'subgroup']

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
        context['subgroup'] = ChartofAccountSubGroup.objects.filter(isdeleted=0).order_by('description')
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
        self.object.save(update_fields=['title', 'description', 'balancecode', 'charttype',
                                        'accounttype', 'ctax', 'taxstatus', 'wtaxstatus',
                                        'mainposting', 'fixedasset', 'taxespayable',
                                        'kindofexpense', 'product', 'typeofexpense',
                                        'mainunit', 'bankaccount_enable',
                                        'department_enable', 'employee_enable',
                                        'supplier_enable', 'customer_enable',
                                        'branch_enable', 'product_enable', 'unit_enable',
                                        'inputvat_enable', 'outputvat_enable', 'vat_enable',
                                        'wtax_enable', 'ataxcode_enable', 'modifyby', 'modifydate',
                                        'reftype_enable', 'refnum_enable', 'refdate_enable', 'subgroup'])
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

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Chartofaccount.objects.filter(isdeleted=0).order_by('accountcode')
        context = {
            "title": "Chart of Account Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('chartofaccount/list.html', context)
