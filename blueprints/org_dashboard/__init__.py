from flask import Blueprint

# Create main organization dashboard blueprint
org_dashboard_bp = Blueprint('org_dashboard', __name__, url_prefix='/org')

# Import routes
from blueprints.org_dashboard import dashboard, team, knowledge, reports, billing, settings
