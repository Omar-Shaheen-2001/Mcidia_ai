from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from models import SupportTicket
from flask import current_app

support_bp = Blueprint('support', __name__, url_prefix='/support')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@support_bp.route('/')
@login_required
@role_required('admin')
def index():
    """Support tickets"""
    db = get_db()
    lang = get_lang()
    
    tickets = db.session.query(SupportTicket).order_by(SupportTicket.created_at.desc()).all()
    
    return render_template('admin/support/index.html', tickets=tickets, lang=lang)
