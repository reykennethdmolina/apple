#__author__ = 'grace'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^savesubgroups/$', views.savesubgroups, name='savesubgroups'),
]
