import datetime
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404, HttpResponse
from productbudget.models import Productbudget
from product.models import Product
from chartofaccount.models import Chartofaccount
from companyparameter.models import Companyparameter
# pagination and search
from endless_pagination.views import AjaxListView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
from annoying.functions import get_object_or_None
from utils.mixins import ReportContentMixin
from easy_pdf.views import PDFTemplateView
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
import pandas as pd


@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = Productbudget
    template_name = 'productbudget/index.html'
    context_object_name = 'data_list'

    # pagination and search
    page_template = 'productbudget/index_list.html'

    def get_queryset(self):
        query = Productbudget.objects.all().filter(isdeleted=0)
        if self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name):
            keysearch = str(self.request.COOKIES.get('keysearch_' + self.request.resolver_match.app_name))
            query = query.filter(Q(year__icontains=keysearch) |
                                 Q(product__code__icontains=keysearch) |
                                 Q(product__description__icontains=keysearch) |
                                 Q(chartofaccount__accountcode__icontains=keysearch) |
                                 Q(chartofaccount__description__icontains=keysearch))
        return query


@method_decorator(login_required, name='dispatch')
class DetailView(DetailView):
    model = Productbudget
    template_name = 'productbudget/detail.html'


@method_decorator(login_required, name='dispatch')
class CreateView(CreateView):
    model = Productbudget
    template_name = 'productbudget/create.html'
    fields = ['year', 'product', 'chartofaccount',
              'remarks', 'formula', 'method',
              'mjan', 'mfeb', 'mmar',
              'mapr', 'mmay', 'mjun',
              'mjul', 'maug', 'msep',
              'moct', 'mnov', 'mdec']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('productbudget.add_productbudget'):
            raise Http404
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['product'] = Product.objects.filter(isdeleted=0).order_by('description')
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enterby = self.request.user
        self.object.modifyby = self.request.user
        self.object.save()
        return HttpResponseRedirect('/productbudget')


@method_decorator(login_required, name='dispatch')
class UpdateView(UpdateView):
    model = Productbudget
    template_name = 'productbudget/edit.html'
    fields = ['year', 'product', 'chartofaccount',
              'remarks', 'formula', 'method',
              'mjan', 'mfeb', 'mmar',
              'mapr', 'mmay', 'mjun',
              'mjul', 'maug', 'msep',
              'moct', 'mnov', 'mdec']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('productbudget.change_productbudget'):
            raise Http404
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['product'] = Product.objects.filter(isdeleted=0).order_by('description')
        if self.request.POST.get('chartofaccount', False):
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.request.POST['chartofaccount'], isdeleted=0)
        elif self.object.chartofaccount:
            context['chartofaccount'] = Chartofaccount.objects.get(pk=self.object.chartofaccount.id, isdeleted=0)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save()
        return HttpResponseRedirect('/productbudget')


