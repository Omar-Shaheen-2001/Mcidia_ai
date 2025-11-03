from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from models import Service, ServiceOffering
from flask import current_app

services_admin_bp = Blueprint('services_admin', __name__, url_prefix='/services')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@services_admin_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """Manage services and offerings"""
    db = get_db()
    lang = get_lang()
    
    services = db.session.query(Service).order_by(Service.display_order).all()
    
    return render_template('admin/services/index.html', services=services, lang=lang)
