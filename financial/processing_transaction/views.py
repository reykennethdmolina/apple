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
from django.db.models import Q
from department.models import Department
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
from inventoryitemclass.models import Inventoryitemclass
from vat.models import Vat
from ataxcode.models import Ataxcode
from . models import Poapvtransaction, Apvcvtransaction, Poapvdetailtemp
from acctentry.views import generatekey
from django.db import connection
from collections import namedtuple


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'processing_transaction/index.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if self.request.GET:
            if self.request.GET['selectprocess'] == 'potoapv' or self.request.GET['selectprocess'] == 'potocv':
                context['data_list'] = Podetail.objects.filter(isdeleted=0, isfullyapv=0, pomain__isdeleted=0,
                                                               pomain__postatus='A', pomain__isfullyapv=0).\
                    order_by('pomain__ponum', 'pomain__supplier_name', 'pomain__inputvattype_id', 'vat_id',
                             'item_counter')
                if 'datefrom' in self.request.GET and self.request.GET['datefrom']:
                    context['data_list'] = context['data_list'].filter(pomain__podate__gte=self.request.GET['datefrom'])
                if 'dateto' in self.request.GET and self.request.GET['dateto']:
                    context['data_list'] = context['data_list'].filter(pomain__podate__lte=self.request.GET['dateto'])
                if 'keywords' in self.request.GET and self.request.GET['keywords']:
                    keysearch = self.request.GET['keywords']
                    context['data_list'] = context['data_list'].filter(Q(pomain__ponum__icontains=keysearch) |
                                                                       Q(invitem_name__icontains=keysearch) |
                                                                       Q(pomain__supplier_name__icontains=keysearch))
            elif self.request.GET['selectprocess'] == 'apvtocv' or self.request.GET['selectprocess'] == 'apvtoapv':
                # added FOR APPROVAL status, making all active APVs eligible for importation regardless of status
                #context['data_list'] = Apmain.objects.all().filter((Q(apstatus='A') | Q(apstatus='R') | Q(apstatus='F')), isdeleted=0, isfullycv=0, status='A').\
                context['data_list'] = Apmain.objects.all().filter((Q(apstatus='A') | Q(apstatus='R') | Q(apstatus='F')), isdeleted=0, isfullycv=0).\
                    order_by('payeename', 'vat_id', 'apnum',)
                if 'datefrom' in self.request.GET and self.request.GET['datefrom']:
                    context['data_list'] = context['data_list'].filter(apdate__gte=self.request.GET['datefrom'])
                if 'dateto' in self.request.GET and self.request.GET['dateto']:
                    context['data_list'] = context['data_list'].filter(apdate__lte=self.request.GET['dateto'])
                if 'keywords' in self.request.GET and self.request.GET['keywords']:
                    keysearch = self.request.GET['keywords']
                    context['data_list'] = context['data_list'].filter(Q(apnum__icontains=keysearch) |
                                                                       Q(payeename__icontains=keysearch))

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        # context['data'] = Poapvtransaction.objects.filter(Q(apmain__apmain_apvcvtransaction__cvamount=True) | Q(apmain__apmain_apvcvtransaction__cvamount=False))
        # context['data'] = Apmain.objects.filter(apmain_apvcvtransaction__apmain=True)

        # PO-based report
        poapvtrans = Poapvtransaction.objects.filter(status='A').order_by('-pomain', '-podetail', '-apmain')
        apvcvtrans = []
        for data in poapvtrans:
            #print data.apmain_id
            #apmain = get_object_or_None(Apvcvtransaction, apmain=data.apmain_id)
            apmain = Apvcvtransaction.objects.filter(apmain_id=data.apmain_id).first()
            #if apmain:
            if apmain is not None:
                print 'pasok'
                if apmain.new_apmain:
                    apvcvtrans.append({
                        'ap_to_ap_num': apmain.new_apmain.apnum,
                        'ap_to_ap_date': apmain.new_apmain.apdate,
                        'ap_to_cv_num': '',
                        'ap_to_cv_date': '',
                        'ap_or_cv_amt': apmain.cvamount
                    })
                elif apmain.cvmain_id:
                    cvmain = Cvmain.objects.filter(pk=apmain.cvmain_id).first()
                    print 'cv'
                    print cvmain
                    if cvmain is not None:
                        apvcvtrans.append({
                            'ap_to_ap_num': '',
                            'ap_to_ap_date': '',
                            'ap_to_cv_num': cvmain.cvnum,
                            'ap_to_cv_date': cvmain.cvdate,
                            'ap_or_cv_amt': apmain.cvamount
                        })
                else:
                    apvcvtrans.append({
                        'ap_to_ap_num': '',
                        'ap_to_ap_date': '',
                        'ap_to_cv_num': '',
                        'ap_to_cv_date': '',
                        'ap_or_cv_amt': ''
                    })
            else:
                apvcvtrans.append({
                    'ap_to_ap_num': '',
                    'ap_to_ap_date': '',
                    'ap_to_cv_num': '',
                    'ap_to_cv_date': '',
                    'ap_or_cv_amt': ''
                })
        context['data'] = zip(poapvtrans, apvcvtrans)

        # APV-based report
        #apvcv = Apvcvtransaction.objects.filter(status='A').order_by('-apmain')
            #context['data2'] = apvcv

        if self.request.GET:
            context['selectprocess'] = self.request.GET['selectprocess']
            if 'datefrom' in self.request.GET:
                context['datefrom'] = self.request.GET['datefrom']
            if 'dateto' in self.request.GET:
                context['dateto'] = self.request.GET['dateto']
            if 'keywords' in self.request.GET:
                context['keywords'] = self.request.GET['keywords']

        return context


