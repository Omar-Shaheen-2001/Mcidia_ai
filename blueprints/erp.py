"""
ERP System Blueprint
Handles ERP modules, subscriptions, and plan management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, ERPModule, ERPPlan, UserERPSubscription, UserERPModule
from datetime import datetime, timedelta

erp_bp = Blueprint('erp', __name__, url_prefix='/erp')


@erp_bp.route('/')
@jwt_required(locations=['cookies'])
def index():
    """ERP Dashboard - Show modules and subscription plans"""
    db = current_app.extensions['sqlalchemy']
    user_id_str = get_jwt_identity()
    if not user_id_str:
        flash('Please login to access ERP system', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = int(user_id_str)
    user = db.session.get(User, user_id)
    
    # Get language from session
    lang = session.get('language', 'ar')
    
    # Get all ERP modules
    all_modules = db.session.query(ERPModule)\
        .filter_by(is_active=True)\
        .order_by(ERPModule.display_order)\
        .all()
    
    # Get all ERP plans
    all_plans = db.session.query(ERPPlan)\
        .filter_by(is_active=True)\
        .order_by(ERPPlan.display_order)\
        .all()
    
    # Get user's current ERP subscription
    user_subscription = db.session.query(UserERPSubscription)\
        .filter_by(user_id=user_id, status='active')\
        .first()
    
    # Get user's activated modules
    activated_module_ids = []
    if user_subscription:
        # Get modules from user's plan
        activated_module_ids = [m.id for m in user_subscription.plan.modules]
    
    # Prepare modules with activation status
    modules_data = []
    for module in all_modules:
        modules_data.append({
            'id': module.id,
            'slug': module.slug,
            'name': module.name_ar if lang == 'ar' else module.name_en,
            'description': module.description_ar if lang == 'ar' else module.description_en,
            'icon': module.icon,
            'color': module.color,
            'is_activated': module.id in activated_module_ids
        })
    
    # Prepare plans data
    plans_data = []
    for plan in all_plans:
        plan_module_ids = [m.id for m in plan.modules]
        plans_data.append({
            'id': plan.id,
            'name': plan.name,
            'name_display': plan.name_ar if lang == 'ar' else plan.name_en,
            'price': plan.price,
            'billing_period': plan.billing_period,
            'max_users': plan.max_users,
            'features': plan.features_ar if lang == 'ar' else plan.features_en,
            'module_count': len(plan_module_ids),
            'is_current': user_subscription and user_subscription.plan_id == plan.id
        })
    
    return render_template('erp/index.html',
                         modules=modules_data,
                         plans=plans_data,
                         current_subscription=user_subscription,
                         lang=lang)


@erp_bp.route('/subscribe/<int:plan_id>', methods=['POST'])
@jwt_required(locations=['cookies'])
def subscribe(plan_id):
    """Subscribe to an ERP plan"""
    db = current_app.extensions['sqlalchemy']
    user_id_str = get_jwt_identity()
    if not user_id_str:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user_id = int(user_id_str)
    lang = session.get('language', 'ar')
    
    # Get the plan
    plan = db.session.get(ERPPlan, plan_id)
    if not plan or not plan.is_active:
        message = 'الخطة غير موجودة' if lang == 'ar' else 'Plan not found'
        return jsonify({'success': False, 'message': message}), 404
    
    # Check for existing active subscription
    existing_subscription = db.session.query(UserERPSubscription)\
        .filter_by(user_id=user_id, status='active')\
        .first()
    
    if existing_subscription:
        # Cancel existing subscription
        existing_subscription.status = 'cancelled'
    
    # Create new subscription
    expires_at = None
    if plan.billing_period == 'monthly':
        expires_at = datetime.utcnow() + timedelta(days=30)
    elif plan.billing_period == 'yearly':
        expires_at = datetime.utcnow() + timedelta(days=365)
    
    new_subscription = UserERPSubscription(
        user_id=user_id,
        plan_id=plan_id,
        status='active',
        started_at=datetime.utcnow(),
        expires_at=expires_at
    )
    
    db.session.add(new_subscription)
    
    # Activate modules for this plan
    # First, deactivate all previous modules
    db.session.query(UserERPModule)\
        .filter_by(user_id=user_id)\
        .delete()
    
    # Then activate new modules
    for module in plan.modules:
        user_module = UserERPModule(
            user_id=user_id,
            module_id=module.id,
            is_active=True,
            activated_at=datetime.utcnow()
        )
        db.session.add(user_module)
    
    db.session.commit()
    
    success_message = f'تم الاشتراك في خطة {plan.name_ar} بنجاح!' if lang == 'ar' else f'Successfully subscribed to {plan.name_en} plan!'
    flash(success_message, 'success')
    
    return jsonify({
        'success': True,
        'message': success_message,
        'redirect': url_for('erp.index')
    })


@erp_bp.route('/module/<slug>')
@jwt_required(locations=['cookies'])
def module_detail(slug):
    """Show ERP module details"""
    db = current_app.extensions['sqlalchemy']
    user_id_str = get_jwt_identity()
    if not user_id_str:
        flash('Please login to access this module', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = int(user_id_str)
    lang = session.get('language', 'ar')
    
    # Get the module
    module = db.session.query(ERPModule).filter_by(slug=slug, is_active=True).first()
    if not module:
        flash('الوحدة غير موجودة' if lang == 'ar' else 'Module not found', 'error')
        return redirect(url_for('erp.index'))
    
    # Check if user has access to this module
    user_subscription = db.session.query(UserERPSubscription)\
        .filter_by(user_id=user_id, status='active')\
        .first()
    
    has_access = False
    if user_subscription:
        module_ids = [m.id for m in user_subscription.plan.modules]
        has_access = module.id in module_ids
    
    if not has_access:
        message = 'الرجاء الاشتراك في خطة مناسبة لتفعيل هذه الوحدة' if lang == 'ar' else 'Please subscribe to a plan to access this module'
        flash(message, 'warning')
        return redirect(url_for('erp.index'))
    
    return render_template('erp/module_detail.html',
                         module=module,
                         lang=lang)


@erp_bp.route('/api/user-subscription')
@jwt_required(locations=['cookies'])
def get_user_subscription():
    """API endpoint to get user's current subscription"""
    db = current_app.extensions['sqlalchemy']
    user_id_str = get_jwt_identity()
    if not user_id_str:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    user_id = int(user_id_str)
    
    subscription = db.session.query(UserERPSubscription)\
        .filter_by(user_id=user_id, status='active')\
        .first()
    
    if not subscription:
        return jsonify({
            'success': True,
            'has_subscription': False,
            'plan': None,
            'modules': []
        })
    
    module_ids = [m.id for m in subscription.plan.modules]
    
    return jsonify({
        'success': True,
        'has_subscription': True,
        'plan': {
            'id': subscription.plan.id,
            'name': subscription.plan.name,
            'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None
        },
        'modules': module_ids
    })
