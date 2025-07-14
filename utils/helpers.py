from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def requires_role(allowed_roles):
    """Decorator to require specific user roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if isinstance(allowed_roles, str):
                roles = [allowed_roles]
            else:
                roles = allowed_roles
            
            if current_user.role.value not in roles:
                flash('You do not have permission to access this page', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def format_currency(amount, currency='USD'):
    """Format amount as currency"""
    return f"{currency} {amount:.2f}"

def calculate_loyalty_points(total_spent):
    """Calculate loyalty points based on total spent"""
    return int(total_spent / 10)  # 1 point per $10

def get_membership_level(total_spent):
    """Determine membership level based on total spent"""
    if total_spent >= 1000:
        return 'VIP'
    elif total_spent >= 500:
        return 'Gold'
    else:
        return 'Silver'
