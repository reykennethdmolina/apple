# author = 'grace'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateView.as_view(), name='update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    url(r'^(?P<pk>[0-9]+)/pdf/$', views.Pdf.as_view(), name='pdf'),
    url(r'^(?P<pk>[0-9]+)/voucher/$', views.Voucher.as_view(), name='voucher'),
    url(r'^(?P<pk>[0-9]+)/preprintedvoucher/$', views.PrePrintedVoucher.as_view(), name='preprintedvoucher'),
    url(r'^approve/$', views.approve, name='approve'),
    url(r'^disapprove/$', views.disapprove, name='disapprove'),
    url(r'^release/$', views.release, name='release'),
    url(r'^importreppcv/$', views.importreppcv, name='importreppcv'),
    url(r'^manualcvautoentry/$', views.manualcvautoentry, name='manualcvautoentry'),
    url(r'^report/$', views.ReportView.as_view(), name='report'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^excel/$', views.GenerateExcel.as_view(), name='excel'),
    url(r'^searchforposting/$', views.searchforposting, name='searchforposting'),
    url(r'^gopost/$', views.gopost, name='gopost'),
    url(r'^gounpost/$', views.gounpost, name='gounpost'),
]
