from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator

from mimetypes import guess_type
import datetime

from caps.consumers import get_profile
from caps.models import *
from caps.forms import *

from tasks.models import *
from tasks.views import *

EMAIL_FMT = '%s@andrew.cmu.edu'
VERIFY_EMAIL_MESSAGE_FMT = """
Welcome to CaPS!
Please click the link below to verify your email address and activate your \
account:

http://%s%s
"""

@ensure_csrf_cookie
def home(request):
    """ Home page, with logging in options and chat options.

    Args:
        request: Django's HTTP request object.

    Returns:
        renders the home page, user - request.user, meeting_counselor - the
            counselor the student has a meeting with, if any.
    """
    context = {'user':request.user}
    now = timezone.now()
    if request.user.username and User.objects.filter(
        username=request.user, student__isnull=False):
        meetings = Meeting.objects.filter(student=request.user.student,
                                start_datetime__lt=now, end_datetime__gt=now)
        if meetings.count() == 1:
            context['meeting_counselor'] = meetings[0].counselor
    if request.user.username and User.objects.filter( 
        username=request.user, counselor__isnull=False):
        meetings = Meeting.objects.filter(counselor=request.user.counselor,
            start_datetime__lt=now,
            end_datetime__gt=now)
        if meetings.count() == 1:
            context['meeting_student'] = meetings[0]
    return render(request, 'caps/Home.html', context)

@ensure_csrf_cookie
def register_desc(request):
    """ Pre registration page for unregistered user.

    Args:
        request: Django's HTTP request object.

    Returns:
        renders the static page, user - request.user.
    """
    context = {'user':request.user}
    return render(request, 'caps/RegisterDesc.html', context)

@ensure_csrf_cookie
def services(request):
    """ Static page showing CapS services.

    Args:
        request: Django's HTTP request object.

    Returns:
        renders the static page, user - request.user.
    """
    context = {'user':request.user}
    return render(request, 'caps/Services.html', context)

@ensure_csrf_cookie
def resources(request):
    """ Static page showing CaPS services.

    Args:
        request: Django's HTTP request object.

    Returns:
        renders the static page, user - request.user.
    """
    context = {'user':request.user}
    return render(request, 'caps/Resources.html', context)

@ensure_csrf_cookie
def contact(request):
    """ Static page shows how to contact CaPS outside of the web app.

    Args:
        request: Django's HTTP request object.

    Returns:
        renders the static page, user - request.user.
    """
    context = {'user':request.user}
    return render(request, 'caps/Contact.html', context)

@transaction.atomic
@ensure_csrf_cookie
def register(request):
    """ Registration page for a student

    Args:
        request: Django's HTTP request object.

    Returns:
        GET - renders the static page, user as the request.user.
        POST - creates a new student.
    """
    context = {}
    if request.method == 'GET':
        if request.user.is_authenticated:
            context = {'errors':["You are already registered!"],
            'user':request.user}
            return render(request, 'caps/Home.html', context)
        context['form'] = RegisterForm()
        return render(request, 'caps/Register.html', context)

    # input validation check
    form = RegisterForm(request.POST)
    context['form'] = form
    if not form.is_valid():
        return render(request, 'caps/Register.html', context)

    # Creating user - input validated and transaction is atomic
    new_user = User.objects.create_user(
        username=form.cleaned_data['username'],
        password=form.cleaned_data['password'],
        first_name=form.cleaned_data['first_name'],
        last_name=form.cleaned_data['last_name'],
        email=EMAIL_FMT % form.cleaned_data['username'],
        is_active=False)
    # need to create Student instance to the newly created User
    new_user_student = Student(user=new_user)
    # create TaskProfile
    create_profile(new_user)
	# Assign compatibility measure task - assuming task already exist and was
	# created by the admin before the first student registered to the site
    task = get_object_or_404(Task, name="Compatibility Measures")
    new_assigned_task = AssignedTask(task=task,
                                     tasks_profile=new_user.tasks_profile)
    new_assigned_task.save()
	# Assign profile picture and confirmation key
    new_user_student.picture = DEFAULT_PROFILE_PICTURE
    new_user_student.set_new_email_key() # auto save
    send_mail(subject='[CaPS] Verify your Email Address',
        message=VERIFY_EMAIL_MESSAGE_FMT % (
            request.get_host(),
            reverse('validate_email', args=[new_user.username,
                new_user.student.email_key])),
        from_email='web@capseling.ml',
        recipient_list=[new_user.email])
    return redirect(reverse('check_email', args=[new_user.username]))

