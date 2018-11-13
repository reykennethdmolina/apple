import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from mistype.models import Mistype
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Mistype
    template_name = 'mistype/index.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        return Mistype.objects.all().filter(isdeleted=0).order_by('-pk')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Mistype
    template_name = 'mistype/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Mistype
    template_name = 'mistype/create.html'
    fields = ['code', 'description', 'reason', 'lastno']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mistype.add_mistype'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/mistype')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Mistype
    template_name = 'mistype/edit.html'
    fields = ['code', 'description', 'reason', 'lastno']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mistype.change_mistype'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'reason', 'lastno',
                                        'modifyby', 'modifydate'])
        return HttpResponseRedirect('/mistype')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Mistype
    template_name = 'mistype/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('mistype.delete_mistype'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/mistype')


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Mistype.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "MIS Type Masterfile List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('mistype/list.html', context)
