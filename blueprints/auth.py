from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, current_app
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, get_csrf_token
from models import User, Role, SubscriptionPlan

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
            access_token = create_access_token(identity=user.id)
            response = make_response(redirect(url_for('dashboard.index')))
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
    response = make_response(redirect(url_for('main.index')))
    unset_jwt_cookies(response)
    flash('تم تسجيل الخروج بنجاح / Logged out successfully', 'info')
    return response
