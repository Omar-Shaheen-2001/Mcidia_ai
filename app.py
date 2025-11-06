import os
from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
csrf = CSRFProtect()

def seed_database():
    """Seed database with default roles and subscription plans"""
    from models import Role, SubscriptionPlan
    
    # Create default roles if they don't exist
    default_roles = [
        {'name': 'system_admin', 'description': 'Platform System Administrator - Full Access'},
        {'name': 'consultant', 'description': 'Professional Consultant'},
        {'name': 'company_user', 'description': 'Company User'},
        {'name': 'client', 'description': 'Individual Client'},
        {'name': 'external_user', 'description': 'External User - Organization Member'}
    ]
    
    for role_data in default_roles:
        existing = db.session.query(Role).filter_by(name=role_data['name']).first()
        if not existing:
            role = Role(**role_data)
            db.session.add(role)
    
    # Create default subscription plans if they don't exist
    default_plans = [
        {'name': 'free', 'price': 0, 'billing_period': 'monthly', 'ai_credits_limit': 1000},
        {'name': 'monthly', 'price': 99, 'billing_period': 'monthly', 'ai_credits_limit': 100000},
        {'name': 'yearly', 'price': 999, 'billing_period': 'yearly', 'ai_credits_limit': 1500000},
        {'name': 'pay_per_use', 'price': 0, 'billing_period': 'one_time', 'ai_credits_limit': None}
    ]
    
    for plan_data in default_plans:
        existing = db.session.query(SubscriptionPlan).filter_by(name=plan_data['name']).first()
        if not existing:
            plan = SubscriptionPlan(**plan_data)
            db.session.add(plan)
    
    db.session.commit()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }
    app.config['JWT_SECRET_KEY'] = os.getenv('SESSION_SECRET', 'jwt-secret-key')
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Disable JWT CSRF, use Flask-WTF instead
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'  # Important for cookie handling
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)
    CORS(app)
    
    # JWT error handlers for HTML pages
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return redirect(url_for('auth.login'))
    
    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return redirect(url_for('auth.login'))
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return redirect(url_for('auth.login'))
    
    # Make current user and CSRF token available to all templates
    @app.context_processor
    def inject_context():
        from flask_wtf.csrf import generate_csrf
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from models import User
        
        # Generate CSRF token for forms
        csrf_token = generate_csrf()
        
        # Try to get current user if logged in
        current_user = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                current_user = db.session.get(User, int(user_id))
        except:
            pass
        
        return dict(csrf_token=csrf_token, current_user=current_user)
    
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.profile import profile_bp
    from blueprints.strategy import strategy_bp
    from blueprints.hr import hr_bp
    from blueprints.finance import finance_bp
    from blueprints.marketing import marketing_bp
    from blueprints.knowledge import knowledge_bp
    from blueprints.governance import governance_bp
    from blueprints.innovation import innovation_bp
    from blueprints.consultation import consultation_bp
    from blueprints.billing import billing_bp
    from blueprints.admin import admin_bp
    from blueprints.main import main_bp
    from blueprints.services_bp import services_bp
    from blueprints.org_dashboard import org_dashboard_bp
    from blueprints.member_dashboard import member_dashboard_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(profile_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(strategy_bp, url_prefix='/strategy')
    app.register_blueprint(hr_bp, url_prefix='/hr')
    app.register_blueprint(finance_bp, url_prefix='/finance')
    app.register_blueprint(marketing_bp, url_prefix='/marketing')
    app.register_blueprint(knowledge_bp, url_prefix='/knowledge')
    app.register_blueprint(governance_bp, url_prefix='/governance')
    app.register_blueprint(innovation_bp, url_prefix='/innovation')
    app.register_blueprint(consultation_bp, url_prefix='/consultation')
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(org_dashboard_bp)
    app.register_blueprint(member_dashboard_bp)
    
    # Create tables and seed default data
    with app.app_context():
        db.create_all()
        seed_database()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
