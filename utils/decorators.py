from functools import wraps
from flask import redirect, url_for, flash, session
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import User

def login_required(f):
    """Decorator for routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=False)
            return f(*args, **kwargs)
        except Exception as e:
            # Debug: print the error
            print(f"JWT Verification Error: {type(e).__name__}: {str(e)}")
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
                verify_jwt_in_request(optional=False)
                user_id = int(get_jwt_identity())
                from flask import current_app
                db = current_app.extensions['sqlalchemy']
                user = db.session.query(User).get(user_id)
                
                # Debug logging
                print(f"[role_required] User ID: {user_id}, User: {user.username if user else 'None'}, Required roles: {roles}")
                if user:
                    print(f"[role_required] User role: {user.role if user.role else 'No role'}")
                
                if user and user.has_role(*roles):
                    return f(*args, **kwargs)
                else:
                    print(f"[role_required] Access denied - user does not have required role")
                    lang = session.get('language', 'ar')
                    flash('ليس لديك صلاحية للوصول / You do not have permission to access this page' if lang == 'ar' else 'You do not have permission to access this page', 'danger')
                    return redirect(url_for('dashboard.index'))
            except Exception as e:
                print(f"[role_required] Exception: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                lang = session.get('language', 'ar')
                flash('يرجى تسجيل الدخول / Please login' if lang == 'ar' else 'Please login', 'warning')
                return redirect(url_for('auth.login'))
        return decorated_function
    return decorator
