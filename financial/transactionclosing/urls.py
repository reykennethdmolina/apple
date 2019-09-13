# author__ = 'grace'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^proc_validate/$', views.proc_validate, name='proc_validate'),
    url(r'^proc_provision/$', views.proc_provision, name='proc_provision'),
    #url(r'^proc_retainedearnings/$', views.proc_retainedearnings, name='proc_retainedearnings'),
    url(r'^proc_currentearnings/$', views.proc_currentearnings, name='proc_currentearnings'),
    url(r'^proc_generalledgersummary/$', views.proc_generalledgersummary, name='proc_generalledgersummary'),
    url(r'^proc_zeroout/$', views.proc_zeroout, name='proc_zeroout'),
    url(r'^proc_updateclosing/$', views.proc_updateclosing, name='proc_updateclosing'),
    url(r'^yearend_init/$', views.yearend_init, name='yearend_init'),
    url(r'^yearend_adjustment/$', views.YearEndAdjustmentView.as_view(), name='yearend_adjustment'),
    url(r'^proc_yearendadjustment/$', views.proc_yearendadjustment, name='proc_yearendadjustment'),
]

