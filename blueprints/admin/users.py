from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required, role_required
from models import User, Role, SubscriptionPlan, Project, Transaction, AILog, Organization
from flask import current_app
from werkzeug.security import generate_password_hash
from datetime import datetime

users_bp = Blueprint('users', __name__, url_prefix='/users')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@users_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """List all users with filtering"""
    db = get_db()
    lang = get_lang()
    
    # Get filter parameters
    role_filter = request.args.get('role')
    status_filter = request.args.get('status')
    plan_filter = request.args.get('plan')
    search = request.args.get('search', '')
    
    # Build query
    query = db.session.query(User)
    
    if role_filter:
        query = query.join(Role).filter(Role.name == role_filter)
    
    if status_filter:
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
    
    if plan_filter:
        query = query.join(SubscriptionPlan).filter(SubscriptionPlan.name == plan_filter)
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.company_name.ilike(f'%{search}%'))
        )
    
    users = query.order_by(User.created_at.desc()).all()
    
    # Get all roles and plans for filters
    roles = db.session.query(Role).all()
    plans = db.session.query(SubscriptionPlan).all()
    
    return render_template(
        'admin/users/index.html',
        users=users,
        roles=roles,
        plans=plans,
        lang=lang,
        current_role_filter=role_filter,
        current_status_filter=status_filter,
        current_plan_filter=plan_filter,
        current_search=search
    )

@users_bp.route('/<int:user_id>')
@login_required
@role_required('system_admin')
def detail(user_id):
    """User detail page"""
    db = get_db()
    lang = get_lang()
    
    user = db.session.query(User).get_or_404(user_id)
    projects = db.session.query(Project).filter_by(user_id=user_id).order_by(Project.created_at.desc()).all()
    transactions = db.session.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).all()
    ai_logs = db.session.query(AILog).filter_by(user_id=user_id).order_by(AILog.created_at.desc()).limit(20).all()
    
    roles = db.session.query(Role).all()
    plans = db.session.query(SubscriptionPlan).all()
    organizations = db.session.query(Organization).filter_by(is_active=True).all()
    
    return render_template(
        'admin/users/detail.html',
        user=user,
        projects=projects,
        transactions=transactions,
        ai_logs=ai_logs,
        roles=roles,
        plans=plans,
        organizations=organizations,
        lang=lang
    )

@users_bp.route('/<int:user_id>/update', methods=['POST'])
@login_required
@role_required('system_admin')
def update(user_id):
    """Update user details"""
    db = get_db()
    lang = get_lang()
    
    user = db.session.query(User).get_or_404(user_id)
    
    # Update fields
    user.username = request.form.get('username', user.username)
    user.email = request.form.get('email', user.email)
    user.company_name = request.form.get('company_name', user.company_name)
    
    # Update role
    role_id = request.form.get('role_id')
    if role_id:
        user.role_id = int(role_id)
    
    # Update subscription plan
    plan_id = request.form.get('subscription_plan_id')
    if plan_id:
        user.subscription_plan_id = int(plan_id)
    
    # Update organization
    org_id = request.form.get('organization_id')
    if org_id:
        user.organization_id = int(org_id) if org_id != 'none' else None
    
    # Update active status
    user.is_active = request.form.get('is_active') == 'on'
    
    try:
        db.session.commit()
        flash('تم تحديث المستخدم بنجاح / User updated successfully' if lang == 'ar' else 'User updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ: {str(e)} / Error: {str(e)}' if lang == 'ar' else f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users.detail', user_id=user_id))

@users_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@login_required
@role_required('system_admin')
def reset_password(user_id):
    """Reset user password"""
    db = get_db()
    lang = get_lang()
    
    user = db.session.query(User).get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    if new_password and len(new_password) >= 6:
        user.set_password(new_password)
        db.session.commit()
        flash('تم إعادة تعيين كلمة المرور بنجاح / Password reset successfully' if lang == 'ar' else 'Password reset successfully', 'success')
    else:
        flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل / Password must be at least 6 characters' if lang == 'ar' else 'Password must be at least 6 characters', 'danger')
    
    return redirect(url_for('admin.users.detail', user_id=user_id))

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def create():
    """Create new user"""
    db = get_db()
    lang = get_lang()
    
    if request.method == 'GET':
        roles = db.session.query(Role).all()
        plans = db.session.query(SubscriptionPlan).all()
        organizations = db.session.query(Organization).filter_by(is_active=True).all()
        return render_template('admin/users/create.html', roles=roles, plans=plans, organizations=organizations, lang=lang)
    
    # POST - Create user
    try:
        new_user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            company_name=request.form.get('company_name'),
            role_id=int(request.form.get('role_id')),
            subscription_plan_id=int(request.form.get('subscription_plan_id')) if request.form.get('subscription_plan_id') else None,
            organization_id=int(request.form.get('organization_id')) if request.form.get('organization_id') and request.form.get('organization_id') != 'none' else None,
            is_active=request.form.get('is_active') == 'on'
        )
        new_user.set_password(request.form.get('password'))
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('تم إنشاء المستخدم بنجاح / User created successfully' if lang == 'ar' else 'User created successfully', 'success')
        return redirect(url_for('admin.users.detail', user_id=new_user.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ: {str(e)} / Error: {str(e)}' if lang == 'ar' else f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin.users.create'))

@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('system_admin')
def delete(user_id):
    """Delete user (soft delete)"""
    db = get_db()
    lang = get_lang()
    
    user = db.session.query(User).get_or_404(user_id)
    
    # Soft delete by deactivating
    user.is_active = False
    db.session.commit()
    
    flash('تم تعطيل المستخدم بنجاح / User deactivated successfully' if lang == 'ar' else 'User deactivated successfully', 'success')
    return redirect(url_for('admin.users.index'))
