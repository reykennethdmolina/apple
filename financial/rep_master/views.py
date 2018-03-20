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
from collector.models import Collector
from employee.models import Employee
from productbudget.models import Productbudget
from chartofaccount.models import Chartofaccount
from customer.models import Customer
from department.models import Department
from supplier.models import Supplier
from purchaseorder.models import Pomain
from django.db.models import Q, Sum, Count
from dateutil.relativedelta import relativedelta
import datetime


@method_decorator(login_required, name='dispatch')
class IndexList(TemplateView):
    template_name = 'rep_master/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['rep_count_bank'] = Bank.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_bankbranch'] = Bankbranch.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_bankaccount'] = Bankaccount.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_product'] = Product.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_mainproduct'] = Mainproduct.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_branch'] = Branch.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_ataxcode'] = Ataxcode.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_vat'] = Vat.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_inputvat'] = Inputvat.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_collector'] = Collector.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_employee'] = Employee.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_productbudget'] = Productbudget.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_chartofaccount'] = Chartofaccount.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_customer'] = Customer.objects.filter(status='A', isdeleted=0).count()
        context['rep_count_department'] = Department.objects.filter(isdeleted=0).count()
        context['rep_count_supplier'] = Supplier.objects.filter(status='A', isdeleted=0).count()

        context['rep_topdept'] = Employee.objects.all().filter(isdeleted=0, status='A').values('department__code')\
                                                       .annotate(total=Count('department')).order_by('-total')[:5]

        context['rep_newemp'] = Employee.objects.all().filter(isdeleted=0, status='A').order_by('-enterdate')[:5]

        # filter status posted soon
        year_ago = datetime.datetime.now() - relativedelta(years=1)
        context['rep_topsupfrompo'] = Pomain.objects.all().filter(isdeleted=0, status='A', responsedate__gte=year_ago)\
                                                          .values('supplier__code', 'supplier__name')\
                                                          .annotate(totaluse=Count('supplier'))\
                                                          .order_by('-totaluse')[:5]
        context['rep_topsupfrompototal'] = Pomain.objects.all().filter(isdeleted=0, status='A', responsedate__gte=year_ago)\
                                                               .exclude(supplier__isnull=True).count()

        return context


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


@method_decorator(login_required, name='dispatch')
class CollectorCashierList(TemplateView):
    template_name = 'rep_master/collectorcashier.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Collector.objects.filter(status='A', isdeleted=0)

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


@method_decorator(login_required, name='dispatch')
class EmployeeList(TemplateView):
    template_name = 'rep_master/employee.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Employee.objects.filter(status='A', isdeleted=0)

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


@method_decorator(login_required, name='dispatch')
class ProductBudgetList(TemplateView):
    template_name = 'rep_master/productbudget.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        query = Productbudget.objects.filter(status='A', isdeleted=0)

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


