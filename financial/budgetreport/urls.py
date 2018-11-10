# author = 'bossing'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='report'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    #url(r'^excel/$', views.GenerateExcel.as_view(), name='excel'),
]
