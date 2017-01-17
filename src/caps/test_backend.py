from django.test import TestCase, Client, RequestFactory
from django.db import transaction
from django.db.utils import IntegrityError

from caps.models import *
from caps.views import *

from unittest import mock # timezone.now() mocking
import pytz # for EST times
	
snapshot_db = ['caps/test_backend_db']

# Aux functions
@transaction.atomic
def register_student(student_username, is_email_confirmed=False):
	""" Aux function to aux functions """
	new_user = User.objects.create_user(
		username=student_username,
		password='42isnotbad',
		first_name='Gal',
		last_name='Anon',
		email=EMAIL_FMT % student_username,
		is_active=is_email_confirmed)
	new_user_student = Student(user=new_user)
	new_user_student.picture = DEFAULT_PROFILE_PICTURE
	new_user_student.save()

def register_student_uncofirmed_email(student_username):
	""" Auxiliary function to register a student with no confirmed email """
	register_student(student_username)
	
def register_student_cofirmed_email(student_username): 
	""" Auxiliary function to register a student with confirmed mail """
	register_student(student_username, True)
	
@transaction.atomic
def register_counselor(counselor_username): # ** not a test function! **
	""" Auxiliary function to register a counselor """
	new_user = User.objects.create_user(
		username=counselor_username,
		password='42isprettysplendid',
		first_name='Julian',
		last_name='Martha Stewart',
		email=EMAIL_FMT % counselor_username,
		is_active=True)
	new_user_counselor = Counselor(user=new_user)
	new_user_counselor.age = 27
	new_user_counselor.seniority = 17
	new_user_counselor.picture = DEFAULT_PROFILE_PICTURE
	new_user_counselor.save()

# This is the function that replaces django.utils.timezone.now()
def mocked_now():
    return datetime.datetime(
		2012, 1, 1, 10, 10, 10, 424242, pytz.timezone('US/Eastern'))

@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
def create_meeting_now(student_username, *args):
	""" Auxiliary function - creates a meeting between a student and
		his counselor that started after and ends before this meeting """
	student = User.objects.get(username=student_username).student
	now = timezone.now()
	meeting = Meeting(
		student=student,
		counselor=student.counselor,
		start_datetime = now - datetime.timedelta(0,1),
		end_datetime = now + datetime.timedelta(0,1)
	)
	meeting.save()


# Test functions
class HomeTest(TestCase):
	fixtures = snapshot_db
	
	def test_home_page_not_loggedin(self):
		""" Home page loads for non-logged in user """
		client = Client()
		response = client.get('/caps/')
		self.assertEqual(response.status_code, 200) # 200 = OK Response
	
	@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
	def test_home_page_loggedin_student(self, *args):
		""" Home page loads for logged in student """
		student_username = 'gfisher'
		counselor_username = 'phi'
		client = Client()
		client.login(username=student_username,password='1')
		response = client.get('/caps/')
		self.assertEqual(response.status_code, 200)
		student = User.objects.get(username=student_username).student
		counselor = User.objects.get(username=counselor_username).counselor
		student.counselor = counselor
		student.save()
		create_meeting_now(student_username)
		response = client.get('/caps/')
		self.assertEqual(response.status_code, 200)
		# ValidationError exception will be thrown in case of an error

	@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
	def test_home_page_loggedin_counselor(self, *args):
		""" Home page loads for logged in counselor """
		student_username = 'gfisher'
		counselor_username = 'phi'
		client = Client()
		client.login(username=counselor_username,password='1')
		response = client.get('/caps/')
		self.assertEqual(response.status_code, 200)
		student = User.objects.get(username=student_username).student
		counselor = User.objects.get(username=counselor_username).counselor
		student.counselor = counselor
		student.save()
		create_meeting_now(student_username)
		response = client.get('/caps/')
		self.assertEqual(response.status_code, 200)
		# ValidationError exception will be thrown in case of an error
	
class RegisterDescriptionTest(TestCase):
	def test_register_desc_page(self):
		""" Description page and registration page is rendered """
		client = Client()
		response = client.get('/caps/registerdesc')
		self.assertEqual(response.status_code, 200)

		
