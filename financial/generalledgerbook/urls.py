from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    # url(r'^reportresult/$', views.ReportResultView.as_view(), name='reportresult'),
    # url(r'^reportresultxlsx/$', views.reportresultxlsx, name='reportresultxlsx'),
    # url(r'^reportresulthtml/$', views.ReportResultHtmlView.as_view(), name='reportresulthtml'),
    #url(r'^cashinbankpdf/$', views.CashInBankPdfView.as_view(), name='cashinbankpdf'),
    url(r'^generate/$', views.generate, name='generate'),
    #url(r'^pdf/$', views.pdf, name='pdf'),
    url(r'^excel/$', views.excel, name='excel'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    # url(r'^reportresult/$', views.ReportResultView.as_view, name='reportresult'),
]
