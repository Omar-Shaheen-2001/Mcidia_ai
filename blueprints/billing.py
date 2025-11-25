from flask import current_app, Blueprint, render_template, request, flash, session, redirect, url_for, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Transaction
import stripe
import os
import unicodedata
import requests
import base64
import json

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_API_URL = 'https://api.stripe.com/v1'

def stripe_create_customer(email, name):
    """Create Stripe customer using requests library for proper UTF-8 encoding"""
    api_key = os.getenv('STRIPE_SECRET_KEY')
    if not api_key:
        raise Exception("Stripe API key not configured")
    
    # Prepare data with ASCII-safe values
    data = {
        'email': email[:254] if email else '',
        'name': name[:100] if name else ''
    }
    
    # Use basic auth with UTF-8 encoding
    auth = (api_key, '')
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(
        f'{STRIPE_API_URL}/customers',
        auth=auth,
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
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.query(User).get(user_id)
    transactions = db.session.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).all()
    lang = session.get('language', 'ar')
    return render_template('billing/index.html', user=user, transactions=transactions, lang=lang)

@billing_bp.route('/pricing')
def pricing():
    db = current_app.extensions['sqlalchemy']
    lang = session.get('language', 'ar')
    return render_template('billing/pricing.html', lang=lang)

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
                success_url=request.host_url + 'billing/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.host_url + 'billing/pricing',
            )
            return redirect(checkout_session.url, code=303)
        else:
            # Pay per use - just update plan
            user.subscription_plan = plan
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
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.query(User).get(user_id)
    session_id = request.args.get('session_id')
    
    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Update user subscription
        user.subscription_status = 'active'
        user.stripe_subscription_id = checkout_session.subscription if checkout_session.subscription else None
        
        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            stripe_payment_id=checkout_session.payment_intent,
            amount=checkout_session.amount_total / 100,
            currency='usd',
            description=f'Subscription Payment',
            status='succeeded',
            transaction_type='subscription'
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash('تم الاشتراك بنجاح! / Subscription successful!', 'success')
    except Exception as e:
        flash(f'خطأ في التحقق من الدفع / Payment verification error', 'danger')
    
    return redirect(url_for('dashboard.index'))

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
