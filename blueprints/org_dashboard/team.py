from flask import render_template, request, redirect, url_for, flash, session, jsonify
from blueprints.org_dashboard import org_dashboard_bp
from utils.decorators import login_required, organization_role_required
from models import User, Organization, OrganizationMembership, Role, db
from flask import current_app

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@org_dashboard_bp.route('/<int:org_id>/team')
@login_required
@organization_role_required('owner', 'admin', org_id_param='org_id')
def team(org_id, _membership=None, _organization=None):
    """Team Management - Manage organization members"""
    lang = get_lang()
    db_session = get_db()
    
    org = _organization
    
    # Get all organization members
    members = db_session.session.query(User).join(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.is_active == True
    ).all()
    
    # Get memberships with roles
    memberships = db_session.session.query(OrganizationMembership).filter_by(
        organization_id=org_id,
        is_active=True
    ).all()
    
    return render_template(
        'org_dashboard/team.html',
        org=org,
        members=members,
        memberships=memberships,
        membership=_membership,
        lang=lang
    )
