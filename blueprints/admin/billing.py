from flask import Blueprint, render_template, request, session
from utils.decorators import login_required, role_required
from models import Transaction, User
from flask import current_app

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@billing_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """List all transactions"""
    db = get_db()
    lang = get_lang()
    
    # Get filter parameters
    status_filter = request.args.get('status')
    type_filter = request.args.get('type')
    
    query = db.session.query(Transaction)
    
    if status_filter:
        query = query.filter(Transaction.status == status_filter)
    
    if type_filter:
        query = query.filter(Transaction.transaction_type == type_filter)
    
    transactions = query.order_by(Transaction.created_at.desc()).all()
    
    return render_template('admin/billing/index.html', transactions=transactions, lang=lang)
