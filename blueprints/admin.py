from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Project, Transaction, AILog, Document, Role
from app import db
from utils.decorators import login_required, role_required
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@role_required('admin')
def index():
    # Get statistics
    total_users = User.query.count()
    total_projects = Project.query.count()
    total_revenue = db.session.query(func.sum(Transaction.amount)).filter_by(status='succeeded').scalar() or 0
    total_ai_usage = db.session.query(func.sum(User.ai_credits_used)).scalar() or 0
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Get recent transactions
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    
    lang = session.get('language', 'ar')
    
    return render_template('admin/index.html', 
                         total_users=total_users,
                         total_projects=total_projects,
                         total_revenue=total_revenue,
                         total_ai_usage=total_ai_usage,
                         recent_users=recent_users,
                         recent_transactions=recent_transactions,
                         lang=lang)

@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    all_users = User.query.all()
    lang = session.get('language', 'ar')
    return render_template('admin/users.html', users=all_users, lang=lang)

@admin_bp.route('/user/<int:user_id>')
@login_required
@role_required('admin')
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    user_projects = Project.query.filter_by(user_id=user_id).all()
    user_transactions = Transaction.query.filter_by(user_id=user_id).all()
    user_ai_logs = AILog.query.filter_by(user_id=user_id).order_by(AILog.created_at.desc()).limit(20).all()
    
    lang = session.get('language', 'ar')
    
    return render_template('admin/user_detail.html',
                         user=user,
                         projects=user_projects,
                         transactions=user_transactions,
                         ai_logs=user_ai_logs,
                         lang=lang)

@admin_bp.route('/user/<int:user_id>/update-role', methods=['POST'])
@login_required
@role_required('admin')
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role_name = request.form.get('role')
    
    role = Role.query.filter_by(name=new_role_name).first()
    if role:
        user.role_id = role.id
        db.session.commit()
        flash(f'تم تحديث دور المستخدم بنجاح / User role updated successfully', 'success')
    else:
        flash('دور غير صالح / Invalid role', 'danger')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/transactions')
@login_required
@role_required('admin')
def transactions():
    all_transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
    lang = session.get('language', 'ar')
    return render_template('admin/transactions.html', transactions=all_transactions, lang=lang)

@admin_bp.route('/ai-logs')
@login_required
@role_required('admin')
def ai_logs():
    logs = AILog.query.order_by(AILog.created_at.desc()).limit(100).all()
    lang = session.get('language', 'ar')
    return render_template('admin/ai_logs.html', logs=logs, lang=lang)
