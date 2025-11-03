from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from models import AILog
from flask import current_app
from sqlalchemy import func

ai_management_bp = Blueprint('ai_management', __name__, url_prefix='/ai')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@ai_management_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """AI management dashboard"""
    db = get_db()
    lang = get_lang()
    
    total_requests = db.session.query(func.count(AILog.id)).scalar() or 0
    total_tokens = db.session.query(func.sum(AILog.tokens_used)).scalar() or 0
    
    recent_logs = db.session.query(AILog).order_by(AILog.created_at.desc()).limit(50).all()
    
    return render_template('admin/ai/index.html', 
                         total_requests=total_requests,
                         total_tokens=total_tokens,
                         recent_logs=recent_logs,
                         lang=lang)
