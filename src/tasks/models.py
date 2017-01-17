from django.core.exceptions import ValidationError
from django.db import models

from django.contrib.auth.models import User

class Option(models.Model):
    number = models.PositiveIntegerField() # Id for the given question
    text = models.CharField(max_length=1023)
    correctness = models.BooleanField()
    question = models.ForeignKey(
        'Question', related_name='options', on_delete=models.CASCADE)
        
    def __str__(self):
        return '%s for %s from %s' % (
            self.text, self.question.text, self.question.task.name)
     
    class Meta:
        unique_together = ("question", "number")

class Question(models.Model):
    number = models.PositiveIntegerField() # Id for the given task
    text = models.CharField(max_length=1023)
    # options (defined in: Option)
    time_limit = models.DurationField(blank=True, null=True)
    task = models.ForeignKey(
        'Task', related_name='questions', on_delete=models.CASCADE)
    
    def __str__(self):
        return '%s from %s' % (self.text, self.task.name)
        
    class Meta:
        unique_together = ("task", "number")

class Task(models.Model):
    name = models.CharField(max_length=255, unique=True)
    interface = models.FileField(upload_to='interfaces')
    # questions (defined in: Question)
    
    def clean(self):
        if not self.interface.name.endswith('.js'):
            raise ValidationError('Incorrect format of interface. (*.js)')

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Task, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class InteractionUnit(models.Model):
    task_interaction = models.ForeignKey('TaskInteraction', 
                                         related_name='interaction_units', 
                                         on_delete=models.CASCADE)
    question = models.ForeignKey(Question)
    selected_options = models.ManyToManyField(Option)
    correctness = models.BooleanField(default=False)
    start_datetime = models.DateTimeField(auto_now_add=True)
    end_datetime = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    
    def duration(self):
        return self.end_datetime - self.start_datetime
    
    def __str__(self):
        return 'Interaction Unit for %s' % self.question.text

class TaskInteraction(models.Model):
    assigned_task = models.OneToOneField('AssignedTask', 
                                         related_name='task_interaction', 
                                         on_delete=models.CASCADE)
    # interaction_units (defined in: InteractionUnit)
    start_datetime = models.DateTimeField(auto_now_add=True)
    end_datetime = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    
    def duration(self):
        return self.end_datetime - self.start_datetime
    
    def __str__(self):
        return 'Interactions for %s by %s' % (self.assigned_task.task.name, 
            self.assigned_task.tasks_profile.user.username)

class AssignedTask(models.Model):
    task = models.ForeignKey(Task)
    # task_interaction (defined in: TaskInteraction)
    tasks_profile = models.ForeignKey(
        'TasksProfile', related_name='assigned_tasks', on_delete=models.CASCADE)
    assignation_datetime = models.DateTimeField(auto_now_add=True)
    deadline_datetime = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return '%s for %s' % (self.task.name, self.tasks_profile.user.username)

class TasksProfile(models.Model):
    user = models.OneToOneField(
        User, related_name='tasks_profile', on_delete=models.CASCADE)
    active_assigned_task = models.OneToOneField(
        AssignedTask, blank=True, null=True)
    # assigned_tasks (defined in: AssignedTask)
    
    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)
