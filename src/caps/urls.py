from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import login, logout_then_login

from caps import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^registerdesc$', views.register_desc, name='registerdesc'),
    url(r'^services$', views.services, name='services'),
    url(r'^resources$', views.resources, name='resources'),
    url(r'^contact$', views.contact, name='contact'),
    url(r'^login$', login, {'template_name':'caps/Login.html'}, name='login'),
    url(r'^logout$', logout_then_login, name='logout'),
    url(r'^register$', views.register, name='register'),
    url(r'^studentprofile$', views.profile_student, name='studentprofile'),
	url(r'^student_profile_for_counselor/(?P<username>\w*)$',
	views.profile_student_for_counselor, name='student_profile_for_counselor'),
    url(r'^counselorprofile/(?P<username>\w*)$', views.profile_counselor,
        name='counselorprofile'),
    url(r'^updateprofile$', views.update_profile, name='updateprofile'),
    url(r'^check_email/(?P<username>\w*)$', views.check_email,
		name='check_email'),
    url(r'^validate_email/(?P<username>.+)/(?P<key>.+)$', views.validate_email,
		name='validate_email'),
	url(r'^counselor_list$', views.counselor_list, name='counselor_list'),
	# Tasks API related URLS
	url(r'^student_exercise/(?P<task_id>\d+)$', views.student_exercise,
		name='studentexercise'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
