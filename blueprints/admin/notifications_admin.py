from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from models import Notification
from flask import current_app

notifications_admin_bp = Blueprint('notifications_admin', __name__, url_prefix='/notifications')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@notifications_admin_bp.route('/')
@login_required
@role_required('admin')
def index():
    """Notifications management"""
    db = get_db()
    lang = get_lang()
    
    notifications = db.session.query(Notification).order_by(Notification.created_at.desc()).all()
    
    return render_template('admin/notifications/index.html', notifications=notifications, lang=lang)
