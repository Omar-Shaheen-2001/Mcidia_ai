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
    """API endpoint for fetching unread notifications as JSON - Admin Only"""
    from models import User
    db = get_db()
    
    try:
        # Check if user is admin
        current_user = db.session.query(User).get(session.get('user_id'))
        if not current_user or current_user.role != 'system_admin':
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403
        
        # Get only broadcast unread notifications (user_id is NULL and is_read is False)
        notifications = db.session.query(Notification).filter(
            Notification.user_id.is_(None),
            Notification.is_read == False
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

@notifications_admin_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read - Admin Only"""
    from models import User
    db = get_db()
    
    try:
        # Check if user is admin
        current_user = db.session.query(User).get(session.get('user_id'))
        if not current_user or current_user.role != 'system_admin':
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403
        
        notification = db.session.query(Notification).get(notification_id)
        if notification:
            notification.is_read = True
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            }), 200
        return jsonify({
            'success': False,
            'error': 'Notification not found'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_admin_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all broadcast notifications as read - Admin Only"""
    from models import User
    db = get_db()
    
    try:
        # Check if user is admin
        current_user = db.session.query(User).get(session.get('user_id'))
        if not current_user or current_user.role != 'system_admin':
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403
        
        db.session.query(Notification).filter(
            Notification.user_id.is_(None),
            Notification.is_read == False
        ).update({'is_read': True})
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'All notifications marked as read'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
