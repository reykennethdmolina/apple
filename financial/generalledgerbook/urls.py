from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    # url(r'^reportresult/$', views.ReportResultView.as_view(), name='reportresult'),
    # url(r'^reportresultxlsx/$', views.reportresultxlsx, name='reportresultxlsx'),
    url(r'^reportresulthtml/$', views.ReportResultHtmlView.as_view(), name='reportresulthtml'),
]
