from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
import xhtml2pdf.pisa as pisa

# class Render:
#
#     @staticmethod
#     def render(template_src, context_dict):
#         template = get_template(template_src)
#         html = template.render(context_dict)
#         response = BytesIO()
#         pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)
#
#         if not pdf.err:
#             return HttpResponse(response.getValue(), content_type='application/pdf')
#         else:
#             return HttpResponse("Error Rendering PDF", status=400)

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    response = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)

    if not pdf.err:
        return HttpResponse(response.getValue(), content_type='application/pdf')
    else:
        return HttpResponse("Error Rendering PDF", status=400)