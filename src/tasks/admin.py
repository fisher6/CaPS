from django.contrib import admin

from tasks.models import *
    
admin.site.register(Option)

class OptionInline(admin.StackedInline):
    model = Option
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]
 
class QuestionInline(admin.TabularInline):
    model = Question
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]

@admin.register(InteractionUnit)    
class TaskAdmin(admin.ModelAdmin):
    readonly_fields = ['start_datetime', 'end_datetime', 'duration']
    
    def duration(self, instance):
        return instance.duration()

class InteractionUnitInline(admin.StackedInline):
    model = InteractionUnit
@admin.register(TaskInteraction)
class TaskInteractionAdmin(admin.ModelAdmin):
    inlines = [InteractionUnitInline]
    readonly_fields = ['start_datetime', 'end_datetime', 'duration']
    
    def duration(self, instance):
        return instance.duration()

class TaskInteractionInline(admin.StackedInline):
    model = TaskInteraction
@admin.register(AssignedTask)
class AssignedTaskAdmin(admin.ModelAdmin):
    inlines = [TaskInteractionInline]
 
class AssignedTaskInline(admin.StackedInline):
    model = AssignedTask
@admin.register(TasksProfile)
class TasksProfileAdmin(admin.ModelAdmin):
    inlines = [AssignedTaskInline]
    exclude = ['active_assigned_task']
    