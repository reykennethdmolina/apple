# __author__ = 'Grace Villanueva'

from django.conf.urls import url
from .import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^importsuppliers/$', views.importsuppliers, name='importsuppliers'),
    url(r'^importitems/$', views.importitems, name='importitems'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    url(r'^savedetailtemp/$', views.savedetailtemp, name='savedetailtemp'),
    url(r'^deletedetailtemp/$', views.deletedetailtemp, name='deletedetailtemp'),
    url(r'^page/(?P<command>[\w\-]+)/(?P<current>[0-9]+)/(?P<limit>[0-9]+)/(?P<search>[\w\-]+)/$', views.paginate,
        name='paginate'),
]

