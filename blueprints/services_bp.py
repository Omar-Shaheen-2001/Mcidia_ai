"""
Services Blueprint
Handles all consulting services pages and API endpoints
"""

from flask import Blueprint, render_template, session, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Service, ServiceOffering, User, Project
from utils.decorators import login_required

services_bp = Blueprint('services', __name__, url_prefix='/services')

def get_lang():
    """Get current language from session"""
    return session.get('lang', 'ar')

def get_db():
    """Get database instance from current app"""
    return current_app.extensions['sqlalchemy']

def get_all_services_with_offerings():
    """Get all active services with their offerings for sidebar"""
    db = get_db()
    services = db.session.query(Service).filter_by(is_active=True).order_by(Service.display_order).all()
    for service in services:
        service.offerings = db.session.query(ServiceOffering).filter_by(
            service_id=service.id,
            is_active=True
        ).order_by(ServiceOffering.display_order).all()
    return services

@services_bp.route('/')
@login_required
def index():
    """Services homepage - shows all categories"""
    lang = get_lang()
    db = get_db()
    services = db.session.query(Service).filter_by(is_active=True).order_by(Service.display_order).all()
    
    # Get current user
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    
    # Get all services for sidebar
    all_services = get_all_services_with_offerings()
    
    return render_template(
        'services/index.html',
        services=services,
        all_services=all_services,
        current_service=None,
        current_offering=None,
        lang=lang,
        user=user
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
@login_required
def service_detail(service_slug):
    """Service category page - shows all offerings for a service"""
    lang = get_lang()
    db = get_db()
    service = db.session.query(Service).filter_by(slug=service_slug, is_active=True).first()
    if not service:
        from flask import abort
        abort(404)
    
    # Get current user
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    
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
        lang=lang,
        user=user
    )

@services_bp.route('/<service_slug>/<offering_slug>')
@login_required
def offering_detail(service_slug, offering_slug):
    """Service offering page - individual service with AI interaction"""
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
    
    # Get current user
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    
    # Get user's projects for this offering
    projects = db.session.query(Project).filter_by(
        user_id=int(user_id),
        module=f"{service_slug}_{offering_slug}"
    ).order_by(Project.updated_at.desc()).limit(5).all()
    
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
        lang=lang,
        user=user
    )

@services_bp.route('/api/<service_slug>/<offering_slug>/generate', methods=['POST'])
@login_required
def api_generate_content(service_slug, offering_slug):
    """API endpoint to generate AI content for an offering"""
    from flask import request, abort
    from utils.ai_client import llm_chat
    from models import AILog
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
    
    # Check AI credits
    plan = user.plan_ref
    if plan and plan.ai_credits_limit:
        if user.ai_credits_used >= plan.ai_credits_limit:
            return jsonify({'error': 'AI credits limit exceeded'}), 403
    
    # Get form data
    form_data = request.get_json()
    
    # Build prompt from template
    lang = session.get('lang', 'ar')
    
    # System prompt
    system_prompt = f"""أنت مستشار خبير في {service.title_ar if lang == 'ar' else service.title_en}.
مهمتك تقديم استشارات احترافية وشاملة في مجال {offering.title_ar if lang == 'ar' else offering.title_en}.
قدم تحليلاً دقيقاً وتوصيات عملية بناءً على المعلومات المقدمة."""
    
    # User message
    user_message = f"""المشروع: {form_data.get('project_name', 'غير محدد')}

الوصف:
{form_data.get('description', '')}

{f"معلومات إضافية: {form_data.get('additional_context', '')}" if form_data.get('additional_context') else ''}

يرجى تقديم استشارة شاملة ومفصلة."""
    
    try:
        # Call AI
        response_text = llm_chat(
            system_prompt=system_prompt,
            user_message=user_message,
            response_format="text"
        )
        
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
