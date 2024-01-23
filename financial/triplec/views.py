import datetime
from datetime import datetime as dt, timedelta
from operator import itemgetter
import requests
import json
import urllib2
import pandas
from django.http import JsonResponse, Http404, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string, get_template
from django.views.generic import ListView, View, DetailView, UpdateView
from django.db.models import Q, Sum, Count
from django.db import connection
from collections import OrderedDict, namedtuple
from annoying.functions import get_object_or_None
from endless_pagination.views import AjaxListView
from collections import defaultdict
from chartofaccount.models import Chartofaccount
from department.models import Department
# from designatedapprover.models import DesignatedApprover
from employee.models import Employee
from triplecvariousaccount.models import Triplecvariousaccount
from .models import TripleC
from .models import Triplecquota
from companyparameter.models import Companyparameter
from supplier.models import Supplier
from ataxcode.models import Ataxcode
from accountspayable.models import Apmain, Apdetail
from financial.utils import Render
from django.utils import timezone
from triplecbureau.models import Triplecbureau as Bureau
from triplecsection.models import Triplecsection as Section
from triplecsubtype.models import Triplecsubtype as Subtype
from triplecpublication.models import Triplecpublication as Publication
# from triplecpage.models import Triplecpage as Page
from triplecrate.models import Triplecrate as Rate
from triplecclassification.models import Triplecclassification as Classification
from triplecsupplier.models import Triplecsupplier
from . forms import ManualDataEntryForm
from django.db.models import Sum, Case, When, IntegerField


upload_size = 3
textsuccess = "text-success"
textwarning = "text-warning"
dataexists = " Data exists"
errorsavingdata = " Error saving data"

@method_decorator(login_required, name='dispatch')
class IndexView(AjaxListView):
    model = TripleC
    template_name = 'triplec/index.html'
    context_object_name = 'data_list'
    # page_template = 'triplec/index_list.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['authors'] = Supplier.objects.all().filter(isdeleted=0, triplec=1).order_by('code')
        context['bureaus'] = Bureau.objects.all().filter(isdeleted=0).order_by('code')
        context['sections'] = Section.objects.all().filter(isdeleted=0).order_by('code')
        context['publications'] = Publication.objects.all().filter(isdeleted=0).order_by('code')
        # context['pages'] = Page.objects.all().filter(isdeleted=0).order_by('code')
        context['classifications'] = Classification.objects.all().filter(isdeleted=0).order_by('code')
        context['subtypes'] = Subtype.objects.all().filter(isdeleted=0).order_by('code')
        context['rates'] = Rate.objects.all().filter(isdeleted=0).order_by('code')
        
        return context


class RetrieveView(DetailView):
    model = TripleC
    template_name = 'triplec/transaction_result.html'

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            dfrom = request.GET.get('dfrom')
            dto = request.GET.get('dto')
            type = request.GET["type"]
            author_name = request.GET["author_name"]
            status = request.GET["status"]
            bureau = request.GET["bureau"]
            section = request.GET["section"]
            page = request.GET["page"]

            triplec_data = TripleC.objects.filter(cms_issue_date__range=[dfrom, dto], isdeleted=0).order_by('pk')

            if type != '':
                triplec_data = triplec_data.filter(type=type)

            if author_name != '':
                triplec_data = triplec_data.filter(author_name__icontains=author_name)

            if status != '':
                if status == 'O_APV':
                    triplec_data = triplec_data.filter(status__icontains='O', apv_no__isnull=False).exclude(apv_no__exact='')
                elif status == 'O':
                    triplec_data = triplec_data.filter(status__icontains=status).exclude(Q(confirmation__isnull=True) | Q(confirmation=''))
                elif status == 'Reverted':
                    triplec_data = triplec_data.filter(status='E').exclude(Q(confirmation__isnull=True) | Q(confirmation=''))
                elif status == 'M':
                    triplec_data = triplec_data.filter(status='E', manual=1)
                else:
                    triplec_data = triplec_data.filter(status__icontains=status)

            if bureau != '':
                triplec_data = triplec_data.filter(bureau=bureau)

            if section != '':
                triplec_data = triplec_data.filter(section=section)

            if page != '':
                triplec_data = triplec_data.filter(Q(cms_page__icontains=page) | Q(page__icontains=page))

            context = {}
            context['triplec_data'] = triplec_data
            context['authors'] = Supplier.objects.filter(isdeleted=0, triplec=1).order_by('code')
            context['bureaus'] = Bureau.objects.filter(isdeleted=0).order_by('code')
            # context['pages'] = Page.objects.filter(isdeleted=0).order_by('code')
            context['sections'] = Section.objects.filter(isdeleted=0).order_by('code')
            context['subtypes'] = Subtype.objects.filter(isdeleted=0).order_by('code')
            context['rates'] = Rate.objects.filter(isdeleted=0).order_by('code')
            context['classifications'] = Classification.objects.filter(isdeleted=0).order_by('code')
            context['parameter'] = Companyparameter.objects.filter(isdeleted=0, status='A').first()
            context['dfrom'] = dfrom
            context['dto'] = dto
            # time benchmarking
            # start_time = dt.now()
            
            template = get_template(self.get_template_names()[0])
            html_content = template.render(context, request)
            
            # end_time = dt.now()
            # time_difference = end_time - start_time
            # print 'time', time_difference.total_seconds()
            return HttpResponse(html_content, content_type='text/html')
        else:
            return super(RetrieveView, self).get(request, *args, **kwargs)
        

@csrf_exempt
def get_ap_id(request):
    if request.method == 'POST':
        try:
            apnum = request.POST.get('apnum')
            ap_id = Apmain.objects.get(apnum=apnum).id
            response = {'result': True, 'ap_id': ap_id}
        except:
            response = {'result': False}

        return JsonResponse(response)


def fileprocess(request):
    df = pandas.read_excel(request.FILES['data_file'])

    # filter article status as 'Archived' only
    filtered = df[df['article status'] == 'Archived']
    records = filtered.to_json(orient='records')
    records = json.loads(records)

    return records


@csrf_exempt
def upload(request):
    if request.method == 'POST':
        if request.FILES['data_file'] \
                and request.FILES['data_file'].name.endswith('.xls') \
                    or request.FILES['data_file'].name.endswith('.xlsx'):
            if request.FILES['data_file']._size < float(upload_size) * 1024 * 1024:
                
                try:
                    records = fileprocess(request)
                    records_count = len(records)
                    
                    successcount = 0
                    existscount = 0
                    failedcount = 0
                    faileddata = []
                    successrecords = []
                    
                    for record in records:
                        issue_date = pandas.to_datetime(record['Issue Date'], unit='ms')
                        
                        save = savedata(record,issue_date)
                        if save:
                            successrecords.append([record])
                            successcount += 1
                        else:
                            failedcount += 1
                            faileddata.append([issue_date, record['Article ID'], record['Article Title'], record['Number Of words'], record['NumberofCharacters'], errorsavingdata, textwarning])
                    
                    if successcount == records_count:
                        result = 1 
                    elif records_count == existscount:
                        result = 2
                    elif records_count == failedcount:
                        result = 3
                    else:
                        result = 4
                    
                    return JsonResponse({
                        'result': result,
                        'success_count': successcount,
                        'records_count': records_count,
                        'failed_data': faileddata,
                        'successrecords': successrecords
                    })
                
                except:
                    return JsonResponse({
                        'result': 3
                    })
    else:
        context = {}
        return render(request, 'triplec/upload.html', context)
    

def strip_non_ascii(string):
    ''' Returns the string without non ASCII characters '''
    if string == '' or string is None:
        return str('')
    
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)


def savedata(record,issue_date):
    try:
        article_title = strip_non_ascii(record['Article Title'])
        byline = strip_non_ascii(record['Byline'])
        created_by = strip_non_ascii(record['Created by'])
       
        TripleC.objects.create(
            cms_issue_date=issue_date,
            cms_article_status='A',
            cms_publication=str(record['Publication']),
            cms_section=str(record['Section']),
            cms_page=str(record['Page']),
            cms_article_id=str(record['Article ID']),
            cms_article_title=article_title,
            cms_byline=byline,
            cms_author_name=str(record['Author name']),
            cms_created_by=created_by,
            cms_no_of_words=int(record['Number Of words']),
            cms_no_of_characters=int(record['NumberofCharacters'])
        )
        return True
    except:
        return False


@csrf_exempt
def save_batch_tagging(request):
    form_data = json.loads(request.POST.getlist('data')[0])
    result = 'success'
    for data in form_data:
        try:
            triplec = TripleC.objects.filter(pk=data['id'])
            if triplec[0].code != data['code'] or triplec[0].type != data['type']:
                triplec.update(code=data['code'], author_name=data['author'], type=data['type'], \
                    modifyby_id=request.user.id, modifydate=datetime.datetime.now())
        except:
            result = 'failed'

    return JsonResponse({
        'result': result
    })


