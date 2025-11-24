from flask import Blueprint, render_template, session, jsonify, request, current_app
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required, role_required
from models import User, ChatSession, AILog
from sqlalchemy import func
from datetime import datetime

consultations_bp = Blueprint('consultations_admin', __name__, url_prefix='/consultations')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@consultations_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """Admin Consultations - View all user consultations"""
    db = get_db()
    lang = get_lang()
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Query consultations with user info and costs
    query = db.session.query(
        User.id,
        User.username,
        User.email,
        func.count(ChatSession.id).label('consultation_count'),
        func.sum(AILog.estimated_cost).label('total_cost')
    ).outerjoin(
        ChatSession, User.id == ChatSession.user_id
    ).outerjoin(
        AILog, (AILog.user_id == User.id) & (AILog.module == 'consultation')
    ).group_by(
        User.id, User.username, User.email
    ).order_by(
        func.count(ChatSession.id).desc()
    ).paginate(page=page, per_page=per_page)
    
    # Get overall statistics
    total_consultations = db.session.query(ChatSession).count()
    total_consultation_cost = db.session.query(func.sum(AILog.estimated_cost)).filter_by(module='consultation').scalar() or 0
    total_active_users = db.session.query(User).join(ChatSession).group_by(User.id).count()
    
    return render_template(
        'admin/consultations/index.html',
        lang=lang,
        users=query.items,
        pagination=query,
        total_consultations=total_consultations,
        total_consultation_cost=total_consultation_cost,
        total_active_users=total_active_users
    )

@consultations_bp.route('/user/<int:user_id>')
@login_required
@role_required('system_admin')
def user_consultations(user_id):
    """View consultations for a specific user"""
    db = get_db()
    lang = get_lang()
    
    user = db.session.query(User).get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get consultations for this user
    consultations = db.session.query(ChatSession).filter_by(
        user_id=user_id
    ).order_by(ChatSession.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get user statistics
    total_consultations = db.session.query(ChatSession).filter_by(user_id=user_id).count()
    total_cost = db.session.query(func.sum(AILog.estimated_cost)).filter_by(user_id=user_id, module='consultation').scalar() or 0
    
    # Distribute total cost equally among consultations
    if total_consultations > 0:
        avg_cost_per_consultation = total_cost / total_consultations
    else:
        avg_cost_per_consultation = 0
    
    # Create cost map - all sessions get equal share of AI costs
    cost_map = {consultation.id: avg_cost_per_consultation for consultation in consultations.items}
    
    return render_template(
        'admin/consultations/user_consultations.html',
        lang=lang,
        user=user,
        consultations=consultations.items,
        pagination=consultations,
        cost_map=cost_map,
        total_consultations=total_consultations,
        total_cost=total_cost
    )

@consultations_bp.route('/session/<int:session_id>')
@login_required
@role_required('system_admin')
def view_session(session_id):
    """View details of a specific consultation session"""
    db = get_db()
    lang = get_lang()
    
    session_obj = db.session.query(ChatSession).get(session_id)
    if not session_obj:
        return jsonify({'error': 'Session not found'}), 404
    
    user = db.session.query(User).get(session_obj.user_id)
    
    # Get total AI usage cost for this user's consultations
    user_consultation_cost = db.session.query(
        func.sum(AILog.estimated_cost)
    ).filter_by(user_id=session_obj.user_id, module='consultation').scalar() or 0
    
    # Get total consultations count
    total_consultations = db.session.query(ChatSession).filter_by(user_id=session_obj.user_id).count()
    
    # Distribute cost equally among this user's consultations
    if total_consultations > 0:
        session_cost = user_consultation_cost / total_consultations
    else:
        session_cost = 0
    
    # Get AI logs for this user's consultations
    ai_logs = db.session.query(AILog).filter_by(
        user_id=session_obj.user_id, 
        module='consultation'
    ).order_by(AILog.created_at.desc()).limit(10).all()
    
    return render_template(
        'admin/consultations/session_detail.html',
        lang=lang,
        session=session_obj,
        user=user,
        session_cost=session_cost,
        ai_logs=ai_logs
    )
