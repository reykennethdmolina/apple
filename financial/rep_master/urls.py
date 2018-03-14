from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^bank$', views.BankList.as_view(), name='bank'),
    url(r'^bankbranch$', views.BankBranchList.as_view(), name='bankbranch'),
    url(r'^bankaccount$', views.BankAccountList.as_view(), name='bankaccount'),
]
