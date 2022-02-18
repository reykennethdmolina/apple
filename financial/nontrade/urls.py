#__author__ = 'kelvin'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^transgenerate/$', views.transgenerate, name='transgenerate'),
    url(r'^tagging/$', views.tagging, name='tagging'),
    url(r'^transexcel/$', views.TransExcel.as_view(), name='transexcel'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^datafix/$', views.datafix, name='datafix'),
]