@method_decorator(login_required, name='dispatch')
class DeleteView(DeleteView):
    model = Productbudget
    template_name = 'productbudget/delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('productbudget.delete_productbudget'):
            raise Http404
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.isdeleted = 1
        self.object.status = 'I'
        self.object.save()
        return HttpResponseRedirect('/productbudget')


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = Productbudget
    template_name = 'productbudget/report/index.html'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context['product'] = Product.objects.filter(isdeleted=0).order_by('code')

        # print context['product']

        return context

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        q = []
        new_list = []
        mtotal = 0
        list_total = []
        report = request.GET['report']
        dyear = request.GET['year']
        product = request.GET['product']
        chartofaccount = request.GET['chartofaccount']
        title = "Product Budget Report"
        list = Productbudget.objects.filter(isdeleted=0).order_by('year')[:0]

        if report == '1':
            title = "Product - Summary"
            q = Productbudget.objects.filter(isdeleted=0).order_by('year')
        elif report == '2':
            title = "Product - Detailed"
            q = Productbudget.objects.filter(isdeleted=0).order_by('year', 'product__code', 'chartofaccount__accountcode')
        elif report == '3':
            title = "Account - Summary"
            q = Productbudget.objects.filter(isdeleted=0).order_by('year')
        elif report == '4':
            title = "Account - Detailed"
            q = Productbudget.objects.filter(isdeleted=0).order_by('year', 'chartofaccount__accountcode', 'product__code')

        # Condition and Statement
        if dyear != '':
            q = q.filter(year=dyear)
        if product != '':
            q = q.filter(product=product)

        if chartofaccount != 'null':
            q = q.filter(chartofaccount=chartofaccount)

        if report == '1':
            q = q.values('product__description', 'product__code')\
                .annotate(
                   Sum('mjan'),
                   Sum('mfeb'),
                   Sum('mmar'),
                   Sum('mapr'),
                   Sum('mmay'),
                   Sum('mjun'),
                   Sum('mjul'),
                   Sum('maug'),
                   Sum('msep'),
                   Sum('moct'),
                   Sum('mnov'),
                   Sum('mdec'),
                   total=Sum('mjan')+Sum('mfeb')+Sum('mmar')+Sum('mapr')+Sum('mmay')+Sum('mjun')+Sum('mjul')+Sum('maug')+Sum('msep')+Sum('moct')+Sum('mnov')+Sum('mdec'),
                   )\
                .order_by('product__code')
            list_total = q.aggregate(
                Sum('mjan__sum'),
                Sum('mfeb__sum'),
                Sum('mmar__sum'),
                Sum('mapr__sum'),
                Sum('mmay__sum'),
                Sum('mjun__sum'),
                Sum('mjul__sum'),
                Sum('maug__sum'),
                Sum('msep__sum'),
                Sum('moct__sum'),
                Sum('mnov__sum'),
                Sum('mdec__sum'),
                Sum('total'),
              )

            list = q

        elif report == '2':

            q = q.values('product__code', 'product__description', 'chartofaccount__accountcode', 'chartofaccount__description',
                         'mjan', 'mfeb', 'mmar', 'mapr', 'mmay', 'mjun', 'mjul', 'maug', 'msep', 'moct', 'mnov', 'mdec')\
                .order_by('product__code', 'chartofaccount__accountcode')
            #print q
            df = pd.DataFrame.from_records(q)

            grandmjan = 0
            grandmfeb = 0
            grandmmar = 0
            grandmapr = 0
            grandmmay = 0
            grandmjun = 0
            grandmjul = 0
            grandmaug = 0
            grandmsep = 0
            grandmoct = 0
            grandmnov = 0
            grandmdec = 0
            grandmtotal = 0

            for code, product in df.fillna('NaN').groupby(['product__code', 'product__description']):
                submjan = 0
                submfeb = 0
                submmar = 0
                submapr = 0
                submmay = 0
                submjun = 0
                submjul = 0
                submaug = 0
                submsep = 0
                submoct = 0
                submnov = 0
                submdec = 0
                submtotal = 0
                for item, data in product.iterrows():
                    mtotal = float(data.mjan)+float(data.mfeb)+float(data.mmar)+float(data.mapr)+float(data.mmay)+float(data.mjun)\
                             +float(data.mjul)+float(data.maug)+float(data.msep)+float(data.moct)+float(data.mnov)+float(data.mdec)
                    new_list.append({'pcode': data.product__code, 'product': data.product__description,
                                     'ccode': data.chartofaccount__accountcode, 'chartofaccount': data.chartofaccount__description,
                                     'mjan': data.mjan, 'mfeb': data.mfeb, 'mmar': data.mmar, 'mapr': data.mapr,
                                     'mmay': data.mmay, 'mjun': data.mjun, 'mjul': data.mjul, 'maug': data.maug,
                                     'msep': data.msep, 'moct': data.moct, 'mnov': data.mnov, 'mdec': data.mdec,
                                     'mtotal': mtotal })

                    submjan += data.mjan
                    submfeb += data.mfeb
                    submmar += data.mmar
                    submapr += data.mapr
                    submmay += data.mmay
                    submjun += data.mjun
                    submjul += data.mjul
                    submaug += data.maug
                    submsep += data.msep
                    submoct += data.moct
                    submnov += data.mnov
                    submdec += data.mdec
                    submtotal += mtotal

                    grandmjan += data.mjan
                    grandmfeb += data.mfeb
                    grandmmar += data.mmar
                    grandmapr += data.mapr
                    grandmmay += data.mmay
                    grandmjun += data.mjun
                    grandmjul += data.mjul
                    grandmaug += data.maug
                    grandmsep += data.msep
                    grandmoct += data.moct
                    grandmnov += data.mnov
                    grandmdec += data.mdec
                    grandmtotal += mtotal

                new_list.append({'pcode': data.product__code, 'product': data.product__description,
                                 'ccode': 'subtotal', 'chartofaccount': '',
                                 'mjan': submjan, 'mfeb': submfeb, 'mmar': submmar, 'mapr': submapr,
                                 'mmay': submmay, 'mjun': submjun, 'mjul': submjul, 'maug': submaug,
                                 'msep': submsep, 'moct': submoct, 'mnov': submnov, 'mdec': submdec,
                                 'mtotal': submtotal })

            list_total.append({'pcode': '', 'product': '',
                             'ccode': 'grandtotal', 'chartofaccount': '',
                             'mjan': grandmjan, 'mfeb': grandmfeb, 'mmar': grandmmar, 'mapr': grandmapr,
                             'mmay': grandmmay, 'mjun': grandmjun, 'mjul': grandmjul, 'maug': grandmaug,
                             'msep': grandmsep, 'moct': grandmoct, 'mnov': grandmnov, 'mdec': grandmdec,
                             'mtotal': grandmtotal })
            #for id, accountcode in df.fillna('NaN').groupby(['chartofaccount_id', 'chartofaccount__accountcode']):
            #print df
            list = new_list

        elif report == '3':
            q = q.values('chartofaccount__description', 'chartofaccount__accountcode')\
                .annotate(
                   Sum('mjan'),
                   Sum('mfeb'),
                   Sum('mmar'),
                   Sum('mapr'),
                   Sum('mmay'),
                   Sum('mjun'),
                   Sum('mjul'),
                   Sum('maug'),
                   Sum('msep'),
                   Sum('moct'),
                   Sum('mnov'),
                   Sum('mdec'),
                   total=Sum('mjan')+Sum('mfeb')+Sum('mmar')+Sum('mapr')+Sum('mmay')+Sum('mjun')+Sum('mjul')+Sum('maug')+Sum('msep')+Sum('moct')+Sum('mnov')+Sum('mdec'),
                   )\
                .order_by('chartofaccount__accountcode')
            list_total = q.aggregate(
                Sum('mjan__sum'),
                Sum('mfeb__sum'),
                Sum('mmar__sum'),
                Sum('mapr__sum'),
                Sum('mmay__sum'),
                Sum('mjun__sum'),
                Sum('mjul__sum'),
                Sum('maug__sum'),
                Sum('msep__sum'),
                Sum('moct__sum'),
                Sum('mnov__sum'),
                Sum('mdec__sum'),
                Sum('total'),
              )

            list = q

        elif report == '4':

            q = q.values('chartofaccount__accountcode', 'chartofaccount__description', 'product__code', 'product__description',
                         'mjan', 'mfeb', 'mmar', 'mapr', 'mmay', 'mjun', 'mjul', 'maug', 'msep', 'moct', 'mnov', 'mdec')\
                .order_by('chartofaccount__accountcode', 'product__code')
            #print q
            df = pd.DataFrame.from_records(q)

            grandmjan = 0
            grandmfeb = 0
            grandmmar = 0
            grandmapr = 0
            grandmmay = 0
            grandmjun = 0
            grandmjul = 0
            grandmaug = 0
            grandmsep = 0
            grandmoct = 0
            grandmnov = 0
            grandmdec = 0
            grandmtotal = 0

            for code, chartofaccount in df.fillna('NaN').groupby(['chartofaccount__accountcode', 'chartofaccount__description']):
                submjan = 0
                submfeb = 0
                submmar = 0
                submapr = 0
                submmay = 0
                submjun = 0
                submjul = 0
                submaug = 0
                submsep = 0
                submoct = 0
                submnov = 0
                submdec = 0
                submtotal = 0
                for item, data in chartofaccount.iterrows():
                    mtotal = float(data.mjan)+float(data.mfeb)+float(data.mmar)+float(data.mapr)+float(data.mmay)+float(data.mjun)\
                             +float(data.mjul)+float(data.maug)+float(data.msep)+float(data.moct)+float(data.mnov)+float(data.mdec)
                    new_list.append({'ccode': data.chartofaccount__accountcode, 'chartofaccount': data.chartofaccount__description,
                                     'pcode': data.product__code, 'product': data.product__description,
                                     'mjan': data.mjan, 'mfeb': data.mfeb, 'mmar': data.mmar, 'mapr': data.mapr,
                                     'mmay': data.mmay, 'mjun': data.mjun, 'mjul': data.mjul, 'maug': data.maug,
                                     'msep': data.msep, 'moct': data.moct, 'mnov': data.mnov, 'mdec': data.mdec,
                                     'mtotal': mtotal })

                    submjan += data.mjan
                    submfeb += data.mfeb
                    submmar += data.mmar
                    submapr += data.mapr
                    submmay += data.mmay
                    submjun += data.mjun
                    submjul += data.mjul
                    submaug += data.maug
                    submsep += data.msep
                    submoct += data.moct
                    submnov += data.mnov
                    submdec += data.mdec
                    submtotal += mtotal

                    grandmjan += data.mjan
                    grandmfeb += data.mfeb
                    grandmmar += data.mmar
                    grandmapr += data.mapr
                    grandmmay += data.mmay
                    grandmjun += data.mjun
                    grandmjul += data.mjul
                    grandmaug += data.maug
                    grandmsep += data.msep
                    grandmoct += data.moct
                    grandmnov += data.mnov
                    grandmdec += data.mdec
                    grandmtotal += mtotal

                new_list.append({'ccode': data.chartofaccount__accountcode, 'chartofaccount': data.chartofaccount__description,
                                 'pcode': 'subtotal', 'product': '',
                                 'mjan': submjan, 'mfeb': submfeb, 'mmar': submmar, 'mapr': submapr,
                                 'mmay': submmay, 'mjun': submjun, 'mjul': submjul, 'maug': submaug,
                                 'msep': submsep, 'moct': submoct, 'mnov': submnov, 'mdec': submdec,
                                 'mtotal': submtotal })

            list_total.append({'ccode': '', 'chartofaccount': '',
                             'pcode': 'grandtotal', 'product': '',
                             'mjan': grandmjan, 'mfeb': grandmfeb, 'mmar': grandmmar, 'mapr': grandmapr,
                             'mmay': grandmmay, 'mjun': grandmjun, 'mjul': grandmjul, 'maug': grandmaug,
                             'msep': grandmsep, 'moct': grandmoct, 'mnov': grandmnov, 'mdec': grandmdec,
                             'mtotal': grandmtotal })
            #for id, accountcode in df.fillna('NaN').groupby(['chartofaccount_id', 'chartofaccount__accountcode']):
            #print df
            list = new_list


        #print q

        context = {
            "title": title,
            "today": timezone.now(),
            "company": company,
            "list": list,
            "list_total": list_total,
            "username": request.user,
        }
        if report == '1':
            return Render.render('productbudget/report/report_1.html', context)
        elif report == '2':
            return Render.render('productbudget/report/report_2.html', context)
        elif report == '3':
            return Render.render('productbudget/report/report_3.html', context)
        elif report == '4':
            return Render.render('productbudget/report/report_4.html', context)
        else:
            return Render.render('productbudget/report/report_1.html', context)
