from django import template

register = template.Library()

@register.filter
def percentage(value, arg):
    try:
        return f"{int((float(value) / float(arg)) * 100)}"
    except (ValueError, ZeroDivisionError):
        return "0"