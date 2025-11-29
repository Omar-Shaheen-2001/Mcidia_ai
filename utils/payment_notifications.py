"""Payment notification utility for admin alerts on successful payments"""
from datetime import datetime
from flask import url_for


def create_payment_success_notification(db, user, transaction, app):
    """
    Create a notification for admin when payment succeeds
    
    Args:
        db: Database instance
        user: User object
        transaction: Transaction object
        app: Flask app instance
    """
    from models import Notification
    
    try:
        # Format payment date
        payment_date = transaction.created_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.created_at else 'N/A'
        
        # Determine subscription type
        subscription_type = user.plan_ref.name if user.plan_ref else 'Unknown'
        plan_names = {
            'free': 'مجاني / Free',
            'monthly': 'شهري / Monthly',
            'yearly': 'سنوي / Yearly',
            'pay_per_use': 'حسب الاستخدام / Pay Per Use'
        }
        subscription_type_display = plan_names.get(subscription_type, subscription_type)
        
        # Build notification title and message
        title = f'✅ دفع ناجح - Successful Payment'
        
        message = f"""
        <strong>اسم المستخدم / Username:</strong> {user.username}<br>
        <strong>البريد الإلكتروني / Email:</strong> {user.email}<br>
        <strong>رقم الحساب / User ID:</strong> #{user.id}<br>
        <strong>نوع الاشتراك / Subscription Type:</strong> {subscription_type_display}<br>
        <strong>رقم العملية / Transaction ID:</strong> {transaction.stripe_payment_id or transaction.id}<br>
        <strong>المبلغ / Amount:</strong> {transaction.amount} {transaction.currency.upper()}<br>
        <strong>تاريخ ووقت الدفع / Payment Date:</strong> {payment_date}<br>
        """
        
        # Add links
        with app.app_context():
            # Invoice link
            if transaction.stripe_invoice_url:
                message += f'<a href="{transaction.stripe_invoice_url}" target="_blank" class="btn btn-sm btn-link">📄 الفاتورة / Invoice</a><br>'
            
            # Stripe dashboard link
            if transaction.stripe_payment_id:
                stripe_url = f"https://dashboard.stripe.com/payments/{transaction.stripe_payment_id}"
                message += f'<a href="{stripe_url}" target="_blank" class="btn btn-sm btn-link">🔗 Stripe Dashboard</a><br>'
            
            # Admin user panel link
            user_admin_url = url_for('admin.users_admin.index', _external=False)
            message += f'<a href="{user_admin_url}?search={user.username}" target="_blank" class="btn btn-sm btn-link">👤 عرض المستخدم / View User</a>'
        
        # Create notification
        notification = Notification(
            title=title,
            message=message,
            notification_type='payment_success',
            status='active',
            is_read=False,
            user_id=None  # Broadcast to all admins
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    except Exception as e:
        print(f"Error creating payment notification: {str(e)}")
        db.session.rollback()
        return None
