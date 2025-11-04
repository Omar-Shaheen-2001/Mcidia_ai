from flask import render_template, session, redirect, url_for
from blueprints.org_dashboard import org_dashboard_bp
from utils.decorators import login_required, organization_role_required
from models import User, Organization, OrganizationMembership, OrganizationSettings, Project, Transaction, AILog, db
from flask import current_app
from sqlalchemy import func
from datetime import datetime, timedelta

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

def get_current_user():
    """Get current logged-in user"""
    from flask_jwt_extended import get_jwt_identity
    user_id = int(get_jwt_identity())
    db_session = get_db()
    return db_session.session.query(User).get(user_id)

@org_dashboard_bp.route('/')
@login_required
def index():
    """Redirect to organization dashboard if user has org membership, else to regular dashboard"""
    user = get_current_user()
    db_session = get_db()
    
    # Check if user has organization membership
    membership = db_session.session.query(OrganizationMembership).filter_by(
        user_id=user.id,
        is_active=True
    ).first()
    
    if membership and membership.org_role in ['owner', 'admin']:
        # Redirect to organization dashboard
        return redirect(url_for('org_dashboard.dashboard', org_id=membership.organization_id))
    else:
        # Redirect to regular dashboard
        return redirect(url_for('dashboard.index'))

@org_dashboard_bp.route('/<int:org_id>/dashboard')
@login_required
@organization_role_required('owner', 'admin', 'member', org_id_param='org_id')
def dashboard(org_id, _membership=None, _organization=None):
    """Organization Dashboard - Main page for organization managers"""
    lang = get_lang()
    db_session = get_db()
    
    org = _organization
    membership = _membership
    
    # Get organization settings
    settings = db_session.session.query(OrganizationSettings).filter_by(
        organization_id=org_id
    ).first()
    
    # Calculate statistics
    stats = {
        'total_users': len(org.users),
        'active_users': sum(1 for u in org.users if u.is_active),
        'total_projects': db_session.session.query(Project).join(User).filter(User.organization_id == org_id).count(),
        'ai_usage_current': org.ai_usage_current or 0,
        'ai_usage_limit': org.ai_usage_limit or 1000,
        'ai_usage_percentage': org.get_ai_usage_percentage(),
        'total_transactions': db_session.session.query(Transaction).join(User).filter(User.organization_id == org_id).count(),
        'total_spent': db_session.session.query(func.sum(Transaction.amount)).join(User).filter(User.organization_id == org_id).scalar() or 0
    }
    
    # Get recent activities
    recent_projects = db_session.session.query(Project).join(User).filter(
        User.organization_id == org_id
    ).order_by(Project.created_at.desc()).limit(5).all()
    
    # Get AI usage trend (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    ai_logs = db_session.session.query(
        func.date(AILog.created_at).label('date'),
        func.count(AILog.id).label('count')
    ).join(User).filter(
        User.organization_id == org_id,
        AILog.created_at >= seven_days_ago
    ).group_by(func.date(AILog.created_at)).all()
    
    return render_template(
        'org_dashboard/dashboard.html',
        org=org,
        membership=membership,
        settings=settings,
        stats=stats,
        recent_projects=recent_projects,
        ai_logs=ai_logs,
        lang=lang
    )
