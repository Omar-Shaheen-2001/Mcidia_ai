from flask import Blueprint, render_template, request, flash, session, redirect, url_for, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Transaction
from app import db
import stripe
import os

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/')
@login_required
def index():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).all()
    lang = session.get('language', 'ar')
    return render_template('billing/index.html', user=user, transactions=transactions, lang=lang)

@billing_bp.route('/pricing')
def pricing():
    lang = session.get('language', 'ar')
    return render_template('billing/pricing.html', lang=lang)

@billing_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    plan = request.form.get('plan')  # monthly, yearly, pay_per_use
    
    try:
        # Create Stripe customer if doesn't exist
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.username
            )
            user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Define prices (in cents)
        prices = {
            'monthly': 9900,  # $99/month
            'yearly': 99900,  # $999/year
            'pay_per_use': 0  # Pay as you go
        }
        
        amount = prices.get(plan, 0)
        
        if amount > 0:
            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': amount,
                        'product_data': {
                            'name': f'Mcidia {plan.capitalize()} Plan',
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
        flash(f'خطأ في الدفع / Payment error: {str(e)}', 'danger')
        return redirect(url_for('billing.pricing'))

@billing_bp.route('/success')
@login_required
def success():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
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
