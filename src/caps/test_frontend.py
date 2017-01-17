from django.test import TestCase, Client
from django.db import transaction
from django.db.utils import IntegrityError

from channels import Channel
from channels.tests import ChannelTestCase, HttpClient

from django_webtest import WebTest

from caps.models import *
from caps.views import *
from caps.consumers import *
from tasks.models import *
from tasks.views import *

import datetime
import warnings

from django.utils import timezone

# From_encoding warning of BS is a python webtest module issue
warnings.filterwarnings(
    'ignore', 'You provided Unicode markup but also provided a value for '
    'from_encoding. Your from_encoding will be ignored.') 

# First name used as account type reference
ACCOUNTS = [
    {'username': 'aureliopg',
     'password': 'dummy1',
     'first_name': EMERGENCY,
     'last_name': 'Puebla Gutierrez',
     'email': 'a@a.com'},

    {'username': 'carlosp',
     'password': 'dummy2',
     'first_name': EMERGENCY,
     'last_name': 'Perez',
     'email': 'b@a.com'},

    {'username': 'marcop',
     'password': 'dummy3',
     'first_name': COUNSELOR,
     'last_name': 'Peyrot',
     'email': 'c@a.com'},

    {'username': 'galf',
     'password': 'dummy4',
     'first_name': COUNSELOR,
     'last_name': 'Fisher',
     'email': 'd@a.com'},

    {'username': 'lauram',
     'password': 'dummy5',
     'first_name': RECEPTIONIST,
     'last_name': 'Miller',
     'email': 'e@a.com'},

    {'username': 'armandog',
     'password': 'dummy6',
     'first_name': STUDENT,
     'last_name': 'Gutierrez',
     'email': 'f@a.com'},

    {'username': 'danielf',
     'password': 'dummy7',
     'first_name': STUDENT,
     'last_name': 'Flores',
     'email': 'g@a.com'},
]

PROFILE_FILLERS = {
    'seniority': 5,
    'age': 30,
    'picture': DEFAULT_PROFILE_PICTURE
}

FULL_COUNSELOR_PROFILE_FILLERS = {
    'position_title': "Therapist",
    'gender': 'Female',
    'degree': 'PhD',
    'seniority': 10,
    'age': 42,
    'school': "CMU",
    'bio': 'This is a bio.',
    'picture': DEFAULT_PROFILE_PICTURE
}

STUDENT_PROFILE_FILLERS = {
    'picture': DEFAULT_PROFILE_PICTURE
}

MEETING_FILLERS = {
    'start_datetime': timezone.now() - datetime.timedelta(hours=1),
    'end_datetime': timezone.now() + datetime.timedelta(hours=1)
}

# Checks if all pages use correct templates to render pages
class TemplateTests(TestCase):

    def setUp(self):
        new_task = Task(name="Compatibility Measures",
                        interface="Compatibility.js")
        new_task.save()
        for account in ACCOUNTS:
            new_user = User.objects.create_user(**account)
            if account['first_name'] == COUNSELOR:
                new_profile = Counselor(user=new_user, **PROFILE_FILLERS)
                new_profile.save()
            elif account['first_name'] == STUDENT:
                new_profile = Student(user=new_user, **STUDENT_PROFILE_FILLERS)
                new_profile.save()
                create_profile(new_user)

        new_task = Task(name="Test", interface="Test.js")
        new_task.save()
        new_assigned_task = AssignedTask(task=new_task,
                                         tasks_profile=User.objects.get(
                                            username='danielf').tasks_profile
                                         )
        new_assigned_task.save()


    def test_home_template(self):
        """ Home Template Usage """
        client = Client()
        response = client.get('/')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/Home.html')

    def test_services_template(self):
        """ Services Template Usage """
        client = Client()
        response = client.get('/caps/services')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/Services.html')

    def test_resources_template(self):
        """ Resources Template Usage """
        client = Client()
        response = client.get('/caps/resources')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/Resources.html')

    def test_contact_template(self):
        """ Contacts Template Usage """
        client = Client()
        response = client.get('/caps/contact')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/Contact.html')

    def test_login_template(self):
        """ Login Template Usage """
        client = Client()
        response = client.get('/caps/login')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateNotUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/Login.html')

    def test_register_template(self):
        """ Register Template Usage """
        client = Client()
        response = client.get('/caps/register')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateNotUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/Register.html')

    def test_registerdesc_template(self):
        """ RegisterDesc Template Usage """
        client = Client()
        response = client.get('/caps/registerdesc')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/RegisterDesc.html')

    def test_student_template(self):
        """ Student Profile Template Usage """
        self.client.login(username='danielf', password='dummy7')
        response = self.client.get('/caps/studentprofile')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateNotUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/ProfileStudent.html')

    def test_studentupdate_template(self):
        """ Student Profile Update Template Usage """
        self.client.login(username='danielf', password='dummy7')
        response = self.client.get('/caps/updateprofile')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateNotUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/StudentUpdateProfile.html')

    def test_counselor_template(self):
        """ Counselor Profile Template Usage """
        self.client.login(username='danielf', password='dummy7')
        response = self.client.get('/caps/counselorprofile/galf')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateNotUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/ProfileCounselor.html')

    def test_counselorlist_template(self):
        """ Counselor List Template Usage """
        self.client.login(username='danielf', password='dummy7')
        response = self.client.get('/caps/counselor_list')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateNotUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'caps/CounselorList.html')

    def test_task_template(self):
        """ Task Template Usage """
        self.client.login(username='danielf', password='dummy7')
        response = self.client.get('/caps/student_exercise/1')
        self.assertTemplateUsed(response, 'caps/Base.html')
        self.assertTemplateNotUsed(response, 'caps/BaseHome.html')
        self.assertTemplateUsed(response, 'tasks/Task.html')


