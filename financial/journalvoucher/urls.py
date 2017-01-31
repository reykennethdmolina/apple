#__author__ = 'reykennethmolina'

from django.conf.urls import url
from .import views

urlpatterns = [
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    #url(r'^create/$', views.CreateView.as_view(), name='create'),
]
