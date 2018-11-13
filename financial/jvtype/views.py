import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from jvtype.models import Jvtype
from department.models import Department
from branch.models import Branch
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter

@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Jvtype
    template_name = 'jvtype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Jvtype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Jvtype
    template_name = 'jvtype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Jvtype
    template_name = 'jvtype/create.html'
    fields = ['code', 'description', 'taxstatus', 'department',
              'branch', 'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('jvtype.add_jvtype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        if self.request.POST.get('department', False):
            context['department'] = Department.objects.get(pk=self.request.POST['department'], isdeleted=0)
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/jvtype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Jvtype
    template_name = 'jvtype/edit.html'
    fields = ['code', 'description', 'taxstatus', 'department', 'branch', 'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('jvtype.change_jvtype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        if self.request.POST.get('department', False):
            context['department'] = Department.objects.get(pk=self.request.POST['department'], isdeleted=0)
        elif self.object.department:
            context['department'] = Department.objects.get(pk=self.object.department.id, isdeleted=0)
        context['branch'] = Branch.objects.filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'taxstatus', 'department',
                                        'branch', 'particulars', 'modifyby',
                                        'modifydate'])
        return HttpResponseRedirect('/jvtype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Jvtype
    template_name = 'jvtype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('jvtype.delete_jvtype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/jvtype')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Jvtype.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "JV Type Masterfile List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('jvtype/list.html', context)
