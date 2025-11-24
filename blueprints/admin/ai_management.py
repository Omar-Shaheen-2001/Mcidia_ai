from flask import Blueprint, render_template, session, request, jsonify
from utils.decorators import login_required, role_required
from models import AILog, User, Organization
from flask import current_app
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

ai_management_bp = Blueprint('ai_management', __name__, url_prefix='/ai')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@ai_management_bp.route('/')
@login_required
@role_required('system_admin', 'org_admin')
def index():
    """AI logs management dashboard"""
    db = get_db()
    lang = get_lang()
    
    # Get filter parameters
    user_id = request.args.get('user_id', type=int)
    org_id = request.args.get('org_id', type=int)
    service_type = request.args.get('service_type', '')
    provider_type = request.args.get('provider_type', '')
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Build query
    query = db.session.query(AILog)
    
    # Apply filters
    if user_id:
        query = query.filter(AILog.user_id == user_id)
    
    if org_id:
        query = query.filter(AILog.organization_id == org_id)
    
    if service_type:
        query = query.filter(AILog.service_type == service_type)
    
    if provider_type:
        query = query.filter(AILog.provider_type == provider_type)
    
    if status:
        query = query.filter(AILog.status == status)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AILog.created_at >= from_date)
        except:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AILog.created_at < to_date)
        except:
            pass
    
    if search:
        search = f"%{search}%"
        query = query.filter(
            or_(
                AILog.prompt.ilike(search),
                AILog.response.ilike(search),
                AILog.error_message.ilike(search)
            )
        )
    
    # Get total count for pagination
    total_count = query.count()
    
    # Order by most recent and paginate
    logs = query.order_by(AILog.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # Calculate statistics
    total_requests = db.session.query(func.count(AILog.id)).scalar() or 0
    total_tokens = db.session.query(func.sum(AILog.tokens_used)).filter(AILog.tokens_used > 0).scalar() or 0
    total_cost = db.session.query(func.sum(AILog.estimated_cost)).filter(AILog.estimated_cost > 0).scalar() or 0
    success_count = db.session.query(func.count(AILog.id)).filter(AILog.status == 'success').scalar() or 0
    failed_count = db.session.query(func.count(AILog.id)).filter(AILog.status == 'failed').scalar() or 0
    
    # Get unique service types and providers for filters
    service_types = db.session.query(func.distinct(AILog.service_type)).filter(AILog.service_type != None).all()
    providers = db.session.query(func.distinct(AILog.provider_type)).filter(AILog.provider_type != None).all()
    
    # Get users and organizations for dropdowns
    users = db.session.query(User).all()
    organizations = db.session.query(Organization).all()
    
    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template('admin/ai/index.html',
                         logs=logs,
                         total_requests=total_requests,
                         total_tokens=total_tokens,
                         total_cost=total_cost,
                         success_count=success_count,
                         failed_count=failed_count,
                         service_types=service_types,
                         providers=providers,
                         users=users,
                         organizations=organizations,
                         current_page=page,
                         total_pages=total_pages,
                         total_count=total_count,
                         per_page=per_page,
                         filters={
                             'user_id': user_id,
                             'org_id': org_id,
                             'service_type': service_type,
                             'provider_type': provider_type,
                             'status': status,
                             'date_from': date_from,
                             'date_to': date_to,
                             'search': search
                         },
                         lang=lang)

@ai_management_bp.route('/log/<int:log_id>')
@login_required
@role_required('system_admin', 'org_admin')
def view_log(log_id):
    """View detailed AI log"""
    db = get_db()
    lang = get_lang()
    
    log = db.session.query(AILog).filter(AILog.id == log_id).first()
    if not log:
        return render_template('errors/404.html'), 404
    
    return render_template('admin/ai/detail.html', log=log, lang=lang)

@ai_management_bp.route('/api/stats')
@login_required
@role_required('system_admin', 'org_admin')
def api_stats():
    """Get AI statistics API"""
    db = get_db()
    
    # Last 30 days stats
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Daily stats
    daily_stats = db.session.query(
        func.date(AILog.created_at).label('date'),
        func.count(AILog.id).label('count'),
        func.sum(AILog.estimated_cost).label('cost')
    ).filter(AILog.created_at >= thirty_days_ago).group_by(
        func.date(AILog.created_at)
    ).order_by(func.date(AILog.created_at)).all()
    
    # Provider breakdown
    provider_breakdown = db.session.query(
        AILog.provider_type,
        func.count(AILog.id).label('count'),
        func.sum(AILog.estimated_cost).label('cost')
    ).group_by(AILog.provider_type).all()
    
    # Service type breakdown
    service_breakdown = db.session.query(
        AILog.service_type,
        func.count(AILog.id).label('count'),
        func.sum(AILog.estimated_cost).label('cost')
    ).group_by(AILog.service_type).all()
    
    return jsonify({
        'daily_stats': [
            {
                'date': str(stat[0]),
                'count': stat[1],
                'cost': float(stat[2] or 0)
            } for stat in daily_stats
        ],
        'provider_breakdown': [
            {
                'provider': stat[0],
                'count': stat[1],
                'cost': float(stat[2] or 0)
            } for stat in provider_breakdown
        ],
        'service_breakdown': [
            {
                'service': stat[0],
                'count': stat[1],
                'cost': float(stat[2] or 0)
            } for stat in service_breakdown
        ]
    })
