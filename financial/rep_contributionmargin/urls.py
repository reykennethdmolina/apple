# author = 'acorales'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^generate/$', views.generate, name='generate'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^excel/$', views.GenerateExcel.as_view(), name='excel'),
    # url(r'^excel/$', views.GenerateExcel.as_view(), name='excel'),
]
