"""
HR Module Blueprint
Comprehensive Human Resources Management System
"""

from flask import Blueprint

hr_module_bp = Blueprint('hr_module', __name__, url_prefix='/erp/hr')

# Import routes after blueprint creation to avoid circular imports
from . import routes
