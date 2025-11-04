from flask import Blueprint

member_dashboard_bp = Blueprint('member_dashboard', __name__, url_prefix='/member')

# Import routes
from . import dashboard, modules, reports, knowledge
