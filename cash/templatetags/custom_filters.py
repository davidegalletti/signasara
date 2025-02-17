# myapp/templatetags/custom_filters.py
from django import template
from datetime import datetime
register = template.Library()

@register.filter
def format_amount(value):
    """Format the amount with space as thousands separator and append 'FCFA'."""
    if value is None:
        return ''
    # Format the number with spaces as thousands separators
    formatted_value = f"{value:,.0f}".replace(',', ' ').replace('.', ',') 
    return formatted_value


@register.filter
def format_date(value, date_format="%d/%m/%y"):
    if isinstance(value, datetime):
        return value.strftime(date_format)
    return value