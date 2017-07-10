from django.conf.urls import url
from . import views

urlpatterns = [
    # ajax dropdown select2
    url(r'^ajaxselect/$', views.ajaxSelect, name='ajaxselect'),
    # ajax range search
    url(r'^ajaxsearch/$', views.ajaxSearch, name='ajaxsearch'),

    # ajax pagination goes here...
]
