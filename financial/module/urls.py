#__author__ = 'kelvin'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateView.as_view(), name='update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    url(r'^pdf/user/$', views.GeneratePDFUser.as_view(), name='pdf_user'),
    url(r'^pdf/useraccess/$', views.GeneratePDFUserAccess.as_view(), name='pdf_useraccess'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^pdf/logs/$', views.GeneratePDFLogs.as_view(), name='pdf_logs'),
    url(r'^excel/logs/$', views.GenerateExcelLogs.as_view(), name='excel_logs'),
    url(r'^pdf/moduleaccess/$', views.GeneratePDFModuleAccess.as_view(), name='pdf_moduleaccess'),
    url(r'^pdf/group/$', views.GeneratePDFGroup.as_view(), name='pdf_group'),
    url(r'^pdf/groupaccess/$', views.GeneratePDFGroupAccess.as_view(), name='pdf_groupaccess'),
    url(r'^pdf/usergroup/$', views.GeneratePDFUserGroup.as_view(), name='pdf_usergroup'),
]
