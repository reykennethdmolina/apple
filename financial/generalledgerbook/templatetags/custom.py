from django.template import Library
import numpy as np
register = Library()

@register.filter
def total_prev(list):
    return sum(row.prev_amount_abs for row in list)

@register.filter
def total_current(list):
    return sum(row.current_amount_abs for row in list)

@register.filter
def total_prev_is(list):
    return sum(row.prev_amount for row in list)

@register.filter
def total_current_is(list):
    return sum(row.current_amount for row in list)

@register.filter
def total_todate_is(list):
    return sum([d.todate_amount for d in list])

@register.filter
def total_variance_is(list):
    prev = sum([d.prev_amount for d in list])
    current = sum([d.current_amount for d in list])
    return float(current) - float(prev)

@register.filter
def total_variance(list):
    prev = sum(row.prev_amount_abs for row in list)
    current = sum(row.current_amount_abs for row in list)
    return float(current) - float(prev)

@register.filter
def subtotal_current(list):
    return sum([d.current_amount_abs for d in list])

@register.filter
def subtotal_current_is(list):
    return sum([d.current_amount for d in list])

@register.filter
def subtotal_prev(list):
    return sum([d.prev_amount_abs for d in list])

@register.filter
def subtotal_prev_is(list):
    return sum([d.prev_amount for d in list])

@register.filter
def subtotal_todate_is(list):
    return sum([d.todate_amount for d in list])

@register.filter
def subtotal_variance_is(list):
    prev = sum([d.prev_amount for d in list])
    current = sum([d.current_amount for d in list])
    return float(current) - float(prev)


@register.filter
def subtotal_variance(list):
    prev = sum([d.prev_amount_abs for d in list])
    current = sum([d.current_amount_abs for d in list])
    return float(current) - float(prev)

@register.filter
def percentage(value, arg):
    return value

@register.filter
def to_negative(value):
    if "-" in value:
        return value.replace("-","(")+")"
    else:
        return value


@register.filter
def add_beg(value, arg):
    new_val = float(value) + float(arg)
    return new_val


@register.filter
def subtotal_jan(list):
    return sum([d.mjan for d in list])

@register.filter
def subtotal_feb(list):
    return sum([d.mfeb for d in list])

@register.filter
def subtotal_mar(list):
    return sum([d.mmar for d in list])

@register.filter
def subtotal_apr(list):
    return sum([d.mapr for d in list])

@register.filter
def subtotal_may(list):
    return sum([d.mmay for d in list])

@register.filter
def subtotal_jun(list):
    return sum([d.mjun for d in list])

@register.filter
def subtotal_jul(list):
    return sum([d.mjul for d in list])

@register.filter
def subtotal_aug(list):
    return sum([d.maug for d in list])

@register.filter
def subtotal_sep(list):
    return sum([d.msep for d in list])

@register.filter
def subtotal_oct(list):
    return sum([d.moct for d in list])

@register.filter
def subtotal_nov(list):
    return sum([d.mnov for d in list])

@register.filter
def subtotal_dec(list):
    return sum([d.mdec for d in list])

@register.filter
def subtotal_total(list):
    return sum([d.mtotal for d in list])

@register.filter
def subtotal_amount(list):
    return sum([d.amount_subtotal for d in list])

@register.filter
def sum_amount(list):
    print "hello"
    return sum([d.amount for d in list])

# Schedule of Expense
@register.filter
def total_budcuramount(list):
    return sum(row.curamount for row in list)

@register.filter
def total_budprevamount(list):
    return sum(row.prevamount for row in list)

@register.filter
def total_budytdamount(list):
    return sum(row.ytdamount for row in list)

@register.filter
def total_budvaramount(list):
    return sum(row.varamount for row in list)

@register.filter
def total_budvarpercent(list):
    varamount = sum(row.varamount for row in list)
    prevamount = sum(row.prevamount for row in list)

    if prevamount == 0:
        return 0
    else:
        return (varamount / prevamount) * 100

# Budget Report
@register.filter
def total_bud_budgetamount(list):
    return sum(row.budget for row in list)

@register.filter
def total_bud_actualamount(list):
    return sum(row.actual for row in list)

@register.filter
def total_bud_varamount(list):
    return sum(row.varamount for row in list)

