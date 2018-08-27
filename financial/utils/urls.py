from django.conf.urls import url
from . import views

urlpatterns = [
    # ajax dropdown select2
    url(r'^ajaxselect/$', views.ajaxSelect, name='ajaxselect'),
    url(r'^ajaxselect2/$', views.ajaxSelect2, name='ajaxselect2'),
    # ajax range search
    url(r'^ajaxsearch/$', views.ajaxSearch, name='ajaxsearch'),
]
