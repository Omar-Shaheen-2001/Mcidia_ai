from functools import wraps
from flask import redirect, url_for, flash, session
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import User

def login_required(f):
    """Decorator for routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            lang = session.get('language', 'ar')
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة / Please login to access this page' if lang == 'ar' else 'Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))
    return decorated_function

def role_required(*roles):
    """Decorator for routes that require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                user = User.query.get(user_id)
                
                if user and user.has_role(*roles):
                    return f(*args, **kwargs)
                else:
                    lang = session.get('language', 'ar')
                    flash('ليس لديك صلاحية للوصول / You do not have permission to access this page' if lang == 'ar' else 'You do not have permission to access this page', 'danger')
                    return redirect(url_for('dashboard.index'))
            except Exception as e:
                lang = session.get('language', 'ar')
                flash('يرجى تسجيل الدخول / Please login' if lang == 'ar' else 'Please login', 'warning')
                return redirect(url_for('auth.login'))
        return decorated_function
    return decorator
