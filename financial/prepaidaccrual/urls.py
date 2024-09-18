
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^transgenerate/$', views.transgenerate, name='transgenerate'),
    url(r'^importprepaidschedule/$', views.ImportPrepaidScheduleView.as_view(), name='importprepaidschedule'),
    url(r'^transexcel/$', views.TransExcel.as_view(), name='transexcel'),
    # url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^prepaidentry/$', views.PrepaidEntryIndexView.as_view(), name='prepaidentry'),
    url(r'^prepaidgenerate/$', views.prepaidgenerate, name='prepaidgenerate'),
    url(r'^getprepaiddata/$', views.getprepaiddata, name='getprepaiddata'),
    url(r'^saveprepaiddata/$', views.saveprepaiddata, name='saveprepaiddata'),
    url(r'^importprepaiddata/$', views.importprepaiddata, name='importprepaiddata'),
    url(r'^editamount/$', views.editamount, name='editamount'),
    url(r'^gopostprepaid/$', views.gopostprepaid, name='gopostprepaid'),
    url(r'^tagaccruedexpense/$', views.tagaccruedexpense, name='tagaccruedexpense'),
    url(r'^manage/accruedexpense/$', views.ManageAccruedExpenseView.as_view(), name='manageaccruedexpenseview'),
    url(r'^manageaccruedexpense/$', views.manageaccruedexpense, name='manageaccruedexpense'),
    url(r'^untagaccruedexpense/$', views.untagaccruedexpense, name='untagaccruedexpense'),
]