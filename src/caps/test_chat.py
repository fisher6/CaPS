from channels import Channel
from channels.tests import ChannelTestCase, HttpClient

from django.contrib.auth.models import User

from unittest import mock
from datetime import datetime
import pytz

from caps.models import *
from caps.consumers import *

class ChatTest(ChannelTestCase):
    # First name used as account type reference
    ACCOUNTS = [
        {'username' : 'aureliopg',
         'password' : 'dummy1',
         'first_name' : EMERGENCY,
         'last_name' : 'Puebla Gutierrez',
         'email' : 'a@a.com'},

        {'username' : 'carlosp',
         'password' : 'dummy2',
         'first_name' : EMERGENCY,
         'last_name' : 'Perez',
         'email' : 'b@a.com'},

        {'username' : 'marcop',
         'password' : 'dummy3',
         'first_name' : COUNSELOR,
         'last_name' : 'Peyrot',
         'email' : 'c@a.com'},

        {'username' : 'galf',
         'password' : 'dummy4',
         'first_name' : COUNSELOR,
         'last_name' : 'Fisher',
         'email' : 'd@a.com'},

        {'username' : 'lauram',
         'password' : 'dummy5',
         'first_name' : RECEPTIONIST,
         'last_name' : 'Miller',
         'email' : 'e@a.com'},

        {'username' : 'armandog',
         'password' : 'dummy6',
         'first_name' : STUDENT,
         'last_name' : 'Gutierrez',
         'email' : 'f@a.com'},

        {'username' : 'danielf',
         'password' : 'dummy7',
         'first_name' : STUDENT,
         'last_name' : 'Flores',
         'email' : 'g@a.com'},
        ]

    PROFILE_FILLERS = {
        'seniority' : 5,
        'age' : 30,
    }

    def setUp(self):
        for account in self.ACCOUNTS:
            new_user = User.objects.create_user(**account)
            if account['first_name'] == EMERGENCY:
                new_profile = Emergency(user=new_user, **self.PROFILE_FILLERS)
            elif account['first_name'] == COUNSELOR:
                new_profile = Counselor(user=new_user, **self.PROFILE_FILLERS)
            elif account['first_name'] == RECEPTIONIST:
                new_profile = Receptionist(user=new_user)
            elif account['first_name'] == STUDENT:
                new_profile = Student(user=new_user)
            new_profile.save()
    
    def test_personnel_simple_availability(self):
        """ Checks for correct available field update. """
        emergency_client = HttpClient()
        emergency_client.login(username=self.ACCOUNTS[0]['username'],
                               password=self.ACCOUNTS[0]['password'])
                               
        self.assertFalse(Emergency.objects.get(
            user__username=self.ACCOUNTS[0]['username']).available)
        emergency_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[0]['username'], 'order':0})
        self.assertIsNone(emergency_client.receive())
        self.assertTrue(Emergency.objects.get(
            user__username=self.ACCOUNTS[0]['username']).available)  
        emergency_client.send_and_consume('websocket.disconnect', {'order':1})
        self.assertIsNone(emergency_client.receive())
        self.assertFalse(Emergency.objects.get(
            user__username=self.ACCOUNTS[0]['username']).available)
        
    def test_anonymous_connect_no_personnel(self):
        """ Checks message when no personnels is available. """
        anonymous_client = HttpClient()
        anonymous_client.send_and_consume(
            'websocket.connect', {'path':EMERGENCY_CHAT, 'order':0})
        self.assertDictEqual(anonymous_client.receive(),
                             {'text':SERVICE_UNAVAILABLE, 'user':SYSTEM})
                             
    def test_error_handle_as_anonymous(self):
        """ Check correct handling of a user with no profile. """
        receptionist_client = HttpClient()
        receptionist_client.login(username=self.ACCOUNTS[4]['username'],
                                  password=self.ACCOUNTS[4]['password'])
        receptionist_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[4]['username'], 'order':0})
            
        User.objects.create_user(username='no_profile', password='no_profile')
        no_profile_client = HttpClient()
        no_profile_client.login(username='no_profile', password='no_profile')
        no_profile_client.send_and_consume(
            'websocket.connect', {'path':EMERGENCY_CHAT, 'order':0})
        self.assertDictEqual(no_profile_client.receive(),
                             {'text':SERVICE_UNAVAILABLE, 'user':SYSTEM})
                             
    def test_supporting(self):
        """ Checks for the coorect handling of supporting attribute. """
        emergency1_client = HttpClient()
        emergency1_client.login(username=self.ACCOUNTS[0]['username'],
                                password=self.ACCOUNTS[0]['password'])
        emergency1_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[0]['username'], 'order':0})
        student1_client = HttpClient()
        student1_client.login(username=self.ACCOUNTS[5]['username'],
                              password=self.ACCOUNTS[5]['password'])
        student1_client.send_and_consume(
            'websocket.connect', {'path':EMERGENCY_CHAT, 'order':0})
        self.assertDictEqual(
            emergency1_client.receive(),
            {'text':CONNECTED_FMT % self.ACCOUNTS[5]['username'], 
             'user':SYSTEM})
        self.assertEqual(
            Emergency.objects.get(
                user__username=self.ACCOUNTS[0]['username']).supporting,
            self.ACCOUNTS[5]['username'])
        
        student1_client.send_and_consume('websocket.disconnect', {'order':1})
        self.assertDictEqual(
            emergency1_client.receive(),
            {'text':DISCONNECTED_FMT % self.ACCOUNTS[5]['username'], 
             'user':SYSTEM})
        self.assertEqual(
            Emergency.objects.get(
                user__username=self.ACCOUNTS[0]['username']).supporting,
            DEFAULT)
            
    def test_send_message(self):
        """ Checks for correct message sending. """
        
        # Connect emergency1 and student1
        emergency1_client = HttpClient()
        emergency1_client.login(username=self.ACCOUNTS[0]['username'],
                                password=self.ACCOUNTS[0]['password'])
        emergency1_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[0]['username'], 'order':0})
        student1_client = HttpClient()
        student1_client.login(username=self.ACCOUNTS[5]['username'],
                              password=self.ACCOUNTS[5]['password'])
        student1_client.send_and_consume(
            'websocket.connect', {'path':EMERGENCY_CHAT, 'order':0})
        self.assertDictEqual(
            emergency1_client.receive(),
            {'text':CONNECTED_FMT % self.ACCOUNTS[5]['username'], 
             'user':SYSTEM})
        
        # Connect emergency2 and student2
        emergency2_client = HttpClient()
        emergency2_client.login(username=self.ACCOUNTS[1]['username'],
                                password=self.ACCOUNTS[1]['password'])
        emergency2_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[1]['username'], 'order':0})
        student2_client = HttpClient()
        student2_client.login(username=self.ACCOUNTS[6]['username'],
                              password=self.ACCOUNTS[6]['password'])
        student2_client.send_and_consume(
            'websocket.connect', {'path':EMERGENCY_CHAT, 'order':0})
        self.assertDictEqual(
            emergency2_client.receive(),
            {'text':CONNECTED_FMT % self.ACCOUNTS[6]['username'], 
             'user':SYSTEM})
        
        # Send from student1
        text = 'student1'
        student1_client.send_and_consume(
            'websocket.receive', {'text':text, 'order':1})
        self.assertDictEqual(
            student1_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[5]['username']})
        self.assertDictEqual(
            emergency1_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[5]['username']})
        self.assertIsNone(student2_client.receive())
        self.assertIsNone(emergency2_client.receive())
        self.assertTrue(Message.objects.filter(text=text).filter(
            from_user__username=self.ACCOUNTS[5]['username']).filter(
                to_user__username=self.ACCOUNTS[0]['username']).count() == 1)
        
        # Send from student2
        text = 'student2'
        student2_client.send_and_consume(
            'websocket.receive', {'text':text, 'order':1})
        self.assertDictEqual(
            student2_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[6]['username']})
        self.assertDictEqual(
            emergency2_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[6]['username']})
        self.assertIsNone(student1_client.receive())
        self.assertIsNone(emergency1_client.receive())
        self.assertTrue(Message.objects.filter(text=text).filter(
            from_user__username=self.ACCOUNTS[6]['username']).filter(
                to_user__username=self.ACCOUNTS[1]['username']).count() == 1)
        
        # Send from emergency1
        text = 'emergency1'
        emergency1_client.send_and_consume(
            'websocket.receive', {'text':text, 'order':1})
        self.assertDictEqual(
            student1_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[0]['username']})
        self.assertDictEqual(
            emergency1_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[0]['username']})
        self.assertIsNone(student2_client.receive())
        self.assertIsNone(emergency2_client.receive())
        self.assertTrue(Message.objects.filter(text=text).filter(
            from_user__username=self.ACCOUNTS[0]['username']).filter(
                to_user__username=self.ACCOUNTS[5]['username']).count() == 1)
        
        # Send from emergency2
        text = 'emergency2'
        emergency2_client.send_and_consume(
            'websocket.receive', {'text':text, 'order':1})
        self.assertDictEqual(
            student2_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[1]['username']})
        self.assertDictEqual(
            emergency2_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[1]['username']})
        self.assertIsNone(student1_client.receive())
        self.assertIsNone(emergency1_client.receive())
        self.assertTrue(Message.objects.filter(text=text).filter(
            from_user__username=self.ACCOUNTS[1]['username']).filter(
                to_user__username=self.ACCOUNTS[6]['username']).count() == 1)
       
    def test_multiple_chats(self):
        """ Checks a single user with two windows. """
        RECEPTIONIST_CHANNEL = 'channel1' # Channel for first WS
        EMERGENCY_CHANNEL = 'channel2' # Channel for second WS
        
        # Connect Student1 to emergency1 and receptionist
        receptionist_client = HttpClient()
        receptionist_client.login(username=self.ACCOUNTS[4]['username'],
                                  password=self.ACCOUNTS[4]['password'])
        receptionist_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[4]['username'], 'order':0})
        emergency1_client = HttpClient()
        emergency1_client.login(username=self.ACCOUNTS[0]['username'],
                                password=self.ACCOUNTS[0]['password'])
        emergency1_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[0]['username'], 'order':0})
        student1_client = HttpClient()
        student1_client.login(username=self.ACCOUNTS[5]['username'],
                              password=self.ACCOUNTS[5]['password'])
        student1_client.reply_channel = EMERGENCY_CHANNEL 
        student1_client.send_and_consume(
            'websocket.connect', {'path':EMERGENCY_CHAT, 'order':0})
        self.assertDictEqual(
            emergency1_client.receive(),
            {'text':CONNECTED_FMT % self.ACCOUNTS[5]['username'], 
             'user':SYSTEM})
        student1_client.reply_channel = RECEPTIONIST_CHANNEL 
        student1_client.send_and_consume(
            'websocket.connect', {'path':RECEPTIONIST_CHAT, 'order':0})
        self.assertDictEqual(
            receptionist_client.receive(),
            {'text':CONNECTED_FMT % self.ACCOUNTS[5]['username'], 
             'user':SYSTEM})
        
        # Send message from student1 to receptionist
        text = 'student1'
        student1_client.send_and_consume(
            'websocket.receive', {'text':text, 'order':1})
        self.assertDictEqual(
            student1_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[5]['username']})
        self.assertDictEqual(
            receptionist_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[5]['username']})
        self.assertIsNone(emergency1_client.receive())
        self.assertTrue(Message.objects.filter(text=text).filter(
            from_user__username=self.ACCOUNTS[5]['username']).filter(
                to_user__username=self.ACCOUNTS[4]['username']).count() == 1)
        
        # Close connection from student1 for receptionist
        student1_client.send_and_consume('websocket.disconnect', {'order':2})
        self.assertDictEqual(
            receptionist_client.receive(),
            {'text':DISCONNECTED_FMT % self.ACCOUNTS[5]['username'], 
             'user':SYSTEM})
        
        # Send message from student1 to emergency1
        student1_client.reply_channel = EMERGENCY_CHANNEL 
        text = 'student2'
        student1_client.send_and_consume(
            'websocket.receive', {'text':text, 'order':1})
        self.assertDictEqual(
            student1_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[5]['username']})
        self.assertDictEqual(
            emergency1_client.receive(),
            {'text':text, 'user':self.ACCOUNTS[5]['username']})
        self.assertIsNone(receptionist_client.receive())
        self.assertTrue(Message.objects.filter(text=text).filter(
            from_user__username=self.ACCOUNTS[5]['username']).filter(
                to_user__username=self.ACCOUNTS[0]['username']).count() == 1)
    
    def test_receptionist(self):
        """ Checks correct receptionist chat handling. """
        # Receptionist opens chat
        receptionist_client = HttpClient()
        receptionist_client.login(username=self.ACCOUNTS[4]['username'],
                                  password=self.ACCOUNTS[4]['password'])
        receptionist_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[4]['username'], 'order':0})
        
        # Student1 opens chat and gets connected to receptionist
        student1_client = HttpClient()
        student1_client.login(username=self.ACCOUNTS[5]['username'],
                              password=self.ACCOUNTS[5]['password'])
        student1_client.send_and_consume(
            'websocket.connect', {'path':RECEPTIONIST_CHAT, 'order':0})
        self.assertDictEqual(
            receptionist_client.receive(),
            {'text':CONNECTED_FMT % self.ACCOUNTS[5]['username'], 
             'user':SYSTEM})
        
        # Student2 opens chat and get unavialable personnel message, closes
        student2_client = HttpClient()
        student2_client.login(username=self.ACCOUNTS[6]['username'],
                              password=self.ACCOUNTS[6]['password'])
        student2_client.send_and_consume(
            'websocket.connect', {'path':RECEPTIONIST_CHAT, 'order':0})
        self.assertDictEqual(student2_client.receive(),
                             {'text':SERVICE_UNAVAILABLE, 'user':SYSTEM})
        student2_client.send_and_consume('websocket.disconnect', {'order':1})
        
        # Student1 closes chat and student2 retries: connected to receptionist
        student1_client.send_and_consume('websocket.disconnect', {'order':1})
        self.assertDictEqual(
            receptionist_client.receive(),
            {'text':DISCONNECTED_FMT % self.ACCOUNTS[5]['username'], 
             'user':SYSTEM})
        student2_client.send_and_consume(
            'websocket.connect', {'path':RECEPTIONIST_CHAT, 'order':0})
        self.assertDictEqual(
            receptionist_client.receive(),
            {'text':CONNECTED_FMT % self.ACCOUNTS[6]['username'], 
             'user':SYSTEM})
             
    @mock.patch('caps.consumers.timezone')
    def test_counselor(self, mock_timezone):
        """ Checks correct function of meetings and counselor chats. """
        eastern = pytz.timezone('US/Eastern')
        meeting = Meeting(
            student = Student.objects.get(
                user__username=self.ACCOUNTS[5]['username']),
            counselor = Counselor.objects.get(
                user__username=self.ACCOUNTS[2]['username']),
            start_datetime = datetime(
                1996, 7, 27, 5, 15, tzinfo=eastern),
            end_datetime = datetime(
                1996, 7, 27, 6, 0, tzinfo=eastern))
        meeting.save()
        
        counselor_client = HttpClient()
        counselor_client.login(username=self.ACCOUNTS[2]['username'],
                               password=self.ACCOUNTS[2]['password'])
        counselor_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[2]['username'], 'order':0})
        student1_client = HttpClient()
        student1_client.login(username=self.ACCOUNTS[5]['username'],
                              password=self.ACCOUNTS[5]['password'])
        
        # Try to access before appointment       
        mock_timezone.now.return_value = datetime(
            1996, 7, 27, 4, 45, tzinfo=eastern)
        student1_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[2]['username'], 'order':0})
        self.assertDictEqual(student1_client.receive(),
                             {'text':SERVICE_UNAVAILABLE, 'user':SYSTEM})
        student1_client.send_and_consume(
            'websocket.disconnect', 
            {'path':self.ACCOUNTS[2]['username'], 'order':1})
                             
        # Access on time 
        mock_timezone.now.return_value = datetime(
            1996, 7, 27, 5, 25, tzinfo=eastern)
        text = 'thanks'
        student1_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[2]['username'], 'order':0})
        self.assertDictEqual(
            counselor_client.receive(),
            {'text':CONNECTED_FMT % self.ACCOUNTS[5]['username'], 
             'user':SYSTEM})
        student1_client.send_and_consume('websocket.receive', 
                                         {'text':text, 'order':1})
        self.assertDictEqual(counselor_client.receive(),
                             {'text':text, 'user':self.ACCOUNTS[5]['username']})
        self.assertDictEqual(student1_client.receive(),
                             {'text':text, 'user':self.ACCOUNTS[5]['username']})
        student1_client.send_and_consume('websocket.disconnect', {'order':2})
        self.assertDictEqual(
            counselor_client.receive(),
            {'text':DISCONNECTED_FMT % self.ACCOUNTS[5]['username'], 
             'user':SYSTEM})
        self.assertTrue(Counselor.objects.get(
            user__username=self.ACCOUNTS[2]['username']).available) 
             
        # Try to access after appointment       
        mock_timezone.now.return_value = datetime(
            1996, 7, 28, 5, 25, tzinfo=eastern)
        student1_client.send_and_consume(
            'websocket.connect', 
            {'path':self.ACCOUNTS[2]['username'], 'order':0})
        self.assertDictEqual(student1_client.receive(),
                             {'text':SERVICE_UNAVAILABLE, 'user':SYSTEM})
        student1_client.send_and_consume(
            'websocket.disconnect', 
            {'path':self.ACCOUNTS[2]['username'], 'order':1})
    