@csrf_exempt
def tag_as_pending(request):
    if request.method == 'POST' and request.is_ajax():
        result = 'success'
        ids = json.loads(request.POST.getlist('data')[0])
        try:
            TripleC.objects.filter(id__in=ids, status='A').update(status='D') 
        except:
            result = 'failed'

    return JsonResponse({
        'result': result
    })


@csrf_exempt
def tag_as_no_payment(request):
    if request.method == 'POST' and request.is_ajax():
        result = 'success'
        ids = json.loads(request.POST.getlist('data')[0])
        try:
            TripleC.objects.filter(id__in=ids, status='A').update(status='Y') 
        except:
            result = 'failed'

    return JsonResponse({
        'result': result
    })


@csrf_exempt
def get_supplier_by_type(request):
    if request.is_ajax and request.method == 'GET':
        ccc = request.GET['ccc']
        try:
            if ccc != '':
                data = Supplier.objects.filter(isdeleted=0, triplec=1, ccc=ccc) \
                    .values('id', 'code', 'name').order_by('code')
            else:
                data = Supplier.objects.filter(isdeleted=0, triplec=1) \
                    .values('id', 'code', 'name').order_by('code')

            return JsonResponse({
                    'data': list(data), 
                    'result': 'success'
                })
        except:
            return JsonResponse({'result': 'Get supplier by type call failed'})
    else:
        return JsonResponse({'result': 'Get supplier by type call failed'})
     

@csrf_exempt
def get_supplier_by_code(request):
    data = {}
    if request.is_ajax and request.method == 'GET':
        code = request.GET['code']
        try:
            if code != '':
                supplier = Supplier.objects.values('id', 'name', 'ccc').filter(code=code)
                
                data={'result': True, 'supplier': list(supplier)}
            else:
                data={'result': False, 'message': 'Code is required'}    
        except:
           data={'result': False, 'message': 'Get supplier by code call failed'}
    else:
        data={'result': False, 'message': 'Method not allowed'}

    return JsonResponse(data)

@csrf_exempt
def get_supplier_by_name(request):
    data = {}
    if request.is_ajax and request.method == 'GET':
        name = request.GET['name']
        try:
            if name != '':
                supplier = Supplier.objects.filter(isdeleted=0, triplec=1, name=name).values('code', 'ccc')
                data={'result': True, 'supplier': list(supplier)}
            else:
                data={'result': False, 'message': 'Code is required'}
        except:
            data={'result': False, 'message': 'Get supplier by name call failed'}
    else:
        data={'result': False, 'message': 'Method not allowed'}
    return JsonResponse(data)
    

@csrf_exempt
def supplier_suggestion(request):
    data = {}
    if request.is_ajax and request.method == 'GET':
        code = request.GET['code']
        try:
            if code != '':
                supplier = Supplier.objects.get(code=code).pk
                triplecsupplier = Triplecsupplier.objects.values('bureau', 'section', 'rate__code').filter(supplier=supplier)
                rate_code = triplecsupplier.first()['rate__code'] if triplecsupplier.exists() else ''
                data={'result': True, 'triplecsupplier': list(triplecsupplier), 'rate_code': rate_code}
            else:
                data={'result': False, 'message': 'Code is required'}    
        except Exception as e:
           print e
           data={'result': False, 'message': 'Supplier suggestion call failed'}
    else:
        data={'result': False, 'message': 'Method not allowed'}

    return JsonResponse(data)


# add validation here
# validate lahat ng butas or disable fields na malaki epekto kung i-update like name
@csrf_exempt
def save_transaction_entry(request):
    if request.is_ajax and request.method == 'POST':
        try:

            triplec = TripleC.objects.filter(pk=request.POST['id'])
            
            status = 'E'
            having_quota = False
            csno_count = 0

            if triplec[0].apv_no:
                return JsonResponse({
                    'result': False,
                    'message': 'Could not be saved. This transaction is already Posted to AP - #'+ str(triplec[0].apv_no)
                })
            elif triplec[0].status == 'O':
                status = 'O'
                having_quota = Triplecquota.objects.filter(confirmation=triplec[0].confirmation, status='A', isdeleted=0).exists()
                csno_count = TripleC.objects.filter(confirmation=triplec[0].confirmation, isdeleted=0).count()
                
            if having_quota and csno_count > 0:
                return JsonResponse({
                        'result': False,
                        'message': 'Updating is not allowed to posted transaction having quota. Please use the revert process.'
                    })
            else:
                triplec.update(
                    issue_date=request.POST['issue_date'],
                    supplier_id=request.POST['supplier_id'],
                    code=request.POST['code'],
                    author_name=request.POST['author_name'],
                    type=request.POST['type'],
                    subtype=request.POST['subtype'],
                    bureau=request.POST['bureau'],
                    section=request.POST['section'],
                    article_title=request.POST['article_title'],
                    byline=request.POST['byline'],
                    no_ccc=request.POST['no_of_ccc'],
                    no_items=request.POST['no_of_items'],
                    page=str(request.POST['page_no']).upper(),
                    no_of_words=request.POST['no_of_words'],
                    no_of_characters=request.POST['no_of_characters'],
                    length1=request.POST['length1'],
                    length2=request.POST['length2'],
                    length3=request.POST['length3'],
                    length4=request.POST['length4'],
                    width1=request.POST['width1'],
                    width2=request.POST['width2'],
                    width3=request.POST['width3'],
                    width4=request.POST['width4'],
                    total_size=request.POST['total_size'],
                    rate_code=request.POST['rate_code'],
                    amount=request.POST['amount'],
                    remarks=request.POST['remarks'],
                    status=status,
                    modifyby_id=request.user.id, 
                    modifydate=datetime.datetime.now()
                )

                data = {
                    'result': True
                }

        except Exception as e:
            data = {
                    'result': False,
                    'message': 'Unable to save this transaction. '+ str(e)
                }
    else:
        data = {
                'result': False,
                'message': 'Method not allowed'
            }
        
    return JsonResponse(data)


@csrf_exempt
def manual_save_transaction_entry(request):
    if request.is_ajax and request.method == 'POST':
        try:
            
            form = ManualDataEntryForm(request.POST)
            if form.is_valid():

                instance = form.save(commit=False) 
                
                # include for default cms data to avoid error in other functions
                instance.cms_issue_date=request.POST['issue_date']
                instance.cms_publication='Inquirer'
                instance.cms_page=str(request.POST['page']).upper()
                instance.cms_article_title=request.POST['article_title']

                if not request.POST['bureau']:
                    instance.bureau=None
                else:
                    bureau_instance = Bureau.objects.get(pk=int(request.POST['bureau']))
                    instance.bureau=bureau_instance
                
                instance.page=str(request.POST['page']).upper()
                instance.byline=request.POST['byline']
                instance.remarks=request.POST['remarks']
                instance.status='E' # Ready for Posting
                instance.modifyby_id=request.user.id
                instance.modifydate=datetime.datetime.now()
                instance.manual=1

                instance.save()

                data = {'result': True}
            else:
                data = {'result': False, 
                        'message': form.errors.as_text()
                    }

        except Exception as e:
            data = {
                    'result': False,
                    'message': 'Unable to save this transaction. ' + str(e)
                }
    else:
        data = {
                'result': False,
                'message': 'Method not allowed'
            }
        
    return JsonResponse(data)


@csrf_exempt
def revert_transaction(request):
    if request.is_ajax and request.method == 'POST':
        try:
            # Note: if CS contains quota, set all associated transactions to 'E'
            # else if no quota for the CS, only the reverted transaction will be 'E'
            # CS number shoud remain as is

            triplec = TripleC.objects.filter(pk=request.POST['id'])

            if triplec[0].status == 'O' and not triplec[0].apv_no:
                # Posted CS
                confirmation = triplec[0].confirmation
                has_quota = Triplecquota.objects.filter(confirmation=confirmation, status='A', isdeleted=0).exists()

                if has_quota:

                    transactions = TripleC.objects.filter(confirmation=confirmation)
                    for transaction in transactions:
                        transaction.status = 'E'
                        transaction.modifyby = request.user
                        transaction.modifydate = datetime.datetime.now()
                        transaction.save()

                    # add Cancelled - C to CS number, isdeleted = 1
                    Triplecquota.objects.filter(confirmation=confirmation).update(
                        confirmation = confirmation,
                        status='C',
                        isdeleted=1,
                        modifyby_id=request.user.id,
                        modifydate=datetime.datetime.now()
                    )
                else:
                    triplec.update(
                        status='E',
                        modifyby_id=request.user.id,
                        modifydate=datetime.datetime.now()
                    )
                data = {
                    'result': True,
                    'message': 'Revert process successful. You may now update the transaction.'
                }
            elif triplec[0].status == 'E':
                data = {
                    'result': False,
                    'message': 'This transaction is already reverted as Ready for Posting.'
                }
            else:
                data = {
                    'result': False,
                    'message': 'The transaction is already posted to APV: AP#'+ str(triplec[0].apv_no)
                }
        except Exception as e:
            data = {
                'result': False,
                'message': 'An error occured: '+ str(e)
            }
    else:
        data = {
                'result': False,
                'message': 'Method not allowed'
            }
        
    return JsonResponse(data)


