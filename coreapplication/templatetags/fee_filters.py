# templatetags/fee_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def sum_amount_paid(payments):
    """Calculate total amount paid from a list of payments"""
    total = Decimal('0.00')
    for payment in payments:
        if payment.payment_status == 'completed':
            total += payment.amount_paid
    return total

@register.filter
def filter_completed(payments):
    """Filter only completed payments"""
    return [payment for payment in payments if payment.payment_status == 'completed']

@register.filter
def calculate_semester_total(payments):
    """Calculate total for a semester's payments"""
    total = Decimal('0.00')
    for payment in payments:
        if payment.payment_status == 'completed':
            total += payment.amount_paid
    return total

@register.filter
def get_balance_class(balance):
    """Return CSS class based on balance amount"""
    if balance < 0:
        return 'text-success'
    elif balance == 0:
        return 'text-muted'
    else:
        return 'text-danger'

@register.filter
def get_status_badge_class(status):
    """Return badge class based on payment status"""
    status_classes = {
        'completed': 'badge-success',
        'pending': 'badge-warning',
        'failed': 'badge-danger',
        'refunded': 'badge-info'
    }
    return status_classes.get(status, 'badge-secondary')