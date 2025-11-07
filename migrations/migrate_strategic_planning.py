"""
Migration script to create Strategic Planning module tables
Run: python migrations/migrate_strategic_planning.py
"""
import sys
sys.path.append('.')

from app import create_app, db
from models import StrategicPlan, StrategicKPI, StrategicInitiative

def migrate():
    """Create strategic planning tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating Strategic Planning tables...")
        
        try:
            # Create tables
            db.create_all()
            print("✓ Tables created successfully!")
            
            # Verify tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['strategic_plans', 'strategic_kpis', 'strategic_initiatives']
            for table in required_tables:
                if table in tables:
                    print(f"✓ Table '{table}' exists")
                else:
                    print(f"✗ Table '{table}' missing!")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == '__main__':
    migrate()
