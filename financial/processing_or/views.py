from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Temp_ormain
from officialreceipt.models import Ormain
from django.db.models import Count


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'processing_or/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        return context


@csrf_exempt
def fileupload(request):
    if request.method == 'POST':
        # file size

        # data-result definition:
        #   1: success
        #   2: failed - upload error
        #   3: failed - file error or AR Type invalid
        #   4: failed - file size too large (> 3mb)
        #   5: failed - file array columns does not match requirement

        if request.FILES['or_file'] and (request.POST['or_artype'] == 'a' or request.POST['or_artype'] == 'c') and request.FILES['or_file'].name.endswith('.txt'):
            if request.FILES['or_file']._size < 3*1024*1024:
                try:
                    data = Temp_ormain.objects.latest('importsequence')
                    sequence = int(data.importsequence) + 1
                except Temp_ormain.DoesNotExist:
                    sequence = 1

                if storeupload(request.FILES['or_file'], sequence):
                    orcount = 0
                    successcount = 0
                    failedcount = 0  
                    existingcount = 0                  
                    with open("static/files/" + str(sequence) + ".txt") as textFile:  
                        for line in textFile:
                            errordata = []
                            orcount += 1
                            data = line.split("\t")
                            for n, i in enumerate(data):
                                data[n] = data[n].replace('"', '')

                            if request.POST['or_artype'] == 'a':
                                if len(data) == 31:       
                                    Temp_ormain.objects.create(
                                        orno=data[0],
                                        ordate=data[1],
                                        prno=data[2],
                                        accounttype=data[3],
                                        collector=data[4],
                                        payeetype=data[5],
                                        adtype=data[6],
                                        agencycode=data[7],
                                        clientcode=data[8],
                                        agentcode=data[9],
                                        payeename=data[10],
                                        amount=data[11],
                                        amountinwords=data[12],
                                        bankaccount=data[13],
                                        particulars=data[14],
                                        artype=data[15],
                                        status=data[16],
                                        statusdate=data[17],
                                        enterby=data[18],
                                        enterdate=data[19],
                                        product=data[20],
                                        initmark=data[21],
                                        glsmark=data[22],
                                        glsdate=data[23],
                                        totalwtax=data[24],
                                        gov=data[25],
                                        branchcode=data[26],
                                        address1=data[27],
                                        address2=data[28],
                                        address3=data[29],
                                        tin=data[30],
                                        importsequence=sequence,
                                        importby=request.user,
                                    ).save()
                                    if errordata:
                                        failedcount += 1    
                                    breakstatus = 0
                                else:
                                    breakstatus = 1
                                    break
                        if breakstatus == 0: 
                            ormain_existing = Ormain.objects.filter(importornum__in=set(Temp_ormain.objects.filter(importsequence=sequence).values_list('orno', flat=True))).order_by('importornum').values('importornum').distinct()
                            existingcount = len(ormain_existing)
                            existingdata = list(ormain_existing)

                            temp_ormain_distinct = Temp_ormain.objects.filter(importsequence=sequence).values('orno').annotate(Count('orno')).count()
                            failedcount = orcount - temp_ormain_distinct

                            tempormain_duplicate = Temp_ormain.objects.filter(importsequence=sequence).values('orno').annotate(Count('id')).order_by().filter(id__count__gt=1)
                            faileddata = list(tempormain_duplicate)

                            successcount = orcount - (failedcount + existingcount)

                            rate = (float(successcount) / float(orcount)) * 100
                            data = {
                                'result': 1,
                                'orcount': orcount,
                                'successcount': successcount,
                                'failedcount': failedcount,
                                'faileddata': faileddata,
                                'existingcount': existingcount,
                                'existingdata': existingdata,
                                'rate': rate,
                                'errordata': errordata,
                            }
                        else:
                            data = {
                                'result': 5
                            }    
                        return JsonResponse(data)
                else:
                    data = {
                        'result': 2
                    }
                return JsonResponse(data)
            else:
                data = {
                    'result': 4
                }
            return JsonResponse(data)    
        else:
            data = {
                'result': 3
            }
            return JsonResponse(data)       


def storeupload(f, sequence):
    with open('static/files/' + str(sequence) + '.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return True

# errordata = validateLength(data[0], 1, 25, errordata)

# def validateLength(name, min, max, errordata):
#     if len(name) > max or not len(name) >= min:
#         if not 1 in errordata:
#             errordata.append(1)  
#     return errordata


# def errorMessages():
#     # 1 = length error or required
#     print 123
