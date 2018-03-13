from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^birpurchasebook$', views.BirPurchaseBook.as_view(), name='birpurchasebook'),
]