class ServicesTest(TestCase):
	def test_services_page(self):
		""" Services page is rendered """
		client = Client()
		response = client.get('/caps/services')
		self.assertEqual(response.status_code, 200)

		
class ResourcesTest(TestCase):
	def test_resources_page(self):
		""" Resources page is rendered """
		client = Client()
		response = client.get('/caps/resources')
		self.assertEqual(response.status_code, 200)

		
class ContactTest(TestCase):
	def test_contact_page(self):
		""" Contact page is rendered """
		client = Client()
		response = client.get('/caps/contact')
		self.assertEqual(response.status_code, 200)


class CapsLoginStudentTest(TestCase):
	fixtures = snapshot_db
	
	def test_login_page_is_rendered(self):
		""" Login page is rendered """
		client = Client()
		client.login(username='gfisher',password='1')
		# user is logged in
		response = client.get('/caps/studentprofile')
		self.assertEqual(response.status_code, 200)

	def test_bad_login_nonexistent_student(self):
		""" Unregistered student fails to login """
		client = Client()
		response = client.post('/caps/login', {'username': 'non_existent_user',
			'password': '1'})
		self.assertTrue(response.content.find(
			"Please enter a correct username and password.".encode()) >= 0)

	def test_bad_login_wrong_password(self):
		""" Bad login password """
		client = Client()
		response = client.post('/caps/login', {'username': 'non_existent_user',
		   'password': '1'})
		self.assertTrue(response.content.find(
			"Please enter a correct username and password.".encode()) >= 0)

	def test_bad_login_blank_username_password(self):
		""" Blank fields in login form """
		client = Client()
		response = client.post('/caps/login', {'username': '',
		   'password': ''})
		self.assertTrue(response.content.find(
			"This field is required.".encode()) >= 0)
		response = client.post('/caps/login', {'username': '',
			'password': '1'})
		self.assertTrue(response.content.find(
			"This field is required.".encode()) >= 0)
		response = client.post('/caps/login', {'username': 'gfisher',
			'password': ''})
		self.assertTrue(response.content.find(
			"This field is required.".encode()) >= 0)

	def test_good_login_student(self):
		""" User Logins successfully """
		client = Client()
		response = client.post(
			'/caps/login', {'username': 'gfisher', 'password': '1'})
		self.assertTrue(response.content.find(
			"Please enter a correct username and password.".encode()) == -1)

	def test_user_already_logged_in(self):
		""" Already logged in user gets redirect to home page """
		client = Client()
		client.login(username='gfisher',password='1')
		# user is logged in
		response = client.get('/caps/login')
		self.assertTrue(response.content.find(
			"You are already logged in!".encode()) >= 0)

		
