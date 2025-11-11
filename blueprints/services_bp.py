"""
Services Blueprint
Handles all consulting services pages and API endpoints
"""

from flask import Blueprint, render_template, session, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Service, ServiceOffering, User, Project, AILog
from utils.decorators import login_required
from utils.ai_providers.ai_manager import AIManager
import json

services_bp = Blueprint('services', __name__, url_prefix='/services')

def get_lang():
    """Get current language from session"""
    return session.get('language', 'ar')

def get_db():
    """Get database instance from current app"""
    return current_app.extensions['sqlalchemy']

def get_all_services_with_offerings():
    """Get all active services with their offerings for sidebar"""
    db = get_db()
    services = db.session.query(Service).filter_by(is_active=True).order_by(Service.display_order).all()
    # Use a separate attribute to avoid mutating the SQLAlchemy relationship
    for service in services:
        service.active_offerings = db.session.query(ServiceOffering).filter_by(
            service_id=service.id,
            is_active=True
        ).order_by(ServiceOffering.display_order).all()
    return services

@services_bp.route('/')
def index():
    """Services homepage - shows all categories (public access)"""
    lang = get_lang()
    db = get_db()
    services = db.session.query(Service).filter_by(is_active=True).order_by(Service.display_order).all()
    
    # Get all services for sidebar
    all_services = get_all_services_with_offerings()
    
    return render_template(
        'services/index.html',
        services=services,
        all_services=all_services,
        current_service=None,
        current_offering=None,
        lang=lang
    )

@services_bp.route('/api/all')
def api_get_all_services():
    """API endpoint to get all services with their offerings"""
    lang = get_lang()
    db = get_db()
    services = db.session.query(Service).filter_by(is_active=True).order_by(Service.display_order).all()
    
    result = []
    for service in services:
        service_dict = service.to_dict(lang)
        service_dict['offerings'] = [
            offering.to_dict(lang) 
            for offering in sorted(service.offerings, key=lambda x: x.display_order)
            if offering.is_active
        ]
        result.append(service_dict)
    
    return jsonify(result)

@services_bp.route('/<service_slug>')
def service_detail(service_slug):
    """Service category page - shows all offerings for a service (public access)"""
    lang = get_lang()
    db = get_db()
    service = db.session.query(Service).filter_by(slug=service_slug, is_active=True).first()
    if not service:
        from flask import abort
        abort(404)
    
    # Get active offerings
    offerings = db.session.query(ServiceOffering).filter_by(
        service_id=service.id,
        is_active=True
    ).order_by(ServiceOffering.display_order).all()
    
    # Get all services for sidebar
    all_services = get_all_services_with_offerings()
    
    return render_template(
        'services/service_detail.html',
        service=service,
        offerings=offerings,
        all_services=all_services,
        current_service=service,
        current_offering=None,
        lang=lang
    )

@services_bp.route('/<service_slug>/<offering_slug>')
def offering_detail(service_slug, offering_slug):
    """Service offering page - individual service with AI interaction (public access)"""
    from flask_jwt_extended import verify_jwt_in_request
    
    lang = get_lang()
    db = get_db()
    
    service = db.session.query(Service).filter_by(slug=service_slug, is_active=True).first()
    if not service:
        from flask import abort
        abort(404)
    
    offering = db.session.query(ServiceOffering).filter_by(
        service_id=service.id,
        slug=offering_slug,
        is_active=True
    ).first()
    if not offering:
        from flask import abort
        abort(404)
    
    # Get current user if logged in
    user = None
    projects = []
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            user = db.session.get(User, int(user_id))
            # Get user's projects for this offering only if logged in
            projects = db.session.query(Project).filter_by(
                user_id=int(user_id),
                module=f"{service_slug}_{offering_slug}"
            ).order_by(Project.updated_at.desc()).limit(5).all()
    except:
        pass
    
    # Get all services for sidebar
    all_services = get_all_services_with_offerings()
    
    return render_template(
        'services/offering_detail.html',
        service=service,
        offering=offering,
        projects=projects,
        all_services=all_services,
        current_service=service,
        current_offering=offering,
        lang=lang
    )