@register.filter
def total_bud_varpercent(list):
    varamount = sum(row.varamount for row in list)
    prevamount = sum(row.budget for row in list)

    if prevamount == 0:
        return 0
    else:
        return (varamount / prevamount) * 100

@register.filter
def total_bud_curytd_budgetamount(list):
    return sum(row.cur_budytd for row in list)

@register.filter
def total_bud_curytd_actualamount(list):
    return sum(row.cur_actualytd for row in list)

@register.filter
def total_bud_curytd_varamount(list):
    return sum(row.cur_varamount for row in list)

@register.filter
def total_bud_curytd_varpercent(list):
    varamount = sum(row.cur_varamount for row in list)
    prevamount = sum(row.cur_budytd for row in list)

    if prevamount == 0:
        return 0
    else:
        return (varamount / prevamount) * 100

@register.filter
def total_bud_lastytd_budgetamount(list):
    return sum(row.last_budytd for row in list)

@register.filter
def total_bud_lastytd_actualamount(list):
    return sum(row.last_actualytd for row in list)

@register.filter
def total_bud_lastytd_varamount(list):
    return sum(row.last_varamount for row in list)

@register.filter
def total_bud_lastytd_varpercent(list):
    varamount = sum(row.last_varamount for row in list)
    prevamount = sum(row.last_actualytd for row in list)

    if prevamount == 0:
        return 0
    else:
        return (varamount / prevamount) * 100

@register.filter
def passitem(item, counter):
    val = 0
    if item:
        val = 'item.col'+str(counter)
        return eval(val)

@register.filter
def subtotalpassitem(item, counter):
    if item:
        val = 'sum(row.col' + str(counter) + ' for row in item)'
        return eval(val)

@register.filter
def diff(debit, credit):
    if debit:
        return debit - credit
    elif credit:
        return debit - credit
    else:
        return 0
    #print list.creditamount_sum
    #return list.debitamount_sum - list.creditamount_sum

@register.filter
def incomeloss(arg1, arg2):
    valloss = 0
    # if arg2:
    #     val = 'sum(row.col' + str(counter) + ' for row in item)'
    #     valloss = eval(arg2)
    #print arg1
    print ''

@register.filter
def revenuetotal(item, counter):
    if item:
        val = 'sum(row.col' + str(counter) + ' for row in item)'
        return eval(val)

@register.filter
def revenuetotal_counter(item, counter):
    data = 0
    if item:
        val = 'sum(row.col' + str(counter) + ' for row in item)'
        data = eval(val)

    return data, counter

@register.filter
def cmitemdata(item, counter):
    #print type(item)
    #print 'cmitemdata'
    if item:
        val = 'item[0].col'+str(counter)
        return eval(val)

@register.filter(name='combine_param')
def combine_param(arg1, arg2):
    return arg1, arg2

@register.filter
def income_loss(arg1, arg2):
    item =0
    counter = 0
    adjustment = 0
    income = 0
    val = 0
    if arg1:
        item = arg1[0]
        counter = arg1[1]
        adjustment = eval('item[0].col' + str(counter))
    if arg2:
        item2 = arg2
        income = eval('sum(row.col' + str(counter) + ' for row in item2)')
        #return eval(val)

    return income + adjustment

@register.filter
def income_loss2(arg1, arg2):

    item =0
    counter = 0
    adjustment = 0
    cm = 0
    val = 0
    if arg1:
        item = arg1[0]
        counter = arg1[1]
        adjustment = eval('item[0].col' + str(counter))
    if arg2:
        item2 = arg2
        cm = eval('sum(row.col' + str(counter) + ' for row in item2)')
        #return eval(val)
    return cm  #+ adjustment
    #return income + adjustment

@register.filter
def contribution_margin(arg1, arg2):
    item =0
    counter = 0
    data1 = 0
    data2 = 0
    val = 0
    if arg1:
        item = arg1[0]
        counter = arg1[1]
        data1 = eval('sum(row.col' + str(counter) + ' for row in item)')
    if arg2:
        item2 = arg2
        data2 = eval('sum(row.col' + str(counter) + ' for row in item2)')
        #return eval(val)
    return data1 - data2
    #return income + adjustment

@register.filter
def opex(item, counter):
    #return item[0]
    if item:
        return eval('item[' + str(counter - 1)+']')
