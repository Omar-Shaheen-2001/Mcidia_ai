from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from models import Document
from flask import current_app

knowledge_admin_bp = Blueprint('knowledge_admin', __name__, url_prefix='/knowledge')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@knowledge_admin_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """Knowledge base management"""
    db = get_db()
    lang = get_lang()
    
    documents = db.session.query(Document).order_by(Document.uploaded_at.desc()).all()
    
    return render_template('admin/knowledge/index.html', documents=documents, lang=lang)
