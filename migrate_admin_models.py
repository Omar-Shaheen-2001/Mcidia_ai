"""
Migration script to add new admin-related columns and tables
This is a Python/Flask/SQLAlchemy project (not TypeScript/Drizzle)
"""
from app import create_app, db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        print("🔄 Running migrations for admin models...")
        
        # Add new columns to users table
        try:
            print("Adding organization_id, is_active, last_login to users table...")
            db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id)'))
            db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE'))
            db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP'))
            db.session.commit()
            print("✅ User columns added successfully")
        except Exception as e:
            print(f"⚠️  User columns may already exist or error: {e}")
            db.session.rollback()
        
        # Create all new tables
        try:
            print("Creating new tables (organizations, notifications, support_tickets, system_settings, audit_logs)...")
            db.create_all()
            print("✅ All tables created successfully")
        except Exception as e:
            print(f"⚠️  Error creating tables: {e}")
            db.session.rollback()
        
        print("✅ Migration completed!")

if __name__ == '__main__':
    migrate()
