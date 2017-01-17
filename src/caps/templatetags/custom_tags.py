from django import template
from django.forms import CheckboxSelectMultiple, RadioSelect, Select

register = template.Library()

@register.filter(name='is_checkbox')
def is_checkbox(field):
    return isinstance(field.field.widget, CheckboxSelectMultiple)

@register.filter(name='is_radio')
def is_checkbox(field):
    return isinstance(field.field.widget, RadioSelect)

@register.filter(name='is_select')
def is_checkbox(field):
    return isinstance(field.field.widget, Select)