class CapsRegistrationTest(TestCase):
	fixtures = snapshot_db  # Snapshot the current state of DB using:
	#python manage.py dumpdata --exclude=contenttypes --exclude=auth.Permission

	def test_registration_page_is_up(self):
		""" Registration page is rendered """
		response = Client().get('/caps/register')
		self.assertEqual(response.status_code, 200)
	
	def test_check_email_page_is_up(self):
		""" Check email page is rendered """
		client = Client()
		u = User.objects.get(username='gfisher')
		u.is_active = False
		u.save()
		response = client.get('/caps/check_email/gfisher')
		self.assertEqual(response.status_code, 200)

	def test_check_email_student_already_validated(self):
		""" User with validated email can't render check email page """
		client = Client()
		client.login(username='gfisher',password='1')
		response = client.get('/caps/check_email/gfisher')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find
			('You already verified your email.'.encode())>=0)
		client.login(username='phi',password='1')
		response = client.get('/caps/check_email/gfisher')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find('Access denied.'.encode()) >= 0)
		
	def test_check_email_bad_arguments(self):
		""" Check email view with bad arguments doesn't crash """
		client = Client()
		response = client.get('/caps/check_email/phi')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find('Access denied.'.encode()) >= 0)
		response = client.get('/caps/check_email/fake_username')
		self.assertEqual(response.status_code, 200)
	
	def test_validate_email_student_already_validated(self):
		""" User with validated email can't render validate email page """
		client = Client()
		client.login(username='gfisher',password='1')
		response = client.get('/caps/validate_email/' + 'gfisher' + '/' + 
			User.objects.get(username='gfisher').student.email_key)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find('Access denied.'.encode()) >= 0)

	def test_validate_email_student_not_validated(self):
		""" User with can validate email """
		username = 'new_s'
		register_student_uncofirmed_email(username)
		User.objects.get(username=username).student.set_new_email_key()
		client = Client()
		client.login(username='new_s',password='42isnotbad')
		response = client.get('/caps/validate_email/' + username + '/' + 
			User.objects.get(username=username).student.email_key)
		self.assertEqual(response.status_code, 302) # Redirect
		# sending request to the page again to see this time we get 404
		response = client.get('/caps/validate_email/' + username + '/' + 
			User.objects.get(username=username).student.email_key)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find('Access denied.'.encode()) >= 0)
		
	def test_register_new_student(self):
		""" Student registers """
		student_username = 'rocky_balboa'
		db_users = User.objects.all().count()
		db_students = Student.objects.all().count()
		register_student_cofirmed_email(student_username)
		self.assertEqual(User.objects.all().filter(
			username=student_username).count(),1)
		self.assertEqual(User.objects.all().count(),db_users + 1)
		self.assertEqual(Student.objects.all().count(),db_students + 1)

	def test_register_already_exists_student(self):
		""" Username already exists at registration """
		with self.assertRaises(IntegrityError):
			register_student_cofirmed_email('gfisher')

	def test_confirm_password(self):
		""" Confirm password field in the registration form """
		password = 'Pa$$w0rd'
		client = Client()
		response = client.post('/caps/register',
	   {'username': '4john_due2', 'first_name': 'john', 'last_name': 'due',
		'password': password, 'confirm_password': password + '!'})  # diff. pass.
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find(
			"Passwords do not match".encode()) >= 0)
	
	def test_registration_student(self):
		""" Student can register """
		password = 'Pa$$w0rd'
		client = Client()
		new_task = Task(name="Compatibility Measures", 
			interface="Compatibility.js")
		new_task.save()
		response = client.post('/caps/register',
	   {'username': '4john_due2', 'first_name': 'john', 'last_name': 'due',
		'password': password, 'confirm_password': password})  # same pass.
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.content.find(
			"Passwords do not match".encode()), -1)
	
	def test_bad_register_blank_fields(self):
		""" Blank fields in registration form """
		client = Client()
		response = client.post('/caps/login',
			{'username': '', 'first_name': '', 'last_name': '',
			'password': '', 'confirm_password': ''})  # same pass.
		self.assertTrue(response.content.find(
			"This field is required.".encode()) >= 0)
	
	def test_user_already_logged_in(self):
		""" Already logged in user gets redirect to home page """
		client = Client()
		client.login(username='gfisher',password='1')
		response = client.get('/caps/register')
		self.assertTrue(response.content.find(
			"You are already registered!".encode()) >= 0)

				
