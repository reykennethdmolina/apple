from django.template import Library
register = Library()

@register.filter
def subtotal_current(list):
    return sum([d.current_amount for d in list])

@register.filter
def subtotal_prev(list):
    return sum([d.prev_amount for d in list])

