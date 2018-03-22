from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^birpurchasebook$', views.BirPurchaseBook.as_view(), name='birpurchasebook'),
    url(r'^birgeneraljournalbook$', views.BirGeneralJournalBook.as_view(), name='birgeneraljournalbook'),
]
