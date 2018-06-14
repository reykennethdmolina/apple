from django.template import Library
register = Library()

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

