"""
Tenancy Utility
Handles organization provisioning and management for multi-tenant architecture
"""

from models import Organization, OrganizationMembership


def get_or_create_user_org(session, user):
    """
    Get or create organization for a user.
    
    Args:
        session: SQLAlchemy database session (actual session object, not extension)
        user: User object
        
    Returns:
        int: organization_id
        
    Raises:
        Exception: If organization creation fails
    """
    # If user already has organization, return it
    if user.organization_id:
        return user.organization_id
    
    # Create new organization for user
    try:
        # Check if organization with this email already exists (race condition guard)
        existing_org = session.query(Organization).filter_by(
            email=user.email
        ).first()
        
        if existing_org:
            # Link user to existing organization
            user.organization_id = existing_org.id
            
            # Check if membership exists
            existing_membership = session.query(OrganizationMembership).filter_by(
                user_id=user.id,
                organization_id=existing_org.id
            ).first()
            
            if not existing_membership:
                # Create membership
                membership = OrganizationMembership(
                    user_id=user.id,
                    organization_id=existing_org.id,
                    membership_role='owner',
                    is_active=True
                )
                session.add(membership)
            
            session.commit()
            return existing_org.id
        
        # Create new organization
        organization = Organization(
            name=f"{user.username}'s Organization" if user.username else "My Organization",
            email=user.email,
            is_active=True
        )
        session.add(organization)
        session.flush()
        
        # Link user to organization
        user.organization_id = organization.id
        
        # Create organization membership
        membership = OrganizationMembership(
            user_id=user.id,
            organization_id=organization.id,
            membership_role='owner',
            is_active=True
        )
        session.add(membership)
        session.commit()
        
        return organization.id
        
    except Exception as e:
        session.rollback()
        raise e
