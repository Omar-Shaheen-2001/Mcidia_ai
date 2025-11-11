from flask import Blueprint, render_template, request, session
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required, role_required
from models import User, Project, Service, ServiceOffering
from flask import current_app
from datetime import datetime

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@projects_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """List all user projects"""
    db = get_db()
    lang = get_lang()
    
    # Get filter parameters
    status_filter = request.args.get('status')
    user_search = request.args.get('user_search', '')
    service_filter = request.args.get('service')
    
    # Build query
    query = db.session.query(Project).join(User, Project.user_id == User.id)
    
    if status_filter:
        query = query.filter(Project.status == status_filter)
    
    if user_search:
        query = query.filter(
            (User.username.ilike(f'%{user_search}%')) |
            (User.email.ilike(f'%{user_search}%'))
        )
    
    if service_filter:
        # Filter by service slug (module starts with service_slug)
        query = query.filter(Project.module.like(f'{service_filter}%'))
    
    # Get projects ordered by creation date (most recent first)
    projects = query.order_by(Project.created_at.desc()).all()
    
    # Build project details with service/offering info
    project_details = []
    for project in projects:
        detail = {
            'project': project,
            'user': project.user,
            'service': None,
            'offering': None
        }
        
        # Parse module to extract service and offering
        if project.module and '_' in project.module:
            parts = project.module.split('_', 1)
            if len(parts) == 2:
                service_slug, offering_slug = parts
                service = db.session.query(Service).filter_by(slug=service_slug).first()
                if service:
                    detail['service'] = service
                    offering = db.session.query(ServiceOffering).filter_by(
                        service_id=service.id,
                        slug=offering_slug
                    ).first()
                    if offering:
                        detail['offering'] = offering
        
        project_details.append(detail)
    
    # Get all services for filter dropdown
    services = db.session.query(Service).filter_by(is_active=True).order_by(Service.display_order).all()
    
    # Get statistics
    total_projects = len(projects)
    draft_projects = sum(1 for p in projects if p.status == 'draft')
    completed_projects = sum(1 for p in projects if p.status == 'completed')
    
    return render_template(
        'admin/projects/index.html',
        project_details=project_details,
        services=services,
        lang=lang,
        current_status_filter=status_filter,
        current_user_search=user_search,
        current_service_filter=service_filter,
        total_projects=total_projects,
        draft_projects=draft_projects,
        completed_projects=completed_projects
    )