@ensure_csrf_cookie
def check_email(request, username):
    """ Static page shows a message to encourage checking email.

    Args:
        request: Django's HTTP request object.
		username: The username of the user who just registered

    Returns:
        renders the static page, user - request.user.
		Appropiate error is sent if needed
    """
    context = {}
    # user who isn't username
    if request.user.is_authenticated() and request.user.username != username:
        context['errors'] = ['Access denied.']
        return render(request, 'caps/Home.html', context)
    student_user_arr = User.objects.filter(username=username)
    # check if username is a student
    if not student_user_arr or not hasattr(student_user_arr[0],'student'):
        #context['errors'] = ['Student ' + username + ' does not exist.']
        # We dont want to create "back door" for anyone can see if a username
        # exist or not using this URL - so we just write access denied.
        context['errors'] = ['Access denied.']
        return render(request, 'caps/Home.html', context)
	# check if username has already verified it's email
    if student_user_arr[0].is_active:
        context['errors'] = ['You already verified your email.']
        return render(request, 'caps/Home.html', context)
    context['username'] = username
    return render(request, 'caps/RegisterCheckEmail.html', context)

@transaction.atomic
@ensure_csrf_cookie
def validate_email(request, username, key):
    """ Validates the student's email.

    Args:
        request: Django's HTTP request object.
        username: the student's username.
        key: the key sent to the specified email.

    Returns:
        renders the static page, user - request.user.
		User will be logged in and sent to home page
		If key is wrong redirect to home page with an error

    """
    user = get_object_or_404(User, username=username)
    if hasattr(user, 'student'):
        if user.student.email_key == DEFAULT or user.student.email_key != key:
            context = {'errors': ['Access denied.']}
            return render(request, 'caps/Home.html', context)
        user.student.clear_email_key()
        user.is_active = True
        user.save()
    # auto login the user and redirect him to home page
    login(request, user)
    return redirect(reverse('home'))

@login_required
@ensure_csrf_cookie
def profile_student(request):
    """ Student profile page.

    Args:
        request: Django's HTTP request object.

    Returns:
        renders the student profile page with student's User - request.user.
    """
    if User.objects.filter(username=request.user, student__isnull=False):
        context = {
            'user': request.user,
        }
        if hasattr(request.user,'tasks_profile'):
            context['assigned_tasks'] = (
                get_assigned_tasks(request.user.tasks_profile))
        meetings = Meeting.objects.filter(student=request.user.student,
            end_datetime__gt=timezone.now())
        if meetings.count() >= 1:
            context['next_meeting'] = meetings[0] # meetings sorted by end_time
        return render(request, 'caps/ProfileStudent.html', context)
    else:
        context = {'errors':['Access denied to view student profile'],
            'user':request.user}
    return render(request, 'caps/Home.html', context)

def profile_student_for_counselor(request, username):
    """ Student profile page .

    Args:
        request: Django's HTTP request object.

    Returns:
        renders the student profile page with student's User - request.user.
    """
    context = {'user':request.user}
    # only a counselor is allowed to load this view
    if not hasattr(request.user,'counselor'):
        context['errors'] = ['Permission denied: not a counselor']
        return render(request, 'caps/Home.html', context)
    student_user_arr = User.objects.filter(username=username)
    # username is a student
    if not student_user_arr or not hasattr(student_user_arr[0],'student'):
        context['errors'] = ['Student ' + username + ' does not exist.']
        return render(request, 'caps/Home.html', context)
    student = student_user_arr[0].student
    # counselor is advising this student
    if not student in request.user.counselor.students_advising.all(): 
        context['errors'] = \
            ['Permission denied: You are not advising ' + username]
        return render(request, 'caps/Home.html', context)
    context = {
        'user': student.user, # or student_user_arr[0]
    }
    if hasattr(student.user, 'tasks_profile'):
        context['assigned_tasks'] = ( # the ( is for syntax convince
            get_assigned_tasks(student.user.tasks_profile))
    meetings = Meeting.objects.filter(student=student, 
        end_datetime__gt=timezone.now())
    if meetings.count() >= 1:
        context['next_meeting'] = meetings[0] # meetings sorted by end_time
    return render(request, 'caps/ProfileStudent.html', context)
    
