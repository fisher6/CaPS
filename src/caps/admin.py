from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from caps.models import *

UserAdmin.add_fieldsets += (
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
    
@admin.register(Counselor, Receptionist, Emergency, Student)
class PersonnelAdmin(admin.ModelAdmin):
    exclude = ['available', 'supporting', 'key', 'email_key']
    list_display = ['user_username', 'user_first_name', 'user_last_name']
    search_fields = ['^user__username', '^user__last_name']
    
    def user_username(self, obj):
        return obj.user.username
     
    def user_first_name(self, obj):
        return obj.user.first_name
     
    def user_last_name(self, obj):
        return obj.user.last_name

admin.site.register(Meeting)
admin.site.register(Message)