from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from django.contrib.auth.models import User

from random import choice

OTHER = 'Other' # Option that appears in most form fields

MALE = 'Male'
FEMALE = 'Female'
GENDER_CHOICES = (
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (OTHER, 'Other')
)

FRESHMAN = 'Freshman'
SOPHMORE = 'Sophmore'
JUNIOR = 'Junior'
SENIOR = 'Senior'
MASTERS = 'Masters'
PHD = 'PHD'
CLASS_YEAR = (
    (FRESHMAN, 'Freshman'),
    (SOPHMORE, 'Sophmore'),
    (JUNIOR, 'Junior'),
    (SENIOR, 'Senior'),
    (MASTERS, 'Masters'),
    (PHD, 'Phd'),
    (OTHER, 'Other')
)

DEPRESSION = 'Depression'
GRADES = 'Academic struggles'
SOCIAL = 'Social issues'
HEALTH = 'Health problems'
SEEKING_HELP_REASONS = (DEPRESSION, GRADES, SOCIAL, HEALTH, OTHER)
			  
DEFAULT = 'default'
MAX_TEXT_STORAGE = 1024

DEFAULT_PROFILE_PICTURE = '/profile-pic/defaultIcon.png'

def get_random_key():
    return ''.join([choice(
        'QWERTYUIOPASDFGHJKLZXCVBNM0123456789') for i in range(20)])


class Counselor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                primary_key=True, related_name="counselor")
    position_title = models.CharField(max_length=30, default="Advisor")
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    seniority = models.IntegerField()
    degree = models.CharField(max_length=50, default='', blank=True)
    school = models.CharField(max_length=50, default='', blank=True)
    bio = models.TextField(max_length=1023, default='', blank=True)
    picture = models.ImageField(upload_to='profile-pic', blank=True)

    available = models.BooleanField(default=False)
    supporting = models.CharField(max_length=150, default=DEFAULT) # username

    key = models.CharField(max_length=20, default=DEFAULT)
    def set_new_key(self):
        self.key = get_random_key()
        self.save()
    def clear_key(self):
        self.key = DEFAULT
        self.save()
    email_key = models.CharField(max_length=20, default=DEFAULT)
    def set_new_email_key(self):
        self.email_key = get_random_key()
        self.save()
    def clear_email_key(self):
        self.email_key = DEFAULT
        self.save()

    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    # meetings (defined in Meeting)
    # students_advising (defined in Student)


class Receptionist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                primary_key=True, related_name="receptionist")
    position_title = models.CharField(max_length=30, default="Secretary")

    available = models.BooleanField(default=False)
    supporting = models.CharField(max_length=150, default=DEFAULT) # username

    key = models.CharField(max_length=20, default=DEFAULT)
    def set_new_key(self):
        self.key = get_random_key()
        self.save()
    def clear_key(self):
        self.key = DEFAULT
        self.save()
    email_key = models.CharField(max_length=20, default=DEFAULT)
    def set_new_email_key(self):
        self.email_key = get_random_key()
        self.save()
    def clear_email_key(self):
        self.email_key = DEFAULT
        self.save()

    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)


class Emergency(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                primary_key=True, related_name="emergency")
    position_title = models.CharField(max_length=30, default="Advisor")
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    seniority = models.IntegerField()
    degree = models.CharField(max_length=50, default='', blank=True)
    school = models.CharField(max_length=50, default='', blank=True)
    about = models.TextField(max_length=1023, default='', blank=True)
    picture = models.ImageField(upload_to='profile-pic', blank=True)

    available = models.BooleanField(default=False)
    supporting = models.CharField(max_length=150, default=DEFAULT) # username

    key = models.CharField(max_length=20, default=DEFAULT)
    def set_new_key(self):
        self.key = get_random_key()
        self.save()
    def clear_key(self):
        self.key = DEFAULT
        self.save()
    email_key = models.CharField(max_length=20, default=DEFAULT)
    def set_new_email_key(self):
        self.email_key = get_random_key()
        self.save()
    def clear_email_key(self):
        self.email_key = DEFAULT
        self.save()

    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    class Meta:
        verbose_name_plural = "Emergencies"


class SeekingHelpReason(models.Model):
    reason = models.CharField(max_length=300)
	
    def __str__(self):
        return '%s' % (self.reason)

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                primary_key=True, related_name="student")
    preferred_name = models.CharField(max_length=30, default='', blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default='', blank=True)
    major = models.CharField(max_length=50, default='', blank=True)
    class_year = models.CharField(
    max_length=10, choices=CLASS_YEAR, default='', blank=True)
    seeking_help_reasons = models.ManyToManyField(SeekingHelpReason,
		blank=True)
    bio = models.TextField(max_length=1023, default='', blank=True)
    picture = models.ImageField(upload_to='profile-pic', blank=True,
                                default=DEFAULT_PROFILE_PICTURE)
    counselor = models.ForeignKey(Counselor, on_delete=models.SET_NULL,
                                  related_name="students_advising",
                                  blank=True, null=True)

    email_key = models.CharField(max_length=20, default=DEFAULT)
    def set_new_email_key(self):
        self.email_key = get_random_key()
        self.save()
    def clear_email_key(self):
        self.email_key = DEFAULT
        self.save()

    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    # meetings (defined in Meeting)


class Meeting(models.Model):
    student = models.ForeignKey(Student, related_name="meetings")
    counselor = models.ForeignKey(Counselor, related_name="meetings")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    ordering = ('end_datetime')
    def clean(self):
        if self.start_datetime > self.end_datetime:
            raise ValidationError('start_datetime is after end_datetime.')
        student_meetings = Meeting.objects.filter(
            student=self.student).exclude(pk=self.pk)
        counselor_meetings = Meeting.objects.filter(
            counselor=self.counselor).exclude(pk=self.pk)
        if student_meetings.filter(
            start_datetime__lte=self.start_datetime).filter(
                end_datetime__gte=self.start_datetime).count():
            raise ValidationError('Student has overlapping meeting.')
        if student_meetings.filter(
            start_datetime__lte=self.end_datetime).filter(
                end_datetime__gte=self.end_datetime).count():
            raise ValidationError('Student has overlapping meeting.')
        if student_meetings.filter(
            start_datetime__gte=self.start_datetime).filter(
                end_datetime__lte=self.end_datetime).count():
            raise ValidationError('Student has overlapping meeting.')
        if counselor_meetings.filter(
            start_datetime__lte=self.start_datetime).filter(
                end_datetime__gte=self.start_datetime).count():
            raise ValidationError('Counselor has overlapping meeting.')
        if counselor_meetings.filter(
            start_datetime__lte=self.end_datetime).filter(
                end_datetime__gte=self.end_datetime).count():
            raise ValidationError('Counselor has overlapping meeting.')
        if counselor_meetings.filter(
            start_datetime__gte=self.start_datetime).filter(
                end_datetime__lte=self.end_datetime).count():
            raise ValidationError('Counselor has overlapping meeting.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Meeting, self).save(*args, **kwargs)

    def __str__(self):
        return '%s with %s at %s' % (
            self.counselor.user.username, self.student.user.username,
            timezone.localtime(self.start_datetime).ctime())


class Message(models.Model):
    from_user = models.ForeignKey(User, blank=True, null=True,
                                  related_name="messages_sent")
    to_user = models.ForeignKey(User, blank = True, null=True,
                                related_name="messages_received")
    text = models.CharField(max_length=MAX_TEXT_STORAGE)

    def __str__(self):
        return self.text
