from flask import current_app, Blueprint, render_template, request, flash, session, redirect, url_for, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Transaction, SubscriptionPlan
import stripe
import os
import unicodedata
import requests
import base64
import json

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_API_URL = 'https://api.stripe.com/v1'

def stripe_create_customer(email, name):
    """Create Stripe customer using requests library with proper UTF-8 encoding"""
    api_key = os.getenv('STRIPE_SECRET_KEY')
    if not api_key:
        raise Exception("Stripe API key not configured")
    
    # Prepare data - use UTF-8 encoding which Stripe supports
    data = {
        'email': str(email)[:254] if email else '',
        'name': str(name)[:100] if name else ''
    }
    
    # Manually construct Authorization header with base64 using UTF-8
    # API key should always be ASCII, but encoding as UTF-8 is safe
    auth_str = base64.b64encode(f'{api_key}:'.encode('utf-8')).decode('ascii')
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
        'Authorization': f'Basic {auth_str}'
    }
    
    response = requests.post(
        f'{STRIPE_API_URL}/customers',
        data=data,
        headers=headers,
        timeout=10
    )
    
    if response.status_code != 200:
        raise Exception(f"Stripe API error: {response.text}")
    
    return response.json()

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/')
@login_required
def index():
    from flask import session as flask_session
    db = current_app.extensions['sqlalchemy']
    
    # Get user_id from JWT or Flask session fallback
    try:
        user_id = int(get_jwt_identity())
    except:
        user_id = flask_session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
    
    user = db.session.query(User).get(user_id)
    transactions = db.session.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).all()
    lang = session.get('language', 'ar')
    
    # Get subscription plan details
    plan_details = None
    plan_names = {
        'free': {'ar': 'مجاني', 'en': 'Free', 'price': 0, 'period': 'شهري / Monthly'},
        'monthly': {'ar': 'شهري', 'en': 'Monthly', 'price': 99, 'period': 'شهري / Monthly'},
        'yearly': {'ar': 'سنوي', 'en': 'Yearly', 'price': 999, 'period': 'سنوي / Yearly'},
        'pay_per_use': {'ar': 'حسب الاستخدام', 'en': 'Pay Per Use', 'price': 0, 'period': 'متغير / Variable'}
    }
    
    if user.plan_ref:
        plan_details = plan_names.get(user.plan_ref.name, {})
    
    return render_template('billing/index.html', 
                         user=user, 
                         transactions=transactions, 
                         lang=lang,
                         plan_details=plan_details)

@billing_bp.route('/pricing')
def pricing():
    from flask import session as flask_session
    db = current_app.extensions['sqlalchemy']
    lang = session.get('language', 'ar')
    
    # Get user if logged in
    user = None
    user_plan = None
    try:
        user_id = int(get_jwt_identity())
        user = db.session.query(User).get(user_id)
        if user and user.plan_ref:
            user_plan = user.plan_ref.name
    except:
        # Try Flask session fallback
        user_id = flask_session.get('user_id')
        if user_id:
            user = db.session.query(User).get(user_id)
            if user and user.plan_ref:
                user_plan = user.plan_ref.name
    
    return render_template('billing/pricing.html', 
                         lang=lang, 
                         user=user, 
                         user_plan=user_plan)

@billing_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.query(User).get(user_id)
    plan = request.form.get('plan')  # monthly, yearly, pay_per_use
    
    try:
        # Create Stripe customer if doesn't exist
        if not user.stripe_customer_id:
            # Use requests library for proper UTF-8 encoding
            customer = stripe_create_customer(
                email=str(user.email).lower() if user.email else f'user{user_id}@mcidia.app',
                name=f'User_{user_id}'
            )
            user.stripe_customer_id = customer.get('id')
            db.session.commit()
        
        # Define prices (in cents)
        prices = {
            'monthly': 9900,  # $99/month
            'yearly': 99900,  # $999/year
            'pay_per_use': 0  # Pay as you go
        }
        
        amount = prices.get(plan, 0)
        
        if amount > 0:
            # Create checkout session with sanitized data
            plan_name = 'Monthly' if plan == 'monthly' else ('Yearly' if plan == 'yearly' else 'PayPerUse')
            checkout_session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': amount,
                        'product_data': {
                            'name': f'Mcidia {plan_name} Plan',
                        },
                        'recurring': {
                            'interval': 'month' if plan == 'monthly' else 'year'
                        } if plan != 'pay_per_use' else None
                    },
                    'quantity': 1,
                }],
                mode='subscription' if plan != 'pay_per_use' else 'payment',
                success_url=request.host_url + f'billing/success?session_id={{CHECKOUT_SESSION_ID}}&plan={plan}',
                cancel_url=request.host_url + 'billing/pricing',
            )
            return redirect(checkout_session.url, code=303)
        else:
            # Pay per use - just update plan
            subscription_plan = db.session.query(SubscriptionPlan).filter_by(name=plan).first()
            if subscription_plan:
                user.subscription_plan_id = subscription_plan.id
            user.subscription_status = 'active'
            db.session.commit()
            flash('تم تفعيل خطة الدفع حسب الاستخدام / Pay-per-use plan activated', 'success')
            return redirect(url_for('dashboard.index'))
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'خطأ في الدفع / Payment error: {str(e)}', 'danger')
        return redirect(url_for('billing.pricing'))

