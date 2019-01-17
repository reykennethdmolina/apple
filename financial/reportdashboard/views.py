from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from module.models import Module
from .models import Reportmaintenance, Reportmaintenancemodule
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from financial.utils import Render
from django.utils import timezone
from companyparameter.models import Companyparameter


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'reportdashboard/index-dynamic.html'
    context_object_name = 'data_list'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['reports'] = Reportmaintenancemodule.objects.filter(isdeleted=0).order_by('reportmaintenance__name', 'reportmodule__name')
        context['reportsblank'] = Reportmaintenance.objects.exclude(id__in=[elem.reportmaintenance.id for elem in Reportmaintenancemodule.objects.filter(isdeleted=0)])
        print context['reportsblank']

        return context


@method_decorator(login_required, name='dispatch')
class MaintenanceView(TemplateView):
    template_name = 'reportdashboard/maintenance.html'
    context_object_name = 'data_list'

    def post(self, request, *args, **kwargs):
        if self.request.POST:
            # COMMAND: edit report list
            if self.request.POST.get('reportlist'):
                Reportmaintenancemodule.objects.filter(reportmaintenance=self.request.POST['reportlist']).delete()
                for data in self.request.POST.getlist('modulelist[]'):
                    Reportmaintenancemodule.objects.create(reportmaintenance=Reportmaintenance.objects.get(pk=self.request.POST['reportlist']),
                                                           reportmodule=Module.objects.get(pk=data))
                return HttpResponseRedirect(self.request.path_info+'?message=saved&get='+self.request.POST['reportlist']
                                            )
            # COMMAND: edit report name
            elif self.request.POST.get('reportedit'):
                exist = Reportmaintenance.objects.filter(name=self.request.POST['reportedit']).exclude(pk=self.request.POST.get('reporteditid'))
                if exist.count() == 0:
                    Reportmaintenance.objects.filter(pk=self.request.POST.get('reporteditid')).update(name=self.request.POST['reportedit'])
                else:
                    return HttpResponseRedirect(self.request.path_info + '?message=exist')
            # COMMAND: new report
            elif self.request.POST.get('reportnew'):
                exist = Reportmaintenance.objects.filter(name=self.request.POST['reportnew'])
                if exist.count() == 0:
                    Reportmaintenance.objects.create(name=self.request.POST['reportnew'])
                else:
                    return HttpResponseRedirect(self.request.path_info+'?message=exist')

        return HttpResponseRedirect(self.request.path_info)

    def dispatch(self, request, *args, **kwargs):
        # COMMAND: delete report
        if self.request.GET.get('delete'):
            Reportmaintenance.objects.filter(pk=self.request.GET['delete']).update(isdeleted=1)
            return redirect('/reportdashboard/maintenance')

        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        # COMMAND: view report list
        if self.request.GET.get('get'):
            context['reportmodule'] = Reportmaintenancemodule.objects.filter(reportmaintenance=self.request.GET['get'], isdeleted=0)
            context['modulelist'] = Module.objects.filter(mainmodule__code='REP', isdeleted=0).order_by('name')

        context['reportlist'] = Reportmaintenance.objects.filter(isdeleted=0)

        return context


@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):
        company = Companyparameter.objects.all().first()
        list = Reportmaintenancemodule.objects.filter(isdeleted=0).order_by('reportmaintenance_id', 'reportmodule_id')
        context = {
            "title": "Report Grouping Master List",
            "today": timezone.now(),
            "company": company,
            "list": list,
            "username": request.user,
        }
        return Render.render('reportdashboard/list.html', context)