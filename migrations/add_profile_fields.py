"""Add profile fields to User model

This script adds new profile-related columns to the User table.
Run this script directly to apply these changes to your database.
"""

from app import create_app, db
from sqlalchemy.exc import OperationalError

def add_profile_fields():
    """Add profile fields to the User model/table"""
    app = create_app()
    
    with app.app_context():
        # Add columns one by one to handle potential errors with each
        try:
            print("Starting migration: Adding profile fields to User model...")
            
            try:
                db.engine.execute('ALTER TABLE user ADD COLUMN full_name VARCHAR(100)')
                print("Added full_name column")
            except OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("Column full_name already exists, skipping")
                else:
                    raise
            
            try:
                db.engine.execute('ALTER TABLE user ADD COLUMN bio TEXT')
                print("Added bio column")
            except OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("Column bio already exists, skipping")
                else:
                    raise
            
            try:
                db.engine.execute('ALTER TABLE user ADD COLUMN department VARCHAR(100)')
                print("Added department column")
            except OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("Column department already exists, skipping")
                else:
                    raise
            
            try:
                db.engine.execute('ALTER TABLE user ADD COLUMN student_id VARCHAR(20)')
                print("Added student_id column")
            except OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("Column student_id already exists, skipping")
                else:
                    raise
            
            try:
                db.engine.execute("ALTER TABLE user ADD COLUMN profile_image VARCHAR(120) DEFAULT 'default.jpg'")
                print("Added profile_image column")
            except OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("Column profile_image already exists, skipping")
                else:
                    raise
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            print("Migration failed. You may need to manually adjust your database schema.")
            return False
        
        return True

if __name__ == "__main__":
    print("Running migration script to add profile fields to User model...")
    success = add_profile_fields()
    
    if success:
        print("Migration completed successfully.")
    else:
        print("Migration failed. Check the error messages above.")