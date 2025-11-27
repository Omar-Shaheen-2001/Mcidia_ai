from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, current_app
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, get_csrf_token, get_jwt_identity, verify_jwt_in_request
from models import User, Role, SubscriptionPlan, PasswordResetToken, SecurityLog
from datetime import datetime, timedelta
import secrets
import hashlib

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get db from current app extensions
        db = current_app.extensions['sqlalchemy']
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        company_name = request.form.get('company_name', '')
        role_name = request.form.get('role', 'client')
        
        # Check if user exists
        if db.session.query(User).filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل / Username already exists', 'danger')
            return redirect(url_for('auth.register'))
        
        if db.session.query(User).filter_by(email=email).first():
            flash('البريد الإلكتروني مستخدم بالفعل / Email already registered', 'danger')
            return redirect(url_for('auth.register'))
        
        # Get role and default plan
        role = db.session.query(Role).filter_by(name=role_name).first()
        if not role:
            role = db.session.query(Role).filter_by(name='client').first()
        
        free_plan = db.session.query(SubscriptionPlan).filter_by(name='free').first()
        
        # Create new user
        user = User(
            username=username,
            email=email,
            company_name=company_name,
            role_id=role.id,
            subscription_plan_id=free_plan.id if free_plan else None,
            subscription_status='active'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('تم التسجيل بنجاح! يمكنك الآن تسجيل الدخول / Registration successful! You can now login', 'success')
        return redirect(url_for('auth.login'))
    
    lang = session.get('language', 'ar')
    return render_template('auth/register.html', lang=lang)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = current_app.extensions['sqlalchemy']
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = db.session.query(User).filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Check if account is active
            if not user.is_active:
                flash('تم تعطيل حسابك من قبل المسؤول. يرجى التواصل مع الدعم الفني / Your account has been deactivated by administrator. Please contact support', 'danger')
                return redirect(url_for('auth.login'))
            
            # Update last login time and online status
            from datetime import datetime
            user.last_login = datetime.utcnow()
            user.is_online = True
            db.session.commit()
            
            # Store user ID in Flask session as backup
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role
            
            # Create access token
            access_token = create_access_token(identity=str(user.id))
            
            # Check user's organization membership to determine where to redirect
            from models import OrganizationMembership
            membership = db.session.query(OrganizationMembership).filter_by(
                user_id=user.id,
                is_active=True
            ).first()
            
            # Determine redirect URL based on membership
            if membership:
                if membership.membership_role in ['owner', 'admin']:
                    # Organization admin/owner -> go to org dashboard
                    redirect_url = url_for('org_dashboard.index', org_id=membership.organization_id)
                elif membership.membership_role == 'member':
                    # Organization member -> go to member dashboard
                    redirect_url = url_for('member_dashboard.index', org_id=membership.organization_id)
                else:
                    # Fallback for unknown roles
                    redirect_url = url_for('dashboard.index')
            else:
                # No membership -> go to default dashboard
                redirect_url = url_for('dashboard.index')
            
            response = make_response(redirect(redirect_url))
            set_access_cookies(response, access_token)
            flash(f'مرحباً {user.username}! / Welcome {user.username}!', 'success')
            return response
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة / Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
    
    lang = session.get('language', 'ar')
    return render_template('auth/login.html', lang=lang)

@auth_bp.route('/logout')
def logout():
    # Update user's online status
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            db = current_app.extensions['sqlalchemy']
            user = db.session.query(User).get(int(user_id))
            if user:
                user.is_online = False
                db.session.commit()
    except Exception as e:
        # Log error but don't fail logout
        print(f"Error updating online status on logout: {e}")
    
    response = make_response(redirect(url_for('main.index')))
    unset_jwt_cookies(response)
    flash('تم تسجيل الخروج بنجاح / Logged out successfully', 'info')
    return response


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password request"""
    db = current_app.extensions['sqlalchemy']
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('يرجى إدخال البريد الإلكتروني / Please enter your email', 'warning')
            return redirect(url_for('auth.forgot_password'))
        
        # Find user by email
        user = db.session.query(User).filter_by(email=email).first()
        
        # Always show success message to prevent email enumeration
        success_message = 'إذا كان البريد مسجلاً لدينا، سيتم إرسال رابط إعادة التعيين / If this email is registered, a reset link will be sent'
        
        if user:
            # Generate secure token
            raw_token = secrets.token_urlsafe(48)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            
            # Invalidate previous unused tokens for this user
            db.session.query(PasswordResetToken).filter_by(
                user_id=user.id, 
                is_used=False
            ).update({'is_used': True})
            
            # Create new token (valid for 1 hour)
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token_hash,
                expires_at=datetime.utcnow() + timedelta(hours=1),
                ip_address=request.remote_addr
            )
            db.session.add(reset_token)
            
            # Log security event
            security_log = SecurityLog(
                user_id=user.id,
                action='password_reset_requested',
                description=f'Password reset requested for email: {email}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500],
                status='success'
            )
            db.session.add(security_log)
            db.session.commit()
            
            # Send reset email
            try:
                from utils.email_service import send_password_reset_email
                
                # Build reset URL with raw token
                reset_url = url_for('auth.reset_password', token=raw_token, _external=True)
                
                email_sent = send_password_reset_email(
                    to_email=user.email,
                    reset_link=reset_url,
                    user_name=user.username
                )
                
                if email_sent:
                    print(f"Password reset email sent to: {email}")
                else:
                    print(f"Failed to send password reset email to: {email}")
                    # For development, print the reset link
                    print(f"Reset link (dev): {reset_url}")
            except Exception as e:
                print(f"Email send error: {e}")
                # For development, print the reset link
                reset_url = url_for('auth.reset_password', token=raw_token, _external=True)
                print(f"Reset link (dev): {reset_url}")
        
        flash(success_message, 'success')
        return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/forgot-password.html', lang=lang)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    db = current_app.extensions['sqlalchemy']
    lang = session.get('language', 'ar')
    
    # Hash the token to compare with stored hash
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Find token in database
    reset_token = db.session.query(PasswordResetToken).filter_by(token=token_hash).first()
    
    # Check if token is valid
    token_valid = reset_token and reset_token.is_valid()
    
    if request.method == 'POST' and token_valid:
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate passwords
        if not password or len(password) < 8:
            flash('كلمة المرور يجب أن تكون 8 أحرف على الأقل / Password must be at least 8 characters', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة / Passwords do not match', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        # Get user and update password
        user = db.session.query(User).get(reset_token.user_id)
        
        if user:
            # Update password
            user.set_password(password)
            
            # Mark token as used
            reset_token.mark_as_used()
            
            # Invalidate all other reset tokens for this user
            db.session.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.id != reset_token.id
            ).update({'is_used': True})
            
            # Log security event for password reset
            security_log = SecurityLog(
                user_id=user.id,
                action='password_reset_completed',
                description=f'Password successfully reset for user: {user.username}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500],
                status='success'
            )
            db.session.add(security_log)
            
            # End all active sessions (logout user everywhere)
            user.is_online = False
            
            # Log session termination event
            session_log = SecurityLog(
                user_id=user.id,
                action='all_sessions_terminated',
                description=f'All sessions terminated after password reset for user: {user.username}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500],
                status='success'
            )
            db.session.add(session_log)
            
            db.session.commit()
            
            # Clear current Flask session completely
            session.clear()
            
            # Create response that clears JWT cookies
            flash('تمت إعادة تعيين كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول / Password reset successfully. You can now login', 'success')
            response = make_response(redirect(url_for('auth.login')))
            
            # Unset JWT cookies to invalidate any existing tokens
            unset_jwt_cookies(response)
            
            return response
        else:
            flash('حدث خطأ. يرجى المحاولة مرة أخرى / An error occurred. Please try again', 'danger')
            return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/reset-password.html', lang=lang, token_valid=token_valid, token=token)