@login_required
@ensure_csrf_cookie
def profile_counselor(request, username):
    """ Counselor profile page.

    Args:
        request: Django's HTTP request object.
        username: the counselor's username.

    Returns:
        renders the counselor profile page with counselor's User - request.user
        Returns an error in the contexts and redirects to home page if counselor
        username doesn't exist.
    """
    try:
        counselor_user = User.objects.get(username=username)
        # accessing the counselor attr will raise exception if the user exist
        # but is not a counselor
        counselor_user.counselor
        context = {'user': counselor_user}
        if request.user.username == username: # counselor viewing his profile
            meetings = Meeting.objects.filter(
                counselor=counselor_user.counselor,
                end_datetime__gt=timezone.now())
            if meetings.count() >= 1:
                context['next_meeting'] = meetings[0]
        return render(request, 'caps/ProfileCounselor.html', context)
    except ObjectDoesNotExist:  # Counselor does not exist in the DB
        context = {'errors':['Counselor ' + username + ' does not exist.'],
            'user':request.user}
        return render(request, 'caps/Home.html', context)

@transaction.atomic
@login_required
@ensure_csrf_cookie
def update_profile(request):
    """ Update student profile page.
	Counselor / Emergency / Receptionist edit their profile using admin console

    Args:
        request: Django's HTTP request object.

    Returns:
        GET - Create the form to edit the student information.
        POST - sends the form information and updates the DB.
    """
    for reason in SEEKING_HELP_REASONS:
        if not SeekingHelpReason.objects.filter(reason=reason):
            r = SeekingHelpReason(reason=reason)
            r.save()
    if request.method == 'GET':
        if User.objects.filter(username=request.user, student__isnull=False):
            context = {
                'user_form': UserForm(instance=request.user),
                'student_form': StudentForm(instance=request.user.student)}
            return render(request, 'caps/StudentUpdateProfile.html', context)
        context = {
            'errors': ['Only a student can edit his profile.\
				Please use CaPS Administration to edit your profile.'],
            'user': request.user}
        return render(request, 'caps/Home.html', context)

    # POST request
    user_form = UserForm(request.POST, instance=request.user)
    if User.objects.filter(username=request.user, student__isnull=False):
        student_form = StudentForm(
            request.POST, request.FILES, instance=request.user.student)

        if user_form.is_valid() and student_form.is_valid():
            user_form.save()
            student_form.save()
            return redirect(reverse('studentprofile'))
        else:
            context = {'user_form': user_form, 'student_form': student_form}
            return render(request, 'caps/StudentUpdateProfile.html', context)
    # if User.objects.filter(username=request.user, counselor__isnull=False):
        # counselor_form = CounselorForm(
            # request.POST, request.FILES, instance=request.user.counselor)
        # if user_form.is_valid() and counselor_form.is_valid():
            # user_form.save()
            # counselor_form.save()
            # return redirect(
                # reverse('counselorprofile', args=[request.user.username]))
        # else:
            # context = {
                # 'user_form': user_form, 'counselor_form': counselor_form}
            # render(request, 'caps/CounselorUpdateProfile.html', context)

@login_required
@ensure_csrf_cookie        
def counselor_list(request):
    """ List of active counselors

    Args:
        request: Django's HTTP request object.

    Returns:
        Renders a template with the active counselors' User objects in context
    """
    context = {'user': request.user,
    'counselor_users': User.objects.filter(
        counselor__isnull=False, is_active=True)}
    return render(request, 'caps/CounselorList.html', context)
    
# Task related views
@login_required
@ensure_csrf_cookie
def student_exercise(request, task_id):
    context = {'user': request.user}
    # only a student is allowed to load this view
    if not hasattr(request.user,'student'):
        context['errors'] = ['Access denied: you are not a student']
        return render(request, 'caps/Home.html', context)
    try:
        context['task'] = init_task(request.user.tasks_profile, task_id)
    except TasksError as error:
        context['errors'] = [str(error)]
        return render(request, 'caps/Home.html', context)
    return render(request, 'tasks/Task.html', context)
