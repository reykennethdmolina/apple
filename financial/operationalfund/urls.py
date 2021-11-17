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
    url(r'^hrapprove/$', views.hrapprove, name='hrapprove'),
    url(r'^hrapprove1/$', views.hrapprove1, name='hrapprove1'),
    url(r'^hrapprove2/$', views.hrapprove2, name='hrapprove2'),
    url(r'^nurseapprove/$', views.nurseapprove, name='nurseapprove'),
    url(r'^releaseof/$', views.releaseof, name='releaseof'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    url(r'^(?P<pk>[0-9]+)/userpdf/$', views.UserPdf.as_view(), name='userpdf'),
    url(r'^(?P<pk>[0-9]+)/cashierpdf/$', views.CashierPdf.as_view(), name='cashierpdf'),

    url(r'^report/$', views.ReportView.as_view(), name='report'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^excel/$', views.GenerateExcel.as_view(), name='excel'),

    # url(r'^report/$', views.ReportView.as_view(), name='report'),
    # url(r'^reportresult/$', views.ReportResultView.as_view(), name='reportresult'),
    # url(r'^reportresultxlsx/$', views.reportresultxlsx, name='reportresultxlsx'),
    # url(r'^reportresulthtml/$', views.ReportResultHtmlView.as_view(), name='reportresulthtml'),

    #url(r'^sendNotif/$', views.sendNotif, name='sendNotif'),

    url(r'^searchforposting/$', views.searchforposting, name='searchforposting'),
    url(r'^searchforpostingReim/$', views.searchforpostingReim, name='searchforpostingReim'),
    url(r'^searchforpostingRev/$', views.searchforpostingRev, name='searchforpostingRev'),
    url(r'^searchforpostingLiq/$', views.searchforpostingLiq, name='searchforpostingLiq'),
    url(r'^searchforpostingEye/$', views.searchforpostingEye, name='searchforpostingEye'),
    url(r'^searchforpostingAntibiotic/$', views.searchforpostingAntibiotic, name='searchforpostingAntibiotic'),
    url(r'^gopost/$', views.gopost, name='gopost'),
    url(r'^gopostreim/$', views.gopostreim, name='gopostreim'),
    url(r'^gopostrev/$', views.gopostrev, name='gopostrev'),
    url(r'^gopostliq/$', views.gopostliq, name='gopostliq'),
    url(r'^goposteye/$', views.goposteye, name='goposteye'),
    url(r'^gopostanti/$', views.gopostanti, name='gopostanti'),

    url(r'^upload/$', views.upload, name='upload'),
    url(r'^uploadhere/$', views.uploadhere, name='uploadhere'),
    url(r'^filedelete/$', views.filedelete, name='filedelete'),
]
