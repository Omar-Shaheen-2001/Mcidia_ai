from flask import render_template, session, redirect, url_for, flash
from . import member_dashboard_bp
from utils.decorators import organization_role_required
from models import db, Project, User, AILog
from sqlalchemy import func

@member_dashboard_bp.route('/<int:org_id>/dashboard')
@organization_role_required('member', 'admin', 'owner', org_id_param='org_id')
def index(org_id, _membership=None, _organization=None):
    """Member dashboard - shows only member's own projects and activities"""
    lang = session.get('language', 'ar')
    
    # Get current user
    from flask_jwt_extended import get_jwt_identity
    user_id = int(get_jwt_identity())
    
    # Get member's statistics
    stats = {
        'my_projects': db.session.query(Project).filter_by(user_id=user_id).count(),
        'active_projects': db.session.query(Project).filter_by(
            user_id=user_id,
            status='active'
        ).count(),
        'completed_projects': db.session.query(Project).filter_by(
            user_id=user_id,
            status='completed'
        ).count(),
        'ai_usage': db.session.query(func.sum(AILog.tokens_used)).filter_by(user_id=user_id).scalar() or 0
    }
    
    # Get member's recent projects
    recent_projects = db.session.query(Project).filter_by(
        user_id=user_id
    ).order_by(Project.created_at.desc()).limit(5).all()
    
    return render_template(
        'member_dashboard/dashboard.html',
        lang=lang,
        organization=_organization,
        membership=_membership,
        stats=stats,
        recent_projects=recent_projects
    )