@csrf_exempt
def importtransdata(request):
    if request.method == 'POST':
        secretkey = generatekey(request)
        if request.POST['transtype'] == 'potoapv' or request.POST['transtype'] == 'potocv':
            referencepo = Podetail.objects.get(pk=int(request.POST.getlist('trans_checkbox')[0])).pomain
            allpodetail = Podetail.objects.filter(id__in=request.POST.getlist('trans_checkbox')).\
                order_by('pomain__ponum', 'pomain__supplier_name', 'pomain__inputvattype_id', 'vat_id', 'item_counter')

            refnum = ''
            refparticulars = ''
            po_nums = allpodetail.values('pomain__ponum').distinct().order_by('pomain__ponum')
            for data in po_nums:
                refnum += ' ' + str(data['pomain__ponum'])
                refparticulars += ' ' + unicode(Pomain.objects.get(ponum=str(data['pomain__ponum'])).particulars)

            if request.POST['transtype'] == 'potoapv':
                year = str(datetime.date.today().year)
                yearqs = Apmain.objects.filter(apnum__startswith=year)

                apnumlast = lastAPNumber('true')

                latestapnum = str(apnumlast[0])
                apnum = year
                last = str(int(latestapnum) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    apnum += '0'
                apnum += last

                # if yearqs:
                #     apnumlast = yearqs.latest('apnum')
                #     latestapnum = str(apnumlast)
                #     print "latest: " + latestapnum
                #
                #     apnum = year
                #     last = str(int(latestapnum[4:]) + 1)
                #     zero_addon = 6 - len(last)
                #     for num in range(0, zero_addon):
                #         apnum += '0'
                #     apnum += last
                # else:
                #     apnum = year + '000001'
                # print 'apnum: ' + apnum

                newapv = Apmain()
                if 'selectapvtype' in request.POST:
                    newapv.aptype = Aptype.objects.filter(code=request.POST['selectapvtype']).first()
                newapv.apsubtype = Apsubtype.objects.get(code='IPO')
                newapv.apnum = apnum
                newapv.apprefix = 'AP'
                #newapv.apdate = datetime.date.today()
                newapv.apdate = datetime.date.today()
                newapv.apstatus = 'F'
                newapv.payee_id = referencepo.supplier.id
                newapv.payeecode = referencepo.supplier.code
                newapv.payeename = referencepo.supplier.name
                newapv.vatcode = referencepo.vat.code
                newapv.atax = referencepo.atc
                newapv.ataxcode = referencepo.atc.code
                newapv.ataxrate = referencepo.atcrate
                newapv.refno = 'PO No.(s) ' + refnum
                newapv.deferred = referencepo.deferredvat
                newapv.creditterm = referencepo.creditterm
                if newapv.creditterm:
                    newapv.duedate = datetime.datetime.now().date() + datetime.timedelta(days=newapv.creditterm.daysdue)
            elif request.POST['transtype'] == 'potocv':
                year = str(datetime.date.today().year)
                yearqs = Cvmain.objects.filter(cvnum__startswith=year)

                cvnumlast = lastCVNumber('true')
                latestcvnum = str(cvnumlast[0])

                cvnum = year
                # print str(int(latestapnum[4:]))
                last = str(int(latestcvnum) + 1)

                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    cvnum += '0'
                cvnum += last

                newapv = Cvmain()
                newapv.cvnum = cvnum
                newapv.cvdate = datetime.date.today()
                newapv.cvstatus = 'F'
                newapv.payee = referencepo.supplier
                newapv.payee_code = referencepo.supplier.code
                newapv.payee_name = referencepo.supplier.name
                newapv.checknum = cvnum
                newapv.checkdate = datetime.date.today()
                newapv.atc = referencepo.atc
                newapv.atcrate = referencepo.atcrate
                newapv.deferredvat = referencepo.deferredvat
                newapv.refnum = 'PO No.(s) ' + refnum
                newapv.cvtype = Cvtype.objects.get(description='NON-AP')
                newapv.cvsubtype = Cvsubtype.objects.get(code='IPO')
                # newapv.bankaccount = Companyparameter.objects.get(code='PDI').def_bankaccount
                newapv.amountinwords = request.POST['hdnamountinwords']

            newapv.vat = referencepo.vat
            newapv.vatrate = referencepo.vatrate
            newapv.inputvattype = referencepo.inputvattype
            newapv.fxrate = referencepo.fxrate
            newapv.particulars = refparticulars
            newapv.branch = Branch.objects.get(code='HO')
            newapv.currency = referencepo.currency
            newapv.enterby = request.user
            newapv.modifyby = request.user
            newapv.save()

            total_amount = 0
            i = 0
            for data in allpodetail:
                newpoapvtrans = Poapvtransaction()
                newpoapvtrans.pomain = data.pomain
                newpoapvtrans.podetail = data

                if request.POST['transtype'] == 'potoapv':
                    newpoapvtrans.apmain = newapv
                elif request.POST['transtype'] == 'potocv':
                    newpoapvtrans.cvmain = newapv

                newpoapvtrans.apamount = decimal.Decimal(request.POST.getlist('temp_actualamount')[i].replace(',', ''))
                print 'PO-APV/PO-CV Trans Amount = ' + str(newpoapvtrans.apamount)

                total_amount += newpoapvtrans.apamount
                print 'Total Amount = ' + str(total_amount)
                newpoapvtrans.save()

                # update podetail and pomain
                data.apvtotalamount += decimal.Decimal(str(newpoapvtrans.apamount))
                print 'PO Detail APV/CV Total Amount = ' + str(data.apvtotalamount)
                data.apvremainingamount -= decimal.Decimal(str(newpoapvtrans.apamount))
                print 'PO Detail Remaining Amount = ' + str(data.apvremainingamount)
                if data.apvremainingamount == 0 and data.netamount == data.apvtotalamount:
                    data.isfullyapv = 1  # can also be isfullycv
                data.save()

                data_main = newpoapvtrans.pomain
                data_main.apvamount += newpoapvtrans.apamount
                print 'PO Main APV/CV Total Amount = ' + str(data_main.apvamount)
                data_main.totalremainingamount -= newpoapvtrans.apamount
                print 'PO Main Remaining Amount = ' + str(data_main.totalremainingamount)
                if data_main.totalremainingamount == 0 and data_main.totalamount == data_main.apvamount:
                    data_main.isfullyapv = 1  # can also be isfullycv
                data_main.save()

                # APV/CV Accounting Entry
                # 1st entry for current item: Inventory Chart of Account
                inventory_entry = Poapvdetailtemp()
                inventory_entry.item_counter = i + 1
                inventory_entry.sort_num = 1
                inventory_entry.secretkey = secretkey
                inventory_entry.apmain = newapv.id
                if request.POST['transtype'] == 'potoapv':
                    inventory_entry.ap_num = newapv.apnum
                    inventory_entry.ap_date = newapv.apdate
                elif request.POST['transtype'] == 'potocv':
                    inventory_entry.ap_num = newapv.cvnum
                    inventory_entry.ap_date = newapv.cvdate
                if data.invitem.inventoryitemclass.inventoryitemtype.code == 'FA' or data.invitem.inventoryitemclass.\
                        inventoryitemtype.code == 'SI':
                    inventory_entry.chartofaccount = data.invitem.inventoryitemclass.chartofaccountinventory_id
                    # if data.department:
                    #     department_expchartofaccount_accountcode_prefix = str(
                    #         Chartofaccount.objects.get(pk=Department.objects.get(
                    #             pk=data.department.id).expchartofaccount_id).accountcode)[:2]
                    #     if str(Inventoryitemclass.objects.get(pk=data.invitem.inventoryitemclass.id).chartexpcostofsale.
                    #                    accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                    #         inventory_entry.chartofaccount = Inventoryitemclass.objects.\
                    #             get(pk=data.invitem.inventoryitemclass.id).chartexpcostofsale_id
                    #     elif str(Inventoryitemclass.objects.get(pk=data.invitem.inventoryitemclass.id).
                    #                      chartexpgenandadmin.
                    #                      accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                    #         inventory_entry.chartofaccount = Inventoryitemclass.objects.\
                    #             get(pk=data.invitem.inventoryitemclass.id).chartexpgenandadmin_id
                    #     elif str(Inventoryitemclass.objects.get(pk=data.invitem.inventoryitemclass.id).chartexpsellexp.
                    #                      accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                    #         inventory_entry.chartofaccount = Inventoryitemclass.objects.\
                    #             get(pk=data.invitem.inventoryitemclass.id).chartexpsellexp_id
                    #     else:
                    #         inventory_entry.chartofaccount = Inventoryitemclass.objects.\
                    #             get(pk=data.invitem.inventoryitemclass.id).chartexpcostofsale_id
                    #     inventory_entry.department = data.department.id
                    # else:
                    #     inventory_entry.chartofaccount = data.invitem.inventoryitemclass.chartofaccountinventory_id
                    # print 'SI'
                elif data.invitem.inventoryitemclass.inventoryitemtype.code == 'SV':
                    if data.department:
                        department_expchartofaccount_accountcode_prefix = str(
                            Chartofaccount.objects.get(pk=Department.objects.get(
                                pk=data.department.id).expchartofaccount_id).accountcode)[:2]
                        if str(Inventoryitemclass.objects.get(pk=data.invitem.inventoryitemclass.id).chartexpcostofsale.
                                       accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                            inventory_entry.chartofaccount = Inventoryitemclass.objects.\
                                get(pk=data.invitem.inventoryitemclass.id).chartexpcostofsale_id
                        elif str(Inventoryitemclass.objects.get(pk=data.invitem.inventoryitemclass.id).
                                         chartexpgenandadmin.
                                         accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                            inventory_entry.chartofaccount = Inventoryitemclass.objects.\
                                get(pk=data.invitem.inventoryitemclass.id).chartexpgenandadmin_id
                        elif str(Inventoryitemclass.objects.get(pk=data.invitem.inventoryitemclass.id).chartexpsellexp.
                                         accountcode)[:2] == department_expchartofaccount_accountcode_prefix:
                            inventory_entry.chartofaccount = Inventoryitemclass.objects.\
                                get(pk=data.invitem.inventoryitemclass.id).chartexpsellexp_id
                        else:
                            inventory_entry.chartofaccount = Inventoryitemclass.objects.\
                                get(pk=data.invitem.inventoryitemclass.id).chartexpcostofsale_id
                        inventory_entry.department = data.department.id
                    else:
                        inventory_entry.chartofaccount = data.invitem.inventoryitemclass.chartofaccountinventory_id
                    print 'SV'

                inventory_entry.balancecode = 'D'
                # inventory_entry.debitamount = float(newpoapvtrans.apamount) / (1 + (float(data.vatrate) / 100.0))
                # follow VATable amount in PODETAIL
                inventory_entry.debitamount = float(data.vatable) + float(data.vatexempt) + float(data.vatzerorated)
                inventory_entry.save()

                # 2nd entry for current item: Input VAT or Deferred Input VAT depending on Supplier Master file
                if data.vatrate > 0:
                    inputvat_entry = Poapvdetailtemp()
                    inputvat_entry.item_counter = i + 1
                    inputvat_entry.sort_num = 2
                    inputvat_entry.secretkey = secretkey
                    inputvat_entry.apmain = newapv.id
                    if request.POST['transtype'] == 'potoapv':
                        inputvat_entry.ap_num = newapv.apnum
                        inputvat_entry.ap_date = newapv.apdate
                    elif request.POST['transtype'] == 'potocv':
                        inputvat_entry.ap_num = newapv.cvnum
                        inputvat_entry.ap_date = newapv.cvdate
                    if data_main.supplier.deferredvat == 'N' or data_main.supplier.deferredvat is None:
                        inputvat_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat_id
                    elif data_main.supplier.deferredvat == 'Y':
                        inputvat_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_deferredinputvat_id
                    # if data.invitem.inventoryitemclass.inventoryitemtype.code == 'FA' or \
                    #                 data.invitem.inventoryitemclass.inventoryitemtype.code == 'SI':
                    #     inputvat_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat_id
                    # elif data.invitem.inventoryitemclass.inventoryitemtype.code == 'SV':
                    #     inputvat_entry.chartofaccount = Companyparameter.objects.get(code='PDI').
                    # coa_deferredinputvat_id
                    inputvat_entry.supplier = data_main.supplier_id
                    inputvat_entry.inputvat = Inputvat.objects.filter(
                        inputvattype=data.invitem.inventoryitemclass.inventoryitemtype.inputvattype).first().id
                    inputvat_entry.vat = data.vat_id
                    inputvat_entry.balancecode = 'D'
                    # inputvat_entry.debitamount = inventory_entry.debitamount * (float(data.vatrate) / 100.0) follow
                    # VAT amount in PODETAIL
                    inputvat_entry.debitamount = data.vatamount
                    inputvat_entry.save()

                # 3rd entry for current item: Expanded Withholding Tax
                if data_main.atc:
                    ewt_entry = Poapvdetailtemp()
                    ewt_entry.item_counter = i + 1
                    ewt_entry.sort_num = 3
                    ewt_entry.secretkey = secretkey
                    ewt_entry.apmain = newapv.id
                    if request.POST['transtype'] == 'potoapv':
                        ewt_entry.ap_num = newapv.apnum
                        ewt_entry.ap_date = newapv.apdate
                    elif request.POST['transtype'] == 'potocv':
                        ewt_entry.ap_num = newapv.cvnum
                        ewt_entry.ap_date = newapv.cvdate
                    ewt_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_ewtax_id
                    ewt_entry.ataxcode = data_main.atc_id
                    ewt_entry.supplier = data_main.supplier_id
                    ewt_entry.balancecode = 'C'
                    # ewt_entry.creditamount = float(newpoapvtrans.apamount) * (float(data_main.atcrate) / 100.0) follow
                    # EWT amount in PODETAIL
                    ewt_entry.creditamount = float(data.atcamount)
                    ewt_entry.save()

                # 4th entry for current item: AP Trade if PO - APV, Cash In Bank if PO - CV
                if request.POST['transtype'] == 'potoapv':
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
                elif request.POST['transtype'] == 'potocv':
                    cashinbank_entry = Poapvdetailtemp()
                    cashinbank_entry.item_counter = i + 1
                    cashinbank_entry.sort_num = 4
                    cashinbank_entry.secretkey = secretkey
                    cashinbank_entry.apmain = newapv.id
                    cashinbank_entry.ap_num = newapv.cvnum
                    cashinbank_entry.ap_date = newapv.cvdate
                    cashinbank_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_cashinbank_id
                    cashinbank_entry.bankaccount = newapv.bankaccount.id
                    cashinbank_entry.balancecode = 'C'
                    cashinbank_entry.creditamount = float(newpoapvtrans.apamount) - ewt_entry.creditamount
                    cashinbank_entry.save()

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
                    if request.POST['transtype'] == 'potoapv':
                        previous_detail = Apdetail.objects.latest('id')
                    elif request.POST['transtype'] == 'potocv':
                        previous_detail = Cvdetail.objects.latest('id')
                    previous_detail.debitamount += entry.debitamount
                    previous_detail.creditamount += entry.creditamount
                    previous_detail.save()
                else:
                    if request.POST['transtype'] == 'potoapv':
                        final_detail = Apdetail()
                        final_detail.apmain = Apmain.objects.get(pk=entry.apmain)
                        final_detail.ap_num = final_detail.apmain.apnum
                        final_detail.ap_date = final_detail.apmain.apdate
                    elif request.POST['transtype'] == 'potocv':
                        final_detail = Cvdetail()
                        final_detail.cvmain = Cvmain.objects.get(pk=entry.apmain)
                        final_detail.cv_num = final_detail.cvmain.cvnum
                        final_detail.cv_date = final_detail.cvmain.cvdate
                    final_detail.item_counter = final_entry_counter
                    print 'hey'
                    final_detail.chartofaccount = Chartofaccount.objects.get(pk=entry.chartofaccount)
                    if entry.supplier:
                        final_detail.supplier = Supplier.objects.get(pk=entry.supplier)
                    if entry.inputvat:
                        final_detail.inputvat = Inputvat.objects.get(pk=entry.inputvat)
                    if entry.vat:
                        final_detail.vat = Vat.objects.get(pk=entry.vat)
                    if entry.ataxcode:
                        final_detail.ataxcode = Ataxcode.objects.get(pk=entry.ataxcode)
                    if entry.department:
                        final_detail.department = Department.objects.get(pk=entry.department)
                    final_detail.balancecode = entry.balancecode
                    final_detail.debitamount = entry.debitamount
                    final_detail.creditamount = entry.creditamount
                    final_detail.enterby = request.user
                    final_detail.modifyby = request.user
                    final_detail.save()
                    final_entry_counter += 1
                    last_entry = entry.chartofaccount
                    last_inputvat = entry.inputvat
                    last_ataxcode = entry.ataxcode

            print "APV/CV successfully generated."
            Poapvdetailtemp.objects.filter(secretkey=secretkey).delete()

            if request.POST['transtype'] == 'potoapv':
                return redirect('/accountspayable/' + str(newapv.id) + '/update')
            elif request.POST['transtype'] == 'potocv':
                return redirect('/checkvoucher/' + str(newapv.id) + '/update')

        elif request.POST['transtype'] == 'apvtocv' or request.POST['transtype'] == 'apvtoapv':
            referenceap = Apmain.objects.get(pk=int(request.POST.getlist('trans_checkbox')[0]))
            allaps = Apmain.objects.filter(id__in=request.POST.getlist('trans_checkbox')).order_by('payeename',
                                                                                                   'vat_id', 'apnum')

            ap_nums = allaps.values_list('apnum', flat=True)
            cvrefnum = ' '.join(ap_nums)
            ap_particulars = allaps.values_list('particulars', flat=True)
            cvparticulars = ' '.join(ap_particulars)

            year = str(datetime.date.today().year)
            yearqs = Cvmain.objects.filter(cvnum__startswith=year)

            # if yearqs:
            #     cvnumlast = yearqs.latest('cvnum')
            #     latestcvnum = str(cvnumlast)
            #     print "latest: " + latestcvnum
            #
            #     cvnum = year
            #     last = str(int(latestcvnum[4:]) + 1)
            #     zero_addon = 6 - len(last)
            #     for num in range(0, zero_addon):
            #         cvnum += '0'
            #     cvnum += last
            # else:
            #     cvnum = year + '000001'
            # print 'cvnum: ' + cvnum

            cvnumlast = lastCVNumber('true')
            latestcvnum = str(cvnumlast[0])

            cvnum = year
            # print str(int(latestapnum[4:]))
            last = str(int(latestcvnum) + 1)

            zero_addon = 6 - len(last)
            for num in range(0, zero_addon):
                cvnum += '0'
            cvnum += last

            if request.POST['transtype'] == 'apvtoapv':
                year = str(datetime.date.today().year)
                yearqs = Apmain.objects.filter(apnum__startswith=year)

                apnumlast = lastAPNumber('true')

                latestapnum = str(apnumlast[0])
                apnum = year
                last = str(int(latestapnum) + 1)
                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    apnum += '0'
                apnum += last

                newapv = Apmain()
                if 'selectapvtype' in request.POST:
                    newapv.aptype = Aptype.objects.filter(code=request.POST['selectapvtype']).first()
                newapv.apsubtype = Apsubtype.objects.get(code='IAP')
                newapv.apnum = apnum
                newapv.apprefix = 'AP'
                newapv.apdate = datetime.date.today()
                newapv.apstatus = 'F'
                newapv.payee_id = referenceap.payee_id
                newapv.payeecode = referenceap.payeecode
                newapv.payeename = referenceap.payeename
                newapv.vatcode = referenceap.vatcode
                newapv.atax = referenceap.atax
                newapv.ataxcode = referenceap.ataxcode
                newapv.ataxrate = referenceap.ataxrate
                newapv.refno = 'APV No.(s) ' + cvrefnum
                newapv.deferred = referenceap.deferred
                newapv.creditterm = referenceap.creditterm
                newapv.duedate = referenceap.duedate
                newapv.bankbranchdisbursebranch = referenceap.bankbranchdisbursebranch
                newapv.bankbranchdisburse = referenceap.bankbranchdisburse
                newapv.bankaccount = referenceap.bankaccount
            elif request.POST['transtype'] == 'apvtocv':
                year = str(datetime.date.today().year)
                yearqs = Cvmain.objects.filter(cvnum__startswith=year)

                cvnumlast = lastCVNumber('true')
                latestcvnum = str(cvnumlast[0])

                cvnum = year
                # print str(int(latestapnum[4:]))
                last = str(int(latestcvnum) + 1)

                zero_addon = 6 - len(last)
                for num in range(0, zero_addon):
                    cvnum += '0'
                cvnum += last

                newapv = Cvmain()
                newapv.cvtype = Cvtype.objects.get(description='AP')
                newapv.cvsubtype = Cvsubtype.objects.get(code='IAP')
                newapv.cvnum = cvnum
                newapv.cvdate = datetime.date.today()
                newapv.cvstatus = 'F'
                newapv.payee = Supplier.objects.get(pk=referenceap.payee_id)
                newapv.payee_code = newapv.payee.code
                newapv.payee_name = newapv.payee.name
                newapv.checknum = cvnum
                newapv.checkdate = datetime.date.today()
                newapv.atc = referenceap.atax
                newapv.atcrate = referenceap.ataxrate
                newapv.deferredvat = referenceap.deferred
                newapv.refnum = 'APV No.(s) ' + cvrefnum
                newapv.bankaccount = referenceap.bankaccount
                newapv.disbursingbranch = referenceap.bankbranchdisburse
                newapv.amountinwords = request.POST['hdnamountinwords']
            newapv.vat = referenceap.vat
            newapv.vatrate = referenceap.vatrate
            newapv.inputvattype = referenceap.inputvattype
            newapv.fxrate = referenceap.fxrate
            newapv.particulars = cvparticulars
            newapv.branch = referenceap.branch
            newapv.currency = referenceap.currency
            newapv.enterby = request.user
            newapv.modifyby = request.user
            newapv.save()

            total_amount = 0
            i = 0
            aptrade_debit_amount = 0
            inputvat_debit_amount = 0
            deferredinputvat_credit_amount = 0
            cashinbank_credit_amount = 0

            for data in allaps:
                newapvcvtrans = Apvcvtransaction()
                newapvcvtrans.apmain = data
                newapvcvtrans.cvamount = float(request.POST.getlist('temp_actualamount')[i].replace(',', ''))
                if request.POST['transtype'] == 'apvtoapv':
                    newapvcvtrans.new_apmain = newapv
                elif request.POST['transtype'] == 'apvtocv':
                    newapvcvtrans.cvmain = newapv
                total_amount += newapvcvtrans.cvamount
                newapvcvtrans.save()
                updateapv = Apmain.objects.get(pk=newapvcvtrans.apmain.id)
                updateapv.cvamount = newapvcvtrans.cvamount
                if updateapv.cvamount == updateapv.amount:
                    updateapv.isfullycv = 1
                updateapv.save()

                #apv_detail = Apdetail.objects.filter(apmain=data, status='A')
                apv_detail = Apdetail.objects.filter(apmain=data)
                for detail in apv_detail:
                    if detail.balancecode == 'C' and detail.chartofaccount.id == Companyparameter.objects.get(code='PDI').coa_aptrade_id:
                        aptrade_debit_amount += detail.creditamount
                        cashinbank_credit_amount += detail.creditamount
                    # if detail.balancecode == 'D':
                    #     if 'DEFERRED' in detail.chartofaccount.title.upper():   # if deferred input vat
                    #         inputvat_debit_amount += detail.debitamount
                    #         deferredinputvat_credit_amount += detail.debitamount
                    #         aptrade_debit_amount -= detail.debitamount
                    #     else:
                    #         cashinbank_credit_amount += detail.debitamount
                    # elif detail.balancecode == 'C':
                    #     aptrade_debit_amount += detail.creditamount
                i += 1

            newapv.amount = cashinbank_credit_amount
            newapv.save()

            cvdetail_item_counter = 1

            # APV/CV accounting entries
            # 1st entry: Accounts Payable Trade
            if request.POST['transtype'] == 'apvtoapv':
                aptrade_cv_entry = Apdetail()
                aptrade_cv_entry.apmain = newapv
                aptrade_cv_entry.ap_num = newapv.apnum
                aptrade_cv_entry.ap_date = newapv.apdate
                aptrade_cv_entry.supplier = Supplier.objects.filter(id=newapv.payee_id).first()
            elif request.POST['transtype'] == 'apvtocv':
                aptrade_cv_entry = Cvdetail()
                aptrade_cv_entry.cvmain = newapv
                aptrade_cv_entry.cv_num = newapv.cvnum
                aptrade_cv_entry.cv_date = newapv.cvdate
                aptrade_cv_entry.supplier = newapv.payee
            aptrade_cv_entry.item_counter = cvdetail_item_counter
            aptrade_cv_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_aptrade
            aptrade_cv_entry.balancecode = 'D'
            aptrade_cv_entry.debitamount = aptrade_debit_amount
            aptrade_cv_entry.enterby = request.user
            aptrade_cv_entry.modifyby = request.user
            aptrade_cv_entry.save()
            cvdetail_item_counter += 1

            # 2nd entry: Input VAT (if there is a Deferred Input VAT from APV which only comes from Services)
            # if inputvat_debit_amount > 0:
            #     if request.POST['transtype'] == 'apvtoapv':
            #         inputvat_cv_entry = Apdetail()
            #         inputvat_cv_entry.apmain = newapv
            #         inputvat_cv_entry.ap_num = newapv.apnum
            #         inputvat_cv_entry.ap_date = newapv.apdate
            #         inputvat_cv_entry.supplier = Supplier.objects.filter(id=newapv.payee_id).first()
            #     elif request.POST['transtype'] == 'apvtocv':
            #         inputvat_cv_entry = Cvdetail()
            #         inputvat_cv_entry.cvmain = newapv
            #         inputvat_cv_entry.cv_num = newapv.cvnum
            #         inputvat_cv_entry.cv_date = newapv.cvdate
            #         inputvat_cv_entry.supplier = newapv.payee
            #     inputvat_cv_entry.item_counter = cvdetail_item_counter
            #     inputvat_cv_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_inputvat
            #     inputvat_cv_entry.inputvat = Inputvat.objects.filter(title='SERVICES').first()
            #     inputvat_cv_entry.vat = newapv.vat
            #     inputvat_cv_entry.balancecode = 'D'
            #     inputvat_cv_entry.debitamount = inputvat_debit_amount
            #     inputvat_cv_entry.enterby = request.user
            #     inputvat_cv_entry.modifyby = request.user
            #     inputvat_cv_entry.save()
            #     cvdetail_item_counter += 1
            #     # 3rd entry: Deferred Input VAT
            #     if request.POST['transtype'] == 'apvtoapv':
            #         deferredinputvat_cv_entry = Apdetail()
            #         deferredinputvat_cv_entry.apmain = newapv
            #         deferredinputvat_cv_entry.ap_num = newapv.apnum
            #         deferredinputvat_cv_entry.ap_date = newapv.apdate
            #         deferredinputvat_cv_entry.supplier = Supplier.objects.filter(id=newapv.payee_id).first()
            #     elif request.POST['transtype'] == 'apvtocv':
            #         deferredinputvat_cv_entry = Cvdetail()
            #         deferredinputvat_cv_entry.cvmain = newapv
            #         deferredinputvat_cv_entry.cv_num = newapv.cvnum
            #         deferredinputvat_cv_entry.cv_date = newapv.cvdate
            #         deferredinputvat_cv_entry.supplier = newapv.payee
            #     deferredinputvat_cv_entry.item_counter = cvdetail_item_counter
            #     deferredinputvat_cv_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_deferredinputvat
            #     deferredinputvat_cv_entry.inputvat = Inputvat.objects.filter(title='SERVICES').first()
            #     deferredinputvat_cv_entry.vat = newapv.vat
            #     deferredinputvat_cv_entry.balancecode = 'C'
            #     deferredinputvat_cv_entry.creditamount = deferredinputvat_credit_amount
            #     deferredinputvat_cv_entry.enterby = request.user
            #     deferredinputvat_cv_entry.modifyby = request.user
            #     deferredinputvat_cv_entry.save()
            #     cvdetail_item_counter += 1

            # 4th entry: Cash in Bank
            if request.POST['transtype'] == 'apvtoapv':
                cashinbank_cv_entry = Apdetail()
                cashinbank_cv_entry.apmain = newapv
                cashinbank_cv_entry.ap_num = newapv.apnum
                cashinbank_cv_entry.ap_date = newapv.apdate
                cashinbank_cv_entry.bankaccount = newapv.bankaccount
            elif request.POST['transtype'] == 'apvtocv':
                cashinbank_cv_entry = Cvdetail()
                cashinbank_cv_entry.cvmain = newapv
                cashinbank_cv_entry.cv_num = newapv.cvnum
                cashinbank_cv_entry.cv_date = newapv.cvdate
                cashinbank_cv_entry.bankaccount = newapv.bankaccount
            cashinbank_cv_entry.item_counter = cvdetail_item_counter
            cashinbank_cv_entry.chartofaccount = Companyparameter.objects.get(code='PDI').coa_cashinbank
            cashinbank_cv_entry.balancecode = 'C'
            cashinbank_cv_entry.creditamount = cashinbank_credit_amount
            cashinbank_cv_entry.enterby = request.user
            cashinbank_cv_entry.modifyby = request.user
            cashinbank_cv_entry.save()

            print "APV/CV successfully generated."

            if request.POST['transtype'] == 'apvtoapv':
                return redirect('/accountspayable/' + str(newapv.id) + '/update')
            elif request.POST['transtype'] == 'apvtocv':
                return redirect('/checkvoucher/' + str(newapv.id) + '/update')

    else:
        print "Something went wrong in saving APV/CV."

    return redirect('/processing_transaction/')


def lastCVNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  SUBSTRING(cvnum, 5) AS num FROM cvmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]

def lastAPNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT  SUBSTRING(apnum, 5) AS num FROM apmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
