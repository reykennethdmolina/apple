# author = 'grace'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^reportresult/$', views.ReportResultView.as_view(), name='reportresult'),
]