# Checks page interactions for a non-authenticated user
class NonAuthUserTests(WebTest):

    def setUp(self):
        new_task = Task(name="Compatibility Measures",
                        interface="Compatibility.js")
        new_task.save()

    def test_home_page(self):
        """ Unauthorized User Homepage Display """
        home = self.app.get('/')
        self.assertEqual(home.status, '200 OK')
        self.assertTrue('mainNav' in home)
        self.assertTrue('homeNav' in home)
        self.assertTrue('We\'re here to help' in home)
        self.assertTrue('Health Tips' in home)
        # navbar
        self.assertTrue('Profile' not in home)
        self.assertTrue('Edit' not in home)
        self.assertTrue('Logout' not in home)
        self.assertTrue('Login' in home)
        # buttons
        self.assertTrue('Chat with your counselor' not in home)
        self.assertTrue('Schedule an Appointment' not in home)
        self.assertTrue('Emergency Response' not in home)
        self.assertTrue('Chat with Student' not in home)
        self.assertTrue('Schedule with Student' not in home)
        self.assertTrue('Get Emergency Help' in home)

    def test_home_navbar_links(self):
        """ Unauthorized User Follow Navbar Links """
        # Get the home page
        home = self.app.get('/')
        self.assertEqual(home.status, '200 OK')

        # Click the "Get Support" link to make sure it goes to the right page
        support = home.click('Get Support')
        self.assertEqual(support.status, '200 OK')
        self.assertTrue('We\'re here to help' in support)
        self.assertTrue('Our Staff' in support)
        self.assertTrue('Register' in support)

        # Click the "Services" link to make sure it goes to the right page
        services = home.click('Services')
        self.assertEqual(services.status, '200 OK')
        self.assertTrue('Consultation' in services)
        self.assertTrue('Individual Therapy' in services)
        self.assertTrue('Outreach and Educational Presentations' in services)
        self.assertTrue('Referrals' in services)
        self.assertTrue('Psychiatric Care' in services)

        # Click the "Resources" link to make sure it goes to the right page
        resources = home.click('Resources')
        self.assertEqual(resources.status, '200 OK')
        self.assertTrue('On-Campus Resources' in resources)
        self.assertTrue('Local Resources' in resources)

        # Click the "Contact" link to make sure it goes to the right page
        contact = home.click('Contact')
        self.assertEqual(contact.status, '200 OK')
        self.assertTrue('Phone Number' in contact)
        self.assertTrue('Office Hours' in contact)
        self.assertTrue('Office Location' in contact)

    def test_registration_form_correct(self):
        """ Unauthorized User Correct Registration Form Submit """
        register = self.app.get('/caps/registerdesc')
        self.assertEqual(register.status, '200 OK')

        register = register.click('Register')
        self.assertEqual(register.status, '200 OK')
        reg_form = register.form

        self.assertEqual('/caps/register', reg_form.action)
        self.assertEqual(len(reg_form.fields.values()), 8)

        reg_form['username'] = 'FooBar'
        reg_form['first_name'] = 'Foo'
        reg_form['last_name'] = 'Bar'
        reg_form['password'] = 'Baz'
        reg_form['confirm_password'] = 'Baz'
        register = reg_form.submit('submit')
        self.assertEqual(register.status, '302 Found')
        self.assertEqual(register.location, '/caps/check_email/FooBar')
        register = register.follow()
        self.assertEqual(register.status, '200 OK')
        self.assertTrue(
            'A confirmation email was sent to' in register)


    def test_registration_form_incorrect_password(self):
        """ Unauthorized User Incorrect Password Registration Form Submit """
        register = self.app.get('/caps/register')
        self.assertEqual(register.status, '200 OK')

        reg_form = register.form
        self.assertEqual('/caps/register', reg_form.action)
        self.assertEqual(len(reg_form.fields.values()), 8)

        reg_form['username'] = 'FooBar'
        reg_form['first_name'] = 'Foo'
        reg_form['last_name'] = 'Bar'
        reg_form['password'] = 'Baz'
        reg_form['confirm_password'] = 'NotBaz'
        register = reg_form.submit('submit')
        self.assertEqual(register.status, '200 OK')
        self.assertTrue('Passwords do not match' in register)


    def test_registration_form_incorrect_username_taken(self):
        """ Unauthorized User Incorrect Username Taken Registration Form""" + \
        """ Submit """
        # Register once as FooBar
        register = self.app.get('/caps/register')
        self.assertEqual(register.status, '200 OK')
        reg_form = register.form

        self.assertEqual('/caps/register', reg_form.action)
        self.assertEqual(len(reg_form.fields.values()), 8)

        reg_form['username'] = 'FooBar'
        reg_form['first_name'] = 'Foo'
        reg_form['last_name'] = 'Bar'
        reg_form['password'] = 'Baz'
        reg_form['confirm_password'] = 'Baz'
        register = reg_form.submit('submit')

        # Try to register again as FooBar
        register = self.app.get('/caps/register')
        self.assertEqual(register.status, '200 OK')
        reg_form = register.form

        self.assertEqual('/caps/register', reg_form.action)
        self.assertEqual(len(reg_form.fields.values()), 8)

        reg_form['username'] = 'FooBar'
        reg_form['first_name'] = 'Foo'
        reg_form['last_name'] = 'Bar'
        reg_form['password'] = 'Baz'
        reg_form['confirm_password'] = 'Baz'
        register = reg_form.submit('submit')
        self.assertTrue('AndrewID FooBar already exists' in register)

    def test_registration_form_incorrect_username_not_filled_in(self):
        """ Unauthorized User Incorrect Username Not Filled In""" + \
         """Registration Form Submit """
        register = self.app.get('/caps/register')
        self.assertEqual(register.status, '200 OK')

        reg_form = register.form
        self.assertEqual('/caps/register', reg_form.action)
        self.assertEqual(len(reg_form.fields.values()), 8)

        reg_form['first_name'] = 'Foo'
        reg_form['last_name'] = 'Bar'
        reg_form['password'] = 'Baz'
        reg_form['confirm_password'] = 'Baz'
        register = reg_form.submit('submit')
        self.assertEqual(register.status, '200 OK')
        self.assertTrue('This field is required.' in register)

    def test_registration_form_incorrect_first_name_not_filled_in(self):
        """ Unauthorized User Incorrect First Name Not Filled In""" + \
        """ Registration Form Submit """
        register = self.app.get('/caps/register')
        self.assertEqual(register.status, '200 OK')

        reg_form = register.form
        self.assertEqual('/caps/register', reg_form.action)
        self.assertEqual(len(reg_form.fields.values()), 8)

        reg_form['username'] = 'FooBar'
        reg_form['last_name'] = 'Bar'
        reg_form['password'] = 'Baz'
        reg_form['confirm_password'] = 'Baz'
        register = reg_form.submit('submit')
        self.assertEqual(register.status, '200 OK')
        self.assertTrue('This field is required.' in register)

    def test_registration_form_incorrect_last_name_not_filled_in(self):
        """ Unauthorized User Incorrect Last Name Not Filled In""" + \
        """ Registration Form Submit """
        register = self.app.get('/caps/register')
        self.assertEqual(register.status, '200 OK')

        reg_form = register.form
        self.assertEqual('/caps/register', reg_form.action)
        self.assertEqual(len(reg_form.fields.values()), 8)

        reg_form['username'] = 'FooBar'
        reg_form['first_name'] = 'Foo'
        reg_form['password'] = 'Baz'
        reg_form['confirm_password'] = 'Baz'
        register = reg_form.submit('submit')
        self.assertEqual(register.status, '200 OK')
        self.assertTrue('This field is required.' in register)

    def test_registration_form_incorrect_password_not_filled_in(self):
        """ Unauthorized User Incorrect Password Not Filled In""" + \
        """ Registration Form Submit """
        register = self.app.get('/caps/register')
        self.assertEqual(register.status, '200 OK')

        reg_form = register.form
        self.assertEqual('/caps/register', reg_form.action)
        self.assertEqual(len(reg_form.fields.values()), 8)

        reg_form['username'] = 'FooBar'
        reg_form['first_name'] = 'Foo'
        reg_form['last_name'] = 'Bar'
        reg_form['confirm_password'] = 'Baz'
        register = reg_form.submit('submit')
        self.assertEqual(register.status, '200 OK')
        self.assertTrue('This field is required.' in register)

    def test_registration_form_incorrect_confirm_password_not_filled_in(self):
        """ Unauthorized User Incorrect Confirm Not Filled In""" + \
        """ Registration Form Submit """
        register = self.app.get('/caps/register')
        self.assertEqual(register.status, '200 OK')

        reg_form = register.form
        self.assertEqual('/caps/register', reg_form.action)
        self.assertEqual(len(reg_form.fields.values()), 8)

        reg_form['username'] = 'FooBar'
        reg_form['first_name'] = 'Foo'
        reg_form['last_name'] = 'Bar'
        reg_form['password'] = 'Baz'
        register = reg_form.submit('submit')
        self.assertEqual(register.status, '200 OK')
        self.assertTrue('This field is required.' in register)

    def test_login_form_incorrect_unregistered(self):
        """ Unauthorized User Incorrect Unregistered Login Form Submit """
        login = self.app.get('/caps/login')
        self.assertEqual(login.status, '200 OK')

        log_form = login.form

        self.assertEqual('/caps/login', log_form.action)
        self.assertEqual(len(log_form.fields.values()), 5)

        log_form['username'] = 'FooBar'
        log_form['password'] = 'Baz'
        login = log_form.submit('submit')
        self.assertEqual(login.status, '200 OK')
        self.assertTrue('Please enter a correct username and password. Note '
                        'that both fields may be case-sensitive.' in login)

    def test_login_form_incorrect_registered_but_not_confirmed(self):
        """ Unauthorized User Incorrect Registered But Not""" + \
        """ Confirmed Login Form Submit """
        # Register but don't confirm email
        register = self.app.get('/caps/registerdesc')
        self.assertEqual(register.status, '200 OK')

        register = register.click('Register')
        self.assertEqual(register.status, '200 OK')
        reg_form = register.form

        self.assertEqual('/caps/register', reg_form.action)
        self.assertEqual(len(reg_form.fields.values()), 8)

        reg_form['username'] = 'FooBar'
        reg_form['first_name'] = 'Foo'
        reg_form['last_name'] = 'Bar'
        reg_form['password'] = 'Baz'
        reg_form['confirm_password'] = 'Baz'
        register = reg_form.submit('submit')
        self.assertEqual(register.status, '302 Found')
        self.assertEqual(register.location, '/caps/check_email/FooBar')
        register = register.follow()
        self.assertEqual(register.status, '200 OK')
        self.assertTrue('A confirmation email was sent to' in register)

        # Login without confirming email
        login = self.app.get('/caps/login')
        self.assertEqual(login.status, '200 OK')

        log_form = login.form

        self.assertEqual('/caps/login', log_form.action)
        self.assertEqual(len(log_form.fields.values()), 5)

        log_form['username'] = 'FooBar'
        log_form['password'] = 'Baz'
        login = log_form.submit('submit')
        self.assertEqual(login.status, '200 OK')
        # In the future, make this error message more useful to this situation.
        self.assertTrue('Please enter a correct username and password. ' + \
                        'Note that both fields may be case-sensitive.' in login)

    def test_cannot_access_student_profile(self):
        """ Unauthorized User Cannot Access Student Profile """
        student_profile = self.app.get('/caps/studentprofile')
        self.assertEqual(student_profile.status, '302 Found')
        self.assertEqual(student_profile.location,
                         '/caps/?next=/caps/studentprofile')

        # Should redirect to home page
        student_profile = student_profile.follow()
        self.assertEqual(student_profile.status, '200 OK')
        self.assertTrue('mainNav' in student_profile)
        self.assertTrue('homeNav' in student_profile)
        self.assertTrue('We\'re here to help' in student_profile)
        self.assertTrue('Health Tips' in student_profile)

    def test_cannot_access_counselor_profile(self):
        """ Unauthorized User Cannot Access Counselor Profile """
        counselor_profile = self.app.get('/caps/counselorprofile/FooBar')
        self.assertEqual(counselor_profile.status, '302 Found')
        self.assertEqual(counselor_profile.location,
                         '/caps/?next=/caps/counselorprofile/FooBar')

        # Should redirect to home page
        counselor_profile = counselor_profile.follow()
        self.assertEqual(counselor_profile.status, '200 OK')
        self.assertTrue('mainNav' in counselor_profile)
        self.assertTrue('homeNav' in counselor_profile)
        self.assertTrue('We\'re here to help' in counselor_profile)
        self.assertTrue('Health Tips' in counselor_profile)

    def test_cannot_access_update_profile(self):
        """ Unauthorized User Cannot Access Update Profile """
        update_profile = self.app.get('/caps/updateprofile')
        self.assertEqual(update_profile.status, '302 Found')
        self.assertEqual(update_profile.location,
                         '/caps/?next=/caps/updateprofile')

        # Should redirect to home page
        update_profile = update_profile.follow()
        self.assertEqual(update_profile.status, '200 OK')
        self.assertTrue('mainNav' in update_profile)
        self.assertTrue('homeNav' in update_profile)
        self.assertTrue('We\'re here to help' in update_profile)
        self.assertTrue('Health Tips' in update_profile)

    def test_cannot_access_counselor_list(self):
        """ Unauthorized User Cannot Access Counselor List """
        update_profile = self.app.get('/caps/counselor_list')
        self.assertEqual(update_profile.status, '302 Found')
        self.assertEqual(update_profile.location,
                         '/caps/?next=/caps/counselor_list')

        # Should redirect to home page
        update_profile = update_profile.follow()
        self.assertEqual(update_profile.status, '200 OK')
        self.assertTrue('mainNav' in update_profile)
        self.assertTrue('homeNav' in update_profile)
        self.assertTrue('We\'re here to help' in update_profile)
        self.assertTrue('Health Tips' in update_profile)

