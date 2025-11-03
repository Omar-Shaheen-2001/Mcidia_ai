from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from models import AuditLog
from flask import current_app

logs_bp = Blueprint('logs', __name__, url_prefix='/logs')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@logs_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """Audit logs and security"""
    db = get_db()
    lang = get_lang()
    
    logs = db.session.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    
    return render_template('admin/logs/index.html', logs=logs, lang=lang)
