
from django import template

register = template.Library()

@register.filter
def loop_counter(value):
    if value is None:
        return range(0)
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return range(0)

@register.filter(name='empty_stars')
def empty_stars(value):
    if value is None:
        return range(5)
    try:
        return range(5 - int(value))
    except (ValueError, TypeError):
        return range(5)

@register.filter(name='split')
def split(value, delimiter):
    """
    Returns a list of strings, split by delimiter
    """
    return value.split(delimiter)

@register.filter
def multiply(value, arg):
    return value * arg

@register.filter
def subtract(value, arg):
    return float(value) - float(arg)

@register.filter
def sum(value, arg):
    return float(value) + float(arg)