from django import template

register = template.Library()

@register.filter(name='format_tin')
def format_tin(tin):
    # Helper function to check if a TIN is composed entirely of zeros
    def zero_tin(tin):
        tin = tin.strip()
        tin = tin.replace('-', '')
        return tin.isdigit() and tin == '0' * len(tin)

    if zero_tin(tin):
        return ''
    
    # Remove any non-digit characters
    tin = ''.join([c for c in tin if c.isdigit()])
    
    if len(tin) == 14 and tin.isdigit():
        return tin[:3] + '-' + tin[3:6] + '-' + tin[6:9] + '-' + tin[9:]
    elif len(tin) < 14 and tin.isdigit():
        # Extract the original last part (before padding)
        original_last_part = tin[-5:]
        
        # Pad with zeros to make it 14 digits long
        tin = tin.zfill(14)
        
        # Check if the original last part is 3 digits long and needs padding
        if len(original_last_part) == 3:
            last_five_digits = original_last_part.zfill(5)
        else:
            last_five_digits = tin[9:]
        
        return tin[:3] + '-' + tin[3:6] + '-' + tin[6:9] + '-' + last_five_digits
    else:
        return tin
