#__author__ = 'reykennethmolina'

from django.conf.urls import url
from . import views

urlpatterns = [
    #url(r'^$', views.accountingentry, name='accountingentry'),
    url(r'^maccountingentry/$', views.maccountingentry, name='maccountingentry'),
    url(r'^checkchartvalidation/$', views.checkchartvalidation, name='checkchartvalidation'),
    url(r'^savemaccountingentry/$', views.savemaccountingentry, name='savemaccountingentry'),
    url(r'^breakdownentry/$', views.breakdownentry, name='breakdownentry'),
    url(r'^savemaccountingentrybreakdown/$', views.savemaccountingentrybreakdown, name='savemaccountingentrybreakdown'),
    url(r'^deletedetailbreakdown/$', views.deletedetailbreakdown, name='deletedetailbreakdown'),
    # url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # url(r'^create/$', views.CreateView.as_view(), name='create'),
    # url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateView.as_view(), name='update'),
    # url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
]