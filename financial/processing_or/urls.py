from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^fileupload/$', views.fileupload, name='fileupload'),
    url(r'^storeupload/$', views.storeupload, name='storeupload'),
    url(r'^exportsave/$', views.exportsave, name='exportsave'),
]
