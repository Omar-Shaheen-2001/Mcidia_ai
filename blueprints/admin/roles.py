from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from models import Role
from flask import current_app

roles_bp = Blueprint('roles', __name__, url_prefix='/roles')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@roles_bp.route('/')
@login_required
@role_required('admin')
def index():
    """Manage roles and permissions"""
    db = get_db()
    lang = get_lang()
    
    roles = db.session.query(Role).all()
    
    return render_template('admin/roles/index.html', roles=roles, lang=lang)
