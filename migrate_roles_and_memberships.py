#!/usr/bin/env python3
"""
Migration script for implementing hierarchical role-based access control.

This script:
1. Creates organization_memberships table
2. Renames 'admin' role to 'system_admin' for clarity
3. Migrates existing users with organization_id to memberships table
4. Sets appropriate organization roles (owner/admin/member)
"""

import os
import sys
from datetime import datetime

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import db
from models import OrganizationMembership, User, Role, Organization
from sqlalchemy import text

def run_migration():
    print("Starting Roles & Memberships Migration...")
    print("=" * 60)
    
    try:
        # Step 1: Create organization_memberships table if it doesn't exist
        print("\n[1/5] Creating organization_memberships table...")
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS organization_memberships (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                membership_role VARCHAR(50) NOT NULL DEFAULT 'member',
                permissions TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_user_org_membership UNIQUE (user_id, organization_id)
            )
        """))
        db.session.commit()
        print("✓ organization_memberships table created/verified!")
        
        # Step 2: Update 'admin' role to 'system_admin' if it exists
        print("\n[2/5] Updating role names for clarity...")
        
        # Check if 'admin' role exists
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            # Check if 'system_admin' already exists
            system_admin_role = Role.query.filter_by(name='system_admin').first()
            if not system_admin_role:
                # Rename 'admin' to 'system_admin'
                admin_role.name = 'system_admin'
                admin_role.description = 'Platform System Administrator - Full Access'
                db.session.commit()
                print("✓ Renamed 'admin' role to 'system_admin'")
            else:
                # Transfer users from 'admin' to 'system_admin'
                print("  'system_admin' role already exists, transferring users...")
                User.query.filter_by(role_id=admin_role.id).update({'role_id': system_admin_role.id})
                db.session.delete(admin_role)
                db.session.commit()
                print("✓ Transferred users from 'admin' to 'system_admin'")
        else:
            print("  'admin' role not found, checking for 'system_admin'...")
            system_admin_role = Role.query.filter_by(name='system_admin').first()
            if not system_admin_role:
                # Create system_admin role
                system_admin_role = Role(
                    name='system_admin',
                    description='Platform System Administrator - Full Access'
                )
                db.session.add(system_admin_role)
                db.session.commit()
                print("✓ Created 'system_admin' role")
            else:
                print("✓ 'system_admin' role already exists")
        
        # Step 3: Ensure 'external_user' role exists for non-admin users
        print("\n[3/5] Ensuring default user roles exist...")
        
        external_user_role = Role.query.filter_by(name='external_user').first()
        if not external_user_role:
            external_user_role = Role(
                name='external_user',
                description='External User - Organization Member'
            )
            db.session.add(external_user_role)
            db.session.commit()
            print("✓ Created 'external_user' role")
        else:
            print("✓ 'external_user' role already exists")
        
        # Keep other existing roles (consultant, company_user, client)
        for role_name in ['consultant', 'company_user', 'client']:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=f'{role_name.replace("_", " ").title()}')
                db.session.add(role)
                print(f"✓ Created '{role_name}' role")
        
        db.session.commit()
        
        # Step 4: Migrate existing users with organization_id to memberships
        print("\n[4/5] Migrating existing organization users to memberships...")
        
        # Get all users that belong to organizations
        users_with_orgs = User.query.filter(User.organization_id.isnot(None)).all()
        
        migrated_count = 0
        skipped_count = 0
        
        for user in users_with_orgs:
            # Check if membership already exists
            existing_membership = OrganizationMembership.query.filter_by(
                user_id=user.id,
                organization_id=user.organization_id
            ).first()
            
            if existing_membership:
                skipped_count += 1
                continue
            
            # Determine membership role based on user's system role
            # System admins become organization owners
            # Others become members
            if user.role == 'system_admin':
                membership_role = 'owner'
            elif user.role in ['consultant', 'company_user']:
                membership_role = 'admin'
            else:
                membership_role = 'member'
            
            # Create membership
            membership = OrganizationMembership(
                user_id=user.id,
                organization_id=user.organization_id,
                membership_role=membership_role,
                is_active=user.is_active,
                joined_at=user.created_at or datetime.utcnow()
            )
            db.session.add(membership)
            migrated_count += 1
        
        db.session.commit()
        print(f"✓ Migrated {migrated_count} users to memberships (skipped {skipped_count} existing)")
        
        # Step 5: Update users without organizations to 'external_user' role
        print("\n[5/5] Updating users without organizations...")
        
        # Get external_user role
        external_user_role = Role.query.filter_by(name='external_user').first()
        system_admin_role = Role.query.filter_by(name='system_admin').first()
        
        # Update users that don't have organization and aren't system admins
        users_without_org = User.query.filter(
            User.organization_id.is_(None),
            User.role_id != system_admin_role.id
        ).all()
        
        updated_count = 0
        for user in users_without_org:
            if user.role not in ['system_admin']:
                user.role_id = external_user_role.id
                updated_count += 1
        
        db.session.commit()
        print(f"✓ Updated {updated_count} users to 'external_user' role")
        
        # Summary
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("\nSummary:")
        print(f"  - organization_memberships table: Created ✓")
        print(f"  - System roles updated: ✓")
        print(f"  - Users migrated to memberships: {migrated_count}")
        print(f"  - External users updated: {updated_count}")
        print("\nRole Structure:")
        print("  Global Roles:")
        print("    - system_admin: Platform administrators")
        print("    - external_user: Default for organization members")
        print("    - consultant, company_user, client: Legacy roles")
        print("\n  Organization Roles (in memberships):")
        print("    - owner: Can manage organization, admins, billing")
        print("    - admin: Can manage users and settings within org")
        print("    - member: Standard user access within org")
        print("=" * 60)
        
    except Exception as e:
        db.session.rollback()
        print(f"\n✗ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    
    with app.app_context():
        run_migration()
