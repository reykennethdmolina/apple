import datetime
from django.views.generic import View, ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse
from mrstype.models import Mrstype
from financial.utils import Render
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from companyparameter.models import Companyparameter
from accountspayable.models import Apmain
from chartofaccount.models import Chartofaccount
from collections import namedtuple
from django.db import connection
from django.template.loader import render_to_string


class IndexView(TemplateView):
    template_name = 'nontrade/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['chart'] = Chartofaccount.objects.filter(isdeleted=0, accounttype='P', nontrade='Y').order_by('accountcode')

        return context


#@csrf_exempt
def transgenerate(request):
    dto = request.GET["dto"]
    dfrom = request.GET["dfrom"]
    transaction = request.GET["transaction"]
    chartofaccount = request.GET["chartofaccount"]
    payeecode = request.GET["payeecode"]
    payeename = request.GET["payeename"]

    # status = request.GET["status"]


    context = {}

    print "transaction listing"

    data = query(dto, dfrom, transaction, chartofaccount, payeecode, payeename)
    #print data

    # ndto = datetime.datetime.strptime(dto, "%Y-%m-%d")
    # todate = datetime.date(int(ndto.year), int(ndto.month), 10)
    # toyear = todate.year
    # tomonth = todate.month
    # nfrom = datetime.datetime.strptime(dfrom, "%Y-%m-%d")
    # fromdate = datetime.date(int(nfrom.year), int(nfrom.month), 10)
    # fromyear = fromdate.year
    # frommonth = fromdate.month
    #
    # prevdate = datetime.date(int(fromyear), int(frommonth), 10) - timedelta(days=15)
    # prevyear = prevdate.year
    # prevmonth = prevdate.month
    #
    # begbalamount = 0
    # endbalamount = 0
    # endcode = ''
    #
    # if chart != '':
    #     begbal =Subledgersummary.objects.filter(chartofaccount_id=chart, year=prevyear, month=prevmonth).first();
    #     if begbal:
    #         begbalamount = begbal.end_amount
    #
    #     endbal =Subledgersummary.objects.filter(chartofaccount_id=chart, year=toyear, month=tomonth).first();
    #     if endbal:
    #         endbalamount = endbal.end_amount
    #         endcode = endbal.end_code
    #
    # context['result'] = query_transaction(dto, dfrom, chart, transtatus, status, payeecode, payeename)
    # context['dto'] = dto
    context['data'] = data
    viewhtml = render_to_string('nontrade/transaction_result.html', context)

    data = {
        'status': 'success',
        'viewhtml': viewhtml,
        # 'begbal': float(begbalamount),
        # 'endbal': float(endbalamount),
        # 'endcode': endcode
    }
    return JsonResponse(data)


def query(dto, dfrom, transaction, chartofaccount, payeecode, payeename):

    conchart = ""
    orderby = "ORDER BY document_date ASC, FIELD(a.document_type, 'AP','CV','JV','OR')"
    conpayeecode = ""
    conpayeename = ""

    if chartofaccount:
        conchart = "SELECT id FROM chartofaccount WHERE id = '"+str(chartofaccount)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"
    else:
        conchart  = "SELECT id FROM chartofaccount WHERE main = '"+str(transaction)+"' AND isdeleted=0 AND accounttype='P' AND nontrade='Y' ORDER BY accountcode"

    if payeecode:
        conpayeecode = "AND IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) = '"+str(payeecode)+"'"

    if payeename:
        conpayeename = "AND IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) LIKE '%"+str(payeename)+"%'"

    print conchart
    ''' Create query '''
    cursor = connection.cursor()

    query = "SELECT a.id, a.document_type, a.document_id, a.document_num, a.document_date, a.subtype, a.particulars, a.chartofaccount_id, a.document_reftype, a.document_refnum, a.document_refdate, " \
            "a.balancecode, IF (a.balancecode = 'C', a.amount, 0) AS creditamount, IF (a.balancecode = 'D', a.amount, 0) AS debitamount, " \
            "a.document_customer_id, a.document_supplier_id,  " \
            "b.accountcode, b.customer_enable, b.supplier_enable, b.nontrade, b.setup_customer, b.setup_supplier, " \
            "IF (b.customer_enable = 'Y', dcust.code, IF (b.supplier_enable = 'Y', dsup.code, IF (b.setup_customer != '', scust.code, ssup.code))) AS pcode,  " \
            "IF (b.customer_enable = 'Y', dcust.name, IF (b.supplier_enable = 'Y', dsup.name, IF (b.setup_customer != '', scust.name, ssup.name))) AS pname, " \
            "IF (b.customer_enable = 'Y', dcust.tin, IF (b.supplier_enable = 'Y', dsup.tin, IF (b.setup_customer != '', scust.tin, ssup.tin))) AS ptin " \
            "FROM subledger AS a " \
            "LEFT OUTER JOIN chartofaccount AS b ON b.id = a.chartofaccount_id " \
            "LEFT OUTER JOIN customer AS dcust ON dcust.id = a.document_customer_id " \
            "LEFT OUTER JOIN customer AS scust ON scust.id =  b.setup_customer " \
            "LEFT OUTER JOIN supplier AS dsup ON dsup.id = a.document_supplier_id " \
            "LEFT OUTER JOIN supplier AS ssup ON ssup.id = b.setup_supplier " \
            "WHERE a.chartofaccount_id IN ("+str(conchart)+") " \
            ""+str(conpayeecode)+" "+str(conpayeename)+" AND DATE(document_date) >= '"+str(dfrom)+"' AND DATE(document_date) <= '"+str(dto)+"' "+str(orderby)

    print query

    cursor.execute(query)
    result = namedtuplefetchall(cursor)

    return result

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]