# author = 'bossing'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='report'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^excel/$', views.GenerateExcel.as_view(), name='excel'),
    url(r'^deptbud/$', views.DeptBudgetInquiry.as_view(), name='deptbudinq'),
    url(r'^transgenerate/$', views.transgenerate, name='transgenerate'),
    url(r'^transexcel/$', views.GenerateTransExcel.as_view(), name='transexcel'),
    url(r'^generate/$', views.generate, name='generate'),
    #url(r'^excel/$', views.GenerateExcel.as_view(), name='excel'),
]
