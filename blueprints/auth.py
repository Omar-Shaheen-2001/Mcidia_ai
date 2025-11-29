from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, current_app
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, get_csrf_token, get_jwt_identity, verify_jwt_in_request
from models import User, Role, SubscriptionPlan, PasswordResetToken, SecurityLog, Notification
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
        
        # Create notification for admins about new user registration
        admin_notification = Notification(
            user_id=None,  # Broadcast to all admins
            title='مستخدم جديد مسجل / New User Registration',
            message=f'مستخدم جديد "{user.username}" ({user.email}) قام بالتسجيل في المنصة / A new user "{user.username}" ({user.email}) has registered on the platform',
            notification_type='internal',
            status='sent',
            is_read=False
        )
        db.session.add(admin_notification)
        db.session.commit()
        
        flash('تم التسجيل بنجاح! يمكنك الآن تسجيل الدخول / Registration successful! You can now login', 'success')
        return redirect(url_for('auth.login'))
    
    lang = session.get('language', 'ar')
    return render_template('auth/register.html', lang=lang)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    from datetime import timedelta
    from user_agents import parse
    
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
            
            # Update last login time, IP address, device, and online status
            
            user.last_login = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            user.is_online = True
            
            # Detect device type from User-Agent
            user_agent = request.headers.get('User-Agent', '')
            ua = parse(user_agent)
            device_type = ua.device.family or 'Unknown'
            if not device_type or device_type == 'Other':
                if 'Mobile' in user_agent or 'Android' in user_agent:
                    device_type = 'Mobile'
                elif 'iPad' in user_agent or 'Tablet' in user_agent:
                    device_type = 'Tablet'
                elif 'Windows' in user_agent:
                    device_type = 'Windows PC'
                elif 'Macintosh' in user_agent:
                    device_type = 'MacOS'
                elif 'Linux' in user_agent:
                    device_type = 'Linux'
                else:
                    device_type = 'Desktop'
            user.last_login_device = device_type
            db.session.commit()
            
            # Create login notification
            import json
            login_notification_data = {
                'login_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'ip_address': request.remote_addr,
                'device': device_type,
                'user_name': user.username,
                'user_email': user.email,
                'browser': ua.browser.family if ua.browser.family else 'Unknown',
                'os': ua.os.family if ua.os.family else 'Unknown'
            }
            
            # Only create login notification for the user if they are Admin
            # Admin sees it as a broadcast notification (user_id=NULL)
            # Regular users don't see login notifications of other users
            if user.role == 'system_admin':
                login_notification = Notification(
                    user_id=None,  # Broadcast to all admins
                    title='✅ Admin تم تسجيل الدخول / Admin Login Successful',
                    message=json.dumps(login_notification_data),
                    notification_type='login',
                    status='sent',
                    is_read=False
                )
                db.session.add(login_notification)
                db.session.commit()
            
            # Store user ID in Flask session as backup
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role
            
            # Create access token
            access_token = create_access_token(identity=str(user.id))
            
            # Check user's organization membership to determine where to redirect
            try:
                from models import OrganizationMembership
            except:
                OrganizationMembership = None
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
            # Log failed login attempt
            failed_login_log = SecurityLog(
                user_id=user.id if user else None,
                action='failed_login_attempt',
                description=f'Failed login attempt for email: {email}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500],
                status='failed'
            )
            db.session.add(failed_login_log)
            db.session.commit()
            
            # Check for multiple failed attempts from the same user in the last 30 minutes
            thirty_min_ago = datetime.utcnow() - timedelta(minutes=30)
            failed_attempts = db.session.query(SecurityLog).filter(
                SecurityLog.action == 'failed_login_attempt',
                SecurityLog.description.contains(email),
                SecurityLog.created_at >= thirty_min_ago,
                SecurityLog.status == 'failed'
            ).count()
            
            # Create notification if 3 or more failed attempts
            if failed_attempts >= 3:
                # Check if we already created a notification for this in the last 10 minutes
                recent_notification = db.session.query(Notification).filter(
                    Notification.message.contains(email),
                    Notification.message.contains('محاولات دخول فاشلة') | Notification.message.contains('failed login'),
                    Notification.created_at >= datetime.utcnow() - timedelta(minutes=10)
                ).first()
                
                if not recent_notification:
                    admin_notification = Notification(
                        user_id=None,  # Broadcast to all admins
                        title='محاولات دخول فاشلة متعددة / Multiple Failed Login Attempts',
                        message=f'تم اكتشاف {failed_attempts} محاولات دخول فاشلة للبريد: {email} خلال آخر 30 دقيقة / {failed_attempts} failed login attempts detected for email: {email} in the last 30 minutes. IP Address: {request.remote_addr}',
                        notification_type='internal',
                        status='sent',
                        is_read=False
                    )
                    db.session.add(admin_notification)
                    db.session.commit()
            
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
                    user_name=user.username,
                    user_id=user.id
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


@auth_bp.route('/dev/reset-links', methods=['GET'])
def dev_reset_links():
    """Development endpoint to view pending password reset links"""
    import os
    import json
    from flask import jsonify
    
    # Only available in development
    if not current_app.debug:
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        link_file = os.path.join(os.path.dirname(current_app.root_path), 'data/dev_reset_links.json')
        if os.path.exists(link_file):
            with open(link_file, 'r', encoding='utf-8') as f:
                links = json.load(f)
            
            return jsonify({
                'message': 'Development mode: password reset links',
                'note': 'Click on reset_link to reset password',
                'links': links,
                'total': len(links)
            })
        else:
            return jsonify({
                'message': 'No password reset requests yet',
                'links': [],
                'total': 0
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/dev/check-email-config', methods=['GET'])
def dev_check_email_config():
    """Development endpoint to check email configuration"""
    import os
    from flask import jsonify
    
    if not current_app.debug:
        return jsonify({'error': 'Not available in production'}), 403
    
    sendgrid_key = os.getenv('SENDGRID_API_KEY')
    sendgrid_from = os.getenv('SENDGRID_FROM_EMAIL')
    
    return jsonify({
        'sendgrid_configured': bool(sendgrid_key),
        'sendgrid_key_length': len(sendgrid_key) if sendgrid_key else 0,
        'sendgrid_from_email': sendgrid_from or 'NOT SET',
        'email_provider': 'SendGrid' if sendgrid_key else 'Development mode'
    })


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