class CapsProfileStudentView(TestCase):
	fixtures = snapshot_db

	def test_student_profile_view_rendered(self):
		""" Profile student is rendered """
		client = Client()
		client.login(username='gfisher',password='1')
		# user is logged in
		create_profile(User.objects.get(username='gfisher'))
		response = client.get('/caps/studentprofile')
		self.assertEqual(response.status_code, 200)

	def test_missing_profile_major_age_warning(self):
		""" Get a warning for missing profile fields """
		client = Client()
		client.login(username='gfisher',password='1')
		# user is logged in
		response = client.get('/caps/studentprofile')
		self.assertTrue(response.content.find(
			"Please edit your profile to add your major.".encode()) >= 0)
		self.assertTrue(response.content.find(
			"Please edit your profile to set your age.".encode()),-1)
		self.assertEqual(User.objects.filter(username='gfisher').count(),1)
		student = User.objects.get(username='gfisher').student
		student.major = "Towel research"
		student.save()
		response = client.get('/caps/studentprofile')
		self.assertEqual(response.content.find(
			"Please edit your profile to add your major.".encode()),-1)
		student.major = ""
		student.age = 122
		student.save()
		response = client.get('/caps/studentprofile')
		self.assertEqual(response.content.find(
			"Please edit your profile to set your age.".encode()),-1)
		student.major = "Hitchiking"
		student.save()

	def test_counselor_info_exist_for_student_profile(self):
		""" Shows counselor information at students profile if exists """
		client = Client()
		client.login(username='gfisher',password='1')
		response = client.get('/caps/studentprofile')
		self.assertTrue(response.content.find(
			"You haven't been assigned a counselor yet.".encode()) >= 0)
		user_counselor = User.objects.create_user(
			username='counselor',
			password='another_pass',
			first_name='Dr.',
			last_name='Phil',
			email=EMAIL_FMT % 'counsel',
			is_active=False)
		user_counselor.counselor = Counselor(user=user_counselor)
		counselor = user_counselor.counselor
		counselor.age = 43
		counselor.seniority = 15
		counselor.save()
		student = User.objects.get(username='gfisher').student
		student.counselor = counselor
		student.save()
		response = client.get('/caps/studentprofile')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content.find(
			"You haven't been assigned a counselor yet.".encode()),-1)
		self.assertNotEqual(response.content.find(
			"Dr. Phil".encode()),-1)
	
	@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
	def test_meeting_info_exist_for_student_profile(self, *args):
		""" Shows meeting information at students profile if exists """
		# No meeting set yet, show appropiate message
		student_username = 'gfisher'
		counselor_username = 'phi'
		student = User.objects.get(username=student_username).student
		counselor = User.objects.get(username=counselor_username).counselor
		student.counselor = counselor
		student.save()
		client = Client()
		client.login(username=student_username,password='1')
		response = client.get('/caps/studentprofile')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find(
			"Next Appointment: No appointment scheduled.".encode()) >= 0)
		create_meeting_now(student_username)
		response = client.get('/caps/studentprofile')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find(
			"Next Appointment: phi with gfisher at".encode()) >= 0)

	def test_non_student_cant_access_student_profile(self):
		""" Non-student gets an error when trying to access student profile """	
		client = Client()
		client.login(username='phi',password='1')
		response = client.get('/caps/studentprofile')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find
			('Access denied to view student profile'.encode())>=0)


class CapsProfileStudentForCounselorView(TestCase):
	fixtures = snapshot_db

	def test_student_profile_for_counselor_error_if_not_counselor(self):
		""" Profile student for counselor shows an error when not counselor
			tries and access it """
		client = Client()
		client.login(username='gfisher',password='1')
		# user is logged in
		response = client.get('/caps/student_profile_for_counselor/gfisher')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find
			("Permission denied: not a counselor".encode())>=0)

	def test_student_profile_for_counselor_error_if_student_doesnt_exist(self):
		""" Profile student for counselor shows an
			error 'username doesnt exist' """
		client = Client()
		client.login(username='phi',password='1')
		# user is logged in
		response = client.get('/caps/student_profile_for_counselor/404user')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find
			("Student 404user does not exist".encode())>=0)
			
	def test_student_profile_for_counselor_error_not_students_counselor(self):
		""" Profile student for counselor shows an error if a counselor
			tries to access a student profile that he is not advising """
		client = Client() 
		client.login(username='phi',password='1')
		# user is logged in
		response = client.get('/caps/student_profile_for_counselor/gfisher')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find
			("Permission denied: You are not advising gfisher".encode())>=0)
	@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
	def test_student_profile_for_counselor_for_students_counselor(self, *args):
		""" Profile student for counselor is rendered when the student's
			counselor tries to access it """
		client = Client()
		client.login(username='phi',password='1')
		# user is logged in
		user_student = User.objects.get(username='gfisher')
		create_profile(user_student)
		student = user_student.student
		student.counselor = User.objects.get(username='phi').counselor
		student.save()
		create_meeting_now('gfisher')
		response = client.get('/caps/student_profile_for_counselor/gfisher')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content.find
			("Permission denied: You are not advising gfisher".encode()),-1)
		
