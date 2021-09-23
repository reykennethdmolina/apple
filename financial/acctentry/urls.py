#__author__ = 'reykennethmolina'

from django.conf.urls import url
from . import views

urlpatterns = [
    #url(r'^$', views.accountingentry, name='accountingentry'),
    url(r'^maccountingentry/$', views.maccountingentry, name='maccountingentry'),
    url(r'^checkchartvalidation/$', views.checkchartvalidation, name='checkchartvalidation'),
    url(r'^savemaccountingentry/$', views.savemaccountingentry, name='savemaccountingentry'),
    url(r'^validateDepartment/$', views.validateDepartment, name='validateDepartment'),
    url(r'^breakdownentry/$', views.breakdownentry, name='breakdownentry'),
    url(r'^savemaccountingentrybreakdown/$', views.savemaccountingentrybreakdown, name='savemaccountingentrybreakdown'),
    url(r'^deletedetailbreakdown/$', views.deletedetailbreakdown, name='deletedetailbreakdown'),
    url(r'^deletedetail/$', views.deletedetail, name='deletedetail'),
    url(r'^updatebreakentry/$', views.updatebreakentry, name='updatebreakentry'),
    url(r'^saveupdatedetailbreakdown/$', views.saveupdatedetailbreakdown, name='saveupdatedetailbreakdown'),
    url(r'^updateentry/$', views.updateentry, name='updateentry'),
    url(r'^saveupdatemaccountingentry/$', views.saveupdatemaccountingentry, name='saveupdatemaccountingentry'),
    url(r'^updatebreakdownstatus/$', views.updatebreakdownstatus, name='updatebreakdownstatus'),
    # url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # url(r'^create/$', views.CreateView.as_view(), name='create'),
    # url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateView.as_view(), name='update'),
    # url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
]