# Checks page interactions for an authenticated student user
    # Student
    # Can login
    # Can visit pages that require login
    # Home page
        # Profile, Edit, Logout exist in navbar, Login does not
        # Correct chat buttons exist
    # Profile
        # Can click relevant links (counselor)
        # Correct items displayed based on what they've filled out
    # Profile edit
        # Correct and incorrect cases
class AuthStudentTests(WebTest):

    def setUp(self):
        new_task = Task(name="Compatibility Measures",
                        interface="Compatibility.js")
        new_task.save()
        for account in ACCOUNTS:
            new_user = User.objects.create_user(**account)
            if account['first_name'] == COUNSELOR:
                new_profile = Counselor(user=new_user, **PROFILE_FILLERS)
                new_profile.save()
            elif account['first_name'] == STUDENT:
                if account['username'] == 'danielf':
                    new_profile = Student(user=new_user,
                                          counselor=Counselor.objects.get(
                                              user=User.objects.get(
                                                  username='galf')),
                                          **STUDENT_PROFILE_FILLERS)
                else:
                    new_profile = Student(user=new_user,
                                          **STUDENT_PROFILE_FILLERS)
                new_profile.save()
                create_profile(new_user)

        new_meeting = Meeting(student=Student.objects.get(
                                        user=User.objects.get(
                                            username='danielf')),
                              counselor=Counselor.objects.get(
                                        user=User.objects.get(
                                            username='galf')),
                              **MEETING_FILLERS)

        new_task = Task(name="Test", interface="Test.js")
        new_task.save()
        new_assigned_task = AssignedTask(task=new_task,
                                         tasks_profile=User.objects.get(
                                            username='danielf').tasks_profile
                                         )
        new_assigned_task.save()
        new_meeting.save()

    def test_home_page_no_meeting(self):
        """ Authorized Student User Homepage Display With No""" + \
        """ Meeting Scheduled """
        home = self.app.get('/', user='armandog')
        self.assertEqual(home.status, '200 OK')
        self.assertTrue('mainNav' in home)
        self.assertTrue('homeNav' in home)
        self.assertTrue('We\'re here to help' in home)
        self.assertTrue('Health Tips' in home)
        # navbar
        self.assertTrue('Profile' in home)
        self.assertTrue('Edit' in home)
        self.assertTrue('Logout' in home)
        self.assertTrue('Login' not in home)
        # buttons
        self.assertTrue('Chat with your counselor' not in home)
        self.assertTrue('Schedule an Appointment' in home)
        self.assertTrue('Emergency Response' not in home)
        self.assertTrue('Chat with Student' not in home)
        self.assertTrue('Schedule with Student' not in home)
        self.assertTrue('Get Emergency Help' in home)

    def test_home_page_meeting(self):
        """ Authorized Student User Homepage Display With Meeting Scheduled """
        home = self.app.get('/', user='danielf')
        self.assertEqual(home.status, '200 OK')
        self.assertTrue('mainNav' in home)
        self.assertTrue('homeNav' in home)
        self.assertTrue('We\'re here to help' in home)
        self.assertTrue('Health Tips' in home)
        # navbar
        self.assertTrue('Profile' in home)
        self.assertTrue('Edit' in home)
        self.assertTrue('Logout' in home)
        self.assertTrue('Login' not in home)
        # buttons
        self.assertTrue('Chat with your counselor' in home)
        self.assertTrue('Schedule an Appointment' in home)
        self.assertTrue('Emergency Response' not in home)
        self.assertTrue('Chat with Student' not in home)
        self.assertTrue('Schedule with Student' not in home)
        self.assertTrue('Get Emergency Help' in home)

    def test_no_registration_form(self):
        """ Authorized Student User No Registration Form Shown""" + \
        """ on Registation Page """
        home = self.app.get('/', user='armandog')
        self.assertEqual(home.status, '200 OK')

        register = home.click('Get Support')
        self.assertEqual(register.status, '200 OK')

        self.assertTrue('You\'re already registered!' in register)

        with self.assertRaises(TypeError):
            reg_form = register.form

    def test_student_can_login(self):
        """ Student User Can Login """
        login = self.app.get('/caps/login')
        self.assertEqual(login.status, '200 OK')

        log_form = login.form

        self.assertEqual('/caps/login', log_form.action)
        self.assertEqual(len(log_form.fields.values()), 5)

        log_form['username'] = 'danielf'
        log_form['password'] = 'dummy7'
        login = log_form.submit('submit')
        self.assertEqual(login.status, '302 Found')
        self.assertEqual(login.location, '/caps/')

    def test_student_profile_display(self):
        """ Authorized Student User Default Profile Display """
        home = self.app.get('/caps/studentprofile', user='armandog')
        self.assertEqual(home.status, '200 OK')

        profile = home.click('Profile', index=0)
        self.assertEqual(profile.status, '200 OK')

        self.assertTrue(STUDENT in profile)
        self.assertTrue('Gutierrez' in profile)
        self.assertTrue('Please edit your profile to add your class year.'
                        in profile)
        self.assertTrue('Please edit your profile to add your major.'
                        in profile)
        self.assertTrue('Please edit your profile to set your age and gender.'
                        in profile)
        self.assertTrue('Please edit your profile to set your gender.'
                        not in profile)
        self.assertTrue('Please edit your profile to set your age.'
                        not in profile)
        self.assertTrue('You haven\'t been assigned a counselor yet.'
                        in profile)
        self.assertTrue('Please edit your profile to tell us a little bit more about yourself.' in profile)
        self.assertTrue('Please specify the reason(s) you seek CaPS help, so we can help you better.' in profile)

    def test_student_profile_display_with_counselor(self):
        """ Authorized Student User Default Profile Display""" + \
        """ If Assigned a Counselor """
        home = self.app.get('/caps/studentprofile', user='danielf')
        self.assertEqual(home.status, '200 OK')

        profile = home.click('Profile', index=0)
        self.assertEqual(profile.status, '200 OK')

        self.assertTrue(STUDENT in profile)
        self.assertTrue('Flores' in profile)
        self.assertTrue('Please edit your profile to add your class year.'
                        in profile)
        self.assertTrue('Please edit your profile to add your major.'
                        in profile)
        self.assertTrue('Please edit your profile to set your age and gender.'
                        in profile)
        self.assertTrue('Please edit your profile to set your gender.'
                        not in profile)
        self.assertTrue('Please edit your profile to set your age.'
                        not in profile)
        self.assertTrue('You haven\'t been assigned a counselor yet.'
                        not in profile)
        self.assertTrue('Please edit your profile to tell us a little bit more about yourself.' in profile)
        self.assertTrue('Please specify the reason(s) you seek CaPS help, so we can help you better.' in profile)

        self.assertTrue('Counselor:' in profile)
        self.assertTrue('counselor Fisher' in profile)

        # Make sure link associated with counselor leads to correct profile
        profile = profile.click('counselor Fisher')

        self.assertTrue('counselor' in profile)
        self.assertTrue('30 years old' in profile)
        self.assertTrue('5 years experience' in profile)

    def test_student_profile_display_with_meeting(self):
        """ Authorized Student User Default Profile Display With a Meeting """
        home = self.app.get('/caps/studentprofile', user='danielf')
        self.assertEqual(home.status, '200 OK')

        profile = home.click('Profile', index=0)
        self.assertEqual(profile.status, '200 OK')

        self.assertTrue(STUDENT in profile)
        self.assertTrue('Flores' in profile)
        self.assertTrue('Please edit your profile to add your class year.'
                        in profile)
        self.assertTrue('Please edit your profile to add your major.'
                        in profile)
        self.assertTrue('Please edit your profile to set your age and gender.'
                        in profile)
        self.assertTrue('Please edit your profile to set your gender.'
                        not in profile)
        self.assertTrue('Please edit your profile to set your age.'
                        not in profile)
        self.assertTrue('You haven\'t been assigned a counselor yet.'
                        not in profile)
        self.assertTrue('Please edit your profile to tell us a little bit more about yourself.' in profile)
        self.assertTrue('Please specify the reason(s) you seek CaPS help, so we can help you better.' in profile)

        # Will also display current time
        self.assertTrue('Next Appointment: galf with danielf at' in profile)

    def test_student_profile_display_with_task(self):
        """ Authorized Student User Default Profile Display With a Task """
        home = self.app.get('/caps/studentprofile', user='danielf')
        self.assertEqual(home.status, '200 OK')

        profile = home.click('Profile', index=0)
        self.assertEqual(profile.status, '200 OK')

        self.assertTrue(STUDENT in profile)
        self.assertTrue('Flores' in profile)
        self.assertTrue('Please edit your profile to add your class year.'
                        in profile)
        self.assertTrue('Please edit your profile to add your major.'
                        in profile)
        self.assertTrue('Please edit your profile to set your age and gender.'
                        in profile)
        self.assertTrue('Please edit your profile to set your gender.'
                        not in profile)
        self.assertTrue('Please edit your profile to set your age.'
                        not in profile)
        self.assertTrue('You haven\'t been assigned a counselor yet.'
                        not in profile)
        self.assertTrue('Please edit your profile to tell us a little bit more about yourself.' in profile)
        self.assertTrue('Please specify the reason(s) you seek CaPS help, so we can help you better.' in profile)

        self.assertTrue('Name' in profile)
        self.assertTrue('Status' in profile)
        self.assertTrue('Deadline' in profile)
        self.assertTrue('Test' in profile)
        self.assertTrue('Not Started' in profile)
        self.assertTrue('None' in profile)

    def test_student_profile_display_without_task(self):
        """ Authorized Student User Default Profile Display Without a Task """
        home = self.app.get('/caps/studentprofile', user='armandog')
        self.assertEqual(home.status, '200 OK')

        profile = home.click('Profile', index=0)
        self.assertEqual(profile.status, '200 OK')

        self.assertTrue(STUDENT in profile)
        self.assertTrue('Gutierrez' in profile)
        self.assertTrue('Please edit your profile to add your class year.'
                        in profile)
        self.assertTrue('Please edit your profile to add your major.'
                        in profile)
        self.assertTrue('Please edit your profile to set your age and gender.'
                        in profile)
        self.assertTrue('Please edit your profile to set your gender.'
                        not in profile)
        self.assertTrue('Please edit your profile to set your age.'
                        not in profile)
        self.assertTrue('Please edit your profile to tell us a little bit more about yourself.' in profile)
        self.assertTrue('Please specify the reason(s) you seek CaPS help, so we can help you better.' in profile)


    def test_student_update_profile_incorrect_no_required(self):
        """ Student User Cannot Update Profile Without Required Fields """
        update = self.app.get('/', user='armandog')
        self.assertEqual(update.status, '200 OK')

        update = update.click('Edit', index=0)
        self.assertEqual(update.status, '200 OK')

        update_form = update.form

        self.assertEqual('/caps/updateprofile', update_form.action)
        self.assertEqual(len(update_form.fields.values()), 14)

        update = update_form.submit('submit')
        self.assertEqual(update.status, '200 OK')

        self.assertTrue("This field is required." in update)


    def test_student_update_profile_incorrect_one_required_gender(self):
        """ Student User Cannot Update Profile Without Required Field Gender """
        update = self.app.get('/', user='armandog')
        self.assertEqual(update.status, '200 OK')

        update = update.click('Edit', index=0)
        self.assertEqual(update.status, '200 OK')

        update_form = update.form

        self.assertEqual('/caps/updateprofile', update_form.action)
        self.assertEqual(len(update_form.fields.values()), 14)

        update_form['gender'] = 'Male'

        update = update_form.submit('submit')
        self.assertEqual(update.status, '200 OK')

        self.assertTrue("This field is required." in update)


    def test_student_update_profile_incorrect_one_required_class_year(self):
        """ Student User Cannot Update Profile Without"""  + \
        """ Required Field Class Year """
        update = self.app.get('/', user='armandog')
        self.assertEqual(update.status, '200 OK')

        update = update.click('Edit', index=0)
        self.assertEqual(update.status, '200 OK')

        update_form = update.form

        self.assertEqual('/caps/updateprofile', update_form.action)
        self.assertEqual(len(update_form.fields.values()), 14)

        update_form['class_year'] = 'Freshman'

        update = update_form.submit('submit')
        self.assertEqual(update.status, '200 OK')

        self.assertTrue("This field is required." in update)


    def test_student_update_profile_correct_all(self):
        """ Student User Can Update Profile With All Fields """
        update = self.app.get('/', user='armandog')
        self.assertEqual(update.status, '200 OK')

        update = update.click('Edit', index=0)
        self.assertEqual(update.status, '200 OK')

        update_form = update.form

        self.assertEqual('/caps/updateprofile', update_form.action)
        self.assertEqual(len(update_form.fields.values()), 14)

        update_form['first_name'] = 'Foo'
        update_form['last_name'] = 'Bar'
        update_form['preferred_name'] = 'Baz'
        update_form['age'] = '42'
        update_form['gender'] = 'Male'
        update_form['major'] = 'Computer Science'
        update_form['class_year'] = 'Freshman'
        update_form['bio'] = 'This is a bio.'
        #update_form['picture']

        update = update_form.submit('submit')

        self.assertEqual(update.status, '302 Found')
        self.assertEqual(update.location, '/caps/studentprofile')

        profile = update.follow()
        self.assertEqual(profile.status, '200 OK')

        self.assertTrue(STUDENT in profile)
        self.assertTrue('Foo' in profile)
        self.assertTrue('Bar' in profile)
        self.assertTrue('Baz' in profile)
        self.assertTrue('Please edit your profile to add your class year.'
                        not in profile)
        self.assertTrue('Freshman' in profile)
        self.assertTrue('Please edit your profile to add your major.'
                        not in profile)
        self.assertTrue('Computer Science' in profile)
        self.assertTrue('Please edit your profile to set your age and gender.'
                        not in profile)
        self.assertTrue('Please edit your profile to set your age.'
                        not in profile)
        self.assertTrue('Please edit your profile to set your gender.'
                        not in profile)
        self.assertTrue('42' in profile)
        self.assertTrue('/ Male' in profile)
        self.assertTrue('You haven\'t been assigned a counselor yet.'
                        in profile)
        self.assertTrue('Please edit your profile to tell us a little bit more about yourself.' not in profile)
        self.assertTrue('This is a bio.' in profile)
        self.assertTrue('Please specify the reason(s) you seek CaPS help, so we can help you better.' in profile)

    def test_student_update_profile_correct_all_but_age(self):
        """ Student User Can Update Profile With All Fields But Age """
        update = self.app.get('/', user='armandog')
        self.assertEqual(update.status, '200 OK')

        update = update.click('Edit', index=0)
        self.assertEqual(update.status, '200 OK')

        update_form = update.form

        self.assertEqual('/caps/updateprofile', update_form.action)
        self.assertEqual(len(update_form.fields.values()), 14)

        update_form['first_name'] = 'Foo'
        update_form['last_name'] = 'Bar'
        update_form['preferred_name'] = 'Baz'
        update_form['gender'] = 'Male'
        update_form['major'] = 'Computer Science'
        update_form['class_year'] = 'Freshman'
        update_form['bio'] = 'This is a bio.'
        #update_form['picture']

        update = update_form.submit('submit')

        self.assertEqual(update.status, '302 Found')
        self.assertEqual(update.location, '/caps/studentprofile')

        profile = update.follow()
        self.assertEqual(profile.status, '200 OK')

        self.assertTrue(STUDENT in profile)
        self.assertTrue('Foo' in profile)
        self.assertTrue('Bar' in profile)
        self.assertTrue('Baz' in profile)
        self.assertTrue('Please edit your profile to add your class year.'
                        not in profile)
        self.assertTrue('Freshman' in profile)
        self.assertTrue('Please edit your profile to add your major.'
                        not in profile)
        self.assertTrue('Computer Science' in profile)
        self.assertTrue('Please edit your profile to set your age and gender.'
                        not in profile)
        self.assertTrue('Please edit your profile to set your age.'
                        in profile)
        self.assertTrue('Please edit your profile to set your gender.'
                        not in profile)
        self.assertTrue('Male' in profile)
        self.assertTrue('You haven\'t been assigned a counselor yet.'
                        in profile)
        self.assertTrue('Please edit your profile to tell us a little bit more about yourself.' not in profile)
        self.assertTrue('This is a bio.' in profile)
        self.assertTrue('Please specify the reason(s) you seek CaPS help, so we can help you better.' in profile)

    def test_can_access_student_profile(self):
        """ Authorized Student User Can Access Student Profile """
        student_profile = self.app.get('/caps/studentprofile', user='armandog')

        self.assertEqual(student_profile.status, '200 OK')

    def test_can_access_counselor_profile(self):
        """ Authorized Student User Can Access Counselor Profile """
        counselor_profile = self.app.get('/caps/counselorprofile/marcop',
                                         user='armandog')

        self.assertEqual(counselor_profile.status, '200 OK')
        self.assertTrue('Next Appointment' not in counselor_profile)
        self.assertTrue('You aren\'t advising any students currently.'
                        not in counselor_profile)
        self.assertTrue('Student Name' not in counselor_profile)

    def test_cannot_access_fake_counselor_profile(self):
        """ Authorized Student User Cannot Access Counselor""" + \
        """ Profile That Doesn't Exist """
        counselor_profile = self.app.get('/caps/counselorprofile/FooBar',
                                         user='armandog')

        self.assertEqual(counselor_profile.status, '200 OK')

        self.assertTrue('Counselor FooBar does not exist.' in counselor_profile)

    def test_can_access_update_profile(self):
        """ Authorized Student User Can Access Update Profile """
        update_profile = self.app.get('/caps/updateprofile', user='armandog')
        self.assertEqual(update_profile.status, '200 OK')

        self.assertTrue('Update Profile' in update_profile)

    def test_can_access_counselor_list(self):
        """ Authorized Student User Cannot Access Counselor List """
        counselor_list = self.app.get('/caps/counselor_list', user='armandog')
        self.assertEqual(counselor_list.status, '200 OK')

        self.assertTrue('Username' in counselor_list)
        self.assertTrue('First Name' in counselor_list)
        self.assertTrue('Last Name' in counselor_list)
        self.assertTrue('marcop' in counselor_list)
        self.assertTrue('galf' in counselor_list)

    def test_student_cannot_access_random_task(self):
        """ Student User Cannot Access Random Task """
        task = self.app.get('/caps/student_exercise/1', user='armandog')
        self.assertEqual(task.status, '200 OK')

        self.assertTrue('Not an assigned task.' in task)


