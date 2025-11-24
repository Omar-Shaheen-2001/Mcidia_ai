from flask import Blueprint, redirect, url_for

# Create main admin blueprint (url_prefix added in app.py registration)
admin_bp = Blueprint('admin', __name__)

# Admin root redirect to dashboard
@admin_bp.route('/')
def index():
    return redirect(url_for('admin.dashboard.index'))

# Import and register sub-blueprints
from .dashboard import dashboard_bp
from .users import users_bp
from .billing import billing_bp
from .services_admin import services_admin_bp
from .organizations import organizations_bp
from .roles import roles_bp
from .ai_management import ai_management_bp
from .knowledge_admin import knowledge_admin_bp
from .reports import reports_bp
from .notifications_admin import notifications_admin_bp
from .settings import settings_bp
from .logs import logs_bp
from .support import support_bp
from .projects import projects_bp
from .consultations_admin import consultations_bp

# Register sub-blueprints
admin_bp.register_blueprint(dashboard_bp)
admin_bp.register_blueprint(users_bp)
admin_bp.register_blueprint(billing_bp)
admin_bp.register_blueprint(services_admin_bp)
admin_bp.register_blueprint(organizations_bp)
admin_bp.register_blueprint(roles_bp)
admin_bp.register_blueprint(ai_management_bp)
admin_bp.register_blueprint(knowledge_admin_bp)
admin_bp.register_blueprint(reports_bp)
admin_bp.register_blueprint(notifications_admin_bp)
admin_bp.register_blueprint(settings_bp)
admin_bp.register_blueprint(logs_bp)
admin_bp.register_blueprint(support_bp)
admin_bp.register_blueprint(projects_bp)
admin_bp.register_blueprint(consultations_bp)
