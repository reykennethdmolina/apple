from django.template import Library
register = Library()

@register.filter
def total_amount(list):
    return "hoy"
    #return sum(row.amount for row in list)

@register.filter
def test(val):
    return "test"
