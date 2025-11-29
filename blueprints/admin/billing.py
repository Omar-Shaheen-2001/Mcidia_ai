from flask import Blueprint, render_template, request, session, current_app
from utils.decorators import login_required, role_required
from models import Transaction, User
from utils.payment_notifications import create_payment_success_notification

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
    
    # Build plan name mapping
    plan_names = {
        'free': {'ar': 'مجاني', 'en': 'Free'},
        'monthly': {'ar': 'شهري', 'en': 'Monthly'},
        'yearly': {'ar': 'سنوي', 'en': 'Yearly'},
        'pay_per_use': {'ar': 'حسب الاستخدام', 'en': 'Pay Per Use'}
    }
    
    # Calculate stats
    total_transactions = len(transactions)
    successful_count = len([t for t in transactions if t.status == 'succeeded'])
    total_amount = sum([t.amount for t in transactions])
    unique_users = len(set([t.user_id for t in transactions]))
    
    # Build enriched transactions list with user and plan data
    enriched_transactions = []
    for trans in transactions:
        user = db.session.query(User).get(trans.user_id)
        plan_name = user.plan_ref.name if user and user.plan_ref else 'unknown'
        plan_display_name = plan_names.get(plan_name, {}).get('ar' if lang == 'ar' else 'en', plan_name)
        
        enriched_transactions.append({
            'transaction': trans,
            'user': user,
            'username': user.username if user else 'Unknown',
            'email': user.email if user else 'N/A',
            'plan_name': plan_display_name,
            'id': trans.id,
            'amount': trans.amount,
            'status': trans.status,
            'created_at': trans.created_at,
            'transaction_type': trans.transaction_type,
            'currency': trans.currency,
            'stripe_invoice_url': trans.stripe_invoice_url,
            'user_id': trans.user_id,
            'payment_method': trans.payment_method,
            'billing_period': trans.billing_period,
            'subscription_start_date': trans.subscription_start_date,
            'subscription_renewal_date': trans.subscription_renewal_date
        })
    
    # Collect payment methods
    payment_methods = {}
    for item in enriched_transactions:
        method = item.get('payment_method') or 'Unknown'
        payment_methods[method] = payment_methods.get(method, 0) + 1
    
    return render_template('admin/billing/index.html', 
                         enriched_transactions=enriched_transactions,
                         total_transactions=total_transactions,
                         successful_count=successful_count,
                         total_amount=total_amount,
                         unique_users=unique_users,
                         payment_methods=payment_methods,
                         lang=lang)


@billing_bp.route('/create-payment-notification/<int:transaction_id>', methods=['POST'])
@login_required
@role_required('system_admin')
def create_payment_notification(transaction_id):
    """Create a notification for a payment (admin endpoint for testing/manual triggering)"""
    db = get_db()
    
    try:
        transaction = db.session.query(Transaction).get(transaction_id)
        if not transaction:
            return {'success': False, 'error': 'Transaction not found'}, 404
        
        user = db.session.query(User).get(transaction.user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}, 404
        
        # Create notification
        notification = create_payment_success_notification(db, user, transaction, current_app)
        
        if notification:
            return {'success': True, 'message': 'Payment notification created', 'notification_id': notification.id}, 200
        else:
            return {'success': False, 'error': 'Failed to create notification'}, 500
    
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500
