"""
Migration script to create OrganizationMembership records for legacy users
who have organization_id but no membership record.

This fixes the issue where old users were created with organization_id 
before the OrganizationMembership system was implemented.
"""

from app import create_app, db
from models import User, OrganizationMembership, Organization
from datetime import datetime

def migrate_legacy_members():
    """Create membership records for users with organization_id but no membership."""
    
    app = create_app()
    with app.app_context():
        # Find users who have organization_id but no membership
        users_without_membership = db.session.query(User).filter(
            User.organization_id.isnot(None)
        ).all()
        
        created_count = 0
        skipped_count = 0
        
        print("\n" + "="*60)
        print("بدء ترحيل المستخدمين القدامى / Starting Legacy User Migration")
        print("="*60 + "\n")
        
        for user in users_without_membership:
            # Check if membership already exists
            existing_membership = db.session.query(OrganizationMembership).filter_by(
                user_id=user.id,
                organization_id=user.organization_id
            ).first()
            
            if existing_membership:
                print(f"✓ تخطي {user.username} - العضوية موجودة بالفعل / Skipping {user.username} - membership exists")
                skipped_count += 1
                continue
            
            # Verify organization exists
            org = db.session.query(Organization).filter_by(id=user.organization_id).first()
            if not org:
                print(f"⚠ تحذير: المؤسسة {user.organization_id} غير موجودة للمستخدم {user.username}")
                print(f"⚠ Warning: Organization {user.organization_id} not found for user {user.username}")
                continue
            
            # Determine the appropriate role
            # If this is the first user in the organization, make them owner
            # Otherwise, make them a member
            existing_memberships = db.session.query(OrganizationMembership).filter_by(
                organization_id=user.organization_id
            ).all()
            
            if not existing_memberships:
                # First user - make them owner
                role = 'owner'
                print(f"📌 إنشاء عضوية مالك للمستخدم الأول في المؤسسة")
                print(f"📌 Creating owner membership for first user in organization")
            else:
                # Subsequent users - make them members
                role = 'member'
                print(f"👤 إنشاء عضوية عضو للمستخدم")
                print(f"👤 Creating member membership for user")
            
            # Create membership
            new_membership = OrganizationMembership(
                user_id=user.id,
                organization_id=user.organization_id,
                membership_role=role,
                is_active=True,
                joined_at=user.created_at if hasattr(user, 'created_at') else datetime.utcnow()
            )
            
            db.session.add(new_membership)
            
            print(f"✅ تم إنشاء عضوية '{role}' للمستخدم: {user.username} ({user.email})")
            print(f"✅ Created '{role}' membership for user: {user.username} ({user.email})")
            print(f"   المؤسسة / Organization: {org.name} (ID: {org.id})")
            print()
            
            created_count += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "="*60)
            print("✅ نجح الترحيل! / Migration Successful!")
            print("="*60)
            print(f"📊 الإحصائيات / Statistics:")
            print(f"   - عضويات جديدة / New memberships: {created_count}")
            print(f"   - تم التخطي / Skipped: {skipped_count}")
            print("="*60 + "\n")
        except Exception as e:
            db.session.rollback()
            print("\n" + "="*60)
            print("❌ فشل الترحيل! / Migration Failed!")
            print("="*60)
            print(f"Error: {str(e)}")
            print("="*60 + "\n")
            raise

if __name__ == '__main__':
    print("\n🚀 بدء سكريبت ترحيل الأعضاء القدامى")
    print("🚀 Starting Legacy Members Migration Script\n")
    
    migrate_legacy_members()
    
    print("✅ اكتمل السكريبت!")
    print("✅ Script completed!\n")
