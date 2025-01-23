from django import template
from datetime import datetime

register = template.Library()

@register.filter
def format_date(value, date_format="%d/%m/%y"):
    if isinstance(value, datetime):
        return value.strftime(date_format)
    return value

@register.filter
def format_date_obj(value, date_format="%d/%m/%y"):
    if value:
        return value.strftime(date_format)
    return ""

@register.filter
def format_amount(value):
    try:
        value = int(value)
        return f"{value:,}".replace(",", " ") + " FCFA"
    except (ValueError, TypeError):
        return value
    
    
@register.filter
def filter_cs_py(students, cs_py_value):
    return students.filter(cs_py=cs_py_value)

@register.filter
def subtract(value, arg):
    return value - arg    