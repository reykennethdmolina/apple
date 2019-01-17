import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from supplieraccount.models import Supplieraccount
from supplier.models import Supplier
from employee.models import Employee
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Supplieraccount
    template_name = 'supplieraccount/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Supplieraccount.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Supplieraccount
    template_name = 'supplieraccount/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Supplieraccount
    template_name = 'supplieraccount/create.html'
    fields = ['supplier', 'accountno', 'employee', 'name',
              'phoneno', 'duono', 'serialno', 'imeino',
              'subsidyamount', 'accountgroup', 'accountcategory', 'remarks']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('supplieraccount.add_supplieraccount'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('name')
        context['employee'] = Employee.objects.filter(isdeleted=0).exclude(lastname='').order_by('lastname')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/supplieraccount')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Supplieraccount
    template_name = 'supplieraccount/edit.html'
    fields = ['supplier', 'accountno', 'employee', 'name',
              'phoneno', 'duono', 'serialno', 'imeino',
              'subsidyamount', 'accountgroup', 'accountcategory', 'remarks']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('supplieraccount.change_supplieraccount'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['supplier'] = Supplier.objects.filter(isdeleted=0).order_by('name')
        context['employee'] = Employee.objects.filter(isdeleted=0).exclude(lastname='').order_by('lastname')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['supplier', 'accountno', 'employee', 'name',
                                        'phoneno', 'duono', 'serialno', 'imeino',
                                        'subsidyamount', 'accountgroup', 'accountcategory', 'remarks',
                                        'modifyby', 'modifydate'])
        return HttpResponseRedirect('/supplieraccount')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Supplieraccount
    template_name = 'supplieraccount/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('supplieraccount.delete_supplieraccount'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/supplieraccount')

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Supplieraccount.objects.filter(isdeleted=0).order_by('supplier', 'name')
        context = {
            "title": "Supplier's Account Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('supplieraccount/list.html', context)


@method_decorator(login_required, name='dispatch')
class GeneratePDFReport2(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Supplieraccount.objects.filter(isdeleted=0).order_by('supplier', 'name')
        context = {
            "title": "Supplier's Account Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('supplieraccount/list_report2.html', context)