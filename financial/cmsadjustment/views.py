from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.decorators import method_decorator
from companyparameter.models import Companyparameter
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from endless_pagination.views import AjaxListView
from . models import Cmmain, Cmitem
from easy_pdf.views import PDFTemplateView
import datetime
from product.models import Product
import decimal


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Cmmain
    template_name = 'cmsadjustment/index.html'
    page_template = 'cmsadjustment/index_list.html'
    context_object_name = 'data_list'

    def get_queryset(self):
        query = Cmmain.objects.all().filter(isdeleted=0)

        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(cmnum__icontains=keysearch) |
                                 Q(cmdate__icontains=keysearch) |
                                 Q(particulars__icontains=keysearch) |
                                 Q(amount__icontains=keysearch))
        return query


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Cmmain
    template_name = 'cmsadjustment/create.html'
    fields = ['cmdate', 'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('cmsadjustment.add_cmmain'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['product'] = Product.objects.filter(isdeleted=0, status='A').order_by('code')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        year = str(form.cleaned_data['cmdate'].year)
        yearqs = Cmmain.objects.filter(cmnum__startswith=year)

        if yearqs:
            cmnumlast = yearqs.latest('cmnum')
            latestcmnum = str(cmnumlast)
            print "latest: " + latestcmnum

            cmnum = year
            last = str(int(latestcmnum[4:]) + 1)
            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                cmnum += '0'
            cmnum += last
        else:
            cmnum = year + '000001'

        print 'cmnum: ' + cmnum
        self.object.cmnum = cmnum
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()

        totalamount = 0
        i = 0

        for data in self.request.POST.getlist('product[]'):
            print 'hey: ' + str(data)
            cmitem = Cmitem()
            cmitem.cmmain = self.object
            cmitem.item_counter = i + 1
            cmitem.cmnum = self.object.cmnum
            cmitem.cmdate = self.object.cmdate
            cmitem.product = Product.objects.get(pk=int(data))
            cmitem.product_code = cmitem.product.code
            cmitem.product_name = cmitem.product.description
            cmitem.amount = float(self.request.POST.getlist('amount[]')[i].replace(',', ''))
            cmitem.enterby = self.request.user
            cmitem.modifyby = self.request.user
            cmitem.save()
            totalamount += cmitem.amount
            i += 1

        self.object.amount = totalamount
        self.object.save()

        return HttpResponseRedirect('/cmsadjustment/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Cmmain
    template_name = 'cmsadjustment/update.html'
    fields = ['cmdate', 'particulars']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('cmsadjustment.change_cmmain'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['product'] = Product.objects.filter(isdeleted=0, status='A').order_by('code')
        context['items'] = Cmitem.objects.filter(isdeleted=0, status='A', cmmain=self.object.pk).\
            order_by('item_counter')
        context['currentcounter'] = Cmitem.objects.filter(isdeleted=0, status='A', cmmain=self.object.pk). \
            order_by('item_counter').last().item_counter + 1
        context['cmnum'] = self.object.cmnum
        context['totalamount'] = self.object.amount

        return context

    def form_valid(self, form):
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['cmdate', 'particulars', 'modifyby', 'modifydate'])

        Cmitem.objects.filter(isdeleted=0, status='A', cmmain=self.object.pk).delete()

        totalamount = 0
        i = 0

        for data in self.request.POST.getlist('product[]'):
            cmitem = Cmitem()
            cmitem.cmmain = self.object
            cmitem.item_counter = i + 1
            cmitem.cmnum = self.object.cmnum
            cmitem.cmdate = self.object.cmdate
            cmitem.product = Product.objects.get(pk=int(data))
            cmitem.product_code = cmitem.product.code
            cmitem.product_name = cmitem.product.description
            cmitem.amount = float(self.request.POST.getlist('amount[]')[i].replace(',', ''))
            cmitem.enterby = self.request.user
            cmitem.modifyby = self.request.user
            cmitem.save()
            totalamount += cmitem.amount
            i += 1

        self.object.amount = totalamount
        self.object.save(update_fields=['amount'])

        return HttpResponseRedirect('/cmsadjustment/' + str(self.object.id) + '/update')


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Cmmain
    template_name = 'cmsadjustment/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)

        # items
        context['items'] = Cmitem.objects.filter(isdeleted=0, status='A', cmmain=self.object.pk).\
            order_by('item_counter')

        return context


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Cmmain
    template_name = 'cmsadjustment/delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('cmsadjustment.delete_cmmain') or self.object.status == 'O' \
                or self.object.cmstatus == 'A' or self.object.cmstatus == 'I' or self.object.cmstatus == 'R':
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'C'
        self.object.cmstatus = 'D'
        self.object.save()

        return HttpResponseRedirect('/cmsadjustment')


@method_decorator(login_required, name='dispatch')
class Pdf(PDFTemplateView):
    model = Cmmain
    template_name = 'cmsadjustment/pdf.html'

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)

        context['cmmain'] = Cmmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        context['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        context['items'] = Cmitem.objects.filter(cmmain=self.kwargs['pk'], isdeleted=0).order_by('item_counter')

        context['pagesize'] = 'Letter'
        context['orientation'] = 'portrait'
        context['logo'] = "http://" + self.request.META['HTTP_HOST'] + "/static/images/pdi.jpg"

        printedcm = Cmmain.objects.get(pk=self.kwargs['pk'], isdeleted=0, status='A')
        printedcm.print_ctr += 1
        printedcm.save()
        return context



