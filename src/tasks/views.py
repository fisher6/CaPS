from django.core import serializers
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, reverse, get_object_or_404
from django.utils import timezone

from django.contrib.auth.decorators import login_required

from tasks.models import *

from json import dumps, loads

COMPLETED = 'Completed'
STARTED = 'Started'
NOT_STARTED = 'Not Started'
MISSED = 'Missed'

class TasksError(Exception):
    """ The estandar error for the framework. """
    pass

def create_profile(user):
    """ Creates a tasks profile for the given user.
    
    Args:
        user: the Django User instance.
    """
    if not hasattr(user, 'tasks_profile'):
        tasks_profile = TasksProfile(user=user)
        tasks_profile.save()
        
def get_assigned_tasks(tasks_profile):
    """ Given a task_profile, returns a dict of the tasks with their status. 
    
    Args:
        tasks_profile: the tasks profile.
        
    Returns:
        A dictionary of three pairs with the status codes as the keys and the 
            list of tasks corresponding to that status as the values.
    """
    task_statusses = {COMPLETED : [], STARTED : [], 
                      NOT_STARTED : [], MISSED : []}
    for assigned_task in AssignedTask.objects.filter(
        tasks_profile=tasks_profile):
        if (hasattr(assigned_task, 'task_interaction') and 
            assigned_task.task_interaction.completed):
            task_statusses[COMPLETED].append(assigned_task)
        elif (hasattr(assigned_task, 'task_interaction') and
            (not assigned_task.deadline_datetime or
             assigned_task.deadline_datetime >= timezone.now())):
            task_statusses[STARTED].append(assigned_task)
        elif (assigned_task.deadline_datetime and 
            assigned_task.deadline_datetime < timezone.now()):
            task_statusses[MISSED].append(assigned_task)
        else:
            task_statusses[NOT_STARTED].append(assigned_task)
    return task_statusses

def init_task(tasks_profile, assigned_task_id):
    """ Set's up the models to begin a task.
    
    Args:
        tasks_profile: the tasks profile.
        assigned_task_id: the id of the assigned_task.
        
    Returns:
        task: the task instance used for the render.
    
    Raises:
        TasksError: if the id doesn't correspond to an assigned task.
    """
    try:
        assigned_task = tasks_profile.assigned_tasks.get(id=assigned_task_id)
    except AssignedTask.DoesNotExist:
        raise TasksError('Not an assigned task.')
    if (hasattr(assigned_task, 'task_interaction') and 
        assigned_task.task_interaction.completed):
        raise TasksError('Attempted to redo a completed task.')
    if (assigned_task.deadline_datetime and 
        assigned_task.deadline_datetime < timezone.now()):
        raise TasksError('Attempted to start a task after its deadline.')
    if not hasattr(assigned_task, 'task_interaction'):
        task_interaction = TaskInteraction(assigned_task=assigned_task)
        task_interaction.save()
    tasks_profile.active_assigned_task = assigned_task
    tasks_profile.save()
    return assigned_task.task
    
# AJAX

@login_required
def get_progress(request):
    """ Returns the percentage of the completed questions. 
    
    Args:
        request: the HTTP request Django object.
    
    Returns:
        json: formated percentage.
    """
    if request.method != 'GET' or not request.is_ajax():
        raise Http404('Invalid request type.')
    tasks_profile = get_object_or_404(TasksProfile, user=request.user)
    if (not tasks_profile.active_assigned_task or 
        tasks_profile.active_assigned_task.task_interaction.completed or
        tasks_profile.active_assigned_task.deadline_datetime and 
        tasks_profile.active_assigned_task.deadline_datetime < timezone.now()):
        raise Http404('Invalid tasks setup.')
    task_interaction = tasks_profile.active_assigned_task.task_interaction
    completed = task_interaction.interaction_units.filter(
        completed=True).count()
    questions = tasks_profile.active_assigned_task.task.questions.count()
    percentage = (float(completed) / questions) if questions else 0.0
    return JsonResponse(dumps({'percentage':percentage}), safe=False)

