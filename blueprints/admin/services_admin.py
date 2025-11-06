from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from utils.decorators import login_required, role_required
from models import Service, ServiceOffering
from flask import current_app
from datetime import datetime

services_admin_bp = Blueprint('services_admin', __name__, url_prefix='/services')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

# ==================== SERVICES MANAGEMENT ====================

@services_admin_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """List all services with their offerings count"""
    db = get_db()
    lang = get_lang()
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    
    # Build query
    query = db.session.query(Service)
    
    # Apply filters
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    if search:
        if lang == 'ar':
            query = query.filter(Service.title_ar.contains(search))
        else:
            query = query.filter(Service.title_en.contains(search))
    
    services = query.order_by(Service.display_order).all()
    
    return render_template('admin/services/index.html', 
                         services=services, 
                         lang=lang,
                         status_filter=status_filter,
                         search=search)

@services_admin_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def create_service():
    """Create new service"""
    db = get_db()
    lang = get_lang()
    
    if request.method == 'GET':
        return render_template('admin/services/create_service.html', lang=lang)
    
    # POST - Create service
    try:
        new_service = Service(
            slug=request.form.get('slug'),
            title_ar=request.form.get('title_ar'),
            title_en=request.form.get('title_en'),
            description_ar=request.form.get('description_ar'),
            description_en=request.form.get('description_en'),
            icon=request.form.get('icon', 'fa-briefcase'),
            color=request.form.get('color', '#0A2756'),
            display_order=int(request.form.get('display_order', 0)),
            is_active=request.form.get('is_active') == 'on'
        )
        
        db.session.add(new_service)
        db.session.commit()
        
        flash('تم إنشاء الخدمة بنجاح / Service created successfully' if lang == 'ar' else 'Service created successfully', 'success')
        return redirect(url_for('admin.services_admin.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ: {str(e)} / Error: {str(e)}' if lang == 'ar' else f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin.services_admin.create_service'))

@services_admin_bp.route('/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def edit_service(service_id):
    """Edit existing service"""
    db = get_db()
    lang = get_lang()
    
    service = db.session.query(Service).filter_by(id=service_id).first_or_404()
    
    if request.method == 'GET':
        return render_template('admin/services/edit_service.html', service=service, lang=lang)
    
    # POST - Update service
    try:
        service.slug = request.form.get('slug')
        service.title_ar = request.form.get('title_ar')
        service.title_en = request.form.get('title_en')
        service.description_ar = request.form.get('description_ar')
        service.description_en = request.form.get('description_en')
        service.icon = request.form.get('icon', 'fa-briefcase')
        service.color = request.form.get('color', '#0A2756')
        service.display_order = int(request.form.get('display_order', 0))
        service.is_active = request.form.get('is_active') == 'on'
        service.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('تم تحديث الخدمة بنجاح / Service updated successfully' if lang == 'ar' else 'Service updated successfully', 'success')
        return redirect(url_for('admin.services_admin.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ: {str(e)} / Error: {str(e)}' if lang == 'ar' else f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin.services_admin.edit_service', service_id=service_id))

@services_admin_bp.route('/<int:service_id>/delete', methods=['POST'])
@login_required
@role_required('system_admin')
def delete_service(service_id):
    """Delete service (soft delete)"""
    db = get_db()
    lang = get_lang()
    
    service = db.session.query(Service).filter_by(id=service_id).first_or_404()
    
    # Soft delete by deactivating
    service.is_active = False
    db.session.commit()
    
    flash('تم تعطيل الخدمة بنجاح / Service deactivated successfully' if lang == 'ar' else 'Service deactivated successfully', 'success')
    return redirect(url_for('admin.services_admin.index'))

@services_admin_bp.route('/<int:service_id>/toggle-status', methods=['POST'])
@login_required
@role_required('system_admin')
def toggle_service_status(service_id):
    """Toggle service active status"""
    db = get_db()
    lang = get_lang()
    
    service = db.session.query(Service).filter_by(id=service_id).first_or_404()
    service.is_active = not service.is_active
    db.session.commit()
    
    status_text = 'تم تفعيل الخدمة / Service activated' if service.is_active else 'تم تعطيل الخدمة / Service deactivated'
    flash(status_text if lang == 'ar' else status_text.split('/')[-1].strip(), 'success')
    return redirect(url_for('admin.services_admin.index'))

# ==================== OFFERINGS MANAGEMENT ====================

@services_admin_bp.route('/<int:service_id>/offerings')
@login_required
@role_required('system_admin')
def offerings(service_id):
    """List all offerings for a service"""
    db = get_db()
    lang = get_lang()
    
    service = db.session.query(Service).filter_by(id=service_id).first_or_404()
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    
    # Build query
    query = db.session.query(ServiceOffering).filter_by(service_id=service_id)
    
    # Apply filters
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    if search:
        if lang == 'ar':
            query = query.filter(ServiceOffering.title_ar.contains(search))
        else:
            query = query.filter(ServiceOffering.title_en.contains(search))
    
    offerings = query.order_by(ServiceOffering.display_order).all()
    
    return render_template('admin/services/offerings.html', 
                         service=service,
                         offerings=offerings, 
                         lang=lang,
                         status_filter=status_filter,
                         search=search)

@services_admin_bp.route('/<int:service_id>/offerings/create', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def create_offering(service_id):
    """Create new offering for a service"""
    db = get_db()
    lang = get_lang()
    
    service = db.session.query(Service).filter_by(id=service_id).first_or_404()
    
    if request.method == 'GET':
        return render_template('admin/services/create_offering.html', service=service, lang=lang)
    
    # POST - Create offering
    try:
        new_offering = ServiceOffering(
            service_id=service_id,
            slug=request.form.get('slug'),
            title_ar=request.form.get('title_ar'),
            title_en=request.form.get('title_en'),
            description_ar=request.form.get('description_ar'),
            description_en=request.form.get('description_en'),
            icon=request.form.get('icon', 'fa-check-circle'),
            display_order=int(request.form.get('display_order', 0)),
            is_active=request.form.get('is_active') == 'on',
            ai_prompt_template=request.form.get('ai_prompt_template'),
            ai_model=request.form.get('ai_model', 'gpt-4'),
            ai_credits_cost=int(request.form.get('ai_credits_cost', 1)),
            form_fields=request.form.get('form_fields')
        )
        
        db.session.add(new_offering)
        db.session.commit()
        
        flash('تم إنشاء الخدمة الفرعية بنجاح / Offering created successfully' if lang == 'ar' else 'Offering created successfully', 'success')
        return redirect(url_for('admin.services_admin.offerings', service_id=service_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ: {str(e)} / Error: {str(e)}' if lang == 'ar' else f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin.services_admin.create_offering', service_id=service_id))

@services_admin_bp.route('/<int:service_id>/offerings/<int:offering_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def edit_offering(service_id, offering_id):
    """Edit existing offering"""
    db = get_db()
    lang = get_lang()
    
    service = db.session.query(Service).filter_by(id=service_id).first_or_404()
    offering = db.session.query(ServiceOffering).filter_by(id=offering_id).first_or_404()
    
    if request.method == 'GET':
        return render_template('admin/services/edit_offering.html', service=service, offering=offering, lang=lang)
    
    # POST - Update offering
    try:
        offering.slug = request.form.get('slug')
        offering.title_ar = request.form.get('title_ar')
        offering.title_en = request.form.get('title_en')
        offering.description_ar = request.form.get('description_ar')
        offering.description_en = request.form.get('description_en')
        offering.icon = request.form.get('icon', 'fa-check-circle')
        offering.display_order = int(request.form.get('display_order', 0))
        offering.is_active = request.form.get('is_active') == 'on'
        offering.ai_prompt_template = request.form.get('ai_prompt_template')
        offering.ai_model = request.form.get('ai_model', 'gpt-4')
        offering.ai_credits_cost = int(request.form.get('ai_credits_cost', 1))
        offering.form_fields = request.form.get('form_fields')
        
        db.session.commit()
        
        flash('تم تحديث الخدمة الفرعية بنجاح / Offering updated successfully' if lang == 'ar' else 'Offering updated successfully', 'success')
        return redirect(url_for('admin.services_admin.offerings', service_id=service_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ: {str(e)} / Error: {str(e)}' if lang == 'ar' else f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin.services_admin.edit_offering', service_id=service_id, offering_id=offering_id))

@services_admin_bp.route('/<int:service_id>/offerings/<int:offering_id>/delete', methods=['POST'])
@login_required
@role_required('system_admin')
def delete_offering(service_id, offering_id):
    """Delete offering (soft delete)"""
    db = get_db()
    lang = get_lang()
    
    offering = db.session.query(ServiceOffering).filter_by(id=offering_id).first_or_404()
    
    # Soft delete by deactivating
    offering.is_active = False
    db.session.commit()
    
    flash('تم تعطيل الخدمة الفرعية بنجاح / Offering deactivated successfully' if lang == 'ar' else 'Offering deactivated successfully', 'success')
    return redirect(url_for('admin.services_admin.offerings', service_id=service_id))

@services_admin_bp.route('/<int:service_id>/offerings/<int:offering_id>/toggle-status', methods=['POST'])
@login_required
@role_required('system_admin')
def toggle_offering_status(service_id, offering_id):
    """Toggle offering active status"""
    db = get_db()
    lang = get_lang()
    
    offering = db.session.query(ServiceOffering).filter_by(id=offering_id).first_or_404()
    offering.is_active = not offering.is_active
    db.session.commit()
    
    status_text = 'تم تفعيل الخدمة الفرعية / Offering activated' if offering.is_active else 'تم تعطيل الخدمة الفرعية / Offering deactivated'
    flash(status_text if lang == 'ar' else status_text.split('/')[-1].strip(), 'success')
    return redirect(url_for('admin.services_admin.offerings', service_id=service_id))
