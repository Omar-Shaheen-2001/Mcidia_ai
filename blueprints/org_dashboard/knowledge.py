from flask import render_template, session
from blueprints.org_dashboard import org_dashboard_bp
from utils.decorators import login_required, organization_role_required
from flask import current_app

def get_lang():
    return session.get('language', 'ar')

@org_dashboard_bp.route('/<int:org_id>/knowledge')
@login_required
@organization_role_required('owner', 'admin', 'member', org_id_param='org_id')
def knowledge(org_id, _membership=None, _organization=None):
    """Knowledge Center - Document management"""
    lang = get_lang()
    org = _organization
    
    return render_template(
        'org_dashboard/knowledge.html',
        org=org,
        membership=_membership,
        lang=lang
    )
