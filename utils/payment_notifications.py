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


def create_account_deletion_notification(db, user, app):
    """
    Create a notification for admin when user deletes their account
    
    Args:
        db: Database instance
        user: User object that is being deleted
        app: Flask app instance
    """
    from models import Notification
    
    try:
        # Format deletion date and time
        deletion_date = datetime.now().strftime('%Y-%m-%d')
        deletion_time = datetime.now().strftime('%H:%M:%S')
        
        # Build notification title
        title = f'🗑️ تم حذف حساب - Account Deleted'
        
        # Build detailed message with user details
        deletion_details = {
            'user_id': user.id,
            'user_name': user.username,
            'user_email': user.email,
            'organization': user.company_name or 'N/A',
            'phone': user.phone or 'N/A',
            'subscription_plan': user.plan_ref.name if user.plan_ref else 'N/A',
            'created_date': user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A',
            'deletion_date': deletion_date,
            'deletion_time': deletion_time,
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
            'last_login_ip': user.last_login_ip or 'N/A',
            'last_login_device': user.last_login_device or 'N/A',
            'user_url': f'/admin/users?search={user.username}'
        }
        
        # Create message with all details
        message = json.dumps(deletion_details)
        
        # Create notification with type='account_deletion' and status='sent'
        notification = Notification(
            title=title,
            message=message,
            notification_type='account_deletion',
            status='sent',
            is_read=False,
            user_id=None  # Broadcast to all admins
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    except Exception as e:
        print(f"Error creating account deletion notification: {str(e)}")
        db.session.rollback()
        return None
