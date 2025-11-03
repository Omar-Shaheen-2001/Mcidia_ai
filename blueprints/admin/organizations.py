from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from models import Organization
from flask import current_app

organizations_bp = Blueprint('organizations', __name__, url_prefix='/organizations')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@organizations_bp.route('/')
@login_required
@role_required('admin')
def index():
    """List all organizations"""
    db = get_db()
    lang = get_lang()
    
    organizations = db.session.query(Organization).order_by(Organization.created_at.desc()).all()
    
    return render_template('admin/organizations/index.html', organizations=organizations, lang=lang)
