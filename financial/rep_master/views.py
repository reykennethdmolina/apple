from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from bank.models import Bank
from bankbranch.models import Bankbranch
from bankaccount.models import Bankaccount


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