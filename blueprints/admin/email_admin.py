"""
Email Administration Blueprint
Manage email settings, logs, and templates
"""
from flask import Blueprint, render_template, request, jsonify, g
from functools import wraps
from datetime import datetime
import os
import json

email_admin_bp = Blueprint('email_admin', __name__, url_prefix='/email')


def admin_required(f):
    """Require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models import User
        from flask import session, redirect, url_for, current_app
        
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        db = current_app.extensions.get('sqlalchemy')
        if not db:
            return redirect(url_for('auth.login'))
        
        user = db.session.query(User).get(user_id)
        if not user or not user.has_role('system_admin'):
            return redirect(url_for('dashboard.index'))
        
        g.user = user
        g.lang = session.get('lang', 'ar')
        return f(*args, **kwargs)
    return decorated_function


@email_admin_bp.route('/')
@admin_required
def index():
    """Email settings page"""
    from models import EmailSettings
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    settings = {s.setting_key: s.setting_value for s in db.session.query(EmailSettings).all()}
    
    sendgrid_configured = bool(os.getenv('SENDGRID_API_KEY'))
    sendgrid_from = os.getenv('SENDGRID_FROM_EMAIL', '')
    
    return render_template('admin/email/settings.html',
                         lang=g.lang,
                         settings=settings,
                         sendgrid_configured=sendgrid_configured,
                         sendgrid_from=sendgrid_from)


@email_admin_bp.route('/logs')
@admin_required
def logs():
    """Email logs page"""
    from models import EmailLog, User
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    email_type = request.args.get('type', '')
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = db.session.query(EmailLog)
    
    if email_type:
        query = query.filter(EmailLog.email_type == email_type)
    if status:
        query = query.filter(EmailLog.status == status)
    if search:
        query = query.filter(
            (EmailLog.to_email.ilike(f'%{search}%')) |
            (EmailLog.subject.ilike(f'%{search}%'))
        )
    
    logs = query.order_by(EmailLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    stats = {
        'total': db.session.query(EmailLog).count(),
        'sent': db.session.query(EmailLog).filter_by(status='sent').count(),
        'failed': db.session.query(EmailLog).filter_by(status='failed').count(),
        'pending': db.session.query(EmailLog).filter_by(status='pending').count()
    }
    
    return render_template('admin/email/logs.html',
                         lang=g.lang,
                         logs=logs,
                         stats=stats,
                         filters={'type': email_type, 'status': status, 'search': search})


@email_admin_bp.route('/templates')
@admin_required
def templates():
    """Email templates page"""
    from models import EmailTemplate
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    templates = db.session.query(EmailTemplate).order_by(EmailTemplate.template_key).all()
    
    return render_template('admin/email/templates.html',
                         lang=g.lang,
                         templates=templates)


@email_admin_bp.route('/templates/<int:template_id>')
@admin_required
def edit_template(template_id):
    """Edit email template page"""
    from models import EmailTemplate
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    template = db.session.query(EmailTemplate).get(template_id)
    if not template:
        from werkzeug.exceptions import NotFound
        raise NotFound()
    
    return render_template('admin/email/edit_template.html',
                         lang=g.lang,
                         template=template)


@email_admin_bp.route('/api/test-email', methods=['POST'])
@admin_required
def test_email():
    """Send test email to admin"""
    from utils.email_service import send_email
    
    to_email = g.user.email
    
    html_content = """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #667eea; text-align: center; }
            .success { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }
            .info { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0; }
            .footer { text-align: center; color: #888; font-size: 12px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 MCIDIA</h1>
            <div class="success">
                <h2 style="margin:0">✅ تم إرسال البريد بنجاح!</h2>
                <p style="margin:10px 0 0">Email Sent Successfully!</p>
            </div>
            <div class="info">
                <strong>📧 معلومات:</strong><br>
                البريد التجريبي يعمل بشكل صحيح<br>
                Test email is working correctly
            </div>
            <p style="text-align: center;">
                <strong>الوقت:</strong> """ + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC') + """
            </p>
            <div class="footer">
                MCIDIA Platform - منصة الاستشارات الذكية<br>
                © 2024 جميع الحقوق محفوظة
            </div>
        </div>
    </body>
    </html>
    """
    
    subject = "🧪 بريد تجريبي من MCIDIA | Test Email"
    
    success = send_email(to_email, subject, html_content, email_type='test', user_id=g.user.id)
    
    if success:
        return jsonify({
            'success': True,
            'message': f'تم إرسال البريد التجريبي إلى {to_email}',
            'message_en': f'Test email sent to {to_email}'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'فشل إرسال البريد، تحقق من الإعدادات',
            'message_en': 'Failed to send email, check settings'
        }), 500


@email_admin_bp.route('/api/check-config')
@admin_required
def check_config():
    """Check email configuration status"""
    from utils.email_service import get_email_provider
    
    provider = get_email_provider()
    
    config = {
        'provider': provider or 'none',
        'sendgrid': {
            'configured': bool(os.getenv('SENDGRID_API_KEY')),
            'api_key_length': len(os.getenv('SENDGRID_API_KEY', '')),
            'from_email': os.getenv('SENDGRID_FROM_EMAIL', 'Not set')
        },
        'resend': {
            'configured': bool(os.getenv('RESEND_API_KEY')),
            'from_email': os.getenv('RESEND_FROM_EMAIL', 'Not set')
        },
        'smtp': {
            'configured': bool(os.getenv('SMTP_HOST')),
            'host': os.getenv('SMTP_HOST', 'Not set'),
            'port': os.getenv('SMTP_PORT', 'Not set')
        }
    }
    
    return jsonify(config)


@email_admin_bp.route('/api/templates/<int:template_id>', methods=['PUT'])
@admin_required
def update_template(template_id):
    """Update email template"""
    from models import EmailTemplate
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    
    template = db.session.query(EmailTemplate).get(template_id)
    if not template:
        from werkzeug.exceptions import NotFound
        raise NotFound()
    
    data = request.json
    
    if 'subject_ar' in data:
        template.subject_ar = data['subject_ar']
    if 'subject_en' in data:
        template.subject_en = data['subject_en']
    if 'html_content' in data:
        template.html_content = data['html_content']
    if 'text_content' in data:
        template.text_content = data['text_content']
    if 'is_active' in data:
        template.is_active = data['is_active']
    
    template.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'تم تحديث القالب بنجاح',
        'message_en': 'Template updated successfully'
    })


@email_admin_bp.route('/api/templates/preview/<int:template_id>')
@admin_required
def preview_template(template_id):
    """Preview email template with sample data"""
    from models import EmailTemplate
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    template = db.session.query(EmailTemplate).get(template_id)
    if not template:
        from werkzeug.exceptions import NotFound
        raise NotFound()
    
    sample_data = {
        'user_name': 'أحمد محمد',
        'reset_link': 'https://mcidia.com/auth/reset-password/sample-token-123',
        'company_name': 'شركة النجاح',
        'email': 'ahmed@example.com'
    }
    
    html = template.html_content
    for key, value in sample_data.items():
        html = html.replace('{' + key + '}', value)
    
    return html


@email_admin_bp.route('/api/logs/<int:log_id>')
@admin_required
def get_log_details(log_id):
    """Get email log details"""
    from models import EmailLog
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    log = db.session.query(EmailLog).get(log_id)
    if not log:
        from werkzeug.exceptions import NotFound
        raise NotFound()
    
    return jsonify(log.to_dict())


@email_admin_bp.route('/api/stats')
@admin_required
def get_stats():
    """Get email statistics"""
    from models import EmailLog
    from flask import current_app
    from sqlalchemy import func
    from datetime import timedelta
    
    db = current_app.extensions.get('sqlalchemy')
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    
    daily_stats = db.session.query(
        func.date(EmailLog.created_at).label('date'),
        func.count(EmailLog.id).label('count'),
        EmailLog.status
    ).filter(
        EmailLog.created_at >= week_ago
    ).group_by(
        func.date(EmailLog.created_at),
        EmailLog.status
    ).all()
    
    type_stats = db.session.query(
        EmailLog.email_type,
        func.count(EmailLog.id).label('count')
    ).group_by(EmailLog.email_type).all()
    
    provider_stats = db.session.query(
        EmailLog.provider,
        func.count(EmailLog.id).label('count')
    ).group_by(EmailLog.provider).all()
    
    return jsonify({
        'daily': [{'date': str(s.date), 'count': s.count, 'status': s.status} for s in daily_stats],
        'by_type': [{'type': s.email_type, 'count': s.count} for s in type_stats],
        'by_provider': [{'provider': s.provider, 'count': s.count} for s in provider_stats]
    })


@email_admin_bp.route('/api/create-defaults', methods=['POST'])
@admin_required
def create_default_templates():
    """Create default email templates"""
    from models import EmailTemplate
    from flask import current_app
    
    db = current_app.extensions.get('sqlalchemy')
    
    default_templates = [
        {
            'template_key': 'password_reset',
            'name_ar': 'إعادة تعيين كلمة المرور',
            'name_en': 'Password Reset',
            'subject_ar': '🔐 إعادة تعيين كلمة المرور – MCIDIA',
            'subject_en': '🔐 Reset Your Password – MCIDIA',
            'variables': 'user_name,reset_link,email',
            'html_content': '''<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; }
        .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; text-align: center; }
        .content { padding: 30px; }
        .btn { display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; }
        .footer { padding: 20px; background: #f8f9fa; text-align: center; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 MCIDIA</h1>
            <p>إعادة تعيين كلمة المرور</p>
        </div>
        <div class="content">
            <p>مرحباً {user_name}،</p>
            <p>تلقينا طلب إعادة تعيين كلمة المرور لحسابك.</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" class="btn">إعادة تعيين كلمة المرور</a>
            </p>
            <p><strong>⏱️ هذا الرابط صالح لمدة ساعة واحدة فقط.</strong></p>
        </div>
        <div class="footer">
            © 2024 MCIDIA. جميع الحقوق محفوظة.
        </div>
    </div>
</body>
</html>'''
        },
        {
            'template_key': 'welcome',
            'name_ar': 'ترحيب بمستخدم جديد',
            'name_en': 'Welcome New User',
            'subject_ar': '🎉 مرحباً بك في MCIDIA!',
            'subject_en': '🎉 Welcome to MCIDIA!',
            'variables': 'user_name,email',
            'html_content': '''<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; }
        .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; text-align: center; }
        .content { padding: 30px; }
        .btn { display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; }
        .footer { padding: 20px; background: #f8f9fa; text-align: center; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 MCIDIA</h1>
            <p>مرحباً بك في منصتنا!</p>
        </div>
        <div class="content">
            <p>مرحباً {user_name}،</p>
            <p>نرحب بك في منصة MCIDIA للاستشارات الذكية!</p>
            <p>يمكنك الآن الوصول إلى جميع خدماتنا الاستشارية المتقدمة.</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="https://mcidia.com/dashboard" class="btn">ابدأ الآن</a>
            </p>
        </div>
        <div class="footer">
            © 2024 MCIDIA. جميع الحقوق محفوظة.
        </div>
    </div>
</body>
</html>'''
        }
    ]
    
    for tmpl_data in default_templates:
        existing = EmailTemplate.query.filter_by(template_key=tmpl_data['template_key']).first()
        if not existing:
            template = EmailTemplate(**tmpl_data)
            db.session.add(template)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'تم إنشاء القوالب الافتراضية',
        'message_en': 'Default templates created'
    })
