from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from flask import current_app

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@reports_bp.route('/')
@login_required
@role_required('admin')
def index():
    """Reports and analytics"""
    db = get_db()
    lang = get_lang()
    
    return render_template('admin/reports/index.html', lang=lang)
