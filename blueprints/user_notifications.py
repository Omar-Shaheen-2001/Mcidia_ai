from flask import Blueprint, render_template, session, jsonify
from utils.decorators import login_required
from models import Notification
from flask import current_app
from flask_jwt_extended import get_jwt_identity

user_notifications_bp = Blueprint('user_notifications', __name__, url_prefix='/user/notifications')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@user_notifications_bp.route('/')
@login_required
def index():
    """User notifications dashboard"""
    db = get_db()
    lang = get_lang()
    
    # Get user_id from JWT token or session
    user_id = None
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
    except:
        pass
    
    if not user_id:
        user_id = session.get('user_id')
    
    # Get user notifications (where user_id matches current user)
    notifications = db.session.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(100).all()
    
    # Calculate statistics
    total_notifications = db.session.query(Notification).filter_by(user_id=user_id).count()
    unread_notifications = db.session.query(Notification).filter_by(user_id=user_id, is_read=False).count()
    read_notifications = db.session.query(Notification).filter_by(user_id=user_id, is_read=True).count()
    
    return render_template(
        'user/notifications/index.html', 
        notifications=notifications,
        total_notifications=total_notifications,
        unread_notifications=unread_notifications,
        read_notifications=read_notifications,
        lang=lang
    )

@user_notifications_bp.route('/api', methods=['GET'])
@login_required
def api_notifications():
    """API endpoint for fetching unread user notifications as JSON"""
    db = get_db()
    
    # Get user_id from JWT token or session
    user_id = None
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
    except:
        pass
    
    # Fallback to session
    if not user_id:
        user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'User not authenticated'
        }), 401
    
    try:
        # Get unread notifications for current user
        notifications = db.session.query(Notification).filter(
            Notification.user_id == user_id,
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

@user_notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a user notification as read"""
    db = get_db()
    
    # Get user_id from JWT token or session
    user_id = None
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
    except:
        pass
    
    if not user_id:
        user_id = session.get('user_id')
    
    try:
        notification = db.session.query(Notification).filter_by(id=notification_id, user_id=user_id).first()
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

@user_notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all user notifications as read"""
    db = get_db()
    
    # Get user_id from JWT token or session
    user_id = None
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
    except:
        pass
    
    if not user_id:
        user_id = session.get('user_id')
    
    try:
        db.session.query(Notification).filter(
            Notification.user_id == user_id,
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
