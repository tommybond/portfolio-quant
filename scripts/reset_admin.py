#!/usr/bin/env python3
"""
Reset Admin User Password
Use this script to reset or create the admin user
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import init_database, create_session, User
from auth.auth import AuthManager

def reset_admin_password(new_password='admin123'):
    """Reset admin user password"""
    print("=" * 60)
    print("Admin User Password Reset Tool")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    try:
        init_database()
        print("   ✅ Database initialized")
    except Exception as e:
        print(f"   ⚠️  Database warning: {e}")
    
    # Create session
    db = create_session()
    auth = AuthManager(db)
    
    # Check if admin exists
    print("\n2. Checking admin user...")
    admin = db.query(User).filter(User.username == 'admin').first()
    
    if admin:
        print(f"   ✅ Admin user exists")
        print(f"      Username: {admin.username}")
        print(f"      Email: {admin.email}")
        print(f"      Role: {admin.role}")
        print(f"      Active: {admin.is_active}")
        
        # Reset password
        print(f"\n3. Resetting password...")
        admin.password_hash = auth.hash_password(new_password)
        admin.is_active = True
        db.commit()
        print(f"   ✅ Password reset successful")
        
    else:
        print("   ⚠️  Admin user does NOT exist")
        print("\n3. Creating admin user...")
        
        admin = auth.create_user(
            username='admin',
            email='admin@nashor.com',
            password=new_password,
            full_name='System Administrator',
            role='admin'
        )
        
        if admin:
            print("   ✅ Admin user created successfully")
        else:
            print("   ❌ Failed to create admin user")
            db.close()
            return False
    
    # Verify authentication
    print("\n4. Verifying authentication...")
    test_user = auth.authenticate('admin', new_password)
    if test_user:
        print("   ✅ Authentication test PASSED")
        print(f"      Username: {test_user.username}")
        print(f"      Role: {test_user.role}")
    else:
        print("   ❌ Authentication test FAILED")
        db.close()
        return False
    
    db.close()
    
    print("\n" + "=" * 60)
    print("✅ Admin user configured successfully!")
    print("=" * 60)
    print(f"\n📋 Login Credentials:")
    print(f"   Username: admin")
    print(f"   Password: {new_password}")
    print("\n⚠️  Please change the password after first login!")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Reset admin user password')
    parser.add_argument('--password', '-p', default='admin123', 
                       help='New password (default: admin123)')
    
    args = parser.parse_args()
    
    success = reset_admin_password(args.password)
    sys.exit(0 if success else 1)
