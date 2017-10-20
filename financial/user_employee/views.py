from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import Http404
from django.contrib.auth.models import User


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'user_employee/index.html'
    context_object_name = 'data_list'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('employee.can_adduser'):
            raise Http404
        return super(IndexView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['user'] = User.objects.filter(is_active=1).order_by('employee__user', 'username')
        return context