@billing_bp.route('/success')
@login_required
def success():
    from datetime import datetime, timedelta
    
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.query(User).get(user_id)
    session_id = request.args.get('session_id')
    plan = request.args.get('plan', 'monthly')  # Get plan from URL parameter
    
    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Update user subscription and plan
        user.subscription_status = 'active'
        subscription_id = checkout_session.subscription if checkout_session.subscription else None
        user.stripe_subscription_id = subscription_id
        
        # Update the subscription plan in database
        subscription_plan = db.session.query(SubscriptionPlan).filter_by(name=plan).first()
        if subscription_plan:
            user.subscription_plan_id = subscription_plan.id
        
        # Get subscription details if available
        billing_period = 'one_time'
        subscription_start_date = datetime.utcnow()
        subscription_renewal_date = None
        payment_method_info = 'Card via Stripe'
        
        # If it's a subscription, get details from Stripe
        if subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                billing_period = subscription.get('billing_cycle_anchor')
                if subscription.get('billing_cycle_anchor'):
                    # Set renewal date based on interval
                    if subscription.get('items', {}).get('data', [{}])[0].get('billing_thresholds') or True:
                        interval = subscription.get('items', {}).get('data', [{}])[0].get('plan', {}).get('interval', 'month')
                        if interval == 'year':
                            subscription_renewal_date = subscription_start_date + timedelta(days=365)
                        else:
                            subscription_renewal_date = subscription_start_date + timedelta(days=30)
                    billing_period = interval
            except Exception as e:
                billing_period = 'monthly'
        
        # Create transaction record with comprehensive data
        transaction = Transaction(
            user_id=user_id,
            stripe_payment_id=checkout_session.payment_intent,
            stripe_subscription_id=subscription_id,
            stripe_invoice_url=checkout_session.get('invoice'),
            amount=checkout_session.amount_total / 100,
            currency='usd',
            description='Mcidia Plan Subscription',
            status='succeeded',
            transaction_type='subscription',
            payment_method=payment_method_info,
            billing_period=billing_period,
            subscription_start_date=subscription_start_date,
            subscription_renewal_date=subscription_renewal_date,
            tax_amount=0,
            discount_amount=0
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash('تم الاشتراك بنجاح! / Subscription successful!', 'success')
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'خطأ في التحقق من الدفع / Payment verification error', 'danger')
    
    return redirect(url_for('dashboard.index'))

@billing_bp.route('/receipt/<int:transaction_id>')
@login_required
def receipt(transaction_id):
    """Display receipt for a transaction"""
    from flask import session as flask_session
    db = current_app.extensions['sqlalchemy']
    
    # Get user_id from JWT or Flask session fallback
    try:
        user_id = int(get_jwt_identity())
    except:
        user_id = flask_session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
    
    user = db.session.query(User).get(user_id)
    transaction = db.session.query(Transaction).get(transaction_id)
    
    # Verify transaction belongs to user
    if not transaction or transaction.user_id != user_id:
        flash('Transaction not found', 'danger')
        return redirect(url_for('billing.index'))
    
    lang = session.get('language', 'ar')
    return render_template('billing/receipt.html', 
                         transaction=transaction, 
                         user=user, 
                         lang=lang)

@billing_bp.route('/receipt/<int:transaction_id>/download-pdf')
@login_required
def download_receipt_pdf(transaction_id):
    """Download receipt as PDF"""
    from flask import session as flask_session, send_file
    from weasyprint import HTML
    from io import BytesIO
    
    db = current_app.extensions['sqlalchemy']
    
    # Get user_id from JWT or Flask session fallback
    try:
        user_id = int(get_jwt_identity())
    except:
        user_id = flask_session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
    
    user = db.session.query(User).get(user_id)
    transaction = db.session.query(Transaction).get(transaction_id)
    
    # Verify transaction belongs to user
    if not transaction or transaction.user_id != user_id:
        flash('Transaction not found', 'danger')
        return redirect(url_for('billing.index'))
    
    lang = session.get('language', 'ar')
    is_ar = lang == 'ar'
    
    try:
        # Prepare data for template
        receipt_data = {
            'transaction': transaction,
            'user': user,
            'lang': lang,
            'is_ar': is_ar
        }
        
        # Render template to HTML string
        html_string = render_template('billing/receipt_pdf.html', **receipt_data)
        
        # Generate PDF from HTML
        pdf_bytes = HTML(string=html_string).write_pdf()
        
        # Create BytesIO object
        pdf_file = BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        # Create filename
        filename = f"receipt_{transaction.id}_{transaction.created_at.strftime('%Y%m%d')}.pdf"
        
        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'خطأ في توليد PDF / Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('billing.receipt', transaction_id=transaction_id))

@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET', '')
        )
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            # Handle successful payment
            pass
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            # Handle subscription renewal
            pass
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
