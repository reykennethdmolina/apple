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
from purchaseorder.models import Pomain, Podetail
from accountspayable.models import Apmain, Apdetail
from checkvoucher.models import Cvmain, Cvdetail
from branch.models import Branch
from aptype.models import Aptype
from apsubtype.models import Apsubtype
from supplier.models import Supplier
from cvtype.models import Cvtype
from cvsubtype.models import Cvsubtype
from chartofaccount.models import Chartofaccount
from companyparameter.models import Companyparameter
from inputvat.models import Inputvat
from vat.models import Vat
from ataxcode.models import Ataxcode
from . models import Poapvtransaction, Apvcvtransaction, Poapvdetailtemp
from acctentry.views import generatekey


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'processing_transaction/index.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if self.request.GET:
            if self.request.GET['selectprocess'] == 'potoapv':
                context['data_list'] = Podetail.objects.filter(isdeleted=0, isfullyapv=0, pomain__isdeleted=0,
                                                               pomain__postatus='A', pomain__isfullyapv=0).\
                    order_by('pomain__ponum', 'pomain__supplier_name', 'pomain__inputvattype_id', 'vat_id',
                             'item_counter')
                if self.request.GET['datefrom']:
                    context['data_list'] = context['data_list'].filter(pomain__podate__gte=self.request.GET['datefrom'])
                if self.request.GET['dateto']:
                    context['data_list'] = context['data_list'].filter(pomain__podate__lte=self.request.GET['dateto'])
            elif self.request.GET['selectprocess'] == 'apvtocv':
                context['data_list'] = Apmain.objects.all().filter(isdeleted=0, apstatus='R', isfullycv=0). \
                    order_by('payeecode', 'vat_id', 'apnum')
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
        secretkey = generatekey(request)
        if request.POST['transtype'] == 'potoapv':
            referencepo = Podetail.objects.get(pk=int(request.POST.getlist('trans_checkbox')[0])).pomain
            allpodetail = Podetail.objects.filter(id__in=request.POST.getlist('trans_checkbox')).\
                order_by('pomain__ponum', 'pomain__supplier_name', 'pomain__inputvattype_id', 'vat_id', 'item_counter')

            refnum = ''
            po_nums = allpodetail.values('pomain__ponum').distinct().order_by('pomain__ponum')
            for data in po_nums:
                refnum += ' ' + str(data['pomain__ponum'])

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
            newapv.particulars = 'Payment setup for various items in ' + refnum
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
            for data in allpodetail:
                print data.id
                newpoapvtrans = Poapvtransaction()
                newpoapvtrans.pomain = data.pomain
                newpoapvtrans.podetail = data
                newpoapvtrans.apmain = newapv
                newpoapvtrans.apamount = decimal.Decimal(request.POST.getlist('temp_actualamount')[i].replace(',', ''))
                print 'PO-APV Trans Amount = ' + str(newpoapvtrans.apamount)

                total_amount += newpoapvtrans.apamount
                print 'Total Amount = ' + str(total_amount)
                newpoapvtrans.save()

                # update podetail and pomain
                data.apvtotalamount += decimal.Decimal(str(newpoapvtrans.apamount))
                print 'PO Detail APV Total Amount = ' + str(data.apvtotalamount)
                data.apvremainingamount -= decimal.Decimal(str(newpoapvtrans.apamount))
                print 'PO Detail Remaining Amount = ' + str(data.apvremainingamount)
                if data.apvremainingamount == 0 and data.netamount == data.apvtotalamount:
                    data.isfullyapv = 1
                data.save()

                data_main = newpoapvtrans.pomain
                data_main.apvamount += newpoapvtrans.apamount
                print 'PO Main APV Total Amount = ' + str(data_main.apvamount)
                data_main.totalremainingamount -= newpoapvtrans.apamount
                print 'PO Main Remaining Amount = ' + str(data_main.totalremainingamount)
                if data_main.totalremainingamount == 0 and data_main.totalamount == data_main.apvamount:
                    data_main.isfullyapv = 1
                data_main.save()

                # APV Accounting Entry
                # 1st entry for current item: Inventory Chart of Account
                inventory_entry = Poapvdetailtemp()
                inventory_entry.item_counter = i + 1
                inventory_entry.sort_num = 1
                inventory_entry.secretkey = secretkey
                inventory_entry.apmain = newapv.id
                inventory_entry.ap_num = newapv.apnum
                inventory_entry.ap_date = newapv.apdate
                if data.invitem.inventoryitemclass.inventoryitemtype.code == 'FA' or \
                    data.invitem.inventoryitemclass.inventoryitemtype.code == 'SI' or \
                        data.invitem.inventoryitemclass.inventoryitemtype.code == 'SV':  # remove this soon
                    inventory_entry.chartofaccount = data.invitem.inventoryitemclass.chartofaccountinventory_id
                # elif data.invitem.inventoryitemclass.inventoryitemtype.code == 'SV':
                    # special entry for SERVICES when available
                inventory_entry.balancecode = 'D'
                inventory_entry.debitamount = float(newpoapvtrans.apamount) / (1 + (float(data.vatrate) / 100.0))
                inventory_entry.save()

                # 2nd entry for current item: Input VAT (for Office Supplies and Fixed Assets) or
                # Deferred Input VAT (for Services)
                if data.vatrate > 0:
                    inputvat_entry = Poapvdetailtemp()
                    inputvat_entry.item_counter = i + 1
                    inputvat_entry.sort_num = 2
                    inputvat_entry.secretkey = secretkey
                    inputvat_entry.apmain = newapv.id
                    inputvat_entry.ap_num = newapv.apnum
                    inputvat_entry.ap_date = newapv.apdate
                    if data.invitem.inventoryitemclass.inventoryitemtype.code == 'FA' or \
                                    data.invitem.inventoryitemclass.inventoryitemtype.code == 'SI':
                        inputvat_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat_id
                    elif data.invitem.inventoryitemclass.inventoryitemtype.code == 'SV':
                        inputvat_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_deferredinputvat_id
                    inputvat_entry.supplier = data_main.supplier_id
                    inputvat_entry.inputvat = Inputvat.objects.filter(
                        inputvattype=data.invitem.inventoryitemclass.inventoryitemtype.inputvattype).first().id
                    inputvat_entry.vat = data.vat_id
                    inputvat_entry.balancecode = 'D'
                    inputvat_entry.debitamount = inventory_entry.debitamount * (float(data.vatrate) / 100.0)
                    inputvat_entry.save()

                # 3rd entry for current item: Expanded Withholding Tax
                if data_main.atc:
                    ewt_entry = Poapvdetailtemp()
                    ewt_entry.item_counter = i + 1
                    ewt_entry.sort_num = 3
                    ewt_entry.secretkey = secretkey
                    ewt_entry.apmain = newapv.id
                    ewt_entry.ap_num = newapv.apnum
                    ewt_entry.ap_date = newapv.apdate
                    ewt_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_ewtax_id
                    ewt_entry.ataxcode = data_main.atc_id
                    ewt_entry.balancecode = 'C'
                    ewt_entry.creditamount = float(newpoapvtrans.apamount) * (float(data_main.atcrate) / 100.0)
                    ewt_entry.save()

                # 4th entry for current item: AP Trade
                aptrade_entry = Poapvdetailtemp()
                aptrade_entry.item_counter = i + 1
                aptrade_entry.sort_num = 4
                aptrade_entry.secretkey = secretkey
                aptrade_entry.apmain = newapv.id
                aptrade_entry.ap_num = newapv.apnum
                aptrade_entry.ap_date = newapv.apdate
                aptrade_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_aptrade_id
                aptrade_entry.supplier = data_main.supplier_id
                aptrade_entry.balancecode = 'C'
                aptrade_entry.creditamount = float(newpoapvtrans.apamount) - ewt_entry.creditamount
                aptrade_entry.save()

                i += 1

            newapv.amount = total_amount
            newapv.save()

            poapvdetailtemp_for_grouping = Poapvdetailtemp.objects.filter(secretkey=secretkey).order_by('sort_num',
                                                                                                        'item_counter',
                                                                                                        'inputvat',
                                                                                                        'ataxcode')
            final_entry_counter = 1
            last_entry = 0
            last_inputvat = 0
            last_ataxcode = 0
            for entry in poapvdetailtemp_for_grouping:
                if last_entry == entry.chartofaccount and last_inputvat == entry.inputvat and last_ataxcode == \
                        entry.ataxcode:
                    previous_apdetail = Apdetail.objects.latest('id')
                    previous_apdetail.debitamount += entry.debitamount
                    previous_apdetail.creditamount += entry.creditamount
                    previous_apdetail.save()
                else:
                    final_apdetail = Apdetail()
                    final_apdetail.item_counter = final_entry_counter
                    final_apdetail.apmain = Apmain.objects.get(pk=entry.apmain)
                    final_apdetail.ap_num = final_apdetail.apmain.apnum
                    final_apdetail.ap_date = final_apdetail.apmain.apdate
                    final_apdetail.chartofaccount = Chartofaccount.objects.get(pk=entry.chartofaccount)
                    if entry.supplier:
                        final_apdetail.supplier = Supplier.objects.get(pk=entry.supplier)
                    if entry.inputvat:
                        final_apdetail.inputvat = Inputvat.objects.get(pk=entry.inputvat)
                    if entry.vat:
                        final_apdetail.vat = Vat.objects.get(pk=entry.vat)
                    if entry.ataxcode:
                        final_apdetail.ataxcode = Ataxcode.objects.get(pk=entry.ataxcode)
                    final_apdetail.balancecode = entry.balancecode
                    final_apdetail.debitamount = entry.debitamount
                    final_apdetail.creditamount = entry.creditamount
                    final_apdetail.enterby = request.user
                    final_apdetail.modifyby = request.user
                    final_apdetail.save()
                    final_entry_counter += 1
                    last_entry = entry.chartofaccount
                    last_inputvat = entry.inputvat
                    last_ataxcode = entry.ataxcode

            print "APV successfully generated."
            Poapvdetailtemp.objects.filter(secretkey=secretkey).delete()

            return redirect('/accountspayable/' + str(newapv.id) + '/update')

        elif request.POST['transtype'] == 'apvtocv':
            referenceap = Apmain.objects.get(pk=int(request.POST.getlist('trans_checkbox')[0]))
            allaps = Apmain.objects.filter(id__in=request.POST.getlist('trans_checkbox')).order_by('payeecode',
                                                                                                   'vat_id', 'apnum')

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
            newcv.bankaccount = Companyparameter.objects.get(code='PDI').def_bankaccount
            newcv.disbursingbranch = referenceap.bankbranchdisburse
            newcv.inputvattype = referenceap.inputvattype
            newcv.amountinwords = request.POST['hdnamountinwords']
            newcv.enterby = request.user
            newcv.modifyby = request.user
            newcv.save()

            total_amount = 0
            i = 0
            aptrade_debit_amount = 0
            inputvat_debit_amount = 0
            deferredinputvat_credit_amount = 0
            cashinbank_credit_amount = 0

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

                apv_detail = Apdetail.objects.filter(apmain=data, status='A')
                for detail in apv_detail:
                    if detail.balancecode == 'D':
                        if 'DEFERRED' in detail.chartofaccount.title.upper():   # if deferred input vat
                            inputvat_debit_amount += detail.debitamount
                            deferredinputvat_credit_amount += detail.debitamount
                            aptrade_debit_amount -= detail.debitamount
                        else:
                            cashinbank_credit_amount += detail.debitamount
                    elif detail.balancecode == 'C':
                        aptrade_debit_amount += detail.creditamount
                i += 1

            newcv.amount = total_amount
            newcv.save()

            cvdetail_item_counter = 1

            # CV accounting entries
            # 1st entry: Accounts Payable Trade
            aptrade_cv_entry = Cvdetail()
            aptrade_cv_entry.item_counter = cvdetail_item_counter
            aptrade_cv_entry.cvmain = newcv
            aptrade_cv_entry.cv_num = newcv.cvnum
            aptrade_cv_entry.cv_date = newcv.cvdate
            aptrade_cv_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_aptrade
            aptrade_cv_entry.supplier = newcv.payee
            aptrade_cv_entry.balancecode = 'D'
            aptrade_cv_entry.debitamount = aptrade_debit_amount
            aptrade_cv_entry.enterby = request.user
            aptrade_cv_entry.modifyby = request.user
            aptrade_cv_entry.save()
            cvdetail_item_counter += 1

            # 2nd entry: Input VAT (if there is a Deferred Input VAT from APV which only comes from Services)
            if inputvat_debit_amount > 0:
                inputvat_cv_entry = Cvdetail()
                inputvat_cv_entry.item_counter = cvdetail_item_counter
                inputvat_cv_entry.cvmain = newcv
                inputvat_cv_entry.cv_num = newcv.cvnum
                inputvat_cv_entry.cv_date = newcv.cvdate
                inputvat_cv_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat
                inputvat_cv_entry.supplier = newcv.payee
                inputvat_cv_entry.inputvat = Inputvat.objects.filter(title='SERVICES').first()
                inputvat_cv_entry.vat = newcv.vat
                inputvat_cv_entry.balancecode = 'D'
                inputvat_cv_entry.debitamount = inputvat_debit_amount
                inputvat_cv_entry.enterby = request.user
                inputvat_cv_entry.modifyby = request.user
                inputvat_cv_entry.save()
                cvdetail_item_counter += 1
                # 3rd entry: Deferred Input VAT
                deferredinputvat_cv_entry = Cvdetail()
                deferredinputvat_cv_entry.item_counter = cvdetail_item_counter
                deferredinputvat_cv_entry.cvmain = newcv
                deferredinputvat_cv_entry.cv_num = newcv.cvnum
                deferredinputvat_cv_entry.cv_date = newcv.cvdate
                deferredinputvat_cv_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_deferredinputvat
                deferredinputvat_cv_entry.supplier = newcv.payee
                deferredinputvat_cv_entry.inputvat = Inputvat.objects.filter(title='SERVICES').first()
                deferredinputvat_cv_entry.vat = newcv.vat
                deferredinputvat_cv_entry.balancecode = 'C'
                deferredinputvat_cv_entry.creditamount = deferredinputvat_credit_amount
                deferredinputvat_cv_entry.enterby = request.user
                deferredinputvat_cv_entry.modifyby = request.user
                deferredinputvat_cv_entry.save()
                cvdetail_item_counter += 1

            # 4th entry: Cash in Bank
            cashinbank_cv_entry = Cvdetail()
            cashinbank_cv_entry.item_counter = cvdetail_item_counter
            cashinbank_cv_entry.cvmain = newcv
            cashinbank_cv_entry.cv_num = newcv.cvnum
            cashinbank_cv_entry.cv_date = newcv.cvdate
            cashinbank_cv_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_cashinbank
            cashinbank_cv_entry.bankaccount = newcv.bankaccount
            cashinbank_cv_entry.balancecode = 'C'
            cashinbank_cv_entry.creditamount = cashinbank_credit_amount
            cashinbank_cv_entry.enterby = request.user
            cashinbank_cv_entry.modifyby = request.user
            cashinbank_cv_entry.save()

            print "CV successfully generated."

            return redirect('/checkvoucher/' + str(newcv.id) + '/update')

    else:
        print "Something went wrong in saving APV/CV."

    return redirect('/processing_transaction/')