class CapsProfileStudentUpdate(TestCase):
	fixtures = snapshot_db

	def test_student_profile_update_rendered(self):
		""" Update profile student page is rendered """
		client = Client()
		client.login(username='gfisher',password='1')
		response = client.get('/caps/updateprofile')
		self.assertEqual(response.status_code, 200)
	
	def test_student_profile_update_error_for_non_student(self):
		""" Non student (counselor/emergency/secratery/admin) gets an error
			when trying to update his profile using this view """
		client = Client()
		client.login(username='phi',password='1')
		response = client.get('/caps/updateprofile')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find
			("use CaPS Administration to edit your profile.".encode()) >= 0)
	
	def test_update_student_profile_post_invalid_form(self):
		""" Student updates profile with invalid data """
		client = Client(enforce_csrf_checks=False)
		client.login(username='gfisher',password='1')
		response = client.get('/caps/updateprofile')
		response = client.post('/caps/updateprofile', {'gender': ''})
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find("Edit Profile".encode()) >= 0)
		
	def test_update_student_profile_post_valid_form(self):
		""" Student updates profile with valid data """
		client = Client(enforce_csrf_checks=False)
		client.login(username='gfisher',password='1')
		response = client.get('/caps/updateprofile')
		response = client.post('/caps/updateprofile', {
			'username': 'gfisher',
			'first_name': 'gal',
			'last_name': 'fisher',
			'gender': 'Male',
			'class_year': 'Senior'
		})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.content.find("Edit Profile".encode()), -1)

		
class CapsProfileCounselorView(TestCase):
	fixtures = snapshot_db

	def test_counselor_profile_view_rendered(self):
		""" Profile counselor is rendered """
		username = 'Julian'
		register_counselor(username)
		client = Client()
		# tests as student
		client.login(username='gfisher',password='1')
		response = client.get('/caps/counselorprofile/Julian')
		self.assertTrue(response.content.find("Counselor Profile".encode())>=0)
		# test as counselor
		client.login(username='phi',password='1')
		response = client.get('/caps/counselorprofile/Julian')
		self.assertTrue(response.content.find("Counselor Profile".encode())>=0)
		response = client.get('/caps/counselorprofile/phi')
		self.assertTrue(response.content.find("Counselor Profile".encode())>=0)

	@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
	def test_counselor_profile_can_see_his_next_meeting(self, *args):
		""" Counselor can see his next meeting (if he has one one) on counselor
			profile page """
		# testing for meeting
		username = 'Julian'
		register_counselor(username)
		client = Client()
		client.login(username='phi',password='1')
		s = User.objects.get(username='gfisher').student
		s.counselor = User.objects.get(username='phi').counselor
		s.save()
		create_meeting_now('gfisher')
		response = client.get('/caps/counselorprofile/phi')
		self.assertTrue(response.content.find(
			"Next Appointment".encode()) >= 0)

	def test_counselor_profile_view_for_inexistent_counselor(self):
		""" Counselor profile page of non-existent counselor renders error """
		fake_couns_username = "judgejudy"
		client = Client()
		client.login(username='gfisher',password='1')
		response = client.get('/caps/counselorprofile/' + fake_couns_username)
		self.assertTrue(response.content.find("does not exist.".encode()) >= 0)
		
		
