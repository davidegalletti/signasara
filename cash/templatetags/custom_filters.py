# myapp/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def format_amount(value):
    """Format the amount with space as thousands separator and append 'FCFA'."""
    if value is None:
        return ''
    # Format the number with spaces as thousands separators
    formatted_value = f"{value:,.0f}".replace(',', ' ').replace('.', ',') + " FCFA"
    return formatted_value
