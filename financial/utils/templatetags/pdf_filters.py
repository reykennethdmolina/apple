from django import template
import urllib2
import base64
import ssl

register = template.Library()

@register.filter
def get64(url):
    """
    Method returning base64 image data instead of URL
    """
    if url.startswith("http"):
        context = ssl._create_unverified_context()
        image = urllib2.urlopen(url, context=context).read()
        return 'data:image/jpg;base64,' + base64.b64encode(image)

    return url