@services_bp.route('/api/<service_slug>/<offering_slug>/generate', methods=['POST'])
@login_required
def api_generate_content(service_slug, offering_slug):
    """API endpoint to generate AI content for an offering"""
    from flask import request, abort
    import json
    
    db = get_db()
    
    # Get offering
    service = db.session.query(Service).filter_by(slug=service_slug).first()
    if not service:
        abort(404)
    
    offering = db.session.query(ServiceOffering).filter_by(
        service_id=service.id,
        slug=offering_slug
    ).first()
    if not offering:
        abort(404)
    
    # Get current user
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    
    # Initialize ai_credits_used if None
    if user.ai_credits_used is None:
        user.ai_credits_used = 0
    
    # Check AI credits
    plan = user.plan_ref
    if plan and plan.ai_credits_limit:
        if user.ai_credits_used >= plan.ai_credits_limit:
            return jsonify({'error': 'AI credits limit exceeded'}), 403
    
    # Get form data
    form_data = request.get_json()
    
    # Build prompt from template
    lang = session.get('language', 'ar')
    
    # Use custom prompt template if available, otherwise use default
    if offering.ai_prompt_template:
        # Parse form_fields to extract field names and values
        import html
        form_fields_schema = []
        try:
            if offering.form_fields:
                form_fields_schema = json.loads(offering.form_fields) if isinstance(offering.form_fields, str) else offering.form_fields
        except Exception as e:
            return jsonify({'error': 'Invalid form fields schema'}), 500
        
        # Validate that form_fields_schema is a list
        if not isinstance(form_fields_schema, list):
            form_fields_schema = []
        
        # Build replacement dictionary with field values
        replacement_dict = {
            'project_name': form_data.get('project_name', 'غير محدد / Not specified'),
            'description': form_data.get('description', ''),
            'additional_context': form_data.get('additional_context', '')
        }
        
        # Add custom fields to replacement dict with validation
        for field in form_fields_schema:
            if not isinstance(field, dict):
                continue
                
            field_name = field.get('name')
            if not field_name or not isinstance(field_name, str):
                continue
            
            field_type = field.get('type', 'text')
            field_value = form_data.get(field_name, 'N/A')
            
            # Validate required fields
            if field.get('required') and (not field_value or field_value == 'N/A'):
                return jsonify({'error': f'Required field missing: {field_name}'}), 400
            
            # Type validation
            if field_type == 'number' and field_value != 'N/A':
                try:
                    field_value = float(field_value)
                except ValueError:
                    return jsonify({'error': f'Invalid number format for field: {field_name}'}), 400
            
            # Sanitize field value to prevent injection
            # Convert to string and escape HTML/special characters
            field_value_str = str(field_value)
            # Remove or escape potential prompt injection characters
            field_value_sanitized = field_value_str.replace('{', '').replace('}', '').strip()
            # Limit length to prevent extremely long inputs
            if len(field_value_sanitized) > 5000:
                field_value_sanitized = field_value_sanitized[:5000] + '...'
            
            replacement_dict[field_name] = field_value_sanitized
        
        # Replace {field_name} with actual values in prompt template
        system_prompt = offering.ai_prompt_template
        for field_name, field_value in replacement_dict.items():
            # Use safe replacement - only replace exact {field_name} pattern
            placeholder = f'{{{field_name}}}'
            if placeholder in system_prompt:
                system_prompt = system_prompt.replace(placeholder, str(field_value))
        
        # User message is just the data summary
        user_message = f"""المشروع / Project: {form_data.get('project_name', 'غير محدد')}

{f"الوصف / Description: {form_data.get('description', '')}" if form_data.get('description') else ''}

{"معلومات إضافية / Additional info: " + form_data.get('additional_context', '') if form_data.get('additional_context') else ''}

يرجى تقديم استشارة شاملة ومفصلة / Please provide comprehensive consultation."""
    else:
        # Default prompt (fallback)
        system_prompt = f"""أنت مستشار خبير في {service.title_ar if lang == 'ar' else service.title_en}.
مهمتك تقديم استشارات احترافية وشاملة في مجال {offering.title_ar if lang == 'ar' else offering.title_en}.
قدم تحليلاً دقيقاً وتوصيات عملية بناءً على المعلومات المقدمة."""
        
        user_message = f"""المشروع: {form_data.get('project_name', 'غير محدد')}

الوصف:
{form_data.get('description', '')}

{f"معلومات إضافية: {form_data.get('additional_context', '')}" if form_data.get('additional_context') else ''}

يرجى تقديم استشارة شاملة ومفصلة."""
    
    try:
        # Use HuggingFace AI via AIManager (same as Strategic Planning)
        ai_manager = AIManager.for_use_case('custom_consultation')
        response_text = ai_manager.chat(system_prompt, user_message)
        
        # Log AI usage
        ai_log = AILog(
            user_id=int(user_id),
            module=f"{service_slug}_{offering_slug}",
            prompt=f"{system_prompt}\n\nUser: {user_message}",
            response=response_text,
            tokens_used=offering.ai_credits_cost or 1
        )
        db.session.add(ai_log)
        
        # Update user credits
        user.ai_credits_used += (offering.ai_credits_cost or 1)
        
        # Create project
        project = Project(
            user_id=int(user_id),
            title=f"{offering.title_ar if lang == 'ar' else offering.title_en} - {form_data.get('project_name', 'جديد')}",
            module=f"{service_slug}_{offering_slug}",
            content=json.dumps({
                'input': form_data,
                'output': response_text
            }, ensure_ascii=False),
            status='completed'
        )
        db.session.add(project)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': response_text,
            'project_id': project.id,
            'credits_used': offering.ai_credits_cost or 1,
            'credits_remaining': (plan.ai_credits_limit - user.ai_credits_used) if plan and plan.ai_credits_limit else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@services_bp.route('/project/<int:project_id>/view')
@login_required
def view_project(project_id):
    """View a consultation project"""
    from flask import abort
    
    db = get_db()
    lang = session.get('language', 'ar')
    
    # Get project
    project = db.session.get(Project, project_id)
    if not project:
        abort(404)
    
    # Check ownership
    user_id = get_jwt_identity()
    if project.user_id != int(user_id):
        abort(403)
    
    # Parse module to get service and offering info
    service = None
    offering = None
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
    
    # Parse project content
    project_data = {}
    try:
        project_data = json.loads(project.content) if project.content else {}
    except:
        project_data = {'input': {}, 'output': ''}
    
    return render_template(
        'services/project_view.html',
        project=project,
        service=service,
        offering=offering,
        project_data=project_data,
        lang=lang
    )
