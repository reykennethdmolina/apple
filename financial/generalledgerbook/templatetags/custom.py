from django.template import Library
register = Library()

@register.filter
def total_prev(list):
    return sum(row.prev_amount_abs for row in list)

@register.filter
def total_current(list):
    return sum(row.current_amount_abs for row in list)

@register.filter
def total_variance(list):
    prev = sum(row.prev_amount_abs for row in list)
    current = sum(row.current_amount_abs for row in list)
    return float(current) - float(prev)

@register.filter
def subtotal_current(list):
    return sum([d.current_amount_abs for d in list])

@register.filter
def subtotal_prev(list):
    return sum([d.prev_amount_abs for d in list])

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

