from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from bank.models import Bank
from bankbranch.models import Bankbranch
from bankaccount.models import Bankaccount
from product.models import Product
from mainproduct.models import Mainproduct
from branch.models import Branch
from ataxcode.models import Ataxcode
from vat.models import Vat
from inputvat.models import Inputvat

@method_decorator(login_required, name='dispatch')
class BankList(TemplateView):
    template_name = 'rep_master/bank.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Bank.objects.filter(status='A', isdeleted=0)

        if self.request.GET:
            if self.request.GET.getlist('rep_order[]'):
                query = query.order_by(*self.request.GET.getlist('rep_order[]'))
                context['rep_order'] = ','.join(map(str, self.request.GET.getlist('rep_order[]')))

            if self.request.GET.get('rep_asc_holder'):
                key_data = str(self.request.GET.get('rep_asc_holder'))
                if key_data == 'd':
                    query = query.reverse()
                context['rep_asc_holder'] = self.request.GET.get('rep_asc_holder')

        context['query'] = query

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class BankBranchList(TemplateView):
    template_name = 'rep_master/bankbranch.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Bankbranch.objects.filter(status='A', isdeleted=0)

        if self.request.GET:
            if self.request.GET.getlist('rep_order[]'):
                query = query.order_by(*self.request.GET.getlist('rep_order[]'))
                context['rep_order'] = ','.join(map(str, self.request.GET.getlist('rep_order[]')))

            if self.request.GET.get('rep_asc_holder'):
                key_data = str(self.request.GET.get('rep_asc_holder'))
                if key_data == 'd':
                    query = query.reverse()
                context['rep_asc_holder'] = self.request.GET.get('rep_asc_holder')

        context['query'] = query

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class BankAccountList(TemplateView):
    template_name = 'rep_master/bankaccount.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Bankaccount.objects.filter(status='A', isdeleted=0)

        if self.request.GET:
            if self.request.GET.getlist('rep_order[]'):
                query = query.order_by(*self.request.GET.getlist('rep_order[]'))
                context['rep_order'] = ','.join(map(str, self.request.GET.getlist('rep_order[]')))

            if self.request.GET.get('rep_asc_holder'):
                key_data = str(self.request.GET.get('rep_asc_holder'))
                if key_data == 'd':
                    query = query.reverse()
                context['rep_asc_holder'] = self.request.GET.get('rep_asc_holder')

        context['query'] = query

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class ProductList(TemplateView):
    template_name = 'rep_master/product.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Product.objects.filter(status='A', isdeleted=0)

        if self.request.GET:
            if self.request.GET.getlist('rep_order[]'):
                query = query.order_by(*self.request.GET.getlist('rep_order[]'))
                context['rep_order'] = ','.join(map(str, self.request.GET.getlist('rep_order[]')))

            if self.request.GET.get('rep_asc_holder'):
                key_data = str(self.request.GET.get('rep_asc_holder'))
                if key_data == 'd':
                    query = query.reverse()
                context['rep_asc_holder'] = self.request.GET.get('rep_asc_holder')

        context['query'] = query

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class MainProductList(TemplateView):
    template_name = 'rep_master/mainproduct.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Mainproduct.objects.filter(status='A', isdeleted=0)

        if self.request.GET:
            if self.request.GET.getlist('rep_order[]'):
                query = query.order_by(*self.request.GET.getlist('rep_order[]'))
                context['rep_order'] = ','.join(map(str, self.request.GET.getlist('rep_order[]')))

            if self.request.GET.get('rep_asc_holder'):
                key_data = str(self.request.GET.get('rep_asc_holder'))
                if key_data == 'd':
                    query = query.reverse()
                context['rep_asc_holder'] = self.request.GET.get('rep_asc_holder')

        context['query'] = query

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class BranchList(TemplateView):
    template_name = 'rep_master/branch.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Branch.objects.filter(status='A', isdeleted=0)

        if self.request.GET:
            if self.request.GET.getlist('rep_order[]'):
                query = query.order_by(*self.request.GET.getlist('rep_order[]'))
                context['rep_order'] = ','.join(map(str, self.request.GET.getlist('rep_order[]')))

            if self.request.GET.get('rep_asc_holder'):
                key_data = str(self.request.GET.get('rep_asc_holder'))
                if key_data == 'd':
                    query = query.reverse()
                context['rep_asc_holder'] = self.request.GET.get('rep_asc_holder')

        context['query'] = query

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class AtaxCodeList(TemplateView):
    template_name = 'rep_master/ataxcode.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Ataxcode.objects.filter(status='A', isdeleted=0)
        print query

        if self.request.GET:
            if self.request.GET.getlist('rep_order[]'):
                query = query.order_by(*self.request.GET.getlist('rep_order[]'))
                context['rep_order'] = ','.join(map(str, self.request.GET.getlist('rep_order[]')))

            if self.request.GET.get('rep_asc_holder'):
                key_data = str(self.request.GET.get('rep_asc_holder'))
                if key_data == 'd':
                    query = query.reverse()
                context['rep_asc_holder'] = self.request.GET.get('rep_asc_holder')

        context['query'] = query

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class VatList(TemplateView):
    template_name = 'rep_master/vat.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Vat.objects.filter(status='A', isdeleted=0)

        if self.request.GET:
            if self.request.GET.getlist('rep_order[]'):
                query = query.order_by(*self.request.GET.getlist('rep_order[]'))
                context['rep_order'] = ','.join(map(str, self.request.GET.getlist('rep_order[]')))

            if self.request.GET.get('rep_asc_holder'):
                key_data = str(self.request.GET.get('rep_asc_holder'))
                if key_data == 'd':
                    query = query.reverse()
                context['rep_asc_holder'] = self.request.GET.get('rep_asc_holder')

        context['query'] = query

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class InputVatList(TemplateView):
    template_name = 'rep_master/inputvat.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Inputvat.objects.filter(status='A', isdeleted=0)

        if self.request.GET:
            if self.request.GET.getlist('rep_order[]'):
                key_data = str(self.request.GET.getlist('rep_order[]'))
                query = query.order_by(*self.request.GET.getlist('rep_order[]'))
                context['rep_order'] = ','.join(map(str, self.request.GET.getlist('rep_order[]')))

            if self.request.GET.get('rep_asc_holder'):
                key_data = str(self.request.GET.get('rep_asc_holder'))
                if key_data == 'd':
                    query = query.reverse()
                context['rep_asc_holder'] = self.request.GET.get('rep_asc_holder')

        context['query'] = query

        return self.render_to_response(context)

