# In your templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def split(value, arg):
    return value.split(arg)[0]

# In your_app/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_programme_name(group_string):
    return group_string.split(' (')[0]

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


from django import template

register = template.Library()

@register.filter
def percentage(value, arg):
    try:
        return f"{int((float(value) / float(arg)) * 100)}"
    except (ValueError, ZeroDivisionError):
        return "0"
    

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filter to access dictionary values by key in Django templates
    Usage: {{ my_dict|get_item:my_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)