"""financial URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import login, logout

admin.site.index_template = 'admin/index.html'
admin.autodiscover()

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^index2/', views.index2, name='index2'),
    url(r'^admin/', admin.site.urls),

    # Apps URLS
    url(r'^mainproduct/', include('mainproduct.urls', namespace='mainproduct')),
    url(r'^product/', include('product.urls', namespace='product')),
    url(r'^adtype/', include('adtype.urls', namespace='adtype')),
    url(r'^journalvoucher/', include('journalvoucher.urls', namespace='journalvoucher')),

    # Apps Grace
    url(r'^vat/', include('vat.urls', namespace='vat')),
    url(r'^wtax/', include('wtax.urls', namespace='wtax')),
    url(r'^mainunit/', include('mainunit.urls', namespace='mainunit')),
    url(r'^unit/', include('unit.urls', namespace='unit')),
    url(r'^typeofexpense/', include('typeofexpense.urls', namespace='typeofexpense')),
    url(r'^currency/', include('currency.urls', namespace='currency')),
    url(r'^industry/', include('industry.urls', namespace='industry')),
    url(r'^bankaccounttype/', include('bankaccounttype.urls', namespace='bankaccounttype')),
    url(r'^cvtype/', include('cvtype.urls', namespace='cvtype')),
    url(r'^aptype/', include('aptype.urls', namespace='aptype')),
    url(r'^bankaccount/', include('bankaccount.urls', namespace='bankaccount')),
    url(r'^customertype/', include('customertype.urls', namespace='customertype')),
    url(r'^creditterm/', include('creditterm.urls', namespace='creditterm')),
    url(r'^customer/', include('customer.urls', namespace='customer')),
    url(r'^mainsupplier/', include('mainsupplier.urls', namespace='mainsupplier')),
    url(r'^collector/', include('collector.urls', namespace='collector')),
    url(r'^maininventory/', include('maininventory.urls', namespace='maininventory')),
    url(r'^serviceinformation/', include('serviceinformation.urls', namespace='serviceinformation')),
    url(r'^outputvat/', include('outputvat.urls', namespace='outputvat')),
    url(r'^supplier/', include('supplier.urls', namespace='supplier')),
    url(r'^mainsupplier_supplier/', include('mainsupplier_supplier.urls', namespace='mainsupplier_supplier')),
    url(r'^companyparameter/', include('companyparameter.urls', namespace='companyparameter')),
    url(r'^employee/', include('employee.urls', namespace='employee')),

    # Apps Kelvin
    url(r'^ataxcode/', include('ataxcode.urls', namespace='ataxcode')),
    url(r'^inputvat/', include('inputvat.urls', namespace='inputvat')),
    url(r'^inputvattype/', include('inputvattype.urls', namespace='inputvattype')),
    url(r'^kindofexpense/', include('kindofexpense.urls', namespace='kindofexpense')),
    url(r'^mistype/', include('mistype.urls', namespace='mistype')),
    url(r'^bank/', include('bank.urls', namespace='bank')),
    url(r'^bankbranch/', include('bankbranch.urls', namespace='bankbranch')),
    url(r'^branch/', include('branch.urls', namespace='branch')),
    url(r'^mainmodule/', include('mainmodule.urls', namespace='mainmodule')),
    url(r'^module/', include('module.urls', namespace='module')),
    url(r'^chartofaccount/', include('chartofaccount.urls', namespace='chartofaccount')),
    url(r'^ofsubtype/', include('ofsubtype.urls', namespace='ofsubtype')),
    url(r'^oftype/', include('oftype.urls', namespace='oftype')),
    url(r'^ortype/', include('ortype.urls', namespace='ortype')),
    url(r'^paytype/', include('paytype.urls', namespace='paytype')),
    url(r'^potype/', include('potype.urls', namespace='potype')),
    url(r'^serviceclassification/', include('serviceclassification.urls', namespace='serviceclassification')),
    url(r'^productgroup/', include('productgroup.urls', namespace='productgroup')),
    url(r'^unitofmeasure/', include('unitofmeasure.urls', namespace='unitofmeasure')),
    url(r'^suppliertype/', include('suppliertype.urls', namespace='suppliertype')),
    url(r'^advertisingcategory/', include('advertisingcategory.urls', namespace='advertisingcategory')),
    url(r'^artype/', include('artype.urls', namespace='artype')),
    url(r'^fxtype/', include('fxtype.urls', namespace='fxtype')),
    url(r'^companyproduct/', include('companyproduct.urls', namespace='companyproduct')),
    url(r'^circulationproduct/', include('circulationproduct.urls', namespace='circulationproduct')),
    url(r'^circulationcategory/', include('circulationcategory.urls', namespace='circulationcategory')),
    url(r'^maingroupproduct/', include('maingroupproduct.urls', namespace='maingroupproduct')),
    url(r'^mrstype/', include('mrstype.urls', namespace='mrstype')),
    url(r'^company/', include('company.urls', namespace='company')),
    url(r'^productbudget/', include('productbudget.urls', namespace='productbudget')),
    url(r'^department/', include('department.urls', namespace='department')),
    url(r'^jvtype/', include('jvtype.urls', namespace='jvtype')),
    url(r'^departmentbudget/', include('departmentbudget.urls', namespace='departmentbudget')),

    # Login/Logout URLs
    url(r'^login/$', login, {'template_name': 'login.html'}),
    url(r'^logout/$', logout, {'next_page': '/login/'})
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
