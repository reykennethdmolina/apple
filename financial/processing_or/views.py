from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Temp_ormain


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'processing_or/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        # with open("static/files/or_master.txt") as textFile:
        #     for line in textFile:
        #         line = line.split("\t")
        #         # print line
        #     # lines = [shlex.split(line) for line in textFile]
        #
        # context['test'] = textFile

        return context


@csrf_exempt
def fileupload(request):
    if request.method == 'POST':
        # add some file filters
        # check if equal row
        if request.FILES['or_file']:
            try:
                data = Temp_ormain.objects.latest('importsequence')
                sequence = int(data.importsequence) + 1
            except Temp_ormain.DoesNotExist:
                sequence = 1

            if storeupload(request.FILES['or_file'], sequence):
                with open("static/files/" + str(sequence) + ".txt") as textFile:
                    for line in textFile:

                        data = line.split("\t")
                        for n, i in enumerate(data):
                            data[n] = data[n].replace('"', '')

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

                    data = {
                        'result': 'success'
                    }
                    return JsonResponse(data)
            else:
                data = {
                    'result': 'failed upload'
                }
            return JsonResponse(data)
        else:
            data = {
                'result': 'failed file'
            }
            return JsonResponse(data)


def storeupload(f, sequence):
    # rename file based on db
    with open('static/files/' + str(sequence) + '.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return True
