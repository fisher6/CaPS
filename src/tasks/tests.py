from django.test import TestCase
from django.test.client import Client
from django.shortcuts import reverse

from django.contrib.auth.models import User

from unittest import mock
from datetime import datetime, timedelta
from json import dumps, loads
import pytz

from tasks.views import *

class TasksTest(TestCase):

    EASTERN = pytz.timezone('US/Eastern')

    @mock.patch('django.utils.timezone.now')
    def setUp(self, mock_now):
        mock_now.return_value = datetime(
            1996, 7, 27, 5, 15, tzinfo=self.EASTERN)
        
        # Create Tasks Profile
        user = User.objects.create_user(username='test', password='test')
        user.save()
        create_profile(user)
        
        self.tasks_profile = user.tasks_profile
        
        # Create Task
        task = Task(name='test_task', interface='example.js')
        task.save()
        
        question = Question(number=1, text='question1', task=task)
        question.save()
        option = Option(
            number=1, text='option1', correctness=True, question=question)
        option.save()
        option = Option(
            number=2, text='option2', correctness=False, question=question)
        option.save()
        
        question = Question(number=3, text='question2', 
                            time_limit=timedelta(seconds=10), task=task)
        question.save()
        option = Option(
            number=5, text='option1', correctness=True, question=question)
        option.save()
        option = Option(
            number=12, text='option2', correctness=False, question=question)
        option.save()
        
        question = Question(number=10, text='question3', task=task)
        question.save()
        option = Option(
            number=2, text='option1', correctness=False, question=question)
        option.save()
        option = Option(
            number=3, text='option2', correctness=False, question=question)
        option.save()
        
        # Create Assigned Tasks
        deadline_datetime = datetime(1996, 7, 30, 6, 0, tzinfo=self.EASTERN)
        
        # + ID = 1; not started, no deadline
        assigned_task = AssignedTask(
            task=task, tasks_profile=self.tasks_profile)
        assigned_task.save()
        
        # + ID = 2; not started, with deadline
        assigned_task = AssignedTask(task=task, 
                                     tasks_profile=self.tasks_profile, 
                                     deadline_datetime=deadline_datetime)
        assigned_task.save()
        
        # + ID = 3; started, no deadline
        assigned_task = AssignedTask(
            task=task, tasks_profile=self.tasks_profile)
        assigned_task.save()
        task_interaction = TaskInteraction(assigned_task=assigned_task)
        task_interaction.save()
        
        # + ID = 4; completed, with deadline
        assigned_task = AssignedTask(task=task, 
                                     tasks_profile=self.tasks_profile, 
                                     deadline_datetime=deadline_datetime)
        assigned_task.save()
        task_interaction = TaskInteraction(
            assigned_task=assigned_task, completed=True)
        task_interaction.save()    
    
    @mock.patch('django.utils.timezone.now')
    def test_get_assigned_tasks(self, mock_now):
        """ Tests for correct assigned_task classification. """  
        mock_now.return_value = datetime(
            1996, 8, 1, 5, 15, tzinfo=TasksTest.EASTERN)
            
        statusses = get_assigned_tasks(self.tasks_profile)
        for key, value in statusses.items():
            self.assertEqual(len(value), 1)
        self.assertEqual(statusses[NOT_STARTED][0].id, 1)
        self.assertEqual(statusses[MISSED][0].id, 2)
        self.assertEqual(statusses[STARTED][0].id, 3)
        self.assertEqual(statusses[COMPLETED][0].id, 4)
        
    @mock.patch('django.utils.timezone.now')
    def test_init_task(self, mock_now):
        """ Tests for correct init_task setup. """  
        mock_now.return_value = datetime(
            1996, 8, 1, 5, 15, tzinfo=TasksTest.EASTERN)
            
        with self.assertRaisesRegexp(TasksError, r'^Not an assigned task\.$'):
            init_task(self.tasks_profile, 5)   
        with self.assertRaisesRegexp(
            TasksError, r'^Attempted to redo a completed task\.$'):
            init_task(self.tasks_profile, 4)
        with self.assertRaisesRegexp(
            TasksError, r'^Attempted to start a task after its deadline\.$'):
            init_task(self.tasks_profile, 2)
        init_task(self.tasks_profile, 1)
        self.assertEqual(self.tasks_profile.active_assigned_task.id, 1)
        task_interaction = (
            self.tasks_profile.active_assigned_task.task_interaction)
        self.assertEqual(task_interaction.start_datetime, datetime(
            1996, 8, 1, 5, 15, tzinfo=pytz.timezone('US/Eastern')))  
            
    def test_no_ajax(self):
        """ Tests for correct validation of ajax. """ 
        client = Client()
        client.login(username='test', password='test')
        
        response = client.get(reverse('get_progress'))
        self.assertEqual(response.status_code, 404)
        response = client.get(reverse('get_next_question'))
        self.assertEqual(response.status_code, 404)
        response = client.post(reverse('send_response'))
        self.assertEqual(response.status_code, 404)
    
    @mock.patch('django.utils.timezone.now')
    def test_invalid_active_task(self, mock_now):
        """ Tests for correct validation of the active task. """ 
        mock_now.return_value = datetime(
            1996, 8, 1, 5, 15, tzinfo=TasksTest.EASTERN)
        client = Client()
        client.login(username='test', password='test')
        
        # Missed
        self.tasks_profile.active_assigned_task = AssignedTask.objects.get(id=2)
        response = client.get(
            reverse('get_progress'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        response = client.get(reverse('get_next_question'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        response = client.post(
            reverse('send_response'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        
        # Completed
        mock_now.return_value = datetime(
            1996, 7, 28, 5, 15, tzinfo=TasksTest.EASTERN)
        self.tasks_profile.active_assigned_task = AssignedTask.objects.get(id=4)
        response = client.get(
            reverse('get_progress'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        response = client.get(reverse('get_next_question'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        response = client.post(
            reverse('send_response'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404) 
        
    @mock.patch('django.utils.timezone.now')
    def test_invalid_json(self, mock_now):
        """ Tests for correct validation of json format. """ 
        mock_now.return_value = datetime(
            1996, 8, 1, 5, 15, tzinfo=TasksTest.EASTERN)
        client = Client()
        client.login(username='test', password='test')
        
        init_task(self.tasks_profile, 1)
        response = client.post(reverse('send_response'), 'random} \" format',
                               content_type='application/json', 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        
        response = client.post(reverse('send_response'), 
                               dumps({'Random':'configuration'}),
                               content_type='application/json', 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        
    @mock.patch('django.utils.timezone.now')
    def test_resend_response(self, mock_now):
        """ Tests for correct validation of resending a response. """ 
        mock_now.return_value = datetime(
            1996, 8, 1, 5, 15, tzinfo=TasksTest.EASTERN)
        client = Client()
        client.login(username='test', password='test')
        
        init_task(self.tasks_profile, 1)
        response = client.get(reverse('get_next_question'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response = client.post(reverse('send_response'), 
                               dumps([1, 2]),
                               content_type='application/json', 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 302)
        response = client.post(reverse('send_response'), 
                               dumps([2]),
                               content_type='application/json', 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)  

    @mock.patch('django.utils.timezone.now')
    def test_invalid_options(self, mock_now):
        """ Tests for correct validation of invalid options. """ 
        mock_now.return_value = datetime(
            1996, 8, 1, 5, 15, tzinfo=TasksTest.EASTERN)
        client = Client()
        client.login(username='test', password='test')
        
        init_task(self.tasks_profile, 1)
        response = client.get(reverse('get_next_question'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response = client.post(reverse('send_response'), 
                               dumps([1, 17]),
                               content_type='application/json', 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)  
     
    @mock.patch('django.utils.timezone.now')
    def test_tasks_interaction(self, mock_now):
        """ Tests for correct base functioning of the framework. """ 
        mock_now.return_value = datetime(
            1996, 8, 1, 5, 15, tzinfo=TasksTest.EASTERN)
        client = Client()
        client.login(username='test', password='test')
        
        init_task(self.tasks_profile, 1)
        task_interaction = (
            self.tasks_profile.active_assigned_task.task_interaction)
            
        response = client.get(reverse('get_progress'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(loads(response.json())['percentage'], 0.0 / 3)
        
        response = client.get(reverse('get_next_question'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            loads(loads(response.json())['question'])[0]['fields']['text'], 
            'question1')
        response = client.post(reverse('send_response'), 
                               dumps([1]),
                               content_type='application/json', 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 302)
        response = client.get(reverse('get_progress'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            task_interaction.interaction_units.get(id=1).correctness)
        self.assertAlmostEqual(loads(response.json())['percentage'], 1.0 / 3)
        
        # Time limited question
        response = client.get(reverse('get_next_question'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            loads(loads(response.json())['question'])[0]['fields']['text'], 
            'question2')
        mock_now.return_value = datetime(
            1996, 8, 1, 5, 16, tzinfo=TasksTest.EASTERN)
        response = client.post(reverse('send_response'), 
                               dumps([5]),
                               content_type='application/json', 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 302)
        response = client.get(reverse('get_progress'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            task_interaction.interaction_units.get(id=2).correctness)
        self.assertAlmostEqual(loads(response.json())['percentage'], 2.0 / 3)
        
        # Get question twice
        response = client.get(reverse('get_next_question'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            loads(loads(response.json())['question'])[0]['fields']['text'], 
            'question3')
        response = client.get(reverse('get_next_question'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            loads(loads(response.json())['question'])[0]['fields']['text'], 
            'question3')
        response = client.post(reverse('send_response'), 
                               dumps([2, 3]),
                               content_type='application/json', 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 302)
        response = client.get(reverse('get_progress'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            task_interaction.interaction_units.get(id=3).correctness)
        self.assertAlmostEqual(loads(response.json())['percentage'], 3.0 / 3)
        
        response = client.get(reverse('get_next_question'), 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(loads(response.json())['question'][0])
        