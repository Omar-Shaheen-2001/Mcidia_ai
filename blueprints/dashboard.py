from flask import Blueprint, render_template, session, current_app, redirect, url_for, jsonify, request, flash
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Project, AILog, Transaction, Service, ServiceOffering, ChatSession
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.query(User).get(user_id)
    
    # Get statistics
    total_projects = db.session.query(Project).filter_by(user_id=user_id).count()
    active_projects = db.session.query(Project).filter_by(user_id=user_id, status='draft').count()
    ai_credits = user.ai_credits_used if user else 0
    total_consultations = db.session.query(ChatSession).filter_by(user_id=user_id).count()
    
    # Get recent projects
    recent_projects = db.session.query(Project).filter_by(user_id=user_id).order_by(Project.updated_at.desc()).limit(5).all()
    
    # Get recent AI logs
    recent_ai_activity = db.session.query(AILog).filter_by(user_id=user_id).order_by(AILog.created_at.desc()).limit(5).all()
    
    # Build service info map for projects
    project_services = {}
    for project in recent_projects:
        if project.module and '_' in project.module:
            parts = project.module.split('_', 1)
            if len(parts) == 2:
                service_slug, offering_slug = parts
                service = db.session.query(Service).filter_by(slug=service_slug).first()
                if service:
                    offering = db.session.query(ServiceOffering).filter_by(
                        service_id=service.id,
                        slug=offering_slug
                    ).first()
                    if offering:
                        project_services[project.id] = {
                            'service': service,
                            'offering': offering
                        }
    
    # Get all active services for dashboard display
    all_services = db.session.query(Service).filter_by(is_active=True).order_by(Service.display_order).limit(8).all()
    
    lang = session.get('language', 'ar')
    
    return render_template('dashboard/index.html', 
                         user=user,
                         total_projects=total_projects,
                         active_projects=active_projects,
                         ai_credits=ai_credits,
                         total_consultations=total_consultations,
                         recent_projects=recent_projects,
                         recent_ai_activity=recent_ai_activity,
                         project_services=project_services,
                         all_services=all_services,
                         lang=lang)

@dashboard_bp.route('/projects')
@login_required
def all_projects():
    """View all projects with pagination and filters"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.query(User).get(user_id)
    
    # Pagination
    page = session.get('projects_page', 1) if isinstance(session.get('projects_page'), int) else 1
    per_page = 10
    
    # Get all projects with pagination
    projects_query = db.session.query(Project).filter_by(user_id=user_id).order_by(Project.updated_at.desc())
    projects_paginated = projects_query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Build service info map for all projects
    project_services = {}
    for project in projects_paginated.items:
        if project.module and '_' in project.module:
            parts = project.module.split('_', 1)
            if len(parts) == 2:
                service_slug, offering_slug = parts
                service = db.session.query(Service).filter_by(slug=service_slug).first()
                if service:
                    offering = db.session.query(ServiceOffering).filter_by(
                        service_id=service.id,
                        slug=offering_slug
                    ).first()
                    if offering:
                        project_services[project.id] = {
                            'service': service,
                            'offering': offering
                        }
    
    # Get statistics
    total_projects = projects_query.count()
    draft_projects = db.session.query(Project).filter_by(user_id=user_id, status='draft').count()
    completed_projects = db.session.query(Project).filter_by(user_id=user_id, status='completed').count()
    archived_projects = db.session.query(Project).filter_by(user_id=user_id, status='archived').count()
    
    lang = session.get('language', 'ar')
    
    return render_template('dashboard/projects.html',
                         user=user,
                         projects=projects_paginated.items,
                         pagination=projects_paginated,
                         project_services=project_services,
                         total_projects=total_projects,
                         draft_projects=draft_projects,
                         completed_projects=completed_projects,
                         archived_projects=archived_projects,
                         current_page=page,
                         lang=lang)

@dashboard_bp.route('/project/<int:project_id>')
@login_required
def view_project(project_id):
    """View project details"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    
    project = db.session.query(Project).filter_by(id=project_id, user_id=user_id).first_or_404()
    lang = session.get('language', 'ar')
    
    # Get service info
    project_services = {}
    if project.module and '_' in project.module:
        parts = project.module.split('_', 1)
        if len(parts) == 2:
            service_slug, offering_slug = parts
            service = db.session.query(Service).filter_by(slug=service_slug).first()
            if service:
                offering = db.session.query(ServiceOffering).filter_by(
                    service_id=service.id,
                    slug=offering_slug
                ).first()
                if offering:
                    project_services = {'service': service, 'offering': offering}
    
    try:
        content = json.loads(project.content) if project.content else {}
    except:
        content = {}
    
    return render_template('dashboard/view_project.html',
                         project=project,
                         project_services=project_services,
                         content=content,
                         lang=lang)

@dashboard_bp.route('/project/<int:project_id>/edit')
@login_required
def edit_project(project_id):
    """Edit project and generate consultation"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    
    project = db.session.query(Project).filter_by(id=project_id, user_id=user_id).first_or_404()
    
    # Redirect to edit page with consultation capability
    return redirect(url_for('services.view_project', project_id=project_id))

@dashboard_bp.route('/api/project/<int:project_id>/delete', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """Delete a project"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    
    project = db.session.query(Project).filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    try:
        db.session.delete(project)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Project deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
