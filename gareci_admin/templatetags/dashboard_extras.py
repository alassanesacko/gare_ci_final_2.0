from django import template

register = template.Library()

@register.filter(name='get')
def get_item(dictionary, key):
    """
    Filter to get an item from a dictionary using a key in a template.
    Usage: {{ dictionary|get:key }}
    """
    return dictionary.get(key, [])