@csrf_exempt
def having_quota(request):
    if request.is_ajax and request.method == 'POST':
        try:
            having_quota = Triplecquota.objects.filter(confirmation=request.POST['csno'], status='A', isdeleted=0).exists()
            csno_count = TripleC.objects.filter(confirmation=request.POST['csno'], isdeleted=0).count()
            data = {
                    'result': True,
                    'message': 'Success',
                    'having_quota': having_quota,
                    'csno_count': csno_count
                }
        except Exception as e:
            data = {
                'result': False,
                'message': 'An error occured: '+ str(e)
            }
    else:
        data = {
                'result': False,
                'message': 'Method not allowed'
            }
        
    return JsonResponse(data)


def get_confirmation(year):
    try:
        record = TripleC.objects.exclude(confirmation__isnull=True).exclude(confirmation__exact='').order_by('-confirmation')[:1]
        if record.exists():
            last_cs = str(record[0].confirmation)
            # Get the maximum last six digits from the filtered record
            series = last_cs[-6:]
            confirmation_number = str(year) + str(series)
        else:
            # first cs
            confirmation_number = str(year) + '000001'

        return confirmation_number
        
    except Exception:
        # fault tolerance - for datafixing
        return '1111111111'
    
    # old version: sorted by year and will reset series each new year to 000001
    # try:
    #     year = str(year)
    #     matching_records = TripleC.objects.filter(confirmation__startswith=year)
        
    #     if matching_records:
    #         # Get the maximum last six digits from the filtered records
    #         max_last_six_digits = matching_records.aggregate(max_last_six=Max('confirmation'))['max_last_six'][-6:]
            
    #         last_cs = year + str(max_last_six_digits)

    #     else:
    #         # first cs
    #         last_cs = year + '000001'
        
    #     return last_cs
        
    # except Exception:
    #     # fault tolerance - for datafixing
    #     return '0000000000'


@method_decorator(login_required, name='dispatch')
class ProcessTransactionView(ListView):
    model = TripleC
    template_name = 'triplec/process_transaction/index.html'
    context_object_name = 'data_list'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplec.process_transaction_triplec'):
            raise Http404
        return super(ListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
       context = super(ProcessTransactionView, self).get_context_data(**kwargs)
       context['triplec'] = TripleC.objects.all().filter(isdeleted=0).order_by('code')
       context['authors'] = Supplier.objects.all().filter(isdeleted=0, triplec=1)
       context['classifications'] = Classification.objects.all().filter(isdeleted=0)
       
       return context


@method_decorator(login_required, name='dispatch')
class GenerateProcessTransaction(View):
    def get(self, request):
        try:
            dfrom = request.GET['dfrom'] or ''
            dto = request.GET['dto'] or ''
            author_name = request.GET['author_name'] or ''
            classification = request.GET['classification'] or ''

            if dfrom != '' and dto != '':
                triplec_data = TripleC.objects.filter(issue_date__range=[dfrom, dto], status='E', isdeleted=0)\
                    .values('code', 'type')
                
            elif dfrom != '' and dto == '':
                triplec_data = TripleC.objects.filter(issue_date=dfrom, status='E', isdeleted=0)\
                    .values('code', 'type')
                
            elif dfrom == '' and dto != '':
                triplec_data = TripleC.objects.filter(issue_date=dto, status='E', isdeleted=0)\
                    .values('code', 'type')
            else:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'Transaction date is required'
                })
            
            if author_name != '':
                triplec_data = triplec_data.filter(author_name=author_name)

            if classification != '':
                triplec_data = triplec_data.filter(type=classification)

            triplec_data = triplec_data.annotate(total=Sum('amount'), transactions=Count('pk')).order_by('code')
            
            param = {}
            for key in range(len(triplec_data)):
                
                if dfrom != '' and dto != '':
                    param[key] = TripleC.objects.filter(issue_date__range=[dfrom, dto], status='E', isdeleted=0, code=triplec_data[key]['code'], type=triplec_data[key]['type'])
                elif dfrom != '' and dto == '':
                    param[key] = TripleC.objects.filter(issue_date=dfrom, status='E', isdeleted=0, code=triplec_data[key]['code'], type=triplec_data[key]['type'])
                elif dfrom == '' and dto != '':
                    param[key] = TripleC.objects.filter(issue_date=dto, status='E', isdeleted=0, code=triplec_data[key]['code'], type=triplec_data[key]['type'])
            
            data = {
                'status': 'success',
                'viewhtml': render_to_string('triplec/process_transaction/generate.html', {"triplec_data": param})
            }

            return JsonResponse(data)
        except:
            return JsonResponse({
                'status': 'failed',
                'message': 'An error occured'
            })


@csrf_exempt
def transaction_posting(request):
    if request.method == 'POST':
        try:
            transactions = json.loads(request.POST.getlist('data')[0])
            
            olditem = ''
            newitem = ''
            existing = []
            confirmation_numbers = []

            for item in transactions:

                newitem = item['code']+'sep'+item['type']

                year = dt.strptime(item['issue_date'], "%Y-%m-%d").year
                csno = get_confirmation(year)
                
                try:
                    triplec = TripleC.objects.filter(pk=item['pk'])
                    
                    if triplec[0].status != 'O':

                        kwargs = {
                            'date_posted': datetime.datetime.now(), 
                            'status': 'O', 
                            'modifyby_id': request.user.id,
                            'modifydate': datetime.datetime.now(),
                        }

                        if triplec[0].confirmation:
                            confirmation_numbers.append(triplec[0].confirmation)

                        elif newitem != olditem:
                            new_csno = int(csno) + 1
                            kwargs.update(
                                confirmation=new_csno,
                            )
                            olditem = newitem
                            confirmation_numbers.append(new_csno)

                        else:
                            kwargs.update(
                                confirmation=csno, 
                            )

                        triplec.update(**kwargs)

                    else:
                        existing.append([triplec[0].confirmation, newitem])

                except:
                    response = {
                        'result': False,
                        'message': 'Unable to save transaction for '+ item['code'] + '. Processing stopped, please retry.'
                    }

            if not existing:
                confirmation_numbers = list(dict.fromkeys(confirmation_numbers))
                success_quota = process_quota(request, confirmation_numbers)
                if success_quota == 'success':
                    response = {
                        'result': True,
                        'confirmation_numbers': confirmation_numbers
                    }
                else:
                    response = {
                        'result': False,
                        'message': 'An internal error: ' + str(success_quota)
                    }
            else:   
                response = {
                    'result': 'existing',
                    'message': 'Already posted transaction(s) has been detected.',
                    'existing': existing
                }
            
        except:
            response = {
                'result': False,
                'message': 'An internal error occured while processing your transaction.'
            }
    else:
        response = {
            'result': False,
            'message': 'Method not allowed'
        }

    return JsonResponse(response)


