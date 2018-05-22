# author = 'grace'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.ReportView.as_view(), name='report'),
    url(r'^reportresultpdf/$', views.ReportResultPdfView.as_view(), name='reportresultpdf'),
    url(r'^cashinbankpdf/$', views.CashInBankPdfView.as_view(), name='cashinbankpdf'),
    # url(r'^reportresultxlsx/$', views.reportresultxlsx, name='reportresultxlsx'),
]
