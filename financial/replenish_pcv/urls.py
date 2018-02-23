#__author__ = 'Grace Ann Villanueva'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    # url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^replenish/$', views.replenish, name='replenish'),
    url(r'^fetch_details/$', views.fetch_details, name='fetch_details'),
    url(r'^(?P<pk>[0-9]+)/pdf/$', views.Pdf.as_view(), name='pdf'),
    url(r'^report/$', views.ReportView.as_view(), name='report'),
    url(r'^reportresult/$', views.ReportResultView.as_view(), name='reportresult'),
    url(r'^reportresultxlsx/$', views.reportresultxlsx, name='reportresultxlsx'),
    # url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateView.as_view(), name='update'),
    # url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    url(r'^approval$', views.ApprovalView.as_view(), name='approval'),
    url(r'^approval/userresponse$', views.userpcvResponse, name='userpcvreponse'),
]