# Checks page interactions for an authenticated counselor user
# Counselor
    # Can login
    # Can visit pages that require login
    # Home page
        # Profile, Edit, Logout exist in navbar, Login does not
        # Correct chat buttons exist
    # Profile
        # Correct items displayed based on what they've filled out
class AuthCounselorTests(WebTest):

    def setUp(self):
        for account in ACCOUNTS:
            new_user = User.objects.create_user(**account)
            if account['first_name'] == COUNSELOR:
                if account['username'] == 'galf':
                    new_profile = Counselor(user=new_user,
                                            **FULL_COUNSELOR_PROFILE_FILLERS)
                else:
                    new_profile = Counselor(user=new_user, **PROFILE_FILLERS)
                new_profile.save()
            elif account['first_name'] == STUDENT:
                if account['username'] == 'danielf':
                    new_profile = Student(user=new_user,
                                          counselor=Counselor.objects.get(
                                              user=User.objects.get(
                                                  username='galf')),
                                          **STUDENT_PROFILE_FILLERS)
                else:
                    new_profile = Student(user=new_user,
                                          **STUDENT_PROFILE_FILLERS)
                new_profile.save()

        new_meeting = Meeting(student=Student.objects.get(
                                    user=User.objects.get(
                                        username='danielf')),
                              counselor=Counselor.objects.get(
                                  user=User.objects.get(
                                      username='galf')),
                              **MEETING_FILLERS)
        new_meeting.save()

    def test_home_page_no_meeting(self):
        """ Authorized Counselor User Homepage Display""" + \
        """ With No Meeting Scheduled """
        home = self.app.get('/', user='marcop')
        self.assertEqual(home.status, '200 OK')
        self.assertTrue('mainNav' in home)
        self.assertTrue('homeNav' in home)
        self.assertTrue('We\'re here to help' in home)
        self.assertTrue('Health Tips' in home)
        # navbar
        self.assertTrue('Profile' in home)
        self.assertTrue('Edit' not in home)
        self.assertTrue('Logout' in home)
        self.assertTrue('Login' not in home)
        # buttons
        self.assertTrue('Chat with your counselor' not in home)
        self.assertTrue('Schedule an Appointment' not in home)
        self.assertTrue('Emergency Response' not in home)
        self.assertTrue('Chat with Student' not in home)
        self.assertTrue('Schedule with Student' not in home)
        self.assertTrue('Get Emergency Help' not in home)

    def test_home_page_meeting(self):
        """ Authorized Counselor User Homepage Display""" + \
        """ With Meeting Scheduled """
        home = self.app.get('/', user='galf')
        self.assertEqual(home.status, '200 OK')
        self.assertTrue('mainNav' in home)
        self.assertTrue('homeNav' in home)
        self.assertTrue('We\'re here to help' in home)
        self.assertTrue('Health Tips' in home)
        # navbar
        self.assertTrue('Profile' in home)
        self.assertTrue('Edit' not in home)
        self.assertTrue('Logout' in home)
        self.assertTrue('Login' not in home)
        # buttons
        self.assertTrue('Chat with your counselor' not in home)
        self.assertTrue('Schedule an Appointment' not in home)
        self.assertTrue('Emergency Response' not in home)
        self.assertTrue('Chat with Student' in home)
        self.assertTrue('Schedule with Student' not in home)
        self.assertTrue('Get Emergency Help' not in home)

    def test_no_registration_form(self):
        """ Authorized Counselor User No Registration Form""" + \
        """ Shown on Registation Page """
        home = self.app.get('/', user='marcop')
        self.assertEqual(home.status, '200 OK')

        register = home.click('Get Support')
        self.assertEqual(register.status, '200 OK')

        self.assertTrue('You\'re already registered!' in register)

        with self.assertRaises(TypeError):
            reg_form = register.form

    def test_counselor_can_login(self):
        """ Counselor User Can Login """
        login = self.app.get('/caps/login')
        self.assertEqual(login.status, '200 OK')

        log_form = login.form

        self.assertEqual('/caps/login', log_form.action)
        self.assertEqual(len(log_form.fields.values()), 5)

        log_form['username'] = 'marcop'
        log_form['password'] = 'dummy3'
        login = log_form.submit('submit')
        self.assertEqual(login.status, '302 Found')
        self.assertEqual(login.location, '/caps/')

    def test_counselor_profile_display(self):
        """ Authorized Counselor User Default Profile Display """
        home = self.app.get('/', user='marcop')
        self.assertEqual(home.status, '200 OK')

        profile = home.click('Profile', index=0)
        self.assertEqual(profile.status, '200 OK')

        self.assertTrue(COUNSELOR in profile)
        self.assertTrue('Peyrot' in profile)
        self.assertTrue('30 years old' in profile)
        self.assertTrue('UnspecifiedGender' in profile)
        self.assertTrue('UnspecifiedDegree' in profile)
        self.assertTrue('UnspecifiedSchool' in profile)
        self.assertTrue('Advisor with' in profile)
        self.assertTrue('5 years experience' in profile)
        self.assertTrue('Please edit your profile to tell us a little bit more about yourself.' in profile)
        self.assertTrue('You aren\'t advising any students currently.'
                        in profile)

    def test_counselor_profile_display_all(self):
        """ Authorized Counselor User Default Profile Display""" + \
        """ All Info Filled In """
        home = self.app.get('/', user='galf')
        self.assertEqual(home.status, '200 OK')

        profile = home.click('Profile', index=0)
        self.assertEqual(profile.status, '200 OK')

        self.assertTrue(COUNSELOR in profile)
        self.assertTrue('Fisher' in profile)
        self.assertTrue('42 years old' in profile)
        self.assertTrue('Female' in profile)
        self.assertTrue('PhD' in profile)
        self.assertTrue('CMU' in profile)
        self.assertTrue('Therapist' in profile)
        self.assertTrue('10 years experience' in profile)
        self.assertTrue('This is a bio.' in profile)
        self.assertTrue('Student Name' in profile)
        # Should also display student names

    def test_counselor_profile_display_with_meeting(self):
        """ Authorized Counselor User Default Profile Display With a Meeting """
        profile = self.app.get('/caps/counselorprofile/galf', user='galf')
        self.assertEqual(profile.status, '200 OK')

        # Will also display current time
        self.assertTrue('Next Appointment: galf with danielf at' in profile)

    def test_cannot_access_student_profile(self):
        """ Authorized Counselor User Cannot Access Student Profile""" + \
        """ That He/She Isn't Counselor For """
        student_profile = self.app.get('/caps/studentprofile', user='marcop')

        self.assertEqual(student_profile.status, '200 OK')

    def test_can_access_student_profile(self):
        """ Authorized Counselor User Can Access Student Profile""" + \
        """ That He/She Is The Counselor For """
        student_profile = self.app.get(
                            '/caps/student_profile_for_counselor/student1',
                            user='galf')

        self.assertEqual(student_profile.status, '200 OK')
        self.assertTrue('Exercises' not in student_profile)

    def test_can_access_counselor_profile(self):
        """ Authorized Counselor User Can Access Counselor Profile """
        counselor_profile = self.app.get('/caps/counselorprofile/marcop',
                                         user='galf')

        self.assertEqual(counselor_profile.status, '200 OK')

    def test_cannot_access_fake_counselor_profile(self):
        """ Authorized Counselor User Cannot Access Counselor""" + \
        """ Profile That Doesn't Exist """
        counselor_profile = self.app.get('/caps/counselorprofile/FooBar',
                                         user='marcop')

        self.assertEqual(counselor_profile.status, '200 OK')
        self.assertTrue('mainNav' in counselor_profile)
        self.assertTrue('homeNav' in counselor_profile)
        self.assertTrue('We\'re here to help' in counselor_profile)
        self.assertTrue('Health Tips' in counselor_profile)

        self.assertTrue('Counselor FooBar does not exist.' in counselor_profile)

    def test_can_access_counselor_list(self):
        """ Authorized Counselor User Cannot Access Counselor List """
        counselor_list = self.app.get('/caps/counselor_list', user='marcop')
        self.assertEqual(counselor_list.status, '200 OK')

        self.assertTrue('Username' in counselor_list)
        self.assertTrue('First Name' in counselor_list)
        self.assertTrue('Last Name' in counselor_list)
        self.assertTrue('marcop' in counselor_list)
        self.assertTrue('galf' in counselor_list)


