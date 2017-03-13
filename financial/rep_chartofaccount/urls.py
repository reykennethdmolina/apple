#__author__ = 'kelvin'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^report', views.report, name='report'),
    url(r'^pdf$', views.Pdf.as_view(), name='pdf'),
    url(r'^xls$', views.xls, name='xls'),
]