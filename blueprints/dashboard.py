from flask import Blueprint, render_template, session
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Project, AILog, Transaction
from app import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    user_id = get_jwt_identity()
    user = db.session.query(User).get(user_id)
    
    # Get statistics
    total_projects = db.session.query(Project).filter_by(user_id=user_id).count()
    active_projects = db.session.query(Project).filter_by(user_id=user_id, status='draft').count()
    ai_credits = user.ai_credits_used if user else 0
    
    # Get recent projects
    recent_projects = db.session.query(Project).filter_by(user_id=user_id).order_by(Project.updated_at.desc()).limit(5).all()
    
    # Get recent AI logs
    recent_ai_activity = db.session.query(AILog).filter_by(user_id=user_id).order_by(AILog.created_at.desc()).limit(5).all()
    
    lang = session.get('language', 'ar')
    
    return render_template('dashboard/index.html', 
                         user=user,
                         total_projects=total_projects,
                         active_projects=active_projects,
                         ai_credits=ai_credits,
                         recent_projects=recent_projects,
                         recent_ai_activity=recent_ai_activity,
                         lang=lang)
