from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^generaljournalbook$', views.GeneralJournalBookView.as_view(), name='generaljournalbook'),
    url(r'^cashreceiptsbook', views.CashReceiptsBookView.as_view(), name='cashreceiptsbook'),
    url(r'^cashdisbursementbook', views.CashDisbursementBook.as_view(), name='cashdisbursementbook'),
]
