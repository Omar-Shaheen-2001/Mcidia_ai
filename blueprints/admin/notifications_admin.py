from flask import Blueprint, render_template, session, jsonify
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
@role_required('system_admin')
def index():
    """Notifications management"""
    db = get_db()
    lang = get_lang()
    
    # Get all notifications (both broadcast and system notifications), sorted by newest first
    all_notifications = db.session.query(Notification).order_by(Notification.created_at.desc()).limit(100).all()
    
    # Calculate statistics
    total_notifications = db.session.query(Notification).count()
    sent_notifications = db.session.query(Notification).filter_by(status='sent').count()
    pending_notifications = db.session.query(Notification).filter_by(status='pending').count()
    
    return render_template(
        'admin/notifications/index.html', 
        notifications=all_notifications,
        total_notifications=total_notifications,
        sent_notifications=sent_notifications,
        pending_notifications=pending_notifications,
        lang=lang
    )

@notifications_admin_bp.route('/api', methods=['GET'])
@login_required
def api_notifications():
    """API endpoint for fetching notifications as JSON"""
    db = get_db()
    
    try:
        # Get only broadcast notifications (user_id is NULL)
        notifications = db.session.query(Notification).filter(
            Notification.user_id.is_(None)
        ).order_by(Notification.created_at.desc()).limit(50).all()
        
        return jsonify({
            'success': True,
            'count': len(notifications),
            'data': [
                {
                    'id': n.id,
                    'title': n.title,
                    'message': n.message,
                    'notification_type': n.notification_type,
                    'status': n.status,
                    'is_read': n.is_read,
                    'created_at': n.created_at.isoformat() if n.created_at else None,
                    'user_id': n.user_id
                }
                for n in notifications
            ]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
