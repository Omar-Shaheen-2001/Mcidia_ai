"""
Migration script to update Organizations table and create OrganizationSettings
Run this file to add new columns to organizations table
"""
from app import create_app
from models import db, Organization, OrganizationSettings
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starting Organizations migration...")
    
    # Add new columns if they don't exist
    try:
        with db.engine.connect() as conn:
            # Check and add missing columns to organizations table
            columns_to_add = [
                ("sector", "VARCHAR(100)"),
                ("city", "VARCHAR(100)"),
                ("email", "VARCHAR(120)"),
                ("phone", "VARCHAR(50)"),
                ("website", "VARCHAR(200)"),
                ("logo_url", "VARCHAR(500)"),
                ("plan_type", "VARCHAR(50) DEFAULT 'free'"),
                ("subscription_status", "VARCHAR(50) DEFAULT 'active'"),
                ("ai_usage_limit", "INTEGER DEFAULT 1000"),
                ("ai_usage_current", "INTEGER DEFAULT 0"),
            ]
            
            for col_name, col_type in columns_to_add:
                try:
                    conn.execute(text(f"ALTER TABLE organizations ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                    conn.commit()
                    print(f"✓ Added column: {col_name}")
                except Exception as e:
                    print(f"Note: Column {col_name} might already exist: {e}")
            
            # Rename industry to sector if needed
            try:
                conn.execute(text("ALTER TABLE organizations RENAME COLUMN industry TO sector"))
                conn.commit()
                print("✓ Renamed industry to sector")
            except Exception as e:
                print(f"Note: industry column might not exist or already renamed: {e}")
            
            # Rename contact_email to email
            try:
                conn.execute(text("ALTER TABLE organizations RENAME COLUMN contact_email TO email"))
                conn.commit()
                print("✓ Renamed contact_email to email")
            except Exception as e:
                print(f"Note: contact_email column might not exist or already renamed: {e}")
            
            # Rename contact_phone to phone
            try:
                conn.execute(text("ALTER TABLE organizations RENAME COLUMN contact_phone TO phone"))
                conn.commit()
                print("✓ Renamed contact_phone to phone")
            except Exception as e:
                print(f"Note: contact_phone column might not exist or already renamed: {e}")
            
            print("\n✓ Organizations table migration completed!")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    
    # Create OrganizationSettings table
    try:
        db.create_all()
        print("✓ OrganizationSettings table created/verified!")
    except Exception as e:
        print(f"Error creating OrganizationSettings table: {e}")
    
    print("\nMigration complete!")
