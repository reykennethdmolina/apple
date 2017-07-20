# __author__ = 'Grace Villanueva'

from django.conf.urls import url
from .import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    # url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^usercreate/$', views.CreateViewUser.as_view(), name='usercreate'),
    url(r'^cashiercreate/$', views.CreateViewCashier.as_view(), name='cashiercreate'),
    url(r'^(?P<pk>[0-9]+)/userupdate/$', views.UpdateViewUser.as_view(), name='userupdate'),
    url(r'^(?P<pk>[0-9]+)/cashierupdate/$', views.UpdateViewCashier.as_view(), name='cashierupdate'),
    url(r'^approve/$', views.approve, name='approve'),
    url(r'^getsupplierdata/$', views.getsupplierdata, name='getsupplierdata'),
    url(r'^releaseof/$', views.releaseof, name='releaseof'),
    # url(r'^(?P<pk>[0-9]+)/delete/$', views.DeleteView.as_view(), name='delete'),
    # url(r'^(?P<pk>[0-9]+)/pdf/$', views.Pdf.as_view(), name='pdf'),
    # url(r'^savedetailtemp/$', views.savedetailtemp, name='savedetailtemp'),
    # url(r'^deletedetailtemp/$', views.deletedetailtemp, name='deletedetailtemp'),
    # url(r'^page/(?P<command>[\w\-]+)/(?P<current>[0-9]+)/(?P<limit>[0-9]+)/(?P<search>[\w\-]+)/$', views.paginate,
    #     name='paginate'),
]