def process_quota(request, confirmation_numbers):
    if confirmation_numbers:

        string_errors = ""
        csno_errors = ""
        has_exception = False

        for confirmation_number in confirmation_numbers:
            try:
                quota = Triplecquota.objects.filter(confirmation=confirmation_number)
                transactions = TripleC.objects.filter(confirmation=confirmation_number, type='COR')

                if transactions:
                    num_items=0
                    total_size=0
                    photos=0
                    num_photos=0
                    num_articles=0
                    num_type_breaking_news=0
                    num_section_breaking_news=0
                    num_breaking_news=0

                    num_items = sum(transaction.no_items for transaction in transactions) # PHOTOS
                    total_size = sum(transaction.total_size for transaction in transactions) # ARTICLE and used for BREAKING NEWS
                    
                    additional = Triplecvariousaccount.objects.filter(isdeleted=0, type='addtl')
                    
                    # P - Photo
                    photos = transactions.filter(subtype=11).count()
                    num_photos = max(photos, num_items)

                    # A - Article
                    num_articles = transactions.filter(subtype=10).count()

                    num_type_breaking_news = transactions.filter(subtype__code__icontains='INSNB').count()
                    num_section_breaking_news = transactions.filter(section__code__icontains='INSNB').count()
                    num_breaking_news = max(num_type_breaking_news, num_section_breaking_news)

                    # used to create new quota
                    kwargs = {
                        'confirmation': confirmation_number,
                        'no_item': num_photos,
                        'enterby_id': request.user.id,
                        'enterdate': datetime.datetime.now(),
                    }
                    # Photo & Article
                    if num_photos >= 8 and num_articles > 0 and total_size >= 50:
                        transpo = additional.get(code='TRANSPO').amount
                        transpo2 = additional.get(code='TRANSPO2').amount
                        cellcard = additional.get(code='TEL').amount

                        # used to update existing quota
                        photo_and_article_quota = {
                            'type': 'A,P',
                            'transportation_amount': transpo,
                            'transportation2_amount': transpo2,
                            'cellcard_amount': cellcard,
                            'status': 'A',
                            'isdeleted': 0,
                            'modifyby_id': request.user.id,
                            'modifydate': datetime.datetime.now(),
                        }

                        if quota.exists():
                            quota.update(**photo_and_article_quota)
                        else:
                            kwargs.update(photo_and_article_quota)
                            Triplecquota.objects.create(**kwargs)

                    # Photo
                    elif num_photos >= 8:
                        transpo = additional.get(code='TRANSPO2').amount

                        # used to update existing quota
                        photo_quota = {
                            'type': 'P',
                            'transportation_amount': transpo,
                            'status': 'A',
                            'isdeleted': 0,
                            'modifyby_id': request.user.id,
                            'modifydate': datetime.datetime.now(),
                        }

                        if quota.exists():
                            quota.update(**photo_quota)
                        else:
                            kwargs.update(photo_quota)
                            Triplecquota.objects.create(**kwargs)

                    # Article
                    elif num_articles > 0 and total_size >= 50:
                        transpo = additional.get(code='TRANSPO').amount
                        cellcard = additional.get(code='TEL').amount

                        # used to update existing quota
                        article_quota = {
                            'type': 'A',
                            'transportation_amount': transpo,
                            'cellcard_amount': cellcard,
                            'status': 'A',
                            'isdeleted': 0,
                            'modifyby_id': request.user.id,
                            'modifydate': datetime.datetime.now(),
                        }

                        if quota.exists():
                            quota.update(**article_quota)
                        else:
                            kwargs.update(article_quota)
                            Triplecquota.objects.create(**kwargs)
                    
                    # BREAKING NEWS
                    # total_size = number of peices
                    elif num_breaking_news > 0 and total_size >= 50:
                        transpo3 = additional.get(code='TRANSPO3').amount
                        cellcard = additional.get(code='TEL').amount

                        # used to update existing quota
                        breaking_news_quota = {
                            'type': 'INSNB',
                            'transportation_amount': transpo3,
                            'cellcard_amount': cellcard,
                            'status': 'A',
                            'isdeleted': 0,
                            'modifyby_id': request.user.id,
                            'modifydate': datetime.datetime.now(),
                        }

                        if quota.exists():
                            quota.update(**breaking_news_quota)
                        else:
                            kwargs.update(breaking_news_quota)
                            Triplecquota.objects.create(**kwargs)

            except Exception as e:
                has_exception = True
                csno_errors += str(confirmation_number)  + ", "
                string_errors += str(e) + ", "
        if has_exception:
            result = "Unable to process the quota of ff: " + csno_errors + string_errors
        else:
            result = 'success'
    else:
        result = 'No CS numbers to process.'
    return result
          

def print_cs(request):

    urlquery = json.loads(request.GET['q'])
    is_batch = request.GET.get('batch')
    parameter = {}
    info = {}
    companyparameter = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
    
    data_list = []

    if is_batch:
        for confirmation in urlquery:
            try:
                ids = TripleC.objects.filter(confirmation=confirmation, status='O', isdeleted=0).values('pk')
                for id in ids:
                    data_list.append(TripleC.objects.values('pk', 'code', 'author_name', 'confirmation', 'date_posted').get(pk=id['pk'], status='O', isdeleted=0))
            except Exception as e:
                print 'confirmation', confirmation, e
    else:
        for triplec_id in urlquery:
            try:
                data_list.append(TripleC.objects.values('pk', 'code', 'author_name', 'confirmation', 'date_posted').get(pk=triplec_id, status='O', isdeleted=0))
            except Exception as e:
                print 'triplec_id', triplec_id, e

    sorted_data_list = sorted(data_list, key=lambda x: x['author_name'])
    grouped_dict = OrderedDict()

    for item in sorted_data_list:
        confnum = item['confirmation']
        if confnum not in grouped_dict:
            grouped_dict[confnum] = []
        grouped_dict[confnum].append(item['pk'])
        
    xnum = 0
    for csno, ids in grouped_dict.items():

        csno = str(csno)
        parameter[xnum] = {}
        details = {}
        batch_cs = TripleC.objects.filter(confirmation=csno, status='O', isdeleted=0)

        parameter[xnum]['main'] = batch_cs.first()

        has_quota = get_object_or_None(Triplecquota, confirmation=csno, status='A', isdeleted=0)
        
        quota_amount = 0
        with_additional = False
        if has_quota:
            transpo = has_quota.transportation_amount
            transpo2 = has_quota.transportation2_amount
            cellcard = has_quota.cellcard_amount

            quota_amount = transpo + transpo2 + cellcard
            with_additional = True

            parameter[xnum]['transportation_amount'] = transpo
            parameter[xnum]['transportation2_amount'] = transpo2
            parameter[xnum]['cellcard_amount'] = cellcard
        
        atc_id = Supplier.objects.get(code=parameter[xnum]['main'].code).atc_id
        rate = Ataxcode.objects.get(pk=atc_id).rate

        subtotal = batch_cs.aggregate(subtotal=Sum('amount'))
        subtotal = float(subtotal['subtotal'])
        total = subtotal + float(quota_amount)

        ewt = 0
        is_ewt = True
        tax = 0
        wtax = 0
        # RANK & FILE or default to 25% wtax
        wtax_rate = companyparameter.ranknfile_percentage_tax
        if rate:
            ewt = percentage(float(rate), total)
            tax = ewt
        else:
            is_ewt = False
            if parameter[xnum]['main'].supplier_id is not None:

                employeenumber = get_object_or_None(Employee, supplier=parameter[xnum]['main'].supplier_id)
                if employeenumber:
                    withholding_tax = get_withholding_tax(employeenumber.code, companyparameter.base_url_201)
                    employee_level = withholding_tax[0].get('employee_level', None)

                    if employee_level and employee_level != "RANK & FILE":
                        wtax_rate = companyparameter.officer_percentage_tax
                        
                if not parameter[xnum]['main'].wtax:
                    save_wtax(xnum, wtax_rate)

            wtax = percentage(float(wtax_rate), total)
            tax = wtax
                
        net = total - tax
        
        parameter[xnum]['size'] = batch_cs.aggregate(total_size=Sum('total_size'))
        parameter[xnum]['with_additional'] = with_additional
        parameter[xnum]['ataxrate'] = rate
        parameter[xnum]['wtax_rate'] = wtax_rate
        parameter[xnum]['subtotal'] = subtotal
        parameter[xnum]['total'] = total
        parameter[xnum]['is_ewt'] = is_ewt
        parameter[xnum]['ewt'] = ewt
        parameter[xnum]['wtax'] = wtax
        parameter[xnum]['net'] = net

        trans_ids = []
        for id in ids:
            trans_ids.append(id)

        details = TripleC.objects.filter(pk__in=trans_ids).order_by('issue_date')
        parameter[xnum]['details'] = details

        xnum += 1
    
    info['logo'] = request.build_absolute_uri('/static/images/pdi.jpg')
    info['parameter'] = companyparameter
    
    return render(request, 'triplec/process_transaction/print_cs.html', {'info': info, 'parameter': parameter})


