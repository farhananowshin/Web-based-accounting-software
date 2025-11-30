from django import template

register = template.Library()

@register.filter
def taka(value):
    """Format with Bangladeshi Taka symbol (absolute value)"""
    try:
        num = float(value)
        return f" {abs(num):,.2f}"
    except (ValueError, TypeError):
        return " 0.00"

@register.filter
def is_negative(value):
    """Check if value is negative"""
    try:
        return float(value) < 0
    except (ValueError, TypeError):
        return False
