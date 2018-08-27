import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from product.models import Product
from mainproduct.models import Mainproduct
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

# Create your views here.

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Product
    template_name = 'product/index.html'
    context_object_name = 'data_list'

    #def get_context_data(self, **kwargs):
    #    context = super(IndexView, self).get_context_data(**kwargs)
    #    context['test'] = Permission.objects.all()
    #    return context

    def get_queryset(self):
        return Product.objects.all().filter(isdeleted=0).order_by('-pk')

@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Product
    template_name = 'product/detail.html'

@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Product
    template_name = 'product/create.html'
    fields = ['code', 'description', 'mainproduct', 'cmsgroup_id', 'pagecount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('product.add_product'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/product')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['mainproduct'] = Mainproduct.objects.filter(isdeleted=0).order_by('description')
        context['cmsgroup'] = Product.objects.filter(isdeleted=0).order_by('description')
        return context

@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Product
    template_name = 'product/edit.html'
    fields = ['code', 'description', 'mainproduct', 'cmsgroup_id', 'pagecount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('product.change_product'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'mainproduct', 'cmsgroup_id',
                                        'pagecount', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/product')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['mainproduct'] = Mainproduct.objects.filter(isdeleted=0).order_by('description')
        context['cmsgroup'] = Product.objects.filter(isdeleted=0).order_by('description')
        return context

@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Product
    template_name = 'product/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('product.delete_product'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/product')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Product.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Product Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('product/list.html', context)