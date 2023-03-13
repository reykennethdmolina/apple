# author = 'jek'

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^retrieve/$', views.retrieve, name='retrieve'),
    url(r'^start/$', views.start, name='start'),
    url(r'^pdf/$', views.Pdf.as_view(), name='pdf'),
]