from django.conf.urls import url
from .import views

urlpatterns = [
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    # url(r'^savedetailtemp/$', views.savedetailtemp, name='savedetailtemp'),
    # url(r'^deletedetailtemp/$', views.deletedetailtemp, name='deletedetailtemp'),
]

