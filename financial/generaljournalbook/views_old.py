from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.apps import apps
from django.db.models import Sum, F, Count
from collections import namedtuple
from django.db import connection


# transaction keys
# transactiontype = {
#     'or': ['officialreceipt', 'Ormain', 'Ordetail'],
#     'jv': ['journalvoucher', 'Jvmain', 'Jvdetail'],
#     'cv': ['checkvoucher', 'Cvmain', 'Cvdetail'],
# }

# dropdown keys
transactiontype_select = [['or', 'Official Receipt'],
                          ['jv', 'Journal Voucher'],
                          ['cv', 'Check Voucher'], ]
reporttype_select = [['custom', 'Customized'],
                     ['ub', 'Unbalanced Accounting Entry']]
groupby_select = [['num', 'Inquiry No.'],
                  ['date', 'Date'],
                  ['branchcode', 'Branch'],
                  ['datastatus', 'Status']]

# order by keys
orderby = [[['num', 'Inquiry No.'],
            ['date', 'Date'],
            ['margin', 'Margin'],
            ['debitamount', 'Debit'],
            ['creditamount', 'Credit']],
           [['num', 'Inquiry No.'],
            ['date', 'Date'],
            ['branchcode', 'Branch'],
            ['datastatus', 'Status'],
            ['debitamount', 'Debit'],
            ['creditamount', 'Credit']]]


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'generaljournalbook/index.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        context['transactiontype_select'] = transactiontype_select
        context['reporttype_select'] = reporttype_select
        context['groupby_select'] = groupby_select
        context['orderby'] = orderby

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if self.request.GET:

            if self.request.GET.getlist('rep_f_transactiontype[]'):
                transactiontype = self.request.GET.getlist('rep_f_transactiontype[]')

                # report type
                if self.request.GET['rep_f_reporttype'] == 'custom':

                    # -------------------------------------------------------------------------------------- date filter
                    # -------------------------------------------------------------------------------------- date filter
                    # -------------------------------------------------------------------------------------- date filter
                    table_date = ''
                    if self.request.GET['rep_f_datefrom'] or self.request.GET['rep_f_dateto']:
                        table_date += "WHERE "
                    if self.request.GET['rep_f_datefrom']:
                        table_date += "date >= DATE('" + self.request.GET['rep_f_datefrom'] + "') "
                    if self.request.GET['rep_f_datefrom'] and self.request.GET['rep_f_dateto']:
                        table_date += "AND"
                    if self.request.GET['rep_f_dateto']:
                        table_date += "date <= DATE('" + self.request.GET['rep_f_dateto'] + "') "

                    # ----------------------------------------------------------------------------------------- order by
                    # ----------------------------------------------------------------------------------------- order by
                    # ----------------------------------------------------------------------------------------- order by
                    first = True
                    table_order = ''
                    if self.request.GET.getlist('rep_f_order_custom[]'):
                        context['rep_f_order'] = ','.join(map(str, self.request.GET.getlist('rep_f_order_custom[]')))

                        table_order = "ORDER BY "
                        for data in self.request.GET.getlist('rep_f_order_custom[]'):
                            if first:
                                first = False
                                table_order += data
                            else:
                                table_order += ", " + data

                        if self.request.GET['rep_f_ordertype']:
                            table_order += " " + self.request.GET['rep_f_ordertype']

                    # --------------------------------------------------------------------------- group by / report type
                    # --------------------------------------------------------------------------- group by / report type
                    # --------------------------------------------------------------------------- group by / report type
                    table_group = ''
                    table_rows = ''
                    if self.request.GET['rep_f_resulttype'] == 'summary':
                        table_group = "GROUP BY datatable." + self.request.GET['rep_f_groupby']
                        table_rows = "SUM(datatable.debitamount) AS debitamount, " \
                                     "SUM(datatable.creditamount) AS creditamount, " \
                                     "COUNT(DISTINCT datatable.num) AS numcount, " \
                                     "SUM(datatable.debitamount) - SUM(datatable.creditamount) AS margin, "
                    else:
                        table_rows = "datatable.debitamount, " \
                                     "datatable.creditamount, "

                    # ---------------------------------------------------------------------------- transaction type loop
                    # ---------------------------------------------------------------------------- transaction type loop
                    # ---------------------------------------------------------------------------- transaction type loop
                    first = True
                    table_transaction = "("
                    for data in transactiontype:
                        if first:
                            first = False
                        else:
                            table_transaction += "UNION ALL "

                        table_transaction += "SELECT " \
                                        "(CASE WHEN '" + data + "' = 'or' THEN 'officialreceipt:update' " \
                                              "WHEN '" + data + "' = 'jv' THEN 'journalvoucher:update' " \
                                              "WHEN '" + data + "' = 'cv' THEN 'checkvoucher:update' END) AS datalink_update, " \
                                        "(CASE WHEN '" + data + "' = 'or' THEN 'officialreceipt:detail' " \
                                              "WHEN '" + data + "' = 'jv' THEN 'journalvoucher:detail' " \
                                              "WHEN '" + data + "' = 'cv' THEN 'checkvoucher:detail' END) AS datalink_detail, " \
                                        + data + "m.id AS dataid, " \
                                        "CONCAT_WS('', '" + data + "-', " + data + "m." + data + "num) AS num, " \
                                        "DATE(" + data + "m." + data + "date) AS DATE, " \
                                        "branch.code AS branchcode, " \
                                        "branch.description AS branchdescription, " \
                                        + data + "m.status AS datastatus, " \
                                        "`" + data + "d`.`debitamount`, " \
                                        "`" + data + "d`.`creditamount` " \
                                     "FROM " + data + "main " + data + "m " \
                                        "LEFT JOIN " + data + "detail `" + data + "d` " \
                                            "ON `" + data + "d`.`" + data + "main_id` = " + data + "m.`id` " \
                                        "LEFT JOIN branch " \
                                            "ON branch.id = " + data + "m.branch_id " \
                                     "WHERE " + data + "m.isdeleted = 0 " \
                                        "AND " + data + "m.status = 'A' "
                    table_transaction += ")"

                    # ------------------------------------------------------------------------------ merging all queries
                    # ------------------------------------------------------------------------------ merging all queries
                    # ------------------------------------------------------------------------------ merging all queries
                    querytotal = "SELECT * FROM " \
                                     "(SELECT " \
                                        "datatable.dataid, datatable.num, datatable.date, " \
                                        "datatable.branchcode, datatable.branchdescription, datatable.datastatus, " \
                                        + table_rows + \
                                        "datatable.datalink_update, datatable.datalink_detail " \
                                     "FROM " + table_transaction + " datatable " \
                                     + table_group + ") datatable " + table_date + table_order

                    context['data'] = executestmt(querytotal)

                elif self.request.GET['rep_f_reporttype'] == 'ub':

                    # -------------------------------------------------------------------------------------- date filter
                    # -------------------------------------------------------------------------------------- date filter
                    # -------------------------------------------------------------------------------------- date filter
                    table_date = ''
                    if self.request.GET['rep_f_datefrom']:
                        table_date += "AND date >= DATE('" + self.request.GET['rep_f_datefrom'] + "') "
                    if self.request.GET['rep_f_dateto']:
                        table_date += "AND date <= DATE('" + self.request.GET['rep_f_dateto'] + "') "

                    # ----------------------------------------------------------------------------------------- order by
                    # ----------------------------------------------------------------------------------------- order by
                    # ----------------------------------------------------------------------------------------- order by
                    first = True
                    table_order = ''
                    if self.request.GET.getlist('rep_f_order_ub[]'):
                        context['rep_f_order'] = ','.join(map(str, self.request.GET.getlist('rep_f_order_ub[]')))

                        table_order = "ORDER BY "
                        for data in self.request.GET.getlist('rep_f_order_ub[]'):
                            if first:
                                first = False
                                table_order += data
                            else:
                                table_order += ", " + data

                        if self.request.GET['rep_f_ordertype']:
                            table_order += " " + self.request.GET['rep_f_ordertype']

                    # ---------------------------------------------------------------------------- transaction type loop
                    # ---------------------------------------------------------------------------- transaction type loop
                    # ---------------------------------------------------------------------------- transaction type loop
                    first = True
                    table_transaction = "("
                    for data in transactiontype:
                        if first:
                            first = False
                        else:
                            table_transaction += "UNION ALL "

                        table_transaction += "SELECT " \
                                        "(CASE WHEN '" + data + "' = 'or' THEN 'officialreceipt:update' " \
                                              "WHEN '" + data + "' = 'jv' THEN 'journalvoucher:update' " \
                                              "WHEN '" + data + "' = 'cv' THEN 'checkvoucher:update' END) AS datalink_update, " \
                                        "(CASE WHEN '" + data + "' = 'or' THEN 'officialreceipt:detail' " \
                                              "WHEN '" + data + "' = 'jv' THEN 'journalvoucher:detail' " \
                                              "WHEN '" + data + "' = 'cv' THEN 'checkvoucher:detail' END) AS datalink_detail, " \
                                        + data + "m.id AS dataid, " \
                                        "CONCAT_WS('', '" + data + "-', " + data + "m." + data + "num) AS num, " \
                                        "DATE(" + data + "m." + data + "date) AS DATE, " \
                                        "`" + data + "d`.`debitamount`, " \
                                        "`" + data + "d`.`creditamount` " \
                                     "FROM " + data + "main " + data + "m " \
                                        "LEFT JOIN " + data + "detail `" + data + "d` " \
                                            "ON `" + data + "d`.`" + data + "main_id` = " + data + "m.`id` " \
                                     "WHERE " + data + "m.isdeleted = 0 " \
                                        "AND " + data + "m.status = 'A' "
                    table_transaction += ")"

                    # ------------------------------------------------------------------------------ merging all queries
                    # ------------------------------------------------------------------------------ merging all queries
                    # ------------------------------------------------------------------------------ merging all queries
                    querytotal = "SELECT * FROM " \
                                     "(SELECT " \
                                        "datatable.dataid, datatable.num, datatable.date, " \
                                        "SUM(datatable.debitamount) AS debitamount, " \
                                        "SUM(datatable.creditamount) AS creditamount, " \
                                        "SUM(datatable.debitamount) - SUM(datatable.creditamount) AS margin, " \
                                        "datatable.datalink_update, datatable.datalink_detail " \
                                     "FROM " + table_transaction + " datatable " \
                                     "GROUP BY datatable.num) datatable " \
                                  "WHERE margin <> 0 " + table_date + table_order

                    context['data'] = executestmt(querytotal)

                # return GET
                context['rep_f_datefrom'] = self.request.GET['rep_f_datefrom']
                context['rep_f_dateto'] = self.request.GET['rep_f_dateto']
                context['rep_f_groupby'] = self.request.GET['rep_f_groupby']
                context['rep_f_resulttype'] = self.request.GET['rep_f_resulttype']
                context['rep_f_ordertype'] = self.request.GET['rep_f_ordertype']
                context['rep_f_reporttype'] = self.request.GET['rep_f_reporttype']
                context['rep_f_transactiontype'] = ','.join(map(str, self.request.GET.getlist('rep_f_transactiontype[]')))

        return self.render_to_response(context)


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def executestmt(query):
    cursor = connection.cursor()

    cursor.execute(query)

    return namedtuplefetchall(cursor)