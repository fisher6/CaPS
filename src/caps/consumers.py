from channels import Channel, Group
from channels.auth import (
    http_session_user, channel_session_user, channel_session_user_from_http)
from channels.sessions import channel_session, enforce_ordering

from django.db import transaction
from django.utils import timezone

import json

from caps.models import *

COUNSELOR = 'counselor'
RECEPTIONIST = 'receptionist'
EMERGENCY = 'emergency' 
STUDENT = 'student'
UNAUTHENTICATED = 'anonymous'
SYSTEM = 'system'

EMERGENCY_CHAT = 'emergency'
RECEPTIONIST_CHAT = 'receptionist'
SERVICE_UNAVAILABLE = (
    'Our personnel is unavailable at this moment, please try later')
CONNECTED_FMT = 'User %s added to chat...'
DISCONNECTED_FMT = 'User %s disconnected from chat...'

def get_profile(message):
    """ Gets the user profile and profile_type from the provided message.
    
    Args:
        message: the channel message with an user instance.
     
    Returns:
        (profile, profile_type): a tuple of the profile instance and the string
            of the profile type.
    """
    if message.user.is_authenticated:
        if hasattr(message.user, 'student'):
            profile = message.user.student
            profile_type = STUDENT
        elif hasattr(message.user, 'counselor'):
            profile = message.user.counselor
            profile_type = COUNSELOR
        elif hasattr(message.user, 'receptionist'):
            profile = message.user.receptionist
            profile_type = RECEPTIONIST
        elif hasattr(message.user, 'emergency'):
            profile = message.user.emergency
            profile_type = EMERGENCY
        else: # Should not happen: bad admin; handle as unauthenticaded
            profile = None
            profile_type = UNAUTHENTICATED
    else:
        profile = None
        profile_type = UNAUTHENTICATED
    return (profile, profile_type)

# Connected to websocket.connect
@enforce_ordering(slight=True)
@channel_session_user_from_http
@transaction.atomic
def ws_connect(message):
    """ Connects the channel to the correct group.
    
    Every time a personnel connects, a new random key is generated to avoid 
    keeping connected students from another chat instanece from getting into a
    new not requested chat. That means that everytime a chatting session is
    done, the key for personnel has to be restablished were it finished by 
    personel. Students get matched to the correct personnel based on the
    request and the personel availaility by getting the same random key.
    Counselor appointements are checked before connecting student.
    
    Args:
        message: the channel message with an user instance.
    """
    profile, profile_type = get_profile(message)
    room_type = message.content['path'].strip("/")
    key = None
    if profile_type != UNAUTHENTICATED and profile_type != STUDENT:
        profile.available = True
        profile.set_new_key() # Auto saved
        key = profile.key
    elif room_type == EMERGENCY_CHAT and (
        profile_type == STUDENT or profile_type == UNAUTHENTICATED):
        responders = Emergency.objects.filter(available=True)
        if responders:
            responder = responders[0]
            responder.available = False
            responder.supporting = message.user.username
            key = responder.key
            responder.save()
    elif room_type == RECEPTIONIST_CHAT and profile_type == STUDENT:
        receptionists = Receptionist.objects.filter(available=True)
        if receptionists:
            receptionist = receptionists[0]
            receptionist.available = False
            receptionist.supporting = message.user.username
            key = receptionist.key
            receptionist.save()
    # COUNSELOR_CHAT, room_type = counselor.user.username
    elif profile_type == STUDENT: 
        if User.objects.filter(username=room_type).count() == 1:
            counselor_user = User.objects.get(username=room_type)
            if (hasattr(counselor_user, 'counselor') and 
                counselor_user.counselor.available):
                now = timezone.now()
                meetings = Meeting.objects.filter(
                    counselor=counselor_user.counselor)
                meetings = meetings.filter(student=profile)
                meetings = meetings.filter(start_datetime__lt=now)
                meetings = meetings.filter(end_datetime__gt=now)
                if meetings.count() == 1:
                    counselor_user.counselor.available = False
                    counselor_user.counselor.supporting = message.user.username
                    key = counselor_user.counselor.key
                    counselor_user.counselor.save()
                
    if key is not None:
        text = {'text':CONNECTED_FMT % message.user.username, 'user':SYSTEM}
        Group('chat-%s' % key).send({'text':json.dumps(text)})
        Group('chat-%s' % key).add(message.reply_channel)
    else:
        key = get_random_key()
        Group('chat-%s' % key).add(message.reply_channel)
        text = {'text':SERVICE_UNAVAILABLE, 'user':SYSTEM}
        Group('chat-%s' % key).send({'text':json.dumps(text)})
    message.channel_session['key'] = key

# Connected to websocket.receive
@enforce_ordering(slight=True)
@channel_session_user
@transaction.atomic
def ws_message(message):
    """ Sends a message on chat and saves it on the record.
    
    Args:
        message: the channel message with an user instance.
    """
    profile, profile_type = get_profile(message)
    from_user = message.user if profile_type != UNAUTHENTICATED else None
    to_user = None
    key = message.channel_session['key']
    if profile_type != UNAUTHENTICATED and profile_type != STUDENT:
        if User.objects.filter(username=profile.supporting).count() == 1:
            to_user = User.objects.get(username=profile.supporting)
    else:
        if Counselor.objects.filter(key=key).count() == 1:
            to_user = Counselor.objects.get(key=key).user
        elif Receptionist.objects.filter(key=key).count() == 1:
            to_user = Receptionist.objects.get(key=key).user
        elif Emergency.objects.filter(key=key).count() == 1:
            to_user = Emergency.objects.get(key=key).user
  
    sent_message = Message(from_user=from_user, to_user=to_user, 
                           text=message['text'][:MAX_TEXT_STORAGE])
    sent_message.save()
    
    text = {'text':message['text'], 'user':(
        from_user.username if from_user is not None else UNAUTHENTICATED)}
    Group('chat-%s' % key).send({'text':json.dumps(text)})

# Connected to websocket.disconnect
@enforce_ordering(slight=True)
@channel_session_user
@transaction.atomic
def ws_disconnect(message):
    """ Disconnects the channel updating the necessary key.
    
    If the channel disconnected is from personnel, availaility is set to
    False and the key is reset to default to prevent a non disconnected user
    from being in the room after a new connection from personnel is stablished.
    Otherwise, availaility is set to True and the key from the supporting
    personnel is maintained as no other user would be in the group.
    
    Args:
        message: the channel message with an user instance.
    """
    profile, profile_type = get_profile(message)
    key = message.channel_session['key']
    if profile_type != UNAUTHENTICATED and profile_type != STUDENT:
        profile.available = False
        profile.supporting = DEFAULT
        profile.clear_key() # Auto saved
    else:
        if Counselor.objects.filter(key=key).count() == 1:
            counselor = Counselor.objects.get(key=key)
            counselor.available = True
            counselor.supporting = DEFAULT
            counselor.save()
        elif Receptionist.objects.filter(key=key).count() == 1:
            receptionist = Receptionist.objects.get(key=key)
            receptionist.available = True
            receptionist.supporting = DEFAULT
            receptionist.save()
        elif Emergency.objects.filter(key=key).count() == 1:
            emergency = Emergency.objects.get(key=key)
            emergency.available = True
            emergency.supporting = DEFAULT
            emergency.save()
    text = {'text':DISCONNECTED_FMT % message.user.username, 'user':SYSTEM}
    Group('chat-%s' % key).discard(message.reply_channel)
    Group('chat-%s' % key).send({'text':json.dumps(text)})
    