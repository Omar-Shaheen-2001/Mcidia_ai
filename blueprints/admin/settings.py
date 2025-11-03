from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from models import SystemSettings
from flask import current_app

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@settings_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """System settings"""
    db = get_db()
    lang = get_lang()
    
    settings = db.session.query(SystemSettings).all()
    
    return render_template('admin/settings/index.html', settings=settings, lang=lang)
