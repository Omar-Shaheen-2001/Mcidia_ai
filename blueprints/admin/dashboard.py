from flask import Blueprint, render_template, session, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required, role_required
from models import User, Project, Transaction, AILog, Service, Role
from sqlalchemy import func
from datetime import datetime, timedelta
from flask import current_app

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@dashboard_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """Admin Dashboard - Main Overview"""
    db = get_db()
    lang = get_lang()
    
    # Get statistics
    total_users = db.session.query(User).count()
    total_projects = db.session.query(Project).count()
    total_revenue = db.session.query(func.sum(Transaction.amount)).filter_by(status='succeeded').scalar() or 0
    total_ai_usage = db.session.query(func.sum(User.ai_credits_used)).scalar() or 0
    
    # Get active users (logged in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = db.session.query(User).filter(User.last_login >= thirty_days_ago).count()
    
    # Get recent users
    recent_users = db.session.query(User).order_by(User.created_at.desc()).limit(10).all()
    
    # Get recent transactions
    recent_transactions = db.session.query(Transaction).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Get user role distribution
    role_distribution = db.session.query(
        Role.name, 
        func.count(User.id).label('count')
    ).join(User).group_by(Role.name).all()
    
    # Get monthly revenue (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_revenue = db.session.query(
        func.date_trunc('month', Transaction.created_at).label('month'),
        func.sum(Transaction.amount).label('revenue')
    ).filter(
        Transaction.status == 'succeeded',
        Transaction.created_at >= six_months_ago
    ).group_by('month').order_by('month').all()
    
    # Get AI usage by module (last 30 days)
    ai_by_module = db.session.query(
        AILog.module,
        func.count(AILog.id).label('count'),
        func.sum(AILog.tokens_used).label('tokens')
    ).filter(
        AILog.created_at >= thirty_days_ago
    ).group_by(AILog.module).all()
    
    # Get most used AI services (by service_type) - last 30 days
    most_used_services = db.session.query(
        AILog.service_type,
        func.count(AILog.id).label('count'),
        func.sum(AILog.estimated_cost).label('total_cost')
    ).filter(
        AILog.created_at >= thirty_days_ago,
        AILog.service_type != None
    ).group_by(AILog.service_type).order_by(func.count(AILog.id).desc()).limit(10).all()
    
    # Get top users by AI usage (last 30 days)
    top_ai_users = db.session.query(
        User.id,
        User.username,
        User.email,
        func.count(AILog.id).label('request_count'),
        func.sum(AILog.estimated_cost).label('total_cost')
    ).outerjoin(
        AILog, User.id == AILog.user_id
    ).filter(
        AILog.created_at >= thirty_days_ago
    ).group_by(User.id, User.username, User.email).order_by(
        func.count(AILog.id).desc()
    ).limit(10).all()
    
    return render_template(
        'admin/dashboard/index.html',
        lang=lang,
        total_users=total_users,
        active_users=active_users,
        total_projects=total_projects,
        total_revenue=total_revenue,
        total_ai_usage=total_ai_usage,
        recent_users=recent_users,
        recent_transactions=recent_transactions,
        role_distribution=role_distribution,
        monthly_revenue=monthly_revenue,
        ai_by_module=ai_by_module,
        most_used_services=most_used_services,
        top_ai_users=top_ai_users
    )

@dashboard_bp.route('/api/metrics')
@login_required
@role_required('system_admin')
def api_metrics():
    """API endpoint for dashboard metrics"""
    db = get_db()
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Daily new users (last 30 days)
    daily_users = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by('date').order_by('date').all()
    
    # Daily revenue (last 30 days)
    daily_revenue = db.session.query(
        func.date(Transaction.created_at).label('date'),
        func.sum(Transaction.amount).label('revenue')
    ).filter(
        Transaction.status == 'succeeded',
        Transaction.created_at >= thirty_days_ago
    ).group_by('date').order_by('date').all()
    
    # AI usage by day (last 30 days)
    daily_ai = db.session.query(
        func.date(AILog.created_at).label('date'),
        func.count(AILog.id).label('requests'),
        func.sum(AILog.tokens_used).label('tokens')
    ).filter(
        AILog.created_at >= thirty_days_ago
    ).group_by('date').order_by('date').all()
    
    return jsonify({
        'daily_users': [{'date': str(r.date), 'count': r.count} for r in daily_users],
        'daily_revenue': [{'date': str(r.date), 'revenue': float(r.revenue or 0)} for r in daily_revenue],
        'daily_ai': [{'date': str(r.date), 'requests': r.requests, 'tokens': r.tokens or 0} for r in daily_ai]
    })
