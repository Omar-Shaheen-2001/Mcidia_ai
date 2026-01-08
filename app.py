import os
from datetime import timedelta
from flask import Flask, redirect, url_for, render_template, request, g
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
    
    # Handle Railway/Production Database URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        # Check for individual components if DATABASE_URL is missing
        pg_user = os.getenv('PGUSER')
        pg_pass = os.getenv('PGPASSWORD')
        pg_host = os.getenv('PGHOST')
        pg_port = os.getenv('PGPORT', '5432')
        pg_db = os.getenv('PGDATABASE')
        if pg_user and pg_pass and pg_host and pg_db:
            db_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    
    if db_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://')
    else:
        # Fallback for local development if everything else is missing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local.db'
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }
    app.config['JWT_SECRET_KEY'] = os.getenv('SESSION_SECRET', 'jwt-secret-key')
    app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
    app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Disable JWT CSRF, use Flask-WTF instead
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_COOKIE_DOMAIN'] = None  # Allow cookies across all subdomains
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)  # Keep tokens valid for 7 days
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Disable CSRF by default, enable manually where needed
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)
    CORS(app)
    
    # Add Jinja filters
    import json
    import markdown
    
    @app.template_filter('from_json')
    def from_json_filter(value):
        """Convert JSON string to Python object"""
        if not value:
            return []
        try:
            return json.loads(value) if isinstance(value, str) else value
        except:
            return []
    
    @app.template_filter('md_to_html')
    def md_to_html(value):
        """Convert Markdown to HTML"""
        if not value:
            return ""
        try:
            html = markdown.markdown(value, extensions=['tables', 'fenced_code', 'codehilite', 'nl2br'])
            return html
        except:
            return value
    
    # Enable CSRF only for form pages (HTML POST requests)
    # API endpoints are protected by JWT instead
    @app.before_request
    def apply_csrf_protection():
        """Only protect HTML forms from CSRF, not JSON API requests"""
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Skip CSRF for API endpoints and JSON requests
            if '/api' not in request.path and request.content_type != 'application/json':
                csrf.protect()
    
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
        from flask import current_app as app_instance
        
        # Try to get current user if logged in
        current_user = None
        try:
            verify_jwt_in_request(optional=True, locations=['cookies'])
            user_id = get_jwt_identity()
            if user_id:
                db_instance = app_instance.extensions['sqlalchemy']
                current_user = db_instance.session.get(User, int(user_id))
        except:
            pass
        
        # Pass csrf_token as the generated token value (not as a function)
        return dict(csrf_token=generate_csrf(), current_user=current_user)
    
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
    from blueprints.strategic_planning_ai import strategic_planning_bp
    from blueprints.strategic_identity import strategic_identity_bp
    from blueprints.erp import erp_bp
    from blueprints.hr_module import hr_module_bp
    from blueprints.admin.settings import settings_bp
    from blueprints.admin.notifications_admin import notifications_admin_bp
    from blueprints.knowledge_rag import knowledge_rag_bp
    from blueprints.user_notifications import user_notifications_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(profile_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(strategy_bp, url_prefix='/strategy')
    app.register_blueprint(strategic_planning_bp, url_prefix='/services/organizational-building/strategic-planning-kpis')
    app.register_blueprint(strategic_identity_bp, url_prefix='/services/organizational-building/strategic-identity')
    app.register_blueprint(hr_bp, url_prefix='/erp/hr')
    app.register_blueprint(finance_bp, url_prefix='/finance')
    app.register_blueprint(marketing_bp, url_prefix='/marketing')
    app.register_blueprint(knowledge_bp, url_prefix='/knowledge')
    app.register_blueprint(governance_bp, url_prefix='/governance')
    app.register_blueprint(innovation_bp, url_prefix='/innovation')
    app.register_blueprint(consultation_bp, url_prefix='/consultation')
    app.register_blueprint(knowledge_rag_bp, url_prefix='/api')
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(org_dashboard_bp)
    app.register_blueprint(member_dashboard_bp)
    app.register_blueprint(erp_bp)
    app.register_blueprint(hr_module_bp)
    app.register_blueprint(settings_bp, url_prefix='/admin/settings')
    app.register_blueprint(notifications_admin_bp, url_prefix='/admin')
    app.register_blueprint(user_notifications_bp)
    
    # Create tables and seed default data
    with app.app_context():
        # Step 1: Create all database tables
        print("\n📋 Creating database tables...")
        db.create_all()
        print("✅ Database tables created")
        
        # Step 2: Seed basic data (roles and subscription plans)
        print("\n📋 Seeding roles and subscription plans...")
        seed_database()
        print("✅ Basic data seeded")
        
        # Step 3: Auto-initialize production database if empty
        from models import User, Service
        user_count = db.session.query(User).count()
        service_count = db.session.query(Service).count()
        
        print(f"\n📊 Database Status: {user_count} users, {service_count} services")
        
        if user_count == 0 or service_count == 0:
            print("\n" + "=" * 70)
            print("🔍 FIRST TIME DEPLOYMENT DETECTED!")
            print("   Initializing production database...")
            print("=" * 70)
            
            try:
                from init_production_db import initialize_production_database
                success = initialize_production_database()
                
                if not success:
                    print("\n⚠️  WARNING: Automatic initialization failed!")
                    print("   Please run manually: python init_production_db.py")
                    print("=" * 70)
                    
            except Exception as e:
                print(f"\n❌ ERROR: Auto-initialization failed: {e}")
                print("\n📝 MANUAL SETUP REQUIRED:")
                print("   Run: python init_production_db.py")
                print("=" * 70)
                import traceback
                traceback.print_exc()
        else:
            print("✅ Database already initialized")
            print(f"   Users: {user_count}, Services: {service_count}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
