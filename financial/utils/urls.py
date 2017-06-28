from django.conf.urls import url
from . import views

urlpatterns = [
    # ajax dropdown select2
    url(r'^ajaxselect/$', views.ajaxSelect, name='ajaxselect'),
    # ajax pagination goes here...
]
