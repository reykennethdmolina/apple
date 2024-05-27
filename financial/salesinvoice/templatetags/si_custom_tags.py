from django import template

register = template.Library()

@register.filter(name='format_tin')
def format_tin(tin):
    if '-' in tin:
        return tin
    
    tin = ''.join([c for c in tin if c.isdigit()])  # Remove any non-digit characters
    
    if len(tin) == 14 and tin.isdigit():
        return tin[:3] + '-' + tin[3:6] + '-' + tin[6:9] + '-' + tin[9:]
    elif len(tin) < 14 and tin.isdigit():
        tin = tin.zfill(14)  # Pad with zeros to make it 14 digits long
        return tin[:3] + '-' + tin[3:6] + '-' + tin[6:9] + '-' + tin[9:]
    else:
        return tin
