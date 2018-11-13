import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
#JsonResponse
from inventoryitem.models import Inventoryitem
from inventoryitemclass.models import Inventoryitemclass
from unitofmeasure.models import Unitofmeasure
#from inventoryitemtype.models import Inventoryitemtype
#from django.views.decorators.csrf import csrf_exempt
#from django.core import serializers
from json_views.views import JSONDataView

from endless_pagination.views import AjaxListView
from django.db.models import Q
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Inventoryitem
    template_name = 'inventoryitem/index.html'
    page_template = 'inventoryitem/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Inventoryitem.objects.all().filter(isdeleted=0)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(code__icontains=keysearch) |
                                 Q(description__icontains=keysearch) |
                                 Q(inventoryitemclass__code__icontains=keysearch) |
                                 Q(inventoryitemclass__description__icontains=keysearch))

            print 123
        return query


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Inventoryitem
    template_name = 'inventoryitem/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Inventoryitem
    template_name = 'inventoryitem/create.html'
    fields = ['code', 'description', 'inventoryitemclass', 'unitofmeasure',
              'unitcost', 'quantity', 'stocklevel', 'expensestatus', 'specialstatus']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitem.add_inventoryitem'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def post(self, request, **kwargs):
        request.POST = request.POST.copy()
        request.POST['code'] = request.POST['prefixcode'] + request.POST['code']
        return super(CreateView, self).post(request, **kwargs)

    # def get_initial(self):
    #     return {'code': 'hoyken'}
    # def form_invalid(self, form, **kwargs):
    #     form= self.get_context_data(**kwargs)
    #     return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/inventoryitem')

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['inventoryitemclass'] = Inventoryitemclass.objects.\
            filter(isdeleted=0).order_by('description')
        context['unitofmeasure'] = Unitofmeasure.objects.\
            filter(isdeleted=0).order_by('description')
        return context


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Inventoryitem
    template_name = 'inventoryitem/edit.html'
    fields = ['code', 'description', 'inventoryitemclass', 'unitofmeasure',
              'unitcost', 'quantity', 'stocklevel', 'expensestatus', 'specialstatus']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitem.change_inventoryitem'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['inventoryitemclass'] = Inventoryitemclass.objects.\
            filter(isdeleted=0).order_by('description')
        context['unitofmeasure'] = Unitofmeasure.objects.\
            filter(isdeleted=0).order_by('description')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['description', 'unitofmeasure',
                                        'unitcost', 'quantity', 'stocklevel',
                                        'expensestatus', 'specialstatus', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/inventoryitem')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Inventoryitem
    template_name = 'inventoryitem/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('inventoryitem.delete_inventoryitem'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/inventoryitem')

@method_decorator(login_required, name='dispatch')
class Getclasstypecode(JSONDataView):


    def get_context_data(self, **kwargs):
        context = super(Getclasstypecode, self).get_context_data(**kwargs)
        inventoryclassid = self.request.GET.get('inventoryclassid')
        context['inventoryclassdata'] = Inventoryitemclass.objects.filter(pk=inventoryclassid)
        return context

#@csrf_exempt
# def getclasstypecode(request):
#
#     if request.method == 'POST':
#         classid = request.POST['inventoryclassid']
#         inventoryclassdata = Inventoryitemclass.objects.all()
#         # inventoryclassdata = Inventoryitemclass.objects.raw("SELECT class.*, itype.code AS testlang "
#         #                                                     "FROM inventoryitemclass AS class "
#         #                                                     "INNER JOIN inventoryitemtype AS itype ON class.inventoryitemtype_id = itype.id "
#         #                                                     "WHERE class.id = %s", str(classid))
#
#         print(inventoryclassdata)
#         data = {
#             'status': 'success',
#             'inventoryclassdata': serializers.serialize("json", inventoryclassdata),
#         }
#     else:
#         data = {
#             'status': 'error',
#         }
#     return JsonResponse(data)

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Inventoryitem.objects.filter(isdeleted=0).order_by('code')
        context = {
            "title": "Inventory Masterfile List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('inventoryitem/list.html', context)
