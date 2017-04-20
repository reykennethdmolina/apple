#__author__ = 'reykennethmolina'

from django.conf.urls import url
from .import views

urlpatterns = [
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateView.as_view(), name='update'),
    #url(r'^create/$', views.CreateView.as_view(), name='create'),
]
