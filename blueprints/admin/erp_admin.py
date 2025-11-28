"""
ERP Module Administration Blueprint
Manage ERP modules and user activation
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, g
from functools import wraps
from datetime import datetime

erp_admin_bp = Blueprint('erp_admin', __name__, url_prefix='/erp')

def admin_required(f):
    """Require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models import User
        from flask import current_app
        
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        db = current_app.extensions.get('sqlalchemy')
        if not db:
            return redirect(url_for('auth.login'))
        
        user = db.session.query(User).get(user_id)
        if not user or not user.has_role('system_admin'):
            return redirect(url_for('dashboard.index'))
        
        g.user = user
        g.lang = session.get('lang', 'ar')
        return f(*args, **kwargs)
    return decorated_function


@erp_admin_bp.route('/')
@admin_required
def index():
    """ERP modules management page"""
    from models import User, ERPModule, UserERPModule
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    
    # Get all modules
    modules = db.session.query(ERPModule).order_by(ERPModule.display_order).all()
    
    # Get all users for dropdown
    users = db.session.query(User).filter_by(is_active=True).order_by(User.username).all()
    
    return render_template('admin/erp/index.html',
                         lang=g.lang,
                         modules=modules,
                         users=users)


@erp_admin_bp.route('/user/<int:user_id>')
@admin_required
def user_modules(user_id):
    """Get user's active modules"""
    from models import User, UserERPModule
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    
    user = db.session.query(User).get_or_404(user_id)
    
    # Get user's active modules
    user_modules = db.session.query(UserERPModule).filter_by(user_id=user_id, is_active=True).all()
    module_ids = [um.module_id for um in user_modules]
    
    return jsonify({
        'user_id': user_id,
        'username': user.username,
        'email': user.email,
        'active_modules': module_ids
    })


@erp_admin_bp.route('/api/activate-module', methods=['POST'])
@admin_required
def activate_module():
    """Activate a module for a user"""
    from models import User, ERPModule, UserERPModule
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    
    data = request.json
    user_id = data.get('user_id')
    module_id = data.get('module_id')
    
    if not user_id or not module_id:
        return jsonify({'success': False, 'message': 'Missing parameters'}), 400
    
    # Verify user exists
    user = db.session.query(User).get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Verify module exists
    module = db.session.query(ERPModule).get(module_id)
    if not module:
        return jsonify({'success': False, 'message': 'Module not found'}), 404
    
    # Check if already activated
    existing = db.session.query(UserERPModule).filter_by(
        user_id=user_id,
        module_id=module_id
    ).first()
    
    if existing:
        if existing.is_active:
            return jsonify({'success': False, 'message': 'Module already activated'}), 400
        else:
            # Reactivate
            existing.is_active = True
            existing.activated_at = datetime.utcnow()
    else:
        # Create new activation
        user_module = UserERPModule(
            user_id=user_id,
            module_id=module_id,
            is_active=True
        )
        db.session.add(user_module)
    
    db.session.commit()
    
    # Log the action
    from models import SecurityLog
    security_log = SecurityLog(
        user_id=g.user.id,
        action='erp_module_activated',
        description=f'Activated ERP module {module.slug} for user {user.username}',
        status='success'
    )
    db.session.add(security_log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'تم تفعيل الوحدة لـ {user.username}' if g.lang == 'ar' else f'Module activated for {user.username}',
        'module_id': module_id
    })


@erp_admin_bp.route('/api/deactivate-module', methods=['POST'])
@admin_required
def deactivate_module():
    """Deactivate a module for a user"""
    from models import User, UserERPModule
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    
    data = request.json
    user_id = data.get('user_id')
    module_id = data.get('module_id')
    
    if not user_id or not module_id:
        return jsonify({'success': False, 'message': 'Missing parameters'}), 400
    
    user_module = db.session.query(UserERPModule).filter_by(
        user_id=user_id,
        module_id=module_id
    ).first()
    
    if not user_module:
        return jsonify({'success': False, 'message': 'Module not found'}), 404
    
    user_module.is_active = False
    db.session.commit()
    
    # Log the action
    from models import SecurityLog
    user = db.session.query(User).get(user_id)
    security_log = SecurityLog(
        user_id=g.user.id,
        action='erp_module_deactivated',
        description=f'Deactivated ERP module for user {user.username}',
        status='success'
    )
    db.session.add(security_log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'تم إلغاء تفعيل الوحدة' if g.lang == 'ar' else 'Module deactivated'
    })


@erp_admin_bp.route('/api/list-all-modules')
@admin_required
def list_all_modules():
    """Get all available ERP modules"""
    from models import ERPModule
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    
    modules = db.session.query(ERPModule).filter_by(is_active=True).all()
    
    return jsonify({
        'modules': [{
            'id': m.id,
            'slug': m.slug,
            'name_ar': m.name_ar,
            'name_en': m.name_en,
            'icon': m.icon,
            'color': m.color
        } for m in modules]
    })
