from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexList.as_view(), name='index'),
    url(r'^bank$', views.BankList.as_view(), name='bank'),
    url(r'^bankbranch$', views.BankBranchList.as_view(), name='bankbranch'),
    url(r'^bankaccount$', views.BankAccountList.as_view(), name='bankaccount'),
    url(r'^product$', views.ProductList.as_view(), name='product'),
    url(r'^mainproduct$', views.MainProductList.as_view(), name='mainproduct'),
    url(r'^branch$', views.BranchList.as_view(), name='branch'),
    url(r'^ataxcode$', views.AtaxCodeList.as_view(), name='ataxcode'),
    url(r'^vat$', views.VatList.as_view(), name='vat'),
    url(r'^inputvat$', views.InputVatList.as_view(), name='inputvat'),
    url(r'^collectorcashier$', views.CollectorCashierList.as_view(), name='collectorcashier'),
    url(r'^employee$', views.EmployeeList.as_view(), name='employee'),
    url(r'^productbudget$', views.ProductBudgetList.as_view(), name='productbudget'),
]
