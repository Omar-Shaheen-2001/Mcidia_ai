from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from utils.decorators import login_required, role_required
from models import Organization, OrganizationSettings, User, Role, Project, Transaction, AILog, OrganizationMembership, db
from flask import current_app
from datetime import datetime, timedelta
from sqlalchemy import func
import json
import io
import csv

organizations_bp = Blueprint('organizations', __name__, url_prefix='/organizations')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@organizations_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """List all organizations with search and filters"""
    db_session = get_db()
    lang = get_lang()
    
    # Get filter parameters
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    plan_filter = request.args.get('plan', '')
    sector_filter = request.args.get('sector', '')
    
    # Base query
    query = db_session.session.query(Organization)
    
    # Apply filters
    if search:
        query = query.filter(
            (Organization.name.ilike(f'%{search}%')) |
            (Organization.email.ilike(f'%{search}%')) |
            (Organization.country.ilike(f'%{search}%'))
        )
    
    if status_filter:
        if status_filter == 'active':
            query = query.filter(Organization.is_active == True, Organization.subscription_status == 'active')
        elif status_filter == 'suspended':
            query = query.filter(Organization.subscription_status == 'suspended')
        elif status_filter == 'expired':
            query = query.filter(Organization.subscription_status == 'expired')
        elif status_filter == 'inactive':
            query = query.filter(Organization.is_active == False)
    
    if plan_filter:
        query = query.filter(Organization.plan_type == plan_filter)
    
    if sector_filter:
        query = query.filter(Organization.sector == sector_filter)
    
    # Get organizations
    organizations = query.order_by(Organization.created_at.desc()).all()
    
    # Get unique sectors for filter dropdown
    sectors = db_session.session.query(Organization.sector).distinct().filter(Organization.sector.isnot(None)).all()
    sectors = [s[0] for s in sectors if s[0]]
    
    return render_template(
        'admin/organizations/index.html',
        organizations=organizations,
        sectors=sectors,
        lang=lang,
        search=search,
        status_filter=status_filter,
        plan_filter=plan_filter,
        sector_filter=sector_filter
    )

