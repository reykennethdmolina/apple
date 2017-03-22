#__author__ = 'kelvin'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^pdf$', views.Pdf.as_view(), name='pdf'),
    url(r'^report/$', views.Report.as_view(), name='report'),
    url(r'^xlsi/$', views.Xlsi.as_view(), name='xlsi'),
    url(r'^xls$', views.xls, name='xls'),
]
