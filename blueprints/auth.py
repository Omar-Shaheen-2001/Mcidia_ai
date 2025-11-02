from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, get_csrf_token
from models import User, Role, SubscriptionPlan
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        company_name = request.form.get('company_name', '')
        role_name = request.form.get('role', 'client')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل / Username already exists', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني مستخدم بالفعل / Email already registered', 'danger')
            return redirect(url_for('auth.register'))
        
        # Get role and default plan
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role.query.filter_by(name='client').first()
        
        free_plan = SubscriptionPlan.query.filter_by(name='free').first()
        
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
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)
            response = make_response(redirect(url_for('dashboard.index')))
            set_access_cookies(response, access_token)
            flash(f'مرحباً {user.username}! / Welcome {user.username}!', 'success')
            return response
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة / Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
    
    lang = session.get('language', 'ar')
    return render_template('auth/login.html', lang=lang)

@auth_bp.route('/logout')
def logout():
    response = make_response(redirect(url_for('main.index')))
    unset_jwt_cookies(response)
    flash('تم تسجيل الخروج بنجاح / Logged out successfully', 'info')
    return response
