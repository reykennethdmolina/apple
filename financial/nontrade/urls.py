#__author__ = 'kelvin'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^transgenerate/$', views.transgenerate, name='transgenerate'),
    # url(r'^tagging/$', views.tagging, name='tagging'),
    url(r'^tagarnontrade/$', views.tagarnontrade, name='tagarnontrade'),
    url(r'^transexcel/$', views.TransExcel.as_view(), name='transexcel'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^datafix/$', views.datafix, name='datafix'),
    url(r'^report/$', views.ReportView.as_view(), name='report'),
    url(r'^pdf2/$', views.GenerateReportPDF.as_view(), name='pdf2'),
    url(r'^manage/$', views.ManageARNonTradeView.as_view(), name='managearnontradeview'),
    url(r'^managearnontrade/$', views.managearnontrade, name='managearnontrade'),
    url(r'^untagarnontrade/$', views.untagarnontrade, name='untagarnontrade'),
]
