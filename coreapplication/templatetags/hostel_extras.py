# hostel/templatetags/hostel_extras.py
from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Template filter to get dictionary value by key
    Usage: {{ dict|lookup:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def lookup_nested(dictionary, key_path):
    """
    Template filter to get nested dictionary value by key path
    Usage: {{ dict|lookup_nested:"key.subkey" }}
    """
    if dictionary is None:
        return None
    
    keys = str(key_path).split('.')
    result = dictionary
    
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return None
        
        if result is None:
            return None
    
    return result

@register.filter
def get_hostel_stat(hostel_stats, hostel_id_and_stat):
    """
    Template filter to get hostel stats
    Usage: {{ hostel_stats|get_hostel_stat:"hostel_id,stat_name" }}
    """
    if hostel_stats is None:
        return None
    
    try:
        hostel_id, stat_name = str(hostel_id_and_stat).split(',')
        hostel_id = int(hostel_id.strip())
        stat_name = stat_name.strip()
        
        hostel_data = hostel_stats.get(hostel_id, {})
        return hostel_data.get(stat_name)
    except (ValueError, AttributeError):
        return None