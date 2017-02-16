#__author__ = 'kelvin'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.ReportView.as_view(), name='index'),
    url(r'^chartofaccount/$', views.ChartofaccountView.as_view(), name='chartofaccountview'),
    url(r'^chartofaccount/generate$', views.ChartofaccountGenerate, name='chartofaccountgenerate'),
    url(r'^chartofaccount/pdf$', views.ChartofaccountPDF.as_view(), name='chartofaccountpdf'),
    url(r'^chartofaccount/xls$', views.ChartofaccountXLS, name='chartofaccountxls'),
]
