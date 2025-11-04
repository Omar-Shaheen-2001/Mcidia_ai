from flask import render_template, request, redirect, url_for, flash, session
from blueprints.org_dashboard import org_dashboard_bp
from utils.decorators import login_required, organization_role_required
from models import Organization, OrganizationSettings, db
from flask import current_app
import json

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@org_dashboard_bp.route('/<int:org_id>/settings', methods=['GET', 'POST'])
@login_required
@organization_role_required('owner', 'admin', org_id_param='org_id')
def settings(org_id, _membership=None, _organization=None):
    """Organization Settings"""
    lang = get_lang()
    db_session = get_db()
    org = _organization
    
    # Get or create settings
    org_settings = db_session.session.query(OrganizationSettings).filter_by(
        organization_id=org_id
    ).first()
    
    if not org_settings:
        org_settings = OrganizationSettings(
            organization_id=org_id,
            default_language=lang,
            enabled_modules=json.dumps(['strategy', 'hr', 'finance'])
        )
        db_session.session.add(org_settings)
        db_session.session.commit()
    
    if request.method == 'POST':
        try:
            # Update organization basic info
            org.name = request.form.get('name')
            org.sector = request.form.get('sector')
            org.country = request.form.get('country')
            org.city = request.form.get('city')
            org.website = request.form.get('website')
            org.address = request.form.get('address')
            
            # Update settings
            org_settings.default_language = request.form.get('default_language')
            org_settings.timezone = request.form.get('timezone')
            
            db_session.session.commit()
            flash('تم حفظ الإعدادات بنجاح / Settings saved successfully', 'success')
            return redirect(url_for('org_dashboard.settings', org_id=org_id))
        except Exception as e:
            db_session.session.rollback()
            flash(f'خطأ في حفظ الإعدادات / Error saving settings: {str(e)}', 'danger')
    
    return render_template(
        'org_dashboard/settings.html',
        org=org,
        org_settings=org_settings,
        membership=_membership,
        lang=lang
    )
