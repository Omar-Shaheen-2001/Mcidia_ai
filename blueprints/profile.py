from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_wtf.csrf import generate_csrf
from models import User
from utils.decorators import login_required
from datetime import datetime
import os

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    """Display user profile settings page"""
    db = current_app.extensions['sqlalchemy']
    user_id = get_jwt_identity()
    user = db.session.query(User).filter_by(id=int(user_id)).first()
    
    if not user:
        flash('المستخدم غير موجود / User not found', 'danger')
        return redirect(url_for('dashboard.index'))
    
    lang = session.get('language', 'ar')
    
    # Get user's subscription plan details (use plan_ref to get the full object)
    subscription_plan = user.plan_ref if user.plan_ref else None
    
    # Calculate AI usage percentage
    ai_usage_percentage = 0
    if subscription_plan and subscription_plan.ai_credits_limit:
        # Use ai_credits_used instead of ai_usage_current
        ai_usage_percentage = min((user.ai_credits_used / subscription_plan.ai_credits_limit) * 100, 100)
    
    # Generate fresh CSRF token
    csrf_token = generate_csrf()
    
    return render_template('profile/settings.html', 
                         user=user, 
                         lang=lang,
                         subscription_plan=subscription_plan,
                         ai_usage_percentage=ai_usage_percentage,
                         csrf_token=csrf_token)

@profile_bp.route('/update-personal-info', methods=['POST'])
@login_required
def update_personal_info():
    """Update user personal information"""
    db = current_app.extensions['sqlalchemy']
    user_id = get_jwt_identity()
    user = db.session.query(User).filter_by(id=int(user_id)).first()
    
    if not user:
        flash('المستخدم غير موجود / User not found', 'danger')
        return redirect(url_for('profile.settings'))
    
    try:
        # Update basic info
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        company_name = request.form.get('company_name')
        
        # Debug logging
        print(f"[DEBUG] Form data - phone: '{phone}', type: {type(phone)}")
        
        # Check if email is already taken by another user
        if email != user.email:
            existing_user = db.session.query(User).filter_by(email=email).first()
            if existing_user:
                flash('البريد الإلكتروني مستخدم بالفعل / Email already in use', 'danger')
                return redirect(url_for('profile.settings'))
        
        # Check if username is already taken by another user
        if username != user.username:
            existing_user = db.session.query(User).filter_by(username=username).first()
            if existing_user:
                flash('اسم المستخدم موجود بالفعل / Username already taken', 'danger')
                return redirect(url_for('profile.settings'))
        
        # Prepare values
        phone_value = phone.strip() if phone and phone.strip() else None
        company_name_value = company_name.strip() if company_name and company_name.strip() else None
        
        print(f"[DEBUG] User ID: {user.id}, Phone to save: '{phone_value}'")
        
        # Update using direct SQL update to ensure it persists
        db.session.query(User).filter_by(id=user.id).update({
            'username': username,
            'email': email,
            'phone': phone_value,
            'company_name': company_name_value
        })
        
        db.session.commit()
        
        # Verify the update worked
        updated_user = db.session.query(User).filter_by(id=user.id).first()
        print(f"[DEBUG] After commit - DB shows: username={updated_user.username}, phone={updated_user.phone}")
        
        flash('تم تحديث المعلومات الشخصية بنجاح / Personal information updated successfully', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء التحديث / Error updating information: {str(e)}', 'danger')
    
    return redirect(url_for('profile.settings'))

@profile_bp.route('/update-password', methods=['POST'])
@login_required
def update_password():
    """Update user password"""
    db = current_app.extensions['sqlalchemy']
    user_id = get_jwt_identity()
    user = db.session.query(User).filter_by(id=int(user_id)).first()
    
    if not user:
        flash('المستخدم غير موجود / User not found', 'danger')
        return redirect(url_for('profile.settings'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Verify current password
    if not user.check_password(current_password):
        flash('كلمة المرور الحالية غير صحيحة / Current password is incorrect', 'danger')
        return redirect(url_for('profile.settings'))
    
    # Check if new passwords match
    if new_password != confirm_password:
        flash('كلمات المرور الجديدة غير متطابقة / New passwords do not match', 'danger')
        return redirect(url_for('profile.settings'))
    
    # Check password strength (minimum 6 characters)
    if len(new_password) < 6:
        flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل / Password must be at least 6 characters', 'danger')
        return redirect(url_for('profile.settings'))
    
    try:
        user.set_password(new_password)
        db.session.commit()
        flash('تم تحديث كلمة المرور بنجاح / Password updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث كلمة المرور / Error updating password: {str(e)}', 'danger')
    
    return redirect(url_for('profile.settings'))

@profile_bp.route('/update-preferences', methods=['POST'])
@login_required
def update_preferences():
    """Update user preferences (language, timezone, notifications)"""
    db = current_app.extensions['sqlalchemy']
    user_id = get_jwt_identity()
    user = db.session.query(User).filter_by(id=int(user_id)).first()
    
    if not user:
        flash('المستخدم غير موجود / User not found', 'danger')
        return redirect(url_for('profile.settings'))
    
    try:
        # Update language preference
        language = request.form.get('language', 'ar')
        session['language'] = language
        
        # Update notification preferences
        email_notifications = request.form.get('email_notifications') == 'on'
        system_notifications = request.form.get('system_notifications') == 'on'
        
        # Note: These would be stored in user preferences table in production
        # For now, we'll flash success
        
        flash('تم تحديث التفضيلات بنجاح / Preferences updated successfully', 'success')
    
    except Exception as e:
        flash(f'حدث خطأ أثناء التحديث / Error updating preferences: {str(e)}', 'danger')
    
    return redirect(url_for('profile.settings'))

@profile_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account (soft delete)"""
    db = current_app.extensions['sqlalchemy']
    user_id = get_jwt_identity()
    user = db.session.query(User).filter_by(id=int(user_id)).first()
    
    if not user:
        flash('المستخدم غير موجود / User not found', 'danger')
        return redirect(url_for('profile.settings'))
    
    password_confirmation = request.form.get('password_confirmation')
    
    # Verify password before deletion
    if not user.check_password(password_confirmation):
        flash('كلمة المرور غير صحيحة / Password is incorrect', 'danger')
        return redirect(url_for('profile.settings'))
    
    try:
        # Soft delete - deactivate the account
        user.is_active = False
        db.session.commit()
        
        # Create admin notification about account deletion
        try:
            from utils.payment_notifications import create_account_deletion_notification
            create_account_deletion_notification(db, user, current_app)
        except Exception as e:
            print(f"Warning: Failed to create account deletion notification: {str(e)}")
        
        # Logout the user
        from flask import make_response
        from flask_jwt_extended import unset_jwt_cookies
        
        response = make_response(redirect(url_for('main.index')))
        unset_jwt_cookies(response)
        flash('تم حذف حسابك بنجاح / Account deleted successfully', 'info')
        return response
    
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الحساب / Error deleting account: {str(e)}', 'danger')
        return redirect(url_for('profile.settings'))
