# author = 'grace'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.ReportView.as_view(), name='report'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^pdfcashinbank/$', views.GeneratePDFCashInBank.as_view(), name='pdfcashinbank'),
    url(r'^pdfdepartment/$', views.GeneratePDFDepartment.as_view(), name='pdfdepartment'),
    url(r'^excel/$', views.GenerateExcel.as_view(), name='excel'),
    #url(r'^reportresultpdf/$', views.ReportResultPdfView.as_view(), name='reportresultpdf'),
    #url(r'^cashinbankpdf/$', views.CashInBankPdfView.as_view(), name='cashinbankpdf'),
    # url(r'^reportresultxlsx/$', views.reportresultxlsx, name='reportresultxlsx'),
]
