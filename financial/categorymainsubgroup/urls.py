#__author__ = 'acorales'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^savesubgroups/$', views.savesubgroups, name='savesubgroups'),
    url(r'^getsubgroups/$', views.getsubgroups, name='getsubgroups'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
]
