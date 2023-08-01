#__author__ = 'ken'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^transgenerate/$', views.transgenerate, name='transgenerate',),
    url(r'^ajaxbankaccount/$', views.ajaxbankaccount, name='ajaxbankaccount'),
    url(r'^ajaxbankinfo/$', views.ajaxbankinfo, name='ajaxbankinfo'),
    url(r'^importguide/$', views.importguide, name='importguide'),
    # url(r'^tagging/$', views.tagging, name='tagging'),
    url(r'^fxsave/$', views.fxsave, name='fxsave'),
    url(r'^reportxls/$', views.reportxls, name='reportxls'),
    url(r'^manualentry/$', views.ManualEntryView.as_view(), name='manualentry'),
    url(r'^savemanualentry/$', views.savemanualentry, name='savemanualentry'),
    url(r'^savebatchpostingbook/$', views.savebatchpostingbook, name='savebatchpostingbook'),
    url(r'^savebatchpostingbank/$', views.savebatchpostingbank, name='savebatchpostingbank'),
    url(r'^delete_upload/$', views.delete_upload, name='delete_upload'),
]
