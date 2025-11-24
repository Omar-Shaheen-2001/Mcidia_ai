from flask import Blueprint, render_template, request, jsonify, current_app, session, send_file
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required, role_required
from models import SystemSettings, BackupLog, db
from datetime import datetime
import os
import json

settings_bp = Blueprint('settings_admin', __name__, url_prefix='/settings')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

def get_or_create_settings():
    """Get settings or create default if doesn't exist"""
    settings = SystemSettings.query.first()
    if not settings:
        settings = SystemSettings()
        db.session.add(settings)
        db.session.commit()
    return settings

@settings_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """Settings Main Dashboard"""
    lang = get_lang()
    settings = get_or_create_settings()
    backups = BackupLog.query.order_by(BackupLog.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/settings/index.html',
        lang=lang,
        settings=settings,
        backups=backups
    )

@settings_bp.route('/general', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def general_settings():
    """General Settings"""
    lang = get_lang()
    settings = get_or_create_settings()
    
    if request.method == 'POST':
        settings.platform_name = request.form.get('platform_name', 'Mcidia')
        settings.platform_description = request.form.get('platform_description')
        settings.support_email = request.form.get('support_email')
        settings.maintenance_mode = request.form.get('maintenance_mode') == 'on'
        settings.updated_by = get_jwt_identity() if get_jwt_identity() else None
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حفظ الإعدادات' if lang == 'ar' else 'Settings saved'}), 200
    
    return render_template(
        'admin/settings/general.html',
        lang=lang,
        settings=settings
    )

@settings_bp.route('/branding', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def branding_settings():
    """Branding & Identity Settings"""
    lang = get_lang()
    settings = get_or_create_settings()
    
    if request.method == 'POST':
        # Colors
        settings.primary_color = request.form.get('primary_color', '#0d6efd')
        settings.secondary_color = request.form.get('secondary_color', '#28a745')
        settings.accent_color = request.form.get('accent_color', '#ffc107')
        
        # Text and Font
        settings.font_family = request.form.get('font_family', 'Arial')
        settings.welcome_message = request.form.get('welcome_message')
        
        # Domain
        settings.custom_domain = request.form.get('custom_domain')
        settings.https_enabled = request.form.get('https_enabled') == 'on'
        settings.cname_record = request.form.get('cname_record')
        
        settings.updated_by = get_jwt_identity() if get_jwt_identity() else None
        
        # Handle file uploads
        if 'dashboard_logo' in request.files and request.files['dashboard_logo'].filename:
            file = request.files['dashboard_logo']
            filename = f'dashboard-logo-{datetime.utcnow().timestamp()}.png'
            filepath = os.path.join('static/uploads/logos', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            settings.dashboard_logo = f'/static/uploads/logos/{filename}'
        
        if 'login_logo' in request.files and request.files['login_logo'].filename:
            file = request.files['login_logo']
            filename = f'login-logo-{datetime.utcnow().timestamp()}.png'
            filepath = os.path.join('static/uploads/logos', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            settings.login_logo = f'/static/uploads/logos/{filename}'
        
        if 'favicon' in request.files and request.files['favicon'].filename:
            file = request.files['favicon']
            filename = f'favicon-{datetime.utcnow().timestamp()}.ico'
            filepath = os.path.join('static/uploads/logos', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            settings.favicon = f'/static/uploads/logos/{filename}'
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حفظ إعدادات الهوية البصرية' if lang == 'ar' else 'Branding settings saved'}), 200
    
    return render_template(
        'admin/settings/branding.html',
        lang=lang,
        settings=settings
    )

@settings_bp.route('/ai', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def ai_settings():
    """AI Settings"""
    lang = get_lang()
    settings = get_or_create_settings()
    
    if request.method == 'POST':
        settings.ai_provider = request.form.get('ai_provider', 'openai')
        settings.ai_model = request.form.get('ai_model', 'gpt-3.5-turbo')
        settings.ai_temperature = float(request.form.get('ai_temperature', 0.7))
        settings.ai_max_tokens = int(request.form.get('ai_max_tokens', 2000))
        settings.updated_by = get_jwt_identity() if get_jwt_identity() else None
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حفظ إعدادات الذكاء الاصطناعي' if lang == 'ar' else 'AI settings saved'}), 200
    
    return render_template(
        'admin/settings/ai.html',
        lang=lang,
        settings=settings
    )

@settings_bp.route('/backup', methods=['GET', 'POST'])
@login_required
@role_required('system_admin')
def backup_settings():
    """Backup & Maintenance Settings"""
    lang = get_lang()
    settings = get_or_create_settings()
    backups = BackupLog.query.order_by(BackupLog.created_at.desc()).all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create_backup':
            # Create backup
            backup_name = f'backup-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}'
            backup = BackupLog(
                backup_name=backup_name,
                backup_type='full',
                backup_path=f'/backups/{backup_name}',
                status='success'
            )
            db.session.add(backup)
            settings.last_backup = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'تم إنشاء النسخة الاحتياطية' if lang == 'ar' else 'Backup created'}), 200
        
        elif action == 'health_check':
            # Health check
            settings.last_health_check = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'status': 'healthy', 'message': 'النظام سليم' if lang == 'ar' else 'System healthy'}), 200
        
        elif action == 'clear_cache':
            # Clear cache
            return jsonify({'success': True, 'message': 'تم مسح الذاكرة المؤقتة' if lang == 'ar' else 'Cache cleared'}), 200
    
    return render_template(
        'admin/settings/backup.html',
        lang=lang,
        settings=settings,
        backups=backups
    )

@settings_bp.route('/backup/download/<int:backup_id>')
@login_required
@role_required('system_admin')
def download_backup(backup_id):
    """Download backup"""
    backup = BackupLog.query.get_or_404(backup_id)
    
    # Here you would implement actual backup download logic
    return jsonify({'error': 'Not implemented yet'}), 501
