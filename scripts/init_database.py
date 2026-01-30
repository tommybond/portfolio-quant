#!/usr/bin/env python3
"""
Initialize database schema
Run this script to create all database tables
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import init_database, create_session, User
from auth.auth import AuthManager

def create_default_admin():
    """Create default admin user"""
    db = create_session()
    auth = AuthManager(db)
    
    # Check if admin exists
    admin = db.query(User).filter(User.username == 'admin').first()
    if admin:
        print("Admin user already exists")
        return
    
    # Create admin user
    admin = auth.create_user(
        username='admin',
        email='admin@nashor.com',
        password='admin123',  # Change in production!
        full_name='System Administrator',
        role='admin'
    )
    
    if admin:
        print("✅ Default admin user created:")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print("   ⚠️  Please change the password after first login!")
    else:
        print("❌ Failed to create admin user")


if __name__ == '__main__':
    print("Initializing database...")
    engine = init_database()
    print("✅ Database tables created successfully")
    
    print("\nCreating default admin user...")
    create_default_admin()
    
    print("\n✅ Database initialization complete!")
