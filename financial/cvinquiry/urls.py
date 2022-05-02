# author = 'bossing'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^generate/$', views.Generate.as_view(), name='generate'),
    url(r'^status/$', views.StatusView.as_view(), name='status'),
    url(r'^transgenerate/$', views.transgenerate, name='transgenerate'),
    url(r'^stalecheck/$', views.stalecheck, name='stalecheck'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^excel/$', views.GenerateExcel.as_view(), name='excel'),
    url(r'^excelstatus/$', views.GenerateExcelStatus.as_view(), name='excelstatus'),
    url(r'^tagreceived/$', views.tagreceived, name='tagreceived'),
    url(r'^tagclaimed/$', views.tagclaimed, name='tagclaimed'),
    url(r'^savecashierremarks/$', views.savecashierremarks, name='savecashierremarks'),
    url(r'^pdf2/$', views.GeneratePDF2.as_view(), name='pdf2'),
    # url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # url(r'^create/$', views.CreateView.as_view(), name='create'),
    # url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateView.as_view(), name='update'),
    # url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    # url(r'^report/$', views.ReportView.as_view(), name='report'),
    # url(r'^pdf2/$', views.GeneratePDF.as_view(), name='pdf2'),
    # url(r'^(?P<pk>[0-9]+)/pdf/$', views.Pdf.as_view(), name='pdf'),
]
