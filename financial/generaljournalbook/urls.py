from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^excel/$', views.GenerateExcel.as_view(), name='excel'),
    url(r'^transaction/$', views.TransactionView.as_view(), name='transaction'),
    url(r'^transgenerate/$', views.transgenerate, name='transgenerate'),
    url(r'^transexcel/$', views.TransExcel.as_view(), name='transexcel'),
]