@login_required
@transaction.atomic
def get_next_question(request):
    """ Returns the next question for the active_assigned_task. 
    
    Args:
        request: the HTTP request Django object.
    
    Returns:
        json: formated question object.
    """
    if request.method != 'GET' or not request.is_ajax():
        raise Http404('Invalid request type.')
    tasks_profile = get_object_or_404(TasksProfile, user=request.user)
    if (not tasks_profile.active_assigned_task or 
        tasks_profile.active_assigned_task.task_interaction.completed or
        tasks_profile.active_assigned_task.deadline_datetime and 
        tasks_profile.active_assigned_task.deadline_datetime < timezone.now()):
        raise Http404('Invalid tasks setup.')
    task_interaction = tasks_profile.active_assigned_task.task_interaction
    data = {'question' : [None], 'options' : []}
    if task_interaction.interaction_units.filter(completed=False):
        # Retrieve if question that was initialized before but not completed
        question = task_interaction.interaction_units.filter(
            completed=False)[0].question
    else:
        if task_interaction.interaction_units.count() == 0:
            last_question_number = -1
            
        else:
            last_question_number = task_interaction.interaction_units.order_by(
                '-question__number')[0].question.number
        if tasks_profile.active_assigned_task.task.questions.filter(
            number__gt=last_question_number).exists():
            question = tasks_profile.active_assigned_task.task.questions.filter(
                number__gt=last_question_number).order_by('number')[0]
        else:
            task_interaction.completed = True
            task_interaction.save()
            return JsonResponse(dumps(data), safe=False)
    if not task_interaction.interaction_units.filter(completed=False):
        interaction_unit = InteractionUnit(task_interaction=task_interaction,
                                           question=question)
        interaction_unit.save()
    data['question'] = serializers.serialize(
        'json', [question], fields=('number', 'text', 'time_limit'))
    data['options'] = serializers.serialize(
        'json', question.options.all(), fields=('number', 'text'))
    return JsonResponse(dumps(data), safe=False)

@login_required
@transaction.atomic
def send_response(request):
    """ Receives and stores a response for the question, returns progress.
    
    Args:
        request: the HTTP request Django object.
    
    Returns:
        redirection: get_progress.
    """
    if request.method != 'POST' or not request.is_ajax():
        raise Http404('Invalid request type.')
    tasks_profile = get_object_or_404(TasksProfile, user=request.user)
    if (not tasks_profile.active_assigned_task or 
        tasks_profile.active_assigned_task.task_interaction.completed or
        tasks_profile.active_assigned_task.deadline_datetime and 
        tasks_profile.active_assigned_task.deadline_datetime < timezone.now()):
        raise Http404('Invalid tasks setup.')
    task_interaction = tasks_profile.active_assigned_task.task_interaction
    
    try:
        selected_options_numbers = loads(request.body.decode('utf-8'))
    except ValueError:
        raise Http404('Invalid json.')
    if (not isinstance(selected_options_numbers, list) or 
        not all(isinstance(num, int) for num in selected_options_numbers)):
        raise Http404('Invalid format.')
    
    if task_interaction.interaction_units.filter(completed=False).count() != 1:
        raise Http404('Attempted to resend response.')
    interaction_unit = task_interaction.interaction_units.filter(
        completed=False)[0]
        
    selected_options = interaction_unit.question.options.filter(
        number__in=selected_options_numbers)
    if selected_options.count() != len(selected_options_numbers):
        raise Http404('Invalid option numbers.')
     
    correctness = True
    for option in selected_options:
        if not option.correctness:
            correctness = False
    interaction_unit.selected_options = selected_options
    interaction_unit.correctness = correctness
    interaction_unit.completed = True
    interaction_unit.save()
    if (interaction_unit.question.time_limit and  
        interaction_unit.question.time_limit < interaction_unit.duration()):
        interaction_unit.correctness = False
        interaction_unit.save()
    return redirect(reverse('get_progress'))