@organizations_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def create():
    """Create a new organization"""
    db_session = get_db()
    lang = get_lang()
    
    if request.method == 'POST':
        try:
            org = Organization(
                name=request.form.get('name'),
                sector=request.form.get('sector'),
                country=request.form.get('country'),
                city=request.form.get('city'),
                size=request.form.get('size', 'medium'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                website=request.form.get('website'),
                address=request.form.get('address'),
                plan_type=request.form.get('plan_type', 'free'),
                subscription_status='active',
                ai_usage_limit=int(request.form.get('ai_usage_limit', 1000)),
                is_active=True
            )
            
            db_session.session.add(org)
            db_session.session.commit()
            
            # Create default settings for the organization
            settings = OrganizationSettings(
                organization_id=org.id,
                default_language=lang,
                enabled_modules=json.dumps(['strategy', 'hr', 'finance'])  # Default modules
            )
            db_session.session.add(settings)
            db_session.session.commit()
            
            flash('تم إنشاء المؤسسة بنجاح / Organization created successfully', 'success')
            return redirect(url_for('admin.organizations.view', org_id=org.id))
        except Exception as e:
            db_session.session.rollback()
            flash(f'خطأ في إنشاء المؤسسة / Error creating organization: {str(e)}', 'danger')
    
    return render_template('admin/organizations/create.html', lang=lang)

@organizations_bp.route('/<int:org_id>')
@login_required
@role_required('system_admin')
def view(org_id):
    """View organization details"""
    db_session = get_db()
    lang = get_lang()
    
    org = db_session.session.query(Organization).get(org_id)
    if not org:
        flash('المؤسسة غير موجودة / Organization not found', 'danger')
        return redirect(url_for('admin.organizations.index'))
    
    # Get organization statistics
    stats = {
        'total_users': len(org.users),
        'active_users': sum(1 for u in org.users if u.is_active),
        'total_projects': db_session.session.query(Project).join(User).filter(User.organization_id == org_id).count(),
        'ai_usage_percentage': org.get_ai_usage_percentage(),
        'total_transactions': db_session.session.query(Transaction).join(User).filter(User.organization_id == org_id).count(),
        'total_spent': db_session.session.query(func.sum(Transaction.amount)).join(User).filter(User.organization_id == org_id).scalar() or 0
    }
    
    return render_template(
        'admin/organizations/view.html',
        org=org,
        stats=stats,
        lang=lang
    )

@organizations_bp.route('/<int:org_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def edit(org_id):
    """Edit organization details"""
    db_session = get_db()
    lang = get_lang()
    
    org = db_session.session.query(Organization).get(org_id)
    if not org:
        flash('المؤسسة غير موجودة / Organization not found', 'danger')
        return redirect(url_for('admin.organizations.index'))
    
    if request.method == 'POST':
        try:
            org.name = request.form.get('name')
            org.sector = request.form.get('sector')
            org.country = request.form.get('country')
            org.city = request.form.get('city')
            org.size = request.form.get('size')
            org.email = request.form.get('email')
            org.phone = request.form.get('phone')
            org.website = request.form.get('website')
            org.address = request.form.get('address')
            org.plan_type = request.form.get('plan_type')
            org.subscription_status = request.form.get('subscription_status')
            org.ai_usage_limit = int(request.form.get('ai_usage_limit', 1000))
            org.is_active = request.form.get('is_active') == '1'
            
            db_session.session.commit()
            flash('تم تحديث المؤسسة بنجاح / Organization updated successfully', 'success')
            return redirect(url_for('admin.organizations.view', org_id=org.id))
        except Exception as e:
            db_session.session.rollback()
            flash(f'خطأ في تحديث المؤسسة / Error updating organization: {str(e)}', 'danger')
    
    return render_template('admin/organizations/edit.html', org=org, lang=lang)

@organizations_bp.route('/<int:org_id>/users')
@login_required
@role_required('system_admin')
def users(org_id):
    """View organization users with their organization-specific roles"""
    db_session = get_db()
    lang = get_lang()
    
    org = db_session.session.query(Organization).get(org_id)
    if not org:
        flash('المؤسسة غير موجودة / Organization not found', 'danger')
        return redirect(url_for('admin.organizations.index'))
    
    # Get all memberships for this organization with user info
    memberships = db_session.session.query(OrganizationMembership).filter_by(
        organization_id=org_id
    ).order_by(OrganizationMembership.joined_at.desc()).all()
    
    # Also get users who have organization_id set but no membership (legacy data)
    legacy_users = db_session.session.query(User).filter(
        User.organization_id == org_id,
        ~User.id.in_([m.user_id for m in memberships])
    ).all()
    
    # Organization membership roles (not system roles)
    org_roles = ['owner', 'admin', 'member']
    
    return render_template(
        'admin/organizations/users.html',
        org=org,
        memberships=memberships,
        legacy_users=legacy_users,
        org_roles=org_roles,
        lang=lang
    )

@organizations_bp.route('/<int:org_id>/users/<int:membership_id>/change-role', methods=['POST'])
@login_required
@role_required('system_admin')
def change_user_org_role(org_id, membership_id):
    """Change a user's organization-specific role"""
    db_session = get_db()
    lang = get_lang()
    
    membership = db_session.session.query(OrganizationMembership).get(membership_id)
    if not membership or membership.organization_id != org_id:
        flash('العضوية غير موجودة / Membership not found', 'danger')
        return redirect(url_for('admin.organizations.users', org_id=org_id))
    
    new_role = request.form.get('membership_role')
    if new_role not in ['owner', 'admin', 'member']:
        flash('دور غير صالح / Invalid role', 'danger')
        return redirect(url_for('admin.organizations.users', org_id=org_id))
    
    try:
        membership.membership_role = new_role
        membership.updated_at = datetime.utcnow()
        db_session.session.commit()
        flash('تم تحديث دور المستخدم بنجاح / User role updated successfully', 'success')
    except Exception as e:
        db_session.session.rollback()
        flash(f'خطأ في تحديث الدور / Error updating role: {str(e)}', 'danger')
    
    return redirect(url_for('admin.organizations.users', org_id=org_id))

@organizations_bp.route('/<int:org_id>/analytics')
@login_required
@role_required('system_admin')
def analytics(org_id):
    """View organization analytics and performance"""
    db_session = get_db()
    lang = get_lang()
    
    org = db_session.session.query(Organization).get(org_id)
    if not org:
        flash('المؤسسة غير موجودة / Organization not found', 'danger')
        return redirect(url_for('admin.organizations.index'))
    
    # Get AI usage over time (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    ai_logs = db_session.session.query(
        func.date_trunc('month', AILog.created_at).label('month'),
        func.count(AILog.id).label('count'),
        func.sum(AILog.tokens_used).label('tokens')
    ).join(User).filter(
        User.organization_id == org_id,
        AILog.created_at >= six_months_ago
    ).group_by('month').order_by('month').all()
    
    # Get project statistics
    project_stats = db_session.session.query(
        func.count(Project.id).label('total'),
        func.sum(func.case((Project.status == 'completed', 1), else_=0)).label('completed')
    ).join(User).filter(User.organization_id == org_id).first()
    
    return render_template(
        'admin/organizations/analytics.html',
        org=org,
        ai_logs=ai_logs,
        project_stats=project_stats,
        lang=lang
    )

@organizations_bp.route('/<int:org_id>/settings', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def settings(org_id):
    """Manage organization settings"""
    db_session = get_db()
    lang = get_lang()
    
    org = db_session.session.query(Organization).get(org_id)
    if not org:
        flash('المؤسسة غير موجودة / Organization not found', 'danger')
        return redirect(url_for('admin.organizations.index'))
    
    # Get or create settings
    org_settings = db_session.session.query(OrganizationSettings).filter_by(organization_id=org_id).first()
    if not org_settings:
        org_settings = OrganizationSettings(organization_id=org_id)
        db_session.session.add(org_settings)
        db_session.session.commit()
    
    if request.method == 'POST':
        try:
            org_settings.default_language = request.form.get('default_language', 'ar')
            org_settings.timezone = request.form.get('timezone', 'Asia/Riyadh')
            org_settings.email_notifications = request.form.get('email_notifications') == '1'
            org_settings.internal_notifications = request.form.get('internal_notifications') == '1'
            org_settings.ai_model_preference = request.form.get('ai_model_preference', 'gpt-4')
            org_settings.allow_document_upload = request.form.get('allow_document_upload') == '1'
            org_settings.enable_api_access = request.form.get('enable_api_access') == '1'
            
            # Handle enabled modules
            enabled_modules = request.form.getlist('enabled_modules')
            org_settings.enabled_modules = json.dumps(enabled_modules)
            
            db_session.session.commit()
            flash('تم تحديث الإعدادات بنجاح / Settings updated successfully', 'success')
            return redirect(url_for('admin.organizations.view', org_id=org.id))
        except Exception as e:
            db_session.session.rollback()
            flash(f'خطأ في تحديث الإعدادات / Error updating settings: {str(e)}', 'danger')
    
    # Available modules
    available_modules = ['strategy', 'hr', 'finance', 'marketing', 'quality', 'innovation', 'governance', 'knowledge']
    current_modules = json.loads(org_settings.enabled_modules) if org_settings.enabled_modules else []
    
    return render_template(
        'admin/organizations/settings.html',
        org=org,
        settings=org_settings,
        available_modules=available_modules,
        current_modules=current_modules,
        lang=lang
    )

@organizations_bp.route('/<int:org_id>/delete', methods=['POST'])
@login_required
@role_required('system_admin')
def delete(org_id):
    """Delete an organization"""
    db_session = get_db()
    
    org = db_session.session.query(Organization).get(org_id)
    if not org:
        flash('المؤسسة غير موجودة / Organization not found', 'danger')
        return redirect(url_for('admin.organizations.index'))
    
    try:
        # Check if organization has users
        if len(org.users) > 0:
            flash('لا يمكن حذف مؤسسة تحتوي على مستخدمين / Cannot delete organization with users', 'danger')
            return redirect(url_for('admin.organizations.view', org_id=org_id))
        
        db_session.session.delete(org)
        db_session.session.commit()
        flash('تم حذف المؤسسة بنجاح / Organization deleted successfully', 'success')
    except Exception as e:
        db_session.session.rollback()
        flash(f'خطأ في حذف المؤسسة / Error deleting organization: {str(e)}', 'danger')
    
    return redirect(url_for('admin.organizations.index'))

@organizations_bp.route('/<int:org_id>/suspend', methods=['POST'])
@login_required
@role_required('system_admin')
def suspend(org_id):
    """Suspend an organization"""
    db_session = get_db()
    
    org = db_session.session.query(Organization).get(org_id)
    if not org:
        return jsonify({'success': False, 'message': 'Organization not found'}), 404
    
    try:
        org.subscription_status = 'suspended'
        org.is_active = False
        db_session.session.commit()
        return jsonify({'success': True, 'message': 'Organization suspended successfully'})
    except Exception as e:
        db_session.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@organizations_bp.route('/<int:org_id>/activate', methods=['POST'])
@login_required
@role_required('system_admin')
def activate(org_id):
    """Activate a suspended organization"""
    db_session = get_db()
    
    org = db_session.session.query(Organization).get(org_id)
    if not org:
        return jsonify({'success': False, 'message': 'Organization not found'}), 404
    
    try:
        org.subscription_status = 'active'
        org.is_active = True
        db_session.session.commit()
        return jsonify({'success': True, 'message': 'Organization activated successfully'})
    except Exception as e:
        db_session.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@organizations_bp.route('/export')
@login_required
@role_required('system_admin')
def export():
    """Export organizations list to CSV"""
    db_session = get_db()
    
    organizations = db_session.session.query(Organization).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(['ID', 'Name', 'Sector', 'Country', 'City', 'Plan', 'Status', 'Users Count', 'AI Usage', 'Created At'])
    
    # Data
    for org in organizations:
        writer.writerow([
            org.id,
            org.name,
            org.sector or '',
            org.country or '',
            org.city or '',
            org.plan_type,
            org.subscription_status,
            len(org.users),
            f"{org.ai_usage_current}/{org.ai_usage_limit}",
            org.created_at.strftime('%Y-%m-%d') if org.created_at else ''
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=organizations.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    return response

@organizations_bp.route('/<int:org_id>/reset-ai-usage', methods=['POST'])
@login_required
@role_required('system_admin')
def reset_ai_usage(org_id):
    """Reset AI usage counter for an organization"""
    db_session = get_db()
    
    org = db_session.session.query(Organization).get(org_id)
    if not org:
        return jsonify({'success': False, 'message': 'Organization not found'}), 404
    
    try:
        org.ai_usage_current = 0
        db_session.session.commit()
        return jsonify({'success': True, 'message': 'AI usage reset successfully'})
    except Exception as e:
        db_session.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
