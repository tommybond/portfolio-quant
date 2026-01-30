# Admin Login Troubleshooting Guide

## Default Admin Credentials

- **Username**: `admin`
- **Password**: `admin123`

---

## Quick Fix: Reset Admin Password

If login is not working, reset the admin password:

```bash
cd ~/Documents/portfolio-quant
source venv/bin/activate
python3 scripts/reset_admin.py
```

Or with a custom password:

```bash
python3 scripts/reset_admin.py --password your_new_password
```

---

## Common Issues & Solutions

### Issue 1: "User not found" or "Invalid password"

**Solution:**
1. **Reset admin user**:
   ```bash
   python3 scripts/reset_admin.py
   ```

2. **Verify admin exists**:
   ```bash
   python3 -c "
   from database.models import create_session, User
   db = create_session()
   admin = db.query(User).filter(User.username == 'admin').first()
   if admin:
       print(f'✅ Admin exists: {admin.username}, Active: {admin.is_active}')
   else:
       print('❌ Admin does NOT exist')
   db.close()
   "
   ```

3. **Test authentication**:
   ```bash
   python3 -c "
   from database.models import create_session
   from auth.auth import AuthManager
   db = create_session()
   auth = AuthManager(db)
   user = auth.authenticate('admin', 'admin123')
   if user:
       print('✅ Authentication works!')
   else:
       print('❌ Authentication failed')
   db.close()
   "
   ```

---

### Issue 2: Database Not Initialized

**Symptoms:**
- Error: "Database initialization warning"
- Login page shows but authentication fails

**Solution:**
```bash
# Initialize database
python3 scripts/init_database.py

# Reset admin user
python3 scripts/reset_admin.py
```

---

### Issue 3: Headless Mode Enabled (Auto-login)

**Symptoms:**
- Login page doesn't appear
- App auto-logs in (or fails to auto-login)

**Check .env file:**
```bash
cat .env | grep HEADLESS_LOGIN
```

**If `HEADLESS_LOGIN=true`:**
- App will try to auto-login as admin
- If auto-login fails, you'll see guest mode

**To disable headless mode:**
```bash
# Edit .env file
nano .env

# Change this line:
HEADLESS_LOGIN=false

# Or remove the line entirely
```

---

### Issue 4: Database Connection Issues

**Symptoms:**
- "Database initialization warning" error
- Authentication fails silently

**Check database:**
```bash
# Check if SQLite database exists
ls -la portfolio_quant.db

# Check database connection
python3 -c "
from database.models import create_session
try:
    db = create_session()
    print('✅ Database connection successful')
    db.close()
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

**Solution:**
```bash
# Reinitialize database
python3 scripts/init_database.py

# Reset admin
python3 scripts/reset_admin.py
```

---

### Issue 5: INTEGRATIONS_AVAILABLE is False

**Symptoms:**
- Login page doesn't show
- App runs in guest mode

**Check:**
```bash
# Run app and check for warnings
streamlit run app.py

# Look for: "⚠️ Some advanced features not available"
```

**Solution:**
```bash
# Install missing dependencies
pip install -r requirements.txt

# Check specific imports
python3 -c "
try:
    from database.models import init_database, create_session, User
    from auth.auth import AuthManager
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
"
```

---

## Step-by-Step Troubleshooting

### Step 1: Verify Admin User Exists
```bash
python3 -c "
from database.models import create_session, User
db = create_session()
admin = db.query(User).filter(User.username == 'admin').first()
if admin:
    print(f'✅ Admin exists')
    print(f'   Username: {admin.username}')
    print(f'   Email: {admin.email}')
    print(f'   Role: {admin.role}')
    print(f'   Active: {admin.is_active}')
else:
    print('❌ Admin does NOT exist - run: python3 scripts/reset_admin.py')
db.close()
"
```

### Step 2: Test Authentication
```bash
python3 -c "
from database.models import create_session
from auth.auth import AuthManager
db = create_session()
auth = AuthManager(db)
user = auth.authenticate('admin', 'admin123')
if user:
    print('✅ Authentication SUCCESSFUL')
    print(f'   User: {user.username}')
    print(f'   Role: {user.role}')
else:
    print('❌ Authentication FAILED')
    print('   Run: python3 scripts/reset_admin.py')
db.close()
"
```

### Step 3: Reset Admin (if needed)
```bash
python3 scripts/reset_admin.py
```

### Step 4: Restart App
```bash
# Stop the app (Ctrl+C)
# Restart
streamlit run app.py
```

---

## Manual Admin Creation

If reset script doesn't work, create admin manually:

```bash
python3 << EOF
import sys
import os
sys.path.insert(0, '.')

from database.models import init_database, create_session, User
from auth.auth import AuthManager

# Initialize
init_database()
db = create_session()
auth = AuthManager(db)

# Delete existing admin if exists
existing = db.query(User).filter(User.username == 'admin').first()
if existing:
    db.delete(existing)
    db.commit()
    print('Deleted existing admin')

# Create new admin
admin = auth.create_user(
    username='admin',
    email='admin@nashor.com',
    password='admin123',
    full_name='System Administrator',
    role='admin'
)

if admin:
    print('✅ Admin created successfully')
    print(f'   Username: admin')
    print(f'   Password: admin123')
else:
    print('❌ Failed to create admin')

db.close()
EOF
```

---

## Verify Login in App

1. **Start the app**:
   ```bash
   streamlit run app.py
   ```

2. **Go to login page** (if not in headless mode)

3. **Enter credentials**:
   - Username: `admin`
   - Password: `admin123`

4. **Check for errors**:
   - If "User not found" → Admin doesn't exist, run reset script
   - If "Invalid password" → Password hash mismatch, run reset script
   - If "Account inactive" → Admin exists but is_active=False

---

## Alternative: Use Headless Mode

If login keeps failing, enable headless mode for auto-login:

```bash
# Edit .env file
nano .env

# Add or update:
HEADLESS_LOGIN=true

# Restart app
streamlit run app.py
```

The app will automatically log in as admin (if admin exists and password is correct).

---

## Still Not Working?

1. **Check app logs** for errors:
   ```bash
   streamlit run app.py 2>&1 | tee app.log
   ```

2. **Check database file**:
   ```bash
   ls -la portfolio_quant.db
   file portfolio_quant.db
   ```

3. **Delete and recreate database**:
   ```bash
   rm portfolio_quant.db
   python3 scripts/init_database.py
   python3 scripts/reset_admin.py
   ```

4. **Check Python environment**:
   ```bash
   which python3
   python3 --version
   source venv/bin/activate
   pip list | grep -E "(sqlalchemy|auth)"
   ```

---

## Summary

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

**Quick Fix:**
```bash
python3 scripts/reset_admin.py
```

**Verify:**
```bash
python3 -c "from database.models import create_session; from auth.auth import AuthManager; db = create_session(); auth = AuthManager(db); user = auth.authenticate('admin', 'admin123'); print('✅ Works!' if user else '❌ Failed'); db.close()"
```
