"""
Services Blueprint
Handles all consulting services pages and API endpoints
"""

from flask import Blueprint, render_template, session, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Service, ServiceOffering, User, Project
from app import db
from utils.decorators import login_required

services_bp = Blueprint('services', __name__, url_prefix='/services')

def get_lang():
    """Get current language from session"""
    return session.get('lang', 'ar')

@services_bp.route('/')
@login_required
def index():
    """Services homepage - shows all categories"""
    lang = get_lang()
    services = Service.query.filter_by(is_active=True).order_by(Service.display_order).all()
    
    # Get current user
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    return render_template(
        'services/index.html',
        services=services,
        lang=lang,
        user=user
    )

@services_bp.route('/api/all')
def api_get_all_services():
    """API endpoint to get all services with their offerings"""
    lang = get_lang()
    services = Service.query.filter_by(is_active=True).order_by(Service.display_order).all()
    
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
    service = Service.query.filter_by(slug=service_slug, is_active=True).first_or_404()
    
    # Get current user
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    # Get active offerings
    offerings = ServiceOffering.query.filter_by(
        service_id=service.id,
        is_active=True
    ).order_by(ServiceOffering.display_order).all()
    
    return render_template(
        'services/service_detail.html',
        service=service,
        offerings=offerings,
        lang=lang,
        user=user
    )

@services_bp.route('/<service_slug>/<offering_slug>')
@login_required
def offering_detail(service_slug, offering_slug):
    """Service offering page - individual service with AI interaction"""
    lang = get_lang()
    service = Service.query.filter_by(slug=service_slug, is_active=True).first_or_404()
    offering = ServiceOffering.query.filter_by(
        service_id=service.id,
        slug=offering_slug,
        is_active=True
    ).first_or_404()
    
    # Get current user
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    # Get user's projects for this offering
    projects = Project.query.filter_by(
        user_id=user_id,
        module=f"{service_slug}_{offering_slug}"
    ).order_by(Project.updated_at.desc()).limit(5).all()
    
    return render_template(
        'services/offering_detail.html',
        service=service,
        offering=offering,
        projects=projects,
        lang=lang,
        user=user
    )

@services_bp.route('/api/<service_slug>/<offering_slug>/generate', methods=['POST'])
@login_required
def api_generate_content(service_slug, offering_slug):
    """API endpoint to generate AI content for an offering"""
    from flask import request
    from utils.ai_client import llm_chat
    from models import AILog
    import json
    
    # Get offering
    service = Service.query.filter_by(slug=service_slug).first_or_404()
    offering = ServiceOffering.query.filter_by(
        service_id=service.id,
        slug=offering_slug
    ).first_or_404()
    
    # Get current user
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    # Check AI credits
    plan = user.plan_ref
    if plan and plan.ai_credits_limit:
        if user.ai_credits_used >= plan.ai_credits_limit:
            return jsonify({'error': 'AI credits limit exceeded'}), 403
    
    # Get form data
    form_data = request.get_json()
    
    # Build prompt from template
    prompt_template = offering.ai_prompt_template or """
    أنت مستشار خبير في {service_title}.
    المطلوب: {offering_title}
    
    البيانات المقدمة:
    {form_data}
    
    قدم استشارة احترافية وشاملة.
    """
    
    lang = session.get('lang', 'ar')
    prompt = prompt_template.format(
        service_title=service.title_ar if lang == 'ar' else service.title_en,
        offering_title=offering.title_ar if lang == 'ar' else offering.title_en,
        form_data=json.dumps(form_data, ensure_ascii=False, indent=2)
    )
    
    try:
        # Call AI
        response_text = llm_chat(
            prompt=prompt,
            model=offering.ai_model or 'gpt-4',
            temperature=0.7
        )
        
        # Log AI usage
        ai_log = AILog(
            user_id=user_id,
            module=f"{service_slug}_{offering_slug}",
            prompt=prompt,
            response=response_text,
            tokens_used=offering.ai_credits_cost or 1
        )
        db.session.add(ai_log)
        
        # Update user credits
        user.ai_credits_used += (offering.ai_credits_cost or 1)
        
        # Create project
        project = Project(
            user_id=user_id,
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
