from django.conf.urls import url

from tasks import views

urlpatterns = [
    url(r'^get_next_question$', views.get_next_question, 
        name='get_next_question'),
    url(r'^send_response$', views.send_response, 
        name='send_response'),
    url(r'^get_progress$', views.get_progress, name='get_progress'),
]
