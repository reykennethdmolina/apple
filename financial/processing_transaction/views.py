from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from annoying.functions import get_object_or_None
import datetime
from datetime import timedelta
from django.utils.crypto import get_random_string
from utils.views import wccount, storeupload
import decimal
from dbfread import DBF

from purchaseorder.models import Pomain
from accountspayable.models import Apmain
from checkvoucher.models import Cvmain
from branch.models import Branch
from aptype.models import Aptype
from apsubtype.models import Apsubtype
from supplier.models import Supplier
from cvtype.models import Cvtype
from cvsubtype.models import Cvsubtype
from . models import Poapvtransaction, Apvcvtransaction


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'processing_transaction/index.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if self.request.GET:
            if self.request.GET['selectprocess'] == 'potoapv':
                context['data_list'] = Pomain.objects.all().filter(isdeleted=0, postatus='A', isfullyapv=0).\
                    order_by('supplier_name', 'inputvattype_id', 'vat_id')
                if self.request.GET['datefrom']:
                    context['data_list'] = context['data_list'].filter(podate__gte=self.request.GET['datefrom'])
                if self.request.GET['dateto']:
                    context['data_list'] = context['data_list'].filter(podate__lte=self.request.GET['dateto'])
            elif self.request.GET['selectprocess'] == 'apvtocv':
                context['data_list'] = Apmain.objects.all().filter(isdeleted=0, apstatus='R', isfullycv=0). \
                    order_by('payeecode', 'inputvattype_id', 'vat_id')
                if self.request.GET['datefrom']:
                    context['data_list'] = context['data_list'].filter(apdate__gte=self.request.GET['datefrom'])
                if self.request.GET['dateto']:
                    context['data_list'] = context['data_list'].filter(apdate__lte=self.request.GET['dateto'])

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        if self.request.GET:
            context['selectprocess'] = self.request.GET['selectprocess']
            context['datefrom'] = self.request.GET['datefrom']
            context['dateto'] = self.request.GET['dateto']

        return context


