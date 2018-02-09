# __author__ = 'Grace Villanueva'

from django.conf.urls import url
from .import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^prf$', views.PrfApprovalView.as_view(), name='prf'),
    url(r'^prf/userresponse$', views.userprfResponse, name='userprfreponse'),
    url(r'^approve/$', views.approve, name='approve'),
]

