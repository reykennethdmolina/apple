# author = 'jek'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateView.as_view(), name='update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    url(r'^report/$', views.ReportView.as_view(), name='report'),
    url(r'^pdf2/$', views.GeneratePDF.as_view(), name='pdf2'),
    url(r'^pdf2cashinbank/$', views.GeneratePDFCashInBank.as_view(), name='pdf2cashinbank'),
    url(r'^pdf2department/$', views.GeneratePDFDepartment.as_view(), name='pdf2department'),
    url(r'^excel/$', views.GenerateExcel.as_view(), name='excel2'),
    url(r'^(?P<pk>[0-9]+)/pdf/$', views.Pdf.as_view(), name='pdf'),
    url(r'^generatedefaultentries/$', views.generatedefaultentries, name='generatedefaultentries'),
    url(r'^searchforposting/$', views.searchforposting, name='searchforposting'),
    url(r'^searchforapproval/$', views.searchforapproval, name='searchforapproval'),
    url(r'^searchforpostingJV/$', views.searchforpostingJV, name='searchforpostingJV'),
    url(r'^gopostjv/$', views.gopostjv, name='gopostjv'),
    url(r'^getcustomercreditterm/$', views.getcustomercreditterm, name='getcustomercreditterm'),
    url(r'^gopost/$', views.gopost, name='gopost'),
    url(r'^goapprove/$', views.goapprove, name='goapprove'),
    url(r'^gounpost/$', views.gounpost, name='gounpost'),
    url(r'^approve/$', views.approve, name='approve'),
    url(r'^disapprove/$', views.disapprove, name='disapprove'),
    url(r'^posting/$', views.posting, name='posting'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^filedelete/$', views.filedelete, name='filedelete'),
    url(r'^tagging/$', views.TaggingIndexView.as_view(), name='tagging'),
    url(r'^transgenerate/$', views.transgenerate, name='transgenerate'),
]