@csrf_exempt
def importtransdata(request):
    if request.method == 'POST':
        if request.POST['transtype'] == 'potoapv':
            referencepo = Pomain.objects.get(pk=int(request.POST.getlist('trans_checkbox')[0]))
            allpos = Pomain.objects.filter(id__in=request.POST.getlist('trans_checkbox')).order_by('ponum')

            po_nums = allpos.values_list('ponum', flat=True)
            refnum = ' '.join(po_nums)

            year = str(datetime.date.today().year)
            yearqs = Apmain.objects.filter(apnum__startswith=year)

            if yearqs:
                apnumlast = yearqs.latest('apnum')
                latestapnum = str(apnumlast)
                print "latest: " + latestapnum

                apnum = year
                last = str(int(latestapnum[4:]) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    apnum += '0'
                apnum += last
            else:
                apnum = year + '000001'
            print 'apnum: ' + apnum

            newapv = Apmain()
            newapv.aptype = Aptype.objects.get(description='PO')
            newapv.apsubtype = Apsubtype.objects.get(code='IPO')
            newapv.apnum = apnum
            newapv.apprefix = 'AP'
            newapv.apdate = datetime.date.today()
            newapv.apstatus = 'F'
            newapv.payee_id = referencepo.supplier.id
            newapv.payeecode = referencepo.supplier.code
            newapv.vat = referencepo.vat
            newapv.vatcode = referencepo.vat.code
            newapv.vatrate = referencepo.vatrate
            newapv.atax = referencepo.atc
            newapv.ataxcode = referencepo.atc.code
            newapv.ataxrate = referencepo.atcrate
            newapv.refno = refnum
            newapv.particulars = 'Purchase Order No.(s) ' + refnum
            newapv.deferred = referencepo.deferredvat
            newapv.currency = referencepo.currency
            newapv.fxrate = referencepo.fxrate
            newapv.branch = Branch.objects.get(code='HO')
            newapv.inputvattype = referencepo.inputvattype
            newapv.creditterm = referencepo.creditterm
            newapv.duedate = datetime.datetime.now().date() + datetime.timedelta(days=newapv.creditterm.daysdue)
            newapv.enterby = request.user
            newapv.modifyby = request.user
            newapv.save()

            total_amount = 0
            i = 0
            for data in allpos:
                newpoapvtrans = Poapvtransaction()
                newpoapvtrans.apamount = float(request.POST.getlist('temp_actualamount')[i].replace(',', ''))
                newpoapvtrans.apmain = newapv
                newpoapvtrans.pomain = data
                total_amount += newpoapvtrans.apamount
                newpoapvtrans.save()
                updatepo = Pomain.objects.get(pk=newpoapvtrans.pomain.id)
                updatepo.apvamount = newpoapvtrans.apamount
                if updatepo.apvamount == updatepo.totalamount:
                    updatepo.isfullyapv = 1
                updatepo.save()
                i += 1

            newapv.amount = total_amount
            newapv.save()

            print "APV successfully generated."
        elif request.POST['transtype'] == 'apvtocv':
            referenceap = Apmain.objects.get(pk=int(request.POST.getlist('trans_checkbox')[0]))
            allaps = Apmain.objects.filter(id__in=request.POST.getlist('trans_checkbox')).order_by('apnum')

            ap_nums = allaps.values_list('apnum', flat=True)
            cvrefnum = ' '.join(ap_nums)

            year = str(datetime.date.today().year)
            yearqs = Cvmain.objects.filter(cvnum__startswith=year)

            if yearqs:
                cvnumlast = yearqs.latest('cvnum')
                latestcvnum = str(cvnumlast)
                print "latest: " + latestcvnum

                cvnum = year
                last = str(int(latestcvnum[4:]) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    cvnum += '0'
                cvnum += last
            else:
                cvnum = year + '000001'
            print 'cvnum: ' + cvnum

            newcv = Cvmain()
            newcv.cvtype = Cvtype.objects.get(description='AP')
            newcv.cvsubtype = Cvsubtype.objects.get(code='IAP')
            newcv.cvnum = cvnum
            newcv.cvdate = datetime.date.today()
            newcv.cvstatus = 'F'
            newcv.payee = Supplier.objects.get(pk=referenceap.payee_id)
            newcv.payee_code = newcv.payee.code
            newcv.payee_name = newcv.payee.name
            newcv.checknum = cvnum
            newcv.checkdate = datetime.date.today()
            newcv.vat = referenceap.vat
            newcv.vatrate = referenceap.vatrate
            newcv.atc = referenceap.atax
            newcv.atcrate = referenceap.ataxrate
            newcv.currency = referenceap.currency
            newcv.fxrate = referenceap.fxrate
            newcv.deferredvat = referenceap.deferred
            newcv.particulars = 'Accounts Payable Voucher No.(s) ' + cvrefnum
            newcv.refnum = cvrefnum
            newcv.branch = Branch.objects.get(code='HO')
            newcv.disbursingbranch = referenceap.bankbranchdisburse
            newcv.inputvattype = referenceap.inputvattype
            newcv.amountinwords = request.POST['hdnamountinwords']
            newcv.enterby = request.user
            newcv.modifyby = request.user
            newcv.save()

            total_amount = 0
            i = 0
            for data in allaps:
                newapvcvtrans = Apvcvtransaction()
                newapvcvtrans.cvamount = float(request.POST.getlist('temp_actualamount')[i].replace(',', ''))
                newapvcvtrans.cvmain = newcv
                newapvcvtrans.apmain = data
                total_amount += newapvcvtrans.cvamount
                newapvcvtrans.save()
                updateapv = Apmain.objects.get(pk=newapvcvtrans.apmain.id)
                updateapv.cvamount = newapvcvtrans.cvamount
                if updateapv.cvamount == updateapv.amount:
                    updateapv.isfullycv = 1
                updateapv.save()
                i += 1

            newcv.amount = total_amount
            newcv.save()

            print "CV successfully generated."
    else:
        print "Something went wrong in saving APV/CV."

    return redirect('/processing_transaction/')
