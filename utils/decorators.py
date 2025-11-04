from functools import wraps
from flask import redirect, url_for, flash, session, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import User, OrganizationMembership, Organization

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
    """Decorator for routes that require specific GLOBAL system roles (e.g., system_admin)"""
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

def organization_role_required(*allowed_roles, org_id_param='id'):
    """
    Decorator for routes that require organization-specific roles.
    
    Args:
        *allowed_roles: Tuple of allowed organization roles ('owner', 'admin', 'member')
        org_id_param: Name of the URL parameter containing organization_id (default: 'id')
    
    Example:
        @organization_role_required('owner', 'admin', org_id_param='org_id')
        def edit_organization(org_id):
            # Only organization owners and admins can access this
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request(optional=False)
                user_id = int(get_jwt_identity())
                
                from flask import current_app
                db = current_app.extensions['sqlalchemy']
                user = db.session.query(User).get(user_id)
                
                if not user:
                    lang = session.get('language', 'ar')
                    flash('يرجى تسجيل الدخول / Please login' if lang == 'ar' else 'Please login', 'warning')
                    return redirect(url_for('auth.login'))
                
                # Check if user is inactive
                if not user.is_active:
                    lang = session.get('language', 'ar')
                    flash('حسابك معطل / Your account is deactivated' if lang == 'ar' else 'Your account is deactivated', 'danger')
                    return redirect(url_for('auth.login'))
                
                # System admins always have access
                if user.has_role('system_admin'):
                    print(f"[organization_role_required] System admin {user.username} granted access")
                    return f(*args, **kwargs)
                
                # Get organization_id from route parameters
                org_id = kwargs.get(org_id_param) or request.view_args.get(org_id_param)
                
                if not org_id:
                    print(f"[organization_role_required] ERROR: org_id_param '{org_id_param}' not found in route parameters")
                    lang = session.get('language', 'ar')
                    flash('خطأ: معرف المؤسسة مفقود / Error: Organization ID missing' if lang == 'ar' else 'Error: Organization ID missing', 'danger')
                    return redirect(url_for('dashboard.index'))
                
                # Get organization and check if it's active
                organization = db.session.query(Organization).get(org_id)
                if not organization:
                    lang = session.get('language', 'ar')
                    flash('المؤسسة غير موجودة / Organization not found' if lang == 'ar' else 'Organization not found', 'danger')
                    return redirect(url_for('dashboard.index'))
                
                if not organization.is_active:
                    lang = session.get('language', 'ar')
                    flash('المؤسسة معطلة / Organization is deactivated' if lang == 'ar' else 'Organization is deactivated', 'danger')
                    return redirect(url_for('dashboard.index'))
                
                # Check membership
                membership = db.session.query(OrganizationMembership).filter_by(
                    user_id=user_id,
                    organization_id=org_id,
                    is_active=True
                ).first()
                
                if not membership:
                    print(f"[organization_role_required] User {user.username} has no membership in org {org_id}")
                    lang = session.get('language', 'ar')
                    flash('ليس لديك صلاحية الوصول لهذه المؤسسة / You do not have access to this organization' if lang == 'ar' else 'You do not have access to this organization', 'danger')
                    return redirect(url_for('dashboard.index'))
                
                # Check if membership role is allowed
                if membership.org_role not in allowed_roles:
                    print(f"[organization_role_required] User {user.username} has role '{membership.org_role}' but needs one of {allowed_roles}")
                    lang = session.get('language', 'ar')
                    flash('ليس لديك الصلاحية المطلوبة / You do not have the required permission' if lang == 'ar' else 'You do not have the required permission', 'danger')
                    return redirect(url_for('dashboard.index'))
                
                print(f"[organization_role_required] User {user.username} with role '{membership.org_role}' granted access to org {org_id}")
                
                # Add membership to kwargs for use in the route
                kwargs['_membership'] = membership
                kwargs['_organization'] = organization
                
                return f(*args, **kwargs)
                
            except Exception as e:
                print(f"[organization_role_required] Exception: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                lang = session.get('language', 'ar')
                flash('حدث خطأ / An error occurred' if lang == 'ar' else 'An error occurred', 'danger')
                return redirect(url_for('dashboard.index'))
        return decorated_function
    return decorator
