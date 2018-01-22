from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^truncatedir/(?P<path>\w{0,50})/$', views.truncateDir, name='truncatedir'),
]
