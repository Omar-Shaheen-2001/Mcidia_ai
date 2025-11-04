from flask import render_template, session, redirect, url_for, flash
from . import member_dashboard_bp
from utils.decorators import organization_role_required
from models import db, Project, AILog
from flask_jwt_extended import get_jwt_identity

@member_dashboard_bp.route('/<int:org_id>/reports')
@organization_role_required('member', 'admin', 'owner', org_id_param='org_id')
def reports(org_id, _membership=None, _organization=None):
    """Display member's reports and project results"""
    lang = session.get('language', 'ar')
    
    # Get current user
    user_id = int(get_jwt_identity())
    
    # Get member's projects
    projects = db.session.query(Project).filter_by(
        user_id=user_id
    ).order_by(Project.created_at.desc()).all()
    
    # Get AI usage logs
    ai_logs = db.session.query(AILog).filter_by(
        user_id=user_id
    ).order_by(AILog.created_at.desc()).limit(20).all()
    
    return render_template(
        'member_dashboard/reports.html',
        lang=lang,
        organization=_organization,
        membership=_membership,
        projects=projects,
        ai_logs=ai_logs
    )
