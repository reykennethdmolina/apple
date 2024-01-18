# __author__ = 'Jek'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    # url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^upload/$', views.upload, name='upload'),
    # url(r'^retrieve/$', views.retrieve, name='retrieve'),
    url(r'^save_batch_tagging/$', views.save_batch_tagging, name='save_batch_tagging'),
    url(r'^tag_as_pending/$', views.tag_as_pending, name='tag_as_pending'),
    url(r'^tag_as_no_payment/$', views.tag_as_no_payment, name='tag_as_no_payment'),
    url(r'^get_supplier_by_type/$', views.get_supplier_by_type, name='get_supplier_by_type'),
    url(r'^get_supplier_by_code/$', views.get_supplier_by_code, name='get_supplier_by_code'),
    url(r'^get_supplier_by_name/$', views.get_supplier_by_name, name='get_supplier_by_name'),
    url(r'^supplier_suggestion/$', views.supplier_suggestion, name='supplier_suggestion'),
    url(r'^save_transaction_entry/$', views.save_transaction_entry, name='save_transaction_entry'),
    url(r'^manual_save_transaction_entry/$', views.manual_save_transaction_entry, name='manual_save_transaction_entry'),
    url(r'^get_confirmation/$', views.get_confirmation, name='get_confirmation'),
    url(r'^process_transaction/$', views.ProcessTransactionView.as_view(), name='process_transaction'),
    url(r'^generate_process_transaction/$', views.GenerateProcessTransaction.as_view(), name='generate_process_transaction'),
    url(r'^transaction_posting/$', views.transaction_posting, name='transaction_posting'),
    url(r'^confirmation_sheet/print/$', views.print_cs, name='print_cs'),
    url(r'^report/$', views.ReportView.as_view(), name='report'),
    url(r'^pdf/$', views.GeneratePDF.as_view(), name='pdf'),
    url(r'^goposttriplec/$', views.goposttriplec, name='goposttriplec'),
    url(r'^revert_transaction/$', views.revert_transaction, name='revert_transaction'),
    url(r'^having_quota/$', views.having_quota, name='having_quota'),
    url(r'^generic_retrieve/$', views.RetrieveView.as_view(), name='generic_retrieve'),
    url(r'^get_ap_id/$', views.get_ap_id, name='get_ap_id'),

    # quota
    url(r'^quota/$', views.QuotaView.as_view(), name='quota'),
    url(r'^quota/(?P<pk>[0-9]+)/$', views.QuotaDetailView.as_view(), name='quota_detail'),
    url(r'^quota/(?P<pk>[0-9]+)/update/$', views.QuotaUpdateView.as_view(), name='quota_update'),

    # cs printing 
    url(r'^confirmation_sheet/batchprint/$', views.BatchPrintCsView.as_view(), name='batchprint_cs'),
    url(r'^confirmation_sheet/retrieve/$', views.retrieve_cs, name='retrieve_cs'),
    url(r'^confirmation_sheet/batchprint/a/$', views.startprint, name='startprint'),
]