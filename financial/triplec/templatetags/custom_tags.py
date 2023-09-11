from django import template

register = template.Library()


@register.simple_tag
def author_codes_to_html(authors, loop_value):
    html = ""
    for author in authors:
        selected = ''
        if author.code == loop_value:
            selected = 'selected'  

        html += '<option value="%s" %s>%s</option>' % (author.code, selected, author.code)
    return html


@register.simple_tag
def author_names_to_html(authors, loop_value):
    html = ""
    for author in authors:
        selected = ''
        if author.name == loop_value:
            selected = 'selected'
        
        html += '<option value="%s" %s>%s</option>' % (author.name, selected, "["+ author.code +"] "+ author.name)
    return html


@register.simple_tag
def classifications_to_html(classifications, loop_value):
    html = ""
    for classification in classifications:
        selected = ''
        if classification.code == loop_value:
            selected = 'selected'  
        html += '<option value="%s" %s>%s</option>' % (classification.code, selected, classification.description)
    return html


@register.simple_tag
def author_codes_to_options_html(authors):
    options_html = ""
    options_html += '<option value="%s">%s</option>' % ("", "-- Select --")
    for author in authors:
        options_html += '<option value="%s">%s</option>' % (author.code, author.code)
    return options_html


@register.simple_tag
def author_names_to_options_html(authors):
    options_html = ""
    options_html += '<option value="%s">%s</option>' % ("", "-- Select --")
    for author in authors:
        options_html += '<option value="%s">%s</option>' % (author.name, "["+ author.code +"] "+ author.name)
    return options_html


@register.simple_tag
def classifications_to_options_html(classifications):
    options_html = ""
    options_html += '<option value="%s">%s</option>' % ("", "-- Select --")
    for classification in classifications:
        options_html += '<option value="%s">%s</option>' % (classification.code, classification.description)
    return options_html
