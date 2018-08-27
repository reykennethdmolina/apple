# author__ = 'Grace Ann'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateView.as_view(), name='update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    url(r'^searchsupplier/$', views.searchSupplier, name='searchsupplier'),
    url(r'^getsupplierdata/$', views.getSupplierData, name='getsupplierdata'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
]