def get_withholding_tax(employeenumber, base_url):
    endpoint = '/api/employees'
    url = base_url + endpoint
    params = {
        'access_key': 'acf42e4acf8fe9f39e382e0a255d88ce1b59900b',
        'employeenumber': employeenumber
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data
    
    return [{}]


def percentage(percent, whole):
    if whole:
        return (percent * whole) / 100.0
    
    return 0.00


def save_wtax(csno, wtax_rate):
    TripleC.objects.filter(confirmation=csno).update(wtax=int(wtax_rate))


@method_decorator(login_required, name='dispatch')
class ReportView(ListView):
    model = TripleC
    template_name = 'triplec/report/index.html'
    context_object_name = 'data_list'

    def dispatch(self, request, *args, **kwargs):
        return super(ListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportView, self).get_context_data(**kwargs)
        context['triplec'] = TripleC.objects.all().filter(isdeleted=0).order_by('code')
        context['authors'] = Supplier.objects.all().filter(isdeleted=0, triplec=1)
        context['bureaus'] = Bureau.objects.all().filter(isdeleted=0).order_by('code')
        context['sections'] = Section.objects.all().filter(isdeleted=0).order_by('code')
       
        return context
    

@method_decorator(login_required, name='dispatch')
class GeneratePDF(View):
    def get(self, request):

        company = Companyparameter.objects.filter(status='A').first()
        datalist = []
        
        if request.method == 'GET' and request.GET['blank'] != '1':

            dfrom = request.GET['from']
            dto = request.GET['to']

            author_code = request.GET['author']
            type = request.GET['type']
            bureau = request.GET['bureau']
            section = request.GET['section']
            report_type = request.GET['report_type']
            report_title = request.GET['report_title']
            status = request.GET['status']
            grand_total = 0
            
            filter_kwargs = {'isdeleted': 0}

            if status in ('O', 'E'):
                filter_kwargs['issue_date__range' if status == 'O' else 'cms_issue_date__range'] = [dfrom, dto]
                filter_kwargs['status'] = status

            # Summary
            if report_type == 'R':
                q = TripleC.objects.filter(**filter_kwargs)\
                    .values('id', 'code', 'author_name', 'subtype_id', 'amount')\
                    .annotate(totalamount=Sum('amount'))\
                    .annotate(totalitems=Sum('no_items'))\
                    .order_by('code')
                
                # subtype_id of 10 = Article
                # Annotate the queryset to calculate the 'totalarticles' based on the 'subtype_id' field
                q = q.annotate(totalarticles=Sum(
                    Case(
                        # When 'type' is 10, assign 1 to the 'totalarticles' field
                        When(subtype_id=10, then=1),
                        default=0,
                        output_field=IntegerField(),
                    )
                ))

                if author_code:
                    q = q.filter(code=author_code)

                if type:
                    q = q.filter(type=type)

                if bureau:
                    q = q.filter(bureau=bureau)

                if section:
                    q = q.filter(section=section)

                datalist = q
                grand_total = q.aggregate(grand_total=Sum('totalamount'))['grand_total']

            # Fixed format - Yearly
            elif report_type == 'Y':
                # name, issue_date, section, title, amount
                q = TripleC.objects.filter(**filter_kwargs) \
                        .values('id', 'issue_date', 'author_name', 'section__description', 'article_title', 'amount') \
                        .annotate(subtotal=Sum('amount')) \
                        .order_by('code')
                
                if author_code:
                    q = q.filter(code=author_code)

                if type:
                    q = q.filter(type=type)

                if bureau:
                    q = q.filter(bureau=bureau)

                if section:
                    q = q.filter(section=section)

                datalist = {}
                for transaction in q:
                    author_name = transaction['author_name']
                    if author_name not in datalist:
                        datalist[author_name] = {
                            'author_name': author_name,
                            'transactions': [],
                            'subtotal': 0,
                        }
                    datalist[author_name]['transactions'].append(transaction)
                    datalist[author_name]['subtotal'] += transaction['subtotal']
                    grand_total += transaction['subtotal']

                # print 'hoy', datalist
            dates = 'AS OF ' + datetime.datetime.strptime(dfrom, '%Y-%m-%d').strftime('%b. %d, %Y')\
                + ' TO ' + datetime.datetime.strptime(dto, '%Y-%m-%d').strftime('%b. %d, %Y')

            context = {
                "today": timezone.now(),
                "company": company,
                "data_list": datalist,
                "username": request.user,
                "report_type": report_type,
                "grand_total": grand_total,
                "heading": {
                    'dates': dates,
                    'report_title': report_title,
                    'logo': request.build_absolute_uri('/static/images/pdi.jpg'),
                }
            }
        else:
             context = {
                "today": timezone.now(),
                "company": company,
                "username": request.user,
                "heading": {
                    'logo': request.build_absolute_uri('/static/images/pdi.jpg'),
                }
            }
             
        return Render.render('triplec/report/pdf.html', context)
        

def get_apnum(pdate):
    apnumlast = lastAPNumber('true')
    latestapnum = str(apnumlast[0])
    apnum = pdate[:4]
    last = str(int(latestapnum) + 1)
    zero_addon = 6 - len(last)
    for num in range(0, zero_addon):
        apnum += '0'
    apnum += last

    return apnum
    

def apv_particulars(issue_dates, particulars_quota):
    date_groups = defaultdict(list)
    for item in issue_dates:
        date_obj = item['issue_date']
        month_name = date_obj.strftime('%b.').upper()
        day = date_obj.day
        year = date_obj.year
        date_groups[(month_name, year)].append(day)

    formatted_dates = []
    for (month, year), day_list in date_groups.items():
        day_str = ', '.join(str(day) for day in sorted(set(day_list)))
        formatted_dates.append("{} {}, {}".format(month, day_str, year))

    particulars = ', '.join(formatted_dates)
    if particulars_quota:
        particulars = particulars + particulars_quota
    return particulars


def validate_autoap_check(data_list):

    validation_list = []
    result = True

    already_posted = 0

    grouped_list = defaultdict(list)
    for item in data_list:
        grouped_list[
            item['confirmation']
        ].append(
            [item['pk']]
        )
        
    for csno, ids in grouped_list.items():
        errors_list = []
        try:

            triplec = TripleC.objects.filter(confirmation=csno,status='O').first()
            if triplec.apv_no is not None and triplec.apv_no != "":
                already_posted += 1
            else:
                
                if not triplec.supplier_id:
                    errors_list.append({'Supplier ID is empty.'})
                else:
                    supplier = Supplier.objects.get(pk=triplec.supplier_id)

                    if not supplier:
                        errors_list.append({'Triple C supplier #'+str(triplec.supplier_id)+' does not exist in Supplier.'})
                    else:
                        
                        entries = []

                        triplec_supplier = Triplecsupplier.objects.filter(supplier=supplier.id).first()
                        if not triplec_supplier:
                            errors_list.append({'Supplier '+str(supplier.name)+' does not exist in Triplecsupplier.'})
                        else:
                            department = get_object_or_None(Department, pk=triplec_supplier.department_id)
                            if not department:
                                errors_list.append({'triplec_supplier Department ID '+str(triplec_supplier.department_id)+' does not exist in Department.'})
                            
                            else:
                                expchart = get_object_or_None(Chartofaccount, pk=department.expchartofaccount_id)
                                if not expchart:
                                    errors_list.append({'Department COA ID '+str(department.expchartofaccount_id)+' does not exist in Chartofaccount.'})
                                else:
                                    # identify chartofaccount of each transaction
                                    for id in ids:
                                        expc = get_expc(expchart, id)
                                        entries.append({'id':id, 'expc':expc})

                                    grouped_entries = defaultdict(list)

                                    for item in entries:
                                        grouped_entries[
                                            item['expc']
                                        ].append(
                                            item['id']
                                        )

                                    has_quota = get_object_or_None(Triplecquota, confirmation=csno, status='A', isdeleted=0)
                                    print 'has_quota', has_quota, csno
                                    if has_quota:
                                        # quota - transpo
                                        transpo = get_object_or_None(Triplecvariousaccount, code='TRANSPO', type='addtl', isdeleted=0)
                                        if transpo:
                                            
                                            if expchart.accountcode == '5100000000':
                                                transpoexpc = transpo.chartexpcostofsale_id
                                            elif expchart.accountcode == '5200000000':
                                                transpoexpc = transpo.chartexpgenandadmin_id
                                            else:
                                                transpoexpc = transpo.chartexpsellexp_id

                                            if not transpoexpc:
                                                errors_list.append({'Quota variousaccount chartexp does not exist in TRANSPO.'})

                                        # quota - transpo2
                                        transpo2 = get_object_or_None(Triplecvariousaccount, code='TRANSPO2', type='addtl', isdeleted=0)
                                        if transpo2:
                                            
                                            if expchart.accountcode == '5100000000':
                                                transpoexpc = transpo2.chartexpcostofsale_id
                                            elif expchart.accountcode == '5200000000':
                                                transpoexpc = transpo2.chartexpgenandadmin_id
                                            else:
                                                transpoexpc = transpo2.chartexpsellexp_id

                                            if not transpoexpc:
                                                errors_list.append({'Quota variousaccount chartexp does not exist in TRANSPO2.'})

                                        # quota - transpo3
                                        transpo2 = get_object_or_None(Triplecvariousaccount, code='TRANSPO3', type='addtl', isdeleted=0)
                                        if transpo2:
                                            
                                            if expchart.accountcode == '5100000000':
                                                transpoexpc = transpo2.chartexpcostofsale_id
                                            elif expchart.accountcode == '5200000000':
                                                transpoexpc = transpo2.chartexpgenandadmin_id
                                            else:
                                                transpoexpc = transpo2.chartexpsellexp_id

                                            if not transpoexpc:
                                                errors_list.append({'Quota variousaccount chartexp does not exist in TRANSPO3.'})

                                        # quota - cellcard
                                        cellcard = get_object_or_None(Triplecvariousaccount, code='TEL', type='addtl', isdeleted=0)
                                        if cellcard:

                                            if expchart.accountcode == '5100000000':
                                                cellcardexpc = cellcard.chartexpcostofsale_id
                                            elif expchart.accountcode == '5200000000':
                                                cellcardexpc = cellcard.chartexpgenandadmin_id
                                            else:
                                                cellcardexpc = cellcard.chartexpsellexp_id

                                            if not cellcardexpc:
                                                errors_list.append({'Quota variousaccount chartexp does not exist in TEL.'})

                                    atc_id = get_object_or_None(Supplier, pk=supplier.id)
                                    atc_id = atc_id.atc_id if atc_id is not None else None
                                    if not atc_id:
                                        errors_list.append({'atc_id of Supplier ID '+str(supplier.id)+' does not exist in Supplier.'})
                                    else:
                                        rate = get_object_or_None(Ataxcode, pk=atc_id)
                                        rate = rate.rate if rate is not None else None
                                        if not rate:
                                            if rate != 0:
                                                errors_list.append({'rate of ATC ID '+str(atc_id)+' does not exist in Ataxcode.'})

                                    companyparameter = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
                                    if not companyparameter.coa_ewtax_id or not companyparameter.coa_wtax_id:
                                        errors_list.append({'coa_ewtax_id or coa_wtax_id does not exist in Company Parameter.'})
        except Exception as e:
            print 'validation error: ', e
            errors_list.append({'Exception: '+ str(e)})

        if errors_list:
            validation_list.append({'csno': csno, 'errors_list': errors_list})
            result = False

    return {'result': result, 'validation_list': validation_list}

    
@csrf_exempt
def goposttriplec(request):

    if request.method == 'POST':

        pkslist = request.POST.getlist('ids[]')
        postdate = request.POST['postdate']
        pdate = datetime.datetime.strptime(postdate, '%m/%d/%Y').strftime('%Y-%m-%d')

        data_list = TripleC.objects.filter(pk__in=pkslist,isdeleted=0,status='O').values('pk', 'confirmation')
        validated = validate_autoap_check(data_list)

        grouped_list = defaultdict(list)

        for item in data_list:
            grouped_list[
                item['confirmation']
            ].append(
                [item['pk']]
            )
        print validated, validated['result']
        if grouped_list and validated['result']:
            already_posted = 0
            total_trans = 0
            successful_trans = 0
            exception = ''

            for csno, ids in grouped_list.items():
                
                apnum = get_apnum(pdate)
                billingremarks = ''
                
                try:
                    total_trans += 1
                    triplec_all = TripleC.objects.filter(confirmation=csno,status='O')
                    triplec = triplec_all.first()
                    
                    if triplec.apv_no is not None and triplec.apv_no != "":
                        already_posted += 1
                    else:
                        supplier = Supplier.objects.get(pk=triplec.supplier_id)
                        various_account = Triplecvariousaccount.objects
                        duedate = add_days_to_date(pdate, 90)

                        # designatedapprover = DesignatedApprover.objects.get(pk=2).approver_id
                        main = Apmain.objects.create(
                            apnum = apnum,
                            apdate = pdate,
                            aptype_id = 14, # Non-UB
                            apsubtype_id = 16, # Triple C
                            branch_id = 5, # Head Office
                            inputvattype_id = 3, # Service
                            creditterm_id = 2, # 90 Days 2
                            payee_id= supplier.id,
                            payeecode= supplier.code,
                            payeename= supplier.name,
                            vat_id = 8, # NA 8
                            vatcode = 'VATNA', # NA 8
                            vatrate = 0,
                            duedate = duedate,
                            refno = triplec.confirmation,
                            currency_id = 1,
                            fxrate = 1,
                            designatedapprover_id = 225, # Arlene Astapan
                            approverremarks = 'For approval from Triple C Posting',
                            responsedate = datetime.datetime.now(),
                            apstatus = 'F',
                            enterby_id = request.user.id,
                            enterdate = datetime.datetime.now(),
                            modifyby_id = request.user.id,
                            modifydate = datetime.datetime.now()
                        )

                        counter = 0
                        amount = 0
                        entries = []

                        triplec_supplier = Triplecsupplier.objects.filter(supplier=supplier.id).first()
                        department = Department.objects.get(pk=triplec_supplier.department_id)
                        expchart = Chartofaccount.objects.get(pk=department.expchartofaccount_id)

                        # identify chartofaccount of each transaction
                        for id in ids:
                            expc = get_expc(expchart, id)
                            entries.append({'id':id, 'expc':expc})

                        grouped_entries = defaultdict(list)

                        for item in entries:
                            grouped_entries[
                                item['expc']
                            ].append(
                                item['id']
                            )
                        
                        for coa, entry_ids in grouped_entries.items():
                            # sort transactions by similar chartofaccount
                            idlist = []
                            for i in entry_ids:
                                idlist.append(i[0])
                            
                            tc = TripleC.objects.filter(pk__in=idlist).aggregate(sum_amount=Sum('amount'))

                            TripleC.objects.filter(pk__in=idlist).update(
                                apv_no = main.apnum,
                                date_apv = main.apdate,
                            )

                            counter += 1
                            Apdetail.objects.create(
                                apmain_id = main.id,
                                ap_num = main.apnum,
                                ap_date = main.apdate,
                                item_counter = counter,
                                debitamount = tc['sum_amount'],
                                creditamount = '0.00',
                                balancecode = 'D',
                                amount = tc['sum_amount'],
                                chartofaccount_id = coa,
                                department_id = department.id,
                                status='A',
                                enterby_id = request.user.id,
                                enterdate = datetime.datetime.now(),
                                modifyby_id = request.user.id,
                                modifydate = datetime.datetime.now()
                            )
                            amount += tc['sum_amount']
                            
                        has_quota = get_object_or_None(Triplecquota, confirmation=csno, status='A', isdeleted=0)

                        particulars_quota = ''
                        has_transpo = False
                        has_cellcard = False
                        if has_quota:

                            # quota - transpo
                            if has_quota.transportation_amount:
                                transpo = various_account.get(code='TRANSPO', type='addtl', isdeleted=0)
                                if transpo:
                                    
                                    if expchart.accountcode == '5100000000':
                                        transpoexpc = transpo.chartexpcostofsale_id
                                    elif expchart.accountcode == '5200000000':
                                        transpoexpc = transpo.chartexpgenandadmin_id
                                    else:
                                        transpoexpc = transpo.chartexpsellexp_id
                                        
                                    counter += 1
                                    Apdetail.objects.create(
                                        apmain_id = main.id,
                                        ap_num = main.apnum,
                                        ap_date = main.apdate,
                                        item_counter = counter,
                                        debitamount = has_quota.transportation_amount,
                                        creditamount = '0.00',
                                        balancecode = 'D',
                                        amount = has_quota.transportation_amount,
                                        chartofaccount_id = transpoexpc,
                                        department_id = department.id,
                                        status='A',
                                        enterby_id = request.user.id,
                                        enterdate = datetime.datetime.now(),
                                        modifyby_id = request.user.id,
                                        modifydate = datetime.datetime.now()
                                    )
                                    amount += has_quota.transportation_amount
                                    has_transpo = True

                            # quota - transpo2
                            if has_quota.transportation2_amount:
                                transpo2 = various_account.get(code='TRANSPO2', type='addtl', isdeleted=0)
                                if transpo2:
                                    
                                    if expchart.accountcode == '5100000000':
                                        transpoexpc = transpo2.chartexpcostofsale_id
                                    elif expchart.accountcode == '5200000000':
                                        transpoexpc = transpo2.chartexpgenandadmin_id
                                    else:
                                        transpoexpc = transpo2.chartexpsellexp_id
                                        
                                    counter += 1
                                    Apdetail.objects.create(
                                        apmain_id = main.id,
                                        ap_num = main.apnum,
                                        ap_date = main.apdate,
                                        item_counter = counter,
                                        debitamount = has_quota.transportation2_amount,
                                        creditamount = '0.00',
                                        balancecode = 'D',
                                        amount = has_quota.transportation2_amount,
                                        chartofaccount_id = transpoexpc,
                                        department_id = department.id,
                                        status='A',
                                        enterby_id = request.user.id,
                                        enterdate = datetime.datetime.now(),
                                        modifyby_id = request.user.id,
                                        modifydate = datetime.datetime.now()
                                    )
                                    amount += has_quota.transportation2_amount
                                    has_transpo = True

                            # quota - cellcard
                            if  has_quota.cellcard_amount:
                                cellcard = various_account.get(code='TEL', type='addtl', isdeleted=0)
                                if cellcard:

                                    if expchart.accountcode == '5100000000':
                                        cellcardexpc = cellcard.chartexpcostofsale_id
                                    elif expchart.accountcode == '5200000000':
                                        cellcardexpc = cellcard.chartexpgenandadmin_id
                                    else:
                                        cellcardexpc = cellcard.chartexpsellexp_id
                                        
                                    counter += 1
                                    Apdetail.objects.create(
                                        apmain_id = main.id,
                                        ap_num = main.apnum,
                                        ap_date = main.apdate,
                                        item_counter = counter,
                                        debitamount = has_quota.cellcard_amount,
                                        creditamount = '0.00',
                                        balancecode = 'D',
                                        amount = has_quota.cellcard_amount,
                                        chartofaccount_id = cellcardexpc,
                                        department_id = department.id,
                                        status='A',
                                        enterby_id = request.user.id,
                                        enterdate = datetime.datetime.now(),
                                        modifyby_id = request.user.id,
                                        modifydate = datetime.datetime.now()
                                    )
                                    amount += has_quota.cellcard_amount
                                    has_cellcard = True

                        if has_transpo and has_cellcard:
                            particulars_quota = " PLUS TRANSPO AND CELLPHONE ALLO."
                        elif has_transpo:
                            particulars_quota = " PLUS TRANSPO ALLO."
                        elif has_cellcard:
                            particulars_quota = " PLUS CELLPHONE ALLO."

                        companyparameter = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
                        
                        supplier_atc = Supplier.objects.get(pk=supplier.id)
                        atc_id = supplier_atc.atc_id

                        ataxcode = Ataxcode.objects.get(pk=atc_id)
                        rate = ataxcode.rate
                        
                        # default 25% or for Rank&File
                        wtax_rate = 25
                        tax = 0
                        if rate:
                            ewt = percentage(float(rate), float(amount))
                            tax = ewt
                            coa_id = companyparameter.coa_ewtax_id
                        else:
                            if triplec.wtax:
                                # Officer 30%
                                wtax_rate = triplec.wtax
                            wtax = percentage(float(wtax_rate), float(amount))
                            tax = wtax
                            # wtax_id 315
                            coa_id = companyparameter.coa_wtax_id

                        aptrade_amount = float(amount) - float(tax)

                        counter += 1
                        # EWT / WTAX
                        Apdetail.objects.create(
                            apmain_id = main.id,
                            ap_num = main.apnum,
                            ap_date = main.apdate,
                            item_counter = counter,
                            debitamount = '0.00',
                            creditamount = tax,
                            balancecode = 'C',
                            ataxcode_id = atc_id,
                            chartofaccount_id = coa_id,
                            supplier_id = supplier.id,      
                            status='A',
                            enterby_id = request.user.id,
                            enterdate = datetime.datetime.now(),
                            modifyby_id = request.user.id,
                            modifydate = datetime.datetime.now()
                        )
                        
                        counter += 1
                        # AP TRADE
                        Apdetail.objects.create(
                            apmain_id = main.id,
                            ap_num = main.apnum,
                            ap_date = main.apdate,
                            item_counter = counter,
                            debitamount = '0.00',
                            creditamount = aptrade_amount,
                            balancecode = 'C',
                            chartofaccount_id = companyparameter.coa_aptrade_id,
                            supplier_id = supplier.id,      
                            status='A',
                            enterby_id = request.user.id,
                            enterdate = datetime.datetime.now(),
                            modifyby_id = request.user.id,
                            modifydate = datetime.datetime.now()
                        )
                        # print 'teest', atc_id, ataxcode.code, ataxcode.rate
                        main.atax_id = atc_id
                        main.ataxcode = ataxcode.code
                        main.ataxrate = ataxcode.rate

                        issue_dates = triplec_all.values('issue_date')
                        particulars = apv_particulars(issue_dates, particulars_quota)
                        
                        main.particulars = particulars
                        main.amount = amount
                        main.save()

                        successful_trans += 1

                except Exception as e:
                    exception = str(e)
                    
            if exception:
                response = {'status': 'error', 'message': 'An exception occured: ('+ exception+') - Note: other transaction(s) may have been successfully saved ('+successful_trans+').'}
            elif already_posted > 0 and successful_trans > 0:
                if already_posted == 1 and successful_trans == 1:
                    response = {'status': 'error', 'message': 'Successfully posted '+str(successful_trans)+' transaction. However, there is '+ str(already_posted)+ ' transaction have been already posted.'}
                elif already_posted == 1 and successful_trans > 1:
                    response = {'status': 'error', 'message': 'Successfully posted '+str(successful_trans)+' transaction. However, there are '+ str(already_posted)+ ' transactions have been already posted'}
                elif already_posted > 1 and successful_trans == 1:
                    response = {'status': 'error', 'message': 'Successfully posted '+str(successful_trans)+' transactions. However, there is '+ str(already_posted)+ ' transaction have been already posted'}
                else:
                    response = {'status': 'error', 'message': 'Successfully posted '+str(successful_trans)+' transactions. However, there are '+ str(already_posted)+ ' transactions have been already posted'}
            elif successful_trans == 0 or already_posted == total_trans:
                if already_posted > 1:
                    response = {'status': 'error', 'message': 'All transactions have been posted and are not allowed for reposting.'}
                else:
                    response = {'status': 'error', 'message': 'This transaction have been posted and is not allowed for reposting.'}
            else:
                response = {'status': 'success'}
        else:
            errors = validated['validation_list']
            for error in errors:
                error['errors_list'] = [list(error_set) for error_set in error['errors_list']]

            # Serialize to JSON
            error_json = json.dumps(errors)
            print 'error_json', error_json
            response = {'status': 'validation_error', 'message': 'Transactions for posting to AP have failed the validation.', 'error_json': error_json}
    else:
        response = {'status': 'error', 'message': 'Method not allowed'}
    
    return JsonResponse(response)


def get_expc(expchart, id):
    entry = TripleC.objects.get(pk=id[0])
    various_account = Triplecvariousaccount.objects
    expc = 0
    priorities = Subtype.objects.exclude(various_account__isnull=True)

    # spcecial cases only e.g. type is Photo as CF-PHOTO
    if priorities:
        for priority in priorities:

            if entry.subtype_id == priority.id:
                expc = various_account.get(pk=priority.various_account_id).chartexpcostofsale_id
                return expc

    class_account_id = Classification.objects.get(code=entry.type)
    supplier_id = Supplier.objects.get(code=entry.code).id
    various_account_id = Triplecsupplier.objects.get(supplier_id=supplier_id).various_account_id

    if entry.type == 'COL':
        expc = various_account.get(pk=class_account_id.various_account_id).chartexpcostofsale_id

    elif entry.type == 'CON':
        if expchart.accountcode == '5100000000':
            if entry.section_id == 29:
                # 29:Comic Section
                # Contributor:various_account2_id = CF-CARTOONS
                expc = various_account.get(pk=class_account_id.various_account2_id).chartexpcostofsale_id
            elif entry.section_id in [18, 33, 32, 12, 37, 1, 7, 40, 43, 30, 14, 3]:
                # CF-CITY CORRESPONDENT
                # 18, 33, 32, 12, 37, 1, 7, 40, 43:*lifestyle*, 30:motoring, 14:news, 3:business
                expc = various_account.get(pk=class_account_id.various_account4_id).chartexpcostofsale_id
            elif entry.subtype_id in [9, 17, 43, 47]:
                # CF-EDITORS - get by type
                # 9:Retainer's fee, 17:editing fee, 43:project director, 47:consultant
                expc = various_account.get(pk=class_account_id.various_account3_id).chartexpcostofsale_id
            elif entry.subtype_id in [10, 11, 13, 46, 38, 24, 49, 50]:
                # Contributors Fee (a.k.a Advertorials)
                # 10:article, 11:photo, 13:layout, 46:proof reading, 38:epa, 24:graphic design, 49:edfee, 50:arts
                expc = various_account.get(pk=class_account_id.various_account_id).chartexpcostofsale_id
            else:
                # default
                if various_account_id:
                    expc = various_account.get(pk=various_account_id).chartexpcostofsale_id
        elif expchart.accountcode == '5200000000':
            expc = various_account.get(pk=class_account_id.various_account_id).chartexpgenandadmin_id
        else:
            expc = various_account.get(pk=class_account_id.various_account_id).chartexpsellexp_id

    elif entry.type == 'COR':
        
        if entry.subtype_id == 9:
            # CF-EDITORS, 9:retainer's fee
            expc = various_account.get(pk=class_account_id.various_account_id).chartexpcostofsale_id
        elif entry.subtype_id in [10, 48]:
            # CF-PROVINCIAL CORRESPONDENTS
            # 10:article, 48:breaking news
            expc = various_account.get(pk=class_account_id.various_account2_id).chartexpcostofsale_id
        else:
            if various_account_id:
                expc = various_account.get(pk=various_account_id).chartexpcostofsale_id
    
    return expc
    

def lastAPNumber(param):
    # print "Summary"
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT SUBSTRING(apnum, 5) AS num FROM apmain ORDER BY id DESC LIMIT 1"

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result[0]


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def add_days_to_date(date_str, days):
    date_format = "%Y-%m-%d"
    input_date = dt.strptime(date_str, date_format)
    new_date = input_date + timedelta(days=days)
    return new_date.strftime(date_format)


class QuotaView(AjaxListView):
    model = Triplecquota
    template_name = 'triplec/process_transaction/quota/index.html'
    context_object_name = 'data_list'
    page_template = 'triplec/process_transaction/quota/index_list.html'
    
    def get_queryset(self):
        query = self.request.GET.get('query')
        if query:
            queryset = self.model.objects.filter(
                Q(confirmation__icontains=query) |
                Q(type__icontains=query) |
                Q(transportation_amount__icontains=query) |
                Q(transportation2_amount__icontains=query) |
                Q(cellcard_amount__icontains=query)
            )
        else:
            queryset = self.model.objects.filter(isdeleted=0)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(QuotaView, self).get_context_data(**kwargs)
        query = self.request.GET.get('query', '')
        context['query'] = query

        data_list = []
        for quota in context['data_list']:
            triplec = TripleC.objects.filter(confirmation=quota.confirmation, isdeleted=0).values('type', 'author_name').first()
            if triplec:
                data_list.append({
                    'quota': quota,
                    'detail': triplec
                })

        context['data_list'] = data_list

        return context


@method_decorator(login_required, name='dispatch')
class QuotaDetailView(DetailView):
    model = Triplecquota
    template_name = 'triplec/process_transaction/quota/detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super(QuotaDetailView, self).get_context_data(**kwargs)
        quota = self.get_object()
        
        context['detail'] = TripleC.objects.filter(confirmation=quota.confirmation)

        return context


@method_decorator(login_required, name='dispatch')
class QuotaUpdateView(UpdateView):
    model = Triplecquota
    template_name = 'triplec/process_transaction/quota/edit.html'
    fields = ['confirmation', 'transportation_amount', 'transportation2_amount', 'cellcard_amount']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('triplec.change_triplec_quota'):
            raise Http404
        return super(QuotaUpdateView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        context = super(QuotaUpdateView, self).get_context_data(**kwargs)
        
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifyby = self.request.user
        self.object.modifydate = datetime.datetime.now()
        self.object.save(update_fields=['transportation_amount', 'transportation2_amount', 'cellcard_amount', 'modifyby', 'modifydate'])
        return HttpResponseRedirect('/triplec/quota')


class BatchPrintCsView(IndexView):
    model = TripleC
    template_name = 'triplec/print_cs/index.html'
    
    def get_context_data(self, **kwargs):
       context = super(BatchPrintCsView, self).get_context_data(**kwargs)
       return context
    

def retrieve_cs(request):
    dfrom = request.GET["dfrom"]
    dto = request.GET["dto"]
    csno_from = request.GET["csno_from"]
    csno_to = request.GET["csno_to"]

    try:
        triplec = TripleC.objects.filter(~Q(confirmation__isnull=True) & ~Q(confirmation=''))
        if dfrom and dto and csno_from and csno_to:
            result = triplec.filter(issue_date__range=[dfrom, dto], confirmation__range=[csno_from, csno_to])
        elif dfrom and dto:
            result = triplec.filter(issue_date__range=[dfrom, dto])
        elif csno_from and csno_to:
            result = triplec.filter(confirmation__range=[csno_from, csno_to])
        else:
            result = None
    except:
        result = None

    if result:
        confirmations = (
            result.values('confirmation', 'issue_date', 'type', 'author_name')
            .annotate(total_size=Sum('total_size'))
            .annotate(total_no_of_items=Sum('no_items'))
            .annotate(amount=Sum('amount'))
            .order_by('confirmation')
        )
        result = list(confirmations)

    context = {}
    context['cs_data'] = result
    viewhtml = render_to_string('triplec/print_cs/index_list.html', context)
    
    data = {
        'status': 'success',
        'viewhtml': viewhtml
    }

    return JsonResponse(data)


def startprint(request):

    cookie_urlquery = request.COOKIES.get('csbatchprint_triplec', '')
    parameter = {}
    info = {}
    data_list = []
    
    if cookie_urlquery:
        companyparameter = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        
        urlquery = json.loads(urllib2.unquote(cookie_urlquery))
        for confirmation in urlquery:
            try:
                ids = TripleC.objects.filter(confirmation=confirmation, status='O', isdeleted=0).values('pk')
                for id in ids:
                    data_list.append(TripleC.objects.values('pk', 'code', 'author_name', 'confirmation', 'date_posted').get(pk=id['pk'], status='O', isdeleted=0))
            except:
                pass

        sorted_data_list = sorted(data_list, key=lambda x: x['author_name'])
        grouped_dict = OrderedDict()

        for item in sorted_data_list:
            conf = item['confirmation']
            if conf not in grouped_dict:
                grouped_dict[conf] = []
            grouped_dict[conf].append(item['pk'])

        xno = 0
        for csno, ids in grouped_dict.items():

            csno = str(csno)
            parameter[xno] = {}
            details = {}
            batch_cs = TripleC.objects.filter(confirmation=csno, status='O', isdeleted=0)

            parameter[xno]['main'] = batch_cs.first()
            has_quota = get_object_or_None(Triplecquota, confirmation=csno, status='A', isdeleted=0)
            
            quota_amount = 0
            with_additional = False
            if has_quota:
                transpo = has_quota.transportation_amount
                transpo2 = has_quota.transportation2_amount
                cellcard = has_quota.cellcard_amount

                quota_amount = transpo + transpo2 + cellcard
                with_additional = True

                parameter[xno]['transportation_amount'] = transpo
                parameter[xno]['transportation2_amount'] = transpo2
                parameter[xno]['cellcard_amount'] = cellcard
            
            atc_id = Supplier.objects.get(code=parameter[xno]['main'].code).atc_id
            rate = Ataxcode.objects.get(pk=atc_id).rate
            # print 'rate', rate, csno
            subtotal = batch_cs.aggregate(subtotal=Sum('amount'))
            subtotal = float(subtotal['subtotal'])
            total = subtotal + float(quota_amount)

            ewt = 0
            is_ewt = True
            tax = 0
            wtax = 0
            # RANK & FILE or default to 25% wtax
            wtax_rate = companyparameter.ranknfile_percentage_tax
            if rate:
                ewt = percentage(float(rate), total)
                tax = ewt
            else:
                is_ewt = False
                if parameter[xno]['main'].supplier_id is not None:

                    employeenumber = get_object_or_None(Employee, supplier=parameter[xno]['main'].supplier_id)
                    if employeenumber:
                        withholding_tax = get_withholding_tax(employeenumber.code, companyparameter.base_url_201)
                        employee_level = withholding_tax[0].get('employee_level', None)
                        if employee_level and employee_level != "RANK & FILE":
                            wtax_rate = companyparameter.officer_percentage_tax
                            
                    if not parameter[xno]['main'].wtax:
                        save_wtax(xno, wtax_rate)

                wtax = percentage(float(wtax_rate), total)
                tax = wtax

            net = total - tax

            parameter[xno]['size'] = batch_cs.aggregate(total_size=Sum('total_size'))
            parameter[xno]['with_additional'] = with_additional
            parameter[xno]['ataxrate'] = rate
            parameter[xno]['wtax_rate'] = wtax_rate
            parameter[xno]['subtotal'] = subtotal
            parameter[xno]['total'] = total
            parameter[xno]['is_ewt'] = is_ewt
            parameter[xno]['ewt'] = ewt
            parameter[xno]['wtax'] = wtax
            parameter[xno]['net'] = net
            
            trans_ids = []
            for id in ids:
                trans_ids.append(id)
                
            details = TripleC.objects.filter(pk__in=trans_ids).order_by('issue_date')
            parameter[xno]['details'] = details

            xno += 1
        
        info['logo'] = request.build_absolute_uri('/static/images/pdi.jpg')
        info['parameter'] = Companyparameter.objects.get(code='PDI', isdeleted=0, status='A')
        
        return render(request, 'triplec/print_cs/print_cs.html', {'info': info, 'parameter': parameter})
    else:
        return render(request, 'triplec/print_cs/print_cs.html', {'info': {}, 'parameter': {}})
