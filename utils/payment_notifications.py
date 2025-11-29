"""Payment notification utility for admin alerts on successful payments"""
from datetime import datetime
from flask import url_for
import json


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
        payment_date = transaction.created_at.strftime('%Y-%m-%d') if transaction.created_at else 'N/A'
        payment_time = transaction.created_at.strftime('%H:%M:%S') if transaction.created_at else 'N/A'
        
        # Determine subscription type
        subscription_type = user.plan_ref.name if user.plan_ref else 'Unknown'
        plan_names = {
            'free': 'مجاني / Free',
            'monthly': 'شهري / Monthly',
            'yearly': 'سنوي / Yearly',
            'pay_per_use': 'حسب الاستخدام / Pay Per Use'
        }
        subscription_type_display = plan_names.get(subscription_type, subscription_type)
        
        # Get renewal date
        renewal_date = transaction.subscription_renewal_date.strftime('%Y-%m-%d') if transaction.subscription_renewal_date else 'N/A'
        
        # Build notification title
        title = f'💳 دفع ناجح - Successful Payment'
        
        # Build detailed message with transaction details
        payment_details = {
            'user_name': user.username,
            'user_email': user.email,
            'organization': user.company_name or 'N/A',
            'plan': subscription_type_display,
            'amount': f'{transaction.amount} {transaction.currency.upper()}',
            'status': 'Succeeded',
            'transaction_id': transaction.stripe_payment_id or f'#{transaction.id}',
            'invoice_id': transaction.stripe_invoice_url or 'N/A',
            'payment_date': payment_date,
            'payment_time': payment_time,
            'payment_method': transaction.payment_method or 'Stripe Card',
            'renewal_date': renewal_date,
            'stripe_url': f"https://dashboard.stripe.com/payments/{transaction.stripe_payment_id}" if transaction.stripe_payment_id else None,
            'invoice_url': transaction.stripe_invoice_url,
            'user_url': f'/admin/users?search={user.username}'
        }
        
        # Create message with all details
        message = json.dumps(payment_details)
        
        # Create notification with type='payment' and status='sent'
        notification = Notification(
            title=title,
            message=message,
            notification_type='payment',
            status='sent',
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
