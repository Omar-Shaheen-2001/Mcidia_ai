"""Add enable_file_upload column to service_offerings table"""
from app import db, app

def migrate():
    """Add the enable_file_upload column"""
    with app.app_context():
        # Check if column already exists
        inspector = db.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('service_offerings')]
        
        if 'enable_file_upload' not in columns:
            with db.engine.begin() as connection:
                connection.execute(db.text(
                    "ALTER TABLE service_offerings ADD COLUMN enable_file_upload BOOLEAN DEFAULT FALSE"
                ))
            print("✅ Column 'enable_file_upload' added to service_offerings table")
        else:
            print("ℹ️ Column 'enable_file_upload' already exists")

if __name__ == '__main__':
    migrate()