class CounselorListTest(TestCase):
	fixtures = snapshot_db
	
	def test_counselor_list_page_is_up(self):
		""" Counselor list page is rendered """
		client = Client()
		client.login(username='gfisher',password='1')
		response = client.get('/caps/counselor_list')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content.find("does not exist.".encode()),-1)
		self.assertTrue(response.content.find(
			"View All Counselors".encode()) >= 0)
		self.assertTrue(response.content.find("phi".encode()) >= 0)
		
	def test_counselor_list_page_wont_appear_if_not_logged_in(self):
		""" Counselor list wont render if not logged in (@login_required) """
		response = Client().get('/caps/counselor_list')
		self.assertEqual(response.content.find(
			"View All Counselors".encode()),-1)
	
	def test_inactive_counselor_doesnt_appear_on_counselor_list(self):
		""" Inactive counselor doesnt appear on counselor list """
		counselor_user = User.objects.get(username='phi')
		counselor_user.is_active = False
		counselor_user.save()
		client = Client()
		client.login(username='gfisher',password='1')
		response = client.get('/caps/counselor_list')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content.find("phi".encode()),-1)

class MeetingTest(TestCase):
	# Testing the Meeting model
	fixtures = snapshot_db
	
	@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
	def test_overlapping_meetings_student(self, *args):
		""" Checks if we can add overlapping meetings for same student """
		student_username = 'gfisher'
		student = User.objects.get(username=student_username).student
		counselor = User.objects.get(username='phi').counselor
		student.counselor = counselor
		student.save()
		with self.assertRaisesRegexp(
			ValidationError, 'Student has overlapping meeting.'):
			# create two meetings together - they will overlap and an
			# ValidationError exception will be raised
			create_meeting_now(student_username)
			create_meeting_now(student_username)
	
	@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
	def test_overlapping_meetings_couselor(self, *args):
		""" Checks if we can add overlapping meetings for same counseor """
		student1_username = 'gfisher'
		student2_username = 'laura'
		register_student_cofirmed_email(student2_username)
		counselor_username = 'phi'
		student1 = User.objects.get(username=student1_username).student
		student2 = User.objects.get(username=student2_username).student
		counselor = User.objects.get(username='phi').counselor
		student1.counselor = counselor
		student1.save()
		student2.counselor = counselor
		student2.save()
		with self.assertRaisesRegexp(
			ValidationError, 'Counselor has overlapping meeting.'):
			# create two meetings together - they will overlap and an
			# ValidationError exception will be raised
			create_meeting_now(student1_username)
			create_meeting_now(student2_username)


# Task related tests
class CapsStudentExerciseView(TestCase):
	fixtures = snapshot_db

	def test_student_exercise_view_rendered(self):
		""" Exercise view is rendered for student """
		client = Client()
		# counselor - should get an error
		client.login(username='phi',password='1')
		response = client.get('/caps/student_exercise/1')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find(
			"Access denied: you are not a student".encode()) >= 0)
		client = Client()
		client.login(username='gfisher',password='1')
		create_profile(User.objects.get(username='gfisher'))
		response = client.get('/caps/student_exercise/1')
		self.assertEqual(response.status_code, 200)
		#response = client.get('/caps/studentprofile')
		#self.assertEqual(response.status_code, 200)
	
	def test_student_starts_a_task(self):
		""" Student can start a new task """
		client = Client()
		# counselor - should get an error
		client.login(username='gfisher',password='1')
		user = User.objects.get(username='gfisher')
		create_profile(user)
		tasks_profile = user.tasks_profile
		task = Task(name='breathe', interface='interfaces/example_TO5cemF.js')
		task.save()
		assigned_task = AssignedTask(task=task,
			tasks_profile=tasks_profile)
		assigned_task.save()
		tasks_profile.active_assigned_task = assigned_task
		tasks_profile.save()
		response = client.get('/caps/student_exercise/1')
		self.assertEqual(response.status_code, 200)

	def test_exercise_view_not_rendered_for_counselor(self):
		""" Counselor can't start a task """
		client = Client()
		client.login(username='eme',password='1')
		response = client.get('/caps/student_exercise/1')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find(
			"Access denied: you are not a student".encode()) >= 0)
			
	def test_exercise_view_not_rendered_for_emergency(self):
		""" Emergency user can't start a task """
		client = Client()
		client.login(username='eme',password='1')
		response = client.get('/caps/student_exercise/1')
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.content.find(
			"Access denied: you are not a student".encode()) >= 0)