from flask import render_template, session, redirect, url_for, flash
from . import member_dashboard_bp
from utils.decorators import organization_role_required
from models import db, OrganizationSettings
import json

@member_dashboard_bp.route('/<int:org_id>/modules')
@organization_role_required('member', 'admin', 'owner', org_id_param='org_id')
def modules(org_id, _membership=None, _organization=None):
    """Display available modules for member based on organization settings"""
    lang = session.get('language', 'ar')
    
    # Get organization settings to know enabled modules
    org_settings = db.session.query(OrganizationSettings).filter_by(
        organization_id=org_id
    ).first()
    
    enabled_modules = []
    if org_settings and org_settings.enabled_modules:
        enabled_modules = json.loads(org_settings.enabled_modules)
    
    # Define all available modules with their details
    all_modules = {
        'strategy': {
            'name_ar': 'التخطيط الاستراتيجي',
            'name_en': 'Strategic Planning',
            'icon': 'fa-chart-line',
            'url': 'services.strategy'
        },
        'hr': {
            'name_ar': 'الموارد البشرية',
            'name_en': 'Human Resources',
            'icon': 'fa-users',
            'url': 'services.hr'
        },
        'finance': {
            'name_ar': 'المالية',
            'name_en': 'Finance',
            'icon': 'fa-dollar-sign',
            'url': 'services.finance'
        },
        'governance': {
            'name_ar': 'الحوكمة',
            'name_en': 'Governance',
            'icon': 'fa-balance-scale',
            'url': 'services.governance'
        },
        'innovation': {
            'name_ar': 'الابتكار',
            'name_en': 'Innovation',
            'icon': 'fa-lightbulb',
            'url': 'services.innovation'
        },
        'marketing': {
            'name_ar': 'التسويق',
            'name_en': 'Marketing',
            'icon': 'fa-bullhorn',
            'url': 'services.marketing'
        },
        'km': {
            'name_ar': 'إدارة المعرفة',
            'name_en': 'Knowledge Management',
            'icon': 'fa-book',
            'url': 'services.knowledge_management'
        }
    }
    
    # Filter only enabled modules
    available_modules = {
        key: value for key, value in all_modules.items()
        if key in enabled_modules
    }
    
    return render_template(
        'member_dashboard/modules.html',
        lang=lang,
        organization=_organization,
        membership=_membership,
        modules=available_modules
    )
