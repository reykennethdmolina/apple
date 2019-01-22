# __author__ = 'Grace Villanueva'

from django.conf.urls import url
from .import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^usercreate/$', views.CreateViewUser.as_view(), name='usercreate'),
    url(r'^cashiercreate/$', views.CreateViewCashier.as_view(), name='cashiercreate'),
    url(r'^(?P<pk>[0-9]+)/userupdate/$', views.UpdateViewUser.as_view(), name='userupdate'),
    url(r'^(?P<pk>[0-9]+)/cashierupdate/$', views.UpdateViewCashier.as_view(), name='cashierupdate'),
    url(r'^saveitemtemp/$', views.saveitemtemp, name='saveitemtemp'),
    url(r'^deleteitemtemp/$', views.deleteitemtemp, name='deleteitemtemp'),
    url(r'^updateitemtemp/$', views.updateitemtemp, name='updateitemtemp'),
    url(r'^autoentry/$', views.autoentry, name='autoentry'),
    url(r'^approve/$', views.approve, name='approve'),
    url(r'^releaseof/$', views.releaseof, name='releaseof'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    url(r'^(?P<pk>[0-9]+)/userpdf/$', views.UserPdf.as_view(), name='userpdf'),
    url(r'^(?P<pk>[0-9]+)/cashierpdf/$', views.CashierPdf.as_view(), name='cashierpdf'),

    url(r'^report/$', views.ReportView.as_view(), name='report'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),

    # url(r'^report/$', views.ReportView.as_view(), name='report'),
    # url(r'^reportresult/$', views.ReportResultView.as_view(), name='reportresult'),
    # url(r'^reportresultxlsx/$', views.reportresultxlsx, name='reportresultxlsx'),
    # url(r'^reportresulthtml/$', views.ReportResultHtmlView.as_view(), name='reportresulthtml'),

    url(r'^searchforposting/$', views.searchforposting, name='searchforposting'),
    url(r'^searchforpostingReim/$', views.searchforpostingReim, name='searchforpostingReim'),
    url(r'^searchforpostingLiq/$', views.searchforpostingLiq, name='searchforpostingLiq'),
    url(r'^gopost/$', views.gopost, name='gopost'),
    url(r'^gopostreim/$', views.gopostreim, name='gopostreim'),
    url(r'^gopostliq/$', views.gopostliq, name='gopostliq'),
]
