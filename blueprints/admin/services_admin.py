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
        title_ar = request.form.get('title_ar', 'New Service')
        new_service = Service(
            name=title_ar,  # Use Arabic title as default name
            slug=request.form.get('slug'),
            title_ar=title_ar,
            title_en=request.form.get('title_en'),
            description=request.form.get('description_ar', ''),  # Default description
            description_ar=request.form.get('description_ar'),
            description_en=request.form.get('description_en'),
            icon=request.form.get('icon', 'fa-briefcase'),
            category=request.form.get('category', ''),
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
        service.name = request.form.get('title_ar', service.name)  # Update name from title_ar
        service.slug = request.form.get('slug')
        service.title_ar = request.form.get('title_ar')
        service.title_en = request.form.get('title_en')
        service.description = request.form.get('description_ar', service.description)
        service.description_ar = request.form.get('description_ar')
        service.description_en = request.form.get('description_en')
        service.icon = request.form.get('icon', 'fa-briefcase')
        service.category = request.form.get('category', service.category)
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
        import json
        
        # Validate and parse form_fields JSON
        form_fields_json = request.form.get('form_fields', '[]')
        try:
            form_fields = json.loads(form_fields_json) if form_fields_json else []
            
            # Validate schema structure
            if not isinstance(form_fields, list):
                flash('Invalid form fields format. Must be a JSON array.' if lang == 'en' else 'صيغة حقول غير صحيحة. يجب أن تكون مصفوفة JSON.', 'danger')
                return redirect(url_for('admin.services_admin.create_offering', service_id=service_id))
            
            # Validate each field has required properties
            for field in form_fields:
                if not isinstance(field, dict):
                    flash('Each field must be an object.' if lang == 'en' else 'كل حقل يجب أن يكون كائن.', 'danger')
                    return redirect(url_for('admin.services_admin.create_offering', service_id=service_id))
                
                if 'name' not in field or not field['name']:
                    flash('Each field must have a name.' if lang == 'en' else 'كل حقل يجب أن يحتوي على اسم.', 'danger')
                    return redirect(url_for('admin.services_admin.create_offering', service_id=service_id))
                
                # Validate field name format (alphanumeric + underscore only)
                if not field['name'].replace('_', '').isalnum():
                    flash(f'Invalid field name: {field["name"]}. Use only letters, numbers, and underscores.' if lang == 'en' else f'اسم حقل غير صحيح: {field["name"]}. استخدم فقط الحروف والأرقام والشرطات السفلية.', 'danger')
                    return redirect(url_for('admin.services_admin.create_offering', service_id=service_id))
                
                # Validate field type
                valid_types = ['text', 'textarea', 'number', 'email', 'date', 'select']
                if field.get('type') not in valid_types:
                    flash(f'Invalid field type: {field.get("type")}. Must be one of: {", ".join(valid_types)}' if lang == 'en' else f'نوع حقل غير صحيح: {field.get("type")}', 'danger')
                    return redirect(url_for('admin.services_admin.create_offering', service_id=service_id))
            
            # Convert back to JSON string for storage
            form_fields_json = json.dumps(form_fields)
            
        except json.JSONDecodeError:
            flash('Invalid JSON format in form fields.' if lang == 'en' else 'صيغة JSON غير صحيحة في الحقول.', 'danger')
            return redirect(url_for('admin.services_admin.create_offering', service_id=service_id))
        
        title_ar = request.form.get('title_ar', 'New Offering')
        new_offering = ServiceOffering(
            service_id=service_id,
            name=title_ar,  # Use Arabic title as default name
            slug=request.form.get('slug'),
            title_ar=title_ar,
            title_en=request.form.get('title_en'),
            description=request.form.get('description_ar', ''),  # Default description
            description_ar=request.form.get('description_ar'),
            description_en=request.form.get('description_en'),
            icon=request.form.get('icon', 'fa-check-circle'),
            price=float(request.form.get('price', 0)) if request.form.get('price') else None,
            display_order=int(request.form.get('display_order', 0)),
            is_active=request.form.get('is_active') == 'on',
            ai_prompt_template=request.form.get('ai_prompt_template'),
            ai_model=request.form.get('ai_model', 'gpt-4'),
            ai_credits_cost=int(request.form.get('ai_credits_cost', 1)),
            form_fields=form_fields_json
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
        import json
        
        # Validate and parse form_fields JSON
        form_fields_json = request.form.get('form_fields', '[]')
        try:
            form_fields = json.loads(form_fields_json) if form_fields_json else []
            
            # Validate schema structure
            if not isinstance(form_fields, list):
                flash('Invalid form fields format. Must be a JSON array.' if lang == 'en' else 'صيغة حقول غير صحيحة. يجب أن تكون مصفوفة JSON.', 'danger')
                return redirect(url_for('admin.services_admin.edit_offering', service_id=service_id, offering_id=offering_id))
            
            # Validate each field has required properties
            for field in form_fields:
                if not isinstance(field, dict):
                    flash('Each field must be an object.' if lang == 'en' else 'كل حقل يجب أن يكون كائن.', 'danger')
                    return redirect(url_for('admin.services_admin.edit_offering', service_id=service_id, offering_id=offering_id))
                
                if 'name' not in field or not field['name']:
                    flash('Each field must have a name.' if lang == 'en' else 'كل حقل يجب أن يحتوي على اسم.', 'danger')
                    return redirect(url_for('admin.services_admin.edit_offering', service_id=service_id, offering_id=offering_id))
                
                # Validate field name format (alphanumeric + underscore only)
                if not field['name'].replace('_', '').isalnum():
                    flash(f'Invalid field name: {field["name"]}. Use only letters, numbers, and underscores.' if lang == 'en' else f'اسم حقل غير صحيح: {field["name"]}. استخدم فقط الحروف والأرقام والشرطات السفلية.', 'danger')
                    return redirect(url_for('admin.services_admin.edit_offering', service_id=service_id, offering_id=offering_id))
                
                # Validate field type
                valid_types = ['text', 'textarea', 'number', 'email', 'date', 'select']
                if field.get('type') not in valid_types:
                    flash(f'Invalid field type: {field.get("type")}. Must be one of: {", ".join(valid_types)}' if lang == 'en' else f'نوع حقل غير صحيح: {field.get("type")}', 'danger')
                    return redirect(url_for('admin.services_admin.edit_offering', service_id=service_id, offering_id=offering_id))
            
            # Convert back to JSON string for storage
            form_fields_json = json.dumps(form_fields)
            
        except json.JSONDecodeError:
            flash('Invalid JSON format in form fields.' if lang == 'en' else 'صيغة JSON غير صحيحة في الحقول.', 'danger')
            return redirect(url_for('admin.services_admin.edit_offering', service_id=service_id, offering_id=offering_id))
        
        offering.name = request.form.get('title_ar', offering.name)  # Update name from title_ar
        offering.slug = request.form.get('slug')
        offering.title_ar = request.form.get('title_ar')
        offering.title_en = request.form.get('title_en')
        offering.description = request.form.get('description_ar', offering.description)
        offering.description_ar = request.form.get('description_ar')
        offering.description_en = request.form.get('description_en')
        offering.icon = request.form.get('icon', 'fa-check-circle')
        offering.price = float(request.form.get('price', 0)) if request.form.get('price') else None
        offering.display_order = int(request.form.get('display_order', 0))
        offering.is_active = request.form.get('is_active') == 'on'
        offering.ai_prompt_template = request.form.get('ai_prompt_template')
        offering.ai_model = request.form.get('ai_model', 'gpt-4')
        offering.ai_credits_cost = int(request.form.get('ai_credits_cost', 1))
        offering.form_fields = form_fields_json
        offering.updated_at = datetime.utcnow()
        
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
