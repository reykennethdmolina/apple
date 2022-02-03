# __author__ = 'Grace Villanueva'

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.UpdateView.as_view(), name='update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    url(r'^get_branch/$', views.get_branch, name='get_branch'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^pdf2/$', views.GeneratePDF2.as_view(), name='pdf2'),
    url(r'^inquiry/$', views.InquiryView.as_view(), name='inquiry'),
    url(r'^transgenerate/$', views.transgenerate, name='transgenerate'),
    url(r'^transexcel/$', views.GenerateTransExcel.as_view(), name='transexcel'),
    url(r'^summarytranspdf/$', views.GenerateSummaryTransPDF.as_view(), name='summarytranspdf'),
    url(r'^summarytransexcel/$', views.GenerateSummaryTransExcel.as_view(), name='summarytransexcel')
]
