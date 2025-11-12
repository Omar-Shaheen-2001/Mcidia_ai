"""
Seed admin user for testing
Run this script to create a test admin user
"""

from app import create_app, db
from models import User, Role, SubscriptionPlan

def seed_admin():
    """Create admin user for testing"""
    
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        existing_admin = db.session.query(User).filter_by(email='admin@example.com').first()
        if existing_admin:
            print("✅ Admin user already exists with email admin@example.com")
            print(f"   Username: {existing_admin.username}")
            print(f"   Email: {existing_admin.email}")
            
            # Update password to ensure it's correct
            existing_admin.set_password('admin123')
            db.session.commit()
            print("✅ Password updated to: admin123")
            return
        
        # Get system_admin role
        admin_role = db.session.query(Role).filter_by(name='system_admin').first()
        if not admin_role:
            print("❌ System admin role not found. Please run seed_database first.")
            return
        
        # Get free plan
        free_plan = db.session.query(SubscriptionPlan).filter_by(name='free').first()
        if not free_plan:
            print("❌ Free plan not found. Please run seed_database first.")
            return
        
        # Create admin user with unique username and role field
        admin_user = User(
            username='Admin',
            email='admin@example.com',
            company_name='Mcidia Platform',
            role='system_admin',
            subscription_plan_id=free_plan.id,
            subscription_status='active',
            ai_credits_used=0,
            is_online=False
        )
        admin_user.set_password('admin123')
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print(f"   Email: admin@example.com")
        print(f"   Password: admin123")
        print(f"   Username: testadmin")
        print(f"   Role: {admin_role.name}")
        print(f"   Plan: {free_plan.name}")

if __name__ == '__main__':
    seed_admin()
