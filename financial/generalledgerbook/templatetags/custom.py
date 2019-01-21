from django.template import Library
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


