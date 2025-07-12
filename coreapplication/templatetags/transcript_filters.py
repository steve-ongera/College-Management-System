# templatetags/transcript_filters.py
from django import template

register = template.Library()

@register.filter
def dict_key(dictionary, key):
    """
    Access dictionary value by key in templates
    Usage: {{ dict|dict_key:"key_name" }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None

@register.filter
def add(value, arg):
    """
    Add the arg to the value
    Usage: {{ value|add:"text" }}
    """
    try:
        return str(value) + str(arg)
    except:
        return value