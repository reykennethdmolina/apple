# __author__ = 'Grace Villanueva'

from django.conf.urls import url
from .import views

urlpatterns = [
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^saverfdetailtemp/$', views.saverfdetailtemp, name='saverfdetailtemp'),
    url(r'^deleterfdetailtemp/$', views.deleterfdetailtemp, name='deleterfdetailtemp'),
]