# Checks page interactions for an authenticated emergency response user
# Emergency
    # Can login
    # Home page
        # Logout exists in navbar, Login does not
        # Correct chat buttons exist
class AuthEmergencyTests(WebTest):

    def setUp(self):
        for account in ACCOUNTS:
            new_user = User.objects.create_user(**account)
            if account['first_name'] == EMERGENCY:
                new_profile = Emergency(user=new_user, **PROFILE_FILLERS)
                new_profile.save()

    def test_home_page(self):
        """ Authorized Emergency User Homepage Display """
        home = self.app.get('/', user='aureliopg')
        self.assertEqual(home.status, '200 OK')
        self.assertTrue('mainNav' in home)
        self.assertTrue('homeNav' in home)
        self.assertTrue('We\'re here to help' in home)
        self.assertTrue('Health Tips' in home)
        # navbar
        self.assertTrue('Profile' in home)
        self.assertTrue('Edit' not in home)
        self.assertTrue('Logout' in home)
        self.assertTrue('Login' not in home)
        # buttons
        self.assertTrue('Chat with your counselor' not in home)
        self.assertTrue('Schedule an Appointment' not in home)
        self.assertTrue('Emergency Response' in home)
        self.assertTrue('Chat with Student' not in home)
        self.assertTrue('Schedule with Student' not in home)
        self.assertTrue('Get Emergency Help' not in home)

    def test_no_registration_form(self):
        """ Authorized Emergency User No Registration Form""" + \
        """ Shown on Registation Page """
        home = self.app.get('/', user='aureliopg')
        self.assertEqual(home.status, '200 OK')

        register = home.click('Get Support')
        self.assertEqual(register.status, '200 OK')

        self.assertTrue('You\'re already registered!' in register)

        with self.assertRaises(TypeError):
            reg_form = register.form

    def test_no_login_form(self):
        """ Authorized Emergency User No Login Form Shown on Login Page """
        login = self.app.get('/caps/login', user='aureliopg')
        self.assertEqual(login.status, '200 OK')

        self.assertTrue('You are already logged in!' in login)

        with self.assertRaises(TypeError):
            log_form = login.form

    def test_receptionist_can_login(self):
        """ Emergency User Can Login """
        login = self.app.get('/caps/login')
        self.assertEqual(login.status, '200 OK')

        log_form = login.form

        self.assertEqual('/caps/login', log_form.action)
        self.assertEqual(len(log_form.fields.values()), 5)

        log_form['username'] = 'aureliopg'
        log_form['password'] = 'dummy1'
        login = log_form.submit('submit')
        self.assertEqual(login.status, '302 Found')
        self.assertEqual(login.location, '/caps/')


