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
        {'name': 'admin', 'description': 'System Administrator'},
        {'name': 'consultant', 'description': 'Professional Consultant'},
        {'name': 'company_user', 'description': 'Company User'},
        {'name': 'client', 'description': 'Individual Client'}
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
    app.config['JWT_SECRET_KEY'] = os.getenv('SESSION_SECRET', 'jwt-secret-key')
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Disable JWT CSRF, use Flask-WTF instead
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    
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
    
    # Make CSRF token available to all templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        # Generate CSRF token for forms (works for both authenticated and unauthenticated requests)
        return dict(csrf_token=generate_csrf())
    
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
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
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
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
    
    # Create tables and seed default data
    with app.app_context():
        db.create_all()
        seed_database()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
