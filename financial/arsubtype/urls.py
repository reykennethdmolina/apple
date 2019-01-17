#__author__ = 'kelvin'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^savearsubtype/$', views.savearsubtype, name='savearsubtype'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
]