# Checks page interactions for an authenticated receptionist user
# Receptionist
    # Can login
    # Home page
        # Logout exists in navbar, Login does not
        # Correct chat buttons exist
class AuthReceptionistTests(WebTest):

    def setUp(self):
        for account in ACCOUNTS:
            new_user = User.objects.create_user(**account)
            if account['first_name'] == RECEPTIONIST:
                new_profile = Receptionist(user=new_user)
                new_profile.save()

    def test_home_page(self):
        """ Authorized Receptionist User Homepage Display """
        home = self.app.get('/', user='lauram')
        self.assertEqual(home.status, '200 OK')
        self.assertTrue('mainNav' in home)
        self.assertTrue('homeNav' in home)
        self.assertTrue('We\'re here to help' in home)
        self.assertTrue('Health Tips' in home)
        # navbar
        self.assertTrue('Profile' in home)
        self.assertTrue('Edit' not in home)
        self.assertTrue('Logout' in home)
        self.assertTrue('Login' not in home)
        # buttons
        self.assertTrue('Chat with your counselor' not in home)
        self.assertTrue('Schedule an Appointment' not in home)
        self.assertTrue('Emergency Response' not in home)
        self.assertTrue('Chat with Student' not in home)
        self.assertTrue('Schedule with Student' in home)
        self.assertTrue('Get Emergency Help' not in home)

    def test_no_registration_form(self):
        """ Authorized Receptionist User No Registration Form""" + \
        """ Shown on Registation Page """
        home = self.app.get('/', user='lauram')
        self.assertEqual(home.status, '200 OK')

        register = home.click('Get Support')
        self.assertEqual(register.status, '200 OK')

        self.assertTrue('You\'re already registered!' in register)
        
        with self.assertRaises(TypeError):
            reg_form = register.form

    def test_no_login_form(self):
        """ Authorized Receptionist User No Login Form Shown on Login Page """
        login = self.app.get('/caps/login', user='lauram')
        self.assertEqual(login.status, '200 OK')

        self.assertTrue('You are already logged in!' in login)

        with self.assertRaises(TypeError):
            log_form = login.form

    def test_receptionist_can_login(self):
        """ Receptionist User Can Login """
        login = self.app.get('/caps/login')
        self.assertEqual(login.status, '200 OK')

        log_form = login.form

        self.assertEqual('/caps/login', log_form.action)
        self.assertEqual(len(log_form.fields.values()), 5)

        log_form['username'] = 'lauram'
        log_form['password'] = 'dummy5'
        login = log_form.submit('submit')
        self.assertEqual(login.status, '302 Found')
        self.assertEqual(login.location, '/caps/')