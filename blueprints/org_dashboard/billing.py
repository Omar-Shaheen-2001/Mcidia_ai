from flask import render_template, session
from blueprints.org_dashboard import org_dashboard_bp
from utils.decorators import login_required, organization_role_required
from flask import current_app

def get_lang():
    return session.get('language', 'ar')

@org_dashboard_bp.route('/<int:org_id>/billing')
@login_required
@organization_role_required('owner', org_id_param='org_id')
def billing(org_id, _membership=None, _organization=None):
    """Billing & Subscription Management"""
    lang = get_lang()
    org = _organization
    
    return render_template(
        'org_dashboard/billing.html',
        org=org,
        membership=_membership,
        lang=lang
    )
